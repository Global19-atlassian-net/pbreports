import os
import logging
import tempfile
import unittest
import json
import nose
from pprint import pformat

from pbcommand.models.report import Report

from pbreports.report.amplicon_analysis_consensus import run_to_report
from base_test_case import LOCAL_DATA, run_backticks, validate_report_complete

log = logging.getLogger(__name__)

_NAME = 'amplicon_analysis_consensus'
_EMPTY = 'amplicon_analysis_consensus_empty'
_SINGLE = 'amplicon_analysis_consensus_single'
DATA_DIR = os.path.join(LOCAL_DATA, _NAME)
EMPTY_DIR = os.path.join(LOCAL_DATA, _EMPTY)
SINGLE_DIR = os.path.join(LOCAL_DATA, _SINGLE)


class TestLongAmpliconAnalysisReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        name = 'amplicon_analysis_summary.csv'
        cls.file_name = os.path.join(DATA_DIR, name)
        log.info("Using {f}".format(f=cls.file_name))

    def test_basic(self):
        report = run_to_report(self.file_name)
        validate_report_complete(self, report)
        self.assertTrue(isinstance(report, Report))
        log.info(pformat(report.to_dict()))
        self.assertIsNotNone(report)


class TestIntegrationLongAmpliconAnalysisReport(TestLongAmpliconAnalysisReport):

    def test_basic(self):
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        t.close()
        report_json = t.name
        exe = "amplicon_analysis_consensus_report"
        cmd = "{e} --debug {csv} {r}".format(e=exe, csv=self.file_name,
                                             r=report_json)

        exit_code = run_backticks(cmd)
        self.assertEqual(exit_code, 0)

        with open(report_json, 'r') as f:
            d = json.loads(f.read())

        self.assertIsNotNone(d)

        # cleanup
        if os.path.exists(report_json):
            os.remove(report_json)


class TestEmptyInputFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        name = 'amplicon_analysis_summary.csv'
        cls.file_name = os.path.join(EMPTY_DIR, name)
        log.info("Using {f}".format(f=cls.file_name))

    # NOTE: we can't easily run the report argparse except via running
    #    it from the command-line, and back-ticks doesn't capture errors
    #    only return codes.
    def test_basic(self):
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        t.close()
        report_json = t.name
        exe = "amplicon_analysis_consensus_report"
        cmd = "{e} --debug {csv} {r}".format(e=exe, csv=self.file_name,
                                             r=report_json)
        exit_code = run_backticks(cmd, 1)
        # Assert the job failed
        self.assertEqual(exit_code, 1)


class TestSingleEntryInputFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        name = 'amplicon_analysis_summary.csv'
        cls.file_name = os.path.join(SINGLE_DIR, name)
        log.info("Using {f}".format(f=cls.file_name))

    def test_basic(self):
        report = run_to_report(self.file_name)
        self.assertTrue(isinstance(report, Report))
        log.info(pformat(report.to_dict()))
        self.assertIsNotNone(report)
