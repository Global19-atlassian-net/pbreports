
"""
Wrapper for generating all four dataset reports in a fault-tolerant manner.
Output file is a JSON datastore listing the reports that succeeded.
"""

import logging
import os
import sys

from pbcore.io import SubreadSet
from pbcommand.cli import (pacbio_args_runner,
                           get_default_argparser_with_base_opts)
from pbcommand.validators import validate_file
from pbcommand.utils import setup_log
from pbcommand.models import DataStore, DataStoreFile, FileTypes

from pbreports.model import InvalidStatsError
from pbreports.report import filter_stats_xml
from pbreports.report import adapter_xml
from pbreports.report import loading_xml
from pbreports.report import control

log = logging.getLogger(__name__)
__version__ = "0.1"


def to_reports(subreads, output_dir):
    output_files = []
    log.info("Loading {f}".format(f=subreads))
    ds = SubreadSet(subreads)
    ds.loadStats()
    for base, to_report in [("filter_stats_xml", filter_stats_xml.to_report_impl),
                            ("adapter_xml", adapter_xml.to_report_impl),
                            ("loading_xml", loading_xml.to_report_impl),
                            ("control", control.to_report_impl)]:
        os.chdir(output_dir)
        try:
            os.mkdir(base)
            rpt_output_dir = os.path.join(output_dir, base)
            file_name = os.path.join(rpt_output_dir, "{b}.json".format(b=base))
            report = to_report(ds, rpt_output_dir)
            log.info("Writing {f}".format(f=file_name))
            report.write_json(file_name)
            output_files.append(DataStoreFile(
                uuid=report.uuid,
                source_id="pbreports.report.dataset_reports",
                type_id=FileTypes.REPORT.file_type_id,
                path=file_name,
                is_chunked=False,
                name=base))
        except InvalidStatsError as e:
            log.error("This dataset lacks some required statistics")
            log.error("Skipping generation of {b} report".format(b=base))
    datastore = DataStore(output_files)
    return datastore


def _run_args(args):
    base_output_dir = os.path.dirname(args.datastore)
    datastore = to_reports(args.subreads, base_output_dir)
    datastore.write_json(args.datastore)
    return 0


def _validate_output_file(path):
    if os.path.exists(path):
        raise IOError("The path {p} already exists".format(p=path))
    return os.path.abspath(path)


def _get_parser():
    p = get_default_argparser_with_base_opts(version=__version__,
                                             description=__doc__)
    p.add_argument("subreads", type=validate_file)
    p.add_argument("datastore", type=_validate_output_file)
    return p


def _main(argv=sys.argv[1:]):
    """Main point of Entry"""
    return pacbio_args_runner(
        argv=argv,
        parser=_get_parser(),
        args_runner_func=_run_args,
        alog=log,
        setup_log_func=setup_log)

if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
