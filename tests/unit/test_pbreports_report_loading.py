import os
import logging
import traceback
import json

from pbcore.util.Process import backticks
from numpy import ndarray
from base_test_case import BaseTestCase
from pbreports.io.filtered_summary_reader import FilteredSummaryReader
from pbreports.report.loading import (make_loading_report, _get_loading_table_and_attributes,
                                      _get_filtered_data, _get_counts_by_cell, _get_productivities,
                                      _get_column_labels, _get_columns)

log = logging.getLogger(__name__)


class TestLoadingRpt(BaseTestCase):

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

    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """
        log.info(TestLoadingRpt.test_exit_code_0.__doc__)

        csv = os.path.join(BaseTestCase.get_data_dir(), 'loading', 'filtered_summary_small.csv')
        cmd = 'pbreport loading {o} {r} {c}'.format(o=self.get_output_dir(),
                                                       r='foo.json',
                                                       c=csv)
        o, c, m = backticks(cmd)
        print "COMMAND: {c}".format(c=cmd)
        log.info(cmd)
        print "o: {o}".format(o=o)
        print "c: {c}".format(c=c)
        print "m: {m}".format(m=m)
        if c is not 0:
            log.error(m)
            log.error(o)
        self.assertEquals(0, c)

    def test_make_loading_report_no_csv(self):
        """
        Test that an IOError is thrown if no csv exists.
        """
        log.info(TestLoadingRpt.test_make_loading_report_no_csv.__doc__)

        def _test_ioerror():
            make_loading_report('foo', 'bar', self.get_output_dir())

        self.assertRaises(IOError, _test_ioerror)

    def test_make_loading_report(self):
        """
        Test the content of the report
        """
        try:
            log.info(TestLoadingRpt.test_make_loading_report.__doc__)
            csv = os.path.join(self.get_data_dir(), 'loading', 'filtered_summary.csv')

            make_loading_report(csv, 'l.json', self.get_output_dir())
            rpt = os.path.join(self.get_output_dir(), 'l.json')
            o = open(rpt, 'r')
            j = o.read()
            o.close()
            d = json.loads(j)

            t = d['tables'][0]
            c0 = t['columns'][0]
            c1 = t['columns'][1]
            c2 = t['columns'][2]
            c3 = t['columns'][3]
            c4 = t['columns'][4]

            self.assertEqual('SMRT Cell ID', c0['header'])
            self.assertEqual('loading.productivity.c0', c0['id'])
            self.assertEqual('m120128_025832_42129_c100277632550000001523007907041250', c0['values'][0])

            self.assertEqual('Productive ZMWs', c1['header'])
            self.assertEqual('loading.productivity.c1', c1['id'])
            self.assertEqual(150292, c1['values'][0])

            self.assertEqual('Productivity 0 (%)', c2['header'])
            self.assertEqual('loading.productivity.c2', c2['id'])
            self.assertAlmostEqual(.171, c2['values'][0], delta=.0003)

            self.assertEqual('Productivity 1 (%)', c3['header'])
            self.assertEqual('loading.productivity.c3', c3['id'])
            self.assertAlmostEqual(.573, c3['values'][0], delta=.0003)

            self.assertEqual('Productivity 2 (%)', c4['header'])
            self.assertEqual('loading.productivity.c4', c4['id'])
            self.assertAlmostEqual(.256, c4['values'][0], delta=.0003)

        except:
            log.error(traceback.format_exc())
            raise

    def test_get_filtered_data(self):
        """
        Test that the data set gets filtered.
        """
        try:
            log.info(TestLoadingRpt.test_get_filtered_data.__doc__)
            csv = os.path.join(self.get_data_dir(), 'loading', 'filtered_summary.csv')

            # read in the raw csv
            reader = FilteredSummaryReader(csv)
            reader.load()

            # count np rows after filter
            a = 0
            data = _get_filtered_data(csv)
            for r in data:
                a += 1

            self.assertTrue(a < reader.num_records)

        except:
            log.error(traceback.format_exc())
            raise

    def test_get_counts_by_cell(self):
        """
        Test the count dictionary created by iterating over np data array
        """
        try:
            log.info(TestLoadingRpt.test_get_counts_by_cell.__doc__)
            csv = os.path.join(self.get_data_dir(), 'loading', 'filtered_summary.csv')

            # read in the raw csv
            reader = FilteredSummaryReader(csv)
            reader.load()
            data = _get_filtered_data(csv)

            cbc = _get_counts_by_cell(data)
            self.assertEquals(1, len(cbc))

        except:
            log.error(traceback.format_exc())
            raise

    def test_get_productivities(self):
        """
        Test productivities array
        """
        try:
            log.info(TestLoadingRpt.test_get_productivities.__doc__)
            self.assertSequenceEqual([0, 1, 2], _get_productivities())
        except:
            log.error(traceback.format_exc())
            raise

    def test_get_column_labels(self):
        """
        Test that column labels render with dependence on productivities
        """
        try:
            log.info(TestLoadingRpt.test_get_column_labels.__doc__)
            exp = ['SMRT Cell ID', 'Productive ZMWs',
                   'Productivity 0 (%)', 'Productivity 1 (%)', 'Productivity 2 (%)']
            self.assertSequenceEqual(exp, _get_column_labels())
        except:
            log.error(traceback.format_exc())
            raise

    def test_get_columns(self):
        """
        Test method that returns list of columns objects
        """

        try:
            log.info(TestLoadingRpt.test_get_columns.__doc__)
            labels = ['SMRT Cell ID', 'Productive ZMWs',
                      'Productivity 0 (%)', 'Productivity 1 (%)', 'Productivity 2 (%)']
            cols = _get_columns()
            for i in range(len(labels)):
                self.assertEqual(labels[i], cols[i].header)
                self.assertEqual('c{i}'.format(i=i), cols[i].id)
        except:
            log.error(traceback.format_exc())
            raise

    def test_get_summary_attributes(self):
        """
        Test method that returns a list of attributes
        """
        try:

            log.info(TestLoadingRpt.test_get_summary_attributes.__doc__)
            expected = ['productivity_c1', 'productivity_c2', 'productivity_c3', 'productivity_c4']

            num_cells = 4

            csv = os.path.join(self.get_data_dir(), 'loading', 'filtered_summary.csv')

            # read in the raw csv
            reader = FilteredSummaryReader(csv)
            reader.load()

            np_arr = _get_filtered_data(csv)
            self.assertIs(type(np_arr), ndarray)

            atts = _get_loading_table_and_attributes(np_arr)
            for i in range(len(expected)):
                for j in atts:
                    self.assertIsNotNone(j)


        except:
            log.error(traceback.format_exc())
            raise