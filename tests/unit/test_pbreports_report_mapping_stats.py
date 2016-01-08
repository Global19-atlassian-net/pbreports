import json
import os
import pprint
import unittest
import logging
import tempfile
import sys
from pbreports.model.model import Report
from pbreports.serializers import dict_to_report

from base_test_case import ROOT_DATA_DIR, run_backticks
from pbreports.report.mapping_stats import to_report, Constants

log = logging.getLogger(__name__)

_EXE = "mapping_stats"

_IO_DATA_DIR = os.path.join(ROOT_DATA_DIR, 'io')
_GMAP_DATA_DIR = os.path.join(
    ROOT_DATA_DIR, 'mapping_stats', 'gmap_2850031_0011')
_LAMBDA_DATA_DIR = os.path.join(
    ROOT_DATA_DIR, 'mapping_stats', "lambda_2372215_0007_tiny")
_CCS_DATA_DIR = os.path.join(ROOT_DATA_DIR, 'mapping_stats', 'ccs')

_TOTAL_NUMBER_OF_ATTRIBUTES = 13
_TOTAL_NUMBER_OF_PLOT_GROUPS = 3
# Tolerance for validating Readlength Q95. This computed from the histogram
_Q95_DELTA = 50


def _almost_value(actual_value, value, delta):
    """Check if a value is +/- delta amount"""
    max_value = value + delta
    min_value = value - delta
    state = min_value <= actual_value <= max_value

    # Failed assertions have not great error messages. Adding message here.
    if not state:
        _d = dict(a=actual_value, v=value, d=delta)
        msg = "Actual value {a} not within {v} +/- {d}".format(**_d)
        log.error(msg)
        sys.stderr.write(msg + "\n")

    return state


def _to_cmd(aligned_bam, report_json):
    cmd = "{e} --debug {a} {j}"
    output_dir = os.path.dirname(report_json)
    d = dict(e=_EXE, o=output_dir, a=aligned_bam, j=report_json)

    s = cmd.format(**d)
    log.info(s)
    return s


class TestIntegrationMappingStatsReport(unittest.TestCase):

    def setUp(self):
        _to_p = lambda x: os.path.join(_IO_DATA_DIR, x)
        self.output_dir = tempfile.mkdtemp(suffix="_mapping_stats")
        self.input_xml = _to_p('lambda_aligned.xml')
        self.aligned_reads_bam = _to_p('lambda_aligned.bam')
        t = tempfile.NamedTemporaryFile(
            delete=False, suffix="mapping_report.json")
        t.close()
        self.report_json = t.name

    def test_basic(self):
        cmd = _to_cmd(self.aligned_reads_bam, self.report_json)

        rcode = run_backticks(cmd)
        self.assertEqual(rcode, 0)

        with open(self.report_json, 'r') as f:
            s = json.load(f)
            log.info("JsonReport: ")
            log.info(pprint.pformat(s, indent=4))

        report = dict_to_report(s)
        self.assertIsNotNone(report)
        self.assertEqual(len(report.tables), 1)

        log.info(str(report.tables[0]))


class TestMappingStatsReport(unittest.TestCase):
    ALIGNMENTS = os.path.join(_LAMBDA_DATA_DIR, "lambda_2zmws_mapped.bam")
    EXPECTED_VALUES = {
        Constants.A_READLENGTH: 9717,
        Constants.A_SUBREAD_LENGTH: 809,
    }

    @classmethod
    def setUpClass(cls):
        _to_p = lambda x: os.path.join(_LAMBDA_DATA_DIR, x)
        cls.output_dir = tempfile.mkdtemp(suffix="_mapping_stats")
        t = tempfile.NamedTemporaryFile(
            delete=False, suffix="mapping_report.json")
        t.close()
        cls.report_json = t.name
        cls.report = to_report(cls.ALIGNMENTS, cls.output_dir)

    def _get_attribute_value_by_id(self, i):
        """helper method to grab value from the report instance"""
        a = self.report.get_attribute_by_id(i)
        if a is None:
            raise KeyError(
                "Unable to find attribute id '{i}' in report".format(i=i))
        else:
            return a.value

    def _compare_metric_values(self, metric_id):
        value = self.EXPECTED_VALUES[metric_id]
        self.assertEqual(self._get_attribute_value_by_id(metric_id), value)

    def test_mapped_readlength_mean(self):
        self._compare_metric_values(Constants.A_READLENGTH)

    def test_mapped_subread_readlength_mean(self):
        self._compare_metric_values(Constants.A_SUBREAD_LENGTH)


