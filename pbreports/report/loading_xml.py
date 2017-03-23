
"""
Generate XML report on ZMW loading and productivity.
"""

import functools
import logging
import os
import sys

import numpy as np

from pbcommand.models.report import Report, Table, Column, Plot, PlotGroup
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log
from pbcore.io import SubreadSet

from pbreports.plot.helper import (get_fig_axes_lpr, get_green,
                                   save_figure_with_thumbnail)
from pbreports.model import InvalidStatsError
from pbreports.util import (get_subreads_report_parser,
                            arg_runner_subreads_report,
                            rtc_runner_subreads_report)
from pbreports.io.specs import *

__version__ = '0.1.0'


class Constants(object):
    TOOL_ID = "pbreports.tasks.loading_report_xml"
    DRIVER_EXE = ("python -m pbreports.report.loading_xml "
                  "--resolved-tool-contract ")
    R_ID = "loading_xml_report"
    T_LOADING = "loading_xml_table"
    C_CONTEXT = "collection_context"
    C_ZMWS = "productive_zmws"
    C_PROD_0_N = "productivity_0_n"
    C_PROD_0_PCT = "productivity_0_pct"
    C_PROD_1_N = "productivity_1_n"
    C_PROD_1_PCT = "productivity_1_pct"
    C_PROD_2_N = "productivity_2_n"
    C_PROD_2_PCT = "productivity_2_pct"
    C_LOADING_TYPE = "loading_type"
    DECIMALS = 3

    P_RRL = "raw_read_length_plot"
    PG_RRL = "raw_read_length_plot_group"
    P_HQ = "hq_hist_plot"
    PG_HQ = "hq_hist_plot_group"


log = logging.getLogger(__name__)
spec = load_spec(Constants.R_ID)


def to_hq_hist_plot(hqbasefraction_dist, output_dir):
    plot_name = get_plot_title(spec, Constants.PG_HQ, Constants.P_HQ)
    x_label = get_plot_xlabel(spec, Constants.PG_HQ, Constants.P_HQ)
    y_label = get_plot_ylabel(spec, Constants.PG_HQ, Constants.P_HQ)
    nbins = int(hqbasefraction_dist['NumBins'].metavalue)
    bin_counts = hqbasefraction_dist['BinCounts']
    heights = [int(bc.metavalue) for bc in bin_counts]
    edges = [float(bn) / float(nbins) for bn in xrange(nbins)]
    bin_width = float(hqbasefraction_dist['BinWidth'].metavalue)
    fig, ax = get_fig_axes_lpr()
    ax.bar(edges, heights, color=get_green(0),
           edgecolor=get_green(0), width=(bin_width * 0.75))
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    png_fn = os.path.join(output_dir, "{p}.png".format(p=Constants.P_HQ))
    png_base, thumbnail_base = save_figure_with_thumbnail(fig, png_fn, dpi=72)
    hq_plot = Plot(Constants.P_HQ,
                   os.path.relpath(png_base, output_dir),
                   title=plot_name, caption=plot_name,
                   thumbnail=os.path.relpath(thumbnail_base, output_dir))
    plot_groups = [PlotGroup(Constants.PG_HQ, plots=[hq_plot])]
    return plot_groups


def expand_data(bin_counts, max_val):
    nbins = len(bin_counts)
    midpoints = [max_val * (float(bn + 0.5) / float(nbins))
                 for bn in xrange(nbins)]
    data = []
    for i in xrange(nbins):
        data.extend([midpoints[i]] * bin_counts[i])
    return data


def to_rl_overlay_plot(numunfilteredbasecalls_dist, readlen_dist, output_dir):
    plot_name = get_plot_title(spec, Constants.PG_RRL, Constants.P_RRL)
    x_label = get_plot_xlabel(spec, Constants.PG_RRL, Constants.P_RRL)
    y_label = get_plot_ylabel(spec, Constants.PG_RRL, Constants.P_RRL)
    unfiltered_bins = [int(bc.metavalue)
                       for bc in numunfilteredbasecalls_dist['BinCounts']]
    poly_bins = [int(bc.metavalue) for bc in readlen_dist['BinCounts']]
    max_unfiltered = len(unfiltered_bins) * \
        int(numunfilteredbasecalls_dist['BinWidth'].metavalue)
    max_poly = len(poly_bins) * int(readlen_dist['BinWidth'].metavalue)
    unfiltered_data = expand_data(unfiltered_bins, max_unfiltered)
    poly_data = expand_data(poly_bins, max_poly)
    fig, ax = get_fig_axes_lpr()
    ax.hist(unfiltered_data, label="Unfiltered", histtype='stepfilled',
            alpha=0.3, bins=len(unfiltered_bins), range=[0, max_unfiltered])
    ax.hist(poly_data, label="Polymerase", histtype='stepfilled',
            alpha=0.3, bins=len(poly_bins), range=[0, max_poly])
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    png_fn = os.path.join(output_dir, "{p}.png".format(p=Constants.P_RRL))
    png_base, thumbnail_base = save_figure_with_thumbnail(fig, png_fn, dpi=72)
    rrl_plot = Plot(Constants.P_RRL,
                    os.path.relpath(png_base, output_dir),
                    title=plot_name, caption=plot_name,
                    thumbnail=os.path.relpath(thumbnail_base, output_dir))
    plot_groups = [PlotGroup(Constants.PG_RRL, plots=[rrl_plot])]
    return plot_groups


