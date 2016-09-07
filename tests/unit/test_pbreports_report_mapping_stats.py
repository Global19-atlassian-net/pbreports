
import warnings
import tempfile
import unittest
import logging
import shutil
import pprint
import json
import os.path as op
import os
import sys

from pbcommand.pb_io.report import dict_to_report, load_report_from_json
from pbcommand.models.report import Report
import pbcommand.testkit
from pbcore.io import AlignmentSet, ConsensusAlignmentSet

import pbtestdata

from pbreports.report import mapping_stats_ccs
from pbreports.report.mapping_stats import to_report, Constants, spec

from base_test_case import ROOT_DATA_DIR, run_backticks, \
    skip_if_data_dir_not_present, LOCAL_DATA, validate_report_metadata, \
    validate_report_complete

log = logging.getLogger(__name__)

_EXE = "mapping_stats"

_IO_DATA_DIR = op.join(ROOT_DATA_DIR, 'io')
_GMAP_DATA_DIR = op.join(
    ROOT_DATA_DIR, 'mapping_stats', 'gmap_2850031_0011')
_LAMBDA_DATA_DIR = op.join(
    ROOT_DATA_DIR, 'mapping_stats', "lambda_2372215_0007_tiny")
_CCS_DATA_DIR = op.join(LOCAL_DATA, 'mapping_stats_ccs')

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
    output_dir = op.dirname(report_json)
    d = dict(e=_EXE, o=output_dir, a=aligned_bam, j=report_json)

    s = cmd.format(**d)
    log.info(s)
    return s


class TestIntegrationMappingStatsReport(unittest.TestCase):
    ALIGNMENTS = pbtestdata.get_file("aligned-bam")

    def setUp(self):
        self.output_dir = tempfile.mkdtemp(suffix="_mapping_stats")
        self.aligned_reads_bam = self.ALIGNMENTS
        t = tempfile.NamedTemporaryFile(
            delete=False, suffix="mapping_report.json")
        t.close()
        self.report_json = t.name

    def test_basic(self):
        cmd = _to_cmd(self.ALIGNMENTS, self.report_json)
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
        validate_report_metadata(self, report, spec)
        validate_report_complete(self, report)


class TestMappingStatsReport(unittest.TestCase):
    ALIGNMENTS = pbtestdata.get_file("aligned-bam")
    TOTAL_NUMBER_OF_ATTRIBUTES = 12
    TOTAL_NUMBER_OF_PLOT_GROUPS = 4
    EXPECTED_VALUES = {
        Constants.A_SUBREAD_CONCORDANCE: 0.9283,
        Constants.A_NREADS: 48,
        Constants.A_NSUBREADS: 112,
        Constants.A_SUBREAD_NBASES: 60467,
        Constants.A_READLENGTH: 1328,
        Constants.A_SUBREAD_LENGTH: 540,
        Constants.A_READLENGTH_Q95: 5900,
        Constants.A_READLENGTH_MAX: 6765,
        Constants.A_SUBREAD_LENGTH_N50: 632,
        Constants.A_READLENGTH_N50: 2151,
    }

    @classmethod
    def _get_input_file(cls):
        return cls.ALIGNMENTS

    @classmethod
    def setUpClass(cls):
        cls.output_dir = tempfile.mkdtemp(suffix="_mapping_stats")
        t = tempfile.NamedTemporaryFile(
            delete=False, suffix="mapping_report.json")
        t.close()
        cls.report_json = t.name
        cls.report = to_report(cls._get_input_file(), cls.output_dir)
        cls.report.write_json(cls.report_json)
        assert isinstance(cls.report, Report)
        log.info(pprint.pformat(cls.report.to_dict()))
        for table in cls.report.tables:
            log.info(str(table))

    def test_report_metadata(self):
        validate_report_metadata(self, self.report, spec)

    def test_number_of_attributes(self):
        value = self.TOTAL_NUMBER_OF_ATTRIBUTES
        self.assertEqual(len(self.report.attributes), value)

    def test_number_of_plot_groups(self):
        # the Yield pie chart has been removed in the streaming version.
        # only subread concordance, subread readlength, readlength histograms
        value = self.TOTAL_NUMBER_OF_PLOT_GROUPS
        self.assertEqual(len(self.report.plotGroups), value)

    def test_number_of_tables(self):
        value = 1
        self.assertEqual(len(self.report.tables), value)

    def test_number_of_columns_in_table(self):
        self.assertEqual(len(self.report.tables[0].columns), 8)

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

    def test_mapped_subread_bases_n(self):
        self._compare_metric_values(Constants.A_SUBREAD_NBASES)

    def test_mapped_readlength_max(self):
        self._compare_metric_values(Constants.A_READLENGTH_MAX)

    def test_number_of_mapped_reads(self):
        self._compare_metric_values(Constants.A_NREADS)

    def test_number_of_mapped_subreads(self):
        self._compare_metric_values(Constants.A_NSUBREADS)

    def test_mapped_readlength_mean(self):
        self._compare_metric_values(Constants.A_READLENGTH)

    def test_mapped_subread_readlength_mean(self):
        self._compare_metric_values(Constants.A_SUBREAD_LENGTH)

    def test_mapped_subreadlength_n50(self):
        self._compare_metric_values(Constants.A_SUBREAD_LENGTH_N50)

    def test_mapped_readlength_n50(self):
        self._compare_metric_values(Constants.A_READLENGTH_N50)

    def test_mapped_subread_concordance_mean(self):
        id_ = Constants.A_SUBREAD_CONCORDANCE
        value = self.EXPECTED_VALUES[id_]
        self.assertAlmostEqual(
            self._get_attribute_value_by_id(id_), value, places=2)

    def test_mapped_readlength_q95(self):
        id_ = Constants.A_READLENGTH_Q95
        value = self.EXPECTED_VALUES[id_]
        self.assertTrue(
            _almost_value(self._get_attribute_value_by_id(id_), value,
                          delta=_Q95_DELTA))


