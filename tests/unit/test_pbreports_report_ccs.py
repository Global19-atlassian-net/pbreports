import json
import os
import logging
import tempfile
import unittest
import pprint
import functools

import pbcommand.testkit
from pbcore.io import ConsensusReadSet

from pbreports.model.model import Report
from pbreports.report.ccs import to_report, Constants
from base_test_case import run_backticks, _get_root_data_dir

ROOT_DATA_DIR = _get_root_data_dir()

log = logging.getLogger(__name__)

_DATA_DIR = os.path.join(ROOT_DATA_DIR, 'reads_of_insert')
if not os.path.exists(_DATA_DIR):
    raise IOError("Unable to find data directory {d}".format(d=_DATA_DIR))


def __get_from_constant(prefix_str, c):
    names = [i for i in dir(c) if i.startswith(prefix_str)]
    return [getattr(Constants, n) for n in names]


_get_attribute_names = functools.partial(__get_from_constant, 'A_')
_get_image_names = functools.partial(__get_from_constant, 'I_')


class TestCCSBasic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # One ccs.h5 file generated from bax files
        cls.bam_file_name = os.path.join(_DATA_DIR, "file.ccsread.bam")
        cls.xml_file_name = os.path.join(_DATA_DIR, "ccs.ccsreadset.xml")
        if not os.path.exists(cls.xml_file_name):
            msg = "Unable to file {f}".format(f=cls.xml_file_name)
            log.error(msg)
            print msg
        cls.ccs_set = ConsensusReadSet(cls.xml_file_name)

    def test_basic(self):
        """Basic smoke test"""
        output_dir = tempfile.mkdtemp()
        report = to_report(self.ccs_set, output_dir)
        d = report.to_dict()
        self.assertIsNotNone(d)

    def test_bam(self):
        """Test .bam input"""
        expected_values = {
            "ccs.ccs_table.number_of_ccs_reads": [4],
            "ccs.ccs_table.total_number_of_ccs_bases": [3340],
            "ccs.ccs_table.mean_ccs_readlength": [835],
            "ccs.ccs_table.mean_accuracy": [994],
            "ccs.ccs_table.mean_ccs_num_passes": [11],
        }
        output_dir = tempfile.mkdtemp()
        bam_file = os.path.join(_DATA_DIR, "file.ccsread.bam")
        ccs_set = ConsensusReadSet(bam_file)
        report = to_report(ccs_set, output_dir)
        print output_dir
        d = report.to_dict()

    def test_integration_bam(self):
        """Run cmdline tool with .bam input"""
        self._run_cmd(self.bam_file_name)

    def test_integration_ds(self):
        """Run cmdline tool with .xml input"""
        self._run_cmd(self.xml_file_name)

    def _run_cmd(self, file_name):
        """Run an subprocess of the command and verify that report is present"""
        exe = "ccs_report"
        output_dir = tempfile.mkdtemp()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        json_report_file_name = temp_file.name
        temp_file.close()

        cmd = "{e} --debug --output-dir {o} {i} {r}".format(e=exe,
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


class TestCCS(unittest.TestCase):
    EXPECTED_VALUES = {
        Constants.A_TOTAL_BASES: 3340,
        Constants.A_NREADS: 4,
        Constants.A_MEAN_READLENGTH: 835,
        Constants.A_MEAN_ACCURACY: 994,
        Constants.A_MEAN_NPASSES: 11,
    }

    @classmethod
    def setUpClass(cls):
        cls.bam_file_name = os.path.join(_DATA_DIR, "file.ccsread.bam")
        cls.xml_file_name = os.path.join(_DATA_DIR, "ccs.ccsreadset.xml")
        if not os.path.exists(cls.xml_file_name):
            msg = "Unable to file {f}".format(f=cls.xml_file_name)
            log.error(msg)
            print msg
        output_dir = tempfile.mkdtemp()
        cls.ccs_set = ConsensusReadSet(cls.xml_file_name)
        cls.report = to_report(cls.ccs_set, output_dir)
        cls.output_dir = output_dir

    def _get_attribute_value_by_id(self, i):
        """helper method to grab value from the report instance"""
        a = self.report.get_attribute_by_id(i)
        if a is None:
            raise KeyError(
                "Unable to find attribute id '{i}' in report".format(i=i))
        else:
            return a.value

    def test_basic(self):
        """Generate report instance from 3 ccs.h5 files"""
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
        value = self.EXPECTED_VALUES[metric_id]
        self.assertEqual(self._get_attribute_value_by_id(metric_id), value)

    def test_total_number_of_ccs_bases(self):
        self._compare_metric_values(Constants.A_TOTAL_BASES)

    def test_number_of_ccs_reads(self):
        self._compare_metric_values(Constants.A_NREADS)

    def test_mean_ccs_readlength(self):
        self._compare_metric_values(Constants.A_MEAN_READLENGTH)

    def test_mean_accuracy(self):
        self._compare_metric_values(Constants.A_MEAN_ACCURACY)

    def test_mean_ccs_num_passes(self):
        self._compare_metric_values(Constants.A_MEAN_NPASSES)


class TestToolContract(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.ccs"
    INPUT_FILES = [os.path.join(_DATA_DIR, "ccs.ccsreadset.xml")]
