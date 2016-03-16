import os
from pprint import pformat
import shutil
import shlex
import unittest
import logging
import tempfile

import pbcommand.testkit

from base_test_case import LOCAL_DATA, run_backticks

import pbreports.report.motifs
from pbreports.report.motifs import to_motifs_report

log = logging.getLogger()

EXE = 'motifs_report'
_DATA_NAME = 'kinetics'
_DATA_DIR = os.path.join(LOCAL_DATA, _DATA_NAME)

_MOTIF_SUMMARY_CSV = os.path.join(_DATA_DIR, 'motif_summary.csv')
_MOTIF_GFF = os.path.join(_DATA_DIR, 'motifs.gff.gz')


def _to_cmd(gff, csv, output_dir, report_json):
    _d = dict(e=EXE, g=gff, c=csv, d=output_dir, j=report_json)
    cmd_str = '{e} {g} {c} {j}'.format(**_d)
    return cmd_str


class TestKineticsMotifs(unittest.TestCase):

    def test_basic(self):
        d = tempfile.mkdtemp()
        t = tempfile.NamedTemporaryFile(
            suffix="_motif_report.json", delete=False, dir=d)
        t.close()
        json_report = t.name
        output_dir = os.path.dirname(json_report)

        report = to_motifs_report(_MOTIF_GFF, _MOTIF_SUMMARY_CSV, output_dir)

        log.info(pformat(report.plotGroups[0].to_dict(), indent=4))
        log.info(str(report.tables[0]))

        self.assertTrue(True)

        if os.path.exists(d):
            shutil.rmtree(d)


class TestIntegrationKineticsMotifs(unittest.TestCase):

    def test_basic(self):
        t = tempfile.NamedTemporaryFile(
            suffix="_motif_report.json", delete=False)
        t.close()
        json_report = t.name
        output_dir = os.path.dirname(json_report)

        _d = dict(g=_MOTIF_GFF, c=_MOTIF_SUMMARY_CSV, j=json_report,
                  d=output_dir,
                  e=EXE)
        cmd_str = '{e} {g} {c} {j}'.format(**_d)

        rcode = run_backticks(cmd_str)
        self.assertEqual(
            rcode, 0, "Exit code '{o}' for command '{c}'".format(o=rcode, c=cmd_str))


class TestKineticsMotifsMain(unittest.TestCase):

    def test_basic(self):
        t = tempfile.NamedTemporaryFile(
            suffix="_motif_report.json", delete=False)
        t.close()
        json_report = t.name
        output_dir = os.path.dirname(json_report)

        _d = dict(g=_MOTIF_GFF, c=_MOTIF_SUMMARY_CSV, j=json_report,
                  d=output_dir,
                  e=EXE)
        cmd_str = '{e} {g} {c} {j}'.format(**_d)

        cmd = shlex.split(cmd_str)

        log.debug(cmd_str)
        log.info(cmd)

        report = pbreports.report.motifs.main(cmd)

        self.assertIsNotNone(report)


class TestToolContract(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(LOCAL_DATA, "kinetics")
    DRIVER_BASE = "python -m pbreports.report.motifs "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        os.path.join(DATA, "motifs.gff.gz"),
        os.path.join(DATA, "motif_summary.csv"),
    ]
    TASK_OPTIONS = {}
