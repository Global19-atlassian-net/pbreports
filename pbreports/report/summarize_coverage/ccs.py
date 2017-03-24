
"""
Alternate entry point for summarize_coverage using ConsensusAlignmentSet input.
"""

import logging
import sys

from pbcommand.models import FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log

from pbreports.report.summarize_coverage import summarize_coverage

log = logging.getLogger(__name__)
__version__ = "0.1"


class Constants(object):
    TOOL_ID = "pbreports.tasks.summarize_coverage_ccs"
    DRIVER_EXE = "python -m {m} --resolved-tool-contract ".format(
        m="pbreports.report.summarize_coverage.ccs")


def _get_parser():
    p = get_pbparser(
        Constants.TOOL_ID,
        __version__,
        "Summarize Coverage (CCS)",
        __doc__,
        Constants.DRIVER_EXE)
    return summarize_coverage.add_options_to_parser(p, ds_type=FileTypes.DS_ALIGN_CCS)


def main(argv=sys.argv):
    return pbparser_runner(argv[1:],
                           _get_parser(),
                           summarize_coverage.args_runner,
                           summarize_coverage.resolved_tool_contract_runner,
                           log,
                           setup_log)


if __name__ == "__main__":
    sys.exit(main())
