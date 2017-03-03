
# FIXME use dataset subreads-sequel in PacBioTestData

import os
import logging
import traceback
import json
import unittest
import tempfile
import shutil
import numpy as np

from pprint import pformat
from numpy import ndarray

from pbcore.io.dataset.DataSetIO import InvalidDataSetIOError
from pbcore.util.Process import backticks
import pbcore.data.datasets as data
from pbcore.io import SubreadSet

import pbtestdata

from pbreports.util import dist_shaper, continuous_dist_shaper
from pbreports.io.filtered_summary_reader import FilteredSummaryReader
from pbreports.report.loading_xml import to_report as make_loading_report
from pbreports.report.filter_stats_xml import to_report as make_filter_report
from pbreports.report.filter_stats_xml import Constants
from pbreports.report.adapter_xml import to_report as make_adapter_report

from base_test_case import validate_report_complete

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

def get_merged_subreadset():
    sfn = ('/pbi/dept/secondary/siv/testdata/pbreports-unittest/data/'
           'loading/merged.dataset.xml')
    return sfn

def get_fixed_bin_dataset():
    sfn = get_fixed_bin_sts()
    sset = SubreadSet()
    sset.loadStats(sfn)
    return sset


class XMLStatsRptsBase(unittest.TestCase):

    def setUp(self):
        """
        Before *every* test
        """
        super(XMLStatsRptsBase, self).setUp()
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
        super(XMLStatsRptsBase, self).tearDown()

    def _compare_attribute_values(self, report_d, expected_d):
        attr = report_d['attributes']
        attr_d = {a_['id'].split(".")[-1]: a_['value'] for a_ in attr}
        for id_, val in expected_d.iteritems():
            self.assertEqual(attr_d[id_], val)


class TestRawDataRpt(XMLStatsRptsBase):

    def test_filter_exit_code_0(self):
        tmpdir = tempfile.mkdtemp()
        cwd = os.getcwd()
        sts_xml = pbtestdata.get_file("subreads-sequel")
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

    def test_make_filter_stats_report_sts_xml(self):
        """
        Test the content of the filter report generated from an sts.xml
        """
        sts_xml = pbtestdata.get_file("stats-xml")
        rpt = make_filter_report(sts_xml, self.get_output_dir())
        d = json.loads(rpt.to_json())
        self._compare_attribute_values(
            report_d=d,
            expected_d={
                Constants.A_NBASES:  1672335649,
                Constants.A_NREADS: 394658,
                Constants.A_READ_N50: 7750,
                Constants.A_READ_LENGTH: 4237
            })
        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'readLenDist0.png')))
        # self.assertTrue(os.path.exists(os.path.join(
        #    self.get_output_dir(),
        #    'readQualDist0.png')))

        # these are from a raw STS file
        self.assertEqual(len(rpt._dataset_uuids), 0,
                         "Incorrect report datasets uuids")
        print pformat(rpt.to_dict())
        validate_report_complete(self, rpt)

    def test_make_filter_stats_report_dataset(self):
        """
        Test the content of the filter report generated from a dataset
        """
        sts_xml = pbtestdata.get_file("subreads-sequel")
        rpt = make_filter_report(sts_xml, self.get_output_dir())
        d = json.loads(rpt.to_json())
        self._compare_attribute_values(
            report_d=d,
            expected_d={
                Constants.A_NBASES:  1672335649,
                Constants.A_NREADS: 394658,
                Constants.A_READ_N50: 7750,
                Constants.A_READ_LENGTH: 4237,
                Constants.A_INSERT_LENGTH: 4450,
                Constants.A_INSERT_N50: 7750
            })

        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'readLenDist0.png')))

    # FIXME would be good to remove that input from pbcore
    def test_make_filter_stats_report_dataset_multiple_chips(self):
        sts_xml = data.getXmlWithStats()
        rpt = make_filter_report(sts_xml, self.get_output_dir())
        d = json.loads(rpt.to_json())
        self._compare_attribute_values(
            report_d=d,
            expected_d={
                Constants.A_NBASES:  342348413,
                Constants.A_NREADS: 25123,
                Constants.A_READ_N50: 21884,
                Constants.A_READ_LENGTH: 13627
            })
        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'readLenDist0.png')))
        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'readLenDist1.png')))


