import logging
import json
import unittest
import tempfile
import shutil
import os.path as op
import csv
import itertools

from pbreports.report.structural_variants import to_report
from base_test_case import LOCAL_DATA, validate_report_complete

log = logging.getLogger(__name__)

_DATA_DIR = op.join(LOCAL_DATA, 'structural_variants')

class TestStructuralVariantsRpt(unittest.TestCase):

    def setUp(self):
        self._output_dir = tempfile.mkdtemp(suffix="structural_variants")
        log.setLevel(logging.INFO)

    def tearDown(self):
        if op.exists(self._output_dir):
            shutil.rmtree(self._output_dir)


    def test_make_sv_report(self):

        table = op.join(_DATA_DIR, 'svann.json')
        plot = op.join(_DATA_DIR, 'svlengths.json')

        rpt = to_report(table, plot, self._output_dir)
        d = json.loads(rpt.to_json())

        self.assertEqual('Report structural_variants', d['title'])

        t = d['tables'][1]
        c0 = t['columns'][0]
        c1 = t['columns'][1]
        c2 = t['columns'][2]
        c3 = t['columns'][3]

        self.assertEqual('Count by Annotation', t['title'])

        self.assertEqual('', c0['header'])
        self.assertEqual('structural_variants.anno_table.annotation', c0['id'])
        self.assertEqual('Alu', c0['values'][0])
        self.assertEqual('Unannotated', c0['values'][1])
        self.assertEqual('Total', c0['values'][2])

        self.assertEqual('Insertions (total bp)', c1['header'])
        self.assertEqual('structural_variants.anno_table.insertions', c1['id'])
        self.assertEqual('1 (5)', c1['values'][0])
        self.assertEqual('2 (21)', c1['values'][1])
        self.assertEqual('3 (26)', c1['values'][2])

        self.assertEqual('Deletions (total bp)', c2['header'])
        self.assertEqual('structural_variants.anno_table.deletions', c2['id'])
        self.assertEqual('0 (0)', c2['values'][0])
        self.assertEqual('5 (9898)', c2['values'][1])   
        self.assertEqual('5 (9898)', c2['values'][2])

        self.assertEqual('Total Variants (total bp)', c3['header'])
        self.assertEqual('structural_variants.anno_table.total', c3['id'])
        self.assertEqual('1 (5)', c3['values'][0])
        self.assertEqual('7 (9919)', c3['values'][1])
        self.assertEqual('8 (9924)', c3['values'][2])


        t = d['tables'][0]
        c0 = t['columns'][0]
        c1 = t['columns'][1]
        c2 = t['columns'][2]
        c3 = t['columns'][3]
        c4 = t['columns'][4]
        c5 = t['columns'][5]

        self.assertEqual('Count by Sample', t['title'])

        self.assertEqual('', c0['header'])
        self.assertEqual('structural_variants.sample_table.sample', c0['id'])
        self.assertEqual('SAMPLE_1', c0['values'][0])
        self.assertEqual('SAMPLE_2', c0['values'][1])

        self.assertEqual('Insertions (total bp)', c1['header'])
        self.assertEqual('structural_variants.sample_table.insertions', c1['id'])
        self.assertEqual('2 (423)', c1['values'][0])
        self.assertEqual('2 (425)', c1['values'][1])

        self.assertEqual('Deletions (total bp)', c2['header'])
        self.assertEqual('structural_variants.sample_table.deletions', c2['id'])
        self.assertEqual('7 (17771)', c2['values'][0])
        self.assertEqual('7 (7771)', c2['values'][1])

        self.assertEqual('Homozygous Variants', c3['header'])
        self.assertEqual('structural_variants.sample_table.homozygous', c3['id'])
        self.assertEqual(3, c3['values'][0])
        self.assertEqual(3, c3['values'][1])

        self.assertEqual('Heterozygous Variants', c4['header'])
        self.assertEqual('structural_variants.sample_table.heterozygous', c4['id'])
        self.assertEqual(6, c4['values'][0])
        self.assertEqual(5, c4['values'][1])

        self.assertEqual('Total Variants (total bp)', c5['header'])
        self.assertEqual('structural_variants.sample_table.total', c5['id'])
        self.assertEqual('9 (18194)', c5['values'][0])
        self.assertEqual('10 (8196)', c5['values'][1])


        self.assertTrue(op.exists(op.join(self._output_dir, 'sv_plot.png')))
        self.assertTrue(op.exists(op.join(self._output_dir, 'sv_plot_thumb.png')))

        validate_report_complete(self, rpt)

    def test_make_sv_report_table_empty_plots(self):

        table = op.join(_DATA_DIR, 'svann.json')
        plot = op.join(_DATA_DIR, 'svlengths_empty.json')

        rpt = to_report(table, plot, self._output_dir)
        d = json.loads(rpt.to_json())

        self.assertTrue(op.exists(op.join(self._output_dir, 'sv_plot.png')))
        self.assertTrue(op.exists(op.join(self._output_dir, 'sv_plot_thumb.png')))

        validate_report_complete(self, rpt)

