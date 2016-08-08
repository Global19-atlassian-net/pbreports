
import json
import os
import os.path as op
import shutil
import logging
import tempfile
import unittest
import pprint
import functools

from pbcommand.models.report import Report
import pbcommand.testkit
from pbcommand.pb_io.report import load_report_from_json
from pbcore.io import ConsensusReadSet

import pbtestdata

from pbreports.report.ccs import to_report, Constants
from base_test_case import run_backticks, LOCAL_DATA, \
                           validate_report_complete

log = logging.getLogger(__name__)


def __get_from_constant(prefix_str, c):
    names = [i for i in dir(c) if i.startswith(prefix_str)]
    return [getattr(Constants, n) for n in names]


_get_attribute_names = functools.partial(__get_from_constant, 'A_')
_get_image_names = functools.partial(__get_from_constant, 'I_')

EXPECTED_VALUES = {
    Constants.A_TOTAL_BASES: 85803,
    Constants.A_NREADS: 18,
    Constants.A_MEAN_READLENGTH: 4766,
    Constants.A_MEAN_ACCURACY: 0.947,
    Constants.A_MEAN_NPASSES: 4,
    #Constants.A_MEAN_QV: 13
}


class TestCCSCommand(unittest.TestCase):
    XML_FILE = pbtestdata.get_file("rsii-ccs")
    BAM_FILE = pbtestdata.get_file("ccs-bam")

    @classmethod
    def setUpClass(cls):
        cls.ccs_set = ConsensusReadSet(cls.XML_FILE, strict=True)

    def test_basic(self):
        """Basic smoke test"""
        output_dir = tempfile.mkdtemp()
        report = to_report(self.ccs_set, output_dir)
        validate_report_complete(self, report)
        d = report.to_dict()
        self.assertIsNotNone(d)

    def test_integration_bam(self):
        """Run cmdline tool with .bam input"""
        self._run_cmd(self.BAM_FILE)

    def test_integration_ds(self):
        """Run cmdline tool with .xml input"""
        self._run_cmd(self.XML_FILE)

    def _run_cmd(self, file_name):
        """Run an subprocess of the command and verify that report is present"""
        exe = "ccs_report"
        output_dir = tempfile.mkdtemp()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        json_report_file_name = temp_file.name
        temp_file.close()
        cmd = "{e} --debug --output-dir {o} {i} {r}".format(
            e=exe,
            i=file_name,
            r=json_report_file_name,
            o=output_dir)
        rcode = run_backticks(cmd)
        self.assertEqual(0, rcode)
        with open(json_report_file_name, 'r') as f:
            s = json.load(f)
            log.info("JsonReport: ")
            log.info(pprint.pformat(s, indent=4))
        self.assertIsNotNone(s)
        # cleanup
        os.remove(json_report_file_name)


class TestCCSMetrics(unittest.TestCase):
    XML_FILE = pbtestdata.get_file("rsii-ccs")

    @classmethod
    def setUpClass(cls):
        cls.output_dir = tempfile.mkdtemp()
        cls.ccs_set = ConsensusReadSet(cls.XML_FILE)
        cls.report = to_report(cls.ccs_set, cls.output_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.output_dir)

    def _get_attribute_value_by_id(self, i):
        """helper method to grab value from the report instance"""
        a = self.report.get_attribute_by_id(i)
        if a is None:
            raise KeyError(
                "Unable to find attribute id '{i}' in report".format(i=i))
        else:
            return a.value

    def test_basic(self):
        self.assertTrue(isinstance(self.report, Report))
        log.info(pprint.pformat(self.report.to_dict()))
        self.assertEqual(len(self.report.tables), 1)
        log.info(str(self.report.tables[0]))

    def test_smoke_attributes(self):
        attr_ids = _get_attribute_names(Constants)
        for attr_id in attr_ids:
            a = self.report.get_attribute_by_id(attr_id)
            self.assertIsNotNone(a)

    def test_images(self):
        image_names = _get_image_names(Constants)
        for image_name in image_names:
            p = os.path.join(self.output_dir, image_name)
            if not os.path.exists(p):
                log.error("Unable fot find image {p}".format(p=p))
            self.assertTrue(os.path.exists(p))

    def _compare_metric_values(self, metric_id):
        value = EXPECTED_VALUES[metric_id]
        self.assertEqual(self._get_attribute_value_by_id(metric_id), value)

    def test_total_number_of_ccs_bases(self):
        self._compare_metric_values(Constants.A_TOTAL_BASES)

    def test_number_of_ccs_reads(self):
        self._compare_metric_values(Constants.A_NREADS)

    def test_mean_ccs_readlength(self):
        self._compare_metric_values(Constants.A_MEAN_READLENGTH)

    def test_mean_accuracy(self):
        value = EXPECTED_VALUES[Constants.A_MEAN_ACCURACY]
        actual = self._get_attribute_value_by_id(Constants.A_MEAN_ACCURACY)
        self.assertEqual('%.3f' % value, '%.3f' % actual)

    #def test_mean_qv(self):
    #    self._compare_metric_values(Constants.A_MEAN_QV)

    def test_mean_ccs_num_passes(self):
        self._compare_metric_values(Constants.A_MEAN_NPASSES)


class TestToolContract(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.ccs"
    INPUT_FILES = [pbtestdata.get_file("rsii-ccs")]

    def run_after(self, rtc, output_dir):
        report = load_report_from_json(rtc.task.output_files[0])
        attr = {a.id: a.value for a in report.attributes}
        self.assertEqual(attr[Constants.A_NREADS],
                         EXPECTED_VALUES[Constants.A_NREADS])


class TestCCSMultipleMovies(unittest.TestCase):
    CCS_BAM = pbtestdata.get_file("rsii-ccs-multi-cell")

    def test_ccs_mulitple_movies_single_bam(self):
        """
        Check that the report doesn't crash when a single BAM file contains
        reads from multiple movies
        """
        ds = ConsensusReadSet(self.CCS_BAM)
        r = to_report(ds, tempfile.mkdtemp())


class TestCCSBarcoded(unittest.TestCase):
    CCS_DS = pbtestdata.get_file("ccs-barcoded")

    def test_ccs_barcodes_table(self):
        ds = ConsensusReadSet(self.CCS_DS)
        r = to_report(ds, tempfile.mkdtemp())
        self.assertEqual([c.values for c in r.tables[1].columns[0:4]],
                         [["lbc1", "lbc3"], [1,1], [1958,1954], [1958,1954]])
        self.assertAlmostEqual(r.tables[1].columns[4].values[0], 0.9724,
                               places=4)
        self.assertAlmostEqual(r.tables[1].columns[4].values[1], 0.9926,
                               places=4)
