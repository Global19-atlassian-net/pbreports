import os
import unittest
import logging
import pprint

import pbcommand.testkit

from pbreports.report.preassembly import to_report

from base_test_case import LOCAL_DATA

_DATA_DIR = os.path.join(LOCAL_DATA, 'preassembly')

log = logging.getLogger(__name__)

filtered_reads = os.path.join(_DATA_DIR, 'filtered_subreads.fasta')
filtered_longreads = os.path.join(_DATA_DIR, 'filtered_longreads.fasta')
corrected_reads = os.path.join(_DATA_DIR, 'corrected.fasta')
length_cutoff = 60


class TestPreassemblyReport(unittest.TestCase):

    def test_basic(self):
        """Basic smoke test to see if report generation is functioning"""
        report = to_report(filtered_reads, filtered_longreads, corrected_reads,
                           length_cutoff=length_cutoff)
        log.info("Generated report: " + str(report))
        log.info(pprint.pformat(report.to_dict()))
        self.assertIsNotNone(report)


class TestPolishedAssembly(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.preassembly "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        filtered_reads,
        filtered_longreads,
        corrected_reads
    ]
    TASK_OPTIONS = {
        "pbreports.task_options.length_cutoff": length_cutoff
    }
