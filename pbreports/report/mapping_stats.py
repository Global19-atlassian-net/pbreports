
"""
Generates a report of statistics for subreads mapped to a reference genome with
Blasr/pbalign.
"""

from collections import OrderedDict
import sys
import os
import math
import time
import functools
import logging

import numpy as np

from pbcommand.models.report import (Attribute, Report, Table, Column, Plot,
    PlotGroup)
from pbcommand.models import TaskTypes, FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log
from pbcore.io import openAlignmentFile, openDataSet
from pbcore.io import AlignmentSet, ConsensusAlignmentSet

from pbreports.plot.rainbow import make_rainbow_plot
from pbreports.plot.helper import get_blue, get_green
from pbreports.util import compute_n50_from_bins
from pbreports.io.align import (from_alignment_file, CrunchedAlignments)
from pbreports.report.streaming_utils import (PlotViewProperties,
                                              to_plot_groups, get_percentile,
                                              generate_plot)

log = logging.getLogger(__name__)

__version__ = '4.2.0'
TOOL_ID = "pbreports.tasks.mapping_stats"

SUBREAD_TYPE = 'SubreadType'
READ_TYPE = 'ReadType'

DATA_TYPES = (READ_TYPE, SUBREAD_TYPE)


class Constants(object):
    # Report Id
    R_ID = "mapping_stats"

    # Column ids
    C_MOVIE = "movie"
    C_READS = "mapped_reads"
    C_READLENGTH = "mapped_polymerase_read_length"
    C_READLENGTH_N50 = "mapped_polymerase_read_length_n50"
    C_SUBREADS = "mapped_subreads"
    C_SUBREAD_NBASES = "mapped_subread_base"
    C_SUBREAD_LENGTH = "mapped_subread_length"
    C_SUBREAD_ACCURACY = "mapped_subread_accuracy"

    # Table id
    #
    T_STATS = "mapping_stats_table"

    # Attribute Ids
    A_NBASES = "mapped_bases_n"
    A_NREADS = "mapped_reads_n"
    A_READLENGTH = "mapped_readlength_mean"
    A_READLENGTH_Q95 = "mapped_readlength_q95"
    A_READLENGTH_MAX = "mapped_readlength_max"
    A_READLENGTH_N50 = "mapped_readlength_n50"

    A_NSUBREADS = "mapped_subreads_n"
    A_SUBREAD_NBASES = "mapped_subread_bases_n"
    A_SUBREAD_ACCURACY = "mapped_subread_accuracy_mean"
    A_SUBREAD_QUALITY = "mapped_subread_read_quality_mean"
    A_SUBREAD_LENGTH = "mapped_subread_readlength_mean"
    A_SUBREAD_LENGTH_MAX = "mapped_subread_readlength_max"
    A_SUBREAD_LENGTH_N50 = "mapped_subreadlength_n50"
    A_SUBREAD_LENGTH_Q95 = "mapped_subreadlength_q95"

    # Plot Group ids
    PG_SUBREAD_ACCURACY = "subread_accuracy_group"
    PG_SUBREAD_LENGTH = "subreadlength_plot"
    PG_READLENGTH = "readlength_plot"
    PG_RAINBOW = "rainbow_plot"

    # Plot ids
    P_SUBREAD_ACCURACY = "subread_accuracy_group_accuracy_plot"
    P_SUBREAD_LENGTH = "subreadlength_plot"
    P_READLENGTH = "readlength_plot"
    P_RAINBOW = "rainbow_plot"

    # XXX for CCS report - easier to put it here
    A_READ_ACCURACY = "mapped_read_accuracy_mean"
    C_READ_ACCURACY = "mapped_read_accuracy"
    P_READ_ACCURACY = "read_accuracy_group_accuracy_plot"
    PG_READ_ACCURACY = "read_accuracy_group"
    C_READ_NBASES = "mapped_bases"


def _validate_file_or_none(arg):
    if arg is None:
        return None
    else:
        return validate_file(arg)


class _MetaKlassAggregator(type):

    def __new__(cls, name, parents, dct):
        """
        A little bit of basic checking to make sure the subclasses are well formed.
        """
        _REQUIRED = 'apply __repr__'.split()

        if name not in ('BaseAggregator', '_BaseHistogram', '_MeanAggregator', '_BaseTotalAggregator'):
            for required in _REQUIRED:
                was_found = False
                if required in dct:
                    was_found = True
                else:
                    # look to super classes
                    for parent in parents:
                        if hasattr(parent, required):
                            was_found = True

                if not was_found:
                    raise ValueError(
                        "{r} must be defined for class {c}".format(c=name, r=required))

        return super(_MetaKlassAggregator, cls).__new__(cls, name, parents, dct)


