import os
import logging
import traceback
import json
import unittest
import tempfile
import shutil
import numpy as np
import os.path as op

from pbcore.util.Process import backticks
from pbcore.io import SubreadSet

from pbreports.report.control import to_report
from base_test_case import validate_report_complete, skip_if_data_dir_not_present

log = logging.getLogger(__name__)


def get_control_subreadset():
    ss = ('/pbi/dept/secondary/siv/testdata/SA3-Sequel/lambda/'
           '314/3140099/r54099_20160830_222805/3_C01_control/'
            'm54099_160831_134818.subreadset.xml')
    return ss


class TestControlRpt(unittest.TestCase):

    def setUp(self):
        self._output_dir = tempfile.mkdtemp(suffix="control")
        log.setLevel(logging.INFO)

    def tearDown(self):
        if op.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    @skip_if_data_dir_not_present
    def test_make_control_report(self):
              
        ss = get_control_subreadset()

        rpt = to_report(ss, self._output_dir)
        d = json.loads(rpt.to_json())

        self.assertEqual(10760, d['attributes'][0]['value'])
        self.assertEqual(9554, np.floor(d['attributes'][1]['value']))
        self.assertAlmostEqual(0.819919, d['attributes'][2]['value'], delta=.0003)
 
        self.assertTrue(os.path.exists(os.path.join(self._output_dir,
            'concordance_plot.png')))
        self.assertTrue(os.path.exists(os.path.join(self._output_dir,
            'concordance_plot_thumb.png')))
        self.assertTrue(os.path.exists(os.path.join(self._output_dir,
            'readlength_plot.png')))
        self.assertTrue(os.path.exists(os.path.join(self._output_dir,
            'readlength_plot_thumb.png')))
        validate_report_complete(self, rpt)
