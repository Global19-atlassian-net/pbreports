import os
import logging
import traceback
import json
import tempfile
import unittest
import shutil

from pbcore.util.Process import backticks

from base_test_case import _get_root_data_dir
from pbreports.serializers import dict_to_report
from pbreports.io.filtered_summary_reader import FilteredSummaryReader

from pbreports.model.model import PbReportError
from pbreports.report.control import (make_control_report, _get_control_reads,
                                      _get_filtered_reads, _process_reads,
                                      CSV_COLUMN_MAP, _get_attr_n_control_reads,
                                      _get_error_report, _get_attr_fraction_control_reads,
                                      _get_attr_control_subread_acc,
                                      _get_attr_control_mean_readlength,
                                      _get_attr_control_95_readlength, _get_attr_n50,
                                      _create_score_figure,_create_length_figure)


log = logging.getLogger(__name__)

CONTROL_READS = 'control'
FILTERED_READS = 'filtered'


class TestControlRpt(unittest.TestCase):

    DATA_DIR = None

    @classmethod
    def setUpClass(cls):
        """
        Load data once.
        """
        try:
            if cls.DATA_DIR is not None:
                log.info('data has already been loaded')
                return

            cls.DATA_DIR = os.path.join(_get_root_data_dir(), 'control')

            cmph5 = os.path.join(cls.DATA_DIR, 'control_reads.cmp.h5')
            csv = os.path.join(cls.DATA_DIR, 'filtered_summary.csv')

            log.info('Loading data 1 time from {c} and {f}'.format(c=cmph5, f=csv))

            cls._data = {}
            cls._data[CONTROL_READS] = _get_control_reads(cmph5)
            cls._data[FILTERED_READS] = _get_filtered_reads(csv)
        except:
            tb = traceback.format_exc()
            log.error(tb)
            print(tb)
            raise

    def setUp(self):
        """
        Before *every* test
        """
        self._output_dir = tempfile.mkdtemp(suffix="control")

    def tearDown(self):
        """
        After *every* test
        """
        if os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_make_coverage_report_none_cmp_h5(self):
        """
        cmp.h5 cannot be null
        """
        csv = os.path.join(self.DATA_DIR, 'filtered_summary.csv')
        with self.assertRaises(PbReportError):
            make_control_report(None, csv, 'foo.json', self._output_dir, '1', False)

    def test_make_coverage_report_no_cmp_h5(self):
        """
        cmp.h5 must exist
        """
        csv = os.path.join(self.DATA_DIR, 'filtered_summary.csv')
        with self.assertRaises(IOError):
            make_control_report('foo', csv, 'foo.json', self._output_dir, '1', False)

    def test_make_coverage_report_none_csv(self):
        """
        csv cannot be null
        """
        cmph5 = os.path.join(self.DATA_DIR, 'control_reads.cmp.h5')
        with self.assertRaises(PbReportError):
            make_control_report(cmph5, None, 'foo.json', self._output_dir, '1', False)

    def test_make_coverage_report_no_csv(self):
        """
        csv must exist
        """
        cmph5 = os.path.join(self.DATA_DIR, 'control_reads.cmp.h5')
        with self.assertRaises(IOError):
            make_control_report(cmph5, 'foo', 'foo.json', self._output_dir, '1', False)

    def test_get_control_reads(self):
        """
        Test that a correct control name is returned. Also, test the control reads dict.
        """
        name, control_reads = self._data[CONTROL_READS]
        self.assertEqual('4kb_Control_c2', name)
        self.assertEqual(333, len(control_reads))

        # sanity test - every control read should be in filtered_summary
        not_in = []
        ids = self._get_all_filtered_read_ids()
        for cid in control_reads.keys():
            if cid not in ids:
                not_in.append(cid)
