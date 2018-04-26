
# TODO(nechols)(2016-04-22) rename this to raw_data_report or similar

"""
Generates:
 - Filter ReadLength histograms with SDF (with thumbnails)
 - Filter ReadScore Histogram with SDF (with thumbnails)
 - Table of total bases, # of reads, mean readlengh, mean
   readscore
"""

import functools
import logging
import os
import sys

import numpy as np

from pbcommand.utils import setup_log
from pbcommand.models.report import Report, Plot, Attribute, PlotGroup
from pbcommand.cli import pbparser_runner
from pbcore.io import SubreadSet

from pbreports.plot.helper import DEFAULT_DPI
from pbreports.plot.tools import plot_stats_xml_distribution, plot_subread_lengths
from pbreports.util import (compute_n50, continuous_dist_shaper,
                            get_subreads_report_parser,
                            arg_runner_subreads_report,
                            rtc_runner_subreads_report)
from pbreports.io.specs import *
from pbreports.model import InvalidStatsError

__version__ = '0.1.0'


class Constants(object):
    TOOL_ID = "pbreports.tasks.filter_stats_report_xml"
    DRIVER_EXE = ("python -m pbreports.report.filter_stats_xml "
                  "--resolved-tool-contract ")
    R_ID = "raw_data_report"

    A_NBASES = "nbases"
    A_NREADS = "nreads"
    A_READ_N50 = "read_n50"
    A_READ_LENGTH = "read_length"
    A_SUBREAD_LENGTH = "subread_length"
    A_SUBREAD_N50 = "subread_n50"
#    A_READ_QUALITY = "read_quality"
    A_INSERT_LENGTH = "insert_length"
    A_INSERT_N50 = "insert_n50"
#    A_INSERT_QUALITY = "insert_quality"

    READ_ATTR = [A_NBASES, A_NREADS, A_READ_LENGTH, A_READ_N50]
    INSERT_ATTR = [A_INSERT_LENGTH, A_INSERT_N50]
    PG_RL = "read_length_plot_group"
    P_RL = "read_length_plot"
    PG_IL = "insert_length_plot_group"
    P_IL = "insert_length_plot"
    PG_SRL = "subread_length_plot_group"
    P_SRL = "subread_length_plot"


class ReadStatsPlots(object):
    P_LENGTH = "read_length_plot"
    P_LENGTH_PREFIX = "readLenDist"
    P_QUAL = "read_quality_plot"
    P_QUAL_PREFIX = "readQualDist"
    PG_LENGTH = "read_length_plot_group"
    PG_QUAL = "read_quality_plot_group"


class InsertStatsPlots(object):
    P_LENGTH_PREFIX = "insertLenDist"
    P_LENGTH = "insert_length_plot"
    P_QUAL = "insert_quality_plot"
    P_QUAL_PREFIX = "insertQualDist"
    PG_LENGTH = "insert_length_plot_group"
    PG_QUAL = "insert_quality_plot_group"


log = logging.getLogger(__name__)
spec = load_spec(Constants.R_ID)


def _total_from_bins(bins, min_val, bin_width):
    _min = min_val
    _wid = bin_width
    bin_means = [_min + (_wid * i) + _wid / 2 for i in range(len(bins))]
    bin_totals = [count * mean for count, mean in zip(bins, bin_means)]
    return sum(bin_totals)


def _to_read_stats_attributes(readLenDists, readQualDists):
    # Build the stats table:
    nbases = 0
    nreads = 0
    n50 = 0
    readscoretotal = 0
    readscorenumber = 0
    approx_read_lens = []

    # if a merge failed there may be more than one dist:
    for rlendist in readLenDists:
        nbases += rlendist.sampleMean * rlendist.sampleSize
        nreads += rlendist.sampleSize

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
        readlen = nbases / nreads
    readlen = int(np.round(readlen, decimals=0))
    readQuality = 0
    if readscorenumber != 0:
        readQuality = readscoretotal / readscorenumber
    return [int(np.round(nbases, decimals=0)),
            nreads,
            readlen,
            n50,
            ]  # readQuality]


def _make_attributes(read_attr, attr_values):
    assert len(read_attr) == len(attr_values)
    return [Attribute(attr_id, value=value)
            for attr_id, value in zip(read_attr, attr_values)]


def to_read_stats_attributes(readLenDists, readQualDists):
    return _make_attributes(
        read_attr=Constants.READ_ATTR,
        attr_values=_to_read_stats_attributes(readLenDists, readQualDists))


# just Insert Length and N50
def to_insert_stats_attributes(readLenDists, readQualDists):
    values = _to_read_stats_attributes(readLenDists, readQualDists)
    readlen = values[2]
    n50 = values[3]
    return _make_attributes(
        read_attr=Constants.INSERT_ATTR,
        attr_values=[readlen, n50])


