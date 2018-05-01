
"""
Generate a report on SubreadSet barcoding.
"""

from __future__ import division
from collections import defaultdict
from pprint import pformat
import functools
import itertools
import warnings
import logging
import os.path as op
import sys

from pbcommand.cli import pbparser_runner
from pbcommand.models.report import Report, Table, Column, Attribute, Plot, PlotGroup
from pbcommand.models import DataStore, FileTypes, get_pbparser
from pbcommand.utils import setup_log
from pbcore.io import openDataSet, BarcodeSet, SubreadSet

from pbreports.plot.helper import make_histogram, make_2d_histogram, get_blue, get_fig_axes_lpr, save_figure_with_thumbnail, DEFAULT_DPI, DEFAULT_THUMB_DPI
from pbreports.io.specs import *

log = logging.getLogger(__name__)
__version__ = '3.1'

spec = load_spec("barcode")


class Constants(object):
    TOOL_ID = "pbreports.tasks.barcode_report"
    TOOL_NAME = "barcode_report"
    DRIVER_EXE = "python -m pbreports.report.barcode --resolved-tool-contract"

    ISOSEQ_MODE = "pbreports.task_options.isoseq_mode"

    A_NBARCODES = "n_barcodes"
    A_MEAN_READS = "mean_reads"
    A_MAX_READS = "max_reads"
    A_MIN_READS = "min_reads"
    A_MEAN_RL = "mean_read_length"
    A_MEAN_MAX_SRL = "mean_longest_subread_length"
    A_NREADS_BARCODED = "n_barcoded_reads"
    A_NREADS_UNBARCODED = "n_unbarcoded_reads"

    C_BIOSAMPLE = "biosample"
    C_IDX = "barcode_index"
    C_BARCODE = 'barcode'
    C_NREADS = 'number_of_reads'
    C_NSUBREADS = 'number_of_subreads'
    C_NBASES = 'number_of_bases'
    C_READLENGTH = "mean_read_length"
    C_SRL = "longest_subread_length"
    C_BCQUAL = "mean_bcqual"
    C_RANK = "rank_order"
    LABEL_NONE = "Not Barcoded"
    BIOSAMPLE_NONE = "No Name"

    PG_STATS = "read_stats"
    P_NREADS = "nreads"
    P_HIST_NREADS = "nreads_histogram"
    P_HIST_RL = "readlength_histogram"

    PG_BQ = "bq_plots"
    P_HIST_BQ = "bq_histogram"
    P_BQ_QQ = "bq_qq"

    PG_HIST2D = "hist2d"
    P_HIST2D_RL = "binned_readlength"
    P_HIST2D_BQ = "binned_bcqual"
    BQ_BINS = 50
    RL_BINS = 50

    SHOW_COLUMNS = [
        C_BIOSAMPLE,
        C_IDX,
        C_BARCODE,
        C_NREADS,
        C_NSUBREADS,
        C_NBASES,
        C_READLENGTH,
        C_SRL,
        C_BCQUAL,
        C_RANK
    ]

    SHOW_ATTRIBUTES = [
        A_NBARCODES,
        A_NREADS_BARCODED,
        A_NREADS_UNBARCODED,
        A_MEAN_READS,
        A_MAX_READS,
        A_MIN_READS,
        A_MEAN_RL,
        A_MEAN_MAX_SRL
    ]

    VALID_FT_IDS = {
        FileTypes.DS_SUBREADS.file_type_id,
        FileTypes.DS_CCS.file_type_id
    }


