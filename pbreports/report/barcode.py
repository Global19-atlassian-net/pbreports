
"""
Generate a report on SubreadSet barcoding.
"""

from __future__ import division
from collections import defaultdict
from pprint import pformat
import itertools
import warnings
import logging
import os.path as op
import sys

from matplotlib import pyplot as plt

from pbcommand.cli import pbparser_runner
from pbcommand.models.report import Report, Table, Column, Attribute, Plot, PlotGroup
from pbcommand.models import FileTypes, get_pbparser
from pbcommand.utils import setup_log
from pbcore.io import openDataSet, BarcodeSet

from pbreports.plot.helper import make_histogram, get_blue, get_fig_axes_lpr
from pbreports.io.specs import *

log = logging.getLogger(__name__)
__version__ = '1.2'

spec = load_spec("barcode")


class Constants(object):
    TOOL_ID = "pbreports.tasks.barcode_report"
    TOOL_NAME = "barcode_report"
    DRIVER_EXE = "python -m pbreports.report.barcode --resolved-tool-contract"

    A_NBARCODES = "n_barcodes"
    A_MEAN_READS = "mean_reads"
    A_MAX_READS = "max_reads"
    A_MIN_READS = "min_reads"
    A_MEAN_RL = "mean_read_length"
    A_MEAN_MAX_SRL = "mean_longest_subread_length"

    C_BARCODE = 'barcode'
    C_NREADS = 'number_of_reads'
    C_NSUBREADS = 'number_of_subreads'
    C_NBASES = 'number_of_bases'
    C_READLENGTH = "mean_read_length"
    C_SRL = "longest_subread_length"
    C_BCQUAL = "mean_bcqual"
    C_RANK = "rank_order"
    LABEL_NONE = "Not Barcoded"

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


# XXX This might eventually need to be moved to pbreports.plot, but it's very
# specialized right now
def make_2d_histogram(x, y, n_bins, ylabel):
    """
    Generate a rainbow-colored 2D histogram where the X axis represents
    individual barcode groups (sorted by descending read count) and the Y axis
    represents a metric within each group (bq, read length, etc.).

    :param x: X-axis values, i.e. barcode group indices
    :param y: Y-axis values corresponding to x
    :param n_bins: (x,y) bin sizes; x should usually be 1
    :param ylabl: Y-axis label
    :returns: matplotlib figure
    """
    cmap = plt.cm.Spectral_r
    cmap.set_under(color=(0.875, 0.875, 0.875))
    fig = plt.figure(figsize=(12, 4))
    ax = fig.add_subplot(111)
    ax.axesPatch.set_facecolor((0.875, 0.875, 0.875))
    ax.grid(color="white", linewidth=0.5, linestyle='-')
    counts, xedges, yedges, im = ax.hist2d(x, y, cmap=cmap, vmin=1,
                                           bins=n_bins)
    x_margin = 5
    if n_bins[0] < 20:
        x_margin = 1
    elif n_bins[0] < 50:
        x_margin = 2
    ymax = max(y) if len(y) > 0 else 1
    ax.set_xlim(-x_margin, n_bins[0] + x_margin)
    ax.set_ylim(-(int(ymax * 0.05)), ymax + int(ymax * (0.05)))
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Barcode Rank Order By Read Count")
    for spine in ["left", "right", "top", "bottom"]:
        ax.spines[spine].set_visible(False)
    fig.colorbar(im, ax=ax, fraction=0.05, pad=0.01)
    fig.tight_layout()
    return fig


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
    fig = make_2d_histogram(x, y,
                            n_bins=[x_bins, Constants.RL_BINS],
                            ylabel="Read Length")
    img_name = "hist2d_readlength.png"
    thumb_name = "hist2d_readlength_thumb.png"
    fig.savefig(op.join(base_dir, img_name), dpi=72)
    fig.savefig(op.join(base_dir, thumb_name), dpi=20)
    plt.close()
    return Plot(Constants.P_HIST2D_RL, img_name, thumbnail=thumb_name)


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
    fig = make_2d_histogram(x, y,
                            n_bins=[x_bins, Constants.BQ_BINS],
                            ylabel="Read Barcode Quality Score")
    img_name = "hist2d_bcqual.png"
    thumb_name = "hist2d_bcqual_thumb.png"
    fig.savefig(op.join(base_dir, img_name), dpi=72)
    fig.savefig(op.join(base_dir, thumb_name), dpi=20)
    plt.close()
    return Plot(Constants.P_HIST2D_BQ, img_name, thumbnail=thumb_name)


