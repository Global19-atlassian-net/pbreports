#!/usr/bin/env python
import argparse
import functools
import logging
import sys
import os
import json
import numpy as np
import types

from pbcore.io.BasH5IO import BasH5Reader, Zmw, ADAPTER_REGION

from pbreports.pbsystem_common.cmdline.core import main_runner_default
from pbreports.pbsystem_common.validators import validate_fofn, bas_fofn_to_bas_files

from pbreports.model.model import Attribute, Report, PlotGroup, Plot
from pbreports.plot.helper import (get_fig_axes_lpr, apply_histogram_data,
                                   save_figure_with_thumbnail)
from pbreports.util import get_base_parser_with_plot_options, add_base_options, \
    add_base_and_plot_options


log = logging.getLogger(__name__)

__version__ = '0.1'
_UNTRIMMED_METHOD_NAME = 'untrimmedAdapterRegions'


def __untrimmed_adapters(self):
    """Get the Untrimmed Adapters (non Hq regions)

    This is a bit hacky. Doing this so I don't make any changes to pbcore API.
    """
    unclippedAdapterRegions = []

    for region in self.regionTable:
        if region.regionType == ADAPTER_REGION:
            unclippedAdapterRegions.append((region.regionStart, region.regionEnd))

    return unclippedAdapterRegions


def __add_untrimmed_method_to_zmw_class():
    f = types.MethodType(__untrimmed_adapters, None, Zmw)
    setattr(Zmw, _UNTRIMMED_METHOD_NAME, f)

__add_untrimmed_method_to_zmw_class()
del __add_untrimmed_method_to_zmw_class


def make_adapter_report(fofn, report, output_dir, dpi, dumpdata):
    bas_files = bas_fofn_to_bas_files(fofn)
    log.info("Found {n} bas/bax files from {f}".format(n=len(bas_files), f=fofn))
    log.debug(bas_files)

    rpt = to_report_streaming(bas_files, output_dir, dpi)
    rpt.write_json(os.path.join(output_dir, report))


def _create_histogram(mas):
    """
    Return a matplotlib figure object with data applied
    mas: median adapter spacing int array
    """
    axis_labels = ('Median Distance Between Adapters', 'Pre-Filter Reads')
    bins = np.logspace(0, 4, 50)
    fig, ax = get_fig_axes_lpr()
    ax.set_xscale('log')
    apply_histogram_data(ax, mas, bins, axis_labels=axis_labels,
                         barcolor='#505050', xlim=(0, 20000))
    return fig

def _create_histogram_figure(histogram):
    """
    Return a matplotlib figure object with data applied
    mas: median adapter spacing int array
    """
    axis_labels = ('Median Distance Between Adapters', 'Pre-Filter Reads')
    bins = np.logspace(0, 4, 50)
    fig, ax = get_fig_axes_lpr()
    ax.set_xscale('log')
    # TODO better API here. Pass in the Histogram object to the plotting function?
    apply_histogram_data(ax, histogram.bins, bins, axis_labels=axis_labels,
                         barcolor='#505050', xlim=(0, 20000), weights=histogram.values)
    return fig


# TODO replace with a real histogram object later
class Histogram(object):
    def __init__(self, minimum=-1, maximum=200000):
        self.counts = np.zeros(maximum-minimum)
        self.total = 0
        self.minimum = minimum
        self.maximum = maximum
        
    def add_value(self, value):
        self.total += 1
        if value is None:
            return

        if not self.minimum <= value <= self.maximum:
            raise ValueError, "Value %i not between %i and %i" % (
                                value, self.minimum, self.maximum)
        # round value to nearest integer
        self.counts[int(value-self.minimum+0.5)] += 1

    def sum_bounds(self, start, stop): # inclusive
        return sum(self.counts[start-self.minimum:stop-self.minimum+1])


    @property
    def bins(self):
        return range(self.minimum, self.maximum)

    @property
    def values(self):
        return self.counts

def _create_attributes(mas, seq_zmws, id_prefix):
    """
    Return a list of attributes to add to the report
    :param mas: (int array) Median adapter spacing
    :param seq_zmws: (tuple) of [(start, end),...]
    :param id_prefix: (str) prefix that can be used on the attribute ids

    """
    atts = []
    atts.append(_get_dimer_att(mas, seq_zmws, id_prefix))
    atts.append(_get_short_inserts_att(mas, seq_zmws, id_prefix))
    atts.append(_get_medium_inserts_att(mas, seq_zmws, id_prefix))
    return atts