class TestMappingStatsReportXML(TestMappingStatsReport):

    @classmethod
    def _get_input_file(cls):
        ds_xml = tempfile.NamedTemporaryFile(suffix=".alignmentset.xml").name
        ds = AlignmentSet(cls.ALIGNMENTS, strict=True)
        ds.write(ds_xml)
        return ds_xml

    def test_attributes_order(self):
        attribute_ids = [a.id for a in self.report.attributes]
        self.assertEqual(attribute_ids, [
            Constants.A_SUBREAD_CONCORDANCE,
            Constants.A_NSUBREADS,
            Constants.A_SUBREAD_NBASES,
            Constants.A_SUBREAD_LENGTH,
            Constants.A_SUBREAD_LENGTH_N50,
            Constants.A_SUBREAD_LENGTH_Q95,
            Constants.A_SUBREAD_LENGTH_MAX,
            Constants.A_NREADS,
            Constants.A_READLENGTH,
            Constants.A_READLENGTH_N50,
            Constants.A_READLENGTH_Q95,
            Constants.A_READLENGTH_MAX,
        ])


class TestEmptyBAM(TestMappingStatsReport):
    """
    Test for valid report behavior when the input contains no alignments.
    """

    ALIGNMENTS = op.join(LOCAL_DATA, "mapping_stats", "empty.subreads.bam")
    TOTAL_NUMBER_OF_PLOT_GROUPS = 0
    EXPECTED_VALUES = {
        Constants.A_SUBREAD_CONCORDANCE: 0,
        Constants.A_NREADS: 0,
        Constants.A_NSUBREADS: 0,
        Constants.A_SUBREAD_NBASES: 0,
        Constants.A_READLENGTH: 0,
        Constants.A_SUBREAD_LENGTH: 0,
        Constants.A_READLENGTH_Q95: 0,
        Constants.A_READLENGTH_MAX: 0,
        Constants.A_SUBREAD_LENGTH_N50: 0,
        Constants.A_READLENGTH_N50: 0,
    }

    @classmethod
    def _get_input_file(cls):
        return cls.ALIGNMENTS


