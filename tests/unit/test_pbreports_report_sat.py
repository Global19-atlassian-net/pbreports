
# TODO this tests using cmp.h5 and corresponding DataSet XML as input, but no
# .bam files - need additional test data

from cStringIO import StringIO
import os
import logging
import traceback
import json
import tempfile
import unittest
import shutil

from pbcore.util.Process import backticks

from base_test_case import _get_root_data_dir

from pbreports.model.model import PbReportError
from pbreports.util import get_top_contigs_from_ref_entry, movie_to_cell
from pbreports.report.sat import (_validate_inputs, _get_read_hole_data,
                                  _cell_2_inst, _get_variants_data,
                                  _get_mapping_stats_data, _deserialize_report,
                                  _get_reads_info, summarize_report)


DATA = os.path.join(_get_root_data_dir(), 'sat')

log = logging.getLogger(__name__)


class TestSatRpt(unittest.TestCase):

    def setUp(self):
        """
        Before *every* test
        """
        self._output_dir = tempfile.mkdtemp(suffix="sat")

    def getAlignmentSet(self):
        return os.path.join(DATA, 'aligned_reads.cmp.h5')

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


    def test_cell_2_inst(self):
        self.assertEqual('42129', _cell_2_inst('m130306_023456_42129_c100422252550000001523053002121396'))

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
        self.assertEqual(2120, d['mapped_readlength_mean'])
        
    
    def test_get_reads_info(self):
        ch5 = self.getAlignmentSet()
        self.assertTrue( os.path.exists(ch5))
        ri, inst = _get_reads_info(ch5)
        d = _get_read_hole_data(ri, inst)
        self.assertEqual('42129', d['instrument'] )
        self.assertEqual(55073, d['reads_in_cell'] )

    def test_exit_code_0(self):
        
        ch5 = self.getAlignmentSet()
        var_rpt = os.path.join(DATA, 'variants_report.json')
        mapping_rpt = os.path.join(DATA, 'mapping_stats_report.json')
        cmd = 'pbreport sat {o} {r} {c} {a} {v}'.format(o=self._output_dir,
                                                                r='rpt.json',
                                                                c=ch5, a=var_rpt,
                                                                v=mapping_rpt)
        o, c, m = backticks(cmd)
        log.info(cmd)
        if c is not 0:
            log.error(m)
            log.error(o)
            print(m)
        self.assertEquals(0, c)
        rpt_file = os.path.join(self._output_dir, 'rpt.json')
        rpt = _deserialize_report(rpt_file)
        self.assertEqual('42129', rpt.get_attribute_by_id('instrument').value)
        self.assertEqual(1, rpt.get_attribute_by_id('coverage').value)
        self.assertEqual(1, rpt.get_attribute_by_id('accuracy').value)
        self.assertEqual(2120, rpt.get_attribute_by_id('mapped_readlength_mean').value)
        self.assertEqual(55073, rpt.get_attribute_by_id('reads_in_cell').value)
        out = StringIO()
        self.assertTrue(summarize_report(rpt_file, out=out))

class TestSatRptDatasetXml(TestSatRpt):
    def getAlignmentSet(self):
        return os.path.join(DATA, 'aligned_reads.xml')
