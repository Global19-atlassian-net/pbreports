
from pprint import pformat
import tempfile
import unittest
import logging
import json
import os

from pbcore.util.Process import backticks
import pbcommand.testkit

import pbtestdata

from pbreports.report.barcode import run_to_report

from base_test_case import validate_report_complete

log = logging.getLogger(__name__)


class TestToolContract(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.barcode"
    INPUT_FILES = [pbtestdata.get_file("barcoded-subreadset"),
                   pbtestdata.get_file("barcodeset")]


class TestBarcodeReportBasic(unittest.TestCase):

    def setUp(self):
        self.barcodes = pbtestdata.get_file("barcodeset")
        self.subreads = pbtestdata.get_file("barcoded-subreadset")

    def test_basic(self):
        report = run_to_report(self.subreads, self.barcodes, subreads=True)
        validate_report_complete(self, report)
        d = report.to_dict()
        self.assertIsNotNone(d)
        self.assertEqual(report.tables[0].columns[0].values, ['lbc1--lbc1', 'lbc3--lbc3'])
        self.assertEqual(report.tables[0].columns[1].values, [1, 1])
        self.assertEqual(report.tables[0].columns[2].values, [1436, 204])


class TestBarcodeIntegration(unittest.TestCase):

    def setUp(self):
        self.barcodes = pbtestdata.get_file("barcodeset")
        self.subreads = pbtestdata.get_file("barcoded-subreadset")
        self.ccs = False

    def test_integration(self):
        exe = "barcode_report"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        json_report_file_name = temp_file.name
        temp_file.close()
        ccs = " --ccs " if self.ccs else ""
        cmd = "{e} --debug {ccs} {b} {ba} {r}".format(e=exe,
                                                      b=self.subreads,
                                                      ba=self.barcodes,
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


@unittest.skip("TODO")
class TestReadsOfInsertBarcodeReportBasic(unittest.TestCase):

    def setUp(self):
        dir_name = os.path.join(_DATA_DIR, 'ccs_01')
        self.barcodes = os.path.join(dir_name, 'barcode.fofn')
        self.subreads = os.path.join(dir_name, 'reads_of_insert.fofn')
        self.ccs = True

    def test_basic(self):
        report = run_to_report(self.subreads, self.barcodes,
                               subreads=False)
        d = report.to_dict()
        self.assertIsNotNone(d)
        log.info(pformat(d))
        log.info(str(report.tables[0]))


@unittest.skip("TODO")
class TestReadsOfInsertBarcodeIntegration(TestBarcodeIntegration):

    def setUp(self):
        dir_name = os.path.join(_DATA_DIR, 'ccs_01')
        self.barcodes = os.path.join(dir_name, 'barcode.fofn')
        self.subreads = os.path.join(dir_name, 'reads_of_insert.fofn')
        self.ccs = True
