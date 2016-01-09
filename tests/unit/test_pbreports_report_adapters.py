import os
import logging
import traceback
import json

from pbcore.util.Process import backticks

from pbreports.model.model import Attribute
from pbreports.util import bas_fofn_to_bas_files
from pbreports.report.adapter import (make_adapter_report,
                                      _get_median_adapter_spacing,
                                      get_hq_adapters, _get_dimer_att,
                                      _get_short_inserts_att,
                                      _get_medium_inserts_att,
                                      _get_report_att, _get_zmw_records,
                                      _create_histograms, _create_histogram_figure)

from base_test_case import BaseTestCase, skip_if_data_dir_not_present

log = logging.getLogger(__name__)


class DataCache(object):

    """
    Since the core logic of makeAdapterReport is composed of functions,
    not classes, and there is no
    state, writing efficient unit tests is tricky.

    Here, store data extracted from the bas.h5 for re-use in different tests
    """
    _data_cache = {}
    data_dir = None

    @staticmethod
    def get_cached_data(fofn, data_key):
        """
        Avoid repeating the bas.h5 io for each test.
        """
        if fofn not in DataCache._data_cache:
            DataCache._data_cache[fofn] = {}

        if data_key not in DataCache._data_cache[fofn]:
            log.debug('Stuffing data in the cache: [{f}][{k}]'.format(f=fofn,
                                                                      k=data_key))

            # keep it simple. If there's no key, stuff everything back in cache
            DataCache.write_fofn(fofn)
            log.info('Wrote: {f}'.format(f=fofn))
            bas_files = bas_fofn_to_bas_files(fofn)
            zmw_i = get_hq_adapters(bas_files)
            trimmed_histogram, untrimmed_histogram = _create_histograms(bas_files)

            DataCache._data_cache[fofn]['zmw_info'] = zmw_i
            DataCache._data_cache[fofn]['mas'] = _get_median_adapter_spacing(
                zmw_i[0])

            DataCache._data_cache[fofn]['bas_files'] = bas_files
            DataCache._data_cache[fofn]['trimmed_histogram'] = trimmed_histogram
            DataCache._data_cache[fofn]['untrimmed_histogram'] = untrimmed_histogram
        else:
            log.debug(
                'Data already exists in the cache: [{f}][{k}]'.format(f=fofn,
                                                                      k=data_key))

        return DataCache._data_cache[fofn][data_key]

    @staticmethod
    def write_fofn(fofn):
        """
        Create a fofn on-the-fly in the output dir
        """
        h5 = os.path.join(DataCache.data_dir, 'adapter',
                          'm110303_231128_ethan_c100078170034500000315004805201190_s1_p0.bas.h5')
        if not os.path.exists(h5):
            raise IOError("Cannot find test data file %s" % h5)
        o = open(fofn, 'w')
        o.write(h5)
        o.close()


