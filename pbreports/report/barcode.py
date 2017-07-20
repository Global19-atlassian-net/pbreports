
"""
Generate a report on SubreadSet barcoding.
"""

from __future__ import division
from collections import defaultdict
from pprint import pformat
import itertools
import logging
import sys

from matplotlib import pyplot as plt

from pbcommand.cli import pbparser_runner
from pbcommand.models.report import Report, Table, Column, Attribute, Plot, PlotGroup
from pbcommand.models import FileTypes, get_pbparser
from pbcommand.utils import setup_log
from pbcore.io import openDataSet, BarcodeSet

from pbreports.io.specs import *

log = logging.getLogger(__name__)
__version__ = '1.0'

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
    LABEL_NONE = "Not Barcoded"

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
    ax.set_ylim(-(int(ymax*0.05)), ymax+int(ymax*(0.05)))
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Barcode Rank Order By Read Count")
    for spine in ["left", "right", "top", "bottom"]:
        ax.spines[spine].set_visible(False)
    fig.colorbar(im, ax=ax, fraction=0.05, pad=0.01)
    fig.tight_layout()
    return fig


def make_readlength_hist2d(bc_groups):
    """
    Create 2D histogram of read lengths per barcoded sample.
    """
    log.info("Creating 2D histogram of read lengths")
    x = []
    y = []
    for i, group in enumerate(bc_groups, start=1):
        x.extend([i] * group.n_reads)
        y.extend(group.readlengths)
    x_bins = max(len(bc_groups), 1)
    fig = make_2d_histogram(x, y,
                            n_bins=[x_bins, Constants.RL_BINS],
                            ylabel="Read Length")
    img_name = "hist2d_readlength.png"
    thumb_name = "hist2d_readlength_thumb.png"
    fig.savefig(img_name, dpi=72)
    fig.savefig(thumb_name, dpi=20)
    return Plot(Constants.P_HIST2D_RL, img_name, thumbnail=thumb_name)


def make_bcqual_hist2d(bc_groups):
    """
    Create 2D histogram of barcode quality scores per barcoded sample.
    """
    log.info("Creating 2D histogram of barcode quality scores")
    x = []
    y = []
    for i, group in enumerate(bc_groups, start=1):
        x.extend([i] * group.n_subreads)
        y.extend(group.bcquals)
    x_bins = max(1, len(bc_groups))
    fig = make_2d_histogram(x, y,
                            n_bins=[x_bins, Constants.BQ_BINS],
                            ylabel="Read Barcode Quality Score")
    img_name = "hist2d_bcqual.png"
    thumb_name = "hist2d_bcqual_thumb.png"
    fig.savefig(img_name, dpi=72)
    fig.savefig(thumb_name, dpi=20)
    return Plot(Constants.P_HIST2D_BQ, img_name, thumbnail=thumb_name)


class BarcodeBin(object):
    """
    Utility class for storing per-barcode metrics plotted as 2D histograms
    """
    __slots__ = ["bc_label", "readlengths", "bcquals"]

    def __init__(self, bc_label, readlengths, bcquals):
        self.bc_label = bc_label
        self.readlengths = readlengths
        self.bcquals = bcquals

    @property
    def n_subreads(self):
        return len(self.bcquals)

    @property
    def n_reads(self):
        return len(self.readlengths)


def make_histograms_2d(bc_info):
    log.info("Generating 2D histograms...")
    groups = []
    for bc_label, reads in bc_info.iteritems():
        if bc_label == Constants.LABEL_NONE:
            continue
        groups.append(BarcodeBin(
            bc_label=bc_label,
            readlengths=[r.readlength for r in reads],
            bcquals=list(itertools.chain(*(r.bq for r in reads)))))
    groups.sort(lambda a, b: cmp(b.n_reads, a.n_reads))
    x = []
    y = []
    plot_rl = make_readlength_hist2d(groups)
    plot_bq = make_bcqual_hist2d(groups)
    return PlotGroup(Constants.PG_HIST2D, plots=[plot_rl, plot_bq])


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


def make_report(read_info, dataset_uuids=()):
    """
    Create a Report object starting from an iterable of ReadInfo objects.
    """

    class MyRow(object):
        __slots__ = ["label", "bases", "reads", "subreads"]

        def __init__(self, label):
            self.label = label
            self.bases = 0
            self.reads = 0
            self.subreads = 0

    label2row = {}
    bc_info = defaultdict(list)

    for bc_read in read_info:
        bc_info[bc_read.label].append(bc_read)
        if not bc_read.label in label2row:
            label2row[bc_read.label] = MyRow(bc_read.label)
        label2row[bc_read.label].bases += bc_read.nbases
        label2row[bc_read.label].reads += 1
        label2row[bc_read.label].subreads += bc_read.n_subreads

    columns = [Column(Constants.C_BARCODE),
               Column(Constants.C_NREADS),
               Column(Constants.C_NSUBREADS),
               Column(Constants.C_NBASES)]

    table = Table('barcode_table', columns=columns)
    labels = sorted(label2row.keys())
    labels_bc = list(labels)  # this will only contain actual barcodes
    if Constants.LABEL_NONE in labels:
        labels.remove(Constants.LABEL_NONE)
        labels_bc = list(labels)
        labels.append(Constants.LABEL_NONE)
    n_barcodes = len(labels_bc)
    for label in labels:
        row = label2row[label]
        table.add_data_by_column_id(Constants.C_BARCODE, label)
        table.add_data_by_column_id(Constants.C_NREADS, row.reads)
        table.add_data_by_column_id(Constants.C_NSUBREADS, row.subreads)
        table.add_data_by_column_id(Constants.C_NBASES, row.bases)

    attributes = [
        Attribute(Constants.A_NBARCODES, value=n_barcodes)
    ]
    if n_barcodes > 0:
        n_reads_all = [label2row[k].reads for k in labels_bc]
        n_reads_sum = sum(n_reads_all)
        #rl_sum = sum([label2row[k].bases for k in labels_bc])
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

    plotgroups = [
        make_histograms_2d(bc_info)
    ]

    report = Report(spec.id,
                    attributes=attributes,
                    tables=[table],
                    dataset_uuids=dataset_uuids,
                    plotgroups=plotgroups)
    return spec.apply_view(report)


def run_to_report(reads, barcodes, dataset_uuids=()):
    """
    Generate a Report instance from a SubreadSet and BarcodeSet.
    """
    return make_report(
        read_info=iter_reads_by_barcode(reads, barcodes),
        dataset_uuids=dataset_uuids)


def args_runner(args):
    log.info("Starting {f} version {v} report generation".format(
        f=__file__, v=__version__))
    report = run_to_report(args.subreads, args.barcodes)
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
        dataset_uuids=dataset_uuids)
    log.debug(pformat(report.to_dict()))
    report.write_json(rtc.task.output_files[0])
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
