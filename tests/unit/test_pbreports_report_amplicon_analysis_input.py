import os
import logging
import tempfile
import unittest
import json
from pprint import pformat

from pbcommand.models.report import Report
import pbcommand.testkit

from pbreports.report.amplicon_analysis_input import run_to_report
from base_test_case import LOCAL_DATA, run_backticks, validate_report_complete

log = logging.getLogger(__name__)

_NAME = 'amplicon_analysis_input'
DATA_DIR = os.path.join(LOCAL_DATA, _NAME)


class TestLongAmpliconAnalysisPcrReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        summary_name = 'amplicon_analysis_input.csv'
        cls.csv_file = os.path.join(DATA_DIR, summary_name)
        log.info("Using {s}".format(s=cls.csv_file))

    def test_make_report(self):
        report = run_to_report(self.csv_file)
        validate_report_complete(self, report)
        self.assertTrue(isinstance(report, Report))
        log.info(pformat(report.to_dict()))
        self.assertIsNotNone(report)
        for j in range(len(report.tables[0].columns[0].values)):
            total = 0
            for col in report.tables[0].columns:
                if col.id.endswith("_pct"):
                    total += col.values[j]
            self.assertAlmostEqual(total, 1.0, places=3)

    def test_integration(self):
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        t.close()
        report_json = t.name
        exe = "amplicon_analysis_input_report"
        cmd = "{e} --debug {s} {r}".format(e=exe,
                                           s=self.csv_file,
                                           r=report_json)
        exit_code = run_backticks(cmd)
        self.assertEqual(exit_code, 0)
        with open(report_json, 'r') as f:
            d = json.loads(f.read())
        self.assertIsNotNone(d)
        # cleanup
        if os.path.exists(report_json):
            os.remove(report_json)


class TestAmpliconAnalysisInput(pbcommand.testkit.PbTestApp):
    name = 'amplicon_analysis_input.csv'
    csv_file_name = os.path.join(LOCAL_DATA, "amplicon_analysis_input", name)
    t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    t.close()
    report_json = t.name
    DRIVER_BASE = "python -m pbreports.report.amplicon_analysis_input "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = False
    INPUT_FILES = [csv_file_name]
    OUTPUT_FILES = [report_json]
    TASK_OPTIONS = {}
