
import os
import logging
import traceback
import json
import unittest
import tempfile
import shutil

from numpy import ndarray

from pbcore.io.dataset.DataSetIO import InvalidDataSetIOError
from pbcore.util.Process import backticks
import pbcore.data.datasets as data
import pbcore.data
from pbcore.io import SubreadSet

from pbreports.util import dist_shaper, continuous_dist_shaper
from pbreports.io.filtered_summary_reader import FilteredSummaryReader
from pbreports.report.loading_xml import to_report as make_loading_report
from pbreports.report.filter_stats_xml import to_report as make_filter_report
from pbreports.report.filter_stats_xml import Constants
from pbreports.report.adapter_xml import to_report as make_adapter_report

log = logging.getLogger(__name__)

def _internal_data():
    if os.path.exists("/pbi/dept/secondary/siv/testdata"):
        return True
    return False

def get_fixed_bin_sts():
    sfn = ('/pbi/dept/secondary/siv/testdata/pbreports-unittest/data/'
           'sts_xml/3120134-r54009_20160323_173308-1_A01-Bug30772/'
           'm54009_160323_173323.sts.xml')
    return sfn

def get_fixed_bin_dataset():
    sfn = get_fixed_bin_sts()
    sset = SubreadSet()
    sset.loadStats(sfn)
    return sset


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
        subreads_xml = data.getXmlWithStats()
        cmd = 'adapter_xml {c} {r}'.format(
            r='foo.json',
            c=subreads_xml)
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

        self.assertRaises((InvalidDataSetIOError, IOError), _test_ioerror)

    def test_make_loading_report_with_sts_xml(self):
        """
        Test the content of the loading report generated from a sts.xml
        """
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

    def test_make_loading_report_with_dataset(self):
        """
        Test the content of the loading report generated from a dataset
        """
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
        self.assertAlmostEqual(4.61, c4['values'][0], delta=.0003)
        self.assertAlmostEqual(13.87, c4['values'][1], delta=.0003)
        self.assertAlmostEqual(4.44, c4['values'][2], delta=.0003)

    def test_make_adapter_report_dataset(self):
        """
        Test make_adapter_report with a dataset
        """
        # All of the histogram generation code should be tested in
        # pbcore.io.dataset, not here. Just test the report.
        log.info(
            TestXMLstatsRpts.test_make_adapter_report_dataset.__doc__)
        sts_xml = data.getXmlWithStats()
        rpt = make_adapter_report(sts_xml, self.get_output_dir())
        d = json.loads(rpt.to_json())
        a = d['attributes']
        self.assertEqual(a[0]['name'], 'Adapter Dimers (0-10bp)')
        self.assertEqual(a[0]['value'], 0.0)
        self.assertEqual(a[1]['value'], 0.0)
        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'interAdapterDist0.png')))
        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'interAdapterDist1.png')))

    def _compare_attribute_values(self, report_d, expected_d):
        attr = report_d['attributes']
        attr_d = {a_['id'].split(".")[-1]:a_['value'] for a_ in attr}
        for id_, val in expected_d.iteritems():
            self.assertEqual(attr_d[id_], val)


    def test_make_filter_stats_report_sts_xml(self):
        """
        Test the content of the filter report generated from an sts.xml
        """
        log.info(
            TestXMLstatsRpts.test_make_filter_stats_report_sts_xml.__doc__)
        sts_xml = data.getStats(0)

        rpt = make_filter_report(sts_xml, self.get_output_dir())

        d = json.loads(rpt.to_json())
        self._compare_attribute_values(
            report_d=d,
            expected_d={
                Constants.A_NBASES:  4080353,
                Constants.A_NREADS: 901,
                Constants.A_READ_N50: 6570,
                Constants.A_READ_LENGTH: 4529,
        #        Constants.A_READ_QUALITY: 0.83
            })

        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'readLenDist0.png')))
        #self.assertTrue(os.path.exists(os.path.join(
        #    self.get_output_dir(),
        #    'readQualDist0.png')))

        # these are from a raw STS file
        self.assertEqual(len(rpt._dataset_uuids), 0,
                         "Incorrect report datasets uuids")

    def test_make_filter_stats_report_dataset(self):
        """
        Test the content of the filter report generated from a dataset
        """
        log.info(
            TestXMLstatsRpts.test_make_filter_stats_report_dataset.__doc__)
        sts_xml = data.getXmlWithStats()

        rpt = make_filter_report(sts_xml, self.get_output_dir())

        d = json.loads(rpt.to_json())
        self._compare_attribute_values(
            report_d=d,
            expected_d={
                Constants.A_NBASES:  342348413,
                Constants.A_NREADS: 25123,
                Constants.A_READ_N50: 21884,
                Constants.A_READ_LENGTH: 13627,
         #       Constants.A_READ_QUALITY: 0.86
            })

        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'readLenDist0.png')))
        # FIXME temporarily disabled
        #self.assertTrue(os.path.exists(os.path.join(
        #    self.get_output_dir(),
        #    'readQualDist0.png')))
        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'readLenDist1.png')))
        #self.assertTrue(os.path.exists(os.path.join(
        #    self.get_output_dir(),
        #    'readQualDist1.png')))

    @unittest.skipIf(not _internal_data(),
                     "Internal data not available")
    def test_reports_with_fixed_bins(self):
        # TODO readQualDists are currently unpopulated, turn back on when
        # they're repopulated
        #for dist_name, nbins in zip(['medianInsertDists', 'readLenDists',
        #                             'readQualDists'], [200, 200, 50]):
        for dist_name, nbins in zip(['medianInsertDists', 'readLenDists'],
                                    [200, 200]):
            ss = SubreadSet()
            ss.loadStats(get_fixed_bin_sts())

            ss2 = SubreadSet()
            ss2.loadStats(get_fixed_bin_sts())

            # shift ss2
            mdist = getattr(ss2.metadata.summaryStats, dist_name)[0].bins
            mdist = [0, 0, 0] + mdist[:-3]
            getattr(ss2.metadata.summaryStats, dist_name)[0].bins = mdist


            ss3 = ss + ss2

            ss4 = SubreadSet()
            ss4.loadStats(get_fixed_bin_sts())

            # shift ss4
            mdist = getattr(ss4.metadata.summaryStats, dist_name)[0].bins
            mdist = [0 for _ in mdist]
            getattr(ss4.metadata.summaryStats, dist_name)[0].bins = mdist

            dists = getattr(ss4.metadata.summaryStats, dist_name)
            self.assertEqual(len(dists), 1)
            for n in [0, 1, 2, 10, 40, 41, 49, 50, 51, 200, 500]:
                ds = continuous_dist_shaper(dists, nbins=n)
                fixed_dists = [ds(dist) for dist in dists]
                self.assertEqual(len(dists[0].bins), nbins)
                self.assertEqual(len(fixed_dists[0].bins), nbins)
                self.assertEqual(sum(dists[0].bins),
                                 sum(fixed_dists[0].bins))

            sss = [ss, ss2, ss3]

            for sset in sss:
                dists = getattr(sset.metadata.summaryStats, dist_name)
                self.assertEqual(len(dists), 1)
                # 0, requested nbins > numBins fails back to no-op
                ops = [1, 2, 3, 4, 7, 10, 40, 41, 49, 50, 51, 200, 500]
                no_ops = [0]
                for n in no_ops:
                    ds = continuous_dist_shaper(dists, nbins=n)
                    fixed_dists = [ds(dist) for dist in dists]
                    self.assertEqual(len(dists[0].bins), nbins)
                    self.assertEqual(len(fixed_dists[0].bins), nbins)
                    self.assertEqual(sum(dists[0].bins),
                                     sum(fixed_dists[0].bins))

                for n in ops:
                    ds = continuous_dist_shaper(dists, nbins=n)
                    fixed_dists = [ds(dist) for dist in dists]
                    self.assertEqual(len(dists[0].bins), nbins)
                    self.assertEqual(len(fixed_dists[0].bins), n)
                    self.assertEqual(sum(dists[0].bins),
                                     sum(fixed_dists[0].bins))

    @unittest.skipIf(not _internal_data(),
                     "Internal data not available")
    def test_abstract_dist_shaper(self):
        bins1 = [0, 2, 3, 4, 3, 2, 0, 0, 0, 0]
        labels1 = [i*5 for i in range(len(bins1))]
        bins2 = [0, 2, 3, 4, 3, 2, 0, 0, 0, 0, 0, 0, 0]
        labels2 = [25 + i * 5 for i in range(len(bins2))]
        dist_list = [(bins1, labels1), (bins2, labels2)]
        merged = [0, 2, 3, 4, 3, 2, 2, 3, 4, 3, 2, 0, 0, 0, 0, 0, 0, 0]
        for nbins in range(1, 100):
            shaper = dist_shaper(dist_list, nbins=nbins)
            for dist in dist_list:
                bins, labels = shaper(dist)
                self.assertEqual(len(bins), len(labels))
                self.assertEqual(len(bins), nbins)
                self.assertEqual(sum(bins), sum(dist[0]))
                """
                if nbins > len(merged):
                    self.assertEqual(bins, merged)
                    self.assertEqual(labels,
                                     [i*5 for i in range(len(merged))])
                """

    @unittest.skipIf(not _internal_data(),
                     "Internal data not available")
    def test_abstract_dist_shaper_float_bwidth(self):
        bins1 = [0, 2, 3, 4, 3, 2, 0, 0, 0, 0]
        labels1 = [i*0.2 for i in range(len(bins1))]
        bins2 = [0, 2, 3, 4, 3, 2, 0, 0, 0, 0, 0, 0, 0]
        labels2 = [1.0 + i * 0.2 for i in range(len(bins2))]
        dist_list = [(bins1, labels1), (bins2, labels2)]
        merged = [0, 2, 3, 4, 3, 2, 2, 3, 4, 3, 2, 0, 0, 0, 0, 0, 0, 0]
        for nbins in range(1, 100):
            shaper = dist_shaper(dist_list, nbins=nbins)
            for dist in dist_list:
                bins, labels = shaper(dist)
                self.assertEqual(len(bins), len(labels))
                self.assertEqual(len(bins), nbins)
                self.assertEqual(sum(bins), sum(dist[0]))
                """
                if nbins > len(merged):
                    self.assertEqual(bins, merged)
                    self.assertEqual(labels,
                                     [i*5 for i in range(len(merged))])
                """
