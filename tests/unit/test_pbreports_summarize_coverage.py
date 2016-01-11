import functools
import itertools
import numpy
import os
import random
import unittest
import logging

import pbcommand.testkit
from pbcore.io import CmpH5Reader, GffIO, AlignmentSet, IndexedBamReader
import pbcore.data

from pbreports.report.summarize_coverage import interval_tree, summarize_coverage

from base_test_case import ROOT_DATA_DIR, skip_if_data_dir_not_present, \
    LOCAL_DATA

SC_DATA_DIR = os.path.join(ROOT_DATA_DIR, 'summarize_coverage')

log = logging.getLogger(__name__)


class TestCompareToPbpy(unittest.TestCase):

    """Compare results from the pbreports summarize_coverage to an archived result from pbpy summarizeCoverage.
    """

    def _get_readers(self):
        ds_reader = AlignmentSet(self.aln_path, strict=True,
            reference=self.ref_path)
        return ds_reader, ds_reader.resourceReaders()

    def setUp(self):
        self.aln_path = pbcore.data.getBamAndCmpH5()[0]
        self.gff_path = os.path.join(LOCAL_DATA, "summarize_coverage",
            "alignment_summary.gff")
        self.ref_path = pbcore.data.getLambdaFasta()
        self.selected_reference = None

    def test_metadata(self):
        """Test that the metadata lines match those from the pbpy version of summarize_coverage.
        """
        ds_reader, bam_readers = self._get_readers()
        bfx_metadata_lines = summarize_coverage.get_metadata_lines(
            bam_readers, {})

        pbpy_gff_reader = GffIO.GffReader(self.gff_path)
        pbpy_metadata_lines = pbpy_gff_reader.headers

        pbpy_i = 0
        bfx_i = 0

        # GffWriter handles this first line, not get_metadata_lines. So just
        # make sure it's there in the pbpy file
        self.assertEqual(pbpy_metadata_lines[0], "##gff-version 3")
        pbpy_i += 1
        self.assertEqual(len(pbpy_metadata_lines[1:]), len(bfx_metadata_lines))

        # Check the date line
        bfx_dateline = bfx_metadata_lines[bfx_i]
        pbpy_dateline = pbpy_metadata_lines[pbpy_i]
        self.assertEqual(
            bfx_dateline.split(' ')[0], pbpy_dateline.split(' ')[0])
        pbpy_i += 1
        bfx_i += 1

        # Check the source line
        bfx_sourceline = bfx_metadata_lines[bfx_i]
        pbpy_sourceline = pbpy_metadata_lines[pbpy_i]
        self.assertEqual(bfx_sourceline, pbpy_sourceline)
        pbpy_i += 1
        bfx_i += 1

        # Check the command line
        bfx_commandline = bfx_metadata_lines[bfx_i]
        pbpy_commandline = pbpy_metadata_lines[pbpy_i]
        self.assertEqual(bfx_commandline.split(' ')[0],
                         pbpy_commandline.split(' ')[0])
        pbpy_i += 1
        bfx_i += 1

        while pbpy_i < len(pbpy_metadata_lines):
            self.assertEqual(pbpy_metadata_lines[pbpy_i],
                             bfx_metadata_lines[bfx_i])
            pbpy_i += 1
            bfx_i += 1

    def test_coverages(self):
        """Test that the regions and calculated coverages are the same for both the bfx and pbpy summarize_coverage results.
        """
        # Read the pbpy gff into a dictionary for comparison
        pbpy_gff_reader = GffIO.GffReader(self.gff_path)
        pbpy_gff_records = {}
        for gff_record in pbpy_gff_reader:
            record_key = (gff_record.seqid.split()[0], gff_record.start, gff_record.end)
            record_val = gff_record
            pbpy_gff_records[record_key] = record_val

        # Recapitulate the first few steps of summarize_coverage.main
        #cmph5_reader = CmpH5Reader(self.cmph5_path)
        ds_reader, readers = self._get_readers()
        interval_lists = summarize_coverage.build_interval_lists(readers)
        get_region_size_frozen = functools.partial(
            summarize_coverage.get_region_size, num_refs=len(interval_lists),
            region_size=0, num_regions=500, force_num_regions=False)

        for ref_group_id in sorted(interval_lists):
            gff_generator = summarize_coverage.generate_gff_records(
                interval_lists[ref_group_id], readers, ref_group_id,
                get_region_size_frozen, {})

            for bfx_gff_record in gff_generator:
                bfx_key = (bfx_gff_record.seqid, bfx_gff_record.start,
                           bfx_gff_record.end)
                self.assertIn(bfx_key, pbpy_gff_records)
                pbpy_gff_record = pbpy_gff_records.pop(bfx_key)

                self.assertEqual(pbpy_gff_record.cov, bfx_gff_record.cov)
                self.assertEqual(pbpy_gff_record.gaps, bfx_gff_record.gaps)
                pbpy_cov2 = [float(k) for k in pbpy_gff_record.cov2.split(',')]
                bfx_cov2 = [float(k) for k in bfx_gff_record.cov2.split(',')]

                for pair in zip(pbpy_cov2, bfx_cov2):
                    self.assertAlmostEqual(pair[0], pair[1])

                self.assertEqual(pbpy_gff_record.source, bfx_gff_record.source)
                self.assertEqual(pbpy_gff_record.type, bfx_gff_record.type)
                self.assertEqual(pbpy_gff_record.score, bfx_gff_record.score)
                self.assertEqual(pbpy_gff_record.strand, bfx_gff_record.strand)
                self.assertEqual(pbpy_gff_record.phase, bfx_gff_record.phase)

        if self.selected_reference is not None:
            remaining_pbpy_records = {}
            for record_key in pbpy_gff_records:
                if record_key[0] == self.selected_reference:
                    remaining_pbpy_records[record_key] = pbpy_gff_records[record_key]
        else:
            remaining_pbpy_records = pbpy_gff_records

        self.assertEqual(len(remaining_pbpy_records), 0)


