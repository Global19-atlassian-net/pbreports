import os
import logging
import unittest
import tempfile
import shlex

from base_test_case import ROOT_DATA_DIR, run_backticks

from pbreports.report.summarize_compare_by_movie import main

log = logging.getLogger()

_DATA_DIR = os.path.join(ROOT_DATA_DIR, 'control', 'summarize_compare_by_movie')
_CONTROL_CMP_H5 = os.path.join(_DATA_DIR, 'control_reads.cmp.h5')
_INPUT_FOFN = os.path.join(_DATA_DIR, 'input.fofn')

_EXE = 'summarize_compare_by_movie'

def _to_cmd(input_fofn, cmp_h5, csv):
    _d = dict(e=_EXE, i=input_fofn, c=cmp_h5, o=csv)
    return "{e} --debug --fofn={i} {c} {o}".format(**_d)

def _generate_tmp_file():
    t = tempfile.NamedTemporaryFile(suffix='_summarize_by_movie.csv', delete=False)
    t.close()
    return t.name


class TestHelp(unittest.TestCase):
    def test_help(self):
        rcode = run_backticks("{e} --help".format(e=_EXE))
        self.assertEqual(rcode, 0)


class TestSummarizeCompareByMovie(unittest.TestCase):
    def test_basic(self):
        csv = _generate_tmp_file()
        cmd = _to_cmd(_INPUT_FOFN, _CONTROL_CMP_H5, csv)

        args = shlex.split(cmd)

        rcode = main(args)
        self.assertEqual(rcode, 0)


class TestIntegrationSummarizeCompareByMovie(unittest.TestCase):

    def test_basic(self):
        csv = _generate_tmp_file()

        cmd = _to_cmd(_INPUT_FOFN, _CONTROL_CMP_H5, csv)
        rcode = run_backticks(cmd)
        self.assertEqual(rcode, 0)