@skip_if_data_dir_not_present
class TestAdapterRpt(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()
        DataCache.data_dir = BaseTestCase.get_data_dir()

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

    def test_streaming_records(self):
        """Test that the records are correctly streamed from the bas.h5 file."""
        fofn = os.path.join(self.get_output_dir(), 'test.fofn')
        bas_files = DataCache.get_cached_data(fofn, 'bas_files')
        self.assertEqual(47332, len(list(
            _get_zmw_records(bas_files, "sequencingZmws"))))
        self.assertEqual(75153, len(list(
            _get_zmw_records(bas_files, "allSequencingZmws"))))

    def test_create_histograms(self):
        """Test that the histograms have the correct number of values."""
        fofn = os.path.join(self.get_output_dir(), 'test.fofn')
        untrimmed_histogram = DataCache._data_cache[fofn]['untrimmed_histogram']
        trimmed_histogram = DataCache._data_cache[fofn]['trimmed_histogram']
        self.assertEqual(47332, trimmed_histogram.total)
        self.assertEqual(75153, untrimmed_histogram.total)

    def test_create_histogram_figure(self):
        """Test that the histogram figure is created properly, and outputs for 
           examination."""
        fofn = os.path.join(self.get_output_dir(), 'test.fofn')
        untrimmed_histogram = DataCache._data_cache[fofn]['untrimmed_histogram']

        fig = _create_histogram_figure(untrimmed_histogram)
        fig.savefig(os.path.join(self.get_output_dir(), "histogram_unittest.png"))

    def test_divide_by_zero(self):
        z = 'FAKE_ZMW'  # Zmw('/foo',1)
        mas = {z: [1, 2]}
        seq_zmws = 0
        id_ = 'foobar'
        name = 'whatev'
        a = _get_report_att(mas, seq_zmws, (0, 10), id_, name)
        self.assertEqual("NA", a.value)
        self.assertEqual(id_, a.id)
        self.assertEqual(name, a.name)

    def test_get_zmw_info(self):
        """Test the adapter intervals and total # ZMW's """
        fofn = os.path.join(self.get_output_dir(), 'test.fofn')
        t = DataCache.get_cached_data(fofn, 'zmw_info')
        self.assertEqual(47332, len(t[0]))
        self.assertEqual(47332, t[1])

    def test_adapter_dimers_att(self):
        """Test that the "dimers" attribute gets created proppa."""

        fofn = os.path.join(self.get_output_dir(), 'test.fofn')
        zmw_info = DataCache.get_cached_data(fofn, 'zmw_info')
        trimmed_histogram = DataCache._data_cache[fofn]['trimmed_histogram']

        att = _get_dimer_att(trimmed_histogram, zmw_info[1], id_prefix="")

        self.assertEqual("Adapter Dimers", att.name)
        self.assertEqual("adapter_dimers", att.id)
        self.assertEqual(0.0002746556241020874, att.value)

    def test_short_inserts_att(self):
        """Test that the "short" inserts attribute gets created proppa"."""

        fofn = os.path.join(self.get_output_dir(), 'test.fofn')
        zmw_info = DataCache.get_cached_data(fofn, 'zmw_info')
        trimmed_histogram = DataCache._data_cache[fofn]['trimmed_histogram']

        att = _get_short_inserts_att(trimmed_histogram, zmw_info[1], id_prefix="")

        self.assertEqual("Short Inserts", att.name)
        self.assertEqual("short_inserts", att.id)
        self.assertEqual(0.0037395419589284205, att.value)

    def test_medium_inserts_att(self):
        """Test that the "medium" inserts attribute gets created proppa" ."""

        fofn = os.path.join(self.get_output_dir(), 'test.fofn')
        zmw_info = DataCache.get_cached_data(fofn, 'zmw_info')
        trimmed_histogram = DataCache._data_cache[fofn]['trimmed_histogram']

        att = _get_medium_inserts_att(trimmed_histogram, zmw_info[1], id_prefix="")

        self.assertEqual("Medium Inserts", att.name)
        self.assertEqual("medium_inserts", att.id)
        self.assertEqual(0.5940167328657145, att.value)

    def test_get_median_adapter_spacing(self):
        """
        Test the function that returns median Adapter Spacing (mas) array
        from pls fofn.
        """
        fofn = os.path.join(self.get_output_dir(), 'test.fofn')
        mas = DataCache.get_cached_data(fofn, 'mas')
        self.assertEqual(47332, len(mas))

    def test_make_adapter_report_no_fofn(self):
        """Test that an IOError is thrown if no fofn exists."""
        log.info(TestAdapterRpt.test_make_adapter_report_no_fofn.__doc__)

        def _test_ioerror():
            make_adapter_report('foo', 'bar', self.get_output_dir(), 60, False)

        self.assertRaises(IOError, _test_ioerror)

    def test_make_adapter_report(self):
        """
        1) Test that the final report gets written.
        2) Test that the "short insert" attribute is within range of the makeAdapterReport.py's value.
        Both numerator and denominator have changed.
        For numerator, regions are now clipped to HQ regions meaning we get fewer adapters:
            (From David A)
            In [2]: b=BasH5Reader("/mnt/secondary/Share/jmiller/adapter-debug/m110303_231128_ethan_c100078170034500000315004805201190_s1_p0.bas.h5")
            In [6]: zmw50=b[50]
            In [7]: zmw50.regionTable
            Out[7]:
            rec.array([(50, 2, 0, 0, 0), (50, 1, 0, 1534, -1), (50, 1, 1583, 1667, -1),
                   (50, 1, 1724, 1960, -1), (50, 0, 1534, 1583, 632),
                   (50, 0, 1667, 1724, 701)],
                  dtype=[('holeNumber', '<i4'), ('regionType', '<i4'), ('regionStart', '<i4'), ('regionEnd', '<i4'), ('regionScore', '<i4')])
            In [8]: zmw50.hqRegion
            Out[8]: (0, 0)
            There's no HQ region for the ZMW.   The BasH5Reader clips everything to the HQ region---so in this case that means it is going to tell you there are no insert regions in there, even though there actually are some reported in the region table.   So that's your explanation.

        For denominator, getting fewer sequencingZmw's ( sequencingZmws vs allSequencingZmws )
        """
        fofn = os.path.join(self.get_output_dir(), 'test.fofn')
        DataCache.write_fofn(fofn)
        make_adapter_report(fofn, 'rpt.json', self.get_output_dir(), 60,
                            False)

        rpt = os.path.join(self.get_output_dir(), 'rpt.json')
        self.assertTrue(os.path.exists(rpt))

        with open(rpt, 'r') as f:
            d = json.loads(f.read())

        delta = .0043 - .0037
        for a in d['attributes']:
            if a['id'] == 'adapter.short_inserts':
                self.assertAlmostEqual(.0043, a['value'], delta=delta)
                
                
    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """
        #This test is a special case, b/c it's a subprocess call
        BaseTestCase.setUpClass()
        DataCache.data_dir = BaseTestCase.get_data_dir()
        
        fofn = os.path.join(self.get_output_dir(), 'test.fofn')
        DataCache.write_fofn(fofn)
        cmd = 'pbreport adapter {o} {r} {f}'.format(o=self.get_output_dir(),
                                                           r='rpt.json',
                                                           f=fofn)
        o, c, m = backticks(cmd)
        log.info(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            print(m)
        self.assertEquals(0, c)
        self.assertTrue(os.path.exists(os.path.join(self.get_output_dir(), 'rpt.json')))
                

