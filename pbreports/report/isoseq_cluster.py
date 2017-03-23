"""
Generate a report for a Iso-Seq Cluster run, given both
consensus isoforms reads in Fasta file and a
cluster summary.
"""

from pprint import pformat
import functools
import logging
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")

from pbcommand.models.report import Report, PlotGroup
from pbcommand.models import FileTypes, get_pbparser
from pbcommand.pb_io.report import load_report_from_json
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log
from pbcore.io import ContigSet

from pbreports.plot.helper import (create_plot_impl, get_blue,
                                   make_histogram_with_cdf)
from pbreports.io.specs import *
from pbreports.util import attributes_to_table, report_to_attributes

log = logging.getLogger(__name__)

__version__ = '0.2.0'


class Constants(object):
    TOOL_ID = "pbreports.tasks.isoseq_cluster"
    DRIVER_EXE = "python -m pbreports.report.isoseq_cluster --resolved-tool-contract"
    R_ID = "isoseq_cluster"

    # Attributes
    A_LENGTH = "avg_consensus_isoform_length"
    A_CONSENSUS = "num_consensus_isoforms"
    A_BASES = "num_total_bases"

    # PlotGroup
    PG_READLENGTH = "consensus_isoforms_readlength_group"
    PG_AVGQV = "hq_lq_isoforms_avgqv_group"

    # Plots
    P_READLENGTH = "consensus_isoforms_readlength_hist"
    P_AVGQV = "hq_lq_isoforms_avgqv_hist"

    # Table
    T_ATTR = "isoseq_classify_table"

spec = load_spec(Constants.R_ID)

create_readlength_plot = functools.partial(
    create_plot_impl, make_histogram_with_cdf, Constants.P_READLENGTH,
    ("Read Length", "Reads", "Reads > Read Length"), 80,
    "consensus_isoforms_readlength_hist.png", get_blue(3))

create_avgqv_plot = functools.partial(
    create_plot_impl, make_histogram_with_cdf, Constants.P_AVGQV,
    ("HQ LQ Isoform Average QV", "Isoforms", "Isoforms > Average QV"), 80,
    "hq_lq_isoforms_avgqv_hist.png", get_blue(3))


def make_report(reads_fasta, hq_isoforms_fq, lq_isoforms_fq, summary_txt, output_dir):
    """
    Generate a report with ID, tables, attributes and plot groups.

    reads_fasta --- an input FASTA file which has all consensus
    isoforms produced by pbtranscript.py cluster.
    This file is required to plot a read length histogram as part of
    the report:
         consensus_isoforms_readlength_hist.png

    hq_isoforms_fq/lq_isoforms_lq --- input FASTQ files which has
    all HQ/LQ isoforms produced by pbtranscript.py cluster.
    These two files will be required to plot the average QV histograms:
         hq_lq_isoforms_avgqv_hist.png

    summary_txt --- a summary TXT file with cluster attributes,
    including two attributes:
         number of consensus isoforms
         average length of consensus isoforms
    Attributes of the report are extracted from this file.

    """
    log.info("Plotting read length histogram from file: {f}".
             format(f=reads_fasta))

    # Collect read lengths of
    reader = ContigSet(reads_fasta)
    rs = [len(r.sequence) for r in reader]
    reader.close()
    readlengths = np.array(rs).astype(float)

    # Plot read length histogram
    readlength_plot = create_readlength_plot(readlengths, output_dir)
    readlength_group = PlotGroup(Constants.PG_READLENGTH,
                                 plots=[readlength_plot],
                                 thumbnail=readlength_plot.thumbnail)

    # Collect average qvs
    hq_qvs = [np.mean(r.quality) for r in ContigSet(hq_isoforms_fq)]
    lq_qvs = [np.mean(r.quality) for r in ContigSet(lq_isoforms_fq)]
    avgqvs = np.array(hq_qvs + lq_qvs)

    # Plot average qv histogram
    avgqv_plot = create_avgqv_plot(avgqvs, output_dir)
    avgqv_group = PlotGroup(Constants.PG_AVGQV,
                            plots=[avgqv_plot],
                            thumbnail=avgqv_plot.thumbnail)

    log.info("Plotting summary attributes from file: {f}".
             format(f=summary_txt))
    # Produce attributes based on summary.
    dataset_uuids = [ContigSet(reads_fasta).uuid]
    attributes = report_to_attributes(summary_txt)
    r = load_report_from_json(summary_txt)
    # FIXME(nechols)(2016-03-22) not using the dataset UUIDs from these
    # reports; should we be?

    table = attributes_to_table(attributes, Constants.T_ATTR)
    log.info(str(table))

    # A report is consist of ID, tables, attributes, and plotgroups.
    report = Report(Constants.R_ID,
                    attributes=attributes,
                    plotgroups=[readlength_group, avgqv_group],
                    dataset_uuids=dataset_uuids)

    return spec.apply_view(report)


