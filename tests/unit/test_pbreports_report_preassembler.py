import os
import unittest
import logging
import pprint

from pbreports.report.preassembly import to_report

from base_test_case import _get_root_data_dir

ROOT_DATA_DIR = _get_root_data_dir()
log = logging.getLogger(__name__)

_DATA_DIR = os.path.join(ROOT_DATA_DIR, 'preassembly')
if not os.path.exists(_DATA_DIR):
    raise IOError("Unable to find data directory {d}".format(d=_DATA_DIR))


class TestPreassemblyReport(unittest.TestCase):

    def test_basic(self):
        """Basic smoke test to see if report generation is functioning"""
        filtered_reads = os.path.join(_DATA_DIR, 'filtered_subreads.fasta')
        filtered_longreads = os.path.join(_DATA_DIR, 'filtered_longreads.fasta')
        corrected_reads = os.path.join(_DATA_DIR, 'corrected.fasta')
        length_cutoff = 6000
        report = to_report(filtered_reads, filtered_longreads, corrected_reads, length_cutoff=length_cutoff)
        log.info("Generated report: " + str(report))
        log.info(pprint.pformat(report.to_dict()))
        self.assertIsNotNone(report)