def _to_read_stats_plots(PlotConstants, title, readLenDists, readQualDists,
                         output_dir, dpi=DEFAULT_DPI, lenDistShaper=None):
    length_plots = []
    # ReadLen distribution to barplot:
    if lenDistShaper is None:
        lenDistShaper = continuous_dist_shaper(readLenDists, trim_excess=True)
    for i, orig_rlendist in enumerate(readLenDists):
        rlendist = lenDistShaper(orig_rlendist)
        assert sum(orig_rlendist.bins) == sum(rlendist.bins)
        png_fn = os.path.join(output_dir, "{p}{i}.png".format(i=i,
                                                              p=PlotConstants.P_LENGTH_PREFIX))
        png_base, thumbnail_base = plot_stats_xml_distribution(
            rlendist,
            get_plot_xlabel(spec, PlotConstants.PG_LENGTH,
                            PlotConstants.P_LENGTH),
            get_plot_ylabel(spec, PlotConstants.PG_LENGTH,
                            PlotConstants.P_LENGTH),
            png_fn,
            dpi=dpi)
        length_plots.append(
            Plot("{p}_{i}".format(i=i, p=PlotConstants.P_LENGTH),
                 os.path.relpath(png_base, output_dir),
                 title=title, caption=title,
                 thumbnail=os.path.relpath(thumbnail_base, output_dir)))

    plot_group_thumb = length_plots[-1].thumbnail if length_plots else None

    plot_groups = [
        PlotGroup(PlotConstants.PG_LENGTH,
                  title=title,
                  plots=length_plots,
                  thumbnail=plot_group_thumb)
    ]
    return plot_groups

    # FIXME these aren't useful yet
    qual_plots = []
    # ReadQual distribution to barplot:
    shaper = continuous_dist_shaper(readQualDists, trim_excess=True)
    for i, orig_rqualdist in enumerate(readQualDists):
        rqualdist = shaper(orig_rqualdist)
        png_fn = os.path.join(output_dir, "{p}{i}.png".format(i=i,
                                                              p=PlotConstants.P_QUAL_PREFIX))
        png_base, thumbnail_base = plot_stats_xml_distribution(
            rqualdist,
            get_plot_xlabel(spec, PlotConstants.PG_QUAL, PlotConstants.P_QUAL),
            get_plot_ylabel(spec, PlotConstants.PG_QUAL, PlotConstants.P_QUAL),
            png_fn,
            dpi=dpi)
        qual_plots.append(
            Plot("{p}_{i}".format(i=i, p=PlotConstants.P_QUAL),
                 os.path.relpath(png_base, output_dir),
                 thumbnail=os.path.relpath(thumbnail_base, output_dir)))
    plot_groups.append(
        PlotGroup(PlotConstants.PG_QUAL,
                  plots=qual_plots))
    return plot_groups

to_read_stats_plots = functools.partial(_to_read_stats_plots, ReadStatsPlots,
                                        get_plotgroup_title(spec, Constants.PG_RL))
to_insert_stats_plots = functools.partial(_to_read_stats_plots, InsertStatsPlots,
                                          get_plotgroup_title(spec, Constants.PG_IL))


def to_subread_lengths_plot(dset, output_dir):
    png_file_name = op.join(output_dir, "subread_lengths.png")
    png, thumb = plot_subread_lengths(dset, png_file_name)
    return PlotGroup(Constants.PG_SRL,
        plots=[Plot(Constants.P_SRL,
                    op.basename(png_file_name),
                    thumbnail=op.basename(thumb))],
        thumbnail=op.basename(thumb))



def to_report(stats_xml, output_dir, dpi=DEFAULT_DPI):
    """Main point of entry

    :type stats_xml: str
    :type output_dir: str
    :type dpi: int

    :rtype: Report
    """
    log.info("Analyzing XML {f}".format(f=stats_xml))
    # stats_xml should be a dataset:
    dset = SubreadSet(stats_xml)
    from_sts_xml = False
    if not dset.metadata.summaryStats:
        dset.loadStats(stats_xml)
        from_sts_xml = True
    return to_report_impl(dset, output_dir, dpi, from_sts_xml)


def to_report_impl(dset, output_dir, dpi=DEFAULT_DPI, from_sts_xml=False):
    dataset_uuids = [dset.uuid]
    if from_sts_xml:
        dataset_uuids = []
    if not dset.metadata.summaryStats.readLenDists:
        raise InvalidStatsError("Pipeline Summary Stats (sts.xml) not found "
                                "or missing key distributions")

    # we want all of the length distributions in this report to look the same,
    # so we make the shaper here and pass it around:
    alldists = (dset.metadata.summaryStats.readLenDists[:] +
                dset.metadata.summaryStats.insertReadLenDists[:])
    len_dist_shaper = continuous_dist_shaper(alldists, trim_excess=True)

    attr = to_read_stats_attributes(
        readLenDists=dset.metadata.summaryStats.readLenDists,
        readQualDists=dset.metadata.summaryStats.readQualDists)

    if not from_sts_xml:
        log.info("Computing mean subread length and N50 from .pbi indices")
        subread_lengths = dset.index.qEnd - dset.index.qStart
        subread_length = int(np.mean(subread_lengths))
        subread_n50 = compute_n50(subread_lengths)
        attr.append(Attribute(Constants.A_SUBREAD_LENGTH, value=subread_length))
        attr.append(Attribute(Constants.A_SUBREAD_N50, value=subread_n50))

    attr.extend(to_insert_stats_attributes(
        readLenDists=dset.metadata.summaryStats.insertReadLenDists,
        readQualDists=dset.metadata.summaryStats.insertReadQualDists))

    plot_groups = to_read_stats_plots(
        readLenDists=dset.metadata.summaryStats.readLenDists,
        readQualDists=dset.metadata.summaryStats.readQualDists,
        output_dir=output_dir,
        lenDistShaper=len_dist_shaper)
    if not from_sts_xml:
        plot_groups.append(to_subread_lengths_plot(dset, output_dir))
    plot_groups.extend(to_insert_stats_plots(
        readLenDists=dset.metadata.summaryStats.insertReadLenDists,
        readQualDists=dset.metadata.summaryStats.insertReadQualDists,
        output_dir=output_dir,
        lenDistShaper=len_dist_shaper))

    # build the report:
    report = Report(Constants.R_ID,
                    attributes=attr,
                    plotgroups=plot_groups,
                    dataset_uuids=dataset_uuids)

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
