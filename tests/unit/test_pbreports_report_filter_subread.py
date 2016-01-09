import json
import os
from pprint import pformat
import unittest
import logging
import tempfile
import functools

from pbreports.model.model import Report
from pbreports.serializers import dict_to_report
from pbreports.report.filter_subread import (to_report,
                                             NoSubreadsFound,
                                             NoSubreadsPassedFilter,
                                             Constants)

from base_test_case import ROOT_DATA_DIR, run_backticks, \
    skip_if_data_dir_not_present

_DATA_DIR_NAME = 'filter_subread'

log = logging.getLogger(__name__)

def __get_from_constant(prefix_str, c):
    names = [i for i in dir(c) if i.startswith(prefix_str)]
    return [getattr(Constants, n) for n in names]


_get_attribute_names = functools.partial(__get_from_constant, 'A_')
_get_image_names = functools.partial(__get_from_constant, 'I_')


@skip_if_data_dir_not_present
class TestFilterSubreadSummaryReport(unittest.TestCase):

    @classmethod
    @skip_if_data_dir_not_present
    def setUpClass(cls):
        name = "filtered_subread_summary.csv"
        cls.filtered_subread_summary_csv = os.path.join(ROOT_DATA_DIR, _DATA_DIR_NAME, name)
        log.info("Using {f}".format(f=cls.filtered_subread_summary_csv))
        output_dir = tempfile.mkdtemp(suffix="filter_subread_")
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        t.close()
        cls.report_json = t.name
        cls.report = to_report(cls.filtered_subread_summary_csv, output_dir)
        cls.output_dir = output_dir

    def test_basic(self):
        self.assertIsNotNone(self.report)

    def test_write_json(self):

        log.info(pformat(self.report.to_dict()))
        with open(self.report_json, 'w') as f:
            f.write(self.report.to_json())

        with open(self.report_json, 'r') as f:
            d = json.loads(f.read())

        report = dict_to_report(d)
        log.info("deserialized report:")
        log.info(pformat(report.to_dict()))
        self.assertIsNotNone(isinstance(report, Report))

        # Cleanup
        os.remove(self.report_json)

    def test_images(self):
        image_names = _get_image_names(Constants)
        for image_name in image_names:
            p = os.path.join(self.output_dir, image_name)
            if not os.path.exists(p):
                log.error("Unable fot find image {p}".format(p=p))
            self.assertTrue(os.path.exists(p))

    def _test_attribute(self, id_, correct_value, decimals=None):
        a = self.report.get_attribute_by_id(id_)
        if decimals is None:
            self.assertEqual(a.value, correct_value)
        else:
            self.assertAlmostEqual(a.value, correct_value, decimals)

    def test_attribute_filter_subread_n50(self):
        value = 948
        self._test_attribute(Constants.A_N50, value)

    def test_attribute_filter_subread_nbases(self):
        value = 203202952
        self._test_attribute(Constants.A_NBASES, value)

    def test_attribute_filter_subread_nreads(self):
        value = 261621
        self._test_attribute(Constants.A_NREADS, value)

    def test_attribute_filter_subread_mean(self):
        value = 776
        self._test_attribute(Constants.A_MEAN, value)

    def test_plot_group_id(self):
        ids =[p.id for p in self.report.plotGroups]
        cids = [Constants.PG_SUBREAD_LENGTH]
        self.assertListEqual(ids, cids)


class TestFilterSubreadSummaryReportIntegration(TestFilterSubreadSummaryReport):

    @skip_if_data_dir_not_present
    def test_basic(self):
        output_dir = tempfile.mkdtemp(suffix="filter_subread_")
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        t.close()
        report_json = t.name
        exe = "filter_subread"
        cmd = "{e} --debug -o {o} -r {r} {csv}".format(e=exe,
                                                       csv=self.filtered_subread_summary_csv,
                                                       r=report_json,
                                                       o=output_dir)

        rcode = run_backticks(cmd)
        self.assertEqual(0, rcode)

        with open(report_json, 'r') as f:
            d = json.loads(f.read())

        report = dict_to_report(d)
        log.info("deserialized report:")
        log.info(pformat(report.to_dict()))

        self.assertIsNotNone(isinstance(report, Report))

        # Cleanup
        self.assertTrue(os.path.exists(report_json))
        os.remove(report_json)


@skip_if_data_dir_not_present
class TestFilterSubreadReportNoSubreadsFound(unittest.TestCase):
    def test_basic(self):
        name = "filtered_subread_summary_empty.csv"
        filtered_subread_summary_csv = os.path.join(ROOT_DATA_DIR, _DATA_DIR_NAME, name)
        log.info("Using {f}".format(f=filtered_subread_summary_csv))
        output_dir = tempfile.mkdtemp(suffix="filter_subread_")
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        t.close()
        with self.assertRaises(NoSubreadsFound):
            report = to_report(filtered_subread_summary_csv, output_dir)
            log.info(report)


@skip_if_data_dir_not_present
class TestFilterSubreadReportNoSubreadsPassedFilterException(unittest.TestCase):
    def test_basic(self):
        name = "filtered_subread_summary_no_passed.csv"
        filtered_subread_summary_csv = os.path.join(ROOT_DATA_DIR, _DATA_DIR_NAME, name)
        log.info("Using {f}".format(f=filtered_subread_summary_csv))
        output_dir = tempfile.mkdtemp(suffix="filter_subread_")
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        t.close()
        with self.assertRaises(NoSubreadsPassedFilter):
            report = to_report(filtered_subread_summary_csv, output_dir)
            log.info(report)

