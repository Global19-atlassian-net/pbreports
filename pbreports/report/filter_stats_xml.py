
"""
Generates:
 - Filter ReadLength histograms with SDF (with thumbnails)
 - Filter ReadScore Histogram with SDF (with thumbnails)
 - Table of total bases, # of reads, mean readlengh, mean
   readscore
"""

from collections import OrderedDict
import functools
import logging
import os
import sys

import numpy as np

from pbcommand.utils import setup_log
from pbcommand.models.report import (Report, Table, Column, Plot, Attribute,
                                     PlotGroup)
from pbcommand.models import TaskTypes, FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.common_options import add_debug_option
from pbcore.io import SubreadSet

from pbreports.plot.helper import (get_fig_axes_lpr,
                                   save_figure_with_thumbnail, get_green)
from pbreports.util import compute_n50, continuous_dist_shaper

__version__ = '0.1.0'


class Constants(object):
    TOOL_ID = "pbreports.tasks.filter_stats_report_xml"
    DRIVER_EXE = ("python -m pbreports.report.filter_stats_xml "
                  "--resolved-tool-contract ")

    A_NBASES = "nbases"
    A_NREADS = "nreads"
    A_READ_N50 = "read_n50"
    A_READ_LENGTH = "read_length"
    A_READ_QUALITY = "read_quality"
    A_SUBREAD_NBASES = "nbases_subreads"
    A_NSUBREADS = "nsubreads"
    A_SUBREAD_N50 = "subread_50"
    A_SUBREAD_LENGTH = "subread_length"
    A_SUBREAD_QUALITY = "subread_quality"

    ATTR_LABELS = OrderedDict([
        (A_NBASES, "Polymerase Read Bases"),
        (A_NREADS, "Polymerase Reads"),
        (A_READ_N50, "Polymerase Read N50"),
        (A_READ_LENGTH, "Polymerase Read Length"),
        (A_READ_QUALITY, "Polymerase Read Quality"),
        (A_SUBREAD_NBASES, "Subread Bases"),
        (A_NSUBREADS, "Subreads"),
        (A_SUBREAD_N50, "Subread N50"),
        (A_SUBREAD_LENGTH, "Subread Length"),
        (A_SUBREAD_QUALITY, "Subread Quality")
    ])
    READ_ATTR = [A_NBASES, A_NREADS, A_READ_N50, A_READ_LENGTH, A_READ_QUALITY]
    SUBREAD_ATTR = [A_SUBREAD_NBASES, A_NSUBREADS, A_SUBREAD_N50,
                    A_SUBREAD_LENGTH, A_SUBREAD_QUALITY]

class ReadStatsPlots(object):
    P_LENGTH = "filter_len_xml_plot"
    P_LENGTH_PREFIX = "readLenDist"
    P_LENGTH_X_AXIS = Constants.A_READ_LENGTH
    P_QUAL_X_AXIS = Constants.A_READ_QUALITY
    P_Y_AXIS = Constants.A_NREADS
    P_QUAL = "filter_qual_xml_plot"
    P_QUAL_PREFIX = "readQualDist"
    PG_LENGTH = "filter_len_xml_plot_group"
    PG_QUAL = "filter_qual_xml_plot_group"

class SubreadStatsPlots(object):
    P_LENGTH_PREFIX = "subreadLenDist"
    P_LENGTH = "filter_subread_len_xml_plot"
    P_LENGTH_X_AXIS = Constants.A_SUBREAD_LENGTH
    P_QUAL_X_AXIS = Constants.A_SUBREAD_QUALITY
    P_Y_AXIS = Constants.A_NSUBREADS
    P_QUAL = "filter_subread_qual_xml_plot"
    P_QUAL_PREFIX = "subreadQualDist"
    PG_LENGTH = "filter_subread_len_xml_plot_group"
    PG_QUAL = "filter_subread_qual_xml_plot_group"


log = logging.getLogger(__name__)


def _total_from_bins(bins, min_val, bin_width):
    _min = min_val
    _wid = bin_width
    bin_means = [_min + (_wid * i) + _wid / 2 for i in range(len(bins))]
    bin_totals = [count * mean for count, mean in zip(bins, bin_means)]
    return sum(bin_totals)


