import os
import logging
import tempfile
import unittest
import json
from pprint import pformat

from pbreports.model.model import Report
from pbreports.report.amplicon_analysis_timing import run_to_report
from base_test_case import ROOT_DATA_DIR, run_backticks

log = logging.getLogger(__name__)

_NAME = 'amplicon_analysis_timing'
DATA_DIR = os.path.join(ROOT_DATA_DIR, _NAME)


class TestAmpliconAnalysisTimingReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        log_file_name = 'amplicon_analysis.log'
        cls.log_file = os.path.join(DATA_DIR, log_file_name)
        log.info("Using {l}".format(l=cls.log_file))

    def test_basic(self):
        report = run_to_report(self.log_file)
        self.assertTrue(isinstance(report, Report))
        log.info(pformat(report.to_dict()))
        self.assertIsNotNone(report)


class TestIntegrationAmpliconAnalysisTimingReport(TestAmpliconAnalysisTimingReport):

    def test_basic(self):
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        t.close()
        report_json = t.name
        exe = "amplicon_analysis_timing_report"
        cmd = "{e} --debug {l} {r}".format(e=exe,
                                           l=self.log_file,
                                           r=report_json)
        exit_code = run_backticks(cmd)
        self.assertEqual(exit_code, 0)

        with open(report_json, 'r') as f:
            d = json.loads(f.read())

        self.assertIsNotNone(d)

        # cleanup
        if os.path.exists(report_json):
            os.remove(report_json)