class CCSConstants(Constants):
    SHOW_COLUMNS = [
        Constants.C_BIOSAMPLE,
        Constants.C_IDX,
        Constants.C_BARCODE,
        Constants.C_NREADS,
        Constants.C_NBASES,
        # FIXME not clear if this is relevant here.  we can report mean CCS
        # read length of course but that's not the same as the polymerase read
        # length; to get that we'd have to refer back to the input SubreadSet.
        Constants.C_READLENGTH,
        Constants.C_BCQUAL,
        Constants.C_RANK
    ]

    SHOW_ATTRIBUTES = [
        Constants.A_NBARCODES,
        Constants.A_NREADS_BARCODED,
        Constants.A_NREADS_UNBARCODED,
        Constants.A_MEAN_READS,
        Constants.A_MAX_READS,
        Constants.A_MIN_READS,
        Constants.A_MEAN_RL,
    ]


def _to_plot(fig, plot_id, base_dir):
    img_name = plot_id + ".png"
    _, thumb_name = save_figure_with_thumbnail(
        fig, op.join(base_dir, img_name))
    return Plot(plot_id, img_name, thumbnail=op.basename(thumb_name))


def make_readlength_hist2d(bc_groups, base_dir):
    """
    Create 2D histogram of read lengths per barcoded sample.
    """
    log.info("Creating 2D histogram of read lengths")
    x, y = [], []
    for i, group in enumerate(bc_groups, start=1):
        x.extend([i] * group.n_reads)
        y.extend(group.readlengths)
    x_bins = max(len(bc_groups), 1)
    fig, ax = make_2d_histogram(x, y,
                                n_bins=[x_bins, Constants.RL_BINS],
                                xlabel="Barcode Rank Order By Read Count",
                                ylabel="Read Length",
                                cbar_label="Read Count")
    return _to_plot(fig, Constants.P_HIST2D_RL, base_dir)


def make_bcqual_hist2d(bc_groups, base_dir):
    """
    Create 2D histogram of barcode quality scores per barcoded sample.
    """
    log.info("Creating 2D histogram of barcode quality scores")
    x, y = [], []
    for i, group in enumerate(bc_groups, start=1):
        x.extend([i] * group.n_subreads)
        y.extend(group.bqs)
    x_bins = max(1, len(bc_groups))
    fig, ax = make_2d_histogram(x, y,
                                n_bins=[x_bins, Constants.BQ_BINS],
                                xlabel="Barcode Rank Order By Read Count",
                                ylabel="Read Barcode Quality Score",
                                cbar_label="Read Count")
    ax.axhline(26, color='black', linestyle='--')
    return _to_plot(fig, Constants.P_HIST2D_BQ, base_dir)


def make_nreads_line_plot(bc_groups, base_dir):
    x = [i for (i, g) in enumerate(bc_groups, start=1)]
    y = [g.n_reads for g in bc_groups]
    mean_nreads = 0 if len(y) == 0 else sum(y) / len(y)
    fig, ax = get_fig_axes_lpr()
    ax.plot(x, y, color='blue')
    line = ax.axhline(mean_nreads, color='red', label="Mean Number of Reads")
    ax.set_xlabel("Barcode Rank Order")
    ax.set_ylabel("Count of Reads")
    fig.legend((line,), ("Mean Number of Reads",), ("upper right"))
    return _to_plot(fig, Constants.P_NREADS, base_dir)


def make_nreads_histogram(bc_groups, base_dir):
    """
    Create simple histogram of read count frequency per barcode.
    """
    fig, ax = make_histogram(
        datum=[float(g.n_reads) for g in bc_groups],  # FIXME workaround
        axis_labels=["Number of Reads", "Number of Barcoded Samples"],
        nbins=min(len(bc_groups), 20),
        barcolor=get_blue(3))
    return _to_plot(fig, Constants.P_HIST_NREADS, base_dir)


def make_readlength_histogram(bc_groups, base_dir):
    """
    Create simple histogram of read length frequency per barcode.
    """
    fig, ax = make_histogram(
        datum=[float(g.mean_read_length()) for g in bc_groups],  # FIXME
        axis_labels=["Mean Read Length", "Number of Barcoded Samples"],
        nbins=min(len(bc_groups), 20),
        barcolor=get_blue(3))
    return _to_plot(fig, Constants.P_HIST_RL, base_dir)