def _to_read_stats_attributes(readLenDists, readQualDists, read_attr):
    # Build the stats table:
    nbases = 0
    nreads = 0
    n50 = 0
    readscoretotal = 0
    readscorenumber = 0
    approx_read_lens = []

    # if a merge failed there may be more than one dist:
    for rlendist in readLenDists:
        nbases += _total_from_bins(rlendist.bins,
                                   rlendist.minBinValue,
                                   rlendist.binWidth)
        nreads += sum(rlendist.bins)

        # N50:
        for i, lbin in enumerate(rlendist.bins):
            # use the average, except for the last bin
            if i != len(rlendist.bins) - 1:
                value = ((i * rlendist.binWidth) + rlendist.minBinValue +
                         rlendist.binWidth / 2)
            # for the last bin, just use the value
            else:
                value = (i * rlendist.binWidth) + rlendist.minBinValue
            approx_read_lens.extend([value] * lbin)
            # TODO(mdsmith)(2016-02-09) make sure maxOutlierValue is updated
            # during a merge /todo
            # but pop off that last value and replace it with the
            # maxOutlierValue:
            # approx_read_lens.pop()
            # approx_read_lens.append(rlendist.maxBinValue)
    n50 = int(np.round(compute_n50(approx_read_lens), decimals=0))
    for rqualdist in readQualDists:
        readscoretotal += _total_from_bins(rqualdist.bins,
                                           rqualdist.minBinValue,
                                           rqualdist.binWidth)
        readscorenumber += sum(rqualdist.bins)

    readlen = 0
    if nreads != 0:
        readlen = int(np.round(nbases / nreads, decimals=0))
    readQuality = 0
    if readscorenumber != 0:
        readQuality = np.round(readscoretotal / readscorenumber, decimals=2)
    _pre_filter = [int(np.round(nbases, decimals=0)),
                   nreads,
                   n50,
                   readlen,
                   readQuality]
    assert len(read_attr) == len(_pre_filter)
    attr = []
    for attr_id, value in zip(read_attr, _pre_filter):
        attr.append(Attribute(attr_id, value=value,
                              name=Constants.ATTR_LABELS[attr_id]))
    return attr


def _to_read_stats_plots(PlotConstants, readLenDists, readQualDists, output_dir,
                         dpi=72):
    length_plots = []
    # ReadLen distribution to barplot:
    shaper = continuous_dist_shaper(readLenDists)
    for i, orig_rlendist in enumerate(readLenDists):
        rlendist = shaper(orig_rlendist)
        len_fig, len_axes = get_fig_axes_lpr()
        len_axes.bar(rlendist.labels, rlendist.bins,
                     color=get_green(0), edgecolor=get_green(0),
                     width=(rlendist.binWidth * 0.75))
        len_axes.set_xlabel(Constants.ATTR_LABELS[PlotConstants.P_LENGTH_X_AXIS])
        len_axes.set_ylabel(Constants.ATTR_LABELS[PlotConstants.P_Y_AXIS])
        png_fn = os.path.join(output_dir, "{p}{i}.png".format(i=i,
            p=PlotConstants.P_LENGTH_PREFIX))
        png_base, thumbnail_base = save_figure_with_thumbnail(len_fig, png_fn,
                                                              dpi=dpi)
        length_plots.append(
            Plot("{p}_{i}".format(i=i, p=PlotConstants.P_LENGTH),
                 os.path.relpath(png_base, output_dir),
                 thumbnail=os.path.relpath(thumbnail_base, output_dir)))
    plot_groups = [
        PlotGroup(PlotConstants.PG_LENGTH,
                  title=Constants.ATTR_LABELS[PlotConstants.P_LENGTH_X_AXIS],
                  plots=length_plots,
                  thumbnail=os.path.relpath(thumbnail_base, output_dir))
    ]

    qual_plots = []
    # ReadQual distribution to barplot:
    shaper = continuous_dist_shaper(readQualDists)
    for i, orig_rqualdist in enumerate(readQualDists):
        rqualdist = shaper(orig_rqualdist)
        qual_fig, qual_axes = get_fig_axes_lpr()
        qual_axes.bar(rqualdist.labels, rqualdist.bins,
                      color=get_green(0), edgecolor=get_green(0),
                      width=(rqualdist.binWidth * 0.75))
        qual_axes.set_xlabel(Constants.ATTR_LABELS[PlotConstants.P_QUAL_X_AXIS])
        qual_axes.set_ylabel(Constants.ATTR_LABELS[PlotConstants.P_Y_AXIS])
        png_fn = os.path.join(output_dir, "{p}{i}.png".format(i=i,
            p=PlotConstants.P_QUAL_PREFIX))
        png_base, thumbnail_base = save_figure_with_thumbnail(qual_fig, png_fn,
                                                              dpi=dpi)
        qual_plots.append(
            Plot("{p}_{i}".format(i=i, p=PlotConstants.P_QUAL),
                 os.path.relpath(png_base, output_dir),
                 thumbnail=os.path.relpath(thumbnail_base, output_dir)))
    plot_groups.append(
        PlotGroup(PlotConstants.PG_QUAL,
                  title=Constants.ATTR_LABELS[PlotConstants.P_QUAL_X_AXIS],
                  plots=qual_plots))
    return plot_groups

