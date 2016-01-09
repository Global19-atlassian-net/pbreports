import os
import logging
import traceback
import json
import tempfile
import unittest
import shutil

from pbcore.util.Process import backticks
from pbcore.io import ReferenceSet

from pbreports.serializers import dict_to_report

from pbreports.model.model import PbReportError
from pbreports.report.top_variants import (make_topvariants_report, VariantFinder,
                                           MinorVariantTableBuilder, VariantTableBuilder)

from base_test_case import _get_root_data_dir, run_backticks, \
    skip_if_data_dir_not_present

log = logging.getLogger(__name__)


ECOLI = 'ecoliK12_pbi_March2013'

@skip_if_data_dir_not_present
class TestTopVariantsRpt(unittest.TestCase):

    DATA_DIR = None

    @classmethod
    def setUpClass(cls):
        """
        Load data once.
        """
        try:
            if cls.DATA_DIR is not None:
                log.info('data has already been loaded')
                return

            cls.DATA_DIR = os.path.join(_get_root_data_dir(), 'topvariants')

#            cmph5 = os.path.join(cls.DATA_DIR, 'control_reads.cmp.h5')
#            csv = os.path.join(cls.DATA_DIR, 'filtered_summary.csv')
#
#            log.info('Loading data 1 time from {c} and {f}'.format(c=cmph5, f=csv))

#            cls._data = {}
#            cls._data[CONTROL_READS] = _get_control_reads(cmph5)
#            cls._data[FILTERED_READS] = _get_filtered_reads(csv)
        except:
            tb = traceback.format_exc()
            log.error(tb)
            print(tb)
            raise

    def setUp(self):
        """
        Before *every* test
        """
        self._output_dir = tempfile.mkdtemp(suffix="topvariants")

    def tearDown(self):
        """
        After *every* test
        """
        if os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_make_topvariants_report_input_files(self):
        """
        input gff and ref must be non-null and exist
        """
        ref = os.path.join(self.DATA_DIR, ECOLI)
        gff = os.path.join(self.DATA_DIR, 'variants.gff.gz')

        # test gff
        with self.assertRaises(PbReportError):
            make_topvariants_report(None, ref, 'foo.json', 1, 10, self._output_dir)

        with self.assertRaises(IOError):
            make_topvariants_report('foo', ref, 'foo.json', 1, 10, self._output_dir)

        # test ref
        with self.assertRaises(PbReportError):
            make_topvariants_report(gff, None, 'foo.json', 1, 10, self._output_dir)

        with self.assertRaises(IOError):
            make_topvariants_report(gff, 'foo', 'foo.json', 1, 10, self._output_dir)

    def test_make_topvariants_report_inputs(self):
        """
        in inputs
        """
        ref = os.path.join(self.DATA_DIR, ECOLI)
        gff = os.path.join(self.DATA_DIR, 'variants.gff.gz')
        # test how_many
        with self.assertRaises(ValueError):
            make_topvariants_report(gff, ref, 'foo.json', None, 10, self._output_dir)

        # test batch size
        with self.assertRaises(ValueError):
            make_topvariants_report(gff, ref, 'foo.json', 1, None, self._output_dir)

    def test_variant_finder(self):
        ref = os.path.join(self.DATA_DIR, ECOLI)
        gff = os.path.join(self.DATA_DIR, 'variants.gff.gz')
        vf = VariantFinder(gff, ref, 100, 10000)
        top = vf.find_top()
        self.assertEqual(9, len(top))

    def test_variant_table_builder(self):
        """
        Test the length and values of a table produced by the standard variant table builder
        """
        tb = VariantTableBuilder()
        columns = tb.table.columns

        self.assertEqual('top_variants_table', tb.table.id)

        self.assertEqual(7, len(columns))
        self.assertEqual('Sequence', columns[0].header)
        self.assertEqual('Position', columns[1].header)
        self.assertEqual('Variant', columns[2].header)
        self.assertEqual('Type', columns[3].header)
        self.assertEqual('Coverage', columns[4].header)
        self.assertEqual('Confidence', columns[5].header)
        self.assertEqual('Genotype', columns[6].header)

        ref = os.path.join(self.DATA_DIR, ECOLI)
        gff = os.path.join(self.DATA_DIR, 'variants.gff.gz')
        vf = VariantFinder(gff, ref, 100, 10000)
        top = vf.find_top()

        for v in top:
            tb.add_variant(v)

        columns = tb.table.columns

        # This tests the first row
        self.assertEqual('ecoliK12_pbi_March2013', columns[0].values[0])
        self.assertEqual(1849183L, columns[1].values[0])
        self.assertEqual('1849183_1849184insT', columns[2].values[0])
        self.assertEqual('INS', columns[3].values[0])
        self.assertEqual(20, columns[4].values[0])
        self.assertEqual(48, columns[5].values[0])
        self.assertEqual('haploid', columns[6].values[0])

        self.assertEqual('ecoliK12_pbi_March2013', columns[0].values[8])
        self.assertEqual(3785544L, columns[1].values[8])
        self.assertEqual('3785544_3785545insA', columns[2].values[8])
        self.assertEqual('INS', columns[3].values[8])
        self.assertEqual(18, columns[4].values[8])
        self.assertEqual(40, columns[5].values[8])
        self.assertEqual('haploid', columns[6].values[8])

    def test_minor_variant_table_builder(self):
        """
        Test the length and values of a table produced by the minor variant table builder
        """
        tb = MinorVariantTableBuilder()

        self.assertEqual('top_minor_variants_table', tb.table.id)

        columns = tb.table.columns
        self.assertEqual(7, len(columns))
        self.assertEqual('Sequence', columns[0].header)
        self.assertEqual('Position', columns[1].header)
        self.assertEqual('Variant', columns[2].header)
        self.assertEqual('Type', columns[3].header)