def make_bcqual_histogram(bc_groups, base_dir):
    """
    Create simple histogram of barcode quality score frequency over all
    barcoded subreads.
    """
    data = []
    for g in bc_groups:
        data.extend(g.bqs)
    fig, ax = make_histogram(
        datum=data,
        axis_labels=["Barcode Quality Score", "Number of Barcoded Subreads"],
        nbins=50,
        barcolor=get_blue(3))
    ax.axvline(26, color='r')
    return _to_plot(fig, Constants.P_HIST_BQ, base_dir)


def make_bq_qq_plot(bc_groups, base_dir):
    """
    Create Q-Q plot for barcode quality scores.
    """
    try:
        import scipy.stats
    except ImportError:
        warnings.warn("Can't import scipy.stats")
        return None
    else:
        data = []
        for g in bc_groups:
            data.append(g.mean_bcqual())
        fig, ax = get_fig_axes_lpr()
        scipy.stats.probplot(data, dist="norm", plot=ax)
        ax.set_title("Q-Q Plot of Barcode Quality Scores")
        return _to_plot(fig, Constants.P_BQ_QQ, base_dir)


def make_plots(bc_groups, base_dir):
    """
    Generate all plots, both 1D and 2D, and return a list of PlotGroups.
    """
    groups = [g for g in bc_groups if g.label != Constants.LABEL_NONE]
    groups.sort(lambda a, b: cmp(b.n_reads, a.n_reads))
    plot_nreads = make_nreads_line_plot(groups, base_dir)
    log.info("Generating 1D histograms...")
    plot_nreads_hist = make_nreads_histogram(groups, base_dir)
    plot_rl = make_readlength_histogram(groups, base_dir)
    log.info("Generating barcode quality score plots...")
    plot_bq = make_bcqual_histogram(groups, base_dir)
    bq_plots = [plot_bq]
    log.info("Generating 2D histograms...")
    plot_rl2d = make_readlength_hist2d(groups, base_dir)
    plot_bq = make_bcqual_hist2d(groups, base_dir)
    return [
        PlotGroup(Constants.PG_STATS, plots=[
                  plot_nreads, plot_nreads_hist, plot_rl]),
        PlotGroup(Constants.PG_BQ, plots=bq_plots),
        PlotGroup(Constants.PG_HIST2D, plots=[plot_rl2d, plot_bq])
    ]


class BarcodeGroup(object):
    """
    Utility class for storing per-barcode metrics from multiple reads
    """
    __slots__ = ["label", "n_bases", "readlengths", "bqs", "srl_max", "idx"]

    def __init__(self,
                 label,
                 n_bases=0,
                 readlengths=(),
                 bqs=(),
                 srl_max=0,
                 idx=None):
        self.label = label
        self.n_bases = n_bases
        self.readlengths = list(readlengths)
        self.bqs = list(bqs)
        self.srl_max = srl_max
        self.idx = idx

    def add_read(self, read_info):
        assert read_info.label == self.label
        self.n_bases += read_info.nbases
        self.readlengths.append(read_info.readlength)
        self.bqs.extend(list(read_info.bq))
        self.srl_max = max(read_info.srl_max, self.srl_max)

    @property
    def n_subreads(self):
        return len(self.bqs)

    @property
    def n_reads(self):
        return len(self.readlengths)

    def mean_read_length(self):
        if self.n_reads == 0:
            return 0
        return int(sum(self.readlengths) / self.n_reads)

    def mean_bcqual(self):
        if self.n_subreads == 0:
            return 0
        return int(sum(self.bqs) / self.n_subreads)


