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


    def test_make_sv_report_table(self):

        table = op.join(_DATA_DIR, 'svann.json')
        plot = op.join(_DATA_DIR, 'svlengths.json')

        rpt = to_report(table, plot, self._output_dir)
        d = json.loads(rpt.to_json())

        t = d['tables'][0]
        c0 = t['columns'][0]
        c1 = t['columns'][1]
        c2 = t['columns'][2]
        c3 = t['columns'][3]
        c4 = t['columns'][4]
        c5 = t['columns'][5]
        c6 = t['columns'][6]

        self.assertEqual("", c0['header'])
        self.assertEqual('structural_variants.anno_table.annotation', c0['id'])
        self.assertEqual('Alu', c0['values'][0])
        self.assertEqual('Unannotated', c0['values'][1])
        self.assertEqual('Total', c0['values'][2])

        self.assertEqual('Insertions (count)', c1['header'])
        self.assertEqual('structural_variants.anno_table.insertions_n', c1['id'])
        self.assertEqual(1, c1['values'][0])
        self.assertEqual(2, c1['values'][1])
        self.assertEqual(3, c1['values'][2])

        self.assertEqual('Insertions (total bp)', c2['header'])
        self.assertEqual('structural_variants.anno_table.insertions_sum', c2['id'])
        self.assertEqual(5, c2['values'][0])
        self.assertEqual(21, c2['values'][1])
        self.assertEqual(26, c2['values'][2])

        self.assertEqual('Deletions (count)', c3['header'])
        self.assertEqual('structural_variants.anno_table.deletions_n', c3['id'])
        self.assertEqual(0, c3['values'][0])
        self.assertEqual(5, c3['values'][1])
        self.assertEqual(5, c3['values'][2])

        self.assertEqual('Deletions (total bp)', c4['header'])
        self.assertEqual('structural_variants.anno_table.deletions_sum', c4['id'])
        self.assertEqual(0, c4['values'][0])
        self.assertEqual(9898, c4['values'][1])   
        self.assertEqual(9898, c4['values'][2])

        self.assertEqual('All Variants (count)', c5['header'])
        self.assertEqual('structural_variants.anno_table.indel_n', c5['id'])
        self.assertEqual(1, c5['values'][0])
        self.assertEqual(7, c5['values'][1])
        self.assertEqual(8, c5['values'][2])

        self.assertEqual('All Variants (total bp)', c6['header'])
        self.assertEqual('structural_variants.anno_table.indel_sum', c6['id'])
        self.assertEqual(5, c6['values'][0])
        self.assertEqual(9919, c6['values'][1])
        self.assertEqual(9924, c6['values'][2])

        self.assertTrue(op.exists(op.join(self._output_dir, 'short_sv_plot.png')))
        self.assertTrue(op.exists(op.join(self._output_dir, 'short_sv_plot_thumb.png')))
        self.assertTrue(op.exists(op.join(self._output_dir, 'long_sv_plot.png')))
        self.assertTrue(op.exists(op.join(self._output_dir, 'long_sv_plot_thumb.png')))

        validate_report_complete(self, rpt)

    def test_make_sv_report_table_empty_plots(self):

        table = op.join(_DATA_DIR, 'svann.json')
        plot = op.join(_DATA_DIR, 'svlengths_empty.json')

        rpt = to_report(table, plot, self._output_dir)
        d = json.loads(rpt.to_json())

        self.assertTrue(op.exists(op.join(self._output_dir, 'short_sv_plot.png')))
        self.assertTrue(op.exists(op.join(self._output_dir, 'short_sv_plot_thumb.png')))
        self.assertTrue(op.exists(op.join(self._output_dir, 'long_sv_plot.png')))
        self.assertTrue(op.exists(op.join(self._output_dir, 'long_sv_plot_thumb.png')))

        validate_report_complete(self, rpt)

