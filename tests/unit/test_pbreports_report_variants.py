
# TODO(nechols)(2016-02-10): refactor so this doesn't need to generate the
# report every time (which slows down the test with large data)

from unittest import SkipTest
import traceback
import tempfile
import unittest
import logging
import shutil
import json
import os.path as op

from pbcommand.models.report import PbReportError
import pbcommand.testkit
from pbcore.util.Process import backticks
from pbcore.io import ReferenceSet

import pbtestdata

from pbreports.util import openReference
from pbreports.util import get_top_contigs_from_ref_entry
from pbreports.report.variants import (make_variants_report, _extract_alignment_summ_data,
                                       LENGTH, GAPS, ERR, COV,
                                       _append_variants_gff_data,
                                       _get_consensus_table_and_attributes,
                                       _ref_ids_ordered_by_len,
                                       _create_variants_plot_grp, _create_bars, _get_legend_file)

from base_test_case import _get_root_data_dir, run_backticks, \
    skip_if_data_dir_not_present, LOCAL_DATA, validate_report_complete

VARIANTS_DATA = op.join(_get_root_data_dir(), 'variants')

DT = 'Desulfurobacterium_thermolithotrophum_DSM11699_gDNA'

log = logging.getLogger(__name__)


class BaseTestCase(object):

    def setUp(self):
        """
        Before *every* test
        """
        self._output_dir = tempfile.mkdtemp(suffix="variants")

    def tearDown(self):
        """
        After *every* test
        """
        if op.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def _get_reference_entry(self):
        return openReference(self.REFERENCE)

    def _get_reference_fasta(self):
        return self.REFERENCE

    def test_make_variants_report_invalid_input_files(self):
        """
        inputs cannot be null or non-existent
        """

        # als tests
        with self.assertRaises(PbReportError):
            make_variants_report(None, self.VARIANTS_GFF, self.REFERENCE,
                                 'foo.json', 1, self._output_dir, '1', False)
        with self.assertRaises(IOError):
            make_variants_report('foo', self.VARIANTS_GFF, self.REFERENCE,
                                 'foo.json', 1, self._output_dir, '1', False)

        # variants tests
        with self.assertRaises(PbReportError):
            make_variants_report(self.ALIGNMENT_SUMMARY, None, self.REFERENCE,
                                 'foo.json', 1, self._output_dir, '1', False)
        with self.assertRaises(IOError):
            make_variants_report(self.ALIGNMENT_SUMMARY, 'foo',
                                 self.REFERENCE, 'foo.json', 1, self._output_dir, '1', False)

        # ref tests
        with self.assertRaises(PbReportError):
            make_variants_report(self.ALIGNMENT_SUMMARY, self.VARIANTS_GFF,
                                 None, 'foo.json', 1, self._output_dir, '1', False)
        with self.assertRaises(IOError):
            make_variants_report(self.ALIGNMENT_SUMMARY, self.VARIANTS_GFF,
                                 'foo', 'foo.json', 1, self._output_dir, '1', False)

    def test_extract_alignment_summ_data(self):
        """
        Test the dicts returned from parsing the alignment_summary gff
        """
#        top_contigs = get_top_contigs(ref, 2)

        top_contigs = get_top_contigs_from_ref_entry(
            self._get_reference_entry(), 2)

        ref_data, contig_variants = _extract_alignment_summ_data(
            self.ALIGNMENT_SUMMARY, top_contigs)
        self.assertEqual(1, len(ref_data))

        results = ref_data[self.CONTIG_ID]
        self.assertEqual(self.TEST_VALUES["contig_len"], results[LENGTH])
        self.assertEqual(0, results[ERR])

        self.assertEqual(1, len(contig_variants))

    def test_get_consensus_attributes(self):
        """
        Test the data in the table object and the attributes
        """
        top_contigs = get_top_contigs_from_ref_entry(
            self._get_reference_entry(), 2)

        ref_data = _extract_alignment_summ_data(
            self.ALIGNMENT_SUMMARY, top_contigs)[0]
        self.assertEqual(1, len(ref_data))

        results = ref_data[self.CONTIG_ID]
        self.assertEqual(self.TEST_VALUES["contig_len"], results[LENGTH])
        self.assertEqual(0, results[ERR])

        _append_variants_gff_data(ref_data, self.VARIANTS_GFF)

        table, attributes = _get_consensus_table_and_attributes(
            ref_data, self._get_reference_entry())
        self.assertEqual(5, len(attributes))

        def __get_att_val(_id, atts):
            for a in atts:
                if a.id == _id:
                    return a.value

        self.assertEqual(self.TEST_VALUES["contig_len"],
                         __get_att_val('mean_contig_length', attributes))
        self.assertAlmostEqual(self.TEST_VALUES["bases_called"],
                               __get_att_val('weighted_mean_bases_called',
                                             attributes), places=4)
        self.assertAlmostEqual(self.TEST_VALUES["concordance"],
                               __get_att_val('weighted_mean_concordance',
                                             attributes),
                               places=4)
        self.assertAlmostEqual(self.TEST_VALUES["coverage"],
                               __get_att_val('weighted_mean_coverage',
                                             attributes),
                               places=2)
        self.assertEqual(self.CONTIG_ID,
                         __get_att_val('longest_contig_name',
                                       attributes))


