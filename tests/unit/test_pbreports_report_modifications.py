import warnings
import tempfile
import unittest
import logging
import shutil
import json
import sys
import os

import numpy as np
import h5py

from pbcommand.pb_io.report import dict_to_report
import pbcommand.testkit
from pbcore.util.Process import backticks

from pbreports.report.modifications import (make_modifications_report,
                                            _create_fig_template,
                                            plot_kinetics_scatter,
                                            plot_kinetics_hist)

from base_test_case import LOCAL_DATA, validate_report_complete

log = logging.getLogger(__name__)


def make_h5(big_h5, ofn, n=None):
    """
    Utility function to extract and save the first N array items from a
    kinetics HDF5 file.
    """
    i = h5py.File(big_h5)
    o = h5py.File(ofn, "w")
    ig = i[f.keys()[0]]
    og = o.create_group(f.keys()[0])
    if n is None:
        sel = ig['base'].__array__() != ''
        n = 0
        for b in sel:
            if not b:
                break
            n += 1
    for k in ig.keys():
        d = og.create_dataset(k, (n,), dtype=ig[k].dtype, compression="gzip",
                              chunks=(min(n, 8192),))
        d[0:n] = ig[k][0:n]  # see note above
    o.close()


def make_h5_low_scores():
    """
    Create an HDF5 input with mostly-zero scores (SE-763).
    """
    ofn = tempfile.NamedTemporaryFile(suffix="h5").name
    h = h5py.File(ofn, "w")
    og = h.create_group("chr1")
    score = og.create_dataset("score", (10001,), dtype=np.dtype("uint32"),
                            compression="gzip", chunks=(1,))
    score[0:10000] = 0
    score[10000] = 100
    cov = og.create_dataset("coverage", (10001,), dtype=np.dtype("uint32"),
                            compression="gzip", chunks=(1,))
    cov[0:10001] = 50
    base = og.create_dataset("base", (10001,), dtype=np.dtype("S1"),
                            compression="gzip", chunks=(1,))
    base[0:10001] = "A"
    h.close()
    return ofn


class TestModificationsRpt(unittest.TestCase):

    def setUp(self):
        """
        Before *every* test
        """
        self._start_dir = os.getcwd()
        self._data_dir = os.path.join(LOCAL_DATA, 'modifications')
        self._output_dir = tempfile.mkdtemp(suffix="modifications")
        os.chdir(self._output_dir)
        self._h5 = os.path.join(self._data_dir, "basemods.h5")

    def tearDown(self):
        """
        After *every* test
        """
        os.chdir(self._start_dir)
        if os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_plot_kinetics_scatter(self):
        f = h5py.File(self._h5)
        fig, ax = _create_fig_template()
        with warnings.catch_warnings(record=True) as w:
            plot_kinetics_scatter(f, ax)
            self.assertEqual(len(w), 0,
                             "\n".join([str(w_.message) for w_ in w]))

    def test_plot_kinetics_hist(self):
        f = h5py.File(self._h5)
        fig, ax = _create_fig_template()
        with warnings.catch_warnings(record=True) as w:
            plot_kinetics_hist(f, ax)
            self.assertEqual(len(w), 0,
                             "\n".join([str(w_.message) for w_ in w]))

    def test_plot_kinetics_hist_low_scores(self):
        h5 = h5py.File(make_h5_low_scores())
        fig, ax = _create_fig_template()
        plot_kinetics_hist(h5, ax)
        fig.savefig("/home/nechols/tmp1.png")

    def test_make_modifications_report(self):
        """
        Create a report object, do assertions on its properties, then assert that it gets written
        """
        h5 = os.path.join(self._data_dir, "basemods.h5")

        make_modifications_report(h5, 'rpt.json', self._output_dir, 60)

        # deserialize report

        log.info("Deserializing report {r}".format(
            r=os.path.join(self._output_dir, 'rpt.json')))
        s = None
        with open(os.path.join(self._output_dir, 'rpt.json'), 'r') as f:
            s = json.load(f)

        report = dict_to_report(s)

        validate_report_complete(self, report)

        self.assertEqual(1, len(report.plotGroups))
        self.assertEqual(2, len(report.plotGroups[0].plots))

        scatter = report.plotGroups[0].plots[0]
        histo = report.plotGroups[0].plots[1]

        self._assert_image_file(report.plotGroups[0].thumbnail)
        self._assert_image_file(scatter.image)
        self._assert_image_file(histo.image)

    def _assert_image_file(self, filename):
        # Should we add validation to model.report that forces the filename to
        # be relative?
        self.assertFalse(os.path.isabs(filename))
        self.assertTrue(
            os.path.exists(os.path.join(self._output_dir, filename)))

    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """

        h5 = os.path.join(self._data_dir, "basemods.h5")
        cmd = 'python -m pbreports.report.modifications {h} {r}'.format(
            r='rpt.json',
            h=h5)

        o, c, m = backticks(cmd)
        log.info(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            sys.stderr.write(str(m) + "\n")

        self.assertEquals(0, c)
        self.assertTrue(
            os.path.exists(os.path.join(self._output_dir, 'rpt.json')))


EXPECTED_FILES = [
    'kinetic_histogram_thumb.png',
    'kinetic_detections.png',
    'kinetic_detections_thumb.png',
    'kinetic_histogram.png',
]


class TestPbreportModifications(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(LOCAL_DATA, "modifications")
    DRIVER_BASE = "python -m pbreports.report.modifications "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [os.path.join(DATA, "basemods.h5")]
    TASK_OPTIONS = {
        "pbreports.task_options.dpi": 60,
        "pbreports.task_options.dumpdata": True,
    }

    def run_after(self, rtc, output_dir):
        # XXX check for images not defined in the tool contract
        file_names = set(os.listdir(output_dir))
        for file_name in EXPECTED_FILES:
            self.assertTrue(file_name in file_names, "Missing %s" % file_name)
