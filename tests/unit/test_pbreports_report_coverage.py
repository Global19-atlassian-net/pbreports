
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
from pbcore.util.Process import backticks
from pbcore.io import ReferenceSet
import pbcore.data

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
    REFERENCE = pbcore.data.getLambdaFasta()
    GFF = op.join(LOCAL_DATA, "summarize_coverage", "alignment_summary.gff")

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
            make_coverage_report(self.GFF, None, 'foo.json', 1, self._output_dir)

    def test_make_coverage_report_no_reference(self):
        """
        Reference must exist
        """
        with self.assertRaises(IOError):
            make_coverage_report(self.GFF, 'foo', 'foo.json', 1, self._output_dir)

    def test_top_contigs(self):
        """
        Test top contigs from ref
        """
        ref = op.join(self._data_dir, 'references', 'simple3')
        self.assertEqual(2, len(get_top_contigs(ref, 2)))

    def test_contigs_to_plot(self):
        """
        Test top contigs from ref
        """
        tcs = get_top_contigs(self.REFERENCE, 25)
        self.assertEqual(1, len(tcs))
        als = self.GFF#op.join(self._data_dir, 'alignment_summary.lambda.gff')
        pls = _get_contigs_to_plot(als, tcs)
        self.assertEqual(len(pls), len(tcs))
        contig = tcs[0]
        c_cov = pls[contig.header]
        self.assertEqual('lambda_NEB3011', c_cov._name)
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
        # attribute hidden="true" id="depth_coverage_mean" name="Coverage" value="2958.16">2958.16</attribute>
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
        # attribute hidden="true" id="depth_coverage_mean" name="Coverage" value="2958.16">2958.16</attribute>
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
        # Should we add validation to model.report that forces the filename to be relative?
        self.assertFalse(op.isabs(filename))
        self.assertTrue(op.exists(op.join(self._output_dir, filename)))

    def test_make_coverage_report(self):
        """
        Create a report object, do assertions on its properties, then assert that it gets written
        """
        gff = self.GFF
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
        ref = op.join(self._data_dir, 'references', 'enzyme_methylation_T0070_mC')
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
