import os
import os.path as op
from pprint import pformat
import tempfile
import unittest
import logging

import pbcommand.testkit

import pbreports.report.overview as overview
from base_test_case import _get_root_data_dir, run_backticks
from pbreports.util import bas_fofn_to_bas_files

log = logging.getLogger(__name__)

ROOT_DATA_DIR = "/pbi/dept/secondary/siv/testdata/SA3-DS"

@unittest.skipUnless(op.exists(ROOT_DATA_DIR), "%s missing"%ROOT_DATA_DIR)
class TestOverViewReport(unittest.TestCase):

    def setUp(self):
        self.input_file = op.join(ROOT_DATA_DIR, "dacetoxidans", "2530923",
            "0005_0006.subreadset.xml")
        self.report = overview.run(self.input_file)
        log.info(pformat(self.report.to_dict()))

    def test_smoke(self):
        """Basic functionality test"""
        self.assertIsNotNone(self.report)
        d = self.report.to_dict()
        self.assertTrue(isinstance(d, dict))
        self.assertTrue('attributes' in d)

    def test_nmovies_attribute(self):
        id_ = 'nmovies'
        a = self.report.get_attribute_by_id(id_)
        self.assertIsNotNone(a)
        self.assertTrue(a.value, 2)

    def test_ncells_attribute(self):
        id_ = 'ncells'
        a = self.report.get_attribute_by_id(id_)
        self.assertEqual(a.value, 2)


class TestOverviewReportIntegration(unittest.TestCase):
    def setUp(self):
        self.input_file = op.join(ROOT_DATA_DIR, "dacetoxidans", "2530923",
            "0005_0006.subreadset.xml")
        t = tempfile.NamedTemporaryFile(delete=False, suffix="overview_report.json")
        t.close()
        self.report_json = t.name

    def test_basic(self):

        cmd = "overview_report --debug {i} {o}".format(i=self.input_file,
                                                          o=self.report_json)
        rcode = run_backticks(cmd)
        self.assertEqual(rcode, 0)


class TestOverviewToolContract(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.overview"
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        op.join(ROOT_DATA_DIR,"dacetoxidans","2530923","0005_0006.subreadset.xml")
    ]
