"""
Generate a report for the results of the new Iso-Seq 3 pipeline, taking a
single TranscriptSet dataset as input.
"""

from pprint import pformat
import functools
import logging
import os
import sys

import numpy as np

from pbcommand.models.report import Report, PlotGroup, Attribute
from pbcommand.models import FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log
from pbcore.io import TranscriptSet

from pbreports.io.specs import *
from pbreports.report.isoseq_cluster import (create_readlength_plot, create_avgqv_plot)

log = logging.getLogger(__name__)

__version__ = '0.1.1'


class Constants(object):
    TOOL_ID = "pbreports.tasks.isoseq3"
    DRIVER_EXE = "python -m pbreports.report.isoseq3 --resolved-tool-contract"
    R_ID = "isoseq3"

    # Attributes
    A_N_HQ_ID = "num_polished_hq_isoforms"
    A_N_LQ_ID = "num_polished_lq_isoforms"

    # PlotGroup
    PG_READLENGTH = "consensus_isoforms_readlength_group"
    PG_AVGQV = "hq_lq_isoforms_avgqv_group"

    # Plots
    P_READLENGTH = "consensus_isoforms_readlength_hist"
    P_AVGQV = "hq_lq_isoforms_avgqv_hist"

    # Table
    T_ATTR = "isoseq_classify_table"

spec = load_spec(Constants.R_ID)


def make_report(hq_transcripts_file, lq_transcripts_file, output_dir):
    """
    Generate a report with ID, tables, attributes and plot groups.
    """
    log.info("Plotting read length histogram from files: {h} {l}".
             format(h=hq_transcripts_file, l=lq_transcripts_file))

    # Collect read lengths and average qvs
    ds_hq = TranscriptSet(hq_transcripts_file, strict=True)
    ds_lq = TranscriptSet(lq_transcripts_file, strict=True)
    readlengths, hq_qvs, lq_qvs = [], [], []
    for k, ds in enumerate([ds_hq, ds_lq]):
        for rec in ds:
            readlengths.append(float(rec.qLen))
            if ds is ds_hq:
                hq_qvs.append(rec.readScore)
            else:
                lq_qvs.append(rec.readScore)
    readlengths = np.array(readlengths)
    avgqvs = np.array(hq_qvs + lq_qvs)
    # Plot read length histogram
    readlength_plot = create_readlength_plot(readlengths, output_dir)
    readlength_group = PlotGroup(Constants.PG_READLENGTH,
                                 plots=[readlength_plot],
                                 thumbnail=readlength_plot.thumbnail)
    # Plot average qv histogram
    avgqv_plot = create_avgqv_plot(avgqvs, output_dir)
    avgqv_group = PlotGroup(Constants.PG_AVGQV,
                            plots=[avgqv_plot],
                            thumbnail=avgqv_plot.thumbnail)
    attributes = [
        Attribute(Constants.A_N_HQ_ID, value=len(ds_hq)),
        Attribute(Constants.A_N_LQ_ID, value=len(ds_lq))
    ]
    report = Report(Constants.R_ID,
                    attributes=attributes,
                    plotgroups=[readlength_group, avgqv_group],
                    dataset_uuids=[ds_hq.uuid, ds_lq.uuid])
    return spec.apply_view(report)


def _run(hq_transcripts_file, lq_transcripts_file, json_report, output_dir):
    if output_dir in ["", None]:
        output_dir = os.getcwd()
    report = make_report(
        hq_transcripts_file=hq_transcripts_file,
        lq_transcripts_file=lq_transcripts_file,
        output_dir=output_dir)
    log.info(pformat(report.to_dict()))
    report.write_json(json_report)
    return 0


def _args_runner(args):
    return _run(
        hq_transcripts_file=args.hq_transcripts,
        lq_transcripts_file=args.lq_transcripts,
        json_report=args.outJson,
        output_dir=os.path.dirname(args.outJson))


def _resolved_tool_contract_runner(rtc):
    return _run(
        hq_transcripts_file=rtc.task.input_files[0],
        lq_transcripts_file=rtc.task.input_files[1],
        json_report=rtc.task.output_files[0],
        output_dir=os.path.dirname(rtc.task.output_files[0]))


def _get_parser():
    p = get_pbparser(
        Constants.TOOL_ID,
        __version__,
        "Iso-Seq Report",
        __doc__,
        Constants.DRIVER_EXE,
        is_distributed=True)
    p.add_input_file_type(
        FileTypes.DS_TRANSCRIPT,
        "hq_transcripts",
        "Clustered high-quality transcripts",
        description="Clustered transcripts from 'sierra' in BAM dataset format")
    p.add_input_file_type(
        FileTypes.DS_TRANSCRIPT,
        "lq_transcripts",
        "Clustered low-quality transcripts",
        description="Clustered transcripts from 'sierra' in BAM dataset format")
    p.add_output_file_type(
        FileTypes.REPORT,
        "outJson",
        "Transcript Clustering Report",
        description="Summary of results from pbtranscript",
        default_name="isoseq3_report")
    return p


def main(argv=sys.argv):
    return pbparser_runner(argv[1:],
                           _get_parser(),
                           _args_runner,
                           _resolved_tool_contract_runner,
                           log,
                           setup_log)

if __name__ == '__main__':
    sys.exit(main())