class BaseAggregator(object):
    __metaclass__ = _MetaKlassAggregator
    DATA_TYPE = None


class AttributeAble(object):

    """
    Any aggregator that is to be used as a pbreport.model.Attribute,
    must implement this interface.
    """
    @property
    def attribute(self):
        raise NotImplemented


class _BaseTotalAggregator(BaseAggregator, AttributeAble):

    """Base class for summing values"""

    def __init__(self, value=0):
        self.value = value

    def apply(self, crunched_npa):
        self.value += len(crunched_npa)

    @property
    def attribute(self):
        return self.value

    def __repr__(self):
        _d = dict(k=self.__class__.__name__,
                  t=self.value)
        return "<{k} total={t} >".format(**_d)

    def __add__(self, other):
        if isinstance(other, self.__class__):
            total = self.value + other.value
            return self.__class__(total=total)
        else:
            _d = dict(s=type(self), o=type(other))
            raise TypeError("Incompatible types. {s} {o}".format(**_d))


class _MeanAggregator(BaseAggregator, AttributeAble):
    NP_FIELD = None

    def __init__(self, nvalues=0, total=0):
        self.nvalues = nvalues
        self.total = total

    def apply(self, crunched_npa):
        self.nvalues += crunched_npa[self.NP_FIELD].shape[0]
        self.total += crunched_npa[self.NP_FIELD].sum()

    @property
    def attribute(self):
        return self.mean

    @property
    def mean(self):
        if self.nvalues == 0:
            # Maybe this is not the expected result
            return 0.0
        return self.total / float(self.nvalues)

    def __repr__(self):
        _d = dict(k=self.__class__.__name__,
                  n=self.nvalues,
                  t=self.total,
                  m=self.mean)
        return "<{k} nvalues:{n} total:{t} mean:{m} >".format(**_d)

    def __add__(self, other):
        if isinstance(other, self.__class__):
            nvalues = self.nvalues + other.nvalues
            total = self.total + other.total
            return self.__class__(nvalues=nvalues, total=total)
        else:
            _d = dict(s=type(self), o=type(other))
            raise TypeError("Incompatible types. {s} {o}".format(**_d))


class _BaseHistogram(BaseAggregator):

    def __init__(self, dx=100.0, nbins=1000, dtype=np.int32):
        """
        :param dx: float, int
        :param nbins: int
        :param dtype: type used to create the np array
        """
        self.dx = dx
        self.dtype = dtype
        self.bins = np.zeros(nbins, dtype=np.int32)

    @property
    def nbins(self):
        return len(self.bins)

    @property
    def bin_edges(self):
        """Used for plotting cdf

        ds = zip(self.bin_edges, self.bins)

        c = to_cdf(ds)

        plot(self.bin_edges, c)
        plot(self.bin_edges, self.bins)

        """
        return [self.dx * i for i in xrange(self.nbins)]

    def apply(self, npa):
        """This will be readlengths"""
        raise NotImplemented

    def __repr__(self):
        x = self.dx * self.nbins
        _d = dict(k=self.__class__.__name__,
                  d=self.dx,
                  n=self.nbins,
                  x=x,
                  i=0)
        return "<{k} dx:{d} nbins:{n} min:{i} max:{x} >".format(**_d)

    def __add__(self, other):
        raise NotImplemented


# Read Aggregator Classes

class ReadCounterAggregator(_BaseTotalAggregator):
    DATA_TYPE = READ_TYPE

    def apply(self, npa):
        self.value += len(npa)


class NumberBasesAggregator(_BaseTotalAggregator):
    DATA_TYPE = READ_TYPE

    def apply(self, npa):
        self.value += npa.sum()

    @property
    def attribute(self):
        return int(self.value)


class MaxReadLengthAggregator(_BaseTotalAggregator):
    DATA_TYPE = READ_TYPE

    def apply(self, npa):
        value = npa.max()
        if value > self.value:
            self.value = value

    def __add__(self, other):
        if isinstance(other, self.__class__):
            value = max(self.value, other.value)
            return self.__class__(value=value)
        else:
            _d = dict(s=type(self), o=type(other))
            raise TypeError("Incompatible types. {s} {o}".format(**_d))