def to_report(stats_xml, output_dir):
    """Main point of entry

    :type stats_xml: str
    :type output_dir: str
    :type dpi: int

    :rtype: Report
    """
    log.info("Analyzing XML {f}".format(f=stats_xml))
    dset = SubreadSet(stats_xml)
    dset.loadStats()
    if stats_xml.endswith(".sts.xml"):
        dset.loadStats(stats_xml)
    if not dset.metadata.summaryStats.prodDist:
        raise InvalidStatsError("Pipeline Summary Stats (sts.xml) not found "
                                "or missing key distributions")

    readlen_dist = dset.metadata.summaryStats.getDist(
        'ReadLenDist', unwrap=False)[0]
    numunfilteredbasecalls_dist = dset.metadata.summaryStats.getDist(
        'NumUnfilteredBasecallsDist', unwrap=False)[0]
    hqbasefraction_dist = dset.metadata.summaryStats.getDist(
        'HqBaseFractionDist', unwrap=False)[0]

    dsets = [dset]
    for subdset in dset.subdatasets:
        if subdset.metadata.summaryStats:
            dsets.append(subdset)

    col_ids = [Constants.C_CONTEXT,
               Constants.C_ZMWS,
               Constants.C_PROD_0_N,
               Constants.C_PROD_0_PCT,
               Constants.C_PROD_1_N,
               Constants.C_PROD_1_PCT,
               Constants.C_PROD_2_N,
               Constants.C_PROD_2_PCT,
               Constants.C_LOADING_TYPE]

    col_values = [[], [], [], [], [], [], [], [], []]
    for dset in dsets:
        loading_type = movie_name = "NA"
        if len(dsets) > 1 and len(col_values[0]) == 0:
            movie_name = "Combined"
        else:
            try:
                collection = list(dset.metadata.collections)[0]
                movie_name = collection.context
                loading_type = collection.automation.name
            except (IndexError, AttributeError) as e:
                log.warn(e)

        productive_zmws = int(dset.metadata.summaryStats.numSequencingZmws)
        empty, productive, other, _ = dset.metadata.summaryStats.prodDist.bins

        prod0 = np.round(100.0 * empty / float(productive_zmws),
                         decimals=Constants.DECIMALS)
        prod1 = np.round(100.0 * productive / float(productive_zmws),
                         decimals=Constants.DECIMALS)
        prod2 = np.round(100.0 * other / float(productive_zmws),
                         decimals=Constants.DECIMALS)
        this_row = [movie_name, productive_zmws, empty, prod0,
                    productive, prod1, other, prod2, loading_type]
        map(lambda (x, y): x.append(y), zip(col_values, this_row))
    columns = [Column(cid, values=vals)
               for cid, vals in zip(col_ids, col_values)]
    tables = [Table(Constants.T_LOADING, columns=columns)]

    plot_groups = []
    plot_groups.extend(to_hq_hist_plot(
        hqbasefraction_dist=hqbasefraction_dist,
        output_dir=output_dir))
    plot_groups.extend(to_rl_overlay_plot(
        numunfilteredbasecalls_dist=numunfilteredbasecalls_dist,
        readlen_dist=readlen_dist,
        output_dir=output_dir))

    report = Report(Constants.R_ID,
                    tables=tables, attributes=None, plotgroups=plot_groups)
    return spec.apply_view(report)


resolved_tool_contract_runner = functools.partial(rtc_runner_subreads_report,
                                                  to_report)
args_runner = functools.partial(arg_runner_subreads_report, to_report)


def main(argv=sys.argv):
    mp = get_subreads_report_parser(Constants.TOOL_ID, __version__, spec.title,
                                    __doc__, Constants.DRIVER_EXE)
    return pbparser_runner(argv[1:],
                           mp,
                           args_runner,
                           resolved_tool_contract_runner,
                           log,
                           setup_log)


# for 'python -m pbreports.report.sat ...'
if __name__ == "__main__":
    sys.exit(main())
