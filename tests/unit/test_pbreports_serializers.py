import os
import logging
import unittest
import json
from pprint import pformat

from pbreports.serializers import dict_to_report

_SERIALIZED_JSON_DIR = 'data_serialized_json'
_DATA_DIR = os.path.join(os.path.dirname(__file__), _SERIALIZED_JSON_DIR)

log = logging.getLogger(__name__)


def _to_report(name):
    file_name = os.path.join(_DATA_DIR, name)
    log.info("loading json report from {f}".format(f=file_name))

    with open(file_name, 'r') as f:
        d = json.loads(f.read())

    log.info("loading dict:")
    log.info(pformat(d))
    r = dict_to_report(d)
    log.info("Convert report to dict:")
    log.info(pformat(r.to_dict()))
    return r


class TestSerializationOverviewReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        name = 'overview.json'
        cls.report = _to_report(name)

    def test_id(self):
        self.assertEqual(self.report.id, "overview")

    def test_attributes(self):
        self.assertTrue(len(self.report.attributes), 2)


class TestSerializationAdapterReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        file_name = 'filter_reports_adapters.json'
        cls.report = _to_report(file_name)

    def test_id(self):
        self.assertEqual(self.report.id, 'adapter')

    def test_attributes(self):
        self.assertEqual(len(self.report.attributes), 6)

    def test_plotgroups(self):
        self.assertEqual(len(self.report.plotGroups), 1)

    def test_plots(self):
        self.assertEqual(len(self.report.plotGroups[0].plots), 1)





