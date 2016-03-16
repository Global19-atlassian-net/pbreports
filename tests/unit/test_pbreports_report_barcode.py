
import json
import os
import os.path as op
import logging
import tempfile
import unittest
from pprint import pformat

from pbcore.util.Process import backticks
from pbcore.io import SubreadSet, FastaWriter
import pbcommand.testkit

from pbreports.report.barcode import run_to_report, _to_tuple_list
from pbreports.util import bas_fofn_to_bas_files

from base_test_case import (_get_root_data_dir, skip_if_data_dir_not_present,
                            LOCAL_DATA)
ROOT_DATA_DIR = _get_root_data_dir()

log = logging.getLogger(__name__)

_DATA_DIR = op.join(ROOT_DATA_DIR, 'barcode')
LOCAL_DATA_DIR = op.join(LOCAL_DATA, "barcode")
# TODO need to make sure this is okay to push to GitHub
BAM_FILE = op.join(LOCAL_DATA_DIR, "barcoded.subreads.bam")


@unittest.skipUnless(op.isfile(BAM_FILE), "TODO")
class TestToolContract(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.barcode"
    INPUT_FILES = [
        tempfile.NamedTemporaryFile(suffix=".subreadset.xml").name,
        tempfile.NamedTemporaryFile(suffix=".fasta").name
    ]

    @classmethod
    def setUpClass(cls):
        super(TestToolContract, cls).setUpClass()
        ds = SubreadSet(cls.BAM_FILE, strict=True)
        ds.write(cls.INPUT_FILES[0])
        with FastaWriter(cls.INPUT_FILES[1]) as fa_out:
            for i in range(1010):
                fa_out.writeRecord("%04d_Forward" % i, "A" * 16)


@skip_if_data_dir_not_present
class TestBarcodeFunctions(unittest.TestCase):

    def test_basic(self):
        bas_h5_fofn = os.path.join(_DATA_DIR, 'ccs_01', 'reads_of_insert.fofn')
        barcode_h5_fofn = os.path.join(_DATA_DIR, 'ccs_01', 'barcode.fofn')
        bas_barcode_list = _to_tuple_list(bas_h5_fofn, barcode_h5_fofn)
        self.assertTrue(len(bas_barcode_list), 3)

    def test_missing_file_in_fofn(self):
        with self.assertRaises(IOError):
            bas_h5_fofn = os.path.join(
                _DATA_DIR, 'ccs_01', 'reads_of_insert_with_no_existent_file.fofn')
            bas_files = bas_fofn_to_bas_files(bas_h5_fofn)
            log.info(pformat(bas_files))

    def test_incompatible_fofn(self):
        with self.assertRaises(ValueError):
            bas_h5_fofn = os.path.join(
                _DATA_DIR, 'ccs_01', 'reads_of_insert.fofn')
            barcode_h5_fofn = os.path.join(
                _DATA_DIR, 'ccs_01', 'barcode_missing_movie.fofn')
            bas_barcode_list = _to_tuple_list(bas_h5_fofn, barcode_h5_fofn)
            log.info(pformat(bas_barcode_list))


@skip_if_data_dir_not_present
class TestBarcodeReportBasic(unittest.TestCase):

    def setUp(self):
        self.bas_h5_fofn = os.path.join(_DATA_DIR, 'bash5.fofn')
        self.barcode_h5_fofn = os.path.join(_DATA_DIR, 'barcodeh5.fofn')

    def test_basic(self):
        report = run_to_report(self.bas_h5_fofn, self.barcode_h5_fofn,
                               subreads=True)
        d = report.to_dict()
        self.assertIsNotNone(d)
        log.info(pformat(d))
        log.info(str(report.tables[0]))


@skip_if_data_dir_not_present
class TestBarcodeIntegration(unittest.TestCase):

    def setUp(self):
        self.bas_h5_fofn = os.path.join(_DATA_DIR, 'bash5.fofn')
        self.barcode_h5_fofn = os.path.join(_DATA_DIR, 'barcodeh5.fofn')
        self.ccs = False

    def test_integration(self):
        exe = "barcode_report"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        json_report_file_name = temp_file.name
        temp_file.close()
        ccs = " --ccs " if self.ccs else ""
        cmd = "{e} --debug {ccs} {b} {ba} {r}".format(e=exe,
                                                      b=self.bas_h5_fofn,
                                                      ba=self.barcode_h5_fofn,
                                                      r=json_report_file_name,
                                                      ccs=ccs)

        log.info("Running cmd {c}".format(c=cmd))
        output, rcode, emsg = backticks(cmd)

        if rcode != 0:
            log.error(output)
            log.error(emsg)

        self.assertEqual(0, rcode)

        with open(json_report_file_name, 'r') as f:
            s = json.load(f)

        self.assertIsNotNone(s)
        log.info(pformat(s))

        # cleanup
        os.remove(json_report_file_name)


@skip_if_data_dir_not_present
class TestReadsOfInsertBarcodeReportBasic(unittest.TestCase):

    def setUp(self):
        dir_name = os.path.join(_DATA_DIR, 'ccs_01')
        self.barcode_h5_fofn = os.path.join(dir_name, 'barcode.fofn')
        self.bas_h5_fofn = os.path.join(dir_name, 'reads_of_insert.fofn')
        self.ccs = True

    def test_basic(self):
        report = run_to_report(self.bas_h5_fofn, self.barcode_h5_fofn,
                               subreads=False)
        d = report.to_dict()
        self.assertIsNotNone(d)
        log.info(pformat(d))
        log.info(str(report.tables[0]))


@skip_if_data_dir_not_present
class TestReadsOfInsertBarcodeIntegration(TestBarcodeIntegration):

    def setUp(self):
        dir_name = os.path.join(_DATA_DIR, 'ccs_01')
        self.barcode_h5_fofn = os.path.join(dir_name, 'barcode.fofn')
        self.bas_h5_fofn = os.path.join(dir_name, 'reads_of_insert.fofn')
        self.ccs = True