class MeanReadLengthAggregator(_MeanAggregator, AttributeAble):
    DATA_TYPE = READ_TYPE

    def apply(self, npa):
        self.nvalues += npa.shape[0]
        self.total += npa.sum()

    @property
    def attribute(self):
        return int(np.round(self.mean))


class ReadLengthHistogram(_BaseHistogram):
    DATA_TYPE = READ_TYPE

    def apply(self, npa):
        """This will be readlengths"""
        for value in npa:
            i = int(math.ceil(value / self.dx))
            # add
            if i > self.bins.size:
                self.bins.resize(i+1)
            self.bins[i] += 1


class N50Aggreggator(BaseAggregator, AttributeAble):
    DATA_TYPE = READ_TYPE

    def __init__(self, max_bins=200000):
        self.max_bins = int(max_bins)
        self.bins = np.zeros(self.max_bins)

    def __repr__(self):
        _d = dict(k=self.__class__.__name__,
                  n=len(self.bins),
                  a=self.attribute)
        return "<{k} nbins:{n} attribute:{a} >".format(**_d)

    def apply(self, npa):
        for value in npa:
            if int(value) > self.bins.size:
                self.bins.resize(int(value)+1)
            self.bins[int(value)] += 1

    @property
    def attribute(self):
        return compute_n50_from_bins(self.bins)


class SubreadN50Aggregator(BaseAggregator, AttributeAble):
    DATA_TYPE = SUBREAD_TYPE

    def __init__(self, max_bins=200000):
        self.bins = np.zeros(max_bins)

    def apply(self, crunched_npa):
        for value in crunched_npa['Length']:
            if int(value) > self.bins.size:
                self.bins.resize(int(value)+1)
            self.bins[int(value)] += 1

    @property
    def attribute(self):
        return compute_n50_from_bins(self.bins)


# Subread Aggregator Classes
class SubreadCounterAggregator(_BaseTotalAggregator):
    DATA_TYPE = SUBREAD_TYPE

    def apply(self, npa):
        self.value += len(npa)


class SubreadNumberOfBasesAggregator(_BaseTotalAggregator):
    DATA_TYPE = SUBREAD_TYPE

    def apply(self, crunched_npa):
        self.value += crunched_npa["Length"].sum()

    @property
    def attribute(self):
        return int(np.round(self.value))


class MaxSubreadLengthAggregator(_BaseTotalAggregator):
    DATA_TYPE = SUBREAD_TYPE

    def apply(self, crunched_npa):
        value = crunched_npa['Length'].max()
        if value > self.value:
            self.value = value

    def __repr__(self):
        _d = dict(k=self.__class__.__name__,
                  t=self.value)
        return "<{k} max={t} >".format(**_d)

    def __add__(self, other):
        if isinstance(other, self.__class__):
            value = self.value + other.value
            return self.__class__(value=value)
        else:
            _d = dict(s=type(self), o=type(other))
            raise TypeError("Incompatible types. {s} {o}".format(**_d))


class NumberSubreadBasesAggregator(_BaseTotalAggregator):
    DATA_TYPE = SUBREAD_TYPE

    def apply(self, crunched_npa):
        """
        This is computed differently in the old report code:

        nlen(subreads) * int(round(np.mean(subreads["Length"]))

        """
        self.value += crunched_npa['Length'].sum()

    @property
    def attribute(self):
        return int(np.round(self.value))


class MeanSubreadLengthAggregator(_MeanAggregator):
    DATA_TYPE = SUBREAD_TYPE

    def apply(self, npa):
        self.nvalues += npa['Length'].shape[0]
        self.total += npa['Length'].sum()

    @property
    def attribute(self):
        return int(np.round(self.mean))


class MeanSubreadAccuracyAggregator(_MeanAggregator):
    DATA_TYPE = SUBREAD_TYPE

    def apply(self, npa):
        self.nvalues += npa['Accuracy'].shape[0]
        self.total += npa['Accuracy'].sum()

    @property
    def attribute(self):
        # hack to make it look like the old report values
        # v = self.mean * 100
        v = self.mean
        return np.round(v, decimals=4)


class MeanSubreadQualityAggregator(_MeanAggregator):
    DATA_TYPE = SUBREAD_TYPE

    def apply(self, npa):
        self.nvalues += npa['Read quality'].shape[0]
        self.total += npa['Read quality'].sum()

    @property
    def attribute(self):
        # hack to make it look like the old report values
        # v = self.mean * 100
        v = self.mean
        return np.round(v, decimals=4)