# FIXME this needs to use AlignmentSet/BAM input
@skip_if_data_dir_not_present
class TestCompareToPbpyBigGenome(TestCompareToPbpy):

    """Compare results from the pbreports summarize_coverage to an archived result from pbpy summarizeCoverage. Same as TestCompareToPbpy, but applied to the human genome.
    """

    def _get_readers(self):
        cmph5 = CmpH5Reader(self.aln_path)
        return cmph5, [cmph5]

    def setUp(self):
        self.aln_path = os.path.join(SC_DATA_DIR, 'aligned_reads_human_chr2.cmp.h5')
        self.gff_path = os.path.join(SC_DATA_DIR, 'alignment_summary_human_chr2.gff')
        self.selected_reference = 'chr2'
    
    def test_metadata(self):
        """The metadata lines won't match. The pbpy version of summarizeCoverge writes out metadata for every reference in the repository, the bfx version only write metadata for contigs with coverage.
        """
        pass


class TestBuildIntervalLists(unittest.TestCase):

    """Test the building of interval lists from BAM alignments."""

    @classmethod
    def setUpClass(cls):
        cls.bam_path = pbcore.data.getBamAndCmpH5()[0]
        cls.ds_reader = AlignmentSet(cls.bam_path, strict=True,
            reference=pbcore.data.getLambdaFasta())
        cls.bam_readers = cls.ds_reader.resourceReaders()
        cls.interval_lists = summarize_coverage.build_interval_lists(
            cls.bam_readers)

    def test_total_alignments(self):
        """Test that all alignments end up in the list."""
        total_ilist_alns = sum(len(v)
                               for v in self.interval_lists.itervalues())
        total_bam_alns = sum([len(b) for b in self.bam_readers])
        self.assertEqual(total_ilist_alns, total_bam_alns)

    def test_keys(self):
        """Test that alignments for each refGroupID in the BAM match the interval_list."""
        for record in self.ds_reader.referenceInfoTable:
            ref_id = record.ID
            ref_length = record.Length
            n_alns = len(list(self.ds_reader.readsInRange(ref_id, 0, ref_length,
                                                        True)))
            if n_alns:
                self.assertEqual(len(self.interval_lists[ref_id]), n_alns)