#                self.fail('control read {c} is not in filtered_summary.csv'.format(c=cid))

        if len(not_in) > 0:
            self.fail('{l} control reads not in filtered_summary.csv'.format(l=len(not_in)))
            log.info('\n'.join(not_in))

    def _get_all_filtered_read_ids(self):
        reader = FilteredSummaryReader(os.path.join(self.DATA_DIR, 'filtered_summary.csv'), CSV_COLUMN_MAP)
        reader.load()
        data = reader.data_as_numpy_array()
        ids = set([])
        for row in data:
            ids.add(row['ReadId'])
        return ids

    def test_get_filtered_data(self):
        """
        Test that only reads that passed filter are returned
        """
        data = self._data[FILTERED_READS]
        for r in data:
            if r['PassedFilter'] == 0:
                self.fail('Found reads that did not pass filter')
        self.assertEqual(26947, len(data))

    def test_process_reads(self):
        """
        Assert length of sample and control arrays
        """
        c_reads = self._data[CONTROL_READS][1]
        f_reads = self._data[FILTERED_READS]
        control_data, sample_data = _process_reads(c_reads, f_reads)

        self.assertTrue(len(control_data[0]) == len(control_data[1]) == len(control_data[2]) == len(control_data[3]))
        self.assertEqual(333, len(control_data[0]))
        self.assertEqual(26614, len(sample_data[0]))

    def test_get_error_report(self):
        """
        Test the special error report you get when
        there are 0 control reads
        """
        rpt = _get_error_report()
        self.assertEqual(1, len(rpt.attributes))
        self.assertEqual('warning', rpt.attributes[0].id)
        self.assertEqual('Warning', rpt.attributes[0].name)
        self.assertEqual('No control reads found', rpt.attributes[0].value)

    def test_attrs(self):
        """
        Create all report attributes, test values
        """
        c_reads = self._data[CONTROL_READS][1]
        f_reads = self._data[FILTERED_READS]
        control_data, sample_data = _process_reads(c_reads, f_reads)

        n_control = control_data.shape[1]
        n_sample = sample_data.shape[1]

        self.assertEqual(333, _get_attr_n_control_reads(n_control).value)

        self.assertEqual(0.01235759082643708,
                         _get_attr_fraction_control_reads(n_control,
                                                          n_sample).value)
        self.assertEqual(0.84888366464380027,
                         _get_attr_control_subread_acc(control_data).value)

        self.assertEqual(2468,
                         _get_attr_control_mean_readlength(control_data).value)

        self.assertEqual(7804,
                         _get_attr_control_95_readlength(control_data).value)
        self.assertEqual(3912, _get_attr_n50(control_data).value)


    def test_create_score_figure(self):
        """
        Test that the score figure obj is not None
        """
        c_reads = self._data[CONTROL_READS][1]
        f_reads = self._data[FILTERED_READS]
        control_data, sample_data = _process_reads(c_reads, f_reads)

        fig = _create_score_figure(control_data, sample_data)
        self.assertIsNotNone(fig)

    def test_create_length_figure(self):
        """
        Test that the length figure obj is not None
        """
        c_reads = self._data[CONTROL_READS][1]
        f_reads = self._data[FILTERED_READS]
        control_data, sample_data = _process_reads(c_reads, f_reads)

        fig = _create_length_figure(control_data, sample_data)
        self.assertIsNotNone(fig)

    def test_make_control_report(self):
        """
        Test that the report gets written proppa
        """
        cmph5 = os.path.join(self.DATA_DIR, 'control_reads.cmp.h5')
        csv = os.path.join(self.DATA_DIR, 'filtered_summary.csv')
        make_control_report(cmph5, csv, 'foo.json', self._output_dir, 60, False)

        # deserialize report
        s = None
        with open(os.path.join(self._output_dir, 'foo.json'), 'r') as f:
            s = json.load(f)

        report = dict_to_report(s)
        self.assertEqual(7, len(report.attributes))

        for i in range(2):
            pg = report.plotGroups[i]
            self.assertFalse(os.path.isabs(pg.thumbnail))
            self.assertTrue(os.path.exists(os.path.join(self._output_dir, pg.thumbnail)))
            p = pg.plots[0]
            self.assertFalse(os.path.isabs(p.image))
            self.assertTrue(os.path.exists(os.path.join(self._output_dir, p.image)))

    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """

        cmph5 = os.path.join(self.DATA_DIR, 'control_reads.cmp.h5')
        csv = os.path.join(self.DATA_DIR, 'filtered_summary.csv')
        cmd = 'pbreport control {o} {r} {c} {g}'.format(o=self._output_dir,
                                                           r='rpt.json',
                                                           c=cmph5, g=csv)

        o, c, m = backticks(cmd)
        log.info(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            print(m)
        self.assertEquals(0, c)
        self.assertTrue(os.path.exists(os.path.join(self._output_dir, 'rpt.json')))
