
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
class TestSummarizeCoverage(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(ROOT_DIR, 'summarize_coverage')
    DRIVER_BASE = "python -m pbreports.report.summarize_coverage.summarize_coverage "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        os.path.join(DATA, "aligned_reads.cmp.h5"),
        os.path.join(DATA,
                     '/pbi/dept/secondary/siv/references/ecoliK12_pbi_March2013'
                     '/sequence/ecoliK12_pbi_March2013.fasta'),
    ]
    TASK_OPTIONS = {}


if __name__ == "__main__":
    unittest.main()
