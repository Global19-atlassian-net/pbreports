
"""
Structural Variants Report
"""

import os
import os.path as op
import logging
import sys
import json
import itertools
import collections

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from matplotlib import rcParams
from matplotlib.transforms import offset_copy

from pbcommand.models.report import Report, Table, Column, PlotGroup, Plot
from pbcommand.models import FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log
from pbreports.io.specs import *
from pbreports.plot.helper import (get_fig_axes_lpr,
                                   save_figure_with_thumbnail)

__version__ = '0.1.0'


class Constants(object):
    TOOL_ID = "pbreports.tasks.structural_variants_report"
    DRIVER_EXE = ("python -m pbreports.report.structural_variants "
                  "--resolved-tool-contract ")
    R_ID = "structural_variants"

    SAMPLE_KEY = "CountBySample"
    T_SAMPLE = "sample_table"
    C_SAMPLE = "sample"
    C_INS = "insertions"
    C_DEL = "deletions"
    C_HOM = "homozygous"
    C_HET = "heterozygous"
    C_TOTAL = "total"

    ANNO_KEY = "CountByAnnotation"
    T_ANNO = "anno_table"
    C_ANNO = "annotation"
    R_TANDEM = "Tandem Repeat"
    R_ALU = "Alu"
    R_L1 = "L1"
    R_SVA = "SVA"
    R_UNANNOTATED = "Unannotated"
    R_TOTAL = "Total"

    PG_SV = "sv_plot_group"
    P_SV = "sv_plot"
    C_SHORT = 'Variants <1 kb'
    C_LONG = 'Variants ' + r'$\geq$' + '1 kb'

    SV_LEN_CUTOFF_S = 1000
    BIN_WIDTH_S = 50
    X_TICKS_S = range(0, SV_LEN_CUTOFF_S + 100, 50)[:-1]
    X_LIMS_S = [X_TICKS_S[0], X_TICKS_S[-1]]
    X_LABELS_S = list(itertools.chain(*[[str(x), ""] for x in xrange(0,1000,100)])) + ["1,000"]
    X_LABEL_S = "variant length (bp)"
    N_BINS_S = X_LIMS_S[1] / BIN_WIDTH_S

    OVERFLOW_BIN_X = 11250
    SV_LEN_CUTOFF_L = 10000
    BIN_WIDTH_L = 500
    X_TICKS_L = range(0, SV_LEN_CUTOFF_L + 500,
                    500) + [OVERFLOW_BIN_X]
    X_LIMS_L = [0, 12000]
    X_LABELS_L = list(itertools.chain(*[[str(x), ""] for x in xrange(0,11)]))[:-1] + [">10"]
    X_LABEL_L = "variant length (kb)"
    N_BINS_L = X_LIMS_L[1] / BIN_WIDTH_L


log = logging.getLogger(__name__)
spec = load_spec(Constants.R_ID)


def _comma_formatter(x, pos=0):
    return ("{0:,d}".format(int(x)))

def _my_combine(n,t):
    """
    Takes two integers, n and t, and returns "n (t)"
    """
    c = _comma_formatter(str(n)) + " (" + _comma_formatter(str(t)) + ")"
    return c


def to_sample_table(table_json):
    col_ids = [Constants.C_SAMPLE, Constants.C_INS, Constants.C_DEL, 
               Constants.C_HOM, Constants.C_HET, Constants.C_TOTAL]
    sample_table = table_json[Constants.SAMPLE_KEY]
    t = []
    if len(sample_table) == 0:
        table = [[], [], [], [], [], []]
    else:
        for row in sample_table:
            r = [row[0]]
            r.append(_my_combine(row[1], row[2]))
            r.append(_my_combine(row[3], row[4]))
            r.append(row[5])
            r.append(row[6])
            r.append(_my_combine(row[7], row[8]))
            t.append(r)
        table = zip(*t)
    columns = []
    for i, col_id in enumerate(col_ids):
        columns.append(Column(col_id, values=table[i]))
    sample_table = Table(Constants.T_SAMPLE, columns=columns)

    return sample_table


