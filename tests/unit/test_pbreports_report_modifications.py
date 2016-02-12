import os
import logging
import traceback
import json
import tempfile
import unittest
import shutil
import sys

from pbcommand.models.report import PbReportError
from pbcommand.pb_io.report import dict_to_report
import pbcommand.testkit
from pbcore.util.Process import backticks

from pbreports.report.modifications import (make_modifications_report)

from base_test_case import LOCAL_DATA

log = logging.getLogger(__name__)


class TestModificationsRpt(unittest.TestCase):

    def setUp(self):
        """
        Before *every* test
        """
        self._data_dir = os.path.join(LOCAL_DATA, 'modifications')
        self._output_dir = tempfile.mkdtemp(suffix="modifications")

    def tearDown(self):
        """
        After *every* test
        """
        if os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_make_modifications_report(self):
        """
        Create a report object, do assertions on its properties, then assert that it gets written
        """
        csv = os.path.join(self._data_dir, 'modifications.csv.gz')

        make_modifications_report(csv, 'rpt.json', self._output_dir, 60, False)

        # deserialize report

        log.info("Deserializing report {r}".format(
            r=os.path.join(self._output_dir, 'rpt.json')))
        s = None
        with open(os.path.join(self._output_dir, 'rpt.json'), 'r') as f:
            s = json.load(f)

        report = dict_to_report(s)

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

        csv = os.path.join(self._data_dir, 'modifications.csv.gz')
        cmd = 'python -m pbreports.report.modifications {c} {o} {r}'.format(
            o=self._output_dir,
            r='rpt.json',
            c=csv)

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
    INPUT_FILES = [os.path.join(DATA, "modifications.csv.gz")]
    TASK_OPTIONS = {
        "pbreports.task_options.dpi": 60,
        "pbreports.task_options.dumpdata": True,
    }

    def run_after(self, rtc, output_dir):
        # XXX check for images not defined in the tool contract
        file_names = set(os.listdir(output_dir))
        for file_name in EXPECTED_FILES:
            self.assertTrue(file_name in file_names, "Missing %s" % file_name)