# TODO sequencing_zmw_method?
def _get_zmw_records(bas_files, sequencing_zmw_method="allSequencingZmws"):
    """
    Return an iterable over pbcore Zmw objects.
    :param bas_files:
    :param sequencing_zmw_method: (str) allSequencingZmws, or sequencingZmws
     method of BasH5Reader
    """
    for bas_file in bas_files:
        log.info("Processing bas file  '{s}'".format(s=bas_file))
        if not os.path.exists(bas_file):
            raise IOError("Unable to find bas/bax file '{f}'.".format(f=bas_file))

        log.info("file {m}".format(m=bas_file))
        b = BasH5Reader(bas_file)

        # sequencing hole numbers
        hns = getattr(b, sequencing_zmw_method)
        for hn in hns:
            zmw = b[hn]
            yield zmw


# TODO this actually opens each BasH5 file twice still. 
# TODO consolidate two methods below?
def calc_untrimmed_adapter_histogram(histogram, bas_file):
    for idx, zmw in enumerate(_get_zmw_records([bas_file], 'allSequencingZmws')):
        intervals = zmw.untrimmedAdapterRegions()
        if len(intervals) == 0:
            histogram.add_value(None)
            continue
        # TODO fix goofy api below
        for spacing in _get_median_adapter_spacing({"dummyZMW": intervals}):
            histogram.add_value(spacing)


def calc_trimmed_adapter_histogram(histogram, bas_file):
    for idx, zmw in enumerate(_get_zmw_records([bas_file], 'sequencingZmws')):
        intervals = zmw.adapterRegions
        if len(intervals) == 0:
            histogram.add_value(None)
            continue
        for spacing in _get_median_adapter_spacing({"dummyZMW": intervals}):
            histogram.add_value(spacing)

def applier(iterable, funcs):
    for it in iterable:
        for func in funcs:
            func(it)

def _create_histograms(bas_files):
    """Returns trimmed and untrimmed Histogram objects"""

    log.info("Started reading info from movie file(s)")
    untrimmed_histogram = Histogram(minimum=-100)
    trimmed_histogram   = Histogram(minimum=-100)
    funcs = [   functools.partial(
                    calc_untrimmed_adapter_histogram, 
                    untrimmed_histogram),
                functools.partial(
                    calc_trimmed_adapter_histogram, 
                    trimmed_histogram) ]
    
    applier(bas_files, funcs)
    log.info("Finished reading info from movie file(s)")
    return trimmed_histogram, untrimmed_histogram


def to_report_streaming(bas_files, output_dir, dpi=60):
    """ Convert a list of bas files to a report instance

    :param bas_files:
    :param output_dir:
    :param dpi: int
    :return: (Report) instance
    """

    trimmed_histogram, untrimmed_histogram = _create_histograms(bas_files)
    log.info("report generation with output dir {d} and files {f}".format(
        d=output_dir, f=bas_files))

    attributes = _create_attributes(
                        untrimmed_histogram, 
                        untrimmed_histogram.total,
                        id_prefix="")
    attributes.extend(
                 _create_attributes(
                        trimmed_histogram, 
                        trimmed_histogram.total,
                        id_prefix="hq"))

    fig = _create_histogram_figure(untrimmed_histogram)

    plot_grp_title = 'Observed Insert Length Distribution'
    pg_id = plot_grp_title.lower().replace(" ", "_")
    png_fn = os.path.join(output_dir, "adapter_" + pg_id + ".png")

    png_fn, thumb = save_figure_with_thumbnail(fig, png_fn, dpi=dpi)

    log.debug("Saved histograms image with thumbnail {x}, {y}".format(x=png_fn, y=thumb))

    plot = Plot('plot1', os.path.basename(png_fn))
    pg = PlotGroup(pg_id, title=plot_grp_title, thumbnail=os.path.basename(thumb), plots=[plot])

    report = Report('adapter', plotgroups=[pg], attributes=attributes)
    return report


