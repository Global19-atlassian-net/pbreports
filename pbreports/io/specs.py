
"""
Lightweight IO layer for accessing view metadata in report specs.
"""

import os.path as op
import os

from pbcommand.pb_io import load_report_spec_from_json

SPEC_DIR = op.join(op.dirname(op.dirname(__file__)), "report", "specs")
REGISTERED_SPECS = {}


def load_spec(report_id):
    global REGISTERED_SPECS
    if not report_id in REGISTERED_SPECS:
        for file_name in os.listdir(SPEC_DIR):
            full_file_name = op.join(SPEC_DIR, file_name)
            try:
                spec = load_report_spec_from_json(full_file_name)
            except ValueError as err:
                import traceback
                msg = 'Failed to load report spec from {!r}:\n{}'.format(
                    op.abspath(full_file_name), traceback.format_exc())
                raise ValueError(msg)
            REGISTERED_SPECS[spec.id] = spec
    return REGISTERED_SPECS[report_id]


def get_plot_xlabel(spec, plotgroup_id, plot_id):
    return spec.get_plotgroup_spec(plotgroup_id).get_plot_spec(plot_id).xlabel


def get_plot_ylabel(spec, plotgroup_id, plot_id):
    return spec.get_plotgroup_spec(plotgroup_id).get_plot_spec(plot_id).ylabel


def get_plot_title(spec, plotgroup_id, plot_id):
    return spec.get_plotgroup_spec(plotgroup_id).get_plot_spec(plot_id).title


def get_plotgroup_title(spec, plotgroup_id):
    return spec.get_plotgroup_spec(plotgroup_id).title


def get_plot_caption(spec, plotgroup_id, plot_id):
    return spec.get_plotgroup_spec(plotgroup_id).get_plot_spec(plot_id).caption
