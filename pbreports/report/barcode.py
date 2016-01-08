import os
import sys
import time
import logging
import argparse
import re
from pprint import pformat

from pbcore.io.BasH5IO import BasH5Reader
from pbcore.io.BarcodeH5Reader import BarcodeH5Reader

from pbreports.pbsystem_common.cmdline.core import main_runner_default
from pbreports.pbsystem_common.validators import bas_fofn_to_bas_files, validate_fofn

from pbreports.model.model import Report, Table, Column

log = logging.getLogger(__name__)

__version__ = '0.5'

# Some of this is borrowed and modified from pbbarcode
_BAS_PLS_REGEX = r'\.ba[x|s]\.h5$|\.pl[x|s]\.h5$|\.cc[x|s]\.h5$'
_BARCODE_EXT = '.bc.h5'
_BC_REGEX = r'\.bc\.h5'


def _movie_name_from_file(fn):
    return re.sub('|'.join((_BC_REGEX, _BAS_PLS_REGEX)), '', os.path.basename(fn))


def _get_movie_in_files(movie_name, file_names):
    movie_file = [f for f in file_names if _movie_name_from_file(f) == movie_name]
    if len(movie_file) != 1:
        raise ValueError("Incompatible FOFN files. Movie '{m}' not in {b}".format(b=file_names, m=movie_file))
    return movie_file[0]


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


def _labels_reads_iterator(bas_barcode_tuple_list, subreads=True):
    log.info("Using {b} with subreads mode? {t}".format(b=bas_barcode_tuple_list, t=subreads))
    for item in bas_barcode_tuple_list:
        if len(item) != 2:
            raise ValueError("Expected tuple of (path/to/movie.bas.h5, path/to/movie.bc.h5)")

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


def run_to_report(bas_barcode_tuple_list, subreads=True):
    """ Generate a Report instance from a list of tuples.

    :param bas_barcode_tuple_list: [(path/to/movie.bas.h5, path/to/movie.bc.h5), ...]
    :param subreads: If the ccs fofn is given this needs to be set to False
    """

    class MyRow(object):

        def __init__(self, label):
            self.label = label
            self.bases = 0
            self.reads = 0

    label2row = {}

    for label, read in _labels_reads_iterator(bas_barcode_tuple_list, subreads=subreads):
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


def args_runner(args):
    # generate list of tuples
    bas_barcode_tuple_list = _to_tuple_list(args.bas_fofn, args.barcode_fofn)

    use_subreads = not args.ccs

    report = run_to_report(bas_barcode_tuple_list, subreads=use_subreads)
    log.info(pformat(report.to_dict()))
    report.write_json(args.report_json)
    return 0


def get_parser():
    p = argparse.ArgumentParser(version=__version__)

    p.add_argument('bas_fofn', help="Bas h5 FOFN.", type=validate_fofn)
    p.add_argument('barcode_fofn', type=validate_fofn, help="Barcode h5 FOFN.")

    p.add_argument('report_json',
                   help="Path to write Report json output.")
    p.add_argument('--debug', action='store_true',
                   help='Flag to debug to stdout.')
    # this is necessary for BasH5Reader to handle the differences between the
    # .ccs.h5 files and .bas.h5 files.
    p.add_argument('--ccs', action='store_true',
                   help='Use consensus reads instead of subreads.')

    p.set_defaults(func=args_runner)
    return p


def main(argv=sys.argv):
    """Main point of Entry"""
    log.info("Starting {f} version {v} report generation".format(f=__file__, v=__version__))
    return main_runner_default(argv[1:], get_parser(), log)


if __name__ == '__main__':
    sys.exit(main())
