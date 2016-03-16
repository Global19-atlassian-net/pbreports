
from unittest import SkipTest
import functools
import unittest
import tempfile
import logging
import pprint
import json
import os

from pbcommand.pb_io.report import dict_to_report
from pbcommand.models.report import Report

from pbreports.report.filter_stats import (to_report,
                                           NoPassedFilteredReadsError,
                                           NoFilteredReadsError,
                                           CsvParserError, Constants)

from base_test_case import ROOT_DATA_DIR, run_backticks, \
    skip_if_data_dir_not_present, AttributesTestBase, LOCAL_DATA

log = logging.getLogger(__name__)

_DATA_DIR_NAME = 'filter_stats'


def __get_from_constant(prefix_str, c):
    names = [i for i in dir(c) if i.startswith(prefix_str)]
    return [getattr(Constants, n) for n in names]


_get_attribute_names = functools.partial(__get_from_constant, 'A_')
_get_image_names = functools.partial(__get_from_constant, 'I_')


class TestFilterStats(unittest.TestCase, AttributesTestBase):
    CSV_FILE = os.path.join(LOCAL_DATA, _DATA_DIR_NAME, "filtered_summary.csv")
    TEST_VALUES = {
        "reads_n_pre_filter": 49,
        "reads_n_post_filter": 19,
        "mean_read_score_pre_filter": 0.33447,
        "mean_read_score_post_filter": 0.86258,
        "mean_read_length_post_filter": 2067,
        "base_n_pre_filter": 39278,
        "base_n_post_filter": 39278,
        # this is 730 from the XML report, perhaps due to
        # sloppy rounding?
        "mean_read_length_pre_filter": 801,
        "n50_read_length_pre_filter": 3315,
        "n50_read_length_post_filter": 3315,
    }

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(cls.CSV_FILE):
            raise SkipTest("File {f} not found".format(f=cls.CSV_FILE))
        cls.output_dir = tempfile.mkdtemp(suffix="filter_stats_")
        t = tempfile.NamedTemporaryFile(dir=cls.output_dir, delete=False)
        t.close()
        cls.report_json = t.name
        cls.report = to_report(cls.CSV_FILE, cls.output_dir, cls.report_json)

    def test_basic(self):
        self.assertIsNotNone(self.report)
        log.info(pprint.pformat(self.report.to_dict()))

    def test_write_json(self):
        self.report.write_json(self.report_json)

        with open(self.report_json, 'r') as f:
            d = json.loads(f.read())

        report = dict_to_report(d)
        self.assertTrue(isinstance(report, Report))

    def test_tables(self):
        for table in self.report.tables:
            log.info(str(table))

        self.assertEqual(len(self.report.tables), 1)

    def test_smoke_attributes(self):

        attr_ids = _get_attribute_names(Constants)
        for attr_id in attr_ids:
            a = self.report.get_attribute_by_id(attr_id)
            self.assertIsNotNone(a)

    def test_images(self):
        image_names = _get_image_names(Constants)
        for image_name in image_names:
            p = os.path.join(self.output_dir, image_name)
            if not os.path.exists(p):
                log.error("Unable fot find image {p}".format(p=p))
            self.assertTrue(os.path.exists(p))

    def test_attribute_reads_n_pre_filter(self):
        self._test_attribute('reads_n_pre_filter')

    def test_attribute_reads_n_post_filter(self):
        self._test_attribute('reads_n_post_filter')

    def test_attribute_mean_read_score_pre_filter(self):
        self._test_attribute('mean_read_score_pre_filter', decimals=3)

    def test_attribute_mean_read_score_post_filter(self):
        self._test_attribute('mean_read_score_post_filter', decimals=3)

    def test_attribute_mean_read_length_post_filter(self):
        self._test_attribute('mean_read_length_post_filter')

    def test_attribute_pre_filter_nbases(self):
        self._test_attribute('base_n_pre_filter')

    def test_attribute_post_filter_nbases(self):
        self._test_attribute('base_n_post_filter')

    def test_attribute_pre_filter_mean_readlength(self):
        self._test_attribute('mean_read_length_pre_filter')

    def test_attribute_n50_read_length_pre_filter(self):
        self._test_attribute('n50_read_length_pre_filter')

    def test_attribute_n50_read_length_post_filter(self):
        self._test_attribute('n50_read_length_post_filter')


