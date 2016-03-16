
from pprint import pformat
import functools
import argparse
import logging
import time
import os
import re
import sys

from pbcommand.cli import pbparser_runner
from pbcommand.models.report import Report, Table, Column
from pbcommand.models import FileTypes, get_pbparser
from pbcommand.utils import setup_log
from pbcore.io import openDataFile  # FIXME(nechols)(2016-03-15)

from pbcore.io.BasH5IO import BasH5Reader
from pbcore.io.BarcodeH5Reader import BarcodeH5Reader

from pbreports.io.validators import bas_fofn_to_bas_files, validate_fofn


log = logging.getLogger(__name__)
__version__ = '0.6'


class Constants(object):
    TOOL_ID = "pbreports.tasks.barcode_report"
    TOOL_NAME = "barcode_report"
    DRIVER_EXE = "python -m pbreports.report.barcode --resolved-tool-contract"

    # Some of this is borrowed and modified from pbbarcode
    BAS_PLS_REGEX = r'\.ba[x|s]\.h5$|\.pl[x|s]\.h5$|\.cc[x|s]\.h5$'
    BARCODE_EXT = '.bc.h5'
    BC_REGEX = r'\.bc\.h5'


# FIXME DELETE
def _movie_name_from_file(fn):
    return re.sub('|'.join((Constants.BC_REGEX, Constants.BAS_PLS_REGEX)), '', os.path.basename(fn))


# FIXME DELETE
def _get_movie_in_files(movie_name, file_names):
    movie_file = [
        f for f in file_names if _movie_name_from_file(f) == movie_name]
    if len(movie_file) != 1:
        raise ValueError("Incompatible FOFN files. Movie '{m}' not in {b}".format(
            b=file_names, m=movie_file))
    return movie_file[0]


# FIXME DELETE
def _to_tuple_list(bas_fofn, barcode_fofn):
    """
    Returns a list of [(/path/to/a.bas.h5, /path/to/bc.h5)...] based on
    the movie names

    :raises ValueError if fofn's are incompatible
    """
    bas_files = bas_fofn_to_bas_files(bas_fofn)
    barcode_files = bas_fofn_to_bas_files(barcode_fofn)

    movie_names = set([])
    for fs in [bas_files, barcode_files]:
        for file_name in fs:
            movie_names.add(_movie_name_from_file(file_name))

    s_movie_names = sorted(movie_names)

    # store the results as a list of [(/path/to/a.bas.h5, /path/to/bc.h5),...]
    bas_bc_files = []

    for movie_name in s_movie_names:
        bas_f = _get_movie_in_files(movie_name, bas_files)
        barcode_f = _get_movie_in_files(movie_name, barcode_files)
        bas_bc_files.append((bas_f, barcode_f))

    return bas_bc_files


# FIXME DELETE
def _labels_reads_iterator_h5(reads, barcodes, subreads=True):
    bas_barcode_tuple_list = _to_tuple_list(reads, barcodes)
    log.info("Using {b} with subreads mode? {t}".format(
        b=bas_barcode_tuple_list, t=subreads))
    for item in bas_barcode_tuple_list:
        if len(item) != 2:
            raise ValueError(
                "Expected tuple of (path/to/movie.bas.h5, path/to/movie.bc.h5)")

    for bas_file, barcode_file in bas_barcode_tuple_list:
        log.info("Processing: %s %s" % (bas_file, barcode_file))
        basH5 = BasH5Reader(bas_file)
        bcH5 = BarcodeH5Reader(barcode_file)

        for label in bcH5.barcodeLabels:
            for labeledZmw in bcH5.labeledZmwsFromBarcodeLabel(label):
                zmw = basH5[labeledZmw.holeNumber]
                if zmw is None:
                    continue
                if subreads:
                    reads = zmw.subreads
                else:
                    reads = [zmw.ccsRead]
                if not any(reads):
                    continue
                for read in reads:
                    yield label, read


