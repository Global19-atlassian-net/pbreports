
import subprocess
import unittest
import tempfile
import os.path as op

from pbcore.util.Process import backticks
from pbcommand.models import DataStore

from pbreports.report import dataset_reports

from test_pbreports_report_control import get_control_subreadset

try:
    import pbtestdata
except ImportError:
    pbtestdata = None

skip_if_no_testdata = unittest.skipUnless(pbtestdata is not None, "Requires PacBioTestData")

class TestDataSetReports(unittest.TestCase):

    def setUp(self):
        self._output_dir = tempfile.mkdtemp(suffix="dataset-reports")

    @skip_if_no_testdata
    def test_sequel_subreads(self):
        data = pbtestdata.get_file("subreads-sequel")
        datastore = dataset_reports.to_reports(data, self._output_dir)
        self.assertEqual(len(datastore.files), 3)

    def test_integration(self):
        ds_out = op.join(self._output_dir, "datastore.json")
        args = ["python", "-m", "pbreports.report.dataset_reports",
                pbtestdata.get_file("subreads-sequel"), ds_out]
        o, c, m = backticks(" ".join(args))
        self.assertEqual(c, 0)
        self.assertTrue(op.exists(ds_out))
        datastore = DataStore.load_from_json(ds_out)
        self.assertEqual(len(datastore.files), 3)

    @unittest.skipUnless(op.exists("/pbi/dept/secondary/siv"),
                         "Requires local test data")
    def test_with_control(self):
        data = get_control_subreadset()
        datastore = dataset_reports.to_reports(data, self._output_dir)
        self.assertEqual(len(datastore.files), 4)