def to_anno_table(table_json):
    col_ids = [Constants.C_ANNO, Constants.C_INS,
               Constants.C_DEL, Constants.C_TOTAL]
    row_ids = [Constants.R_TANDEM, Constants.R_ALU, Constants.R_L1,
               Constants.R_SVA, Constants.R_UNANNOTATED, Constants.R_TOTAL]
    anno_table = table_json[Constants.ANNO_KEY]
    t = []
    for _id in row_ids:
        for row in anno_table:
            if _id == row[0]:
                r = [row[0]]
                for i in xrange(1,6,2):
                    r.append(_my_combine(row[i], row[i+1]))
                t.append(r)
    table = zip(*t)
    columns = []
    for i, col_id in enumerate(col_ids):
        columns.append(Column(col_id, values=table[i]))
    anno_table = Table(Constants.T_ANNO, columns=columns)

    return anno_table


def process_short_data(data):
    short_ins = [x for x in data.get(
        "Insertion", []) if x < Constants.SV_LEN_CUTOFF_S]
    short_del = [x for x in data.get(
        "Deletion", []) if x < Constants.SV_LEN_CUTOFF_S]

    return short_ins, short_del


def process_long_data(data):
    long_ins_raw = [x for x in data.get(
        "Insertion", []) if x >= Constants.SV_LEN_CUTOFF_S]
    long_del_raw = [x for x in data.get(
        "Deletion", []) if x >= Constants.SV_LEN_CUTOFF_S]
    # mapping all lengths above 10k to a constant
    long_ins = [Constants.OVERFLOW_BIN_X if x > Constants.SV_LEN_CUTOFF_L
                        else x for x in long_ins_raw]
    long_del = [Constants.OVERFLOW_BIN_X if x > Constants.SV_LEN_CUTOFF_L
                        else x for x in long_del_raw]

    return long_ins, long_del
    

def add_subplot(fig, ax, sample, data, counter, y_max, position):
    insertions = data[0]
    deletions = data[1]
    y_label = get_plot_ylabel(spec, Constants.PG_SV, Constants.P_SV)
    if position == 0:
        x_ticks = Constants.X_TICKS_S 
        x_lims = Constants.X_LIMS_S
        x_labels = Constants.X_LABELS_S
        n_bins = Constants.N_BINS_S
        x_label = Constants.X_LABEL_S
    if position == 1:
        x_ticks = Constants.X_TICKS_L
        x_lims = Constants.X_LIMS_L
        x_labels = Constants.X_LABELS_L
        n_bins = Constants.N_BINS_L
        x_label = Constants.X_LABEL_L
    ax = ax[counter, position]
    if insertions or deletions:
        ax.hist([deletions, insertions], label=["Deletions", "Insertions"], histtype='barstacked',
                color=["#FF7E79", "#A9D18E"], edgecolor="none", bins=n_bins,
                width=0.85 * (x_lims[1] - x_lims[0]) / n_bins, range=[x_lims[0], x_lims[1]])
    ax.set_xlabel(x_label, size = 20)
    ax.set_ylabel(y_label, size = 20)
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=x_lims[0], right=x_lims[1])
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(_comma_formatter))
    ax.grid(color='#e0e0e0', linewidth=0.9, linestyle='-')
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels, size = 15)
    ax.tick_params(axis='y', labelsize=15)
    rcParams['xtick.direction'] = 'out'
    rcParams['ytick.direction'] = 'out'
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    y_top = ax.get_ylim()[1]
    if y_top > y_max[position]:
        y_max[position] = y_top


def add_subplots(fig, ax, sample, data, counter, y_max):
    short_ins, short_del = process_short_data(data)
    add_subplot(fig, ax, sample, [short_ins, short_del], counter, y_max, 0)
    long_ins, long_del = process_long_data(data)
    add_subplot(fig, ax, sample, [long_ins, long_del], counter, y_max, 1)


def label_rows(fig, axes, rows):
    pad = 5 # in points
    for ax, row in zip(axes[:,0], rows):
        ax.annotate(row, xy=(0, 0.5), xytext=(-ax.yaxis.labelpad - pad, 0),
        xycoords=ax.yaxis.label, textcoords='offset points',
        size=25, ha='right', va='center')
    fig.tight_layout()
    fig.subplots_adjust(left=0.15, top=0.95)