class SubReadlengthHistogram(_BaseHistogram):
    DATA_TYPE = SUBREAD_TYPE

    def apply(self, crunched_npa):
        """This will be readlengths"""
        for value in crunched_npa['Length']:
            i = int(math.ceil(value / self.dx))
            # add
            if i > self.bins.size:
                self.bins.resize(i+1)
            self.bins[i] += 1


class SubReadAccuracyHistogram(_BaseHistogram):
    DATA_TYPE = SUBREAD_TYPE

    def __init__(self, dx=0.01, nbins=101):
        super(SubReadAccuracyHistogram, self).__init__(dx=dx, nbins=nbins)

    def apply(self, crunched_npa):
        """This will be readlengths"""
        for value in crunched_npa['Accuracy']:
            i = int(math.ceil(value / self.dx))
            if i < 0:
                log.warn(
                    "Assuming GMAP mode. Negative accuracy found {n}".format(n=i))
                continue
            # add
            try:
                if i > self.bins.size:
                    self.bins.resize(i+1)
                self.bins[i] += 1
            except IndexError as e:
                log.error(e)
                x = self.dx * self.nbins
                _d = dict(v=value, i=i, d=self.dx, x=x, n=self.nbins)
                log.error(
                    "Max value {v} dx:{d} nbins{n} value {x}".format(**_d))
                raise


class MappedReadLengthQ95(ReadLengthHistogram, AttributeAble):

    """
    mapped_readlength_q95

    This aggregator is a histogram and a regular attribute-style

    """

    @property
    def attribute(self):
        percentile = 95
        value = get_percentile(self.bins, self.bin_edges, percentile)
        return value

    def __repr__(self):
        x = self.dx * self.nbins
        _d = dict(k=self.__class__.__name__,
                  d=self.dx,
                  n=self.nbins,
                  x=x,
                  i=0,
                  a=self.attribute)
        return "<{k} q95:{a} dx:{d} nbins:{n} min:{i} max:{x} >".format(**_d)


class MappedSubreadLengthQ95(SubReadlengthHistogram, AttributeAble):

    @property
    def attribute(self):
        percentile = 95
        value = get_percentile(self.bins, self.bin_edges, percentile)
        return value


class StatisticsModel(object):

    def __init__(self, aggregators, filter_func=None):
        """Core container class used to apply subreads, reads

        the filter func operates on a region_file

        if the filter_func returns True, the aggregator.apply will be called

        """
        self.aggregators = aggregators
        self.filter_func = filter_func

    def __repr__(self):
        _d = dict(k=self.__class__.__name__,
                  n=len(self.aggregators))
        return "<{k} naggregators:{n} >".format(**_d)


# various utility functions
def _is_sam_or_bam_file(file_name):
    exts = {".sam", ".bam"}
    return any(file_name.endswith(ext) for ext in exts)


def _movienames_from_bam(aligned_file):
    movies = []
    if _is_sam_or_bam_file(aligned_file):
        movies = movies + list(openAlignmentFile(aligned_file).movieNames)
    return movies


def analyze_movie(movie, alignment_file, stats_models):
    """
    The regions should only correspond to a single Movie


    :type movie: Movie
    :type stats_models: list
    """

    started_at = time.time()
    log.info("Analyzing Movie {n}".format(n=movie))

    movie_names, unrolled, data_, columns = from_alignment_file(
        movie, alignment_file)

    if len(data_) == 0:
        msg = "Movie '{n}' produced no alignments.".format(n=movie)
        log.warn(msg)
        return

    crunched = CrunchedAlignments(movie_names, unrolled, data_, columns)

    log.debug("Movie names from crunched {m}.".format(m=movie_names))

    reads = crunched.reads()

    # subreads recarray
    # ["Length", "Accuracy", "isFirst", "modStart", "isFullSubread", "isMaxSubread"]
    subreads = crunched.subreads()

    log.info("Movie")
    log.info(movie)
    log.info(('Number of reads', len(reads)))
    log.info(('Number of subreads', len(subreads)))

    for model in stats_models:
        if model.filter_func(movie):
            for aggregator in model.aggregators:
                if aggregator.DATA_TYPE == READ_TYPE:
                    aggregator.apply(reads)
                if aggregator.DATA_TYPE == SUBREAD_TYPE:
                    aggregator.apply(subreads)
        else:
            log.warn(
                "model {m}. Skipping movie {r}".format(m=repr(model), r=movie))
            pass

    run_time = time.time() - started_at
    _d = dict(n=movie, s=run_time)
    log.info("Completed analyzing Movie {n} with in {s:.2f} sec.".format(**_d))