def __get_zmw_adapters(sequencing_zmw_method, zmw_method_name, bas_files):
    """
    Function to used to get adapters from bas files.


    Return a tuple.

    :param sequencing_zmw_method: (str) allSequencingZmws, or sequencingZmws
     method of BasH5Reader
    :param zmw_method_name: (str) untrimmedAdapterRegions, or adapterRegions (Zmw method name)
    :param bas_files:

    Position 0: a dictionary, where the key is a ZMW tuple and the value is
    a list adapter interval tuples
    Postion 1: the total number of sequencing ZMW's represented by the fofn
    """
    adapters = {}
    seq_zmws = []

    for bas_file in bas_files:
        log.info("Processing bas file  '{s}'".format(s=bas_file))
        if not os.path.exists(bas_file):
            raise IOError("Unable to find bas/bax file '{f}'.".format(f=bas_file))

        movie_name = bas_file.strip().split(".")[0]
        log.info("movie {m}".format(m=movie_name))
        b = BasH5Reader(bas_file)

        # sequencing hole numbers
        # Should this be allSequencingZmws or sequencingZmws?
        # hns = b.allSequencingZmws
        hns = getattr(b, sequencing_zmw_method)
        for hn in hns:
            zmw = b[hn]
            adapters.setdefault(zmw, [])

            # intervals = zmw.untrimmedAdapterRegions()
            # intervals = zmw.adapterRegions
            m = getattr(zmw, zmw_method_name)
            # handle bound or unbound
            if isinstance(m, types.MethodType):
                intervals = m()
            else:
                intervals = m

            if len(intervals) == 0:
                continue
            adapters[zmw].extend(intervals)

        b.close()
        seq_zmws.append(len(hns))
    return adapters, np.sum(seq_zmws)

get_untrimmed_adapters = functools.partial(__get_zmw_adapters, 'allSequencingZmws', _UNTRIMMED_METHOD_NAME)
get_hq_adapters = functools.partial(__get_zmw_adapters, 'sequencingZmws', 'adapterRegions')


def _get_dimer_att(mas, seq_zmws, id_prefix):
    idx = "{x}_adapter_dimers".format(x=id_prefix) if id_prefix else "adapter_dimers"
    return _get_report_att(mas, seq_zmws, (0, 10), idx, 'Adapter Dimers')


def _get_short_inserts_att(mas, seq_zmws, id_prefix):
    idx = "{x}_short_inserts".format(x=id_prefix) if id_prefix else "short_inserts"
    return _get_report_att(mas, seq_zmws, (11, 100), idx, 'Short Inserts')


def _get_medium_inserts_att(mas, seq_zmws, id_prefix):
    idx = "{x}_medium_inserts".format(x=id_prefix) if id_prefix else "medium_inserts"
    return _get_report_att(mas, seq_zmws, (101, 1000), idx, 'Medium Inserts')


def _get_report_att(mas, seq_zmws, bounds, id_, name):
    if len(bounds) != 2:
        raise ValueError('bounds must be int tuple of len == 2')
    # bug 23860
    if seq_zmws == 0:
        log.debug('Setting attribute (id={i}) value to NA')
        v = 'NA'
    else:
        v = mas.sum_bounds(bounds[0], bounds[1]) / float(seq_zmws)
    att = Attribute(id_, v, name)
    log.debug('Created attribute: {a}'.format(a=json.dumps(att.to_dict())))
    return att


def _get_median_adapter_spacing(adapters):
    """
    For all sequencing ZMW's, get all adapter intervals.
    Return a list of median adapter spacings for each ZMW that has at least
    one interval.
    """
    mas = {}  # Median Adapter Spacing
    for zmw in adapters:
        adapters[zmw].sort(key=lambda x: x[0])
        spacing = []
        lastEnd = None
        for (start, end) in adapters[zmw]:
            if lastEnd is not None:
                spacing.append(start - lastEnd)
            lastEnd = end

        mas[zmw] = np.median(spacing) if len(spacing) > 0 else -1

    return mas.values()


def args_runner(args):
    log.info("Starting {x}")
    return make_adapter_report(args.fofn, args.report, args.output, args.dpi, args.dumpdata)


def add_options_to_parser(p):
    p.description = 'Generates adapter related statistics which are helpful in quantifying ' + \
            'the presence of adapter dimers.'
    p = add_base_and_plot_options(p)
    p.add_argument("fofn", type=validate_fofn,
                   help="file containing list of bas.h5 file names")
    p.set_defaults(func=args_runner)
    return p


def get_parser():
    p = argparse.ArgumentParser(version=__version__)
    p = add_options_to_parser(p)
    return p


def main(argv=sys.argv):
    """Main point of Entry"""
    log.info("Starting {f} version {v} report generation".format(f=__file__, v=__version__))
    return main_runner_default(argv[1:], get_parser(), log)
