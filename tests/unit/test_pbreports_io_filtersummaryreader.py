import os
import logging
import traceback

from base_test_case import BaseTestCase, skip_if_data_dir_not_present
from pbreports.io.filtered_summary_reader import FilteredSummaryReader

log = logging.getLogger(__name__)


@skip_if_data_dir_not_present
class TestFilteredSummaryReader(BaseTestCase):

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

    def test_io_error(self):
        """
        Test: Throws IOError in constructor
        """
        log.info(TestFilteredSummaryReader.test_io_error.__doc__)
        try:
            FilteredSummaryReader('/i/dont/exits')
            self.fail('Should have thrown IOError')
        except IOError:
            pass
        except:
            log.error(traceback.format_exc())
            raise

    def test_count_records(self):
        """
        Test: Count num csv records
        """
        try:

            log.info(TestFilteredSummaryReader.test_count_records.__doc__)
            fsr = FilteredSummaryReader(os.path.join(
                BaseTestCase.get_data_dir(), 'loading', 'filtered_summary_small.csv'))
            fsr.load()
            self.assertEqual(2, fsr.num_records)

        except:
            log.error(traceback.format_exc())
            raise

    def test_get_column_data(self):
        """
        Test: Assert array equals when getting column data
        """
        try:
            log.info(TestFilteredSummaryReader.test_count_records.__doc__)
            fsr = FilteredSummaryReader(os.path.join(
                BaseTestCase.get_data_dir(), 'loading', 'filtered_summary_small.csv'))
            fsr.load()

            ri_exp = ['m120128_025832_42129_c100277632550000001523007907041250_s2_p0/0',
                      'm120128_025832_42129_c100277632550000001523007907041250_s2_p0/1']
            ri_act = []

            data = fsr.data_as_numpy_array()
            for row in data:
                ri_act.append(row['ReadId'])

            self.assertSequenceEqual(ri_exp, ri_act)

        except:
            log.error(traceback.format_exc())
            raise

    def test_num_reads(self):
        """
        Test: get num reads from csv
        """
        try:
            log.info(TestFilteredSummaryReader.test_num_reads.__doc__)
            fsr = FilteredSummaryReader(os.path.join(BaseTestCase.get_data_dir(),
                                                     'loading', 'filtered_summary_small.csv'))
            fsr.load()

            self.assertEqual(1, fsr.num_reads)

        except:
            log.error(traceback.format_exc())
            raise
