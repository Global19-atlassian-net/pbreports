
"""
Tests for end-to-end tool contract support.  Any report tool that has emit and
resolve functions should have a class here.
"""

import unittest
import os.path

import pbcommand.testkit

from base_test_case import _get_root_data_dir

ROOT_DIR = _get_root_data_dir()
READ_FAS = os.path.join(ROOT_DIR, 'preassembly',
                        'filtered_subreads.fasta')
LONG_FAS = os.path.join(ROOT_DIR, 'preassembly',
                        'filtered_longreads.fasta')
CORR_FAS = os.path.join(ROOT_DIR, 'preassembly',
                        'corrected.fasta')
LEN_CUT = 6000


@unittest.skipUnless(os.path.isdir(ROOT_DIR), "%s not available" % ROOT_DIR)
class TestPolishedAssembly(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.preassembly "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        READ_FAS,
        LONG_FAS,
        CORR_FAS,
    ]
    TASK_OPTIONS = {
        "pbreports.task_options.length_cutoff": LEN_CUT
    }


if __name__ == "__main__":
    unittest.main()