class ReadInfo(object):
    """
    Container class for storing information about a single barcoded ZMW read
    and associated subreads.
    """
    __slots__ = ["label", "nbases", "readlength", "bq", "srl_max", "bc_idx"]

    def __init__(self, label, nbases, qmax, srl_max, bq, bc_idx):
        self.label = label
        self.nbases = nbases
        self.readlength = qmax
        self.bq = bq
        self.srl_max = srl_max
        self.bc_idx = bc_idx

    @property
    def idx(self):
        if self.is_barcoded():
            return "{f}--{r}".format(f=self.bc_idx[0], r=self.bc_idx[1])
        else:
            return "None"

    def is_barcoded(self):
        return self.bc_idx != (-1, -1)

    @property
    def n_subreads(self):
        return len(self.bq)


def _to_abs_path(dir_name, path):
    if os.path.isabs(path):
        return path
    else:
        return os.path.join(dir_name, path)


def _get_barcoded_datasets(reads_file):
    dir_name = os.path.dirname(os.path.abspath(reads_file))
    if reads_file.endswith(".datastore.json"):
        datastore = DataStore.load_from_json(reads_file)
        datasets = [_to_abs_path(dir_name, f.path)
                    for u, f in datastore.files.iteritems()
                    if f.file_type_id in Constants.VALID_FT_IDS]
        if len(datasets) == 0:
            raise ValueError("No datasets containing barcoded reads were " +
                             "present in the input.  This could mean that " +
                             "demultiplexing was run with incorrect inputs " +
                             "or an overly restrictive minimum barcode score.")
        return datasets
    else:
        return [reads_file]


def get_barcoded_dataset(reads_file):
    log.info("Opening all barcoded datasets")
    return openDataSet(*_get_barcoded_datasets(reads_file), strict=True)


def get_biosample_dict(barcoded_subreads):
    biosamples = {}
    sub_datasets = [barcoded_subreads]
    if len(barcoded_subreads.subdatasets) > 0:
        sub_datasets = barcoded_subreads.subdatasets
    for ss in sub_datasets:
        try:
            biosample = ss.metadata.collections[
                0].wellSample.bioSamples[0].name
        except IndexError:
            biosample = Constants.BIOSAMPLE_NONE
            log.warn("No biosample info found, using %s", biosample)
        except Exception as e:
            log.error(e)
            biosample = Constants.BIOSAMPLE_NONE
        try:
            barcode = ss.metadata.collections[
                0].wellSample.bioSamples[0].DNABarcodes[0].name
        except IndexError:
            pass
        except Exception as e:
            log.error(e)
        else:
            biosamples[barcode] = biosample
    return biosamples


def iter_reads_by_barcode(barcoded_dataset, barcodes, isoseq_mode=False):
    """
    Given a SubreadSet or ConsensusReadSet and BarcodeSet as input, return an
    iterable of ReadInfo objects
    """
    log.info("Extracting barcoded read info from input datasets...")
    ds = barcoded_dataset
    for er in ds.externalResources:
        if er.barcodes is not None and er.barcodes != barcodes.fileNames[0]:
            raise ValueError("Mismatch between external resource " +
                             "barcodes and input BarcodeSet: " +
                             "{a} != {b}".format(a=er.barcodes,
                                                 b=barcodes))
    assert ds.isIndexed
    zmws_by_barcode = defaultdict(set)
    records_by_zmw = defaultdict(list)
    for rr in ds.resourceReaders():
        for i, (f, r, z, q) in enumerate(zip(rr.pbi.bcForward,
                                             rr.pbi.bcReverse,
                                             rr.pbi.holeNumber,
                                             rr.pbi.qId)):
            bc_key = (f, r)
            if isoseq_mode:
                bc_key = tuple(sorted(bc_key))
            movie = rr.readGroupInfo(q).MovieName
            zmws_by_barcode[bc_key].add((movie, z))
            records_by_zmw[(movie, z)].append((rr, i))
    log.info("Combining with BarcodeSet labels...")
    bc_ids = sorted(zmws_by_barcode.keys())
    bcs = [bc for bc in barcodes]
    for i_bc, (barcode_fw, barcode_rev) in enumerate(bc_ids):
        if barcode_fw == -1:
            barcode_id = Constants.LABEL_NONE
        else:
            barcode_id = "{f}--{r}".format(f=bcs[barcode_fw].id,
                                           r=bcs[barcode_rev].id)
        zmws = sorted(list(zmws_by_barcode[(barcode_fw, barcode_rev)]))
        for (movie, zmw) in zmws:
            qlen = 0
            qmax = srl_max = 0
            bq = []
            for rr, i_rec in records_by_zmw[(movie, zmw)]:
                srl = rr.pbi.qEnd[i_rec] - rr.pbi.qStart[i_rec]
                qlen += srl
                qmax = max(qmax, rr.pbi.qEnd[i_rec])
                srl_max = max(srl_max, srl)  # meaningless for CCS
                bq.append(rr.pbi.bcQual[i_rec])
            bc_idx = (barcode_fw, barcode_rev)
            yield ReadInfo(barcode_id, qlen, qmax, srl_max, bq, bc_idx)


