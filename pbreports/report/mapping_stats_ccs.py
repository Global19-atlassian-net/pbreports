
"""
Create a Mapping Report from a Aligned CCS BAM or ConsensusAlignment DataSet
"""

import sys

from pbcommand.models import get_pbparser, FileTypes

from pbreports.report import mapping_stats

TOOL_ID = "pbreports.tasks.mapping_stats_ccs"
DRIVER_EXE = "python -m pbreports.report.mapping_stats_ccs --resolved-tool-contract"
__version__ = "0.1"

def get_parser():
    parser = get_pbparser(TOOL_ID, __version__, "CCS Mapping Statistics", __doc__, DRIVER_EXE)

    parser.add_input_file_type(FileTypes.DS_ALIGN_CCS, "alignment_file", "ConsensusAlignment XML DataSet", "BAM, SAM or ConsensusAlignment DataSet")
    parser.add_output_file_type(FileTypes.REPORT, "report_json", "PacBio Json Report", "Output report JSON file.", "mapping_stats_report.json")

    return parser


if __name__ == '__main__':
    sys.exit(mapping_stats.main(get_parser_func=get_parser))
