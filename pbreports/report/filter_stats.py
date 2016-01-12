import os
import logging
import sys
import functools
import operator
import argparse
import warnings

import numpy as np

from pbreports.pbsystem_common.cmdline.core import main_runner_default
from pbreports.pbsystem_common.validators import validate_dir, validate_file
from pbreports.model.model import Report, Attribute, Table, Column
from pbreports.plot.helper import get_green, get_blue
from pbreports.util import compute_n50_from_bins
from pbreports.model.aggregators import (CountAggregator, MeanAggregator,
                                         SumAggregator, HistogramAggregator,
                                         MinAggregator, MaxAggregator,
                                         BaseAggregator)


from pbreports.report.streaming_utils import (PlotViewProperties,
                                              to_plot_groups,
                                              custom_read_accuracy_histogram,
                                              custom_read_length_histogram)

__version__ = '3.2'

log = logging.getLogger(__name__)

_REQUIRED_HEADER_FIELDS = ('Readlength', 'ReadScore',
                           'PassedFilter', 'SequencingZMW', "ReadId")

# Format is { Name: ( dType, f(str->dType) ) }
VALID_COLUMNS = {"Movie": ("|S64", str),
                 "ReadId": ("|S64", str),
                 "#Bases": (int, int),
                 "Readlength": (int, int),
                 "ReadScore": (float, float),
                 "Productivity": (int, int),
                 "SequencingZMW": (int, int),
                 "PassedFilter": (int, int),
                 "Sandwiches": (int, int),
                 "Whitelisted": (int, int),
                 "SNR": (float, float),
                 "ArtifactScore": ("|S64", str)}

COLUMN_TYPES = {k: operator.getitem(v, 1)
                for k, v in VALID_COLUMNS.iteritems()}

class Constants(object):
    R_ID = 'filtering_report'

    #Plot Groups
    PG_READ_LENGTH = "filter_readlength"
    PG_READ_SCORE = "filter_quality"

    # Plots
    P_PRE_FILTER_READ_LENGTH_HIST = "pre_filter_readlength_histogram"
    P_POST_FILTER_READ_LENGHT_HIST = "post_filter_readlength_histogram"
    P_PRE_FILTER_READ_SCORE_HIST = "pre_filterread_score_histogram"
    P_POST_FILTER_READ_SCORE_HIST = "post_filterread_score_histogram"

    # Images
    I_PRE_FILTER_READ_LENGTH = "pre_filter_readlength_histogram.png"
    I_POST_FILTER_READ_LENGTH = "post_filter_readlength_histogram.png"
    I_PRE_FILTER_READ_SCORE = "pre_filterread_score_histogram.png"
    I_POST_FILTER_READ_SCORE = "post_filterread_score_histogram.png"

    # Attributes
    A_BASE_N_POST_FILTER = "base_n_post_filter"
    A_BASE_N_PRE_FILTER = "base_n_pre_filter"
    A_MEAN_READ_LENGTH_POST_FILTER = "mean_read_length_post_filter"
    A_MEAN_READ_LENGTH_PRE_FILTER = "mean_read_length_pre_filter"
    A_MEAN_READ_SCORE_POST_FILTER = "mean_read_score_post_filter"
    A_MEAN_READ_SCORE_PRE_FILTER = "mean_read_score_pre_filter"
    A_READS_N_POST_FILTER = "reads_n_post_filter"
    A_READS_N_PRE_FILTER = "reads_n_pre_filter"
    A_N50_READ_LENGTH_PRE_FILTER = "n50_read_length_pre_filter"
    A_N50_READ_LENGTH_POST_FILTER = "n50_read_length_post_filter"

    # Tables
    T_FILTER_STATS = "filter_stats_table"

    #Columns
    C_METRICS = "metrics"
    C_PRE_FILTER = "pre_filter"
    C_POST_FILTER = "post_filter"


class CountBases(SumAggregator):

    def apply(self, record):
        self.total += getattr(record, self.record_field)