def get_unbarcoded_reads_info(dataset_in, dataset_bc):
    log.info("Identifying non-barcoded reads...")
    barcoded_zmws = set()
    for rr in dataset_bc.resourceReaders():
        for zmw, qId in zip(rr.pbi.holeNumber, rr.pbi.qId):
            movie = rr.readGroupInfo(qId).MovieName
            barcoded_zmws.add((movie, zmw))
    # not necessarily subreads
    nonbarcoded_records_by_zmw = defaultdict(list)
    for rr in dataset_in.resourceReaders():
        for i, (zmw, qId) in enumerate(zip(rr.pbi.holeNumber, rr.pbi.qId)):
            movie = rr.readGroupInfo(qId).MovieName
            if (movie, zmw) in barcoded_zmws:
                continue
            else:
                nonbarcoded_records_by_zmw[(movie, zmw)].append((rr, i))
    log.info("Collecting metrics for non-barcoded reads...")
    for (movie, zmw) in sorted(nonbarcoded_records_by_zmw.keys()):
        qlen = 0
        qmax = srl_max = 0
        for rr, i_rec in nonbarcoded_records_by_zmw[(movie, zmw)]:
            srl = rr.pbi.qEnd[i_rec] - rr.pbi.qStart[i_rec]
            qlen += srl
            qmax = max(qmax, rr.pbi.qEnd[i_rec])
            srl_max = max(srl_max, srl)
        bq = [0] * len(nonbarcoded_records_by_zmw[(movie, zmw)])
        yield ReadInfo(Constants.LABEL_NONE, qlen, qmax, srl_max, bq, (-1, -1))


