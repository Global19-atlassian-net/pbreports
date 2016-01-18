import os
import logging
import traceback
import json
import tempfile
import unittest
import shutil

from pbcommand.models.report import PbReportError
from pbcore.util.Process import backticks
from pbcore.io import ReferenceSet

from pbreports.util import openReference
from pbreports.util import get_top_contigs_from_ref_entry
from pbreports.report.variants import (make_variants_report, _extract_alignment_summ_data,
                                       LENGTH, GAPS, ERR, COV,
                                       _append_variants_gff_data,
                                       _get_consensus_table_and_attributes,
                                       _ref_ids_ordered_by_len,
                                       _create_variants_plot_grp, _create_bars, _get_legend_file)

from base_test_case import _get_root_data_dir, run_backticks, \
    skip_if_data_dir_not_present

VARIANTS_DATA = os.path.join(_get_root_data_dir(), 'variants')

DT='Desulfurobacterium_thermolithotrophum_DSM11699_gDNA'

log = logging.getLogger(__name__)


@skip_if_data_dir_not_present
class TestVariantsRpt(unittest.TestCase):

    def setUp(self):
        """
        Before *every* test
        """
#        self._data_dir = os.path.join(_get_root_data_dir(), 'variants')
        self._data_dir = VARIANTS_DATA
        self._output_dir = tempfile.mkdtemp(suffix="variants")

    def tearDown(self):
        """
        After *every* test
        """
        if os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_make_variants_report_invalid_input_files(self):
        """
        inputs cannot be null or non-existent
        """
        als = os.path.join(self._data_dir, 'alignment_summary.gff')
        variants = os.path.join(self._data_dir, 'variants.gff.gz')
        ref = os.path.join(self._data_dir, 'ecoliK12_pbi_March2013')

        # als tests
        with self.assertRaises(PbReportError):
            make_variants_report(None, variants, ref, 'foo.json', 1, self._output_dir, '1', False)
        with self.assertRaises(IOError):
            make_variants_report('foo', variants, ref, 'foo.json', 1, self._output_dir, '1', False)

        # variants tests
        with self.assertRaises(PbReportError):
            make_variants_report(als, None, ref, 'foo.json', 1, self._output_dir, '1', False)
        with self.assertRaises(IOError):
            make_variants_report(als, 'foo', ref, 'foo.json', 1, self._output_dir, '1', False)

        # ref tests
        with self.assertRaises(PbReportError):
            make_variants_report(als, variants, None, 'foo.json', 1, self._output_dir, '1', False)
        with self.assertRaises(IOError):
            make_variants_report(als, variants, 'foo', 'foo.json', 1, self._output_dir, '1', False)

    def test_top_contigs(self):
        """
        Test top contigs from ref
        """
        ref = os.path.join(self._data_dir, 'ecoliK12_pbi_March2013')
        #ref_entry = ReferenceEntry.from_ref_dir(ref)
        ref_entry = openReference(ref)
        self.assertEqual(1, len(get_top_contigs_from_ref_entry(ref_entry, 2)))

    def test_extract_alignment_summ_data(self):
        """
        Test the dicts returned from parsing the alignment_summary gff
        """
        als = os.path.join(self._data_dir, 'alignment_summary.gff')
#        ref = os.path.join(self._data_dir, 'ecoliK12_pbi_March2013')
#        top_contigs = get_top_contigs(ref, 2)

        top_contigs = get_top_contigs_from_ref_entry(self._get_ecoli_reference_entry(), 2)

        ref_data, contig_variants = _extract_alignment_summ_data(als, top_contigs)
        self.assertEqual(1, len(ref_data))

        results = ref_data['ecoliK12_pbi_March2013']
        self.assertEqual(4642522, results[LENGTH])
        self.assertEqual(0, results[ERR])

        self.assertEqual(1, len(contig_variants))

    def test_append_variants_gff_data(self):
        """
        Test that ERR information gets added to the ref_data dict
        """
        als = os.path.join(self._data_dir, 'alignment_summary.gff')
