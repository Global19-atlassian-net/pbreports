
"""
Tests for end-to-end tool contract support in pbreports.report.variants
"""

import unittest
import os.path

import pbcommand.testkit

from base_test_case import _get_root_data_dir

ROOT_DIR = _get_root_data_dir()
ECOLI = 'ecoliK12_pbi_March2013'


@unittest.skipUnless(os.path.isdir(ROOT_DIR), "%s not available" % ROOT_DIR)
class TestPbreportVariants(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(ROOT_DIR, 'variants')
    DRIVER_BASE = "python -m pbreports.report.variants"
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        os.path.join(DATA, ECOLI, "sequence", "ecoliK12_pbi_March2013.fasta"),
        os.path.join(DATA, "alignment_summary.gff"),
        os.path.join(DATA, 'variants.gff.gz'),
    ]
    TASK_OPTIONS = {
        "pbreports.task_options.max_contigs": 25,
        "pbreports.task_options.dpi": 60,
        "pbreports.task_options.dumpdata": True, 
    }


if __name__ == "__main__":
    unittest.main()