@skip_if_data_dir_not_present
class TestFilterStatsLarge(unittest.TestCase, AttributesTestBase):
    CSV_FILE = os.path.join(
        ROOT_DATA_DIR, _DATA_DIR_NAME, "filtered_summary.csv")
    TEST_VALUES = {
        "reads_n_pre_filter": 300584,
        "reads_n_post_filter": 93408,
        "mean_read_score_pre_filter": 0.2680,
        "mean_read_score_post_filter": 0.856,
        "mean_read_length_post_filter": 2285,
        "base_n_pre_filter": 219279027,
        "base_n_post_filter": 213483772,
        # this is 730 from the XML report, perhaps due to
        # sloppy rounding?
        "mean_read_length_pre_filter": 729,
        "n50_read_length_pre_filter": 3449,
        "n50_read_length_post_filter": 3451,
    }


class TestFilterStatsNoFilteredReads(unittest.TestCase):

    def test_01(self):
        name = "filtered_summary_with_no_reads.csv"
        file_name = os.path.join(LOCAL_DATA, _DATA_DIR_NAME, name)
        output_dir = tempfile.mkdtemp(suffix="filter_stats_")
        t = tempfile.NamedTemporaryFile(dir=output_dir, delete=False)
        t.close()
        report_json = t.name
        with self.assertRaises(NoFilteredReadsError) as e:
            report = to_report(file_name, output_dir, report_json)
            log.info(report)
            log.info(e)


class TestFilterStatsNoReadsPassedFilter(unittest.TestCase):

    def test_01(self):
        name = "filtered_summary_with_no_passed_filter.csv"
        file_name = os.path.join(LOCAL_DATA, _DATA_DIR_NAME, name)
        output_dir = tempfile.mkdtemp(suffix="filter_stats_")
        t = tempfile.NamedTemporaryFile(dir=output_dir, delete=False)
        t.close()
        report_json = t.name
        with self.assertRaises(NoPassedFilteredReadsError) as e:
            report = to_report(file_name, output_dir, report_json)
            log.info(report)
            log.info(e)


class TestFilterStatsCsvParserError(unittest.TestCase):

    def test_01(self):
        name = "filtered_summary_with_missing_header_field.csv"
        file_name = os.path.join(LOCAL_DATA, _DATA_DIR_NAME, name)
        output_dir = tempfile.mkdtemp(suffix="filter_stats_")
        t = tempfile.NamedTemporaryFile(dir=output_dir, delete=False)
        t.close()
        report_json = t.name
        with self.assertRaises(CsvParserError) as e:
            report = to_report(file_name, output_dir, report_json)
            log.info(report)
            log.info(e)


class TestFilterStatsAllQvsZero(unittest.TestCase):

    def test_01(self):
        name = "filtered_summary_with_all_qvs_zero.csv"
        file_name = os.path.join(LOCAL_DATA, _DATA_DIR_NAME, name)
        output_dir = tempfile.mkdtemp(suffix="filter_stats_")
        t = tempfile.NamedTemporaryFile(dir=output_dir, delete=False)
        t.close()
        report_json = t.name
        report = to_report(file_name, output_dir, report_json)

        self.assertIsInstance(report, Report)
        log.info(report)
        log.info(report.tables[0])


class TestIntegrationFilterStats(unittest.TestCase):
    CSV_FILE = os.path.join(LOCAL_DATA, _DATA_DIR_NAME, "filtered_summary.csv")

    def test_basic(self):
        output_dir = tempfile.mkdtemp(suffix="filter_stats_integration_")
        t = tempfile.NamedTemporaryFile(dir=output_dir, delete=False)
        t.close()
        report_json = t.name

        exe = "filter_stats"
        cmd = "{e} --debug -o {o} -r {r} {csv}".format(e=exe, o=output_dir,
                                                       r=report_json,
                                                       csv=self.CSV_FILE)
        rcode = run_backticks(cmd)
        self.assertEqual(rcode, 0)

        with open(report_json, 'r') as f:
            s = json.load(f)
            log.info("JsonReport: ")
            log.info(pprint.pformat(s, indent=4))

        self.assertIsNotNone(s)

        # cleanup
        os.remove(report_json)


@skip_if_data_dir_not_present
class TestFilterStatsWithOnlyZeroQvs(unittest.TestCase):

    def test_basic(self):
        # this file has only QV's == 0
        name = "filtered_summary.csv"
        file_name = os.path.join(
            ROOT_DATA_DIR, _DATA_DIR_NAME, 'bug_24271', name)
        output_dir = tempfile.mkdtemp(suffix="filter_stats_")
        t = tempfile.NamedTemporaryFile(dir=output_dir, delete=False)
        t.close()
        report_json = t.name
        report = to_report(file_name, output_dir, report_json)
        # if we've got here, the report construction doesn't fail.
        self.assertIsInstance(report, Report)
