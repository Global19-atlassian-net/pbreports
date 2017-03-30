import os
import os.path as op
import logging
import sys
import json
import itertools

from pbcommand.models.report import Report, Table, Column, Plotgroup, Plot
from pbcommand.models import FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log
from pbreports.io.specs import *

__version__ = '0.1.0'


class Constants(object):
    TOOL_ID = "pbreports.tasks.structural_variants_report"
    DRIVER_EXE = ("python -m pbreports.report.structural_variants "
                  "--resolved-tool-contract ")
    R_ID = "structural_variants"

    T_ID = "anno_table"
    C_ANNOTATION = "annotation"
    C_INS_N = "insertions_n"
    C_INS_MEAN = "insertions_mean"
    C_INS_SUM = "insertions_sum"
    C_DEL_N = "deletions_n"
    C_DEL_MEAN = "deletions_mean"
    C_DEL_SUM = "deletions_sum"
    C_INDEL_N = "indel_n"
    C_INDEL_SUM = "indel_sum"

    PG_SHORT_SV = "short_sv_plot_group"
    P_SHORT_SV = "short_sv_plot"
    PG_LONG_SV = "long_sv_plot_group"
    PG_LONG_SV = "long_sv_plot"


log = logging.getLogger(__name__)
spec = load_spec(Constants.R_ID)


def to_sv_table(table_json):
    
    col_ids = [Constants.C_ANNOTATION, Constants.C_INS_N, Constants.C_INS_MEAN,
               Constants.C_INS_SUM, Constants.C_DEL_N, Constants.C_DEL_MEAN,
               Constants.C_DEL_SUM, Constants.C_INDEL_N, Constants.C_INDEL_SUM]

    t = []
    for anno, vals in table_json.iteritems():
        r = [str(anno)]
        r.extend([int(x) for x in vals[0:6]])
        r.extend([float(x) for x in vals[6:8]])
        t.append(r)

    table = zip(*t)

    columns = []
    for i, col_id in enumerate(col_ids):
        columns.append(Column(col_id, values=table[i]))

    sv_table = Table(Constants.T_ID, columns=columns)

    return sv_table
    

def to_short_plotgroup(plot_json, output_dir):
    plot_name = get_plot_title(spec, Constants.PG_SHORT_SV, Constants.P_SHORT_SV)
    x_label = get_plot_xlabel(spec, Constants.PG_SHORT_SV, Constants.P_SHORT_SV)
    y_label = get_plot_ylabel(spec, Constants.PG_SHORT_SV, Constants.P_SHORT_SV)
    insertions = [x for x in plot_json["Insertion"] if x < 1000]
    deletions = [x for x in plot_json["Deletion"] if x < 1000]
    fig, ax = get_fig_axes_lpr()
    ax.hist(insertions, label="Insertions", histtype='barstacked',
            alpha=0.3, bins=20, range=[0, 1000])
    ax.hist(deletions, label="Deletions", histtype='barstacked',
            alpha=0.3, bins=20, range=[0, 1000])
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    png_fn = os.path.join(output_dir, "{p}.png".format(p=Constants.P_SHORT_SV))
    png_base, thumbnail_base = save_figure_with_thumbnail(fig, png_fn, dpi=72)
    short_plot = Plot(Constants.P_SHORT_SV,
                    os.path.relpath(png_base, output_dir),
                    title=plot_name, caption=plot_name,
                    thumbnail=os.path.relpath(thumbnail_base, output_dir))
    plot_group = PlotGroup(Constants.PG_SHORT_SV, plots=[short_plot])
    return plot_group


def to_long_plotgroup(plot_json, output_dir):
    plot_name = get_plot_title(spec, Constants.PG_LONG_SV, Constants.P_LONG_SV)
    x_label = get_plot_xlabel(spec, Constants.PG_LONG_SV, Constants.P_LONG_SV)
    y_label = get_plot_ylabel(spec, Constants.PG_LONG_SV, Constants.P_LONG_SV)
    insertions = [x for x in plot_json["Insertion"] if 1000 <= x < 20000]
    deletions = [x for x in plot_json["Deletion"] if 1000 <= x < 20000]
    fig, ax = get_fig_axes_lpr()
    ax.hist(insertions, label="Insertions", histtype='barstacked',
            alpha=0.3, bins=38, range=[1000, 20000])
    ax.hist(deletions, label="Deletions", histtype='barstacked',
            alpha=0.3, bins=38, range=[1000, 20000])
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    png_fn = os.path.join(output_dir, "{p}.png".format(p=Constants.P_LONG_SV))
    png_base, thumbnail_base = save_figure_with_thumbnail(fig, png_fn, dpi=72)
    short_plot = Plot(Constants.P_LONG_SV,
                    os.path.relpath(png_base, output_dir),
                    title=plot_name, caption=plot_name,
                    thumbnail=os.path.relpath(thumbnail_base, output_dir))
    plot_group = PlotGroup(Constants.PG_LONG_SV, plots=[long_plot])
    return plot_group


def to_report(table_json_file, plot_json_file, output_dir):
    log.info("Starting {f} v{v}".format(f=os.path.basename(__file__),
                                        v=__version__))

    with open(table_json_file) as f:
        table_json = json.load(f)

    with open(plot_json_file) as f:
        plot_json = json.load(f)

    tables = [to_sv_table(table_json)]
    plotgroups = [to_short_plotgroup(plot_json, output_dir),
                  to_long_plotgroup(plot_json, output_dir)]
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
        is_distributed=True)
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

