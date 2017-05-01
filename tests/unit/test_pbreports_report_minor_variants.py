import logging
import json
import unittest
import tempfile
import shutil
import os.path as op
import csv
import itertools

from pbreports.report.minor_variants import to_report
from base_test_case import LOCAL_DATA, validate_report_complete

log = logging.getLogger(__name__)

_DATA_DIR = op.join(LOCAL_DATA, 'minor_variants')


def make_table_from_csv(csvpath):
    table_tr = []
    with open(csvpath, 'rb') as csvfile:
        t = csv.reader(csvfile)
        for row in t:
            table_tr.append(row)
    table = zip(*table_tr)
    return table

def stringify(a):
    if type(a) is float:
        return repr(a)
    else:
        return str(a)

class TestMinorVariantsRpt(unittest.TestCase):

    def setUp(self):
        self._output_dir = tempfile.mkdtemp(suffix="minor_variants")
        log.setLevel(logging.INFO)

    def tearDown(self):
        if op.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_make_mv_supplementary_table(self):

        juliet_summary = op.join(_DATA_DIR, 'mix.json')
        rpt = to_report(juliet_summary, self._output_dir)
        var_csv = 'variant_summary.csv'

        self.assertTrue(op.exists(op.join(self._output_dir, var_csv)))

        ref_supp_csv = op.join(_DATA_DIR, var_csv)
        test_supp_csv = op.join(self._output_dir, var_csv)

        ref_supp_table = make_table_from_csv(ref_supp_csv)
        test_supp_table = make_table_from_csv(test_supp_csv)        

        exact_cols = [0, 1, 2, 3, 5, 6, 7, 8]
        approx_cols = [4, 9]
 
        for col in exact_cols:
            self.assertEqual(ref_supp_table[col], test_supp_table[col])

        for col in approx_cols:
            self.assertEqual(ref_supp_table[col][0], test_supp_table[col][0])
            ref_supp_table_col = [float(a) for a in itertools.chain(*[item.split(";") for item in ref_supp_table[col][1:]])]
            test_supp_table_col = [float(a) for a in itertools.chain(*[item.split(";") for item in test_supp_table[col][1:]])]
            self.assertEqual(len(ref_supp_table_col), len(test_supp_table_col)) 
            for item in zip(ref_supp_table_col, test_supp_table_col):
                self.assertAlmostEqual(item[0], item[1], delta=.0003)


    def test_make_mv_variant_table(self):
        juliet_summary = op.join(_DATA_DIR, 'mix.json')
        rpt = to_report(juliet_summary, self._output_dir)
        var_csv = 'variant_summary.csv'

        self.assertTrue(op.exists(op.join(self._output_dir, var_csv)))

        test_supp_csv = op.join(self._output_dir, var_csv)
        test_supp_table = make_table_from_csv(test_supp_csv)
        rpt_var_table = json.loads(rpt.to_json())['tables'][1]
        
        test_supp_col_formatted = []
        for item in test_supp_table[9][1:]:
                s = item.split(";")
                vals = ["{0:.2f}".format(round(float(x),2)) for x in s]
                val_string = ";".join(vals)
                test_supp_col_formatted.append(val_string)

        test_supp_table[9] = [test_supp_table[9][0], test_supp_col_formatted]

        for col in xrange(9):
            rpt_var_col = [str(rpt_var_table['columns'][col]['header'])]
            rpt_var_col.extend(stringify(v) for v in rpt_var_table['columns'][col]['values'])
            self.assertEqual(list(test_supp_table[col]), rpt_var_col)


    def test_make_mv_sample_table(self):

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
        self.assertAlmostEqual(4.25456790123457, c6['values'][0], delta=.0003)
        self.assertAlmostEqual(95.8553791887125, c6['values'][1], delta=.0003)

        validate_report_complete(self, rpt)
