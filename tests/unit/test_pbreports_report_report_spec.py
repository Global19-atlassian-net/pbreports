#!/usr/bin/env python

import os
import os.path as op
import unittest

from pbreports.report.report_spec import (
    MetaAttribute, MetaPlotGroup, MetaPlot, MetaColumn, MetaTable, MetaReport)
from base_test_case import LOCAL_DATA, _DIR_NAME

SPEC_DIR = os.path.join(_DIR_NAME, '../../pbreports/report/specs/')
LOCAL_DATA_DIR = op.join(LOCAL_DATA, "report_spec")
PLOT1_FILE = op.relpath(op.join(LOCAL_DATA_DIR, "plot1.png"))
THUMBNAIL1_FILE = op.relpath(op.join(LOCAL_DATA_DIR, "thumbnail1.png"))
THUMBNAIL2_FILE = op.relpath(op.join(LOCAL_DATA_DIR, "thumbnail2.png"))
TEST_JSON = op.join(LOCAL_DATA_DIR, "test.json")

# test if all spec files can be read in
class TestReadingMetaReports(unittest.TestCase):

	def test_read_specs(self):
		for spec in os.listdir(SPEC_DIR):
			specfile = op.join(SPEC_DIR, spec)
			tmp_meta_rpt = MetaReport.from_json(specfile)

# test if bad input produces appropriate error messages
class TestBadInput(unittest.TestCase):

	def setUp(self):
        	self.meta_rpt = MetaReport.from_json(TEST_JSON)

	def test_attribute(self):
		with self.assertRaises(AssertionError):
			self.meta_rpt.get_meta_attribute("attribute1").as_attribute(1.0)
		with self.assertRaises(AssertionError):
			self.meta_rpt.get_meta_attribute("attribute2").as_attribute(2)
		with self.assertRaises(AssertionError):
			self.meta_rpt.get_meta_attribute("attribute3").as_attribute(3)

	def test_column(self):
		with self.assertRaises(AssertionError):
			self.meta_rpt.get_meta_table("table1").get_meta_column("column1").as_column(values=[1,2.0,3])
                with self.assertRaises(AssertionError):
                        self.meta_rpt.get_meta_table("table2").get_meta_column("column1").as_column(values=[3.1,2.0,3])
                with self.assertRaises(AssertionError):
                        self.meta_rpt.get_meta_table("table2").get_meta_column("column2").as_column(values=["movie1",2.0,"movie3"])

# test to see if values are read in correctly and retrievable
class TestCorrectReportValues(unittest.TestCase):
	
	def setUp(self):
		self.meta_rpt = MetaReport.from_json(TEST_JSON)

		attributes = []
		attributes.append(self.meta_rpt.get_meta_attribute("attribute1").as_attribute(1))
		attributes.append(self.meta_rpt.get_meta_attribute("attribute2").as_attribute(2.2))
		attributes.append(self.meta_rpt.get_meta_attribute("attribute3").as_attribute("test_string"))

		plotgroups = []
		plots = []
		plots.append(self.meta_rpt.get_meta_plotgroup("plotgroup1").get_meta_plot("plot1").as_plot(image=PLOT1_FILE, thumbnail=THUMBNAIL1_FILE))
		plotgroups.append(self.meta_rpt.get_meta_plotgroup("plotgroup1").as_plotgroup(thumbnail=THUMBNAIL2_FILE, plots=plots))

		tables = []
		columns = []
		columns.append(self.meta_rpt.get_meta_table("table1").get_meta_column("column1").as_column(values=[1,22,142]))
		tables.append(self.meta_rpt.get_meta_table("table1").as_table(columns=columns))
		columns = []
		columns.append(self.meta_rpt.get_meta_table("table2").get_meta_column("column1").as_column(values=[1.0,2.1,3.37]))
		columns.append(self.meta_rpt.get_meta_table("table2").get_meta_column("column2").as_column(values=["string1","string2","string3"]))
		tables.append(self.meta_rpt.get_meta_table("table2").as_table(columns=columns))

		self.rpt = self.meta_rpt.as_report(attributes=attributes,plotgroups=plotgroups,tables=tables)

	def test_attribute(self):
		self.assertEqual(self.rpt.get_attribute_by_id('attribute1').value, 1)
		self.assertEqual(self.rpt.get_attribute_by_id('attribute2').value, 2.2)
		self.assertEqual(self.rpt.get_attribute_by_id('attribute3').value, 'test_string')

        def test_column(self):
                self.assertEqual(self.rpt.get_table_by_id('table1').get_column_by_id('column1').values, [1,22,142])
                self.assertEqual(self.rpt.get_table_by_id('table2').get_column_by_id('column1').values, [1.0,2.1,3.37])
		self.assertEqual(self.rpt.get_table_by_id('table2').get_column_by_id('column2').values, ["string1","string2","string3"])

	def test_plot(self):
		self.assertEqual(self.rpt.get_plotgroup_by_id('plotgroup1').get_plot_by_id('plot1').image, PLOT1_FILE)
                self.assertEqual(self.rpt.get_plotgroup_by_id('plotgroup1').get_plot_by_id('plot1').thumbnail, THUMBNAIL1_FILE)

	def test_plotgroup(self):
