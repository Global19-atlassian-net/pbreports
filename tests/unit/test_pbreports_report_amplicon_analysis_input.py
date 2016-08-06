import os
import logging
import tempfile
import unittest
import json
from pprint import pformat

from pbcommand.models.report import Report

from pbreports.report.amplicon_analysis_input import (run_to_report,
                                                      parse_summary,
                                                      parse_mappings,
                                                      tabulate_results)
from base_test_case import LOCAL_DATA, run_backticks, validate_report_complete

log = logging.getLogger(__name__)

_NAME = 'amplicon_analysis_input'
DATA_DIR = os.path.join(LOCAL_DATA, _NAME)


class TestLongAmpliconAnalysisPcrReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        summary_name = 'amplicon_analysis_summary.csv'
        cls.summary_file = os.path.join(DATA_DIR, summary_name)
        zmw_name = 'amplicon_analysis_zmws.json'
        cls.zmw_file = os.path.join(DATA_DIR, zmw_name)
        log.info("Using {s} and {z}".format(
            s=cls.summary_file, z=cls.zmw_file))

    def test_process_files(self):
        s = parse_summary(self.summary_file)
        c = parse_mappings(self.zmw_file)
        d = tabulate_results(s, c)
        for bc_id, fields in d.iteritems():
            total = 0
            for k, v in fields.iteritems():
                if k.endswith("_pct"):
                    total += v
            self.assertAlmostEqual(total, 1.0, places=3)

    def test_make_report(self):
        report = run_to_report(self.summary_file, self.zmw_file)
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
        cmd = "{e} --debug {s} {z} {r}".format(e=exe,
                                               s=self.summary_file,
                                               z=self.zmw_file,
                                               r=report_json)
        exit_code = run_backticks(cmd)
        self.assertEqual(exit_code, 0)
        with open(report_json, 'r') as f:
            d = json.loads(f.read())
        self.assertIsNotNone(d)
        # cleanup
        if os.path.exists(report_json):
            os.remove(report_json)
