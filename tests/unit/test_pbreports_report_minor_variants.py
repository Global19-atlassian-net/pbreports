import logging
import json
import unittest
import tempfile
import shutil
import os.path as op

import numpy

from pbreports.report.minor_variants import to_report
from base_test_case import LOCAL_DATA, validate_report_complete

log = logging.getLogger(__name__)

_DATA_DIR = op.join(LOCAL_DATA, 'minor_variants')

class TestMinorVariantsRpt(unittest.TestCase):

    def setUp(self):
        self._output_dir = tempfile.mkdtemp(suffix="minor_variants")
        log.setLevel(logging.INFO)

    def tearDown(self):
        if op.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_make_control_report(self):

        juliet_summary = op.join(_DATA_DIR, 'mix.json')

        rpt = to_report(juliet_summary, self._output_dir)
        d = json.loads(rpt.to_json())

        t = d['tables'][0]
        c0 = t['columns'][0]
        c1 = t['columns'][1]
        c2 = t['columns'][2]
        c3 = t['columns'][3]
        c4 = t['columns'][4]
        c5 = t['columns'][5]
        c6 = t['columns'][6]

        self.assertEqual('Barcode Name', c0['header'])
        self.assertEqual('minor_variants.sample_table.barcode', c0['id'])
        self.assertEqual('1--1', c0['values'][0])
        self.assertEqual('0--0', c0['values'][1])

        self.assertEqual('Median Coverage', c1['header'])
        self.assertEqual('minor_variants.sample_table.coverage', c1['id'])
        self.assertEqual(2911, c1['values'][0])
        self.assertEqual(2877, c1['values'][1])

        self.assertEqual('Number of Variants', c2['header'])
        self.assertEqual('minor_variants.sample_table.variants', c2['id'])
        self.assertEqual(4, c2['values'][0])
        self.assertEqual(5, c2['values'][1])

        self.assertEqual('Number of Genes', c3['header'])
        self.assertEqual('minor_variants.sample_table.genes', c3['id'])
        self.assertEqual(1, c3['values'][0])
        self.assertEqual(1, c3['values'][1])

        self.assertEqual('Number of DRMs', c4['header'])
        self.assertEqual('minor_variants.sample_table.drms', c4['id'])
        self.assertEqual(7, c4['values'][0])
        self.assertEqual(4, c4['values'][1])   

        self.assertEqual('Number of Haplotypes', c5['header'])
        self.assertEqual('minor_variants.sample_table.haplotypes', c5['id'])
        self.assertEqual(4, c5['values'][0])
        self.assertEqual(5, c5['values'][1])

        self.assertEqual('Maximum Frequency Haplotype (%)', c6['header'])
        self.assertEqual('minor_variants.sample_table.haplotype_frequency', c6['id'])
        self.assertAlmostEqual(0.0425456790123457, c6['values'][0], delta=.0003)
        self.assertAlmostEqual(0.958553791887125, c6['values'][1], delta=.0003)

        self.assertTrue(op.exists(op.join(self._output_dir,
                                                    'variant_summary.csv')))

        validate_report_complete(self, rpt)
