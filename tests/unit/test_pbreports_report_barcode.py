import json
import os
import logging
import tempfile
import unittest
from pprint import pformat
from pbcore.util.Process import backticks

from pbreports.report.barcode import run_to_report, _to_tuple_list
from pbreports.util import bas_fofn_to_bas_files

from base_test_case import _get_root_data_dir
ROOT_DATA_DIR = _get_root_data_dir()

log = logging.getLogger(__name__)

_DATA_DIR = os.path.join(ROOT_DATA_DIR, 'barcode')
if not os.path.exists(_DATA_DIR):
    raise IOError("Unable to find data directory {d}".format(d=_DATA_DIR))


class TestBarcodeFunctions(unittest.TestCase):

    def test_basic(self):
        bas_h5_fofn = os.path.join(_DATA_DIR, 'ccs_01', 'reads_of_insert.fofn')
        barcode_h5_fofn = os.path.join(_DATA_DIR, 'ccs_01', 'barcode.fofn')
        bas_barcode_list = _to_tuple_list(bas_h5_fofn, barcode_h5_fofn)
        self.assertTrue(len(bas_barcode_list), 3)

    def test_missing_file_in_fofn(self):
        with self.assertRaises(IOError):
            bas_h5_fofn = os.path.join(_DATA_DIR, 'ccs_01', 'reads_of_insert_with_no_existent_file.fofn')
            bas_files = bas_fofn_to_bas_files(bas_h5_fofn)
            log.info(pformat(bas_files))

    def test_incompatible_fofn(self):
        with self.assertRaises(ValueError):
            bas_h5_fofn = os.path.join(_DATA_DIR, 'ccs_01', 'reads_of_insert.fofn')
            barcode_h5_fofn = os.path.join(_DATA_DIR, 'ccs_01', 'barcode_missing_movie.fofn')
            bas_barcode_list = _to_tuple_list(bas_h5_fofn, barcode_h5_fofn)
            log.info(pformat(bas_barcode_list))


class TestBarcodeReportBasic(unittest.TestCase):

    def setUp(self):
        self.bas_h5_fofn = os.path.join(_DATA_DIR, 'bash5.fofn')
        self.barcode_h5_fofn = os.path.join(_DATA_DIR, 'barcodeh5.fofn')
        self.bas_barcode_list = _to_tuple_list(self.bas_h5_fofn, self.barcode_h5_fofn)

    def test_basic(self):
        use_subreads = True
        report = run_to_report(self.bas_barcode_list, subreads=use_subreads)
        d = report.to_dict()
        self.assertIsNotNone(d)
        log.info(pformat(d))
        log.info(str(report.tables[0]))


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


class TestReadsOfInsertBarcodeReportBasic(unittest.TestCase):

    def setUp(self):
        dir_name = os.path.join(_DATA_DIR, 'ccs_01')
        self.barcode_h5_fofn = os.path.join(dir_name, 'barcode.fofn')
        self.bas_h5_fofn = os.path.join(dir_name, 'reads_of_insert.fofn')
        self.ccs = True
        self.bas_barcode_list = _to_tuple_list(self.bas_h5_fofn, self.barcode_h5_fofn)

    def test_basic(self):
        use_subreads = False
        report = run_to_report(self.bas_barcode_list, subreads=use_subreads)
        d = report.to_dict()
        self.assertIsNotNone(d)
        log.info(pformat(d))
        log.info(str(report.tables[0]))


class TestReadsOfInsertBarcodeIntegration(TestBarcodeIntegration):

    def setUp(self):
        dir_name = os.path.join(_DATA_DIR, 'ccs_01')
        self.barcode_h5_fofn = os.path.join(dir_name, 'barcode.fofn')
        self.bas_h5_fofn = os.path.join(dir_name, 'reads_of_insert.fofn')
        self.ccs = True
        self.bas_barcode_list = _to_tuple_list(self.bas_h5_fofn, self.barcode_h5_fofn)
        log.info(pformat(self.bas_barcode_list))
