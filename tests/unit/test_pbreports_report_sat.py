
from cStringIO import StringIO
import tempfile
import os
import logging
import traceback
import json
import tempfile
import unittest
import shutil

from pbcommand.models.report import PbReportError
import pbcommand.testkit
from pbcommand.pb_io.report import load_report_from_json
from pbcore.util.Process import backticks
from pbcore.io import AlignmentSet
import pbcore.data

from pbreports.util import get_top_contigs_from_ref_entry, movie_to_cell
from pbreports.report.sat import (_validate_inputs, _get_read_hole_data,
                                  _cell_2_inst, _get_variants_data,
                                  _get_mapping_stats_data,
                                  _get_reads_info, summarize_report)

from base_test_case import LOCAL_DATA

DATA = os.path.join(LOCAL_DATA, "sat")
log = logging.getLogger(__name__)


class TestCoreFunctions(unittest.TestCase):

    def test_cell_2_inst(self):
        self.assertEqual('42129', _cell_2_inst(
            'm130306_023456_42129_c100422252550000001523053002121396'))

    def test_timestamped_moviename(self):
        moviename = "m54004_151002_00100"
        cellname = movie_to_cell(moviename)
        # XXX for the time being the cellname will be the timestamped
        # moviename...
        self.assertEqual(moviename, cellname)
        self.assertEqual('54004', _cell_2_inst(cellname))

    def test_variants_rpt_atts(self):
        rpt = os.path.join(DATA, 'variants_report.json')
        d = _get_variants_data(rpt)
        self.assertEqual(1, d['coverage'])
        self.assertEqual(1, d['accuracy'])

    def test_mapping_stats_rpt_atts(self):
        rpt = os.path.join(DATA, 'mapping_stats_report.json')
        d = _get_mapping_stats_data(rpt)
        self.assertEqual(1328, d['mapped_readlength_mean'])


# XXX note that due to use of canned data, we have a rather unusual instrument
# ID and a variants report that has nothing to do with the actual alignments;
# this is close enough for a unit test however
class TestSatRpt(unittest.TestCase):

    def setUp(self):
        """
        Before *every* test
        """
        self._output_dir = tempfile.mkdtemp(suffix="sat")

    def getAlignmentSet(self):
        return pbcore.data.getBamAndCmpH5()[0]

    def tearDown(self):
        """
        After *every* test
        """
        if os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def test_validate_inputs(self):
        """
        inputs cannot be null or non-existent
        """
        als = self.getAlignmentSet()
        _validate_inputs([('a', als)])

        with self.assertRaises(PbReportError):
            _validate_inputs([('a', None)])

        with self.assertRaises(IOError):
            _validate_inputs([('a', '/dont/exist')])

    def test_get_reads_info(self):
        bam = self.getAlignmentSet()
        assert os.path.exists(bam)
        ri, inst = _get_reads_info(bam)
        d = _get_read_hole_data(ri, inst)
        self.assertEqual('sidney', d['instrument'] )
        self.assertEqual(48, d['reads_in_cell'] )

    def test_exit_code_0(self):
        bam = self.getAlignmentSet()
        var_rpt = os.path.join(DATA, 'variants_report.json')
        mapping_rpt = os.path.join(DATA, 'mapping_stats_report.json')
        cmd = 'python -m pbreports.report.sat {o} {r} {c} {a} {v}'.format(o=self._output_dir,
                                                                r='rpt.json',
                                                                c=bam,
                                                                a=var_rpt,
                                                                v=mapping_rpt)
        o, c, m = backticks(cmd)
        log.info(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            print(m)
        self.assertEquals(0, c)
        rpt_file = os.path.join(self._output_dir, 'rpt.json')
        rpt = load_report_from_json(rpt_file)
        self.assertEqual('sidney', rpt.get_attribute_by_id('instrument').value)
        self.assertEqual(1, rpt.get_attribute_by_id('coverage').value)
        self.assertEqual(1, rpt.get_attribute_by_id('accuracy').value)
        self.assertEqual(1328, rpt.get_attribute_by_id('mapped_readlength_mean').value)
        self.assertEqual(48, rpt.get_attribute_by_id('reads_in_cell').value)
        out = StringIO()
        self.assertTrue(summarize_report(rpt_file, out=out))


class TestSatRptDatasetXml(TestSatRpt):

    @classmethod
    def setUpClass(cls):
        ds = AlignmentSet(pbcore.data.getBamAndCmpH5()[0], strict=True)
        cls.alignment_set_xml = tempfile.NamedTemporaryFile(
            suffix=".alignmentset.xml").name
        ds.write(cls.alignment_set_xml)

    def getAlignmentSet(self):
        return self.alignment_set_xml


class TestSatRptToolContract(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbreports.report.sat "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        pbcore.data.getBamAndCmpH5()[0],
        os.path.join(DATA, 'variants_report.json'),
        os.path.join(DATA, 'mapping_stats_report.json'),
    ]
    TASK_OPTIONS = {}
