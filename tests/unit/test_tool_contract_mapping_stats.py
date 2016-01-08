
"""
Tests for end-to-end tool contract support in pbreports.report.mapping_stats
"""

import unittest
import os.path

import pbcommand.testkit
import pbcore.data


class TestPbreportMappingStats(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.mapping_stats "
    REQUIRES_PBCORE = True
    INPUT_FILES = [pbcore.data.getBamAndCmpH5()[0]]
    TASK_OPTIONS = {}


@unittest.skip("PLEASE MAKE TEST DATA")
class TestPbreportMappingStatsCCS(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.mapping_stats_ccs "
    INPUT_FILES = [] # FIXME pending blasr bug fix


if __name__ == "__main__":
    unittest.main()