class TestPartialEmptyBAM(TestMappingStatsReport):
    """
    Test for valid report behavior when at least one BAM file in the dataset
    is empty (but not all).
    """

    @classmethod
    def _get_input_file(cls):
        ds_xml = tempfile.NamedTemporaryFile(suffix=".alignmentset.xml").name
        bams = [cls.ALIGNMENTS, TestEmptyBAM.ALIGNMENTS]
        ds = AlignmentSet(*bams, strict=True)
        ds.write(ds_xml)
        return ds_xml


@skip_if_data_dir_not_present
class TestMappingStatsReportLarge(TestMappingStatsReport):
    ALIGNMENTS = op.join(_IO_DATA_DIR, "lambda_aligned.xml")
    EXPECTED_VALUES = {
        Constants.A_SUBREAD_CONCORDANCE: 0.8723,
        Constants.A_NREADS: 1491,
        Constants.A_NSUBREADS: 18768,
        Constants.A_SUBREAD_NBASES: 14398098,
        Constants.A_READLENGTH: 11103,
        Constants.A_SUBREAD_LENGTH: 767,
        Constants.A_READLENGTH_Q95: 23470,
        Constants.A_READLENGTH_MAX: 28619,
        Constants.A_SUBREAD_LENGTH_N50: 841,
        Constants.A_READLENGTH_N50: 18057,
    }

    @classmethod
    @skip_if_data_dir_not_present
    def setUpClass(cls):
        super(TestMappingStatsReportLarge, cls).setUpClass()

    @classmethod
    def _get_input_file(cls):
        return cls.ALIGNMENTS


class TestMappingStatsMisc(unittest.TestCase):

    def setUp(self):
        self.bam_file = op.join(LOCAL_DATA, "mapping_stats",
                                "duplicate.subreads.bam")

    def test_duplicate_subreads(self):
        """Test that report doesn't crash on duplicate subreads"""
        output_dir = tempfile.mkdtemp(suffix="_mapping_stats")
        with warnings.catch_warnings(record=True) as w:
            report = to_report(self.bam_file, output_dir)
            shutil.rmtree(output_dir)
            self.assertTrue(w >= 4)


# gmap data from pbsmrtpipe is not yet available for testing, this class needs to be updated
# with fresh data


@unittest.skip
class TestMappingStatsGmapReport(unittest.TestCase):
    TOTAL_NUMBER_OF_PLOT_GROUPS = 4
    TOTAL_NUMBER_OF_ATTRIBUTES = 12

    @classmethod
    def setUpClass(cls):
        _to_p = lambda x: op.join(_GMAP_DATA_DIR, x)
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
        value = self.TOTAL_NUMBER_OF_ATTRIBUTES
        self.assertEqual(len(self.report.attributes), value)

    def test_number_of_plot_groups(self):
        value = self.TOTAL_NUMBER_OF_PLOT_GROUPS
        self.assertEqual(len(self.report.plotGroups), value)

    def test_number_of_tables(self):
        value = 1
        self.assertEqual(len(self.report.tables), value)

    def test_mapped_subread_concordance_mean(self):
        id_ = Constants.A_SUBREAD_CONCORDANCE
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

    def test_mapped_readlength_max(self):
        id_ = Constants.A_READLENGTH_MAX
        value = 14150
        self.assertEqual(self._get_attribute_value_by_id(id_), value)


