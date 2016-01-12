import os
import logging
import traceback
import json
import tempfile
import unittest
import shutil
import sys

from pbcore.util.Process import backticks

from pbreports.report.modifications import (make_modifications_report)
from pbreports.serializers import dict_to_report
from pbreports.model.model import PbReportError

from base_test_case import LOCAL_DATA

log = logging.getLogger(__name__)


class TestModificationsRpt(unittest.TestCase):

    def setUp(self):
        """
        Before *every* test
        """
        self._data_dir = os.path.join(LOCAL_DATA, 'modifications')
        self._output_dir = tempfile.mkdtemp(suffix="modifications")

    def tearDown(self):
        """
        After *every* test
        """
        if os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_make_modifications_report(self):
        """
        Create a report object, do assertions on its properties, then assert that it gets written
        """
        csv = os.path.join(self._data_dir, 'modifications.csv.gz')

        make_modifications_report(csv, 'rpt.json', self._output_dir, 60, False)

        # deserialize report

        log.info("Deserializing report {r}".format(
            r=os.path.join(self._output_dir, 'rpt.json')))
        s = None
        with open(os.path.join(self._output_dir, 'rpt.json'), 'r') as f:
            s = json.load(f)

        report = dict_to_report(s)

        self.assertEqual(1, len(report.plotGroups))
        self.assertEqual(2, len(report.plotGroups[0].plots))

        scatter = report.plotGroups[0].plots[0]
        histo = report.plotGroups[0].plots[1]

        self._assert_image_file(report.plotGroups[0].thumbnail)
        self._assert_image_file(scatter.image)
        self._assert_image_file(histo.image)

    def _assert_image_file(self, filename):
        # Should we add validation to model.report that forces the filename to
        # be relative?
        self.assertFalse(os.path.isabs(filename))
        self.assertTrue(
            os.path.exists(os.path.join(self._output_dir, filename)))

    def test_exit_code_0(self):
        """
        Like a cram test. Assert exits with 0.
        """

        csv = os.path.join(self._data_dir, 'modifications.csv.gz')
        cmd = 'pbreport modifications {o} {r} {c}'.format(o=self._output_dir,
                                                          r='rpt.json',
                                                          c=csv)

        o, c, m = backticks(cmd)
        log.info(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            sys.stderr.write(str(m) + "\n")

        self.assertEquals(0, c)
        self.assertTrue(
            os.path.exists(os.path.join(self._output_dir, 'rpt.json')))