class N50Aggregator(BaseAggregator):

    def __init__(self, record_field, max_bins=1000):
        self.record_field = record_field
        self.max_bins = int(max_bins)
        self.bins = np.zeros(max_bins, dtype=np.int32)

    def apply(self, record):
        value = getattr(record, self.record_field)
        if int(value) > self.bins.size:
            self.bins.resize(int(value)+1)
            # np.resize to larger size also fills the extra elements with zeros
            self.bins[int(value)]  = 1
        else:
            self.bins[int(value)] += 1

    def __repr__(self):
        _d = dict(k=self.__class__.__name__,
                  n=len(self.bins),
                  a=self.attribute)
        return "<{k} nbins:{n} attribute:{a} >".format(**_d)

    @property
    def attribute(self):
        if len(self.bins) == 0:
            # No values? Probably should raise an exception?
            return 0.0

        return compute_n50_from_bins(self.bins)


class _BaseFilterException(Exception):
    pass


class CsvParserError(_BaseFilterException):
    pass


class NoFilteredReadsError(_BaseFilterException):
    pass


class NoPassedFilteredReadsError(_BaseFilterException):
    pass


def _get_header_fields_from_csv(file_name):
    """Peak into the CSV file and extract the column headers.

    :raises: CsvParserError if unable to extract column headers.
    """
    with open(file_name, 'r') as f:
        header = f.readline()

    if ',' in header.rstrip():
        return header.rstrip().split(',')
    else:
        msg = "Malformed CSV. Enable to get column headers in {h}.".format(
            h=header)
        raise CsvParserError(msg)


def _validate_header(headers):
    return all([field in headers for field in _REQUIRED_HEADER_FIELDS])


