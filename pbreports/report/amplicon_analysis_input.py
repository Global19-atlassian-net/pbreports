"""Summarize the Long Amplicon Analysis using the ZMW results"""

from collections import defaultdict
from pprint import pformat
import argparse
import logging
import json
import os
import sys

from pbcommand.models.report import Report, Table, Column
from pbcommand.models import FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.common_options import add_debug_option
from pbcommand.utils import setup_log


log = logging.getLogger(__name__)

__version__ = '0.1.1'


class Constants(object):
    TOOL_ID = "pbreports.tasks.amplicon_analysis_input"
    DRIVER_EXE = "python -m pbreports.report.amplicon_analysis_input --resolved-tool-contract "
    DATA_GOOD = "good"
    DATA_CHIMERA = "chimera"
    DATA_NOISE = "noise"


def parse_summary(summary):
    # Internal helper function for parsing the Summary CSV header
    def parse_summary_header(header):
        parts = header.strip().split(',')
        name = parts.index("FastaName")
        barcode = parts.index("BarcodeName")
        noise = parts.index("NoiseSequence")
        chimera = parts.index("IsChimera")
        return name, barcode, chimera, noise

    # Parse the summary file
    summary_data = {}
    with open(summary) as handle:
        # Read the summary header to find the location of important fields
        name, barcode, chimera, noise = parse_summary_header(
            handle.next().strip())

        for line in handle:
            # Parse the requisite fields from the current line
            parts = line.split(',')
            seq_name = parts[name]
            barcode_name = parts[barcode]
            noise_flag = parts[noise] == "1"
            chimera_flag = parts[chimera] == "1"

            # Catch whether it's a new barcode for summary setup
            if barcode_name not in summary_data:
                summary_data[barcode_name] = {
                    Constants.DATA_GOOD: set(),
                    Constants.DATA_CHIMERA: set(),
                    Constants.DATA_NOISE: set()
                }

            # Add the current sequence to the appropriate bin
            if chimera_flag:
                summary_data[barcode_name][Constants.DATA_CHIMERA].add(seq_name)
            elif noise_flag:
                summary_data[barcode_name][Constants.DATA_NOISE].add(seq_name)
            else:
                summary_data[barcode_name][Constants.DATA_GOOD].add(seq_name)
    return summary_data


def parse_mappings(mappings_file):
    consensus_sums = defaultdict(float)
    with open(mappings_file) as json_in:
        for barcode_id, zmws_d in json.load(json_in).iteritems():
            for zmw_id, consensus_d in zmws_d.iteritems():
                for consensus_id, weight in consensus_d.iteritems():
                    consensus_sums[consensus_id] += weight
    return consensus_sums


def tabulate_results(summary_data, consensus_sums):
    # Combine the individual consensus sums by barcode and in total
    tabulated_data = {'all': defaultdict(float)}
    for barcode, barcode_dict in summary_data.iteritems():
        data = defaultdict(float)
        for sequence_type, consensus_sequences in barcode_dict.iteritems():
            data[sequence_type] = 0.0
            for consensus in consensus_sequences:
                weight = consensus_sums[consensus]
                data[sequence_type] += weight
                tabulated_data['all'][sequence_type] += weight
        tabulated_data[barcode] = data
    # Round the final tallys and their percentages to the nearest integer
    final_data = {}
    for barcode, data in tabulated_data.iteritems():
        final_data[barcode] = defaultdict(float)
        total = data[Constants.DATA_GOOD] + data[Constants.DATA_CHIMERA] + data[Constants.DATA_NOISE]
        for sequence_type, weight in data.iteritems():
            value = tabulated_data[barcode][sequence_type]
            final_data[barcode][sequence_type] = int(value)
            final_data[barcode][sequence_type + '_pct'] = value / total
    return final_data


