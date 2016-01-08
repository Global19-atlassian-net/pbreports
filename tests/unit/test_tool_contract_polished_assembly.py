
"""
Tests for end-to-end tool contract support.  Any report tool that has emit and
resolve functions should have a class here.
"""

import unittest
import os.path

import pbcommand.testkit

from base_test_case import _get_root_data_dir

ROOT_DIR = _get_root_data_dir()
FASTQ = os.path.join(ROOT_DIR, 'polished_assembly',
                     'polished_assembly.fastq')
GFF = os.path.join(ROOT_DIR, 'polished_assembly', 'alignment_summary.gff')


@unittest.skipUnless(os.path.isdir(ROOT_DIR), "%s not available" % ROOT_DIR)
class TestPolishedAssembly(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(ROOT_DIR, 'summarize_coverage')
    DRIVER_BASE = "python -m pbreports.report.polished_assembly "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        GFF,
        FASTQ,
    ]
    TASK_OPTIONS = {}


if __name__ == "__main__":
    unittest.main()