def _make_report_impl(attribute_ids,
                      column_ids,
                      use_spec,
                      biosamples,
                      read_info,
                      dataset_uuids=(),
                      base_dir=None):
    """
    Create a Report object starting from an iterable of ReadInfo objects.
    """
    log.info("Creating report files...")
    if base_dir == None:
        base_dir = os.getcwd()

    bc_groups = {}
    bc_info = defaultdict(list)

    for bc_read in read_info:
        bc_info[bc_read.label].append(bc_read)
        if not bc_read.label in bc_groups:
            bc_groups[bc_read.label] = BarcodeGroup(
                bc_read.label, idx=bc_read.idx)
        bc_groups[bc_read.label].add_read(bc_read)

    table = Table('barcode_table',
                  columns=[Column(column_id) for column_id in column_ids])

    def add_column_if_present(column_id, value):
        if column_id in column_ids:
            table.add_data_by_column_id(column_id, value)

    labels = sorted(bc_groups.keys())
    labels_bc = list(labels)  # this will only contain actual barcodes
    if Constants.LABEL_NONE in labels:
        labels.remove(Constants.LABEL_NONE)
        labels_bc = list(labels)
        labels.append(Constants.LABEL_NONE)
    rank = {}
    k = 0
    groups = sorted(bc_groups.values(), lambda a, b: cmp(b.n_reads, a.n_reads))
    for bc_group in groups:
        if bc_group.label != Constants.LABEL_NONE:
            k += 1
            rank[bc_group.label] = k
    n_barcodes = len(labels_bc)
    n_barcoded_reads = n_unbarcoded_reads = 0
    for label in labels:
        row = bc_groups[label]
        add_column_if_present(Constants.C_BIOSAMPLE, biosamples.get(
            label, Constants.BIOSAMPLE_NONE))
        add_column_if_present(Constants.C_IDX, row.idx)
        add_column_if_present(Constants.C_BARCODE, label)
        add_column_if_present(Constants.C_NREADS, row.n_reads)
        add_column_if_present(Constants.C_NSUBREADS, row.n_subreads)
        add_column_if_present(Constants.C_NBASES, row.n_bases)
        add_column_if_present(
            Constants.C_READLENGTH, row.mean_read_length())
        add_column_if_present(Constants.C_SRL, row.srl_max)
        add_column_if_present(Constants.C_BCQUAL, row.mean_bcqual())
        add_column_if_present(Constants.C_RANK, rank.get(label, None))
        if label == Constants.LABEL_NONE:
            n_unbarcoded_reads += row.n_reads
        else:
            n_barcoded_reads += row.n_reads

    attributes = [
        Attribute(Constants.A_NBARCODES, value=n_barcodes),
        Attribute(Constants.A_NREADS_BARCODED, value=n_barcoded_reads),
        Attribute(Constants.A_NREADS_UNBARCODED, value=n_unbarcoded_reads)
    ]
    if n_barcodes > 0:
        n_reads_all = [bc_groups[k].n_reads for k in labels_bc]
        n_reads_sum = sum(n_reads_all)
        #rl_sum = sum([bc_groups[k].bases for k in labels_bc])
        srl_max_sum = rl_sum = 0
        for k in labels_bc:
            rl_sum += sum([b.readlength for b in bc_info[k]])
            srl_max_sum += max([b.srl_max for b in bc_info[k]])
        attributes.extend([
            Attribute(Constants.A_MEAN_READS, value=int(
                n_reads_sum / n_barcodes)),
            Attribute(Constants.A_MAX_READS, value=max(n_reads_all)),
            Attribute(Constants.A_MIN_READS, value=min(n_reads_all)),
            # XXX these need to be clarified
            Attribute(Constants.A_MEAN_RL, value=int(rl_sum / n_reads_sum)),
        ])
        if Constants.A_MEAN_MAX_SRL in attribute_ids:
            attributes.append(Attribute(Constants.A_MEAN_MAX_SRL,
                                        value=int(srl_max_sum / n_barcodes)))
    else:
        attributes.extend([Attribute(ID, value=0) for ID in attribute_ids[3:]])

    plotgroups = make_plots(bc_groups.values(), base_dir)

    report = Report(use_spec.id,
                    attributes=attributes,
                    tables=[table],
                    dataset_uuids=dataset_uuids,
                    plotgroups=plotgroups)
    return use_spec.apply_view(report)


make_report = functools.partial(
    _make_report_impl, Constants.SHOW_ATTRIBUTES, Constants.SHOW_COLUMNS)
make_report_ccs = functools.partial(
    _make_report_impl, CCSConstants.SHOW_ATTRIBUTES, CCSConstants.SHOW_COLUMNS)


