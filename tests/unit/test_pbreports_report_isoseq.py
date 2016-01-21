
# TODO(nechols)(2016-01-21): test actual output

import os
import logging
import shutil
import unittest
import tempfile

from pbcommand.models.report import Report
from pbcommand.pb_io.report import load_report_from_json
from pbcommand.testkit import PbTestApp

import pbreports.report.isoseq_classify
import pbreports.report.isoseq_cluster

from base_test_case import (LOCAL_DATA, run_backticks,
                            get_report_id_from_constants,
                            get_image_names_from_constants,
                            get_plot_groups_from_constants)

log = logging.getLogger(__name__)

_DATA_DIR = os.path.join(LOCAL_DATA, 'isoseq')

# This will keep the report results and skip the teardown classmethod
_DEBUG = False


class _TestIsoSeqBase(unittest.TestCase):
    """Test isoseq_classify_report.py.

    This is semi-abstract class. This should be cleanup a bit more
    """

    @classmethod
    def setUpClass(cls):
        cls.results_dir = tempfile.mkdtemp(prefix="isoseq_results_")
        cls.report_constants = pbreports.report.isoseq_classify.Constants
        cls.input_fasta = os.path.join(_DATA_DIR, 'isoseq_flnc.fasta')
        cls.output_summary_txt = os.path.join(_DATA_DIR, 'isoseq_classify_summary.txt')
        cls.report_json = os.path.join(cls.results_dir, "isoseq_classify.json")
        _d = dict(o=cls.results_dir, f=cls.input_fasta, s=cls.output_summary_txt, j=cls.report_json)
        cmd = 'isoseq_classify_report --debug {f} {s} {j}'.format(**_d)
        cls.code = run_backticks(cmd)

    def test_exit_code(self):
        self.assertEqual(0, self.code)

    def _to_report(self):
        return load_report_from_json(self.report_json)

    def test_validate_report(self):
        r = self._to_report()
        self.assertIsInstance(r, Report)

    def test_report_id(self):
        r = self._to_report()
        report_ids = get_report_id_from_constants(self.report_constants)
        report_id = report_ids[0]
        self.assertEqual(r.id, report_id)

    def test_report_plot_groups(self):
        r = self._to_report()
        report_plot_group_ids = [p.id for p in r.plotGroups]
        plot_group_ids = get_plot_groups_from_constants(self.report_constants)
        self.assertSequenceEqual(report_plot_group_ids, plot_group_ids)


    def test_images_exist(self):
        image_names = get_image_names_from_constants(self.report_constants)
        images = [os.path.join(self.results_dir, p) for p in image_names]
        for image in images:
            emsg = "Unable to find image {i}".format(i=image)
            self.assertTrue(os.path.exists(image), emsg)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'results_dir'):
            if not _DEBUG:
                if os.path.exists(cls.results_dir):
                    log.info("Removing dir {d}".format(d=cls.results_dir))
                    shutil.rmtree(cls.results_dir)


class TestIsoSeqClassify(_TestIsoSeqBase):
    pass


class TestIsoSeqCluster(_TestIsoSeqBase):

    @classmethod
    def setUpClass(cls):
        cls.report_constants = pbreports.report.isoseq_cluster.Constants
        cls.results_dir = tempfile.mkdtemp(prefix="isoseq_results_")
        cls.input_fasta = os.path.join(_DATA_DIR, 'isoseq_flnc.fasta')
        cls.output_summary_txt = os.path.join(_DATA_DIR, 'isoseq_cluster_summary.txt')
        cls.report_json = os.path.join(cls.results_dir, "isoseq_cluster.json")
        _d = dict(o=cls.results_dir, f=cls.input_fasta, s=cls.output_summary_txt, j=cls.report_json)
        cmd = 'isoseq_cluster_report --debug {f} {s} {j}'.format(**_d)
        cls.code = run_backticks(cmd)


class TestIsoSeqClassifyTCI(PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.isoseq_classify"
    INPUT_FILES = [
        os.path.join(_DATA_DIR, "isoseq_classify_ncfl.contigset.xml"),
        os.path.join(_DATA_DIR, "isoseq_classify_summary.json"),
    ]


class TestIsoSeqClusterTCI(PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.isoseq_cluster"
    INPUT_FILES = [
        os.path.join(_DATA_DIR, "consensus_isoforms.contigset.xml"),
        os.path.join(_DATA_DIR, "isoseq_cluster_summary.json"),
    ]