def _labels_reads_iterator(reads, barcodes):
    with openDataSet(reads) as ds:
        movies = set()
        apply(movies.update, [rr.movieNames for rr in ds.resourceReaders()])
        if len(movies) != 1:  # FIXME
            raise NotImplementedError("Multiple-movie datasets are not " +
                                      "supported by this application.")
        with openDataFile(barcodes) as bc:
            pass


def _run_to_report(labels_reads_iterator, reads, barcodes,
                   subreads=True):
    """ Generate a Report instance from a SubreadSet and BarcodeSet.
    :param subreads: If the ccs fofn is given this needs to be set to False
    """

    class MyRow(object):

        def __init__(self, label):
            self.label = label
            self.bases = 0
            self.reads = 0

    label2row = {}

    for label, read in labels_reads_iterator(reads, barcodes,
                                             subreads=subreads):
        if not label in label2row:
            label2row[label] = MyRow(label)
        label2row[label].bases += len(read)
        label2row[label].reads += 1

    columns = [Column('barcode', header="Barcode Name"),
               Column('number_of_reads', header="Reads"),
               Column('number_of_bases', header="Bases")]

    table = Table('barcode_table', title='Barcodes', columns=columns)
    labels = sorted(label2row.keys())
    for label in labels:
        row = label2row[label]
        table.add_data_by_column_id('barcode', label)
        table.add_data_by_column_id('number_of_reads', row.reads)
        table.add_data_by_column_id('number_of_bases', row.bases)

    report = Report('barcode', tables=[table])
    return report


run_to_report = functools.partial(_run_to_report, _labels_reads_iterator_h5)
run_to_report_bam = functools.partial(_run_to_report, _labels_reads_iterator)


# FIXME should handle exclusively DataSet input
def args_runner(args):
    log.info("Starting {f} version {v} report generation".format(
        f=__file__, v=__version__))
    report = run_to_report(args.subreads, args.barcodes,
                           subreads=not args.ccs)
    log.info(pformat(report.to_dict()))
    report.write_json(args.report_json)
    return 0


def resolved_tool_contract_runner(rtc):
    log.info("Starting {f} version {v} report generation".format(
        f=__file__, v=__version__))
    report = run_to_report_bam(
        reads=rtc.task.input_files[0],
        barcodes=rtc.task.input_files[1],
        subreads=True)
    log.info(pformat(report.to_dict()))
    report.write_json(args.report_json)
    return 0


def get_parser():
    p = get_pbparser(
        tool_id=Constants.TOOL_ID,
        version=__version__,
        name=Constants.TOOL_NAME,
        description=__doc__,
        driver_exe=Constants.DRIVER_EXE)
    p.add_input_file_type(FileTypes.DS_SUBREADS, "subreads",
                          name="BarcodedSubreadSet",
                          description="Barcoded Subread DataSet XML")
    p.add_input_file_type(FileTypes.DS_BARCODE, "barcodes",
                          name="BarcodeSet",
                          description="Barcode DataSet XML")
    p.add_output_file_type(FileTypes.REPORT, "report_json",
                           name="JSON report",
                           description="Path to write Report json output.",
                           default_name="barcode_report")
    # TODO(nechols)(2016-03-15) not yet supported in SA 3.x
    # this is necessary for BasH5Reader to handle the differences between the
    # .ccs.h5 files and .bas.h5 files.
    ap = p.arg_parser.parser
    ap.add_argument('--ccs', action='store_true',
                    help='Use consensus reads instead of subreads.')
    return p


def main(argv=sys.argv[1:]):
    return pbparser_runner(
        argv=argv[1:],
        parser=get_parser(),
        args_runner_func=args_runner,
        contract_runner_func=resolved_tool_contract_runner,
        alog=log,
        setup_log_func=setup_log)


if __name__ == '__main__':
    sys.exit(main())
