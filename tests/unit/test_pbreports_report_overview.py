import os
import os.path as op
from pprint import pformat
import tempfile
import unittest
import logging

import pbcommand.testkit

from pbreports.report import overview
from base_test_case import run_backticks, validate_report_complete

import pbtestdata

log = logging.getLogger(__name__)


class TestOverViewReport(unittest.TestCase):

    def setUp(self):
        self.input_file = pbtestdata.get_file("subreads-xml")
        self.report = overview.run(self.input_file)
        log.info(pformat(self.report.to_dict()))

    def test_smoke(self):
        """Basic functionality test"""
        self.assertIsNotNone(self.report)
        d = self.report.to_dict()
        self.assertTrue(isinstance(d, dict))
        self.assertTrue('attributes' in d)
        validate_report_complete(self, self.report)

    def test_nmovies_attribute(self):
        id_ = 'nmovies'
        a = self.report.get_attribute_by_id(id_)
        self.assertIsNotNone(a)
        self.assertTrue(a.value, 1)

    def test_ncells_attribute(self):
        id_ = 'ncells'
        a = self.report.get_attribute_by_id(id_)
        self.assertEqual(a.value, 1)


class TestOverviewReportIntegration(unittest.TestCase):

    def setUp(self):
        self.input_file = pbtestdata.get_file("subreads-xml")
        t = tempfile.NamedTemporaryFile(suffix="overview_report.json").name
        self.report_json = t

    def test_basic(self):
        cmd = "overview_report --debug {i} {o}".format(i=self.input_file,
                                                       o=self.report_json)
        rcode = run_backticks(cmd)
        self.assertEqual(rcode, 0)


class TestOverviewToolContract(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.overview"
    REQUIRES_PBCORE = True
    INPUT_FILES = [pbtestdata.get_file("subreads-xml")]
