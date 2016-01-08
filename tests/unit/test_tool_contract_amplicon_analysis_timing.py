
"""
Tests for end-to-end tool contract support.  Any report tool that has emit and
resolve functions should have a class here.
"""

import unittest
import os.path
import tempfile

import pbcommand.testkit

from base_test_case import _get_root_data_dir

ROOT_DIR = _get_root_data_dir()
_NAME = 'amplicon_analysis_timing'
DATA_DIR = os.path.join(ROOT_DIR, _NAME)


@unittest.skipUnless(os.path.isdir(ROOT_DIR), "%s not available" % ROOT_DIR)
class TestAmpliconAnalysisTiming(pbcommand.testkit.PbTestApp):
    log_file_name = 'amplicon_analysis.log'
    log_file = os.path.join(DATA_DIR, log_file_name)
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
