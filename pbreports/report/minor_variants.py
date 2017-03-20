import os
import os.path as op
import logging
import sys
import numpy as np
import json

from pbcommand.models.report import Report, Table, Column, Plot, PlotGroup, Attribute
from pbcommand.models import TaskTypes, FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.common_options import add_debug_option
from pbcommand.utils import setup_log
from pbreports.io.specs import *

class Constants(object):
    TOOL_ID = "pbreports.tasks.minor_variants_report"
    DRIVER_EXE = ("python -m pbreports.report.minor_variants "
                  "--resolved-tool-contract ")
    R_ID = "minor_variants"
    T_ID = "sample_table"
    C_SAMPLES = "barcode"
    C_COVERAGE = "coverage"
    C_VARIANTS = "variants"
    C_GENES = "genes"
    C_DRMS = "drms"
    C_HAPLOTYPES = "haplotypes"
    C_HAP_FREQ = "haplotype_frequency"
    VARIANT_FILE = "variant_summary.csv"


def to_variant_table(juliet_summary, output_dir):
    samples = positions = ref_codons = sample_codons = frequencies = 
    coverage = genes = drms = haplotype_names = haplotype_frequencies = []
    
    variant_table = [samples, positions, ref_codons, sample_codons, frequencies,
                     coverage, genes, drms, haplotype_names, haplotype_frequencies]
    
    return variant_table


def write_variant_table(variant_table, output_dir):
    with open(op.join(output_dir, Constants.VARIANT_FILE), 'w') as csvfile:
        writer = csv.writer(csvfile)
        [writer.writerow(r) for r in variant_table]



def aggregate_variant_table(variant_table):
    samples = coverage = variants = genes = drms = haploytypes = max_hap_freq = []
    
    return samples, coverage, variants, genes, drms, haploytypes, max_hap_freq
        

def to_sample_table(variant_table):
    samples, coverage, variants, genes, drms, haploytypes, 
    max_hap_freq = aggregate_variant_table(variant_table)
    
    columns = [Column(Constants.C_SAMPLES),
               Column(Constants.C_COVERAGE),
               Column(Constants.C_VARIANTS),
               Column(Constants.C_GENES),
               Column(Constants.C_DRMS),
               Column(Constants.C_HAPLOTYPES),
               Column(Constants.C_HAP_FREQ)]
    sample_table = Table(Constants.T_ID, columns=columns)
    sample.table.add_data_by_column_id(Constants.C_SAMPLES, samples)
    sample.table.add_data_by_column_id(Constants.C_COVERAGE, coverage)
    sample.table.add_data_by_column_id(Constants.C_VARIANTS, variants)
    sample.table.add_data_by_column_id(Constants.C_GENES, genes)
    sample.table.add_data_by_column_id(Constants.C_DRMS, drms)
    sample.table.add_data_by_column_id(Constants.C_HAPLOTYPES, haplotypes)
    sample.table.add_data_by_column_id(Constants.C_HAP_FREQ, max_hap_freq)

    return sample_table


def to_report(juliet_summary_file, output_dir):
    
    with open(juliet_summary_file) as f:
        juliet_summary = json.load(f)

    variant_table = to_variant_table(juliet_summary)
    write_variant_table(variant_table, output_dir)
    tables = [to_sample_table(variant_table)]
    report = Report(Constants.R_ID, tables=tables)

    return spec.apply_view(report)


def resolved_tool_contract_runner(resolved_tool_contract):
    rtc = resolved_tool_contract
    log.info("Starting {f} v{v}".format(f=os.path.basename(__file__),
                                        v=__version__))
    output_dir = os.path.dirname(rtc.task.output_files[0])
    try:
        report = to_report(rtc.task.input_files[0], output_dir)
        report.write_json(rtc.task.output_files[0])
        return 0
    except InvalidStatsError as e:
        log.error(e)
        return 1


def _add_options_to_parser(p):
    p.add_input_file_type(
        FileTypes.JSON,
        file_id="json",
        name="JSON",
        description="Juliet Summary JSON")
    p.add_output_file_type(FileTypes.REPORT, "report", spec.title,
                           description=("Filename of JSON output report. Should be name only, "
                                        "and will be written to output dir"),
                           default_name="report")
    p.add_output_file_type(FileTypes.CSV, "csv", "Per-Variant Table",
                           description=("Filename of CSV output table. Should be name only, "
                                        "and will be written to output dir"),
                           default_name="report")


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
        "Minor Variants Report",
        __doc__,
        Constants.DRIVER_EXE,
        is_distributed=True)
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


if __name__ == "__main__":
    sys.exit(main())