#        ref = os.path.join(self._data_dir, 'ecoliK12_pbi_March2013')
#        top_contigs = get_top_contigs(ref, 2)

        top_contigs = get_top_contigs_from_ref_entry(self._get_ecoli_reference_entry(), 2)

        ref_data = _extract_alignment_summ_data(als, top_contigs)[0]
        self.assertEqual(1, len(ref_data))

        results = ref_data['ecoliK12_pbi_March2013']
        self.assertEqual(4642522, results[LENGTH])
        self.assertEqual(0, results[ERR])

        vars = os.path.join(self._data_dir, 'variants.gff.gz')
        _append_variants_gff_data(ref_data, vars)
        self.assertEqual(4642522, results[LENGTH])
        self.assertEqual(9, results[ERR])

    def _get_ecoli_reference_entry(self):
        ref = os.path.join(self._data_dir, 'ecoliK12_pbi_March2013')
        return openReference(ref)
        #return ReferenceEntry.from_ref_dir(ref)


    def _get_dt_reference_entry(self):
        ref = os.path.join(self._data_dir, 'dt', DT)
        return openReference(ref)
        #return ReferenceEntry.from_ref_dir(ref)



    def test_get_consensus_table(self):
        """
        Test the data in the table object and the attributes
        """
        als = os.path.join(self._data_dir, 'alignment_summary.gff')
        top_contigs = get_top_contigs_from_ref_entry(self._get_ecoli_reference_entry(), 2)

        ref_data = _extract_alignment_summ_data(als, top_contigs)[0]
        self.assertEqual(1, len(ref_data))

        results = ref_data['ecoliK12_pbi_March2013']
        self.assertEqual(4642522, results[LENGTH])
        self.assertEqual(0, results[ERR])

        vars = os.path.join(self._data_dir, 'variants.gff.gz')
        _append_variants_gff_data(ref_data, vars)

        table, attributes = _get_consensus_table_and_attributes(ref_data, self._get_ecoli_reference_entry())
        self.assertEqual(5, len(table.columns))
        self.assertEqual('ecoliK12_pbi_March2013', table.columns[0].values[0])
        self.assertEqual(4642522, table.columns[1].values[0])
        self.assertEqual(1, table.columns[2].values[0])
        self.assertAlmostEqual(.99999, table.columns[3].values[0], places=4)
        self.assertAlmostEqual(16.43, table.columns[4].values[0], places=2)

    def test_get_consensus_attributes(self):
        """
        Test the data in the table object and the attributes
        """
        als = os.path.join(self._data_dir, 'alignment_summary.gff')
        top_contigs = get_top_contigs_from_ref_entry(self._get_ecoli_reference_entry(), 2)

        ref_data = _extract_alignment_summ_data(als, top_contigs)[0]
        self.assertEqual(1, len(ref_data))

        results = ref_data['ecoliK12_pbi_March2013']
        self.assertEqual(4642522, results[LENGTH])
        self.assertEqual(0, results[ERR])

        vars = os.path.join(self._data_dir, 'variants.gff.gz')
        _append_variants_gff_data(ref_data, vars)

        table, attributes = _get_consensus_table_and_attributes(ref_data, self._get_ecoli_reference_entry())
        self.assertEqual(5, len(attributes))

        def __get_att_val(_id, atts):
            for a in atts:
                if a.id == _id:
                    return a.value

        self.assertEqual(4642522, __get_att_val('mean_contig_length', 
                                                attributes))
        self.assertEqual(1, __get_att_val('weighted_mean_bases_called', 
                                          attributes))
        self.assertAlmostEqual(0.99999, 
                               __get_att_val('weighted_mean_concordance', 
                                             attributes), 
                               places=4)
        self.assertAlmostEqual(16.43, 
                               __get_att_val('weighted_mean_coverage', 
                                             attributes), 
                               places=2)
        self.assertEqual('ecoliK12_pbi_March2013', 
                         __get_att_val('longest_contig_name', 
                                       attributes))
        
        
    def test_get_consensus_table_dt(self):
        """
        Test the data in the table object and the attributes
        """
        als = os.path.join(self._data_dir, 'dt', 'alignment_summary.gff')
        top_contigs = get_top_contigs_from_ref_entry(self._get_dt_reference_entry(), 2)
        ref_data = _extract_alignment_summ_data(als, top_contigs)[0]
        
        log.info( str(ref_data) )
        self.assertEqual(1, len(ref_data))
        results = ref_data['gi|325064654|gb|CP002543.1|']
        self.assertEqual(1541968, results[LENGTH])
        self.assertEqual(0, results[ERR])
        
        vars = os.path.join(self._data_dir, 'dt', 'variants.gff.gz')
        _append_variants_gff_data(ref_data, vars)

        table, attributes = _get_consensus_table_and_attributes(ref_data, self._get_dt_reference_entry())
        self.assertEqual(5, len(table.columns))
        # There is no longer the concept of display name, which would remove
        # 'DSM 11699, complete genome'. Bummer
        self.assertEqual('gi|325064654|gb|CP002543.1| Desulfurobacterium '
                         'thermolithotrophum DSM 11699, complete genome',
                         table.columns[0].values[0])
        self.assertEqual(1541968, table.columns[1].values[0])
        self.assertAlmostEqual(.0049, table.columns[2].values[0], places=2)
        self.assertAlmostEqual(.986630, table.columns[3].values[0], places=4)
        self.assertAlmostEqual(.08, table.columns[4].values[0], places=2)


    def test_get_consensus_attributes_dt(self):
        """
        Test the data in the table object and the attributes for the dt reference 
        """
        als = os.path.join(self._data_dir, 'dt', 'alignment_summary.gff')
        top_contigs = get_top_contigs_from_ref_entry(self._get_dt_reference_entry(), 2)
        ref_data = _extract_alignment_summ_data(als, top_contigs)[0]
        
        log.info( str(ref_data) )
        self.assertEqual(1, len(ref_data))
        results = ref_data['gi|325064654|gb|CP002543.1|']
        self.assertEqual(1541968, results[LENGTH])
        self.assertEqual(0, results[ERR])

        vars = os.path.join(self._data_dir, 'dt', 'variants.gff.gz')
        _append_variants_gff_data(ref_data, vars)

        table, attributes = _get_consensus_table_and_attributes(ref_data, self._get_dt_reference_entry())
        self.assertEqual(5, len(attributes))

        def __get_att_val(_id, atts):
            for a in atts:
                if a.id == _id:
                    return a.value

        self.assertEqual(1541968, __get_att_val('mean_contig_length', attributes))
        self.assertAlmostEqual(.0049, __get_att_val('weighted_mean_bases_called', attributes), places=2)
        self.assertAlmostEqual(.986630, __get_att_val('weighted_mean_concordance', attributes), places=4)
        self.assertAlmostEqual(.08, __get_att_val('weighted_mean_coverage', attributes), places=2)
        

    def test_create_variants_plot_grp(self):
        """
        Test that plotGroup of variants plots is created as expected
        """
        top_contigs = get_top_contigs_from_ref_entry(self._get_ecoli_reference_entry(), 25)
        als = os.path.join(self._data_dir, 'alignment_summary.gff')
        ref_data, contig_variants = _extract_alignment_summ_data(als, top_contigs)

        plot_group = _create_variants_plot_grp(top_contigs, contig_variants, self._output_dir)
        self.assertEqual(1, len(plot_group.plots))

        self._assert_image_file(plot_group.thumbnail)

        for plot in plot_group.plots:
            self._assert_image_file(plot.image)
        self._assert_image_file(plot_group.legend)

    def test_legend(self):
        """
        Create the legend png
        """
        top_contigs = get_top_contigs_from_ref_entry(self._get_ecoli_reference_entry(), 25)
        als = os.path.join(self._data_dir, 'alignment_summary.gff')
        contig_variants = _extract_alignment_summ_data(als, top_contigs)[1]
        ctgvar = None
        for t in top_contigs:
            ctgvar = contig_variants[t.header]

        bars = _create_bars(ctgvar)
        self.assertEqual(3, len(bars))

        leg = _get_legend_file(bars, self._output_dir)
        leg_path = os.path.join(self._output_dir, leg)

        log.info('legend path: {l}'.format(l=leg_path))
        self.assertTrue(os.path.exists(leg_path))

    def _assert_image_file(self, filename):
        # Should we add validation to model.report that forces the filename to be relative?
        self.assertFalse(os.path.isabs(filename))
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, filename)))

    def test_make_variants_report(self):
        """
        Create a report object, do assertions on its properties, then assert that it gets written
        """
        als = os.path.join(self._data_dir, 'alignment_summary.gff')
        variants = os.path.join(self._data_dir, 'variants.gff.gz')
        ref = os.path.join(self._data_dir, 'ecoliK12_pbi_March2013')

        report = make_variants_report(als, variants, ref, 25, 'rpt.json', self._output_dir, 60, False)
        self.assertEqual(5, len(report.attributes))
        self.assertEqual(1, len(report.tables))
        self.assertEqual(1, len(report.plotGroups))
        self.assertIsNotNone(report.plotGroups[0].legend)

        self.assertTrue(os.path.exists(os.path.join(self._output_dir, 'rpt.json')))

    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """

        als = os.path.join(self._data_dir, 'alignment_summary.gff')
        variants = os.path.join(self._data_dir, 'variants.gff.gz')
        ref = os.path.join(self._data_dir, 'ecoliK12_pbi_March2013')
        cmd = 'python -m pbreports.report.variants {o} {r} {c} {a} {v}'.format(
            o=self._output_dir,
            r='rpt.json',
            c=ref, a=als,
            v=variants)

        rcode = run_backticks(cmd)
        self.assertEquals(0, rcode)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, 'rpt.json')))


    def test_exit_code_0_fasta(self):
        """
        Like a cram test. Assert exits with 0 with fasta.
        """

        als = os.path.join(self._data_dir, 'alignment_summary.gff')
        variants = os.path.join(self._data_dir, 'variants.gff.gz')
        ref = os.path.join(self._data_dir, 'ecoliK12_pbi_March2013',
                           'sequence',
                           'ecoliK12_pbi_March2013.fasta')
        cmd = 'python -m pbreports.report.variants {o} {r} {c} {a} {v}'.format(
            o=self._output_dir, r='rpt.json', c=ref, a=als, v=variants)

        rcode = run_backticks(cmd)
        self.assertEquals(0, rcode)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, 'rpt.json')))


    def test_exit_code_0_referenceset(self):
        """
        Like a cram test. Assert exits with 0 with ReferenceSet XML
        """

        als = os.path.join(self._data_dir, 'alignment_summary.gff')
        variants = os.path.join(self._data_dir, 'variants.gff.gz')
        ref = os.path.join(self._data_dir, 'ecoliK12_pbi_March2013',
                           'sequence',
                           'ecoliK12_pbi_March2013.fasta')
        ref_name = os.path.join(self._output_dir, "refset.xml")
        refset = ReferenceSet(ref)
        refset.write(ref_name)
        ref = ref_name
        cmd = 'python -m pbreports.report.variants {o} {r} {c} {a} {v}'.format(
            o=self._output_dir, r='rpt.json', c=ref, a=als, v=variants)

        rcode = run_backticks(cmd)
        self.assertEquals(0, rcode)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir,
                                                    'rpt.json')))


class TestVariansReportMisc(unittest.TestCase):
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
