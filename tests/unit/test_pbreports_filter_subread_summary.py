import os
import unittest
import logging
import tempfile

import numpy as np

from base_test_case import ROOT_DATA_DIR, run_backticks

from pbreports.util import bas_fofn_to_bas_files
from pbreports.report.filter_subread_summary import run

_DATA_DIR_NAME = 'filter_subread_summary'

log = logging.getLogger(__name__)


class TestFilterSubreadSummaryReport(unittest.TestCase):

    def setUp(self):
        name = "region.fofn"
        self.region_fofn = os.path.join(ROOT_DATA_DIR, _DATA_DIR_NAME, name)
        self.region_files = bas_fofn_to_bas_files(self.region_fofn)

    def test_basic(self):
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        t.close()
        output_csv = t.name
        state = run(self.region_files, output_csv)
        self.assertTrue(state)

        log.info("Loading csv resuls from {f}".format(f=output_csv))
        r = np.recfromcsv(output_csv)
        self.assertIsNotNone(r)

        nreads = 41883
        self.assertEqual(r.size, nreads)

        p = r[r['passedfilter'] == 1]
        nreads_passed_filter = 41010
        self.assertEqual(p.size, nreads_passed_filter)

        # Cleanup
        self.assertTrue(os.path.exists(output_csv))
        os.remove(output_csv)


class TestFilterSubreadSummaryIntegration(TestFilterSubreadSummaryReport):

    def test_basic(self):
        t = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        t.close()
        output_csv = t.name
        exe = "filter_subread_summary"
        cmd = "{e} --debug {r} -o {csv}".format(e=exe, r=self.region_fofn,
                                                csv=output_csv)

        rcode = run_backticks(cmd)
        self.assertEqual(0, rcode)

        # Cleanup
        self.assertTrue(os.path.exists(output_csv))
        os.remove(output_csv)
