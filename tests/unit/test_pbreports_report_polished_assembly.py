import os
import logging
import traceback
import json
import unittest
import tempfile
import shutil
import sys

from pbcore.util.Process import backticks

from pbreports.report.polished_assembly import (make_polished_assembly_report,
                                                _get_att_max_contig_length,
                                                _get_att_n_50_contig_length,
                                                _get_att_sum_contig_lengths)
from pbreports.serializers import dict_to_report

from base_test_case import ROOT_DATA_DIR, skip_if_data_dir_not_present

log = logging.getLogger(__name__)


class TestPolishedAssemblyRpt(unittest.TestCase):

    def setUp(self):
        """
        Before *every* test
        """
        self._output_dir = tempfile.mkdtemp(suffix="control")

    def tearDown(self):
        """
        After *every* test
        """
        if os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_make_polished_assembly_report_io(self):
        """
        IOError if fasta does not exist
        """
        with self.assertRaises(IOError):
            make_polished_assembly_report('foo', 'bar', 'baz', self._output_dir)

    @skip_if_data_dir_not_present
    def test_make_polished_assembly_report(self):
        """
        Test the attributes of the report
        """
        fastq = os.path.join(ROOT_DATA_DIR, 'polished_assembly', 'polished_assembly.fastq.gz')
        gff = os.path.join(ROOT_DATA_DIR, 'polished_assembly', 'alignment_summary.gff')
        make_polished_assembly_report('rpt.json', gff, fastq, self._output_dir)
         # deserialize report
        s = None
        with open(os.path.join(self._output_dir, 'rpt.json'), 'r') as f:
            s = json.load(f)

        report = dict_to_report(s)

        polished_contigs = self._get_att('polished_contigs', report.attributes)
        self.assertEqual(13, polished_contigs.value)

        max_contig_length = self._get_att('max_contig_length', report.attributes)
        self.assertEqual(7070936, max_contig_length.value)

        n_50_contig_length = self._get_att('n_50_contig_length', report.attributes)
        self.assertEqual(4204013, n_50_contig_length.value)

        sum_contig_length = self._get_att('sum_contig_lengths', report.attributes)
        self.assertEqual(28553574, sum_contig_length.value)

    def test_get_att_sum_contig_length(self):
        self.assertEqual(0, _get_att_sum_contig_lengths([]).value)

    def test_get_att_max_contig_length(self):
        self.assertEqual(0, _get_att_max_contig_length([]).value)

    def test_get_att_n_50_contig_length(self):
        self.assertEqual(0, _get_att_n_50_contig_length([]).value)

    def _get_att(self, id_, list_of_atts):
        for a in list_of_atts:
            log.debug(a.id)
            if a.id == id_:
                return a
        raise ValueError('Did not find expected attribute "{a}" in list'.format(a=id_))

    @skip_if_data_dir_not_present
    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """
        fastq = os.path.join(ROOT_DATA_DIR, 'polished_assembly', 'polished_assembly.fastq.gz')
        gff = os.path.join(ROOT_DATA_DIR, 'polished_assembly', 'alignment_summary.gff')
        r = os.path.join(self._output_dir, 'rpt.json')
        cmd = 'pbreport polished-assembly {g} {f} {r}'.format(g=gff, f=fastq, r=r)
        log.info(cmd)

        o, c, m = backticks(cmd)

        if c is not 0:
            log.error(m)
            log.error(o)
            sys.stderr.write(str(m))
            print(m)

        s = None
        with open(os.path.join(self._output_dir, 'rpt.json'), 'r') as f:
            s = json.load(f)

        report = dict_to_report(s)
        self.assertEqual(4, len(report.attributes))
