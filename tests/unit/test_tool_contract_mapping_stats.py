
"""
Tests for end-to-end tool contract support in pbreports.report.mapping_stats
"""

import unittest
import os.path

import pbcommand.testkit

from base_test_case import _get_root_data_dir

ROOT_DIR = _get_root_data_dir()
ECOLI = 'ecoliK12_pbi_March2013'


@unittest.skipUnless(os.path.isdir(ROOT_DIR), "%s not available" % ROOT_DIR)
class TestPbreportMappingStats(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(ROOT_DIR, 'io')
    DRIVER_BASE = "python -m pbreports.report.mapping_stats "
    REQUIRES_PBCORE = True
    INPUT_FILES = [ os.path.join(DATA, "lambda_aligned.xml") ]
    TASK_OPTIONS = {}


@unittest.skip("PLEASE MAKE TEST DATA")
class TestPbreportMappingStatsCCS(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(ROOT_DIR, 'io')
    DRIVER_BASE = "python -m pbreports.report.mapping_stats_ccs "
    INPUT_FILES = [] # FIXME pending blasr bug fix


if __name__ == "__main__":
    unittest.main()