def label_columns(fig, axes):
    pad = 5 # in points
    columns = [Constants.C_SHORT, Constants.C_LONG]
    for ax, col in zip(axes[0], columns):
        ax.annotate(col, xy=(0.5, 1), xytext=(0, pad),
                    xycoords='axes fraction', textcoords='offset points',
                    size=25, ha='center', va='baseline')


def to_plotgroup(plot_json, output_dir):
    n_samples = len(plot_json)
    if n_samples > 0:
        fig, ax = plt.subplots(n_samples, 2, figsize=(15, n_samples*5), squeeze=False)
        od = collections.OrderedDict(sorted(plot_json.items()))
        counter = 0
        y_max = [0, 0]
        for sample, data in od.iteritems():
            add_subplots(fig, ax, sample, data, counter, y_max)
            counter+=1
        label_rows(fig, ax, od.keys())
        label_columns(fig, ax)
        for row in xrange(0, n_samples):
            ax[row, 0].set_ylim(top=y_max[0]*1.1)
            ax[row, 1].set_ylim(top=y_max[1]*1.1)
        p1 = mpatches.Patch(color='#FF7E79', linewidth=0)
        p2 = mpatches.Patch(color='#A9D18E', linewidth=0)
        fig.legend((p1,p2), ("Deletions", "Insertions"), "upper left", fontsize=15)
    else:
        fig = plt.figure()
    plot_name = get_plot_title(spec, Constants.PG_SV, Constants.P_SV)
    png_fn = os.path.join(output_dir, "{p}.png".format(p=Constants.P_SV))
    png_base, thumbnail_base = save_figure_with_thumbnail(fig, png_fn, dpi=72, bbox_inches='tight')
    plot = Plot(Constants.P_SV, os.path.relpath(png_base, output_dir),
                title=plot_name, caption=plot_name,
                thumbnail=os.path.relpath(thumbnail_base, output_dir))
    plot_group = PlotGroup(Constants.PG_SV, plots=[plot])

    return plot_group


def to_report(table_json_file, plot_json_file, output_dir):

    log.info("Starting {f} v{v}".format(f=os.path.basename(__file__),
                                        v=__version__))
    with open(table_json_file) as f:
        table_json = json.load(f)
    with open(plot_json_file) as f:
        plot_json = json.load(f)
    tables = [to_sample_table(table_json), to_anno_table(table_json)]
    plotgroups = [to_plotgroup(plot_json, output_dir)]
    report = Report(Constants.R_ID, tables=tables, plotgroups=plotgroups)

    return spec.apply_view(report)


def _args_runner(args):
    output_dir = os.path.dirname(args.report)
    report = to_report(args.table_json, args.plot_json, output_dir)
    report.write_json(args.report)
    return 0


def _resolved_tool_contract_runner(rtc):
    output_dir = os.path.dirname(rtc.task.output_files[0])
    report = to_report(rtc.task.input_files[0],
                       rtc.task.input_files[1],
                       output_dir)
    report.write_json(rtc.task.output_files[0])
    return 0


def _add_options_to_parser(p):
    p.add_input_file_type(
        FileTypes.JSON,
        file_id="json_table",
        name="JSON Table Data",
        description="JSON of table data")
    p.add_input_file_type(
        FileTypes.JSON,
        file_id="json_plot",
        name="JSON Plot Data",
        description="JSON of plot data")
    p.add_output_file_type(FileTypes.REPORT, "report", spec.title,
                           description=("Filename of JSON output report. Should be name only, "
                                        "and will be written to output dir"),
                           default_name="report")
    return p


def _get_parser():
    p = get_pbparser(
        Constants.TOOL_ID,
        __version__,
        "Report",
        __doc__,
        Constants.DRIVER_EXE,
        is_distributed=False)
    return _add_options_to_parser(p)


def main(argv=sys.argv):
    return pbparser_runner(argv[1:],
                           _get_parser(),
                           _args_runner,
                           _resolved_tool_contract_runner,
                           log,
                           setup_log)


if __name__ == "__main__":
    sys.exit(main())
