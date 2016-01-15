
import os
import logging
import traceback
import json
import unittest
import tempfile
import shutil

from numpy import ndarray

from pbcore.util.Process import backticks
import pbcore.data.datasets as data

from pbreports.io.filtered_summary_reader import FilteredSummaryReader
from pbreports.report.loading_xml import to_report as make_loading_report
from pbreports.report.filter_stats_xml import to_report as make_filter_report
from pbreports.report.adapter_xml import to_report as make_adapter_report

log = logging.getLogger(__name__)


class TestXMLstatsRpts(unittest.TestCase):

    def setUp(self):
        """
        Before *every* test
        """
        super(TestXMLstatsRpts, self).setUp()
        self.cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def get_output_dir(self):
        return self.tmpdir

    def tearDown(self):
        """
        After *every* test
        """
        os.chdir(self.cwd)
        shutil.rmtree(self.tmpdir)
        super(TestXMLstatsRpts, self).tearDown()

    def test_loading_exit_code_0(self):
        log.info(TestXMLstatsRpts.test_loading_exit_code_0.__doc__)
        sts_xml = data.getStats(0)
        cmd = 'loading_xml {c} {r}'.format(
            r='foo.json',
            c=sts_xml)
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

    def test_adapter_exit_code_0(self):
        log.info(TestXMLstatsRpts.test_adapter_exit_code_0.__doc__)
        sts_xml = data.getStats(0)
        cmd = 'adapter_xml {c} {r}'.format(
            r='foo.json',
            c=sts_xml)
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

    def test_filter_exit_code_0(self):
        log.info(TestXMLstatsRpts.test_filter_exit_code_0.__doc__)
        tmpdir = tempfile.mkdtemp()
        cwd = os.getcwd()
        sts_xml = data.getStats(0)
        cmd = 'filter_stats_xml {c} {r}'.format(
            r='foo.json',
            c=sts_xml)
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
        log.info(TestXMLstatsRpts.test_make_loading_report_no_csv.__doc__)

        def _test_ioerror():
            make_loading_report('foo')

        self.assertRaises(IOError, _test_ioerror)

    def test_make_loading_report_with_sts_xml(self):
        """
        Test the content of the loading report generated from a sts.xml
        """
        try:
            log.info(
                TestXMLstatsRpts.test_make_loading_report_with_sts_xml.__doc__)
            sts_xml = data.getStats(0)

            rpt = make_loading_report(sts_xml)
            d = json.loads(rpt.to_json())

            t = d['tables'][0]
            c0 = t['columns'][0]
            c1 = t['columns'][1]
            c2 = t['columns'][2]
            c3 = t['columns'][3]
            c4 = t['columns'][4]

            self.assertEqual('Collection Context', c0['header'])
            self.assertEqual('loading_xml_report.loading_xml_table.'
                             'collection_context', c0['id'])
            self.assertEqual('NA', c0['values'][0])

            self.assertEqual('Productive ZMWs', c1['header'])
            self.assertEqual('loading_xml_report.loading_xml_table.'
                             'productive_zmws', c1['id'])
            self.assertEqual(2876, c1['values'][0])

            self.assertEqual('Productivity 0 (%)',
                             c2['header'])
            self.assertEqual('loading_xml_report.loading_xml_table.'
                             'productivity_0',
                             c2['id'])
            self.assertAlmostEqual(54.80, c2['values'][0], delta=.0003)

            self.assertEqual('Productivity 1 (%)',
                             c3['header'])
            self.assertEqual('loading_xml_report.loading_xml_table.'
                             'productivity_1',
                             c3['id'])
            self.assertAlmostEqual(31.33, c3['values'][0], delta=.0003)

            self.assertEqual('Productivity 2 (%)',
                             c4['header'])
            self.assertEqual('loading_xml_report.loading_xml_table.'
                             'productivity_2',
                             c4['id'])
            self.assertAlmostEqual(13.87, c4['values'][0], delta=.0003)

        except:
            log.error(traceback.format_exc())
            raise

    def test_make_loading_report_with_dataset(self):
        """
        Test the content of the loading report generated from a dataset
        """
        try:
            log.info(
                TestXMLstatsRpts.test_make_loading_report_with_dataset.__doc__)
            sts_xml = data.getXmlWithStats()


            rpt = make_loading_report(sts_xml)
            d = json.loads(rpt.to_json())

            t = d['tables'][0]
            c0 = t['columns'][0]
            c1 = t['columns'][1]
            c2 = t['columns'][2]
            c3 = t['columns'][3]
            c4 = t['columns'][4]

            self.assertEqual('Collection Context', c0['header'])
            self.assertEqual('loading_xml_report.loading_xml_table.'
                             'collection_context', c0['id'])
            self.assertEqual('Combined', c0['values'][0])
            # Turn these back on when a context is inserted in the testdataset:
            #self.assertEqual('dummy1', c0['values'][1])
            #self.assertEqual('dummy2', c0['values'][2])
            self.assertEqual('NA', c0['values'][1])
            self.assertEqual('NA', c0['values'][2])

            self.assertEqual('Productive ZMWs', c1['header'])
            self.assertEqual('loading_xml_report.loading_xml_table.'
                             'productive_zmws', c1['id'])
            self.assertEqual(153168, c1['values'][0])
            self.assertEqual(2876, c1['values'][1])
            self.assertEqual(150292, c1['values'][2])

            self.assertEqual('Productivity 0 (%)',
                             c2['header'])
            self.assertEqual('loading_xml_report.loading_xml_table.'
                             'productivity_0',
                             c2['id'])
            self.assertAlmostEqual(78.98, c2['values'][0], delta=.0003)
            self.assertAlmostEqual(54.80, c2['values'][1], delta=.0003)
            self.assertAlmostEqual(79.45, c2['values'][2], delta=.0003)

            self.assertEqual('Productivity 1 (%)',
                             c3['header'])
            self.assertEqual('loading_xml_report.loading_xml_table.'
                             'productivity_1',
                             c3['id'])
            self.assertAlmostEqual(16.4, c3['values'][0], delta=.0003)
            self.assertAlmostEqual(31.33, c3['values'][1], delta=.0003)
            self.assertAlmostEqual(16.12, c3['values'][2], delta=.0003)

            self.assertEqual('Productivity 2 (%)',
                             c4['header'])
            self.assertEqual('loading_xml_report.loading_xml_table.'
                             'productivity_2',
                             c4['id'])
            self.assertAlmostEqual(4.61 , c4['values'][0], delta=.0003)
            self.assertAlmostEqual(13.87, c4['values'][1], delta=.0003)
            self.assertAlmostEqual(4.44, c4['values'][2], delta=.0003)

        except:
            log.error(traceback.format_exc())
            raise

    def test_make_adapter_report_sts_xml(self):
        """
        Test make_adapter_report with an sts.xml file
        """
        # All of the histogram generation code should be tested in
        # pbcore.io.dataset, not here. Just test the report.
        try:
            log.info(
                TestXMLstatsRpts.test_make_adapter_report_sts_xml.__doc__)
            sts_xml = data.getStats(1)
            rpt = make_adapter_report(sts_xml, self.get_output_dir())

            d = json.loads(rpt.to_json())

            t = d['tables'][0]
            c0 = t['columns'][0]
            c1 = t['columns'][1]

            self.assertEqual('Adapter Dimers (0-10bp)', c0['values'][0])
            self.assertEqual('Short Inserts (11-100bp)', c0['values'][1])
            self.assertEqual(0.0, c1['values'][0])
            self.assertEqual(0.0, c1['values'][1])
            self.assertTrue(os.path.exists(os.path.join(
                self.get_output_dir(),
                'interAdapterDist0.png')))

        except:
            log.error(traceback.format_exc())
            raise

    def test_make_adapter_report_dataset(self):
        """
        Test make_adapter_report with a dataset
        """
        # All of the histogram generation code should be tested in
        # pbcore.io.dataset, not here. Just test the report.
        try:
            log.info(
                TestXMLstatsRpts.test_make_adapter_report_dataset.__doc__)
            sts_xml = data.getXmlWithStats()
            rpt = make_adapter_report(sts_xml, self.get_output_dir())

            d = json.loads(rpt.to_json())

            t = d['tables'][0]
            c0 = t['columns'][0]
            c1 = t['columns'][1]

            self.assertEqual('Adapter Dimers (0-10bp)', c0['values'][0])
            self.assertEqual('Short Inserts (11-100bp)', c0['values'][1])
            self.assertEqual(0.0, c1['values'][0])
            self.assertEqual(0.0, c1['values'][1])
            self.assertTrue(os.path.exists(os.path.join(
                self.get_output_dir(),
                'interAdapterDist0.png')))
            self.assertTrue(os.path.exists(os.path.join(
                self.get_output_dir(),
                'interAdapterDist1.png')))

        except:
            log.error(traceback.format_exc())
            raise

    def test_make_filter_stats_report_sts_xml(self):
        """
        Test the content of the filter report generated from an sts.xml
        """
        try:
            log.info(
                TestXMLstatsRpts.test_make_filter_stats_report_sts_xml.__doc__)
            sts_xml = data.getStats(0)

            rpt = make_filter_report(sts_xml, self.get_output_dir())

            d = json.loads(rpt.to_json())

            t = d['tables'][0]
            c0 = t['columns'][0]
            c1 = t['columns'][1]
            self.assertEqual('Metrics', c0['header'])
            self.assertEqual('filtering_stats_xml_report.filter_xml_table.'
                             'filter_names_column', c0['id'])
            self.assertEqual('Polymerase Read Bases', c0['values'][0])
            self.assertEqual('Polymerase Reads', c0['values'][1])
            self.assertEqual('Polymerase Read N50', c0['values'][2])
            self.assertEqual('Polymerase Read Length', c0['values'][3])
            self.assertEqual('Polymerase Read Quality', c0['values'][4])

            self.assertEqual('Values', c1['header'])
            self.assertEqual('filtering_stats_xml_report.filter_xml_table.'
                             'filter_stats_column', c1['id'])
            self.assertEqual(4464266.29, c1['values'][0])
            self.assertEqual(901, c1['values'][1])
            self.assertEqual(0, c1['values'][2])
            self.assertEqual(4954.79, c1['values'][3])
            self.assertEqual(0.83, c1['values'][4])
            self.assertTrue(os.path.exists(os.path.join(
                self.get_output_dir(),
                'readLenDist0.png')))
            self.assertTrue(os.path.exists(os.path.join(
                self.get_output_dir(),
                'readQualDist0.png')))

        except:
            log.error(traceback.format_exc())
            raise

    def test_make_filter_stats_report_dataset(self):
        """
        Test the content of the filter report generated from a dataset
        """
        try:
            log.info(
                TestXMLstatsRpts.test_make_filter_stats_report_dataset.__doc__)
            sts_xml = data.getXmlWithStats()

            rpt = make_filter_report(sts_xml, self.get_output_dir())

            d = json.loads(rpt.to_json())

            t = d['tables'][0]
            c0 = t['columns'][0]
            c1 = t['columns'][1]
            self.assertEqual('Metrics', c0['header'])
            self.assertEqual('filtering_stats_xml_report.filter_xml_table.'
                             'filter_names_column', c0['id'])
            self.assertEqual('Polymerase Read Bases', c0['values'][0])
            self.assertEqual('Polymerase Reads', c0['values'][1])
            self.assertEqual('Polymerase Read N50', c0['values'][2])
            self.assertEqual('Polymerase Read Length', c0['values'][3])
            self.assertEqual('Polymerase Read Quality', c0['values'][4])

            self.assertEqual('Values', c1['header'])
            self.assertEqual('filtering_stats_xml_report.filter_xml_table.'
                             'filter_stats_column', c1['id'])
            self.assertEqual(393167212.65, c1['values'][0])
            self.assertEqual(25123, c1['values'][1])
            self.assertEqual(0, c1['values'][2])
            self.assertEqual(15649.69, c1['values'][3])
            self.assertEqual(0.86, c1['values'][4])
            self.assertTrue(os.path.exists(os.path.join(
                self.get_output_dir(),
                'readLenDist0.png')))
            self.assertTrue(os.path.exists(os.path.join(
                self.get_output_dir(),
                'readQualDist0.png')))
            self.assertTrue(os.path.exists(os.path.join(
                self.get_output_dir(),
                'readLenDist1.png')))
            self.assertTrue(os.path.exists(os.path.join(
                self.get_output_dir(),
                'readQualDist1.png')))

        except:
            log.error(traceback.format_exc())
            raise
