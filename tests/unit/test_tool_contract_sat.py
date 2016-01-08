
"""
Tests for end-to-end tool contract support in pbreports.report.sat
"""

import unittest
import os.path

import pbcommand.testkit

from base_test_case import _get_root_data_dir

ROOT_DIR = _get_root_data_dir()

@unittest.skipUnless(os.path.isdir(ROOT_DIR), "%s not available" % ROOT_DIR)
class TestPbreportsSat(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(ROOT_DIR, 'sat')
    DRIVER_BASE = "python -m pbreports.report.sat "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        os.path.join(DATA, "aligned_reads.xml"),
        os.path.join(DATA, 'variants_report.json'),
        os.path.join(DATA, 'mapping_stats_report.json'),
    ]
    TASK_OPTIONS = {}


if __name__ == "__main__":
    unittest.main()