class TestLoadingRpt(XMLStatsRptsBase):

    def test_loading_exit_code_0(self):
        tmpdir = tempfile.mkdtemp()
        cwd = os.getcwd()
        sts_xml = pbtestdata.get_file("subreads-sequel")
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

    def test_make_loading_report_no_csv(self):
        """
        Test that an IOError is thrown if the specified path does not exist
        """
        def _test_ioerror():
            make_loading_report('foo', self.get_output_dir())
        self.assertRaises((InvalidDataSetIOError, IOError), _test_ioerror)

    def test_make_loading_report_with_dataset(self):
        """
        Test the content of the loading report generated from a simple
        SubreadSet
        """
        sts_xml = pbtestdata.get_file("subreads-sequel")

        rpt = make_loading_report(sts_xml, self.get_output_dir())
        d = json.loads(rpt.to_json())

        t = d['tables'][0]
        c0 = t['columns'][0]
        c1 = t['columns'][1]
        c2 = t['columns'][2]
        c3 = t['columns'][3]
        c4 = t['columns'][4]
        c5 = t['columns'][5]
        c6 = t['columns'][6]
        c7 = t['columns'][7]
        c8 = t['columns'][8]

        self.assertEqual('Collection Context', c0['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'collection_context', c0['id'])
        self.assertEqual('m54006_160504_020705', c0['values'][0])

        self.assertEqual('Productive ZMWs', c1['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productive_zmws', c1['id'])
        self.assertEqual(1035426, c1['values'][0])

        self.assertEqual('Productivity 0',
                         c2['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_0_n',
                         c2['id'])
        self.assertEqual(631530, c2['values'][0])

        self.assertEqual('(%)',
                         c3['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_0_pct',
                         c3['id'])
        self.assertAlmostEqual(60.992, c3['values'][0], delta=.0003)

        self.assertEqual('Productivity 1',
                         c4['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_1_n',
                         c4['id'])
        self.assertEqual(394658, c4['values'][0])

        self.assertEqual('(%)',
                         c5['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_1_pct',
                         c5['id'])
        self.assertAlmostEqual(38.116, c5['values'][0], delta=.0003)

        self.assertEqual('Productivity 2',
                         c6['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_2_n',
                         c6['id'])
        self.assertEqual(9238, c6['values'][0])

        self.assertEqual('(%)',
                         c7['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_2_pct',
                         c7['id'])
        self.assertAlmostEqual(0.892, c7['values'][0], delta=.0003)
        self.assertEqual(c8['values'][0], "Workflow_Magbead.py")

    @unittest.skipIf(not _internal_data(),
                     "Internal data not available")
    def test_make_loading_report_with_merged_dataset(self):
        """
        Test the content of the loading report generated from a dataset with
        multiple sub-datasets
        """
        ss = get_merged_subreadset()

        rpt = make_loading_report(ss, self.get_output_dir())
        d = json.loads(rpt.to_json())

        t = d['tables'][0]
        c0 = t['columns'][0]
        c1 = t['columns'][1]
        c2 = t['columns'][2]
        c3 = t['columns'][3]
        c4 = t['columns'][4]
        c5 = t['columns'][5]
        c6 = t['columns'][6]
        c7 = t['columns'][7]

        self.assertEqual('Collection Context', c0['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'collection_context', c0['id'])
        self.assertEqual('Combined', c0['values'][0])
        # Turn these back on when a context is inserted in the testdataset:
        #self.assertEqual('dummy1', c0['values'][1])
        #self.assertEqual('dummy2', c0['values'][2])
        self.assertEqual('m54086_160831_230338', c0['values'][1])
        self.assertEqual('m54099_160830_232701', c0['values'][2])

        self.assertEqual('Productive ZMWs', c1['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productive_zmws', c1['id'])
        self.assertEqual(2073466, c1['values'][0])
        self.assertEqual(1036722, c1['values'][1])
        self.assertEqual(1036744, c1['values'][2])

        self.assertEqual('Productivity 0',
                         c2['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_0_n',
                         c2['id'])
        self.assertEqual(1325603, c2['values'][0])
        self.assertEqual(853636, c2['values'][1])
        self.assertEqual(471967, c2['values'][2])

        self.assertEqual('(%)',
                         c3['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_0_pct',
                         c3['id'])
        self.assertAlmostEqual(63.932, c3['values'][0], delta=.0003)
        self.assertAlmostEqual(82.340, c3['values'][1], delta=.0003)
        self.assertAlmostEqual(45.524, c3['values'][2], delta=.0003)

        self.assertEqual('Productivity 1',
                         c4['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_1_n',
                         c4['id'])
        self.assertEqual(743972, c4['values'][0])
        self.assertEqual(180176, c4['values'][1])
        self.assertEqual(563796, c4['values'][2])

        self.assertEqual('(%)',
                         c5['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_1_pct',
                         c5['id'])
        self.assertAlmostEqual(35.881, c5['values'][0], delta=.0003)
        self.assertAlmostEqual(17.379, c5['values'][1], delta=.0003)
        self.assertAlmostEqual(54.381, c5['values'][2], delta=.0003)

        self.assertEqual('Productivity 2',
                         c6['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_2_n',
                         c6['id'])
        self.assertEqual(3891, c6['values'][0])
        self.assertEqual(2910, c6['values'][1])
        self.assertEqual(981, c6['values'][2])

        self.assertEqual('(%)',
                         c7['header'])
        self.assertEqual('loading_xml_report.loading_xml_table.'
                         'productivity_2_pct',
                         c7['id'])
        self.assertAlmostEqual(0.188, c7['values'][0], delta=.0003)
        self.assertAlmostEqual(0.281, c7['values'][1], delta=.0003)
        self.assertAlmostEqual(0.095, c7['values'][2], delta=.0003)
        validate_report_complete(self, rpt)


class TestAdapterReport(XMLStatsRptsBase):

    def test_adapter_exit_code_0(self):
        subreads_xml = pbtestdata.get_file("subreads-sequel")
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

    def test_make_adapter_report_dataset(self):
        """
        Test make_adapter_report with a dataset
        """
        # All of the histogram generation code should be tested in
        # pbcore.io.dataset, not here. Just test the report.
        sts_xml = data.getXmlWithStats()
        rpt = make_adapter_report(sts_xml, self.get_output_dir())
        d = json.loads(rpt.to_json())
        a = d['attributes']
        self.assertEqual(a[0]['name'], 'Adapter Dimers (0-10bp) %')
        self.assertEqual(a[0]['value'], 0.0)
        self.assertEqual(a[1]['value'], 0.0)
        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'interAdapterDist0.png')))
        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'interAdapterDist1.png')))
        validate_report_complete(self, rpt)

    def test_make_adapter_report_dataset2(self):
        """
        Test make_adapter_report with a more recent dataset
        """
        # All of the histogram generation code should be tested in
        # pbcore.io.dataset, not here. Just test the report.
        xml = pbtestdata.get_file("subreads-sequel")
        rpt = make_adapter_report(xml, self.get_output_dir())
        d = json.loads(rpt.to_json())
        a = d['attributes']
        self.assertEqual(a[0]['name'], 'Adapter Dimers (0-10bp) %')
        self.assertEqual(a[0]['value'], 0.09)
        self.assertEqual(a[1]['value'], 0.52)
        self.assertEqual("{:.2f}".format(a[2]['value']), "0.00")
        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'interAdapterDist0.png')))
        validate_report_complete(self, rpt)

    def test_make_adapter_report_merged_dataset(self):
        xml = get_merged_subreadset()
        rpt = make_adapter_report(xml, self.get_output_dir())
        d = json.loads(rpt.to_json())
        a = d['attributes']
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0]['name'], 'Adapter Dimers (0-10bp) %')
        self.assertEqual(a[0]['value'], 0.06)
        self.assertEqual(a[1]['value'], 0.64)
        self.assertTrue(os.path.exists(os.path.join(
            self.get_output_dir(),
            'interAdapterDist0.png')))


class TestBinning(unittest.TestCase):

    @unittest.skipIf(not _internal_data(),
                     "Internal data not available")
    def test_reports_with_fixed_bins(self):
        # TODO readQualDists are currently unpopulated, turn back on when
        # they're repopulated
        # for dist_name, nbins in zip(['medianInsertDists', 'readLenDists',
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
        labels1 = [i * 5 for i in range(len(bins1))]
        bins2 = [0, 2, 3, 4, 3, 2, 0, 0, 0, 0, 0, 0, 0]
        labels2 = [25 + i * 5 for i in range(len(bins2))]
        dist_list = [(bins1, labels1), (bins2, labels2)]
        merged = [0, 2, 3, 4, 3, 2, 2, 3, 4, 3, 2, 0, 0, 0, 0, 0, 0, 0]
        for nbins in range(1, 100):
            shaper = dist_shaper(dist_list, nbins=nbins)
            for dist in dist_list:
                # print 'pre'
                # print dist[0]
                bins, labels = shaper(dist)
                # print 'post'
                # print bins
                # print labels
                self.assertEqual(len(bins), len(labels))
                self.assertEqual(len(bins), nbins)
                self.assertEqual(sum(bins), sum(dist[0]))
                # print ""
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
        labels1 = [i * 0.2 for i in range(len(bins1))]
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

    def test_dist_shaper_leading_and_trailing(self):

        # basic setup:
        bins = [0, 0, 0, 0, 1, 2, 3, 4, 0, 0, 0, 0]
        labels = [i * 5 for i in range(len(bins))]
        self.assertEqual(len(bins), len(labels))
        self.assertEqual(labels[-1], 55)

        # no-op re-binning
        shaper = dist_shaper([(bins, labels)], nbins=len(bins))
        ob, ol = shaper((bins, labels))
        self.assertEqual(bins, ob)
        self.assertEqual(labels, ol)

        # nbins = npopulated_columns - 1
        eb = [3, 7, 0]
        el = [20, 30, 40]
        nbins = np.count_nonzero(bins) - 1
        shaper = dist_shaper([(bins, labels)], nbins=nbins)
        ob, ol = shaper((bins, labels))
        self.assertEqual(eb, ob)
        self.assertEqual(el, ol)

        # nbins = npopulated_columns - 1, excess trimmed
        eb = [3, 7]
        el = [20, 30]
        nbins = np.count_nonzero(bins) - 1
        shaper = dist_shaper([(bins, labels)], nbins=nbins, trim_excess=True)
        ob, ol = shaper((bins, labels))
        self.assertEqual(eb, ob)
        self.assertEqual(el, ol)

        # nbins = npopulated_columns
        eb = [1, 2, 3, 4]
        el = [i * 5 for i in range(4, 4 + len(eb))]
        nbins = np.count_nonzero(bins)
        shaper = dist_shaper([(bins, labels)], nbins=nbins)
        ob, ol = shaper((bins, labels))
        self.assertEqual(eb, ob)
        self.assertEqual(el, ol)

        # nbins = npopulated_columns + 1
        eb = [1, 2, 3, 4, 0]
        el = [i * 5 for i in range(4, 4 + len(eb))]
        nbins = np.count_nonzero(bins) + 1
        shaper = dist_shaper([(bins, labels)], nbins=nbins)
        ob, ol = shaper((bins, labels))
        self.assertEqual(eb, ob)
        self.assertEqual(el, ol)

        # nbins = npopulated_columns + 1, excess trimmed
        eb = [1, 2, 3, 4]
        el = [i * 5 for i in range(4, 4 + len(eb))]
        nbins = np.count_nonzero(bins) + 1
        shaper = dist_shaper([(bins, labels)], nbins=nbins, trim_excess=True)
        ob, ol = shaper((bins, labels))
        self.assertEqual(eb, ob)
        self.assertEqual(el, ol)

        # larger setup:
        bins = [0, 0, 0, 0, 1, 2, 3, 4, 5, 0, 0, 0]
        labels = [i * 5 for i in range(len(bins))]
        self.assertEqual(len(bins), len(labels))
        self.assertEqual(labels[-1], 55)

        # nbins = npopulated_columns - 1
        eb = [3, 7, 5, 0]
        el = [20, 30, 40, 50]
        nbins = np.count_nonzero(bins) - 1
        shaper = dist_shaper([(bins, labels)], nbins=nbins)
        ob, ol = shaper((bins, labels))
        self.assertEqual(eb, ob)
        self.assertEqual(el, ol)

        # nbins = npopulated_columns - 1, excess trimmed
        eb = [3, 7, 5]
        el = [20, 30, 40]
        nbins = np.count_nonzero(bins) - 1
        shaper = dist_shaper([(bins, labels)], nbins=nbins, trim_excess=True)
        ob, ol = shaper((bins, labels))
        self.assertEqual(eb, ob)
        self.assertEqual(el, ol)
