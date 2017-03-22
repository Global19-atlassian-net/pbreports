import os
import os.path as op
import logging
import sys
import csv
import itertools
import json

import numpy as np

from pbcommand.models.report import Report, Table, Column
from pbcommand.models import TaskTypes, FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.common_options import add_debug_option
from pbcommand.utils import setup_log
from pbreports.io.specs import *
from pbreports.model import InvalidStatsError

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
    """Returns list of drms for a given variant, 
       using the boolean array and list of possible values"""
    split_drms = drms.split(" + ")
    drm_vals = []
    for drm in split_drms:
        drm_vals.append(str(drm))
    return drm_vals

def get_hap_vals(hap_hits, hap_vals, _type):
    """Returns list of haplotype name or frequency values
       for a given variant, using the boolean array and
       list of possible values"""
    haps = []
    for i, hap_hit in enumerate(hap_hits):
        if hap_hit:
           haps.append(_type(hap_vals[i]))
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
                        haplotype_names.append(get_hap_vals(variant['haplotype_hit'], _all_hap_names, str))
                        haplotype_frequencies.append(get_hap_vals(variant['haplotype_hit'], _all_hap_freqs, float))

    variant_table = [samples, positions, ref_codons, sample_codons, frequencies,
                     coverage, genes, drms, haplotype_names, haplotype_frequencies]
   
    return variant_table


def join_col(col):
    """Converts an array of arrays into an array of strings, using ';' as the sep."""
    joined_col = []
    for item in col:
        joined_col.append(";".join(map(str, item)))
    return joined_col

def write_variant_table(variant_table, output_dir):
    for i in [7,8,9]:
        variant_table[i] = join_col(variant_table[i])
    variant_table_tr = zip(*variant_table)
    with open(op.join(output_dir, Constants.VARIANT_FILE), 'w') as csvfile:
        writer = csv.writer(csvfile)
        [writer.writerow(r) for r in variant_table_tr]


def my_agg(my_list, _func):
    """Performs the specified function on an array of arrays, 
       returning None in the case of a ValueError"""
    try:
        return _func(i for i in itertools.chain(*my_list))
    except ValueError:
       # case for max of empty list
       return None

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
        drms.append(len(my_agg(_drms, np.unique)))
        haplotypes.append(len(my_agg(_haplotypes, np.unique)))
        max_hap_freq.append(float(my_agg(_max_hap_freq, max)))

    sample_table = [samples, coverage, variants, genes, drms, haplotypes, max_hap_freq]

    return sample_table
        

def to_sample_table(variant_table):
    
    sample_table = aggregate_variant_table(variant_table)

    col_ids = [Constants.C_SAMPLES, Constants.C_COVERAGE, Constants.C_VARIANTS,
               Constants.C_GENES, Constants.C_DRMS, Constants.C_HAPLOTYPES,
               Constants.C_HAP_FREQ]

    columns = []
    for i, col_id in enumerate(col_ids):
        columns.append(Column(col_id, values=sample_table[i]))

    sample_table_r = Table(Constants.T_ID, columns=columns)

    return sample_table_r


def to_report(juliet_summary_file, output_dir):
    
    with open(juliet_summary_file) as f:
        juliet_summary = json.load(f)

    variant_table = to_variant_table(juliet_summary)
    write_variant_table(variant_table, output_dir)
    tables = [to_sample_table(variant_table)]
    report = Report(Constants.R_ID, tables=tables)

    return spec.apply_view(report, force=True)


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

