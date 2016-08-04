
# FIXME we might want to move this to kineticsTools someday, just to keep the
# HDF5 dependency contained (but as long as it's in pbcore it doesn't matter)

"""
Generates plots showing the distribution of kinetics across all bases, taken
from ipdSummary output.
"""

import collections
import argparse
import logging
import gzip
import os
import os.path as op
import sys

from pylab import legend, arange
import numpy as np
import h5py

from pbcommand.models.report import Report, PlotGroup, Plot
from pbreports.report.report_spec import (MetaAttribute, MetaPlotGroup, MetaPlot,
                                          MetaColumn, MetaTable, MetaReport)
from pbcommand.models import TaskTypes, FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.common_options import add_debug_option
from pbcommand.utils import setup_log

import pbreports.plot.helper as PH
from pbreports.util import (add_base_and_plot_options,
                            add_base_options_pbcommand)
from pbreports.util import Constants as BaseConstants

log = logging.getLogger(__name__)

__version__ = '2.1'

# Import Mapping MetaReport
_DIR_NAME = os.path.dirname(os.path.realpath(__file__))
SPEC_DIR = os.path.join(_DIR_NAME, 'specs/')
MOD_SPEC = op.join(SPEC_DIR, 'modifications.json')
meta_rpt = MetaReport.from_json(MOD_SPEC)

class Constants(BaseConstants):
    TOOL_ID = "pbreports.tasks.modifications_report"
    DRIVER_EXE = "python -m pbreports.report.modifications --resolved-tool-contract"
    PG_KIN = "kinetic_detections"
    P_SCAT = "kinetic_scatter"
    P_HIST = "kinetic_histogram"

def _create_fig_template(dims=(8, 6), facecolor='#ffffff', gridcolor='#e0e0e0'):
    fig, ax = PH.get_fig_axes_lpr(dims=dims)
    ax = fig.add_subplot(111)

    ax.axesPatch.set_facecolor(facecolor)
    ax.grid(color=gridcolor, linewidth=0.5, linestyle='-')
    ax.set_axisbelow(True)
    PH.set_tick_label_font_size(ax, 12, 12)
    PH.set_axis_label_font_size(ax, 16)
    return fig, ax


def plot_kinetics_scatter(basemods_h5, ax):

    handles = []
    colors = ['red', 'green', 'blue', 'magenta']
    bases = ['A', 'C', 'G', 'T']

    for base, color in zip(bases, colors):
        baseHits = basemods_h5['base'].__array__() == base
        n_bases = np.count_nonzero(baseHits)

        if n_bases > 0:
            # Add a bit of scatter to avoid ugly aliasing in plot due to
            # integer quantization
            cov = basemods_h5['coverage'][baseHits] + 0.25 * np.random.randn(n_bases)
            score = basemods_h5['score'][baseHits] + 0.25 * np.random.randn(n_bases)

            pl = ax.scatter(cov, score, c=color, label=base,
                            lw=0, alpha=0.3, s=12)
            handles.append(pl)
        else:
            log.warn("Base {b} not found".format(b=base))

    ax.set_xlabel(meta_rpt.get_meta_plotgroup(Constants.PG_KIN).get_meta_plot(Constants.P_SCAT).xlabel)
    ax.set_ylabel(meta_rpt.get_meta_plotgroup(Constants.PG_KIN).get_meta_plot(Constants.P_SCAT).ylabel)
    legend(handles, bases, loc='upper left')

    if len(basemods_h5['base']) > 0:
        ax.set_xlim(0, np.percentile(basemods_h5['coverage'], 95.0) * 1.4)
        ax.set_ylim(0, np.percentile(basemods_h5['score'], 99.9) * 1.3)