class TestRegionSize(unittest.TestCase):

    """Test setting the region size for a set of references."""

    def test_region_size_override(self):
        """Test that a non-zero region_size takes precedence over other options.
        """

        r_size = summarize_coverage.get_region_size(
            1000000, 20, 500, 100, True)
        self.assertEqual(r_size, 500)

        r_size = summarize_coverage.get_region_size(100, 1, 6907, 100,
                                                    False)
        self.assertEqual(r_size, 6907)

    def test_honors_max_regions(self):
        """Test that when force_num_regions is False, MAX_NUM_REGIONS is used to set region size.
        """

        r_size = summarize_coverage.get_region_size(
            50000, 10000, 0, 100, False)

        ugly_expected_r_size = 50000.0 / \
            (summarize_coverage.Constants.MAX_NUM_REGIONS / 10000)
        pretty_expected_r_size = summarize_coverage.get_pretty_value(
            ugly_expected_r_size)
        self.assertEqual(r_size, pretty_expected_r_size)

    def test_force_num_regions(self):
        """Test that force_num_regions works."""

        r_size = summarize_coverage.get_region_size(50000, 10000, 0, 100, True)
        self.assertEqual(r_size, 500)


    @skip_if_data_dir_not_present
    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0, even though region size is 0 See
        bug 25079
        """
        from pbcore.util.Process import backticks
        import tempfile
#         als = os.path.join(self._data_dir, 'alignment_summary.gff')
#         variants = os.path.join(self._data_dir, 'variants.gff.gz')
#         ref = os.path.join(self._data_dir, 'ecoliK12_pbi_March2013')
        ref = pbcore.data.getLambdaFasta()
        tiny_reads = pbcore.data.getBamAndCmpH5()[0]
        out = os.path.join(tempfile.mkdtemp(suffix="summ_cov"), 'gff')
        cmd = 'summarize_coverage --region_size=0 --num_regions=500 {a} {r} {g}'.format(
            a=tiny_reads, r=ref, g=out)

        o, c, m = backticks(cmd)
        log.info(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            print(m)
        self.assertEquals(0, c)
        self.assertTrue(
            os.path.exists(os.path.join(out)))


class TestPrettyValue(unittest.TestCase):

    """Test that get_pretty_value produces reasonable values."""

    def primes(self, n):
        """ Returns  a list of primes < n """
        sieve = [True] * n
        for i in xrange(3, int(n ** 0.5) + 1, 2):
            if sieve[i]:
                sieve[i * i::2 * i] = [False] * ((n - i * i - 1) / (2 * i) + 1)
        return [2] + [i for i in xrange(3, n, 2) if sieve[i]]

    def test_pretty_is_nearby(self):
        """Test the pretty value is near the ugly value."""

        list_of_primes = self.primes(1000000)

        for prime in list_of_primes:
            pretty_prime = summarize_coverage.get_pretty_value(prime)

            diff_pct = min(
                abs(pretty_prime / float(prime) - 1),
                abs(prime / float(pretty_prime) - 1))

            # This is not a very tight bound, but it's what we've got
            self.assertTrue(diff_pct < 0.55 or abs(prime - pretty_prime) < 10)


class TestProjectIntoRegion(unittest.TestCase):

    def test_adds_half_open(self):
        """Test that intervals add up correctly and are interpreted as half-open.
        """

        region_start = 0
        region_end = 100

        intervals = []
        intervals.append(interval_tree.Interval(5, 10))
        intervals.append(interval_tree.Interval(10, 15))

        for i in range(10):
            intervals.append(interval_tree.Interval(30, 40))

        cov_arr = summarize_coverage.project_into_region(
            intervals, region_start, region_end)

        self.assertEqual(cov_arr[5], 1)
        self.assertEqual(cov_arr[10], 1)
        self.assertEqual(cov_arr[15], 0)
        self.assertEqual(cov_arr[30], 10)
        self.assertEqual(cov_arr[40], 0)

        self.assertEqual(len(cov_arr), 100)

    def test_shifts(self):
        """Test that interval bounds are shifted appropriately given the region start and end.
         """

        region_start = 1000
        region_end = 2000

        intervals = []
        intervals.append(interval_tree.Interval(500, 2500))
        cov_arr = summarize_coverage.project_into_region(
            intervals, region_start, region_end)
        self.assertEqual(numpy.max(cov_arr), 1)
        self.assertEqual(numpy.min(cov_arr), 1)
        self.assertEqual(len(cov_arr), 1000)

        intervals.append(interval_tree.Interval(500, 1500))
        cov_arr = summarize_coverage.project_into_region(
            intervals, region_start, region_end)
        self.assertTrue(all(cov_arr[:500] == 2))
        self.assertTrue(all(cov_arr[500:] == 1))

        intervals.append(interval_tree.Interval(1900, 10000))
        cov_arr = summarize_coverage.project_into_region(
            intervals, region_start, region_end)
        self.assertTrue(all(cov_arr[:500] == 2))
        self.assertTrue(all(cov_arr[500:900] == 1))
        self.assertTrue(all(cov_arr[900:] == 2))


class TestGaps(unittest.TestCase):

    """Test for gap enumeration in the coverage array. It just makes me suspicious.
    """

    def test_contiguous_gaps(self):
        """Test the counting of contiguous gaps in the coverage array.
        """
        region_start = 0
        region_end = 100

        intervals = []
        intervals.append(interval_tree.Interval(50, 55))
        cov_arr = summarize_coverage.project_into_region(
            intervals, region_start, region_end)
        n_gaps, tot_gaps = summarize_coverage.get_gaps_from_coverage(cov_arr)
        self.assertEqual(n_gaps, 2)
        self.assertEqual(tot_gaps, 95)

        intervals.append(interval_tree.Interval(75, 80))
        cov_arr = summarize_coverage.project_into_region(
            intervals, region_start, region_end)
        n_gaps, tot_gaps = summarize_coverage.get_gaps_from_coverage(cov_arr)
        self.assertEqual(n_gaps, 3)
        self.assertEqual(tot_gaps, 90)

    def test_random_gaps(self):
        """Test random coverage arrays for contiguous gap counting."""

        n_cases = 25
        full_interval_size = 10000
        n_regions_to_test = 50
        max_intervals = 10

        for case in xrange(n_cases):
            n_intervals = random.randrange(1, max_intervals)
            interval_list = []
            for i in xrange(n_intervals):
                ival_length = random.randrange(full_interval_size / 20)
                ival_start = random.randrange(full_interval_size - ival_length)
                ival_end = ival_start + ival_length
                interval_list.append(
                    interval_tree.Interval(ival_start, ival_end))

            cov_arr = summarize_coverage.project_into_region(
                interval_list, 0, full_interval_size)

            n_gaps, tot_gaps = summarize_coverage.get_gaps_from_coverage(
                cov_arr)
            exp_n_gaps, exp_tot_gaps = 0, 0
            for i in xrange(len(cov_arr) - 1):
                if cov_arr[i] == 0:
                    exp_tot_gaps += 1
                if cov_arr[i] != 0 and cov_arr[i + 1] == 0:
                    exp_n_gaps += 1
            if cov_arr[-1] == 0:
                exp_tot_gaps += 1
            if cov_arr[0] == 0:
                exp_n_gaps += 1

            self.assertEqual(n_gaps, exp_n_gaps)
            self.assertEqual(tot_gaps, exp_tot_gaps)


class TestSummarizeCoverage(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.summarize_coverage.summarize_coverage "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        pbcore.data.getBamAndCmpH5()[0],
        pbcore.data.getLambdaFasta()
    ]
    TASK_OPTIONS = {}


if __name__ == '__main__':
    unittest.main()
