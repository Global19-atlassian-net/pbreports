
from pprint import pformat
import tempfile
import unittest
import logging
import json
import os
import os.path as op
import re

import pysam

from pbcore.util.Process import backticks
from pbcore.io import BarcodeSet, SubreadSet, FastaWriter
import pbcommand.testkit

from pbreports.report.barcode import run_to_report

from base_test_case import LOCAL_DATA

log = logging.getLogger(__name__)

LOCAL_DATA_DIR = op.join(LOCAL_DATA, "barcode")
# TODO need to make sure this is okay to push to GitHub
BAM_FILE = op.join(LOCAL_DATA_DIR, "barcoded.subreads.bam")


def _make_dataset(file_name=None):
    if file_name is None:
        file_name = tempfile.NamedTemporaryFile(suffix=".subreadset.xml").name
    ds = SubreadSet(BAM_FILE, strict=True)
    ds.write(file_name)
    return file_name


def _make_barcodes(file_name=None):
    if file_name is None:
        file_name = tempfile.NamedTemporaryFile(suffix=".barcodeset.xml").name
    fasta_file_name = file_name
    if file_name.endswith(".barcodeset.xml"):
        fasta_file_name = re.sub(".barcodeset.xml", ".fasta", file_name)
    with FastaWriter(fasta_file_name) as fa_out:
        for i in range(1010):
            fa_out.writeRecord("%04d_Forward" % i, "A" * 16)
    pysam.faidx(fasta_file_name)
    ds = BarcodeSet(fasta_file_name, strict=True)
    ds.write(file_name)
    return file_name


class TestToolContract(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.barcode"
    INPUT_FILES = [
        tempfile.NamedTemporaryFile(suffix=".subreadset.xml").name,
        tempfile.NamedTemporaryFile(suffix=".fasta").name
    ]

    @classmethod
    def setUpClass(cls):
        super(TestToolContract, cls).setUpClass()
        _make_dataset(cls.INPUT_FILES[0])
        _make_barcodes(cls.INPUT_FILES[1])


class TestBarcodeReportBasic(unittest.TestCase):

    def setUp(self):
        self.subreads = _make_dataset()
        self.barcodes = _make_barcodes()

    def test_basic(self):
        report = run_to_report(self.subreads, self.barcodes, subreads=True)
        d = report.to_dict()
        self.assertIsNotNone(d)
        log.info(pformat(d))
        log.info(str(report.tables[0]))


class TestBarcodeIntegration(unittest.TestCase):

    def setUp(self):
        self.subreads = _make_dataset()
        self.barcodes = _make_barcodes()
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
