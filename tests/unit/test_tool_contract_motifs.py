
"""
Tests for end-to-end tool contract support in pbreports.report.motifs
"""

import unittest
import os.path

import pbcommand.testkit

from base_test_case import _get_root_data_dir, skip_if_data_dir_not_present

ROOT_DIR = _get_root_data_dir()

@skip_if_data_dir_not_present
class TestPbreportMotifs(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(ROOT_DIR, "kinetics")
    DRIVER_BASE = "python -m pbreports.report.motifs "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        os.path.join(DATA, "motifs.gff.gz"),
        os.path.join(DATA, "motif_summary.csv"),
    ]
    TASK_OPTIONS = {}


if __name__ == "__main__":
    unittest.main()
