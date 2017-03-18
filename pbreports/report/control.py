import os
import os.path as op
import logging
import sys
import numpy as np
import functools

from pbcommand.models.report import Report, Table, Column, Plot, PlotGroup, Attribute
from pbcommand.models import TaskTypes, FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.common_options import add_debug_option
from pbcommand.utils import setup_log
from pbcore.io import SubreadSet
from pbreports.plot.helper import (get_fig_axes_lpr, get_green,
                                   save_figure_with_thumbnail)
from pbreports.model import InvalidStatsError
from pbreports.io.specs import *
from pbreports.util import _cont_dist_shaper, dist_shaper

__version__ = '0.1.0'


class Constants(object):
    TOOL_ID = "pbreports.tasks.control_report"
    DRIVER_EXE = ("python -m pbreports.report.control "
                  "--resolved-tool-contract ")
    R_ID = "control"
    A_NREADS = "reads_n"
    A_READLENGTH_MEAN = "readlength_mean"
    A_CONCORDANCE_MEAN = "concordance_mean"
    A_CONCORDANCE_MODE = "concordance_mode"
    
    P_READLENGTH = "readlength_plot"
    PG_READLENGTH = "readlength_plotgroup"
    P_CONCORDANCE = "concordance_plot"
    PG_CONCORDANCE = "concordance_plotgroup"
    

log = logging.getLogger(__name__)
spec = load_spec(Constants.R_ID)


def to_nreads(readlen_dist):
    nreads = int(readlen_dist.sampleSize)
    attribute = Attribute(Constants.A_NREADS, nreads)
    return attribute

def to_readlength_mean(readlen_dist):
    readlength_mean = float(readlen_dist.sampleMean)
    attribute = Attribute(Constants.A_READLENGTH_MEAN, readlength_mean)
    return attribute

def to_concordance_mean(readqual_dist):
    concordance_mean = float(readqual_dist.sampleMean)
    attribute = Attribute(Constants.A_CONCORDANCE_MEAN, concordance_mean)
    return attribute

def to_concordance_mode(readqual_dist):
    concordance_mode = float(89.1)
    attribute = Attribute(Constants.A_CONCORDANCE_MODE, concordance_mode)
    return attribute

def to_attributes(readlen_dist, readqual_dist):
    attributes = []
    attributes.append(to_nreads(readlen_dist))
    attributes.append(to_readlength_mean(readlen_dist))
    attributes.append(to_concordance_mean(readqual_dist))
    attributes.append(to_concordance_mode(readqual_dist))
    return attributes

def reshape(readlen_dist, edges, heights):
    lenDistShaper = functools.partial(_cont_dist_shaper, dist_shaper([(heights, edges)], nbins=40, trim_excess=False))
    readlen_dist = lenDistShaper(readlen_dist)
    nbins = int(readlen_dist.numBins)
    bin_counts = readlen_dist['BinCounts']
    heights = readlen_dist.bins
    bin_width = float(readlen_dist.binWidth)
    edges = [float(bn)*bin_width for bn in xrange(nbins)]
    return edges, heights, bin_width

def to_readlen_plotgroup(readlen_dist, output_dir):
    plot_name = get_plot_title(spec, Constants.PG_READLENGTH, Constants.P_READLENGTH)
    x_label = get_plot_xlabel(spec, Constants.PG_READLENGTH, Constants.P_READLENGTH)
    y_label = get_plot_ylabel(spec, Constants.PG_READLENGTH, Constants.P_READLENGTH)
    nbins = int(readlen_dist.numBins)
    bin_counts = readlen_dist['BinCounts']
    heights = readlen_dist.bins
    bin_width = float(readlen_dist.binWidth)
    edges = [float(bn)*bin_width for bn in xrange(nbins)]
    edges, heights, bin_width = reshape(readlen_dist, edges, heights)
    fig, ax = get_fig_axes_lpr()
    ax.bar(edges, heights, color=get_green(0), edgecolor=get_green(0), width=(bin_width * 0.75))
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    png_fn = os.path.join(output_dir, "{p}.png".format(p=Constants.P_READLENGTH))
    png_base, thumbnail_base = save_figure_with_thumbnail(fig, png_fn, dpi = 72)
    readlen_plot = Plot(Constants.P_READLENGTH,
                   os.path.relpath(png_base, output_dir),
                   title=plot_name, caption=plot_name,
                   thumbnail=os.path.relpath(thumbnail_base, output_dir))
    plot_groups = [PlotGroup(Constants.PG_READLENGTH, plots=[readlen_plot])]
    return plot_groups

def to_concordance_plotgroup(readqual_dist, output_dir):
    plot_name = get_plot_title(spec, Constants.PG_CONCORDANCE, Constants.P_CONCORDANCE)
    x_label = get_plot_xlabel(spec, Constants.PG_CONCORDANCE, Constants.P_CONCORDANCE)
    y_label = get_plot_ylabel(spec, Constants.PG_CONCORDANCE, Constants.P_CONCORDANCE)
    nbins = int(readqual_dist.numBins)
    bin_counts = readqual_dist['BinCounts']
    heights = readqual_dist.bins
    edges = [float(bn)/float(nbins) for bn in xrange(nbins)]
    bin_width = float(readqual_dist.binWidth)
    fig, ax = get_fig_axes_lpr()
    ax.bar(edges, heights, color=get_green(0), edgecolor=get_green(0), width=(bin_width * 0.75))
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    png_fn = os.path.join(output_dir, "{p}.png".format(p=Constants.P_CONCORDANCE))
    png_base, thumbnail_base = save_figure_with_thumbnail(fig, png_fn, dpi = 72)
    concordance_plot = Plot(Constants.P_CONCORDANCE,
                   os.path.relpath(png_base, output_dir),
                   title=plot_name, caption=plot_name,
                   thumbnail=os.path.relpath(thumbnail_base, output_dir))
    plot_groups = [PlotGroup(Constants.PG_CONCORDANCE, plots=[concordance_plot])]
    return plot_groups

def to_plotgroups(readlen_dist, readqual_dist, output_dir):
    plotgroups = []
    plotgroups.extend(to_readlen_plotgroup(readlen_dist, output_dir))
    plotgroups.extend(to_concordance_plotgroup(readqual_dist, output_dir))
    return plotgroups

def to_report(stats_xml, output_dir):
    log.info("Analyzing XML {f}".format(f=stats_xml))
    dset = SubreadSet(stats_xml)
    dset.loadStats()
    if stats_xml.endswith(".sts.xml"):
        dset.loadStats(stats_xml)
    if not dset.metadata.summaryStats.controlReadLenDist:
        raise InvalidStatsError("Control Read Length Distribution not found")
    if not dset.metadata.summaryStats.controlReadQualDist:
        raise InvalidStatsError("Control Read Quality Distribution not found")
    
    readlen_dist = dset.metadata.summaryStats.controlReadLenDist
    readqual_dist = dset.metadata.summaryStats.controlReadQualDist

    attributes = to_attributes(readlen_dist, readqual_dist)
    plotgroups = to_plotgroups(readlen_dist, readqual_dist, output_dir)
   
    report = Report(Constants.R_ID, attributes=attributes, plotgroups=plotgroups)

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
        FileTypes.DS_SUBREADS,
        file_id="subread_set",
        name="SubreadSet",
        description="SubreadSet")
    p.add_output_file_type(FileTypes.REPORT, "report", spec.title,
                           description=("Filename of JSON output report. Should be name only, "
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
        "Control Report",
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
