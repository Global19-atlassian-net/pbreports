import traceback
import unittest
import tempfile
import logging
import shutil
import json
import os.path as op
import os
import sys

from pbcommand.pb_io.report import dict_to_report
from pbcore.util.Process import backticks

from pbreports.report.polished_assembly import (make_polished_assembly_report,
                                                _get_att_max_contig_length,
                                                _get_att_n_50_contig_length,
                                                _get_att_sum_contig_lengths)

from base_test_case import (LOCAL_DATA, ROOT_DATA_DIR, AttributesTestBase,
    skip_if_data_dir_not_present)

log = logging.getLogger(__name__)


class _BaseTestCase(AttributesTestBase, unittest.TestCase):
    TEST_VALUES = {}
    FASTQ = None
    GFF = None

    def setUp(self):
        """
        Before *every* test
        """
        self._output_dir = tempfile.mkdtemp(suffix="control")

    def tearDown(self):
        """
        After *every* test
        """
        if op.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_make_polished_assembly_report_io(self):
        """
        IOError if fasta does not exist
        """
        with self.assertRaises(IOError):
            make_polished_assembly_report('foo', 'bar', 'baz', self._output_dir)

    def test_make_polished_assembly_report(self):
        """
        Test the attributes of the report
        """
        make_polished_assembly_report('rpt.json', self.GFF, self.FASTQ, self._output_dir)
        # deserialize report
        s = None
        with open(op.join(self._output_dir, 'rpt.json'), 'r') as f:
            s = json.load(f)
        self.report = dict_to_report(s)
        self._test_attribute("polished_contigs")
        self._test_attribute("max_contig_length")
        self._test_attribute("n_50_contig_length")
        self._test_attribute("sum_contig_lengths")

    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """
        r = op.join(self._output_dir, 'rpt.json')
        cmd = 'python -m pbreports.report.polished_assembly {g} {f} {r}'.format(g=self.GFF, f=self.FASTQ, r=r)
        log.info(cmd)
        o, c, m = backticks(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            sys.stderr.write(str(m))
            print(m)
        s = None
        with open(op.join(self._output_dir, 'rpt.json'), 'r') as f:
            s = json.load(f)
        report = dict_to_report(s)
        self.assertEqual(4, len(report.attributes))


class TestPolishedAssemblyReport(_BaseTestCase):
    TEST_VALUES = {
        "polished_contigs": 8,
        "max_contig_length": 15566,
        "n_50_contig_length": 12197,
        "sum_contig_lengths": 40640,
    }
    GFF = op.join(LOCAL_DATA, "polished_assembly", "alignment_summary.gff")
    FASTQ = op.join(LOCAL_DATA, "polished_assembly", "assembly.fastq.gz")


class TestPolishedAssemblyReportQuiver(TestPolishedAssemblyReport):
    FASTQ = op.join(LOCAL_DATA, "polished_assembly", "assembly_quiver.fastq.gz")

    def test_make_polished_assembly_report_io(self):
        """
        IOError if fasta does not exist
        """
        with self.assertRaises(IOError):
            make_polished_assembly_report('foo', 'bar', 'baz', self._output_dir)

    def test_get_att_sum_contig_length(self):
        self.assertEqual(0, _get_att_sum_contig_lengths([]).value)

    def test_get_att_max_contig_length(self):
        self.assertEqual(0, _get_att_max_contig_length([]).value)

    def test_get_att_n_50_contig_length(self):
        self.assertEqual(0, _get_att_n_50_contig_length([]).value)


@skip_if_data_dir_not_present
class TestPolishedAssemblyReportBig(_BaseTestCase):
    TEST_VALUES = {
        "polished_contigs": 13,
        "max_contig_length": 7070936,
        "n_50_contig_length": 4204013,
        "sum_contig_lengths": 28553574,
    }
    FASTQ = op.join(ROOT_DATA_DIR, 'polished_assembly', 'polished_assembly.fastq.gz')
    GFF = op.join(ROOT_DATA_DIR, 'polished_assembly', 'alignment_summary.gff')
