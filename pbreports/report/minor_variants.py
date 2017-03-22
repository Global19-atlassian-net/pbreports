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
from pbreports.model import InvalidStatsError
import csv
import matplotlib.mlab as ml

__version__ = '0.1.0'

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


log = logging.getLogger(__name__)
spec = load_spec(Constants.R_ID)


def get_drm_vals(drms):
    split_drms = drms.split(" + ")
    drm_vals = []
    for drm in split_drms:
        drm_vals.append(str(drm))
    return drm_vals

def get_hap_vals(hap_hits, hap_vals):
    haps = []
    for i in xrange(len(hap_hits)):
        if hap_hits[i]:
           haps.append(hap_vals[i])
    return haps

def to_variant_table(juliet_summary):
    samples = []
    positions = []
    ref_codons = []
    sample_codons = []
    frequencies = []
    coverage = []
    genes = []
    drms = []
    haplotype_names = []
    haplotype_frequencies = []
    _all_hap_names = []
    _all_hap_freqs = []

    for sample in juliet_summary.keys():
        for haplotype in juliet_summary[sample]['haplotypes']:
            _all_hap_names.append(haplotype['name'])
            _all_hap_freqs.append(haplotype['frequency'])
        for gene in juliet_summary[sample]['genes']:
            _genes = gene['name']
            for position in gene['variant_positions']:
                _coverage = position['coverage']
                _ref_codons = position['ref_codon']
                _position = position['ref_position']
                for aa in position['variant_amino_acids']:
                    for variant in aa['variant_codons']:
                        samples.append(sample)
                        positions.append(_position)
                        ref_codons.append(_ref_codons)
                        sample_codons.append(variant['codon'])
                        frequencies.append(variant['frequency'])
                        coverage.append(_coverage)
                        genes.append(_genes)
                        drms.append(get_drm_vals(variant['known_drm']))
                        haplotype_names.append(get_hap_vals(variant['haplotype_hit'], _all_hap_names))
                        haplotype_frequencies.append(get_hap_vals(variant['haplotype_hit'], _all_hap_freqs))

    variant_table = [samples, positions, ref_codons, sample_codons, frequencies,
                     coverage, genes, drms, haplotype_names, haplotype_frequencies]
   
    return variant_table


def write_variant_table(variant_table, output_dir):
    variant_table_tr = zip(*variant_table)
    with open(op.join(output_dir, Constants.VARIANT_FILE), 'w') as csvfile:
        writer = csv.writer(csvfile)
        [writer.writerow(r) for r in variant_table_tr]


def my_unique(my_list):
    long_list = []
    for a_list in my_list:
        long_list.extend(a_list)
    unique_items = np.unique(long_list)
    return unique_items

def my_max(my_list):
    max_item = 0
    long_list = []
    for _list in my_list:
        for item in _list:
            if type(item) == float:
                long_list.append(item)
    if len(long_list) > 0:
        max_item = max(long_list)
    return max_item

def aggregate_variant_table(variant_table):

    samples = []
    coverage = []
    variants = []
    genes = []
    drms = []
    haplotypes = []
    max_hap_freq = []

    for sample in set(variant_table[0]):
        indices = [i for i, x in enumerate(variant_table[0]) if x == sample]
        _coverage = [variant_table[5][i] for i in indices]
        _genes = [variant_table[6][i] for i in indices]
        _drms = [variant_table[7][i] for i in indices]
        _haplotypes = [variant_table[8][i] for i in indices]
        _max_hap_freq = [variant_table[9][i] for i in indices]

        samples.append(str(sample))
        coverage.append(int(np.median(_coverage)))
        variants.append(len(_coverage))
        genes.append(len(np.unique(_genes)))
        drms.append(len(my_unique(_drms)))
        haplotypes.append(len(my_unique(_haplotypes)))
        max_hap_freq.append(float(my_max(_max_hap_freq)))

    sample_table = [samples, coverage, variants, genes, drms, haplotypes, max_hap_freq]

    return sample_table
        

def to_sample_table(variant_table):
    
    sample_table = aggregate_variant_table(variant_table)

    col_ids = [Constants.C_SAMPLES, Constants.C_COVERAGE, Constants.C_VARIANTS,
               Constants.C_GENES, Constants.C_DRMS, Constants.C_HAPLOTYPES,
               Constants.C_HAP_FREQ]

    columns = []
    for i in xrange(len(col_ids)):
        columns.append(Column(col_ids[i], sample_table[i]))

    sample_table_r = Table(Constants.T_ID, columns=columns)

    return sample_table_r


def to_report(juliet_summary_file, output_dir):
    
    with open(juliet_summary_file) as f:
        juliet_summary = json.load(f)

    variant_table = to_variant_table(juliet_summary)
    write_variant_table(variant_table, output_dir)
    tables = [to_sample_table(variant_table)]
    report = Report(Constants.R_ID, tables=tables)

    return spec.apply_view(report)


def args_runner(args):
    log.info("Starting {f} v{v}".format(f=os.path.basename(__file__),
                                        v=__version__))
    output_dir = os.path.dirname(args.report)
    try:
        report = to_report(args.subread_set, output_dir)
        report.write_json(args.report)
        return 0
    except InvalidStatsError as e:
        log.error(e)
        return 1


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

