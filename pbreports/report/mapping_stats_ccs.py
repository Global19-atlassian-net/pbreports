
"""
Generates a report of statistics for CCS reads mapped to a reference genome
with Blasr/pbalign.
"""

from collections import OrderedDict
import sys

from pbcommand.models import get_pbparser, FileTypes

from pbreports.report.streaming_utils import PlotViewProperties
from pbreports.report.mapping_stats import *

TOOL_ID = "pbreports.tasks.mapping_stats_ccs"
DRIVER_EXE = "python -m pbreports.report.mapping_stats_ccs --resolved-tool-contract"
__version__ = "0.1"


class CCSMappingStatsCollector(MappingStatsCollector):
    COLUMN_ATTR = [
        Constants.A_NREADS, Constants.A_READLENGTH, Constants.A_READLENGTH_N50,
        Constants.A_NBASES, Constants.A_READ_CONCORDANCE
    ]
    ATTR_LABELS = OrderedDict([
        (Constants.A_READ_CONCORDANCE, "Mapped Consensus Read Mean Concordance"),
        (Constants.A_NREADS, "Mapped Consensus Reads"),
        (Constants.A_NBASES, "Mapped Consensus Bases"),
        (Constants.A_READLENGTH, "Mapped Consensus Read Length Mean"),
        (Constants.A_READLENGTH_Q95, "Mapped Consensus Read Length 95%"),
        (Constants.A_READLENGTH_MAX, "Mapped Consensus Read Length Max"),
        (Constants.A_READLENGTH_N50, "Mapped N50"),
    ])
    ATTR_DESCRIPTIONS = {
        Constants.A_READ_CONCORDANCE: "The mean concordance of CCS reads that mapped to the reference sequence",
        Constants.A_NREADS: "The number of CCS reads that mapped to the reference sequence",
        Constants.A_NBASES: "The number of CCS read bases that mapped to the reference sequence",
        Constants.A_READLENGTH: "The mean length of CCS reads that mapped to the reference sequence",
        Constants.A_READLENGTH_Q95: "The 95th percentile of length of CCS reads that mapped to the reference sequence",
        Constants.A_READLENGTH_MAX: "The maximum length of CCS reads that mapped to the reference sequence",
        Constants.A_READLENGTH_N50: "The read length at which 50% of the bases are in reads longer than, or equal to, this value"
    }
    HISTOGRAM_IDS = {
        Constants.P_READ_CONCORDANCE: "read_concordance_histogram",
        Constants.P_READLENGTH: "readlength_histogram",
    }
    COLUMNS = [
        (Constants.C_MOVIE, "Movie"),
        (Constants.C_READS, "Mapped Reads"),
        (Constants.C_READLENGTH, "Mapped Consensus Read Length"),
        (Constants.C_READLENGTH_N50, "Mapped Consensus Read Length n50"),
        (Constants.C_READ_NBASES, "Mapped Consensus Bases"),
        (Constants.C_READ_CONCORDANCE, "Mapped Read Concordance")
    ]
    COLUMN_AGGREGATOR_CLASSES = [
        ReadCounterAggregator,
        MeanReadLengthAggregator,
        N50Aggreggator,
        NumberSubreadBasesAggregator,
        MeanSubreadConcordanceAggregator
    ]

    def _get_plot_view_configs(self):
        """
        Any change to the 'raw' view of a report plot should be changed here.

        There's three histogram plots.

        1. Subread accuracy
        2. Subread rendlength
        3. Readlength

        """
        _p = [
            PlotViewProperties(
                Constants.P_READ_CONCORDANCE,
                Constants.PG_READ_CONCORDANCE,
                generate_plot,
                'mapped_read_concordance_histogram.png',
                xlabel="Concordance",
                ylabel="Consensus Reads",
                color=get_green(3),
                edgecolor=get_green(2),
                use_group_thumb=True,
                plot_group_title="Mapped Consensus Read Concordance"),
            PlotViewProperties(
                Constants.P_READLENGTH,
                Constants.PG_READLENGTH,
                generate_plot,
                'mapped_readlength_histogram.png',
                xlabel="Read Length",
                ylabel="Reads",
                color=get_blue(3),
                edgecolor=get_blue(2),
                use_group_thumb=True,
                plot_group_title="Mapped Consensus Read Length")
        ]
        return {v.plot_id: v for v in _p}

    def _get_total_aggregators(self):
        return OrderedDict([
            (Constants.A_READ_CONCORDANCE, MeanSubreadConcordanceAggregator()),
            (Constants.A_NREADS, ReadCounterAggregator()),
            (Constants.A_READLENGTH, MeanReadLengthAggregator()),
            (Constants.A_READLENGTH_MAX, MaxReadLengthAggregator()),
            (Constants.A_READLENGTH_Q95, MappedReadLengthQ95(dx=10,
                                                             nbins=10000)),
            (Constants.A_READLENGTH_N50, N50Aggreggator()),
            (Constants.A_NBASES, NumberBasesAggregator()),
            (self.HISTOGRAM_IDS[Constants.P_READLENGTH],
             ReadLengthHistogram()),
            (self.HISTOGRAM_IDS[Constants.P_READ_CONCORDANCE],
             SubReadConcordanceHistogram(dx=0.005, nbins=1001))
        ])


def to_report(alignment_file, output_dir):
    return CCSMappingStatsCollector(alignment_file).to_report(output_dir)


def _args_runner(args):
    return run_and_write_report(args.alignment_file, args.report_json,
                                report_func=to_report)


def _resolved_tool_contract_runner(resolved_contract):
    """
    Run the mapping report from a resolved tool contract.

    :param resolved_contract:
    :type resolved_contract: ResolvedToolContract
    :return: Exit code
    """

    alignment_path = resolved_contract.task.input_files[0]

    # This is a bit different than the output dir oddness that Johann added.
    # the reports dir should be determined from the dir of the abspath of the report.json file
    # resolved values will always be absolute paths.
    output_report = resolved_contract.task.output_files[0]

    return run_and_write_report(alignment_path, output_report,
                                report_func=to_report)


def _get_parser():
    parser = get_pbparser(TOOL_ID, __version__,
                          "CCS Mapping Statistics", __doc__, DRIVER_EXE)
    parser.add_input_file_type(FileTypes.DS_ALIGN_CCS, "alignment_file",
                               "ConsensusAlignment XML DataSet",
                               "BAM, SAM or ConsensusAlignment DataSet")
    parser.add_output_file_type(FileTypes.REPORT, "report_json",
                                "PacBio Json Report",
                                "Output report JSON file.",
                                default_name="mapping_stats_report")
    return parser


if __name__ == '__main__':
    sys.exit(main(get_parser_func=_get_parser,
                  args_runner_func=_args_runner,
                  rtc_runner_func=_resolved_tool_contract_runner))
