
# TODO(nechols)(2016-01-21): test output

"""
Tests for end-to-end tool contract support in pbreports.report.isoseq_*
"""

import unittest
import os.path

import pbcommand.testkit

from base_test_case import LOCAL_DATA

DATA = os.path.join(LOCAL_DATA, "isoseq")

class TestPbreportIsoseqClassify(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.isoseq_classify "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        os.path.join(DATA, "isoseq_flnc.fasta"),
        os.path.join(DATA, "isoseq_classify_summary.txt"),
    ]
    TASK_OPTIONS = {}


class TestPbreportIsoseqCluster(pbcommand.testkit.PbTestApp):
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
