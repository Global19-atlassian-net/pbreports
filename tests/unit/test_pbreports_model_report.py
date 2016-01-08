import json
import logging
from pprint import pformat
import re
import unittest

from pbreports.model.model import (Report, Attribute, PlotGroup, Plot, Table,
                                   Column, PbReportError)

log = logging.getLogger(__name__)


class TestReport(unittest.TestCase):

    def test_report_null_ns(self):
        """Can't create a report without a namespace."""
        with self.assertRaises(PbReportError):
            r = Report(None)

    def test_report_empty_ns(self):
        """Can't create a report with an empty namespace."""
        with self.assertRaises(PbReportError):
            r = Report("")

    def test_duplicate_ids(self):
        """Can't add elements with the same id."""
        with self.assertRaises(PbReportError):
            r = Report('redfang')
            r.add_attribute(Attribute('a', 'b'))
            r.add_attribute(Attribute('a', 'c'))

    def test_illegal_id(self):
        """Ids must be alphanumberic with underscores"""
        with self.assertRaises(PbReportError):
            r = Report('redfang')
            r.add_attribute(Attribute('a b', 'b'))
            r.add_attribute(Attribute('a', 'c'))

    def test_empty_id(self):
        with self.assertRaises(PbReportError):
            r = Report('')

    def test_uppercase_id(self):
        with self.assertRaises(PbReportError):
            r = Report('A')

    def test_to_dict(self):
        """
        The id of report sub elements is prepended with the id of the parent
        element when to_dict is called.
        """
        r = Report('redfang')
        a = Attribute('a', 'b')
        a2 = Attribute('a2', 'b2')
        r.add_attribute(a)
        r.add_attribute(a2)

        pg = PlotGroup('pgid')
        pg.add_plot(Plot('pid', 'anImg'))
        pg.add_plot(Plot('pid2', 'anImg2'))
        r.add_plotgroup(pg)

        t = Table('tabid')
        t.add_column(Column('c1'))
        r.add_table(t)

        d = r.to_dict()

        log.debug("\n" + pformat(d))

        self.assertEqual('redfang', d['id'])
        self.assertEqual('redfang.a', d['attributes'][0]['id'])
        self.assertEqual('redfang.a2', d['attributes'][1]['id'])
        self.assertEqual('redfang.pgid', d['plotGroups'][0]['id'])
        self.assertEqual('redfang.pgid.pid', d['plotGroups'][0]['plots'][0]['id'])
        self.assertEqual('redfang.pgid.pid2', d['plotGroups'][0]['plots'][1]['id'])

        self.assertEqual('redfang.tabid', d['tables'][0]['id'])
        self.assertEqual('redfang.tabid.c1', d['tables'][0]['columns'][0]['id'])

    def test_version_and_changelist(self):
        r = Report('example')
        d = r.to_dict()
        log.info("\n" + pformat(d))
        self.assertTrue('_version' in d)
        self.assertTrue('_changelist' in d)

        # Not used anymore. The all version information is encoded in _version.
        # that should be sufficient.
        # self.assertTrue(isinstance(d['_changelist'], int))
        rx = re.compile(r'[0-9]*\.[0-9]*')
        self.assertIsNotNone(rx.search(d['_version']))

    def test_to_dict_multi(self):
        """
        Multiple complex elements.
        The id of report sub elements is prepended with the id of the parent
        element when to_dict is called.
        """
        r = Report('redfang')
        a = Attribute('a', 'b')
        a2 = Attribute('a2', 'b2')
        r.add_attribute(a)
        r.add_attribute(a2)

        pg = PlotGroup('pgid')
        pg.add_plot(Plot('pid', 'anImg'))
        pg.add_plot(Plot('pid2', 'anImg2'))
        r.add_plotgroup(pg)

        pg = PlotGroup('pgid2')
        pg.add_plot(Plot('pid2', 'anImg2'))
        pg.add_plot(Plot('pid22', 'anImg22'))
        r.add_plotgroup(pg)

        t = Table('tabid')
        t.add_column(Column('c1'))
        r.add_table(t)

        t = Table('tabid2')
        t.add_column(Column('c2'))
        r.add_table(t)

        d = r.to_dict()

        log.debug(str(d))

        self.assertEqual('redfang', d['id'])
        self.assertEqual('redfang.a', d['attributes'][0]['id'])
        self.assertEqual('redfang.a2', d['attributes'][1]['id'])

        self.assertEqual('redfang.pgid', d['plotGroups'][0]['id'])
        self.assertEqual('redfang.pgid.pid', d['plotGroups'][0]['plots'][0]['id'])
        self.assertEqual('redfang.pgid.pid2', d['plotGroups'][0]['plots'][1]['id'])

        self.assertEqual('redfang.pgid2', d['plotGroups'][1]['id'])
        self.assertEqual('redfang.pgid2.pid2', d['plotGroups'][1]['plots'][0]['id'])
        self.assertEqual('redfang.pgid2.pid22', d['plotGroups'][1]['plots'][1]['id'])

        self.assertEqual('redfang.tabid', d['tables'][0]['id'])
        self.assertEqual('redfang.tabid.c1', d['tables'][0]['columns'][0]['id'])

        self.assertEqual('redfang.tabid2', d['tables'][1]['id'])
        self.assertEqual('redfang.tabid2.c2', d['tables'][1]['columns'][0]['id'])

        log.info(repr(r))
        self.assertIsNotNone(repr(r))

    def test_get_attribute_by_id(self):
        a = Attribute('a', 'b')
        a2 = Attribute('b', 'b2')
        attributes = [a, a2]
        r = Report('redfang', attributes=attributes)

        a1 = r.get_attribute_by_id('a')

        self.assertEqual(a, a1)

    def test_get_attribute_by_id_with_bad_id(self):
        a1 = Attribute('a', 'b')
        a2 = Attribute('b', 'b2')
        attributes = [a1, a2]
        report = Report('redfang', attributes=attributes)

        a = report.get_attribute_by_id('a')
        self.assertEqual(a.value, 'b')

        bad_a = report.get_attribute_by_id('id_that_does_not_exist')
        self.assertIsNone(bad_a)
