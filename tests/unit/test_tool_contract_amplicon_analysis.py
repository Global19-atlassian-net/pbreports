
"""
Tests for end-to-end tool contract support.  Any amplicon analysis report tool
that has emit and resolve functions should have a class here.
"""

import unittest
import os.path
import tempfile

import pbcommand.testkit

from base_test_case import LOCAL_DATA


class TestAmpliconAnalysisConsensus(pbcommand.testkit.PbTestApp):
    name = 'amplicon_analysis_summary.csv'
    csv_file_name = os.path.join(LOCAL_DATA, "amplicon_analysis_consensus",
                                 name)
    t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    t.close()
    report_json = t.name
    DRIVER_BASE = "python -m pbreports.report.amplicon_analysis_consensus "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = False
    INPUT_FILES = [
        csv_file_name,
    ]
    OUTPUT_FILES = [report_json]
    TASK_OPTIONS = {}


class TestAmpliconAnalysisInput(pbcommand.testkit.PbTestApp):
    name = 'amplicon_analysis_summary.csv'
    csv_file_name = os.path.join(LOCAL_DATA, "amplicon_analysis_input", name)
    zmw_name = 'amplicon_analysis_zmws.json'
    zmw_file = os.path.join(LOCAL_DATA, "amplicon_analysis_input", zmw_name)
    t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    t.close()
    report_json = t.name
    DRIVER_BASE = "python -m pbreports.report.amplicon_analysis_input "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = False
    INPUT_FILES = [
        csv_file_name,
        zmw_file,
    ]
    OUTPUT_FILES = [report_json]
    TASK_OPTIONS = {}


class TestAmpliconAnalysisTiming(pbcommand.testkit.PbTestApp):
    DATA_DIR = os.path.join(LOCAL_DATA, "amplicon_analysis_timing")
    log_file = os.path.join(DATA_DIR, "amplicon_analysis.log")
    t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    t.close()
    report_json = t.name
    DRIVER_BASE = "python -m pbreports.report.amplicon_analysis_timing "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = False
    INPUT_FILES = [
        log_file,
    ]
    OUTPUT_FILES = [report_json]
    TASK_OPTIONS = {}


if __name__ == "__main__":
    unittest.main()