#		self.assertEqual(rpt.get_plotgroup_by_id('plotgroup1').legend, LEGEND1_FILE)
                self.assertEqual(self.rpt.get_plotgroup_by_id('plotgroup1').thumbnail, THUMBNAIL2_FILE)
		
# test to see if metavalues are read in correctly and retrievable 
class TestCorrectMetaReportValues(unittest.TestCase):
	
	def setUp(self):	
        	self.meta_rpt = MetaReport.from_json(TEST_JSON)
	
	def test_attribute(self):
		self.assertEqual(self.meta_rpt.get_meta_attribute('attribute1').type, 'int')
		self.assertEqual(self.meta_rpt.get_meta_attribute('attribute1').description, 'An attribute of type int')
		self.assertEqual(self.meta_rpt.get_meta_attribute('attribute1').name, 'Attribute 1')
		self.assertEqual(self.meta_rpt.get_meta_attribute('attribute1').id, 'attribute1')

	def test_plotgroup(self):
		self.assertEqual(self.meta_rpt.get_meta_plotgroup('plotgroup1').id, 'plotgroup1')
		self.assertEqual(self.meta_rpt.get_meta_plotgroup('plotgroup1').title, 'Plotgroup 1')
		self.assertEqual(self.meta_rpt.get_meta_plotgroup('plotgroup1').description, 'The first plotgroup')
#		self.assertEqual(self.meta_rpt.get_meta_plotgroup('plotgroup1').legend, 'legend1')

	def test_plot(self):
		self.assertEqual(self.meta_rpt.get_meta_plotgroup('plotgroup1').get_meta_plot('plot1').id, 'plot1')
		self.assertEqual(self.meta_rpt.get_meta_plotgroup('plotgroup1').get_meta_plot('plot1').description, 'The first plot of the first plotgroup')
		self.assertEqual(self.meta_rpt.get_meta_plotgroup('plotgroup1').get_meta_plot('plot1').caption, 'Plot 1')
                self.assertEqual(self.meta_rpt.get_meta_plotgroup('plotgroup1').get_meta_plot('plot1').xlab, 'x variable')
                self.assertEqual(self.meta_rpt.get_meta_plotgroup('plotgroup1').get_meta_plot('plot1').ylab, 'y variable')

	def test_table(self):
                self.assertEqual(self.meta_rpt.get_meta_table('table1').id, 'table1')
                self.assertEqual(self.meta_rpt.get_meta_table('table1').title, 'Table 1')
                self.assertEqual(self.meta_rpt.get_meta_table('table1').description, 'The first table')

	def test_column(self):
                self.assertEqual(self.meta_rpt.get_meta_table('table1').get_meta_column('column1').id, 'column1')
                self.assertEqual(self.meta_rpt.get_meta_table('table1').get_meta_column('column1').header, 'Column 1')
                self.assertEqual(self.meta_rpt.get_meta_table('table1').get_meta_column('column1').description, 'A column of type int')
                self.assertEqual(self.meta_rpt.get_meta_table('table1').get_meta_column('column1').type, 'int')