def make_nreads_line_plot(bc_groups, base_dir):
    x = [i for (i,g) in enumerate(bc_groups, start=1)]
    y = [g.n_reads for g in bc_groups]
    mean_nreads = 0 if len(y) == 0 else sum(y) / len(y)
    fig, ax = get_fig_axes_lpr()
    ax.plot(x, y, color='blue')
    ax.axhline(mean_nreads, color='red', label="Mean Number of Reads")
    ax.set_xlabel("Barcode Rank Order")
    ax.set_ylabel("Count of Reads")
    plt.legend()
    img_name = "nreads.png"
    thumb_name = "nreads_thumb.png"
    fig.savefig(op.join(base_dir, img_name), dpi=72)
    fig.savefig(op.join(base_dir, thumb_name), dpi=20)
    plt.close()
    return Plot(Constants.P_NREADS, img_name, thumbnail=thumb_name)


def make_nreads_histogram(bc_groups, base_dir):
    """
    Create simple histogram of read count frequency per barcode.
    """
    fig, ax = make_histogram(
        datum=[float(g.n_reads) for g in bc_groups],  # FIXME workaround
        axis_labels=["Number of Reads", "Number of Barcoded Samples"],
        nbins=min(len(bc_groups), 20),
        barcolor=get_blue(3))
    img_name = "nreads_histogram.png"
    thumb_name = "nreads_histogram_thumb.png"
    fig.savefig(op.join(base_dir, img_name), dpi=72)
    fig.savefig(op.join(base_dir, thumb_name), dpi=20)
    plt.close()
    return Plot(Constants.P_HIST_NREADS, img_name, thumbnail=thumb_name)


def make_readlength_histogram(bc_groups, base_dir):
    """
    Create simple histogram of read length frequency per barcode.
    """
    fig, ax = make_histogram(
        datum=[float(g.mean_read_length()) for g in bc_groups],  # FIXME
        axis_labels=["Mean Read Length", "Number of Barcoded Samples"],
        nbins=min(len(bc_groups), 20),
        barcolor=get_blue(3))
    img_name = "readlength_histogram.png"
    thumb_name = "readlength_histogram_thumb.png"
    fig.savefig(op.join(base_dir, img_name), dpi=72)
    fig.savefig(op.join(base_dir, thumb_name), dpi=20)
    plt.close()
    return Plot(Constants.P_HIST_RL, img_name, thumbnail=thumb_name)


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
    img_name = "bcqual_histogram.png"
    thumb_name = "bcqual_histogram_thumb.png"
    fig.savefig(op.join(base_dir, img_name), dpi=72)
    fig.savefig(op.join(base_dir, thumb_name), dpi=20)
    plt.close()
    return Plot(Constants.P_HIST_BQ, img_name, thumbnail=thumb_name)


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
        img_name = "bcqual_qq.png"
        thumb_name = "bcqual_qq_thumb.png"
        fig.savefig(op.join(base_dir, img_name), dpi=72)
        fig.savefig(op.join(base_dir, thumb_name), dpi=20)
        plt.close()
        return Plot(Constants.P_BQ_QQ, img_name, thumbnail=thumb_name)


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
    plot_qq = None
    try:  # FIXME workaround until DEP-414 is fixed
        plot_qq = make_bq_qq_plot(groups, base_dir)
    except Exception as e:
        log.error(str(e))
        warnings.warn("Q-Q plot broken: {e}".format(e=str(e)))
    bq_plots = [plot_bq]
    if plot_qq is not None:
        bq_plots.append(plot_qq)
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
    __slots__ = ["label", "n_bases", "readlengths", "bqs", "srl_max"]

    def __init__(self,
                 label,
                 n_bases=0,
                 readlengths=(),
                 bqs=(),
                 srl_max=0):
        self.label = label
        self.n_bases = n_bases
        self.readlengths = list(readlengths)
        self.bqs = list(bqs)
        self.srl_max = srl_max

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

    def is_barcoded(self):
        return self.bc_idx != (-1, -1)

    @property
    def n_subreads(self):
        return len(self.bq)