class TestMappingStatsCCSReport(unittest.TestCase):
    EXPECTED_VALUES = {
        Constants.A_READ_CONCORDANCE: 0.999,
        Constants.A_NREADS: 10,
        Constants.A_READLENGTH: 1123,
        Constants.A_READLENGTH_MAX: 1866,
        Constants.A_READLENGTH_Q95: 1890,
        "number_of_plot_groups": 4,
        "number_of_attributes": 7,
    }

    @classmethod
    def setUpClass(cls):
        cls.output_dir = tempfile.mkdtemp(suffix="_mapping_stats")
        cls.aligned_reads_xml = pbtestdata.get_file("rsii-ccs-aligned")
        t = tempfile.NamedTemporaryFile(
            delete=False, suffix="mapping_report.json")
        t.close()
        cls.report_json = t.name
        cls.report = mapping_stats_ccs.to_report(cls.aligned_reads_xml,
                                                 cls.output_dir)
        cls.report.write_json(cls.report_json)

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
        value = self.EXPECTED_VALUES["number_of_attributes"]
        self.assertEqual(len(self.report.attributes), value)

    def test_number_of_plot_groups(self):
        value = self.EXPECTED_VALUES["number_of_plot_groups"]
        self.assertEqual(len(self.report.plotGroups), value)

    def test_number_of_tables(self):
        value = 1
        self.assertEqual(len(self.report.tables), value)

    def test_report_metadata(self):
        validate_report_metadata(self, self.report, mapping_stats_ccs.spec)

    def _compare_metric_values(self, metric_id):
        value = self.EXPECTED_VALUES[metric_id]
        self.assertEqual(self._get_attribute_value_by_id(metric_id), value)

    def test_mapped_read_concordance_mean(self):
        self._compare_metric_values(Constants.A_READ_CONCORDANCE)

    def test_mapped_reads_n(self):
        self._compare_metric_values(Constants.A_NREADS)

    def test_mapped_readlength_mean(self):
        self._compare_metric_values(Constants.A_READLENGTH)

    def test_mapped_readlength_max(self):
        self._compare_metric_values(Constants.A_READLENGTH_MAX)

    def test_mapped_readlength_q95(self):
        id_ = Constants.A_READLENGTH_Q95
        value = self.EXPECTED_VALUES[id_]
        self.assertTrue(
            _almost_value(value, self._get_attribute_value_by_id(id_), _Q95_DELTA))

    def test_attributes_order(self):
        attribute_ids = [a.id for a in self.report.attributes]
        self.assertEqual(attribute_ids, [
            Constants.A_READ_CONCORDANCE,
            Constants.A_NREADS,
            Constants.A_NBASES,
            Constants.A_READLENGTH,
            Constants.A_READLENGTH_N50,
            Constants.A_READLENGTH_Q95,
            Constants.A_READLENGTH_MAX,
        ])


class TestPbreportMappingStats(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.mapping_stats "
    REQUIRES_PBCORE = True
    INPUT_FILES = [pbtestdata.get_file("aligned-xml")]
    TASK_OPTIONS = {}

    def run_after(self, rtc, output_dir):
        r = load_report_from_json(rtc.task.output_files[0])
        with AlignmentSet(self.INPUT_FILES[0]) as ds:
            self.assertEqual(r._dataset_uuids, [ds.uuid])
        validate_report_metadata(self, r, spec)


class TestPbreportMappingStatsCCS(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.mapping_stats_ccs "
    REQUIRES_PBCORE = True
    INPUT_FILES = [pbtestdata.get_file("rsii-ccs-aligned")]
    TASK_OPTIONS = {}

    def run_after(self, rtc, output_dir):
        r = load_report_from_json(rtc.task.output_files[0])
        with ConsensusAlignmentSet(self.INPUT_FILES[0]) as ds:
            self.assertEqual(r._dataset_uuids, [ds.uuid])
            self.assertEqual(len(r.plotGroups), 4)
        validate_report_metadata(self, r, mapping_stats_ccs.spec)


@skip_if_data_dir_not_present
class TestMappingStatsMultipleMovies(TestMappingStatsReportLarge):
    ALIGNMENTS = "/pbi/dept/secondary/siv/testdata/SA3-RS/ecoli/tiny-multimovie/Alignment_Results/combined.alignmentset.xml"
    EXPECTED_VALUES = {
        Constants.A_SUBREAD_CONCORDANCE: 0.829,
        Constants.A_NSUBREADS: 27,
        Constants.A_SUBREAD_NBASES: 120373,
        Constants.A_SUBREAD_LENGTH: 4458,
        Constants.A_SUBREAD_LENGTH_N50: 10937,
        Constants.A_NREADS: 6,
        Constants.A_READLENGTH: 20328,
        Constants.A_READLENGTH_N50: 24306,
        Constants.A_READLENGTH_Q95: 32080,
        Constants.A_READLENGTH_MAX: 32086,
    }

    def test_all_movies_in_table_have_mapped_reads(self):
        for column in self.report.tables[0].columns:
            if column.id == "mapped_reads":
                self.assertTrue(all([x > 0 for x in column.values]),
                                "Not all movies have a mapped read")
