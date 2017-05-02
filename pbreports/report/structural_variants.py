import os
import os.path as op
import logging
import sys
import json
import itertools

import matplotlib.ticker as ticker
from matplotlib import rcParams

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

    T_ID = "anno_table"
    C_ANNOTATION = "annotation"
    C_INS_N = "insertions_n"
    C_INS_SUM = "insertions_sum"
    C_DEL_N = "deletions_n"
    C_DEL_SUM = "deletions_sum"
    C_INDEL_N = "indel_n"
    C_INDEL_SUM = "indel_sum"

    PG_SHORT_SV = "short_sv_plot_group"
    P_SHORT_SV = "short_sv_plot"
    PG_LONG_SV = "long_sv_plot_group"
    P_LONG_SV = "long_sv_plot"


log = logging.getLogger(__name__)
spec = load_spec(Constants.R_ID)


def to_sv_table(table_json):
    
    col_ids = [Constants.C_ANNOTATION, Constants.C_INS_N, Constants.C_INS_SUM, 
               Constants.C_DEL_N, Constants.C_DEL_SUM, Constants.C_INDEL_N,
               Constants.C_INDEL_SUM]

    t = []
    for row in table_json:
        r = [str(row[0])]
        r.extend([int(x) for x in row[1:7]])
        t.append(r)

    table = zip(*t)

    columns = []
    for i, col_id in enumerate(col_ids):
        columns.append(Column(col_id, values=table[i]))

    sv_table = Table(Constants.T_ID, columns=columns)

    return sv_table
    

def comma_formatter(x, pos=0):
    return ("{0:,d}".format(int(x)))

def to_plotgroup(data, pg, p, bin_n, x_ticks, x_lims, x_labels, output_dir):
    """
    This plots a stacked histogram given a length 2 array of arrays
    :param data: array containing insertion array and deletion array
    :type data: array
    :param pg: plotgroup id
    :type pg: string
    :param p: plot id
    :type p: string
    :param bin_n: number of bins for the histogram
    :type bin_n: int
    :param x_ticks: the values to place on the x axis
    :type x_ticks: array
    :param x_labels: the names to place on the x tick marks
    :type x_labels: array
    :param output_dir: output directory for the plots
    :type output_dir: string
    """
    plot_name = get_plot_title(spec, pg, p)
    x_label = get_plot_xlabel(spec, pg, p)
    y_label = get_plot_ylabel(spec, pg, p)
    insertions = data[0]
    deletions = data[1]
    fig, ax = get_fig_axes_lpr()
    if insertions or deletions:
        ax.hist([deletions, insertions], label=["Deletions", "Insertions"], histtype='barstacked',
                color=["#FF7E79", "#A9D18E"], edgecolor = "none", bins=bin_n,
                width=0.85*(x_lims[1] - x_lims[0])/bin_n, range=[x_lims[0], x_lims[1]])
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=x_lims[0], right=x_lims[1])
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(comma_formatter))
    ax.xaxis.grid(False)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels)
    rcParams['xtick.direction'] = 'out'
    rcParams['ytick.direction'] = 'out'
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    png_fn = os.path.join(output_dir, "{p}.png".format(p=p))
    png_base, thumbnail_base = save_figure_with_thumbnail(fig, png_fn, dpi=72)
    plot = Plot(p, os.path.relpath(png_base, output_dir),
                    title=plot_name, caption=plot_name,
                    thumbnail=os.path.relpath(thumbnail_base, output_dir))
    plot_group = PlotGroup(pg, plots=[plot])
    return plot_group


def to_plotgroups(plot_json, output_dir):
    short_ins = [x for x in plot_json.get("Insertion", []) if x < 1000]
    short_del = [x for x in plot_json.get("Deletion", []) if x < 1000]
    x_ticks = range(0,1100,100)
    x_lims = [x_ticks[0], x_ticks[-1]]
    x_labels = ["0", "100", "200", "300", "400", "500", "600", "700", "800", "900", "1,000"]
    plotgroups = [to_plotgroup([short_ins, short_del], Constants.PG_SHORT_SV,
                               Constants.P_SHORT_SV, 20, x_ticks, x_lims, x_labels, output_dir)]
    long_ins = [x for x in plot_json.get("Insertion", []) if x >= 1000]
    long_del = [x for x in plot_json.get("Deletion", []) if x >= 1000]
    long_ins_clipped = [22250 if x > 20000 else x for x in long_ins]
    long_del_clipped = [22250 if x > 20000 else x for x in long_del]
    x_ticks = [1000, 5000, 10000, 15000, 20000, 22250]
    x_lims = [1000, 23000]
    x_labels = ["1", "5", "10", "15", "20", ">20"]
    plotgroups.append(to_plotgroup([long_ins_clipped, long_del_clipped], Constants.PG_LONG_SV,
                               Constants.P_LONG_SV, 44, x_ticks, x_lims, x_labels, output_dir))
    return plotgroups


def to_report(table_json_file, plot_json_file, output_dir):
    log.info("Starting {f} v{v}".format(f=os.path.basename(__file__),
                                        v=__version__))

    with open(table_json_file) as f:
        table_json = json.load(f)

    with open(plot_json_file) as f:
        plot_json = json.load(f)

    tables = [to_sv_table(table_json)]
    plotgroups = to_plotgroups(plot_json, output_dir)
    report = Report(Constants.R_ID, tables=tables, plotgroups=plotgroups)

    return spec.apply_view(report)


def _args_runner(args):
    output_dir = os.path.dirname(args.report)
    report = to_report(args.table_json, args.plot_json, output_dir)
    report.write_json(args.report)
    return 0


def _resolved_tool_contract_runner(rtc):
    output_dir = os.path.dirname(rtc.task.output_files[0])
    report = to_report(rtc.task.input_files[0], rtc.task.input_files[1], output_dir)
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
        "Structural Variants Report",
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