#        self.assertEqual('Frequency', columns[4].header)
        self.assertEqual('Coverage', columns[4].header)
        self.assertEqual('Confidence', columns[5].header)
        self.assertEqual('Frequency', columns[6].header)

        ref = os.path.join(self.DATA_DIR, ECOLI)
        gff = os.path.join(self.DATA_DIR, 'rare_variants.gff.gz')
        vf = VariantFinder(gff, ref, 100, 10000)
        v = vf.find_top()[0]

        tb.add_variant(v)
        columns = tb.table.columns
        self.assertEqual('lambda_NEB3011', columns[0].values[0])
        self.assertEqual(35782L, columns[1].values[0])
        self.assertEqual('35782G>T', columns[2].values[0])
        self.assertEqual('SUB', columns[3].values[0])
        self.assertEqual(742, columns[4].values[0])
        self.assertEqual(7, columns[5].values[0])
        self.assertEqual(9, columns[6].values[0])

    def test_make_topvariants_report(self):
        """
        Call the main report generation method. Deserialize report, check content.
        """
        ref = os.path.join(self.DATA_DIR, ECOLI)
        gff = os.path.join(self.DATA_DIR, 'variants.gff.gz')
        make_topvariants_report(gff, ref, 100, 10000, 'rpt.json', self._output_dir)

        # deserialize report
        s = None
        with open(os.path.join(self._output_dir, 'rpt.json'), 'r') as f:
            s = json.load(f)

        report = dict_to_report(s)
        self.assertEqual('Genotype', report.tables[0].columns[6].header)

    def test_make_minor_topvariants_report(self):
        """
        Call the main report generation method with minor kwarg==True. Deserialize report, check content.
        """
        ref = os.path.join(self.DATA_DIR, ECOLI)
        gff = os.path.join(self.DATA_DIR, 'rare_variants.gff.gz')
        make_topvariants_report(gff, ref, 100, 10000, 'rpt.json', self._output_dir, is_minor_variants_rpt=True)

        # deserialize report
        s = None
        with open(os.path.join(self._output_dir, 'rpt.json'), 'r') as f:
            s = json.load(f)

        report = dict_to_report(s)
        self.assertEqual('Frequency', report.tables[0].columns[6].header)

    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """
        ref = os.path.join(self.DATA_DIR, ECOLI)
        gff = os.path.join(self.DATA_DIR, 'variants.gff.gz')
        j = 'rpt.json'
        cmd = 'pbreport topvariants {o} {j} {g} {r}'.format(o=self._output_dir,
                                                                    g=gff, r=ref, j=j)
        log.info(cmd)

        rcode = run_backticks(cmd)
        self.assertEquals(0, rcode)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, j)))

    def test_exit_code_0_fasta(self):
        """
        Like a cram test. Assert exits with 0 with fasta
        """
        ref = os.path.join(self.DATA_DIR, ECOLI,
                           'sequence',
                           'ecoliK12_pbi_March2013.fasta')
        gff = os.path.join(self.DATA_DIR, 'variants.gff.gz')
        j = 'rpt.json'
        cmd = 'pbreport topvariants {o} {j} {g} {r}'.format(o=self._output_dir,
                                                                    g=gff, r=ref, j=j)
        log.info(cmd)

        rcode = run_backticks(cmd)
        self.assertEquals(0, rcode)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, j)))

    def test_exit_code_0_referenceset(self):
        """
        Like a cram test. Assert exits with 0 with ReferenceSet XML
        """
        ref = os.path.join(self.DATA_DIR, ECOLI,
                           'sequence',
                           'ecoliK12_pbi_March2013.fasta')
        ref_name = os.path.join(self._output_dir, "refset.xml")
        refset = ReferenceSet(ref)
        refset.write(ref_name)
        ref = ref_name
        gff = os.path.join(self.DATA_DIR, 'variants.gff.gz')
        j = 'rpt.json'
        cmd = 'pbreport topvariants {o} {j} {g} {r}'.format(o=self._output_dir,
                                                                    g=gff, r=ref, j=j)
        log.info(cmd)

        rcode = run_backticks(cmd)
        self.assertEquals(0, rcode)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, j)))

    def test_exit_code_0_top_corrections(self):
        """
        Like a cram test. Assert exits with 0. This creates the 'top corrections' report,
        which is exactly the same as the top variants reports, except that table
        columns in the smrtportal have been renamed. This is accomplished via the rules.
        """
        ref = os.path.join(self.DATA_DIR, 'reference')
        gff = os.path.join(self.DATA_DIR, 'corrections.gff')
        cmd = 'pbreport topvariants {o} rpt.json {g} {r}'.format(o=self._output_dir,
                                                                    g=gff, r=ref)
        log.info(cmd)
        o, c, m = backticks(cmd)

        if c is not 0:
            log.error(m)
            log.error(o)
            print(m)
        self.assertEquals(0, c)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, 'rpt.json')))

    def test_exit_code_0_minor(self):
        """
        Like a cram test. Create the minor report in a subprocess. Assert that the report is correct.
        """
        ref = os.path.join(self.DATA_DIR, ECOLI)
        gff = os.path.join(self.DATA_DIR, 'rare_variants.gff.gz')
        cmd = 'pbreport minor-topvariants {o} rpt.json {g} {r}'.format(o=self._output_dir,
                                                                          g=gff, r=ref)
        log.info(cmd)
        o, c, m = backticks(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            print(m)
        self.assertEquals(0, c)
        # deserialize report
        s = None
        with open(os.path.join(self._output_dir, 'rpt.json'), 'r') as f:
            s = json.load(f)

        report = dict_to_report(s)
        self.assertEqual('Frequency', report.tables[0].columns[6].header)