def run_to_report(ds_bc_file, barcodes_file, subreads_in_file, base_dir=None,
                  isoseq_mode=False):
    """
    Generate a Report instance from a SubreadSet and BarcodeSet.
    """
    barcoded_reads = get_barcoded_dataset(ds_bc_file)
    subreads_in = SubreadSet(subreads_in_file, strict=True)
    barcodes = BarcodeSet(barcodes_file)
    ds_bc_uuids = [barcoded_reads.uuid]
    if len(barcoded_reads.subdatasets) > 0:
        ds_bc_uuids = [ds.uuid for ds in barcoded_reads.subdatasets]
    dataset_uuids = [
        barcodes.uuid,
        subreads_in.uuid
    ] + ds_bc_uuids
    biosamples = get_biosample_dict(barcoded_reads)
    read_info = list(iter_reads_by_barcode(barcoded_reads, barcodes, isoseq_mode)) + \
        list(get_unbarcoded_reads_info(subreads_in, barcoded_reads))
    if isinstance(barcoded_reads, SubreadSet):
        return make_report(use_spec=spec,
                           biosamples=biosamples,
                           read_info=read_info,
                           dataset_uuids=dataset_uuids,
                           base_dir=base_dir)
    else:
        use_spec = spec
        if isoseq_mode:
            use_spec = spec_isoseq3
        return make_report_ccs(use_spec=use_spec,
                               biosamples=biosamples,
                               read_info=read_info,
                               dataset_uuids=dataset_uuids,
                               base_dir=base_dir)


def args_runner(args):
    log.info("Starting {f} version {v} report generation".format(
        f=__file__, v=__version__))
    report = run_to_report(args.ds_bc, args.barcodes, args.subreads_in,
                           base_dir=op.dirname(args.report_json),
                           isoseq_mode=args.isoseq_mode)
    log.info(pformat(report.to_dict()))
    report.write_json(args.report_json)
    return 0


def resolved_tool_contract_runner(rtc):
    log.info("Starting {f} version {v} report generation".format(
        f=__file__, v=__version__))
    report = run_to_report(
        ds_bc_file=rtc.task.input_files[0],
        barcodes_file=rtc.task.input_files[2],
        subreads_in_file=rtc.task.input_files[1],
        base_dir=op.dirname(rtc.task.output_files[0]),
        isoseq_mode=rtc.task.options.get(Constants.ISOSEQ_MODE, False))
    log.debug(pformat(report.to_dict()))
    report.write_json(rtc.task.output_files[0])
    report.tables[0].to_csv(rtc.task.output_files[1])
    return 0


def get_parser():
    p = get_pbparser(
        tool_id=Constants.TOOL_ID,
        version=__version__,
        name=Constants.TOOL_NAME,
        description=__doc__,
        driver_exe=Constants.DRIVER_EXE)
    p.add_input_file_type(
        FileTypes.DATASTORE,
        "ds_bc",
        name="JSON Datastore or SubreadSet or ConsensusReadSet",
        description="Datastore of barcoded SubreadSet/ConsensusReadSet files")
    p.add_input_file_type(FileTypes.DS_SUBREADS, "subreads_in",
                          name="Input SubreadSet",
                          description="Input SubreadSet (without barcodes)")
    p.add_input_file_type(FileTypes.DS_BARCODE, "barcodes",
                          name="BarcodeSet",
                          description="Barcode DataSet XML")
    p.add_output_file_type(FileTypes.REPORT, "report_json",
                           name="Barcode Report",
                           description="Summary of barcoding results",
                           default_name="barcode_report")
    p.tool_contract_parser.add_output_file_type(
        FileTypes.CSV, "report_csv",
        name="Barcode Report Details",
        description="Barcode Details Table as CSV",
        default_name="barcodes_report")
    p.add_boolean(Constants.ISOSEQ_MODE, "isoseq_mode", False,
                  "Iso-Seq mode", "Iso-Seq mode")
    return p


def main(argv=sys.argv):
    return pbparser_runner(
        argv=argv[1:],
        parser=get_parser(),
        args_runner_func=args_runner,
        contract_runner_func=resolved_tool_contract_runner,
        alog=log,
        setup_log_func=setup_log)


if __name__ == '__main__':
    sys.exit(main())
