
from pprint import pformat
import tempfile
import unittest
import logging
import uuid
import json
import os.path as op
import os

from pbcore.util.Process import backticks
import pbcommand.testkit
from pbcommand.models import DataStore, DataStoreFile, FileTypes

import pbtestdata

from pbreports.report.barcode import *

from base_test_case import (validate_report_complete,
                            skip_if_data_dir_not_present)

log = logging.getLogger(__name__)


def _make_datastore(subreads):
    files = [
        DataStoreFile(uuid.uuid4(), "barcoding.tasks.lima-out-0",
                      FileTypes.DS_SUBREADS.file_type_id, subreads)
    ]
    ds = DataStore(files)
    ds_path = tempfile.NamedTemporaryFile(suffix=".datastore.json").name
    ds.write_json(ds_path)
    return ds_path


class TestBarcodeReport(unittest.TestCase):

    def setUp(self):
        self.barcodes = pbtestdata.get_file("barcodeset")
        self.subreads = pbtestdata.get_file("barcoded-subreadset")
        self._tmp_dir = tempfile.mkdtemp()
        self._start_dir = os.getcwd()
        os.chdir(self._tmp_dir)

    def tearDown(self):
        os.chdir(self._start_dir)

    def test_iter_reads_by_barcode(self):
        for input_file in [self.subreads, _make_datastore(self.subreads)]:
            table = sorted(list(iter_reads_by_barcode(input_file, self.barcodes)), lambda a,b: cmp(b.nbases, a.nbases))
            self.assertEqual([r.label for r in table],
                             ["Not Barcoded", "lbc1--lbc1", "lbc3--lbc3"])
            self.assertEqual([r.idx for r in table], ["None", "0--0", "2--2"])
            self.assertEqual([r.nbases for r in table], [9791, 1436, 204])
            self.assertEqual([r.n_subreads for r in table], [1,1,1])

    def _get_synthetic_read_info(self):
        return [ # totally synthetic data
            # label nbases qmax srl_max bq
            ReadInfo("bc1", 1000, 1140, 400, [0.5]*7, (0,0)),
            ReadInfo("bc1", 2000, 2400, 100, [0.8]*20, (0,0)),
            ReadInfo("bc2", 2000, 2380, 200, [0.9]*19, (1,1)),
            ReadInfo("bc2", 3000, 3560, 300, [0.6]*28, (1,1)),
            ReadInfo("bc3", 2500, 2720, 300, [0.7]*22, (2,2)),
            ReadInfo("Not Barcoded", 10000, 5000, 1000, [0]*90, (-1,-1))
        ]

    def test_read_info(self):
        read_info = self._get_synthetic_read_info()
        self.assertTrue(read_info[0].is_barcoded())
        self.assertFalse(read_info[-1].is_barcoded())
        self.assertEqual(read_info[0].n_subreads, 7)

    def test_make_report(self):
        read_info = self._get_synthetic_read_info()
        biosamples = {"bc1": "A", "bc2": "B", "bc3": "C", "Not Barcoded": "D"}
        report = make_report(biosamples, read_info)
        attr = {a.id:a.value for a in report.attributes}
        self.assertEqual(attr["mean_read_length"], 2440)
        self.assertEqual(attr["mean_longest_subread_length"], 333)
        self.assertEqual(attr["min_reads"], 1)
        self.assertEqual(attr["max_reads"], 2)
        self.assertEqual(attr["n_barcodes"], 3)
        self.assertEqual(attr["mean_reads"], 1)

    def test_make_2d_histogram(self):
        x = [1,1,1,1,1,2,2,2,2,2,2,2,2,2,3,3,3,3,3,3]
        y = [4,4,3,1,2,5,6,3,3,2,4,5,6,1,3,3,4,6,5,1]
        fig = make_2d_histogram(x, y, [3,6], "Imaginary read metric")
        fig.savefig("fake_hist2d.png", dpi=72)

    def _get_synthetic_bc_info(self):
        return [
            BarcodeGroup("bc2", 20, [5,6,3,3,2,4,5,6,1], [40,50,50,80,76,90,84,20,43]),
            BarcodeGroup("bc3", 10, [3,3,4,6,5,1], [40,50,60,70,55,39]),
            BarcodeGroup("bc1", 8, [4,4,3,1,2], [25,30,50,75,65]),
            BarcodeGroup("Not Barcoded", 30, [10,10,10], [0,0,0])
        ]

    def test_barcode_info(self):
        bc_groups = self._get_synthetic_bc_info()
        self.assertEqual(bc_groups[0].n_subreads, 9)
        self.assertEqual(bc_groups[0].n_reads, 9)
        self.assertEqual(bc_groups[0].mean_read_length(), 3)
        bc_group = BarcodeGroup("bc1")
        read_info = self._get_synthetic_read_info()
        bc_group.add_read(read_info[0])
        bc_group.add_read(read_info[1])
        self.assertEqual(bc_group.n_reads, 2)
        self.assertEqual(bc_group.n_subreads, 27)
        self.assertRaises(AssertionError,
                          lambda: bc_group.add_read(read_info[3]))

    def test_make_nreads_histogram(self):
        bc_groups = self._get_synthetic_bc_info()
        p = make_nreads_histogram(bc_groups, self._tmp_dir)
        self.assertTrue(op.isfile(p.image))

    def test_make_readlength_histogram(self):
        bc_groups = self._get_synthetic_bc_info()
        p = make_readlength_histogram(bc_groups, self._tmp_dir)
        self.assertTrue(op.isfile(p.image))

    def test_make_bcqual_histogram(self):
        bc_groups = self._get_synthetic_bc_info()
        p = make_bcqual_histogram(bc_groups, self._tmp_dir)
        self.assertTrue(op.isfile(p.image))

    def test_make_bq_qq_plot(self):
        try:
            import scipy.stats
        except ImportError:
            raise unittest.SkipTest("Can't import scipy")
        else:
            bc_groups = self._get_synthetic_bc_info()
            p = make_bq_qq_plot(bc_groups, self._tmp_dir)
            self.assertTrue(op.isfile(p.image))

    def test_make_nreads_line_plot(self):
        bc_groups = self._get_synthetic_bc_info()
        p = make_nreads_line_plot(bc_groups, self._tmp_dir)
        self.assertTrue(op.isfile(p.image))

    def test_make_readlength_hist2d(self):
        bc_groups = self._get_synthetic_bc_info()
        p = make_readlength_hist2d(bc_groups, self._tmp_dir)
        self.assertTrue(op.isfile(p.image))

    def test_make_bcqual_hist2d(self):
        bc_groups = self._get_synthetic_bc_info()
        p = make_bcqual_hist2d(bc_groups, self._tmp_dir)
        self.assertTrue(op.isfile(p.image))

    def test_make_plots(self):
        bc_groups = self._get_synthetic_bc_info()
        pgs = make_plots(bc_groups, self._tmp_dir)
        self.assertEqual(len(pgs), 3)
        for pg in pgs:
            for p in pg.plots:
                self.assertTrue(op.isfile(p.image))

    def test_make_report_no_reads(self):
        report = make_report({}, [])
        attr = {a.id:a.value for a in report.attributes}
        self.assertEqual(attr["n_barcodes"], 0)
        self.assertEqual(len(report.tables[0].columns[0].values), 0)

    def test_make_report_no_barcoded_reads(self):
        read_info = [
            ReadInfo("Not Barcoded", 10000, 5000, 1000, [0]*90, (-1,-1))
        ]
        biosamples = {"Not Barcoded": "A"}
        report = make_report(biosamples, read_info)
        attr = {a.id:a.value for a in report.attributes}
        self.assertEqual(attr["n_barcodes"], 0)
        self.assertEqual(len(report.tables[0].columns[0].values), 1)

    def test_run_to_report(self):
        report = run_to_report(self.subreads, self.barcodes)
        validate_report_complete(self, report)
        d = report.to_dict()
        self.assertIsNotNone(d)
        attr = {a.id:a.value for a in report.attributes}
        self.assertEqual(attr, {
            'mean_read_length': 5341,
            'mean_longest_subread_length': 820,
            'min_reads': 1,
            'mean_reads': 1,
            'n_barcodes': 2,
            'max_reads': 1
        })
        self.assertEqual(report.tables[0].columns[2].values, [
                         'lbc1--lbc1', 'lbc3--lbc3', 'Not Barcoded'])
        self.assertEqual(report.tables[0].columns[3].values, [1, 1, 1])
        self.assertEqual(report.tables[0].columns[4].values, [1, 1, 1])
        self.assertEqual(report.tables[0].columns[5].values, [1436, 204, 9791])
        self.assertEqual(report.tables[0].columns[-2].values, [1, 2, None])

    @skip_if_data_dir_not_present
    def test_large_dataset(self):
        SUBREADS = "/pbi/dept/secondary/siv/testdata/SA3-Sequel/phi29/315/3150101/r54008_20160219_002905/1_A01_tiny_barcoded/m54008_160219_003234.tiny.subreadset.xml"
        BARCODES = "/pbi/dept/secondary/siv/barcodes/Sequel_RSII_384_barcodes_v1/Sequel_RSII_384_barcodes_v1.barcodeset.xml"
        report = run_to_report(SUBREADS, BARCODES)
        validate_report_complete(self, report)
        d = report.to_dict()
        self.assertIsNotNone(d)
        attr = {a.id:a.value for a in report.attributes}
        self.assertEqual(attr, {
            'mean_read_length': 14411,
            'mean_longest_subread_length': 28314,
            'min_reads': 989,
            'mean_reads': 1065,
            'n_barcodes': 3,
            'max_reads': 1116
        })
        self.assertEqual(report.tables[0].columns[1].values,
                         ["0--0", "1--1", "2--2"])
        self.assertEqual(report.tables[0].columns[2].values,
                         ['bc1001--bc1001', 'bc1002--bc1002', 'bc1003--bc1003'])
        self.assertEqual(report.tables[0].columns[3].values, [1091, 1116, 989])
        self.assertEqual(report.tables[0].columns[4].values, [5370, 5053, 4710])
        self.assertEqual(report.tables[0].columns[5].values, [10306688, 10034254, 9452616])

    def test_integration(self):
        exe = "barcode_report"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        json_report_file_name = temp_file.name
        temp_file.close()
        cmd = "{e} --debug {b} {ba} {r}".format(e=exe,
                                                b=self.subreads,
                                                ba=self.barcodes,
                                                r=json_report_file_name)
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


class TestToolContract(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.barcode"
    INPUT_FILES = [_make_datastore(pbtestdata.get_file("barcoded-subreadset")),
                   pbtestdata.get_file("barcodeset")]
