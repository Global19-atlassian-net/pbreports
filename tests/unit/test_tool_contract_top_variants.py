
"""
Tests for end-to-end tool contract support.  Any report tool that has emit and
resolve functions should have a class here.
"""

import unittest
import os.path

import pbcommand.testkit

from base_test_case import _get_root_data_dir

ROOT_DIR = _get_root_data_dir()
ECOLI = 'ecoliK12_pbi_March2013'


@unittest.skipUnless(os.path.isdir(ROOT_DIR), "%s not available" % ROOT_DIR)
class TestPbreportTopVariants(pbcommand.testkit.PbTestApp):
    from pbreports.report.top_variants import Constants
    DATA = os.path.join(ROOT_DIR, "topvariants")
    DRIVER_BASE = "python -m pbreports.report.top_variants "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        os.path.join(DATA, "variants.gff.gz"),
        os.path.join(DATA, ECOLI, "sequence", "ecoliK12_pbi_March2013.fasta"),
    ]
    TASK_OPTIONS = {
        Constants.HOW_MANY_ID: Constants.HOW_MANY_DEFAULT,
        Constants.BATCH_SORT_SIZE_ID: Constants.BATCH_SORT_SIZE_DEFAULT,
    }


if __name__ == "__main__":
    unittest.main()
