
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

def get_parser():
    driver_exe = ("python -m "
                  "pbreports.report.summarize_coverage.ccs"
                  "--resolved-tool-contract ")
    p = get_pbparser(
        "pbreports.tasks.summarize_coverage_ccs",
        __version__,
        "Summarize Coverage (CCS)",
        __doc__,
        driver_exe)
    return p


def main(argv=sys.argv):
    mp = get_parser()
    summarize_coverage.add_options_to_parser(mp, ds_type=FileTypes.DS_ALIGN_CCS)
    return pbparser_runner(argv[1:],
                           mp,
                           summarize_coverage.args_runner,
                           summarize_coverage.resolved_tool_contract_runner,
                           log,
                           setup_log)


if __name__ == "__main__":
    sys.exit(main())
