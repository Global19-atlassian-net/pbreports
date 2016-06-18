
import traceback
import tempfile
import unittest
import logging
import shutil
import json
import os.path as op
import os
import sys

from pbcommand.models.report import PbReportError
import pbcommand.testkit.core
from pbcore.util.Process import backticks
from pbcore.io import ReferenceSet, FastaReader, FastaWriter, GffReader, GffWriter

import pbtestdata

from pbreports.util import get_top_contigs
from pbreports.report.coverage import (make_coverage_report,
                                       _get_contigs_to_plot, _create_contig_plot,
                                       _get_reference_coverage_stats, _get_att_mean_coverage,
                                       _get_att_percent_missing, _create_histogram,
                                       _create_coverage_plot_grp, _create_coverage_histo_plot_grp)

from base_test_case import (ROOT_DATA_DIR, LOCAL_DATA,
                            skip_if_data_dir_not_present)

log = logging.getLogger(__name__)


class TestCoverageRpt(unittest.TestCase):
    REFERENCE = pbtestdata.get_file("lambda-fasta")
    GFF = pbtestdata.get_file("alignment-summary-gff")
    CONTIG_ID = "lambda_NEB3011"
    PLOT_FILE_NAME = "coverage_plot_lambda_NEB3011.png"

    def setUp(self):
        self._data_dir = op.join(ROOT_DATA_DIR, 'coverage')
        self._output_dir = tempfile.mkdtemp(suffix="coverage")
        log.setLevel(logging.INFO)

    def tearDown(self):
        if op.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_make_coverage_report_none_gff(self):
        """
        Gff cannot be null
        """
        with self.assertRaises(PbReportError):
            make_coverage_report(None, self.REFERENCE, 'foo.json', 1,
                                 self._output_dir)

    def test_make_coverage_report_no_gff(self):
        """
        Gff exists
        """
        with self.assertRaises(IOError):
            make_coverage_report('foo', self.REFERENCE, 'foo.json', 1,
                                 self._output_dir)

    def test_make_coverage_report_none_reference(self):
        """
        Reference cannot be null
        """
        with self.assertRaises(PbReportError):
            make_coverage_report(
                self.GFF, None, 'foo.json', 1, self._output_dir)

    def test_make_coverage_report_no_reference(self):
        """
        Reference must exist
        """
        with self.assertRaises(IOError):
            make_coverage_report(
                self.GFF, 'foo', 'foo.json', 1, self._output_dir)

    def test_top_contigs(self):
        """
        Test top contigs from ref
        """
        ref = op.join(LOCAL_DATA, "coverage", 'simple3', "sequence",
                      "simple3.fasta")
        self.assertEqual(2, len(get_top_contigs(ref, 2)))

    def test_contigs_to_plot(self):
        """
        Test top contigs from ref
        """
        tcs = get_top_contigs(self.REFERENCE, 25)
        self.assertEqual(1, len(tcs))
        # op.join(self._data_dir, 'alignment_summary.lambda.gff')
        als = self.GFF
        pls = _get_contigs_to_plot(als, tcs)
        self.assertEqual(len(pls), len(tcs))
        contig = tcs[0]
        c_cov = pls[contig.header]
        self.assertEqual(self.CONTIG_ID, c_cov._name)
        self.assertEqual(self.PLOT_FILE_NAME, op.basename(c_cov.file_name))
        # TODO  more testing of cc

    def test_create_contig_plot(self):
        """
        Simple non-null test of single contig fig,ax
        """
        tcs = get_top_contigs(self.REFERENCE, 25)
        als = self.GFF
        pls = _get_contigs_to_plot(als, tcs)
        contig = tcs[0]
        c_cov = pls[contig.header]
        fig, ax = _create_contig_plot(c_cov)
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)

    def test_get_coverage_stats(self):
        """
        Test the coverage stats object (needs more)
        """
        tcs = get_top_contigs(self.REFERENCE, 25)
        als = self.GFF
        pls = _get_contigs_to_plot(als, tcs)
        contig = tcs[0]
        c_cov = pls[contig.header]
        stats = _get_reference_coverage_stats(pls.values())
        self.assertEqual(485, len(stats.means))

    def test_attributes(self):
        """
        Test that attribute values match expected
        """
        tcs = get_top_contigs(self.REFERENCE, 25)
        als = self.GFF
        pls = _get_contigs_to_plot(als, tcs)
        contig = tcs[0]
        c_cov = pls[contig.header]
        stats = _get_reference_coverage_stats(pls.values())
        att = _get_att_mean_coverage(stats)
        # This was in coverage.xml for the alignment summary gff used
        # attribute hidden="true" id="depth_coverage_mean" name="Coverage"
        # value="2958.16">2958.16</attribute>
        self.assertAlmostEqual(1.228, att.value, places=3)
        att = _get_att_percent_missing(stats)
        self.assertAlmostEqual(58.4, att.value, places=1)

    @skip_if_data_dir_not_present
    def test_attributes_high_coverage(self):
        tcs = get_top_contigs(self.REFERENCE, 25)
        als = op.join(self._data_dir, "alignment_summary.lambda.gff")
        pls = _get_contigs_to_plot(als, tcs)
        contig = tcs[0]
        c_cov = pls[contig.header]
        stats = _get_reference_coverage_stats(pls.values())
        att = _get_att_mean_coverage(stats)
        # This was in coverage.xml for the alignment summary gff used
        # attribute hidden="true" id="depth_coverage_mean" name="Coverage"
        # value="2958.16">2958.16</attribute>
        self.assertAlmostEqual(2958.16, att.value, places=2)
        att = _get_att_percent_missing(stats)
        self.assertEqual(0, att.value)

    def test_create_histogram(self):
        """
        Simple (non null) test of histogram
        """
        tcs = get_top_contigs(self.REFERENCE, 25)
        als = self.GFF
        pls = _get_contigs_to_plot(als, tcs)
        stats = _get_reference_coverage_stats(pls.values())
        fig, ax = _create_histogram(stats)
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)

    def test_create_coverage_plot_grp(self):
        """
        Test that plotGroup of coverage plots is created as expected
        """
        tcs = get_top_contigs(self.REFERENCE, 25)
        als = self.GFF
        pls = _get_contigs_to_plot(als, tcs)
        plot_group = _create_coverage_plot_grp(tcs, pls, self._output_dir)
        # only 1 contig in lambda
        self.assertEqual(1, len(plot_group.plots))
        self._assert_image_file(plot_group.thumbnail)

        for plot in plot_group.plots:
            self._assert_image_file(plot.image)

    def test_create_coverage_histo_plot_grp(self):
        """
        Test that plotGroup of the histogram is created as expected
        """
        tcs = get_top_contigs(self.REFERENCE, 25)
        als = self.GFF
        pls = _get_contigs_to_plot(als, tcs)
        stats = _get_reference_coverage_stats(pls.values())
        plot_group = _create_coverage_histo_plot_grp(stats, self._output_dir)
        # only 1 histo
        self.assertEqual(1, len(plot_group.plots))
        self._assert_image_file(plot_group.thumbnail)
        for plot in plot_group.plots:
            self._assert_image_file(plot.image)

    def _assert_image_file(self, filename):
        # Should we add validation to model.report that forces the filename to
        # be relative?
        self.assertFalse(op.isabs(filename))
        self.assertTrue(op.exists(op.join(self._output_dir, filename)))

    def test_make_coverage_report(self):
        """
        Create a report object, do assertions on its properties, then assert that it gets written
        """
        report = make_coverage_report(self.GFF, self.REFERENCE, 25, 'rpt.json',
                                      self._output_dir)
        self.assertEqual(2, len(report.attributes))
        self.assertEqual(0, len(report.tables))
        self.assertEqual(2, len(report.plotGroups))
        self.assertTrue(op.exists(op.join(self._output_dir, 'rpt.json')))

    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """
        r = op.join(self._output_dir, 'rpt.json')
        cmd = 'python -m pbreports.report.coverage {c} {g} {r}'.format(
            r=r, c=self.REFERENCE, g=self.GFF)
        log.info(cmd)
        o, c, m = backticks(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            sys.stderr.write(str(m) + "\n")
        self.assertEquals(0, c)
        self.assertTrue(op.exists(r))

    def test_exit_code_0_referenceset(self):
        """
        Like a cram test. Assert exits with 0 with ReferenceSet XML
        """
        ref_name = op.join(self._output_dir, "refset.xml")
        refset = ReferenceSet(self.REFERENCE)
        refset.write(ref_name)
        ref = ref_name
        r = op.join(self._output_dir, 'rpt.json')
        cmd = 'python -m pbreports.report.coverage {c} {g} {r}'.format(
            r=r, c=ref, g=self.GFF)
        log.info(cmd)
        o, c, m = backticks(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            sys.stderr.write(str(m) + "\n")
        self.assertEquals(0, c)
        self.assertTrue(op.exists(r))

    @skip_if_data_dir_not_present
    def test_exit_code_0_div_by_0_bug(self):
        """
        Like a cram test. Assert exits with 0, even though totalNumContigs is 0.
        """
        ref = op.join(self._data_dir, 'references', 'enzyme_methylation_T0070_mC',
                      'sequence', 'enzyme_methylation_T0070_mC.fasta')
        gff = op.join(self._data_dir, 'tiny_alignment_summary.gff')
        r = op.join(self._output_dir, 'rpt.json')
        cmd = 'python -m pbreports.report.coverage {c} {g} {r}'.format(
            r=r, c=ref, g=gff)
        o, c, m = backticks(cmd)
        log.info(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            print(m)
        self.assertEquals(0, c)
        self.assertTrue(op.exists(r))


class TestCoveragePlotQuivered(TestCoverageRpt):
    REFERENCE = tempfile.NamedTemporaryFile(suffix=".fasta").name
    GFF = tempfile.NamedTemporaryFile(suffix=".gff").name
    CONTIG_ID = "lambda_NEB3011|quiver"
    PLOT_FILE_NAME = "coverage_plot_lambda_NEB3011_quiver.png"

    @classmethod
    def setUpClass(cls):
        with FastaWriter(cls.REFERENCE) as fasta_out:
            with FastaReader(TestCoverageRpt.REFERENCE) as fasta_in:
                for rec in fasta_in:
                    header = rec.id + "|quiver"
                    fasta_out.writeRecord(header, rec.sequence)
        with GffWriter(cls.GFF) as gff_out:
            with GffReader(TestCoverageRpt.GFF) as gff_in:
                for header in gff_in.headers:
                    gff_out.writeHeader(header)
                for rec in gff_in:
                    rec.seqid += "|quiver"
                    gff_out.writeRecord(rec)

    def test_attributes_high_coverage(self):
        raise unittest.SkipTest("Not applicable")

    def test_plot_file_names(self):
        report = make_coverage_report(self.GFF, self.REFERENCE, 25, 'rpt.json',
                                      self._output_dir)
        n = 0
        for pg in report.plotGroups:
            if pg.id == "coverage_plots":
                for p in pg.plots:
                    if p.id.startswith("coverage_contig"):
                        self.assertEqual(self.PLOT_FILE_NAME,
                                         op.basename(p.image))
                        n += 1
        self.assertEqual(n, 1, "Contig coverage plot not found")


@skip_if_data_dir_not_present
class TestManyContigs(unittest.TestCase):
    REFERENCE = "/pbi/dept/secondary/siv/references/ecoli_split_1000/ecoli_split_1000.referenceset.xml"
    GFF = "/pbi/dept/secondary/siv/testdata/pbreports-unittest/data/coverage/alignment_summary_ecoli_split_1000.gff"

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.report_out = op.join(self.tmp_dir, "coverage_report.json")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_get_top_contigs(self):
        top_contigs = get_top_contigs(self.REFERENCE, 25)
        self.assertTrue(len(top_contigs), 25)

    def test__get_contigs_to_plot(self):
        top_contigs = get_top_contigs(self.REFERENCE, 25)
        cov_map = _get_contigs_to_plot(self.GFF, top_contigs)
        self.assertNotEqual(len(cov_map), 0)


    def test_make_report(self):
        rpt = make_coverage_report(self.GFF, self.REFERENCE,
                                   report=self.report_out,
                                   output_dir=self.tmp_dir,
                                   max_contigs_to_plot=25)
        attr = {a.id:a.value for a in rpt.attributes}
        self.assertEqual(attr['missing_bases_pct'], 0.0)
        self.assertAlmostEqual(attr['depth_coverage_mean'], 68.06, places=2)


class TestToolContract(pbcommand.testkit.core.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.coverage"
    INPUT_FILES = [
        pbtestdata.get_file("lambda-fasta"),
        pbtestdata.get_file("alignment-summary-gff")
    ]
    IS_DISTRIBUTED = True
    RESOLVED_IS_DISTRIBUTED = True