class Record(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        o = " ".join([''.join([x, '=', str(getattr(self, x))])
                     for x in _REQUIRED_HEADER_FIELDS])
        _d = dict(k=self.__class__.__name__, o=o)
        return "<{k} {o}>".format(**_d)


def _row_to_record(column_names, row):
    if ',' not in row:
        raise CsvParserError("Malformed row {r}".format(r=row))
    d = {}
    for name, value in zip(column_names, row.strip().split(',')):
        t = COLUMN_TYPES[name]
        # print row
        # print name, t, value
        v = t(value)
        d[name] = v

    r = Record(**d)
    return r


def _filter_record_by_attribute(attr_name, func, value, record):
    v = getattr(record, attr_name)
    return func(value, v)


def _filter_record(filter_func, record):
    """Returns Bool"""
    return filter_func(record)


def null_filter(record):
    return True


def _multi_filter_record(filter_funcs, record):
    """Returns Bool"""
    for filter_func in filter_funcs:
        if not filter_func(record):
            # Bail out at the first chance
            return False

    return True


def _apply(filter_funcs, aggregators, record):
    """Run the filters and call apply method on the aggregator if
    the record passes filtering.
    """
    if not isinstance(filter_funcs, (list, tuple)):
        filter_funcs = [filter_funcs]

    if not isinstance(aggregators, (list, tuple)):
        aggregators = [aggregators]

    if _multi_filter_record(filter_funcs, record):
        for aggregator in aggregators:
            aggregator.apply(record)


def applyer(row_to_record_func, iterable, funcs):
    for it in iterable:
        record = row_to_record_func(it)
        for func in funcs:
            func(record)

        del record


def to_table(pre_filter_data, post_filter_data):
    """Create a pbreports.model.Table instance

    Data list must be:
        number of bases,
        number of reads,
        mean readlength
        mean readscore
    """

    metric_names = ["Polymerase Read Bases",
                    "Polymerase Reads",
                    "Polymerase Read N50",
                    "Polymerase Read Length",
                    "Polymerase Read Quality"
                    ]

    columns = [Column(Constants.C_METRICS, header="Metrics", values=metric_names),
               Column(Constants.C_PRE_FILTER, header="Pre-Filter", values=pre_filter_data),
               Column(Constants.C_POST_FILTER, header="Post-Filter", values=post_filter_data)]

    table = Table(Constants.T_FILTER_STATS, title="Filtering", columns=columns)

    log.debug(table)

    return table


def _plot_view_configs():
    """
    Any change to the 'raw' view of a report plot should be changed here.
    """

    _p = [PlotViewProperties(Constants.P_PRE_FILTER_READ_LENGTH_HIST,
                             Constants.PG_READ_LENGTH,
                             custom_read_length_histogram,
                             Constants.I_PRE_FILTER_READ_LENGTH,
                             xlabel="ReadLength",
                             ylabel="Reads",
                             rlabel="bp > Read Length",
                             title="Pre-Filter",
                             color=get_green(3),
                             edgecolor=get_green(2),
                             plot_group_title="Polymerase Read Length"),
          PlotViewProperties(Constants.P_POST_FILTER_READ_LENGHT_HIST,
                             Constants.PG_READ_LENGTH,
                             custom_read_length_histogram,
                             Constants.I_POST_FILTER_READ_LENGTH,
                             xlabel="ReadLength",
                             ylabel="Reads",
                             rlabel="bp > Read Length",
                             title="Post-Filter",
                             color=get_green(3),
                             edgecolor=get_green(2),
                             use_group_thumb=True,
                             plot_group_title="Polymerase Read Length"),
          PlotViewProperties(Constants.P_PRE_FILTER_READ_SCORE_HIST,
                             Constants.PG_READ_SCORE,
                             custom_read_accuracy_histogram,
                             Constants.I_PRE_FILTER_READ_SCORE,
                             xlabel="Read Quality",
                             ylabel="Reads",
                             rlabel="bp > Read Quality",
                             title="Pre-Filter",
                             color=get_blue(3),
                             edgecolor=get_blue(2),
                             plot_group_title="Polymerase Read Quality"),
          PlotViewProperties(Constants.P_POST_FILTER_READ_SCORE_HIST,
                             Constants.PG_READ_SCORE,
                             custom_read_accuracy_histogram,
                             Constants.I_POST_FILTER_READ_SCORE,
                             xlabel="Read Quality",
                             ylabel="Reads",
                             rlabel="bp > Read Quality",
                             title="Post-Filter",
                             color=get_blue(3),
                             edgecolor=get_blue(2),
                             use_group_thumb=True,
                             plot_group_title="Polymerase Read Quality")
          ]

    # make it easier to access
    return {v.plot_id: v for v in _p}


def __default_attribute_display_names():
    _d = {Constants.A_BASE_N_POST_FILTER: 'Number of Bases',
          Constants.A_BASE_N_PRE_FILTER: 'Number of Bases',
          Constants.A_MEAN_READ_LENGTH_POST_FILTER: 'Mean Read Length',
          Constants.A_MEAN_READ_LENGTH_PRE_FILTER: 'Mean Read Length',
          Constants.A_MEAN_READ_SCORE_POST_FILTER: 'Mean Read Score',
          Constants.A_MEAN_READ_SCORE_PRE_FILTER: 'Mean Read Score',
          Constants.A_READS_N_POST_FILTER: 'Number of Reads',
          Constants.A_READS_N_PRE_FILTER: 'Number of Reads',
          Constants.A_N50_READ_LENGTH_POST_FILTER: "N50 Read Length",
          Constants.A_N50_READ_LENGTH_PRE_FILTER: "N50 Read Length"}

    return _d


def id_to_display_name(id_):
    display_names = __default_attribute_display_names()
    return display_names[id_]


def to_attributes(**kw):
    """create a list of attributes from {id:aggregator}"""
    attributes = []
    for id_, ag in kw.iteritems():
        name = id_to_display_name(id_)
        v = ag.attribute
        a = Attribute(id_, v, name=name)
        attributes.append(a)
    return attributes


def _log_aggros(id_to_ags):
    for i, a in id_to_ags.iteritems():
        log.info((i, a))


def to_report(filter_csv, output_dir, dpi=72):
    """Main point of entry

    The filter stats report has two main modes.

    All Reads: (i.e., PreFilter)

    SequencingZMW > 0
    - total bases
    - total number of reads
    - n50
    - mean readlength
    - mean readscore

    HQ Region: (i.e., PostFilter)

    PassedFilter > 0, SequencingZMW > 0
    - total bases
    - total number of reads
    - n50
    - mean readlength
    - mean readscore


    Generates:
    - Pre and Post filter ReadLength histograms with SDF (with thumbnails)
    - Pre and Post filter ReadScore Histogram with SDF (with thumbnails)
    - Pre and Post table of total bases, # of reads, mean readlengh, mean readscore


    :type filter_csv: str
    :type output_dir: str
    :type dpi: int

    :rtype: Report
    """
    log.info("Analyzing CSV {f}".format(f=filter_csv))

    # A little sanity checking
    csv_header_fields = _get_header_fields_from_csv(filter_csv)
    if not _validate_header(csv_header_fields):
        raise CsvParserError("Unable to find required fields {r} in {f}.".format(
            r=_REQUIRED_HEADER_FIELDS, f=filter_csv))

    P = functools.partial

    row_to_rec_func = P(_row_to_record,
                        _get_header_fields_from_csv(filter_csv))

    # General Filters
    # General construct to create a func with signature f(record) -> Bool
    seq_zmw_filter_f = lambda record: record.SequencingZMW > 0
    hq_filter_f = lambda record: record.PassedFilter > 0

    # Pre-Filter Aggregator(s)
    nbases_ag = SumAggregator('Readlength')
    nreads_ag = CountAggregator('Readlength')
    readlength_ag = MeanAggregator('Readlength')
    max_readlength_ag = MaxAggregator('Readlength')
    min_readlength_ag = MinAggregator('Readlength')
    # the histogram is adaptively computed. The min value and dx is the
    readlength_hist_ag = HistogramAggregator('Readlength', 0, dx=100)
    read_score_hist_ag = HistogramAggregator('ReadScore', 0, dx=0.002)

    # n50_ag = N50Aggregator('Readlength', max_bins=200000)
    pre_n50_ag = N50Aggregator('Readlength', max_bins=200000)

    readscore_ag = SumAggregator('ReadScore', total=0)
    readscore_mean_ag = MeanAggregator('ReadScore')

    # Create/bind core Functions that can be based to the applyer method
    # Calling these 'Models'. A model is list of filters and an aggregator
    # Signature to _apply is ([filter1, filter2], aggregator, record)
    # calling functools.partial returns a function signature f(record)
    pre_filters = [seq_zmw_filter_f]
    pre_agros = [nbases_ag, nreads_ag,
                 readscore_ag, readscore_mean_ag,
                 min_readlength_ag, max_readlength_ag,
                 readlength_ag,
                 readlength_hist_ag,
                 read_score_hist_ag,
                 pre_n50_ag]

    pre_models = [P(_apply, pre_filters, pre_agros)]

    # Post-Filter Aggregator(s)
    post_nbases_ag = SumAggregator('Readlength')
    post_nreads_ag = CountAggregator('Readlength')
    post_readlength_ag = MeanAggregator('Readlength')
    post_min_readlength_ag = MinAggregator('Readlength')
    post_max_readlength_ag = MaxAggregator('Readlength')
    # the histogram is adaptively computed. The min value and dx is the
    post_readlength_hist_ag = HistogramAggregator('Readlength', 0, dx=100)
    post_readscore_hist_ag = HistogramAggregator('ReadScore', 0, dx=0.002)

    post_readscore_ag = SumAggregator('ReadScore')
    post_readscore_mean_ag = MeanAggregator('ReadScore')

    post_n50_ag = N50Aggregator('Readlength', max_bins=200000)

    # Post Filter Models
    post_filters = [seq_zmw_filter_f, hq_filter_f]

    post_agros = [post_nbases_ag, post_nreads_ag,
                  post_readlength_ag, post_readscore_ag,
                  post_min_readlength_ag, post_max_readlength_ag,
                  post_readscore_mean_ag,
                  post_n50_ag,
                  post_readlength_hist_ag, post_readscore_hist_ag]

    post_models = [P(_apply, post_filters, post_agros)]

    models = pre_models + post_models

    with open(filter_csv, 'r') as f:
        # read in header
        _ = f.readline()
        applyer(row_to_rec_func, f, models)

    # Sanity Checking of data
    # Look for csv files with only the csv header (i.e., empty with no data)
    if nreads_ag.attribute < 1:
        msg = "No filtered reads found in {f}. Unable to generate FilterStats report".format(
            f=filter_csv)
        raise NoFilteredReadsError(msg)

    # Exit if all the reads were filtered out.
    if post_nreads_ag.attribute < 1:
        msg = "No filtered reads found in {f}. Unable to generate report.".format(
            f=filter_csv)
        raise NoPassedFilteredReadsError(msg)

    # this is getting really messy
    id_to_aggro = {Constants.A_BASE_N_POST_FILTER: post_nbases_ag,
                   Constants.A_BASE_N_PRE_FILTER: nbases_ag,
                   Constants.A_MEAN_READ_LENGTH_POST_FILTER: post_readlength_ag,
                   Constants.A_MEAN_READ_LENGTH_PRE_FILTER: readlength_ag,
                   Constants.A_MEAN_READ_SCORE_POST_FILTER: post_readscore_mean_ag,
                   Constants.A_MEAN_READ_SCORE_PRE_FILTER: readscore_mean_ag,
                   Constants.A_READS_N_POST_FILTER: post_nreads_ag,
                   Constants.A_READS_N_PRE_FILTER: nreads_ag,
                   Constants.A_N50_READ_LENGTH_PRE_FILTER: pre_n50_ag,
                   Constants.A_N50_READ_LENGTH_POST_FILTER: post_n50_ag}

    _log_aggros(id_to_aggro)

    attributes = to_attributes(**id_to_aggro)

    plot_aggregators = {Constants.P_PRE_FILTER_READ_LENGTH_HIST: readlength_hist_ag,
                        Constants.P_POST_FILTER_READ_LENGHT_HIST: post_readlength_hist_ag,
                        Constants.P_PRE_FILTER_READ_SCORE_HIST: read_score_hist_ag,
                        Constants.P_POST_FILTER_READ_SCORE_HIST: post_readscore_hist_ag}

    _log_aggros(plot_aggregators)

    # this is dict of {id:PlotView instances}
    view_configs = _plot_view_configs()
    plot_groups = to_plot_groups(view_configs, output_dir, plot_aggregators)

    # Temp lists to Create Pbreports Table
    # Each list has [nbases, nreads, n50, mean readlength, mean readscore]
    _pre_filter = [nbases_ag.attribute,
                   nreads_ag.attribute,
                   pre_n50_ag.attribute,
                   readlength_ag.attribute,
                   np.round(readscore_mean_ag.attribute, decimals=3)]

    _post_filter = [post_nbases_ag.attribute,
                    post_nreads_ag.attribute,
                    post_n50_ag.attribute,
                    post_readlength_ag.attribute,
                    np.round(post_readscore_mean_ag.attribute, decimals=3)]

    table = to_table(_pre_filter, _post_filter)

    report = Report(Constants.R_ID, tables=[table], plotgroups=plot_groups,
                    attributes=attributes)

    log.debug(report)
    for attribute in report.attributes:
        log.debug(attribute)

    log.info(str(report.tables[0]))
    return report


def args_runner(args):
    log.info("Starting {f} v{v}".format(f=os.path.basename(__file__),
                                        v=__version__))
    report = to_report(args.filter_summary_csv, args.output_dir, dpi=args.dpi)
    report.write_json(args.json_report)
    return 0


def get_parser():
    desc = ""
    parser = argparse.ArgumentParser(version=__version__, description=desc)
    parser.add_argument('filter_summary_csv', type=validate_file,
                        help="Filter CSV file.")
    parser.add_argument(
        '-o', "--output", dest='output_dir', default=os.getcwd(), type=validate_dir,
        help="Output directory for histogram images generated")
    parser.add_argument('-r', '--report', dest='json_report',
                        help='Path of JSON report.')
    parser.add_argument("--dpi", default=60, type=int,
                        help="dots/inch")
    parser.add_argument('--debug', action='store_true',
                        help="Enable debug mode to stdout.")

    parser.set_defaults(func=args_runner)
    return parser


def main(argv=sys.argv):
    """Main point of Entry"""
    log.info("Starting {f} version {v} report generation".format(f=__file__, v=__version__))
    return main_runner_default(argv[1:], get_parser(), log)

