
import os
import logging
import subprocess
import unittest

from pbcore.io import IndexedBamReader

import pbtestdata

from pbreports.io.align import from_alignment_file, alignment_info_from_bam

from base_test_case import ROOT_DATA_DIR, skip_if_data_dir_not_present

log = logging.getLogger(__name__)
IO_DATA_DIR = os.path.join(ROOT_DATA_DIR, 'io')


class TestBam(unittest.TestCase):

    """
    Test the from_alignment_file function that does
    all the alignment file reading for mapping_stats.py
    """
    BAM_PATH = pbtestdata.get_file("aligned-bam")
    MOVIE = "m140905_042212_sidney_c100564852550000001823085912221377_s1_X0"
    EXPECTED_VALUES = {
        "nmovies": 1,
        "unrolled": 48,
        "ndata": 112,
        "ncolumns": 5,
    }

    @classmethod
    def setUpClass(cls):
        log.info("Loading alignments from {c}".format(c=cls.BAM_PATH))
        movie_names, unrolled, datum, columns = from_alignment_file(
            alignment_info_from_bam(cls.BAM_PATH)[cls.MOVIE])
        cls.datum = datum
        cls.unrolled = unrolled
        cls.movie_names = movie_names
        cls.columns = columns

    def test_read_aligned_bam(self):
        self.assertEqual(list(self.movie_names)[0], self.MOVIE)

    def test_movie_names(self):
        self.assertEqual(
            len(self.movie_names), self.EXPECTED_VALUES["nmovies"])

    def test_unrolled(self):
        self.assertEqual(len(self.unrolled), self.EXPECTED_VALUES["unrolled"])

    def test_datum(self):
        self.assertEqual(len(self.datum), self.EXPECTED_VALUES["ndata"])

    def test_columns(self):
        self.assertEqual(len(self.columns), self.EXPECTED_VALUES["ncolumns"])

    def test_alignment_info_from_bam(self):
        raise unittest.SkipTest("FIXME")


@skip_if_data_dir_not_present
class TestBamLarge(TestBam):
    BAM_PATH = os.path.join(IO_DATA_DIR, "lambda_aligned.bam")
    MOVIE = "m150404_101626_42267_c100807920800000001823174110291514_s1_p0"
    EXPECTED_VALUES = {
        "nmovies": 1,
        "unrolled": 1491,
        "ndata": 18768,
        "ncolumns": 5,
    }

    @classmethod
    @skip_if_data_dir_not_present
    def setUpClass(cls):
        super(TestBamLarge, cls).setUpClass()

    def test_alignment_info_from_bam(self):
        datum, unrolled, max_subread, movie_names = alignment_info_from_bam(
            self.BAM_PATH)[self.MOVIE].as_tuple()
        self.assertEqual(max_subread[(self.MOVIE, 17417)],
                         ((self.MOVIE, 17417, 1196, 3131), 1925))
        self.assertEqual(max_subread[(self.MOVIE, 27338)],
                         ((self.MOVIE, 27338, 4356, 5498), 1115))