class TestMappingStatsReportLarge(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _to_p = lambda x: os.path.join(_IO_DATA_DIR, x)
        cls.output_dir = tempfile.mkdtemp(suffix="_mapping_stats")
        cls.input_xml = _to_p('lambda_aligned.xml')
        cls.aligned_reads_bam = _to_p('lambda_aligned.bam')
        cls.mode = "external"
        t = tempfile.NamedTemporaryFile(
            delete=False, suffix="mapping_report.json")
        t.close()
        cls.report_json = t.name
        cls.report = to_report(cls.aligned_reads_bam, cls.output_dir)
        if isinstance(cls.report, Report):
            log.info(pprint.pformat(cls.report.to_dict()))
            for table in cls.report.tables:
                log.info(str(table))

    def _get_attribute_value_by_id(self, i):
        """helper method to grab value from the report instance"""
        a = self.report.get_attribute_by_id(i)
        if a is None:
            raise KeyError(
                "Unable to find attribute id '{i}' in report".format(i=i))
        else:
            return a.value

    def test_number_of_attributes(self):
        value = _TOTAL_NUMBER_OF_ATTRIBUTES
        self.assertEqual(len(self.report.attributes), value)

    def test_number_of_plot_groups(self):
        # the Yield pie chart has been removed in the streaming version.
        # only subread accuracy, subread readlength, readlength histograms
        value = _TOTAL_NUMBER_OF_PLOT_GROUPS
        self.assertEqual(len(self.report.plotGroups), value)

    def test_number_of_tables(self):
        value = 1
        self.assertEqual(len(self.report.tables), value)

    def test_number_of_columns_in_table(self):
        self.assertEqual(len(self.report.tables[0].columns), 8)

    @unittest.skip("Filter stats are pulled from the Filter Stat report.")
    def test_post_filter_reads_n(self):
        id_ = Constants.A_FILTERED_READS
        value = 26947
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_subread_accuracy_mean(self):
        id_ = Constants.A_SUBREAD_ACCURACY
        value = 0.8723
        self.assertAlmostEqual(
            self._get_attribute_value_by_id(id_), value, places=2)

    def test_mapped_subread_read_quality_mean(self):
        id_ = Constants.A_SUBREAD_QUALITY
        value = 0.8263
        self.assertAlmostEqual(
            self._get_attribute_value_by_id(id_), value, places=2)

    def test_mapped_reads_n(self):
        id_ = Constants.A_NREADS
        value = 1491
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_subreads_n(self):
        id_ = Constants.A_NSUBREADS
        value = 18768
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_bases_n(self):
        id_ = Constants.A_NBASES
        value = 16555228
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_subread_bases_n(self):
        id_ = Constants.A_SUBREAD_NBASES
        value = 14398098
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_readlength_mean(self):
        id_ = Constants.A_READLENGTH
        value = 11103
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_subread_readlength_mean(self):
        id_ = Constants.A_SUBREAD_LENGTH
        value = 767
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_readlength_q95(self):
        id_ = Constants.A_READLENGTH_Q95
        value = 23470
        self.assertTrue(
            _almost_value(self._get_attribute_value_by_id(id_), value, _Q95_DELTA))

    @unittest.skip("Hot start metrics are not supported in streaming model.")
    def test_mean_max_subread_readlength(self):
        id_ = Constants.A_SUBREAD_LENGTH_MAX_MEAN
        value = 2684
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_readlength_max(self):
        id_ = Constants.A_READLENGTH_MAX
        value = 28619
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_mapped_full_subread_readlength_mean(self):
        id_ = Constants.A_FULL_SUBREAD_LENGTH_MEAN
        value = 1768
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_mean_first_subread_readlength(self):
        id_ = Constants.A_FIRST_SUBREAD_LENGTH_MEAN
        value = 2575
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_pct_first_subreads_ts_lt_50(self):
        id_ = Constants.A_FIRST_SUBREAD_PCT_50
        value = 0.02
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_pct_first_subreads_ts_lt_100(self):
        id_ = Constants.A_FIRST_SUBREAD_PCT_100
        value = 0.02
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_number_of_mapped_reads(self):
        id_ = Constants.A_NREADS
        value = 1491
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_number_of_mapped_subreads(self):
        id_ = Constants.A_NSUBREADS
        value = 18768
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_number_of_aligned_reads(self):
        id_ = Constants.A_NALIGNMENTS
        value = 1491
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_subreadlength_n50(self):
        id_ = Constants.A_SUBREAD_LENGTH_N50
        value = 841
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_readlength_n50(self):
        id_ = Constants.A_READLENGTH_N50
        value = 18057
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

# gmap data from pbsmrtpipe is not yet available for testing, this class needs to be updated
# with fresh data


@unittest.skip
class TestMappingStatsGmapReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _to_p = lambda x: os.path.join(_GMAP_DATA_DIR, x)
        cls.output_dir = tempfile.mkdtemp(suffix="_mapping_stats")
        cls.input_fofn = _to_p('input.fofn')
        cls.aligned_reads_cmph5 = _to_p('aligned_reads.cmp.h5')
        t = tempfile.NamedTemporaryFile(
            delete=False, suffix="mapping_report.json")
        t.close()
        cls.report_json = t.name

        cls.report = to_report(cls.aligned_reads_cmph5, cls.output_dir)
        if isinstance(cls.report, Report):
            log.info(pprint.pformat(cls.report.to_dict()))
            for table in cls.report.tables:
                log.info(str(table))

    def _get_attribute_value_by_id(self, i):
        """helper method to grab value from the report instance"""
        a = self.report.get_attribute_by_id(i)
        if a is None:
            raise KeyError(
                "Unable to find attribute id '{i}' in report".format(i=i))
        else:
            return a.value

    def test_number_of_attributes(self):
        value = _TOTAL_NUMBER_OF_ATTRIBUTES
        self.assertEqual(len(self.report.attributes), value)

    def test_number_of_plot_groups(self):
        value = _TOTAL_NUMBER_OF_PLOT_GROUPS
        self.assertEqual(len(self.report.plotGroups), value)

    def test_number_of_tables(self):
        value = 1
        self.assertEqual(len(self.report.tables), value)

    @unittest.skip("Filter stats are pulled from the Filter Stat report.")
    def test_post_filter_reads_n(self):
        id_ = 'post_filter_reads_n'
        value = 809
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_subread_accuracy_mean(self):
        id_ = Constants.A_SUBREAD_ACCURACY
        value = 0.8465
        self.assertAlmostEqual(
            self._get_attribute_value_by_id(id_), value, places=2)

    def test_mapped_reads_n(self):
        id_ = Constants.A_NREADS
        value = 708
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_subreads_n(self):
        id_ = Constants.A_NSUBREADS
        value = 874
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_bases_n(self):
        id_ = Constants.A_NBASES
        value = 1387289
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_subread_bases_n(self):
        id_ = Constants.A_SUBREAD_NBASES
        value = 1345765
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_readlength_mean(self):
        id_ = Constants.A_READLENGTH
        value = 1959
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_subread_readlength_mean(self):
        id_ = Constants.A_SUBREAD_LENGTH
        value = 1540
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_readlength_q95(self):
        id_ = Constants.A_READLENGTH_Q95
        value = 5900
        self.assertTrue(
            _almost_value(value, self._get_attribute_value_by_id(id_), _Q95_DELTA))

    @unittest.skip("Hot start metrics are not supported in streaming model.")
    def test_mean_max_subread_readlength(self):
        id_ = 'mean_max_subread_readlength'
        value = 1585
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def test_mapped_readlength_max(self):
        id_ = Constants.A_READLENGTH_MAX
        value = 14150
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_mapped_full_subread_readlength_mean(self):
        id_ = 'mapped_full_subread_readlength_mean'
        value = 0
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_mean_first_subread_readlength(self):
        id_ = 'mean_first_subread_readlength'
        value = 1528
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_pct_first_subreads_ts_lt_50(self):
        id_ = 'pct_first_subreads_ts_lt_50'
        value = 13.84
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_pct_first_subreads_ts_lt_100(self):
        id_ = 'pct_first_subreads_ts_lt_100'
        value = 14.27
        self.assertEqual(self._get_attribute_value_by_id(id_), value)


class TestMappingStatsCCSReport(unittest.TestCase):
    EXPECTED_VALUES = {
        Constants.A_SUBREAD_ACCURACY: 0.996,
        Constants.A_NREADS: 743,
        Constants.A_NSUBREADS: 743,
        Constants.A_NBASES: 715295,
        Constants.A_SUBREAD_NBASES: 715295,
        Constants.A_READLENGTH: 963,
        Constants.A_SUBREAD_LENGTH: 963,
        Constants.A_READLENGTH_MAX: 3343,
        Constants.A_READLENGTH_Q95: 1890,
    }

    @classmethod
    def setUpClass(cls):
        _to_p = lambda x: os.path.join(_CCS_DATA_DIR, x)
        cls.output_dir = tempfile.mkdtemp(suffix="_mapping_stats")
        cls.input_fofn = _to_p('input.fofn')
        cls.aligned_reads_xml = _to_p('aligned.consensusalignmentset.xml')
        t = tempfile.NamedTemporaryFile(
            delete=False, suffix="mapping_report.json")
        t.close()
        cls.report_json = t.name
        cls.report = to_report(cls.aligned_reads_xml, cls.output_dir)

        if isinstance(cls.report, Report):
            log.info(pprint.pformat(cls.report.to_dict()))
            for table in cls.report.tables:
                log.info(str(table))

    def _get_attribute_value_by_id(self, i):
        """helper method to grab value from the report instance"""
        a = self.report.get_attribute_by_id(i)
        if a is None:
            raise KeyError(
                "Unable to find attribute id '{i}' in report".format(i=i))
        else:
            return a.value

    def test_number_of_attributes(self):
        value = _TOTAL_NUMBER_OF_ATTRIBUTES
        self.assertEqual(len(self.report.attributes), value)

    def test_number_of_plot_groups(self):
        value = _TOTAL_NUMBER_OF_PLOT_GROUPS
        self.assertEqual(len(self.report.plotGroups), value)

    def test_number_of_tables(self):
        value = 1
        self.assertEqual(len(self.report.tables), value)

    @unittest.skip("Filter metrics should be pulled from Filter Stats report.")
    def test_post_filter_reads_n(self):
        id_ = 'post_filter_reads_n'
        value = 0
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    def _compare_metric_values(self, metric_id):
        value = self.EXPECTED_VALUES[metric_id]
        self.assertEqual(self._get_attribute_value_by_id(metric_id), value)

    def test_mapped_subread_accuracy_mean(self):
        self._compare_metric_values(Constants.A_SUBREAD_ACCURACY)

    def test_mapped_reads_n(self):
        self._compare_metric_values(Constants.A_NREADS)

    def test_mapped_subreads_n(self):
        self._compare_metric_values(Constants.A_NSUBREADS)

    def test_mapped_bases_n(self):
        self._compare_metric_values(Constants.A_NBASES)

    def test_mapped_subread_bases_n(self):
        self._compare_metric_values(Constants.A_SUBREAD_NBASES)

    def test_mapped_readlength_mean(self):
        self._compare_metric_values(Constants.A_READLENGTH)

    def test_mapped_subread_readlength_mean(self):
        self._compare_metric_values(Constants.A_SUBREAD_LENGTH)

    def test_mapped_readlength_max(self):
        self._compare_metric_values(Constants.A_READLENGTH_MAX)

    def test_mapped_readlength_q95(self):
        id_ = Constants.A_READLENGTH_Q95
        print "VALUE IS", self._get_attribute_value_by_id(id_)
        value = self.EXPECTED_VALUES[id_]
        self.assertTrue(
            _almost_value(value, self._get_attribute_value_by_id(id_), _Q95_DELTA))

    @unittest.skip("Hot start metrics are not supported in streaming mode.")
    def test_mean_max_subread_readlength(self):
        id_ = 'mean_max_subread_readlength'
        value = 837
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_mapped_full_subread_readlength_mean(self):
        id_ = 'mapped_full_subread_readlength_mean'
        value = 0
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_mean_first_subread_readlength(self):
        id_ = 'mean_first_subread_readlength'
        value = 837
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_pct_first_subreads_ts_lt_50(self):
        id_ = 'pct_first_subreads_ts_lt_50'
        value = 0.74
        self.assertEqual(self._get_attribute_value_by_id(id_), value)

    @unittest.skip("Deprecated metric from when adapter info used to be included.")
    def test_pct_first_subreads_ts_lt_100(self):
        id_ = 'pct_first_subreads_ts_lt_100'
        value = 0.75
        self.assertEqual(self._get_attribute_value_by_id(id_), value)
