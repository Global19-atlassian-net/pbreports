import os
import logging
import traceback
import json
import tempfile
import unittest
import shutil
import sys

from pbcommand.models.report import PbReportError
from pbcore.util.Process import backticks
from pbcore.io import ReferenceSet

from pbreports.util import get_top_contigs
from pbreports.report.coverage import (make_coverage_report,
                                       _get_contigs_to_plot, _create_contig_plot,
                                       _get_reference_coverage_stats, _get_att_mean_coverage,
                                       _get_att_percent_missing, _create_histogram,
                                       _create_coverage_plot_grp, _create_coverage_histo_plot_grp)

from base_test_case import _get_root_data_dir, skip_if_data_dir_not_present

log = logging.getLogger(__name__)


@skip_if_data_dir_not_present
class TestCoverageRpt(unittest.TestCase):

    def setUp(self):
        """
        Before *every* test
        """
        self._data_dir = os.path.join(_get_root_data_dir(), 'coverage')
        self._output_dir = tempfile.mkdtemp(suffix="coverage")

    def tearDown(self):
        """
        After *every* test
        """
        if os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_make_coverage_report_none_gff(self):
        """
        Gff cannot be null
        """
        ref = os.path.join(self._data_dir, 'lambda')
        with self.assertRaises(PbReportError):
            make_coverage_report(None, ref, 'foo.json', 1, self._output_dir, '1', False)

    def test_make_coverage_report_no_gff(self):
        """
        Gff exists
        """
        ref = os.path.join(self._data_dir, 'lambda')
        with self.assertRaises(IOError):
            make_coverage_report('foo', ref, 'foo.json', 1, self._output_dir, '1', False)

    def test_make_coverage_report_none_reference(self):
        """
        Reference cannot be null
        """
        gff = os.path.join(self._data_dir, 'alignment_summary.gff')
        with self.assertRaises(PbReportError):
            make_coverage_report(gff, None, 'foo.json', 1, self._output_dir, '1', False)

    def test_make_coverage_report_no_reference(self):
        """
        Reference must exist
        """
        gff = os.path.join(self._data_dir, 'alignment_summary.gff')
        with self.assertRaises(IOError):
            make_coverage_report(gff, 'foo', 'foo.json', 1, self._output_dir, '1', False)

    def test_top_contigs(self):
        """
        Test top contigs from ref
        """
        ref = os.path.join(self._data_dir, 'references', 'simple3')
        self.assertEqual(2, len(get_top_contigs(ref, 2)))

    def test_contigs_to_plot(self):
        """
        Test top contigs from ref
        """
        ref = os.path.join(self._data_dir, 'references', 'lambda')
        tcs = get_top_contigs(ref, 25)
        self.assertEqual(1, len(tcs))
        als = os.path.join(self._data_dir, 'alignment_summary.lambda.gff')
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
        ref = os.path.join(self._data_dir, 'references', 'lambda')
        tcs = get_top_contigs(ref, 25)
        als = os.path.join(self._data_dir, 'alignment_summary.lambda.gff')
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
        ref = os.path.join(self._data_dir, 'references', 'lambda')
        tcs = get_top_contigs(ref, 25)
        als = os.path.join(self._data_dir, 'alignment_summary.lambda.gff')
        pls = _get_contigs_to_plot(als, tcs)
        contig = tcs[0]
        c_cov = pls[contig.header]
        stats = _get_reference_coverage_stats(pls.values())
        self.assertEqual(485, len(stats.means))

    def test_attributes(self):
        """
        Test that attribute values match expected
        """
        ref = os.path.join(self._data_dir, 'references', 'lambda')
        tcs = get_top_contigs(ref, 25)
        als = os.path.join(self._data_dir, 'alignment_summary.lambda.gff')
        pls = _get_contigs_to_plot(als, tcs)
        contig = tcs[0]
        c_cov = pls[contig.header]
        stats = _get_reference_coverage_stats(pls.values())
        att = _get_att_mean_coverage(stats)
        # This was in coverage.xml for the alignment summary gff used
        # attribute hidden="true" id="depth_coverage_mean" name="Coverage" value="2958.16">2958.16</attribute>

        self.assertEqual(2958.1640346377467, att.value)

        att = _get_att_percent_missing(stats)
        self.assertEqual(0, att.value)

    def test_create_histogram(self):
        """
        Simple (non null) test of histogram
        """
        ref = os.path.join(self._data_dir, 'references', 'lambda')
        tcs = get_top_contigs(ref, 25)
        als = os.path.join(self._data_dir, 'alignment_summary.lambda.gff')
        pls = _get_contigs_to_plot(als, tcs)

        stats = _get_reference_coverage_stats(pls.values())

        fig, ax = _create_histogram(stats)
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)

    def test_create_coverage_plot_grp(self):
        """
        Test that plotGroup of coverage plots is created as expected
        """
        ref = os.path.join(self._data_dir, 'references', 'lambda')
        tcs = get_top_contigs(ref, 25)
        als = os.path.join(self._data_dir, 'alignment_summary.lambda.gff')
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

        ref = os.path.join(self._data_dir, 'references', 'lambda')
        tcs = get_top_contigs(ref, 25)
        als = os.path.join(self._data_dir, 'alignment_summary.lambda.gff')
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
        self.assertFalse(os.path.isabs(filename))
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, filename)))

    def test_make_coverage_report(self):
        """
        Create a report object, do assertions on its properties, then assert that it gets written
        """
        ref = os.path.join(self._data_dir, 'references', 'lambda')
        gff = os.path.join(self._data_dir, 'alignment_summary.lambda.gff')

        report = make_coverage_report(gff, ref, 25, 'rpt.json', self._output_dir, 60, False)
        self.assertEqual(2, len(report.attributes))
        self.assertEqual(0, len(report.tables))
        self.assertEqual(2, len(report.plotGroups))

        self.assertTrue(os.path.exists(os.path.join(self._output_dir, 'rpt.json')))

    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """

        ref = os.path.join(self._data_dir, 'references', 'lambda')
        gff = os.path.join(self._data_dir, 'alignment_summary.lambda.gff')
        r = 'rpt.json'
        cmd = 'python -m pbreports.report.coverage {o} {r} {c} {g}'.format(o=self._output_dir,
                                                            r=r,
                                                            c=ref, g=gff)

        log.info(cmd)
        o, c, m = backticks(cmd)

        if c is not 0:
            log.error(m)
            log.error(o)
            sys.stderr.write(str(m) + "\n")

        self.assertEquals(0, c)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, r)))


    def test_exit_code_0_fasta(self):
        """
        Like a cram test. Assert exits with 0 with fasta
        """

        ref = os.path.join(self._data_dir, 'references', 'lambda', 'sequence',
                           'lambda.fasta')
        gff = os.path.join(self._data_dir, 'alignment_summary.lambda.gff')
        r = 'rpt.json'
        cmd = 'python -m pbreports.report.coverage {o} {r} {c} {g}'.format(o=self._output_dir,
                                                            r=r,
                                                            c=ref, g=gff)

        log.info(cmd)
        o, c, m = backticks(cmd)

        if c is not 0:
            log.error(m)
            log.error(o)
            sys.stderr.write(str(m) + "\n")

        self.assertEquals(0, c)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, r)))


    def test_exit_code_0_referenceset(self):
        """
        Like a cram test. Assert exits with 0 with ReferenceSet XML
        """

        ref = os.path.join(self._data_dir, 'references', 'lambda', 'sequence',
                           'lambda.fasta')
        ref_name = os.path.join(self._output_dir, "refset.xml")
        refset = ReferenceSet(ref)
        refset.write(ref_name)
        ref = ref_name
        gff = os.path.join(self._data_dir, 'alignment_summary.lambda.gff')
        r = 'rpt.json'
        cmd = 'python -m pbreports.report.coverage {o} {r} {c} {g}'.format(o=self._output_dir,
                                                            r=r,
                                                            c=ref, g=gff)

        log.info(cmd)
        o, c, m = backticks(cmd)

        if c is not 0:
            log.error(m)
            log.error(o)
            sys.stderr.write(str(m) + "\n")

        self.assertEquals(0, c)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, r)))


    def test_exit_code_0_div_by_0_bug(self):
        """
        Like a cram test. Assert exits with 0, even though totalNumContigs is 0.
        """

        ref = os.path.join(self._data_dir, 'references', 'enzyme_methylation_T0070_mC')
        gff = os.path.join(self._data_dir, 'tiny_alignment_summary.gff')
        r = 'rpt.json'
        cmd = 'python -m pbreports.report.coverage {o} {r} {c} {g}'.format(o=self._output_dir,
                                                            r=r,
                                                            c=ref, g=gff)

        o, c, m = backticks(cmd)
        log.info(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            print(m)

        self.assertEquals(0, c)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, r)))