def analyze_movies(movies, alignment_file_names, stats_models):
    for movie in movies:
        for alignment_file_name in alignment_file_names:
            analyze_movie(movie, alignment_file_name, stats_models)

    log.info("Completed analyzing {n} movies.".format(n=len(movies)))


def get_attributes(aggregators_d, display_names_d):

    attributes = []

    for id_, aggregator in aggregators_d.iteritems():
        if isinstance(aggregator, AttributeAble):
            if id_ in display_names_d:
                display_name = display_names_d[id_]
            else:
                display_name = aggregator.__class__.__name__

            a = Attribute(id_, aggregator.attribute, name=display_name)
            attributes.append(a)
        else:
            # log.warn("Skipping attribute {i} for
            # {c}.".format(c=aggregator.__class__.__name__, i=id_))
            pass

    return attributes


class MappingStatsCollector(object):
    """
    Wrapper class for generating the report.  This allows us to re-use the
    logic but override the content in the CCS version (mapping_stats_ccs.py).
    """
    COLUMN_ATTR = [
        Constants.A_NREADS, Constants.A_READLENGTH, Constants.A_READLENGTH_N50,
        Constants.A_NSUBREADS, Constants.A_SUBREAD_NBASES,
        Constants.A_SUBREAD_LENGTH, Constants.A_SUBREAD_ACCURACY
    ]
    ATTR_LABELS = OrderedDict([
          (Constants.A_SUBREAD_ACCURACY, "Mean Mapped Concordance"),
          (Constants.A_NSUBREADS, "Mapped Subreads"),
          (Constants.A_SUBREAD_LENGTH, "Mapped Subread Length Mean"),
          (Constants.A_SUBREAD_LENGTH_N50, "Mapped Subread N50"),
          (Constants.A_SUBREAD_LENGTH_Q95, "Mapped Subread Length 95%"),
          (Constants.A_SUBREAD_LENGTH_MAX, "Mapped Subread Length Max"),
          (Constants.A_SUBREAD_NBASES, "Mapped Subread Bases"),
          (Constants.A_NREADS , "Mapped Polymerase Reads"),
          (Constants.A_READLENGTH, "Mapped Polymerase Read Length Mean"),
          (Constants.A_READLENGTH_N50, "Mapped Polymerase Read N50"),
          (Constants.A_READLENGTH_Q95, "Mapped Polymerase Read Length 95%"),
          (Constants.A_READLENGTH_MAX, "Mapped Polymerase Read Length Max"),
    ])
    ATTR_DESCRIPTIONS = {
          Constants.A_SUBREAD_ACCURACY: "The mean concordance of subreads that mapped to the reference sequence",
          Constants.A_NREADS : "The number of polymerase reads mapped to the reference sequence",
          Constants.A_NSUBREADS: "The number of subreads mapped to the reference sequence",
          Constants.A_SUBREAD_NBASES: "The number of subread bases mapped to the reference sequence",
          Constants.A_READLENGTH: "The approximate mean length of polymerase reads that mapped to the reference sequence (including adapters and other unmapped regions)",
          Constants.A_SUBREAD_LENGTH: "The mean length of subreads that mapped to the reference sequence",
          Constants.A_READLENGTH_Q95: "The 95th percentile of read length of polymerase reads that mapped to the reference sequence",
          Constants.A_SUBREAD_LENGTH_Q95: "The 95th percentile of length of subreads that mapped to the reference sequence",
          Constants.A_READLENGTH_MAX: "The maximum length of polymerase reads that mapped to the reference sequence",
          Constants.A_SUBREAD_LENGTH_MAX: "The maximum length of subreads that mapped to the reference sequence",
          Constants.A_SUBREAD_LENGTH_N50: "50% of bases that mapped to the reference sequence are in subreads longer than this value",
          Constants.A_READLENGTH_MAX: "The maximum length of polymerase reads that mapped to the reference sequence",
          Constants.A_READLENGTH_N50: "50% of bases that mapped to the reference sequence are in polymerase reads longer than this value",
    }
    HISTOGRAM_IDS = {
        Constants.P_SUBREAD_ACCURACY: "subread_accuracy_histogram",
        Constants.PG_SUBREAD_LENGTH: "subreadlength_histogram",
        Constants.P_READLENGTH: "readlength_histogram",
    }
    COLUMNS = [
        (Constants.C_MOVIE, "Movie"),
        (Constants.C_READS, "Mapped Reads"),
        (Constants.C_READLENGTH, "Mapped Polymerase Read Length"),
        (Constants.C_READLENGTH_N50, "Mapped Polymerase Read Length n50"),
        (Constants.C_SUBREADS, "Mapped Subreads"),
        (Constants.C_SUBREAD_NBASES, "Mapped Subread Bases"),
        (Constants.C_SUBREAD_LENGTH, "Mapped Subread Length"),
        (Constants.C_SUBREAD_ACCURACY, "Mapped Subread Accuracy")
    ]
    COLUMN_AGGREGATOR_CLASSES = [
        ReadCounterAggregator,
        MeanReadLengthAggregator,
        N50Aggreggator,
        SubreadCounterAggregator,
        NumberSubreadBasesAggregator,
        MeanSubreadLengthAggregator,
        MeanSubreadAccuracyAggregator
    ]

    def __init__(self, alignment_file):
        self.alignment_file = alignment_file
        self.dataset_uuids = []
        if alignment_file.endswith('.xml'):
            log.debug('Importing alignments from dataset XML')
            alignment_set = openDataSet(alignment_file)
            if not isinstance(alignment_set,
                              (AlignmentSet, ConsensusAlignmentSet)):
                raise TypeError("Dataset type %s not allowed here" %
                    type(alignment_set).__name__)
            self.alignment_file_list = alignment_set.toExternalFiles()
            self.dataset_uuids.append(alignment_set.uuid)
            movies = []
            for x in self.alignment_file_list:
                if not os.path.exists(x):
                    raise IOError("Unable to find DataSet external resource {x}".format(x=x))
                movies.extend(_movienames_from_bam(x))
            self.movies = sorted(list(set(movies)))
        elif _is_sam_or_bam_file(alignment_file):
            self.alignment_file_list = [alignment_file]
            self.movies = _movienames_from_bam(alignment_file)
        else:
            raise ValueError("Unsupported alignment file type '${x}'".format(
                x=alignment_file))

    def _get_plot_view_configs(self):
        """
        Any change to the 'raw' view of a report plot should be changed here.
    
        There's three histogram plots.
    
        1. Subread accuracy
        2. Subread rendlength
        3. Readlength
    
        """
        _p = [
            PlotViewProperties(
                Constants.P_SUBREAD_ACCURACY,
                Constants.PG_SUBREAD_ACCURACY,
                generate_plot,
                'mapped_subread_accuracy_histogram.png',
                xlabel="Concordance",
                ylabel="Subreads",
                color=get_green(3),
                edgecolor=get_green(2),
                use_group_thumb=True,
                plot_group_title="Mapped Subread Accuracy"),
            PlotViewProperties(
                Constants.P_SUBREAD_LENGTH,
                Constants.PG_SUBREAD_LENGTH,
                generate_plot,
                'mapped_subreadlength_histogram.png',
                xlabel="Subread Length",
                ylabel="Subreads",
                use_group_thumb=True,
                color=get_blue(3),
                edgecolor=get_blue(2),
                plot_group_title="Mapped Subread Length"),
            PlotViewProperties(
                Constants.P_READLENGTH,
                Constants.PG_READLENGTH,
                generate_plot,
                'mapped_readlength_histogram.png',
                xlabel="Read Length",
                ylabel="Reads",
                color=get_blue(3),
                edgecolor=get_blue(2),
                use_group_thumb=True,
                plot_group_title="Mapped Polymerase Read Length"),
        ]
        return {v.plot_id: v for v in _p}

    def _get_total_aggregators(self):
        return OrderedDict([ 
            (Constants.A_SUBREAD_ACCURACY, MeanSubreadAccuracyAggregator()),
            (Constants.A_NSUBREADS, SubreadCounterAggregator()),
            (Constants.A_SUBREAD_LENGTH, MeanSubreadLengthAggregator()),
            (Constants.A_SUBREAD_LENGTH_N50, SubreadN50Aggregator()),
            (Constants.A_SUBREAD_LENGTH_Q95, MappedSubreadLengthQ95(dx=10,
                                                                  nbins=10000)),
            (Constants.A_SUBREAD_LENGTH_MAX, MaxSubreadLengthAggregator()),
            (Constants.A_SUBREAD_NBASES, SubreadNumberOfBasesAggregator()),
            (Constants.A_NREADS, ReadCounterAggregator()),
            (Constants.A_READLENGTH, MeanReadLengthAggregator()),
            (Constants.A_READLENGTH_N50, N50Aggreggator()),
            # the bin size is important here. The computed percentile is
            # computed from the integral.
            (Constants.A_READLENGTH_Q95, MappedReadLengthQ95(dx=10, nbins=10000)),
            (Constants.A_READLENGTH_MAX, MaxReadLengthAggregator()),
            #'mapped_subread_read_quality_mean', MeanSubreadQualityAggregator()),
            ("readlength_histogram", ReadLengthHistogram(dx=500)),
            ("subreadlength_histogram", SubReadlengthHistogram()),
            ("subread_accuracy_histogram", SubReadAccuracyHistogram(dx=0.005,
                nbins=1001))
        ])

    def _to_table(self, movie_datum):
        """
        Create a pbreports Table for each movie.

        :param movie_datum: List of

        [(
        movie_name,
        reads,
        mean readlength,
        polymerase readlength
        number of subread bases
        mean subread readlength
        mean subread accuracy), ...]
        """
        columns = [Column(k, header=h) for k,h in self.COLUMNS]
        table = Table(Constants.T_STATS,
                      title="Mapping Statistics Summary",
                      columns=columns)

        for movie_data in movie_datum:
            if len(movie_data) != len(columns):
                log.error(movie_datum)
                raise ValueError(
                    "Incompatible values. {n} values provided, expected {a}".format(n=len(movie_data), a=len(columns)))

            for value, c in zip(movie_data, columns):
                table.add_data_by_column_id(c.id, value)

        log.debug(str(table))
        print table
        return table

    def to_report(self, output_dir):
        """
        This needs to be cleaned up. Keeping the old interface for testing purposes.
        """
        started_at = time.time()
    
        log.info("Found {n} movies.".format(n=len(self.movies)))
    
        log.info("Working from {n} alignment file{s}: {f}".format(
            n=len(self.alignment_file_list),
            s='s' if len(self.alignment_file_list) > 1 else '',
            f=self.alignment_file_list))
    
        # make this a dict {attribute_key_name:Aggreggator} so it's easy to
        # access the instances after they've been computed.
        # there's duplicated keys in the attributes?
        # number_of_aligned_reads/mapped_reads_n
        _total_aggregators = self._get_total_aggregators()
        null_filter = lambda r: True
        total_model = StatisticsModel(
            _total_aggregators.values(), filter_func=null_filter)
    
        # need to create specific instances for a given movie. This is used to
        # create the mapping reports stats table
        movie_models = {}
    
        def _my_filter(movie_name1, movie_name2):
            return movie_name1 == movie_name2
    
        for movie in self.movies:
            ags = [k() for k in self.COLUMN_AGGREGATOR_CLASSES]
            # Note this WILL NOT work because of how scope works in python
            # filter_by_movie_func = lambda m_name: movie.name == m_name
            _my_filter_func = functools.partial(_my_filter, movie)
            model = StatisticsModel(ags, filter_func=_my_filter_func)
            movie_models[movie] = model
    
        # The statistic models that will be run
        all_models = [total_model] + movie_models.values()
        log.debug(all_models)
    
        # Run all the analysis. Now the aggregators can be accessed
    
        analyze_movies(self.movies, self.alignment_file_list, all_models)
    
        # temp structure used to create the report table. The order is important
    
        # add total values
        _to_a = lambda k: _total_aggregators[k].attribute
        _row = [_to_a(n) for n in self.COLUMN_ATTR]
        _row.insert(0, 'All Movies')
        movie_datum = [_row]
    
        # Add each individual movie stats
        for movie_name_, model_ in movie_models.iteritems():
            _row = [movie_name_]
            for a in model_.aggregators:
                _row.append(a.attribute)
            movie_datum.append(_row)
        log.info(movie_datum)
    
        # create the Report table
    
        table = self._to_table(movie_datum)
    
        for movie_name, model in movie_models.iteritems():
            log.info("Movie name {n}".format(n=movie_name))
            for a in model.aggregators:
                log.info(movie_name + " " + repr(a))
    
        log.info("")
        log.info("Total models")
        for a in total_model.aggregators:
            log.info(a)
    
        attributes = get_attributes(_total_aggregators, self.ATTR_LABELS)
    
        log.info("Attributes from streaming mapping Report.")
        for a in attributes:
            log.info(a)
    
        plot_config_views = self._get_plot_view_configs()
    
        # keeping the ids independent requires a bit of dictionary madness
        # {report_id:HistogramAggregator}
        id_to_aggregators = {k:_total_aggregators[v]
                             for k,v in self.HISTOGRAM_IDS.iteritems()}
    
        plot_groups = to_plot_groups(plot_config_views, output_dir,
                                     id_to_aggregators)
        rb_pg = PlotGroup(Constants.PG_RAINBOW,
            title="Mapped Accuracy vs. Read Length")
        rb_png = "mapped_accuracy_vs_read_length.png"
        make_rainbow_plot(self.alignment_file, rb_png)
        rb_plt = Plot(Constants.P_RAINBOW, rb_png,
            caption="Mapped Accuracy vs. Read Length")
        rb_pg.add_plot(rb_plt)
        plot_groups.append(rb_pg)
    
        tables = [table]
        report = Report(Constants.R_ID,
                        attributes=attributes,
                        plotgroups=plot_groups,
                        tables=tables,
                        dataset_uuids=self.dataset_uuids)
    
        log.debug(report)
    
        run_time = time.time() - started_at
        log.info("Completed running in {s:.2f} sec.".format(s=run_time))
        return report


