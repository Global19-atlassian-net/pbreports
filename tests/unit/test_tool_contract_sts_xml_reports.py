
"""
Tests for end-to-end tool contract support.  Any report tool that has emit and
resolve functions should have a class here.
"""

import unittest
import os.path

import pbcommand.testkit

from pbcore.data import datasets as data


class TestLoadingReport(pbcommand.testkit.PbTestApp):
    MAX_NPROC = 12
    RESOLVED_NPROC = 1
    DATA = pbtestdata.get_file("subreads-sequel")
    DRIVER_BASE = "python -m pbreports.report.loading_xml "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [DATA]
    TASK_OPTIONS = {}


class TestAdapterReport(pbcommand.testkit.PbTestApp):
    MAX_NPROC = 12
    RESOLVED_NPROC = 1
    DATA = data.getXmlWithStats()
    DRIVER_BASE = "python -m pbreports.report.adapter_xml "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [DATA]
    TASK_OPTIONS = {}


class TestFilterStatsReport(pbcommand.testkit.PbTestApp):
    MAX_NPROC = 12
    RESOLVED_NPROC = 1
    DATA = data.getXmlWithStats()
    DRIVER_BASE = "python -m pbreports.report.filter_stats_xml "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [DATA]
    TASK_OPTIONS = {}


if __name__ == "__main__":
    unittest.main()