def create_table(tabulated_data):
    """Long Amplicon Analysis results table"""

    columns = []
    columns.append(Column("barcode_col", header="Sample"))
    columns.append(Column("good", header="Good"))
    columns.append(Column("good_pct", header="Good (%)"))
    columns.append(Column("chimera", header="Chimeric"))
    columns.append(Column("chimera_pct", header="Chimeric (%)"))
    columns.append(Column("noise", header="Noise"))
    columns.append(Column("noise_pct", header="Noise (%)"))

    t = Table("result_table",
              title="Amplicon Input Molecule Summary", columns=columns)

    for barcode, data in tabulated_data.iteritems():
        if barcode != 'all':
            t.add_data_by_column_id('barcode_col', barcode)
            for column_id in ['good', 'good_pct', 'chimera', 'chimera_pct', 'noise', 'noise_pct']:
                t.add_data_by_column_id(column_id, data[column_id])
    t.add_data_by_column_id('barcode_col', 'All')
    for column_id in ['good', 'good_pct', 'chimera', 'chimera_pct', 'noise', 'noise_pct']:
        t.add_data_by_column_id(column_id, tabulated_data['all'][column_id])

    log.info(str(t))
    return t


def run_to_report(summary_csv, zmws_json):
    log.info("Generating PCR report v{v} from summary '{s}' "
             "and ZMW mappings '{j}'".format(v=__version__,
                                             s=summary_csv,
                                             j=zmws_json))

    # Parse the data into dictionaries
    summary_data = parse_summary(summary_csv)
    consensus_sums = parse_mappings(zmws_json)

    # Tabulate the values for each category
    tabulated_data = tabulate_results(summary_data, consensus_sums)

    # Convert the data into a PBreports table
    table = create_table(tabulated_data)

    # ids must be lowercase.
    r = Report("amplicon_analysis_input",
               title="Amplicon Inputs",
               tables=[table])

    return r


def amplicon_analysis_input(summary_csv, zmws_json, report_json):
    log.info("Running {f} v{v}.".format(
        f=os.path.basename(__file__), v=__version__))
    report = run_to_report(summary_csv, zmws_json)
    log.info(pformat(report.to_dict()))
    report.write_json(report_json)
    return 0


def args_runner(args):
    amplicon_analysis_input(args.report_csv, args.zmws_json, args.report_json)
    return 0


def resolved_tool_contract_runner(resolved_tool_contract):
    rtc = resolved_tool_contract
    amplicon_analysis_input(rtc.task.input_files[0],
                            rtc.task.input_files[1],
                            rtc.task.output_files[0])
    return 0


def _add_options_to_parser(p):
    p.add_input_file_type(
        FileTypes.CSV,
        file_id="report_csv",
        name="ConsensusReportCSV",
        description="Consensus Report CSV")
    p.add_input_file_type(
        FileTypes.JSON,
        file_id="zmws_json",
        name="JSON per-ZMW info",
        description="JSON file containing per-ZMW info")
    p.add_output_file_type(
        FileTypes.REPORT,
        file_id="report_json",
        name="LAA input report",
        description="Long Amplicon Analysis input report JSON",
        default_name="amplicon_input_report")


def add_options_to_parser(p):
    """
    API function for extending main pbreport arg parser (independently of
    tool contract interface).
    """
    p_wrap = _get_parser_core()
    p_wrap.arg_parser.parser = p
    p.description = __doc__
    add_debug_option(p)
    _add_options_to_parser(p_wrap)
    p.set_defaults(func=args_runner)
    return p


def _get_parser_core():
    p = get_pbparser(
        Constants.TOOL_ID,
        __version__,
        "Amplicon Analysis Input",
        __doc__,
        Constants.DRIVER_EXE)
    return p


def get_parser():
    p = _get_parser_core()
    _add_options_to_parser(p)
    return p


def main(argv=sys.argv):
    mp = get_parser()
    return pbparser_runner(argv[1:],
                           mp,
                           args_runner,
                           resolved_tool_contract_runner,
                           log,
                           setup_log)

# for 'python -m pbreports.report.amplicon_analysis_input ...'
if __name__ == "__main__":
    sys.exit(main())