def to_report(alignment_file, output_dir):
    return MappingStatsCollector(alignment_file).to_report(output_dir)


def summarize_report(report_file, out=sys.stdout):
    """
    Utility function to harvest statistics from an existing report
    """
    from pbcommand.pb_io.report import load_report_from_json
    W = lambda s: out.write(s + "\n")
    report = load_report_from_json(report_file)
    attr = {a.id: a.value for a in report.attributes}
    W("%s:" % report_file)
    W("  MEAN ACCURACY: {f}".format(f=attr[Constants.A_SUBREAD_ACCURACY]))
    W("  NSUBREADS: {n}".format(n=attr[Constants.A_NSUBREADS]))
    W("  NREADS: {n}".format(n=attr[Constants.A_NREADS]))
    W("  NBASES: {n}".format(n=attr[Constants.A_SUBREAD_NBASES]))
    W("  READLENGTH_MEAN: {n}".format(n=attr[Constants.A_READLENGTH]))
    W("  SUBREADLENGTH_MEAN: {n}".format(n=attr[Constants.A_SUBREAD_LENGTH]))


def run_and_write_report(alignment_file, json_report, report_func=to_report):
    output_dir = os.path.dirname(json_report)
    report = report_func(alignment_file, output_dir)
    report.write_json(json_report)
    log.info("Wrote output to %s" % json_report)
    return 0