def _run(fasta_file, hq_isoforms_fq, lq_isoforms_fq, summary_txt, json_report, output_dir):
    if output_dir in ["", None]:
        output_dir = os.getcwd()
    report = make_report(
        reads_fasta=fasta_file,
        hq_isoforms_fq=hq_isoforms_fq,
        lq_isoforms_fq=lq_isoforms_fq,
        summary_txt=summary_txt,
        output_dir=output_dir)
    log.info(pformat(report.to_dict()))
    report.write_json(json_report)
    return 0


def args_runner(args):
    return _run(
        fasta_file=args.reads_fasta,
        hq_isoforms_fq=args.hq_isoforms_fq,
        lq_isoforms_fq=args.lq_isoforms_fq,
        summary_txt=args.summary_txt,
        json_report=args.outJson,
        output_dir=os.path.dirname(args.outJson))


def resolved_tool_contract_runner(resolved_tool_contract):
    rtc = resolved_tool_contract
    return _run(
        fasta_file=rtc.task.input_files[0],
        hq_isoforms_fq=rtc.task.input_files[2],
        lq_isoforms_fq=rtc.task.input_files[3],
        summary_txt=rtc.task.input_files[1],
        json_report=rtc.task.output_files[0],
        output_dir=os.path.dirname(rtc.task.output_files[0]))


def get_contract_parser():
    p = get_pbparser(
        Constants.TOOL_ID,
        __version__,
        "Iso-Seq Cluster Report",
        __doc__,
        Constants.DRIVER_EXE,
        is_distributed=True)

    p.add_input_file_type(FileTypes.DS_CONTIG, "reads_fasta", "Fasta reads",
                          description="Reads in FASTA format, usually are consensus, " +
                          "isoforms produced by Iso-Seq Cluster.")

    p.add_input_file_type(FileTypes.DS_CONTIG, "hq_isoforms_fq", "HQ isoforms in Fastq",
                          description="HQ isoforms in FASTQ format produced by Iso-Seq Cluster.")

    p.add_input_file_type(FileTypes.DS_CONTIG, "lq_isoforms_fq", "LQ isoforms in Fastq",
                          description="LQ isoforms in FASTQ format produced by Iso-Seq Cluster.")

    p.add_input_file_type(FileTypes.JSON, "summary_txt", "Summary text",
                          description="A summary produced by Iso-Seq Cluster, e.g. " +
                          "cluster_summary.txt")
    p.add_output_file_type(FileTypes.REPORT, "outJson", "Transcript Clustering Report",
                           description="Summary of results from pbtranscript",
                           default_name="isoseq_cluster_report")
    return p


def main(argv=sys.argv):
    mp = get_contract_parser()
    return pbparser_runner(argv[1:],
                           mp,
                           args_runner,
                           resolved_tool_contract_runner,
                           log,
                           setup_log)

if __name__ == '__main__':
    sys.exit(main())
