import os
import logging
import subprocess
import unittest

from pbcore.io import IndexedBamReader

from base_test_case import ROOT_DATA_DIR
from pbreports.io.align import from_alignment_file, alignment_info_from_bam

log = logging.getLogger(__name__)
IO_DATA_DIR = os.path.join(ROOT_DATA_DIR, 'io')


class TestBam(unittest.TestCase):
    """Test the from_alignment_file function that does
    all the alignment file reading for mapping_stats.py
    """

    @classmethod
    def setUpClass(cls):
        bam_name = "lambda_aligned.bam"
        cls.bam_path = os.path.join(IO_DATA_DIR, bam_name)
        cls.movie = 'm150404_101626_42267_c100807920800000001823174110291514_s1_p0'
        movie_names, unrolled, datum, columns = from_alignment_file(cls.movie, cls.bam_path)
        cls.datum = datum
        cls.unrolled = unrolled
        cls.movie_names = movie_names
        cls.columns = columns

        log.info("Loading alignments from {c}".format(c=cls.bam_path))

    def test_read_aligned_bam(self):
        self.assertEqual(list(self.movie_names)[0], self.movie)

    def test_movie_names(self):
        nmovies = 1
        self.assertEqual(len(self.movie_names), nmovies)

    def test_unrolled(self):
        n = 1491
        self.assertEqual(len(self.unrolled), n)

    def test_datum(self):
        n = 18768
        self.assertEqual(len(self.datum), n)

    def test_columns(self):
        n = 5
        self.assertEqual(len(self.columns), n)

    def test_alignment_info_from_bam(self):
        movie = "m150404_101626_42267_c100807920800000001823174110291514_s1_p0"
        datum, unrolled, max_subread, movie_names = alignment_info_from_bam(
            self.bam_path, movie)
        self.assertEqual(max_subread[(movie, 17417)],
            (('m150404_101626_42267_c100807920800000001823174110291514_s1_p0', 17417, 1196, 3131), 1925))
        self.assertEqual(max_subread[(movie, 27338)],
            (('m150404_101626_42267_c100807920800000001823174110291514_s1_p0', 27338, 4356, 5498), 1115))
