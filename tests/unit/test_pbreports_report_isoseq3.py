import os
import logging
import shutil
import unittest
import tempfile

from pbcommand.models.report import Report
from pbcommand.pb_io.report import load_report_from_json
from pbcommand.testkit import PbTestApp

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


@skip_if_data_dir_not_present
class TestIsoSeq3Report(unittest.TestCase):

    TRANSCRIPTS = "/pbi/dept/secondary/siv/testdata/isoseqs/TranscriptSet/polished.transcriptset.xml"

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_make_report(self):
        r = isoseq3.make_report(self.TRANSCRIPTS, 0.98, self.tmp_dir)
        attr = {a.id:a.value for a in r.attributes}
        self.assertEqual(attr, {
            "num_polished_hq_isoforms": 11701,
            "num_polished_lq_isoforms": 44
        })