def _args_runner(args):
    return run_and_write_report(args.alignment_file, args.report_json)


def _resolved_tool_contract_runner(resolved_contract):
    """
    Run the mapping report from a resolved tool contract.

    :param resolved_contract:
    :type resolved_contract: ResolvedToolContract
    :return: Exit code
    """

    alignment_path = resolved_contract.task.input_files[0]

    # This is a bit different than the output dir oddness that Johann added.
    # the reports dir should be determined from the dir of the abspath of the report.json file
    # resolved values will always be absolute paths.
    output_report = resolved_contract.task.output_files[0]

    return run_and_write_report(alignment_path, output_report)


def _get_parser():
    desc = "Create a Mapping Report from a Aligned BAM or Alignment DataSet"
    driver_exe = "python -m pbreports.report.mapping_stats --resolved-tool-contract "
    parser = get_pbparser(TOOL_ID, __version__, "Mapping Statistics", desc, driver_exe)

    parser.add_input_file_type(FileTypes.DS_ALIGN, "alignment_file", "Alignment XML DataSet", "BAM, SAM or Alignment DataSet")
    parser.add_output_file_type(FileTypes.REPORT, "report_json", "PacBio Json Report", "Output report JSON file.", "mapping_stats_report.json")

    return parser


def main(argv=sys.argv, get_parser_func=_get_parser,
         args_runner_func=_args_runner,
         rtc_runner_func=_resolved_tool_contract_runner):
    mp = get_parser_func()
    return pbparser_runner(argv[1:],
                           mp,
                           args_runner_func,
                           rtc_runner_func,
                           log,
                           setup_log)


if __name__ == '__main__':
    sys.exit(main())