class TestVariantsReport(BaseTestCase, unittest.TestCase):
    """
    Base test case using local lambda data.
    """
    CONTIG_ID = "lambda_NEB3011"
    REFERENCE = pbtestdata.get_file("lambda-fasta")
    ALIGNMENT_SUMMARY = pbtestdata.get_file("consensus-summary-gff")
    VARIANTS_GFF = pbtestdata.get_file("variants-gff")
    TEST_VALUES = {
        "contig_len": 48502,
        "bases_called": 1.0,
        "concordance": 0.999897,
        "coverage": 282.88,
        "n_gff_err_1": 0,
        "n_gff_err_2": 5,
    }

    def test_append_variants_gff_data(self):
        """
        Test that ERR information gets added to the ref_data dict
        """
#        top_contigs = get_top_contigs(ref, 2)

        top_contigs = get_top_contigs_from_ref_entry(
            self._get_reference_entry(), 2)

        ref_data = _extract_alignment_summ_data(
            self.ALIGNMENT_SUMMARY, top_contigs)[0]
        self.assertEqual(1, len(ref_data))

        results = ref_data[self.CONTIG_ID]
        self.assertEqual(self.TEST_VALUES["contig_len"], results[LENGTH])
        self.assertEqual(self.TEST_VALUES["n_gff_err_1"], results[ERR])

        _append_variants_gff_data(ref_data, self.VARIANTS_GFF)
        self.assertEqual(self.TEST_VALUES["contig_len"], results[LENGTH])
        self.assertEqual(self.TEST_VALUES["n_gff_err_2"], results[ERR])

    def test_get_consensus_table(self):
        """
        Test the data in the table object and the attributes
        """
        top_contigs = get_top_contigs_from_ref_entry(
            self._get_reference_entry(), 2)

        ref_data = _extract_alignment_summ_data(
            self.ALIGNMENT_SUMMARY, top_contigs)[0]
        self.assertEqual(1, len(ref_data))

        results = ref_data[self.CONTIG_ID]
        self.assertEqual(self.TEST_VALUES["contig_len"], results[LENGTH])
        self.assertEqual(0, results[ERR])

        _append_variants_gff_data(ref_data, self.VARIANTS_GFF)

        table, attributes = _get_consensus_table_and_attributes(
            ref_data, self._get_reference_entry())
        self.assertEqual(5, len(table.columns))
        self.assertEqual(self.CONTIG_ID, table.columns[0].values[0])
        self.assertEqual(self.TEST_VALUES["contig_len"],
                         table.columns[1].values[0])
        self.assertEqual(1, table.columns[2].values[0])
        self.assertAlmostEqual(self.TEST_VALUES["concordance"],
                               table.columns[3].values[0], places=4)
        self.assertAlmostEqual(self.TEST_VALUES["coverage"],
                               table.columns[4].values[0], places=2)

    def test_top_contigs(self):
        """
        Test top contigs from ref
        """
        #ref_entry = ReferenceEntry.from_ref_dir(ref)
        ref_entry = openReference(self.REFERENCE)
        self.assertEqual(1, len(get_top_contigs_from_ref_entry(ref_entry, 2)))

    def test_create_variants_plot_grp(self):
        """
        Test that plotGroup of variants plots is created as expected
        """
        top_contigs = get_top_contigs_from_ref_entry(
            self._get_reference_entry(), 25)
        ref_data, contig_variants = _extract_alignment_summ_data(
            self.ALIGNMENT_SUMMARY, top_contigs)

        plot_group = _create_variants_plot_grp(
            top_contigs, contig_variants, self._output_dir)
        self.assertEqual(1, len(plot_group.plots))

        self._assert_image_file(plot_group.thumbnail)

        for plot in plot_group.plots:
            self._assert_image_file(plot.image)
        self._assert_image_file(plot_group.legend)

    def test_legend(self):
        """
        Create the legend png
        """
        top_contigs = get_top_contigs_from_ref_entry(
            self._get_reference_entry(), 25)
        contig_variants = _extract_alignment_summ_data(
            self.ALIGNMENT_SUMMARY, top_contigs)[1]
        ctgvar = None
        for t in top_contigs:
            ctgvar = contig_variants[t.header]

        bars = _create_bars(ctgvar)
        self.assertEqual(3, len(bars))

        leg = _get_legend_file(bars, self._output_dir)
        leg_path = op.join(self._output_dir, leg)

        log.info('legend path: {l}'.format(l=leg_path))
        self.assertTrue(op.exists(leg_path))

    def _assert_image_file(self, filename):
        # Should we add validation to model.report that forces the filename to
        # be relative?
        self.assertFalse(op.isabs(filename))
        self.assertTrue(op.exists(op.join(self._output_dir, filename)))

    def test_make_variants_report(self):
        """
        Create a report object, do assertions on its properties, then assert that it gets written
        """
        report = make_variants_report(self.ALIGNMENT_SUMMARY, self.VARIANTS_GFF,
                                      self.REFERENCE, 25, 'rpt.json', self._output_dir, 60, False)
        self.assertEqual(5, len(report.attributes))
        self.assertEqual(1, len(report.tables))
        self.assertEqual(1, len(report.plotGroups))
        self.assertIsNotNone(report.plotGroups[0].legend)
        self.assertTrue(op.exists(op.join(self._output_dir, 'rpt.json')))
        validate_report_complete(self, report)

    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """
        cmd = 'python -m pbreports.report.variants {o} {r} {c} {a} {v}'.format(
            o=self._output_dir,
            r='rpt.json',
            c=self.REFERENCE,
            a=self.ALIGNMENT_SUMMARY,
            v=self.VARIANTS_GFF)
        rcode = run_backticks(cmd)
        self.assertEquals(0, rcode)
        self.assertTrue(op.exists(op.join(self._output_dir, 'rpt.json')))

    def test_exit_code_0_referenceset(self):
        """
        Like a cram test. Assert exits with 0 with ReferenceSet XML
        """
        ref_name = op.join(self._output_dir, "refset.xml")
        refset = ReferenceSet(self._get_reference_fasta())
        refset.write(ref_name)
        ref = ref_name
        cmd = 'python -m pbreports.report.variants {o} {r} {c} {a} {v}'.format(
            o=self._output_dir, r='rpt.json', c=ref, a=self.ALIGNMENT_SUMMARY,
            v=self.VARIANTS_GFF)
        rcode = run_backticks(cmd)
        self.assertEquals(0, rcode)
        self.assertTrue(op.exists(op.join(self._output_dir, "rpt.json")))


@skip_if_data_dir_not_present
class TestVariantsReportEcoli(TestVariantsReport):
    CONTIG_ID = "ecoliK12_pbi_March2013"
    REFERENCE = "/pbi/dept/secondary/siv/references/ecoliK12_pbi_March2013/sequence/ecoliK12_pbi_March2013.fasta"
    ALIGNMENT_SUMMARY = op.join(VARIANTS_DATA, "alignment_summary.gff")
    VARIANTS_GFF = op.join(VARIANTS_DATA, "variants.gff.gz")
    TEST_VALUES = {
        "contig_len": 4642522,
        "concordance": 0.99999,
        "coverage": 16.43,
        "bases_called": 1,
        "n_gff_err_1": 0,
        "n_gff_err_2": 9,
    }


@skip_if_data_dir_not_present
class TestVariantsReportLarge(BaseTestCase, unittest.TestCase):
    CONTIG_ID = "chr1"
    DATA_DIR = "/pbi/dept/secondary/siv/testdata/pbreports-unittest/data/summarizeConsensus"
    ALIGNMENT_SUMMARY = op.join(
        DATA_DIR, "alignment_summary_variants_big_chr.gff")
    VARIANTS_GFF = op.join(DATA_DIR, "variants_big_chr.gff")
    REFERENCE = "/pbi/dept/secondary/siv/references/hg19_M_sorted/hg19_M_sorted.referenceset.xml"
    TEST_VALUES = {
        "contig_len": 200000000,
        "concordance": 0.9995,
        "coverage": 20.142,
        "bases_called": 1,
        "n_gff_err_1": 0,
        "n_gff_err_2": 100000,
    }

    def _get_reference_fasta(self):
        return op.join(self.REFERENCE, "sequence", "hg19_M_sorted.fasta")


class TestVariantsReportMisc(unittest.TestCase):

    def test_ref_ids_ordered_by_len(self):
        """
        Test the list of seq ids ordered by len
        """
        ref_data = {}
        ref_data['1'] = (1, 0, 0, 0)
        ref_data['2'] = (2, 0, 0, 0)
        ref_data['3'] = (3, 0, 0, 0)
        o = _ref_ids_ordered_by_len(ref_data)
        self.assertEqual('3', o[0])
        self.assertEqual('2', o[1])
        self.assertEqual('1', o[2])


class TestToolContract(pbcommand.testkit.PbTestApp):
    DATA_DIR = op.join(LOCAL_DATA, "variants")
    DRIVER_BASE = "python -m pbreports.report.variants"
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        pbtestdata.get_file("lambda-fasta"),
        pbtestdata.get_file("consensus-summary-gff"),
        pbtestdata.get_file("variants-gff")
    ]
    TASK_OPTIONS = {
        "pbreports.task_options.max_contigs": 25,
        "pbreports.task_options.dpi": 60,
        "pbreports.task_options.dumpdata": True,
    }