class TestApplyView(unittest.TestCase):

        def setUp(self):
                self.meta_rpt = MetaReport.from_json(TEST_JSON)

                attributes = []
                attributes.append(self.meta_rpt.get_meta_attribute("attribute1").as_attribute(1))
                attributes.append(self.meta_rpt.get_meta_attribute("attribute2").as_attribute(2.2))
                attributes.append(self.meta_rpt.get_meta_attribute("attribute3").as_attribute("test_string"))

                plotgroups = []
                plots = []
                plots.append(self.meta_rpt.get_meta_plotgroup("plotgroup1").get_meta_plot("plot1").as_plot(image=PLOT1_FILE, thumbnail=THUMBNAIL1_FILE))
                plotgroups.append(self.meta_rpt.get_meta_plotgroup("plotgroup1").as_plotgroup(thumbnail=THUMBNAIL2_FILE, plots=plots))

                tables = []
                columns = []
                columns.append(self.meta_rpt.get_meta_table("table1").get_meta_column("column1").as_column(values=[1,22,142]))
                tables.append(self.meta_rpt.get_meta_table("table1").as_table(columns=columns))
                columns = []
                columns.append(self.meta_rpt.get_meta_table("table2").get_meta_column("column1").as_column(values=[1.0,2.1,3.37]))
                columns.append(self.meta_rpt.get_meta_table("table2").get_meta_column("column2").as_column(values=["string1","string2","string3"]))
                tables.append(self.meta_rpt.get_meta_table("table2").as_table(columns=columns))

                self.rpt = self.meta_rpt.as_report(attributes=attributes,plotgroups=plotgroups,tables=tables)
		self.rpt = self.meta_rpt.apply_view(self.rpt)

        def test_attribute(self):
                self.assertEqual(self.rpt.get_attribute_by_id('attribute1').value, 1)
                self.assertEqual(self.rpt.get_attribute_by_id('attribute2').value, 2.2)
                self.assertEqual(self.rpt.get_attribute_by_id('attribute3').value, 'test_string')
		self.assertEqual(self.rpt.get_attribute_by_id('attribute1').name, 'Attribute 1')
                self.assertEqual(self.rpt.get_attribute_by_id('attribute1').id, 'attribute1')

        def test_column(self):
                self.assertEqual(self.rpt.get_table_by_id('table1').get_column_by_id('column1').values, [1,22,142])
                self.assertEqual(self.rpt.get_table_by_id('table2').get_column_by_id('column1').values, [1.0,2.1,3.37])
                self.assertEqual(self.rpt.get_table_by_id('table2').get_column_by_id('column2').values, ["string1","string2","string3"])
                self.assertEqual(self.rpt.get_table_by_id('table1').get_column_by_id('column1').header, 'Column 1')
                self.assertEqual(self.rpt.get_table_by_id('table1').get_column_by_id('column1').id, 'column1')
	def test_table(self):
                self.assertEqual(self.rpt.get_table_by_id('table1').title, 'Table 1')
                self.assertEqual(self.rpt.get_table_by_id('table1').id, 'table1')

        def test_plot(self):
                self.assertEqual(self.rpt.get_plotgroup_by_id('plotgroup1').get_plot_by_id('plot1').image, PLOT1_FILE)
                self.assertEqual(self.rpt.get_plotgroup_by_id('plotgroup1').get_plot_by_id('plot1').thumbnail, THUMBNAIL1_FILE)
                self.assertEqual(self.rpt.get_plotgroup_by_id('plotgroup1').get_plot_by_id('plot1').caption, 'Plot 1')

        def test_plotgroup(self):
                self.assertEqual(self.rpt.get_plotgroup_by_id('plotgroup1').thumbnail, THUMBNAIL2_FILE)
                self.assertEqual(self.rpt.get_plotgroup_by_id('plotgroup1').title, 'Plotgroup 1')
