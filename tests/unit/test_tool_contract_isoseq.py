
"""
Tests for end-to-end tool contract support in pbreports.report.isoseq_*
"""

import unittest
import os.path

import pbcommand.testkit

from base_test_case import _get_root_data_dir

ROOT_DIR = _get_root_data_dir()


@unittest.skipUnless(os.path.isdir(ROOT_DIR), "%s not available" % ROOT_DIR)
class TestPbreportIsoseqClassify(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(ROOT_DIR, "isoseq")
    DRIVER_BASE = "python -m pbreports.report.isoseq_classify "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        os.path.join(DATA, "isoseq_flnc.fasta"),
        os.path.join(DATA, "isoseq_classify_summary.txt"),
    ]
    TASK_OPTIONS = {}


@unittest.skipUnless(os.path.isdir(ROOT_DIR), "%s not available" % ROOT_DIR)
class TestPbreportIsoseqCluster(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(ROOT_DIR, "isoseq")
    DRIVER_BASE = "python -m pbreports.report.isoseq_cluster "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        os.path.join(DATA, "isoseq_flnc.fasta"),
        os.path.join(DATA, "isoseq_cluster_summary.txt")
    ]
    TASK_OPTIONs = {}


if __name__ == "__main__":
    unittest.main()

