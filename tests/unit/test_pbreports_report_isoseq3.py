import os
import logging
import shutil
import unittest
import tempfile

from pbcommand.models.report import Report
from pbcommand.pb_io.report import load_report_from_json
from pbcommand.testkit import PbTestApp
from pbcore.io import TranscriptSet

from pbreports.report import isoseq3

from base_test_case import (LOCAL_DATA, run_backticks,
                            get_report_id_from_constants,
                            get_image_names_from_constants,
                            get_plot_groups_from_constants,
                            validate_report_complete,
                            ROOT_DATA_DIR, skip_if_data_dir_not_present)

log = logging.getLogger(__name__)

_DATA_DIR = os.path.join(LOCAL_DATA, 'isoseq')

# This will keep the report results and skip the teardown classmethod
_DEBUG = False

def _setup_transcripts(hq_file, lq_file, cutoff=0.98):
    TRANSCRIPTS = "/pbi/dept/secondary/siv/testdata/isoseqs/TranscriptSet/polished.transcriptset.xml"
    with TranscriptSet(TRANSCRIPTS, strict=True) as ds_in:
        ds_hq = ds_in.copy()
        ds_lq = ds_in.copy()
        ds_hq.filters.addFilter(rq=[(">=", cutoff)])
        ds_lq.filters.addFilter(rq=[("<", cutoff)])
        ds_hq.updateCounts()
        ds_lq.updateCounts()
        ds_hq.write(hq_file)
        ds_lq.write(lq_file)


@skip_if_data_dir_not_present
class TestIsoSeq3Report(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hq_file = tempfile.NamedTemporaryFile(suffix=".transcriptset.xml").name
        cls.lq_file = tempfile.NamedTemporaryFile(suffix=".transcriptset.xml").name
        _setup_transcripts(cls.hq_file, cls.lq_file)

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_make_report(self):
        r = isoseq3.make_report(self.hq_file, self.lq_file, self.tmp_dir)
        attr = {a.id:a.value for a in r.attributes}
        self.assertEqual(attr, {
            "num_polished_hq_isoforms": 11701,
            "num_polished_lq_isoforms": 44
        })


class TestIsoSeq3ToolContract(PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.isoseq3 "
    INPUT_FILES = [
        tempfile.NamedTemporaryFile(suffix=".transcriptset.xml").name,
        tempfile.NamedTemporaryFile(suffix=".transcriptset.xml").name
    ]

    @classmethod
    def setUpClass(cls):
        _setup_transcripts(cls.INPUT_FILES[0], cls.INPUT_FILES[1])
        super(TestIsoSeq3ToolContract, cls).setUpClass()

    def run_after(self, rtc, output_dir):
        r = load_report_from_json(rtc.task.output_files[0])
        attr = {a.id:a.value for a in r.attributes}
        self.assertEqual(attr, {
            "num_polished_hq_isoforms": 11701,
            "num_polished_lq_isoforms": 44
        })