def plot_kinetics_hist(basemods_h5, ax):

    colors = ['red', 'green', 'blue', 'magenta']
    bases = ['A', 'C', 'G', 'T']

    # Check for empty or peculiar modifications report:
    d = basemods_h5['score']
    if len(d) == 0:
        binLim = 1.0
    elif np.isnan(np.sum(d)):
        binLim = np.nanmax(d)
    else:
        binLim = np.percentile(d, 99.9) * 1.2

    ax.set_xlim(0, binLim)
    bins = arange(0, binLim, step=binLim / 75)

    for base, color in zip(bases, colors):
        baseHits = basemods_h5['base'].__array__() == base
        if np.count_nonzero(baseHits) > 0:
            pl = ax.hist(basemods_h5['score'][baseHits], color=color,
                         label=base, bins=bins, histtype="step", log=True)
        else:
            log.warn("Base {b} not found".format(b=base))

    ax.set_xlabel(meta_rpt.get_meta_plotgroup(Constants.PG_KIN).get_meta_plot(Constants.P_HIST).xlabel)
    ax.set_ylabel(meta_rpt.get_meta_plotgroup(Constants.PG_KIN).get_meta_plot(Constants.P_HIST).ylabel)


    if len(d) > 0:
        ax.legend(loc='upper right')


def get_qmod_plot(basemods_h5, output_dir, dpi):
    """
    Return a plot object
    """
    fig, ax = _create_fig_template()

    plot_kinetics_scatter(basemods_h5, ax)

    png_path = os.path.join(output_dir, "kinetic_detections.png")
    png, thumbpng = PH.save_figure_with_thumbnail(fig, png_path, dpi=dpi)

    return Plot(Constants.P_SCAT, os.path.basename(png),
                thumbnail=os.path.basename(thumbpng))


def get_qmod_hist(basemods_h5, output_dir, dpi):
    """
    Return a plot object
    """
    fig, ax = _create_fig_template()

    plot_kinetics_hist(basemods_h5, ax)

    png_path = os.path.join(output_dir, "kinetic_histogram.png")
    png, thumbpng = PH.save_figure_with_thumbnail(fig, png_path, dpi=dpi)

    return Plot(Constants.P_HIST, os.path.basename(png),
                thumbnail=os.path.basename(thumbpng))


def make_modifications_report(modifications_h5, report, output_dir, dpi=72):
    """
    Entry point to report generation.
    """
    basemods_h5 = h5py.File(modifications_h5)
    scatter = get_qmod_plot(basemods_h5, output_dir, dpi)
    hist = get_qmod_hist(basemods_h5, output_dir, dpi)
    pg = PlotGroup(Constants.PG_KIN,
                   title=meta_rpt.get_meta_plotgroup(Constants.PG_KIN).title,
                   thumbnail=scatter.thumbnail,
                   plots=[scatter, hist])
    rpt = Report(meta_rpt.id, plotgroups=[pg])
    rpt = meta_rpt.apply_view(rpt)
    rpt.write_json(os.path.join(output_dir, report))
    return 0


def add_options_to_parser(p):
    from pbreports.io.validators import validate_file
    p.description = __doc__  # FIXME which is probably wrong
    p.version = __version__
    p = add_base_and_plot_options(p)
    p.add_argument("basemods_h5", help="modifications.h5", type=validate_file)
    p.set_defaults(func=_args_runner)
    return p


def args_runner(args):
    return make_modifications_report(
        modifications_h5=args.basemods_h5,
        report=os.path.basename(args.report),
        output_dir=args.output)


def resolved_tool_contract_runner(resolved_tool_contract):
    rtc = resolved_tool_contract
    return make_modifications_report(
        modifications_h5=rtc.task.input_files[0],
        report=os.path.basename(rtc.task.output_files[0]),
        output_dir=os.path.dirname(rtc.task.output_files[0]))


def get_parser():
    p = get_pbparser(
        Constants.TOOL_ID,
        __version__,
        "Modifications Report",
        __doc__,
        Constants.DRIVER_EXE,
        is_distributed=True)
    p.add_input_file_type(FileTypes.H5, "basemods_h5", "HDF5 file",
                          "HDF5 file of base modifications from ipdSummary")
    add_base_options_pbcommand(p, "Basemods report")
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
