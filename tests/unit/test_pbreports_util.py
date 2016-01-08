import logging
import traceback
import os
import unittest
import nose

from base_test_case import BaseTestCase
from pbreports.util import (validate_output_dir, validate_report,
                            movie_to_cell, get_fasta_readlengths,
                            compute_n50_from_file, compute_n50,
                            validate_file, validate_nonempty_file)

from base_test_case import ROOT_DATA_DIR

_NAME = 'amplicon_analysis_consensus'
_EMPTY = 'amplicon_analysis_consensus_empty'
_FILE = 'amplicon_analysis_summary.csv'
DATA_ABS_PATH = os.path.join(ROOT_DATA_DIR, _NAME, _FILE)
EMPTY_ABS_PATH = os.path.join(ROOT_DATA_DIR, _EMPTY, _FILE)
DATA_REL_PATH = os.path.relpath( DATA_ABS_PATH )
EMPTY_REL_PATH = os.path.relpath( EMPTY_ABS_PATH )

log = logging.getLogger(__name__)


class TestFunctions(unittest.TestCase):

    def test_01_compute_n50(self):
        x = [6, 5, 4]
        n = compute_n50(x)
        self.assertEqual(n, 5)

    def test_02_compute_n50(self):
        x = [91, 77, 70, 69, 62, 56, 45, 29, 16, 4]
        n = compute_n50(x)
        self.assertEqual(n, 69)


class TestUtil(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()

    def setUp(self):
        """
        Before *every* test
        """
        try:
            BaseTestCase.setUp(self)
        except Exception as err:
            log.error(err)
            tb = traceback.format_exc()
            log.error(tb)
            raise
        log.debug("In setUp()")

    def tearDown(self):
        """
        After *every* test
        """
        try:
            BaseTestCase.tearDown(self)
        except Exception as err:
            log.error(err)
            tb = traceback.format_exc()
            log.error(tb)
            raise

    def test_validate_file(self):
        """
        Test: Return abspath if file found
        """
        file_path = validate_file( DATA_REL_PATH )
        self.assertEqual( file_path, DATA_ABS_PATH )

    @nose.tools.raises(IOError)
    def test_validate_file_fails(self):
        """
        Test: Raise IOError if file not found
        """
        validate_file( "this_file_doesn't_exist" )

    def test_validate_nonempty_file(self):
        """
        Test: Return abspath if file found and not empty
        """
        file_path = validate_nonempty_file( DATA_REL_PATH )
        self.assertEqual( file_path, DATA_ABS_PATH )

    @nose.tools.raises(IOError)
    def test_validate_nonempty_file_fails(self):
        """
        Test: Raise IOError if file found but empty
        """
        validate_nonempty_file( EMPTY_REL_PATH )

    def test_validate_report(self):
        """
        Test: Raise ValueError if report has path sep
        """
        try:

            log.info(TestUtil.test_validate_report.__doc__)

            # we know this gets made
            validate_report('foo')

            try:
                validate_report('/foo')
                self.fail('No path separators allowed')
            except ValueError:
                pass

        except:
            log.error(traceback.format_exc())
            raise

    def test_validate_output_dir(self):
        """
        Test: Raise IOError if output does not exist
        """
        try:

            log.info(TestUtil.test_validate_output_dir.__doc__)

            # we know this gets made
            validate_output_dir(self.get_output_dir())

            try:
                validate_output_dir('/whatev')
                self.fail('Did not validate dir')
            except IOError:
                pass

        except:
            log.error(traceback.format_exc())
            raise

    def test_movie_2_cell(self):
        """
        Parse a cell name from a movie name
        """
        try:

            log.info(TestUtil.test_movie_2_cell.__doc__)
            self.assertEqual('m120128_025832_42129_c100277632550000001523007907041250',
                             movie_to_cell('m120128_025832_42129_c100277632550000001523007907041250_s2_p0'))

        except:
            log.error(traceback.format_exc())
            raise
        
        
    def test_get_fasta_readlengths(self):
        """
        Test getting num reads and total readlength
        """
        with self.assertRaises(IOError):
            get_fasta_readlengths('what.ever')
            
        fasta = os.path.join( ROOT_DATA_DIR, 'polished_assembly', 'polished_assembly.fasta.gz')
        l = get_fasta_readlengths(fasta)
        self.assertEqual( 2, len(l) )
        self.assertEqual( 47938, sum(l) )
        
    def test_compute_n50_from_file(self):
        """
        Test getting N50 from file
        """
        with self.assertRaises(IOError):
            get_fasta_readlengths('what.ever')
            
        fasta = os.path.join( ROOT_DATA_DIR, 'polished_assembly', 'polished_assembly.fasta.gz')
        self.assertEqual( 33586, compute_n50_from_file(fasta) )
        
        
    def test_compute_n50_from_readlenths(self):
        """
        Test getting N50 from length list
        """
        fasta = os.path.join( ROOT_DATA_DIR, 'polished_assembly', 'polished_assembly.fasta.gz')
        l = get_fasta_readlengths(fasta)
        self.assertEqual( 33586, compute_n50(l) )
