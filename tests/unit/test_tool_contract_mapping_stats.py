
"""
Tests for end-to-end tool contract support in pbreports.report.mapping_stats
"""

import unittest
import os.path

import pbcommand.testkit
import pbcore.data

from base_test_case import LOCAL_DATA


class TestPbreportMappingStats(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.mapping_stats "
    REQUIRES_PBCORE = True
    INPUT_FILES = [pbcore.data.getBamAndCmpH5()[0]]
    TASK_OPTIONS = {}


class TestPbreportMappingStatsCCS(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.mapping_stats_ccs "
    REQUIRES_PBCORE = True
    INPUT_FILES = [os.path.join(LOCAL_DATA, "mapping_stats_ccs",
        "aligned.consensusalignmentset.xml")]
    TASK_OPTIONS = {}


if __name__ == "__main__":
    unittest.main()