def iter_reads_by_barcode(reads, barcodes):
    """
    Open a SubreadSet and BarcodeSet and return an iterable of ReadInfo objects
    """
    log.info("Extracting barcoded read info from input datasets...")
    with openDataSet(reads) as ds:
        for er in ds.externalResources:
            if er.barcodes is not None and er.barcodes != barcodes:
                raise ValueError("Mismatch between external resource " +
                                 "barcodes and input BarcodeSet: " +
                                 "{a} != {b}".format(a=er.barcodes,
                                                     b=barcodes))
        assert ds.isIndexed
        zmws_by_barcode = defaultdict(set)
        subreads_by_zmw = defaultdict(list)
        for rr in ds.resourceReaders():
            for i, (f, r, z, q) in enumerate(zip(rr.pbi.bcForward,
                                                 rr.pbi.bcReverse,
                                                 rr.pbi.holeNumber,
                                                 rr.pbi.qId)):
                movie = rr.readGroupInfo(q).MovieName
                zmws_by_barcode[(f, r)].add((movie, z))
                subreads_by_zmw[(movie, z)].append((rr, i))
        with BarcodeSet(barcodes) as ds_bc:
            bc_ids = sorted(zmws_by_barcode.keys())
            bcs = [bc for bc in ds_bc]
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
                    for rr, i_subread in subreads_by_zmw[(movie, zmw)]:
                        srl = rr.pbi.qEnd[i_subread] - rr.pbi.qStart[i_subread]
                        qlen += srl
                        qmax = max(qmax, rr.pbi.qEnd[i_subread])
                        srl_max = max(srl_max, srl)
                        bq.append(rr.pbi.bcQual[i_subread])
                    bc_idx = (barcode_fw, barcode_rev)
                    yield ReadInfo(barcode_id, qlen, qmax, srl_max, bq, bc_idx)


def make_report(read_info, dataset_uuids=(), base_dir=None):
    """
    Create a Report object starting from an iterable of ReadInfo objects.
    """
    if base_dir == None:
        base_dir = os.getcwd()

    bc_groups = {}
    bc_info = defaultdict(list)

    for bc_read in read_info:
        bc_info[bc_read.label].append(bc_read)
        if not bc_read.label in bc_groups:
            bc_groups[bc_read.label] = BarcodeGroup(bc_read.label)
        bc_groups[bc_read.label].add_read(bc_read)

    columns = [Column(Constants.C_BARCODE),
               Column(Constants.C_NREADS),
               Column(Constants.C_NSUBREADS),
               Column(Constants.C_NBASES),
               Column(Constants.C_READLENGTH),
               Column(Constants.C_SRL),
               Column(Constants.C_BCQUAL),
               Column(Constants.C_RANK)]

    table = Table('barcode_table', columns=columns)
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
    for label in labels:
        row = bc_groups[label]
        table.add_data_by_column_id(Constants.C_BARCODE, label)
        table.add_data_by_column_id(Constants.C_NREADS, row.n_reads)
        table.add_data_by_column_id(Constants.C_NSUBREADS, row.n_subreads)
        table.add_data_by_column_id(Constants.C_NBASES, row.n_bases)
        table.add_data_by_column_id(
            Constants.C_READLENGTH, row.mean_read_length())
        table.add_data_by_column_id(Constants.C_SRL, row.srl_max)
        table.add_data_by_column_id(Constants.C_BCQUAL, row.mean_bcqual())
        table.add_data_by_column_id(Constants.C_RANK, rank.get(label, None))

    attributes = [
        Attribute(Constants.A_NBARCODES, value=n_barcodes)
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
            Attribute(Constants.A_MEAN_MAX_SRL,
                      value=int(srl_max_sum / n_barcodes))
        ])
    else:
        ids = [Constants.A_MEAN_READS, Constants.A_MAX_READS,
               Constants.A_MIN_READS, Constants.A_MEAN_RL,
               Constants.A_MEAN_MAX_SRL]
        attributes.extend([Attribute(ID, value=0) for ID in ids])

    plotgroups = make_plots(bc_groups.values(), base_dir)

    report = Report(spec.id,
                    attributes=attributes,
                    tables=[table],
                    dataset_uuids=dataset_uuids,
                    plotgroups=plotgroups)
    return spec.apply_view(report)


def run_to_report(reads, barcodes, dataset_uuids=(), base_dir=None):
    """
    Generate a Report instance from a SubreadSet and BarcodeSet.
    """
    return make_report(
        read_info=iter_reads_by_barcode(reads, barcodes),
        dataset_uuids=dataset_uuids,
        base_dir=base_dir)


def args_runner(args):
    log.info("Starting {f} version {v} report generation".format(
        f=__file__, v=__version__))
    report = run_to_report(args.subreads, args.barcodes,
                           base_dir=op.dirname(args.report_json))
    log.info(pformat(report.to_dict()))
    report.write_json(args.report_json)
    return 0


def resolved_tool_contract_runner(rtc):
    log.info("Starting {f} version {v} report generation".format(
        f=__file__, v=__version__))
    dataset_uuids = [
        openDataSet(rtc.task.input_files[0]).uuid,
        BarcodeSet(rtc.task.input_files[1]).uuid
    ]
    report = run_to_report(
        reads=rtc.task.input_files[0],
        barcodes=rtc.task.input_files[1],
        dataset_uuids=dataset_uuids,
        base_dir=op.dirname(rtc.task.output_files[0]))
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
    p.add_input_file_type(FileTypes.DS_SUBREADS, "subreads",
                          name="BarcodedSubreadSet",
                          description="Barcoded Subread DataSet XML")
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