to_read_stats_plots = functools.partial(_to_read_stats_plots, ReadStatsPlots)
to_subread_stats_plots = functools.partial(_to_read_stats_plots,
                                           SubreadStatsPlots)


def to_report(stats_xml, output_dir, dpi=72):
    """Main point of entry

    :type stats_xml: str
    :type output_dir: str
    :type dpi: int

    :rtype: Report
    """
    log.info("Analyzing XML {f}".format(f=stats_xml))
    # stats_xml should be a dataset:
    dset = SubreadSet(stats_xml)
    dataset_uuids = [dset.uuid]
    # but if it isn't, no problem:
    if not dset.metadata.summaryStats:
        dset.loadStats(stats_xml)
        # an sts file was provided which will generate a new random uuid
        dataset_uuids = []
    if not dset.metadata.summaryStats.readLenDists:
        raise IOError("Pipeline Summary Stats (sts.xml) not found or missing "
                      "key distributions")

    attr = _to_read_stats_attributes(
        readLenDists=dset.metadata.summaryStats.readLenDists,
        readQualDists=dset.metadata.summaryStats.readQualDists,
        read_attr=Constants.READ_ATTR)
    attr.extend(_to_read_stats_attributes(
        readLenDists=dset.metadata.summaryStats.insertReadLenDists,
        readQualDists=dset.metadata.summaryStats.insertReadQualDists,
        read_attr=Constants.SUBREAD_ATTR))

    plot_groups = to_read_stats_plots(
        readLenDists=dset.metadata.summaryStats.readLenDists,
        readQualDists=dset.metadata.summaryStats.readQualDists,
        output_dir=output_dir)
    plot_groups.extend(to_subread_stats_plots(
        readLenDists=dset.metadata.summaryStats.insertReadLenDists,
        readQualDists=dset.metadata.summaryStats.insertReadQualDists,
        output_dir=output_dir))

    # build the report:
    report = Report("filtering_stats_xml_report",
                    title="Filtering stats XML report",
                    attributes=attr,
                    plotgroups=plot_groups,
                    dataset_uuids=dataset_uuids)

    return report


def args_runner(args):
    log.info("Starting {f} v{v}".format(f=os.path.basename(__file__),
                                        v=__version__))
    output_dir = os.path.dirname(args.report)
    report = to_report(args.subread_set, output_dir)
    report.write_json(args.report)
    return 0


def resolved_tool_contract_runner(resolved_tool_contract):
    rtc = resolved_tool_contract
    log.info("Starting {f} v{v}".format(f=os.path.basename(__file__),
                                        v=__version__))
    output_dir = os.path.dirname(rtc.task.output_files[0])
    report = to_report(rtc.task.input_files[0], output_dir)
    report.write_json(rtc.task.output_files[0])
    return 0


def _add_options_to_parser(p):
    p.add_input_file_type(
        FileTypes.DS_SUBREADS,
        file_id="subread_set",
        name="SubreadSet",
        description="SubreadSet")
    p.add_output_file_type(
        FileTypes.REPORT, "report", "JSON report",
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
        "Filtering Statistics XML Report",
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


# for 'python -m pbreports.report.sat ...'
if __name__ == "__main__":
    sys.exit(main())
