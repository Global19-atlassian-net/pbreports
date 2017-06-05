
"""
Generate a report on SubreadSet barcoding.
"""

from collections import defaultdict
from pprint import pformat
import logging
import sys

from pbcommand.cli import pbparser_runner
from pbcommand.models.report import Report, Table, Column
from pbcommand.models import FileTypes, get_pbparser
from pbcommand.utils import setup_log
from pbcore.io import openDataSet, BarcodeSet

from pbreports.io.specs import *

log = logging.getLogger(__name__)
__version__ = '0.7'

spec = load_spec("barcode")


class Constants(object):
    TOOL_ID = "pbreports.tasks.barcode_report"
    TOOL_NAME = "barcode_report"
    DRIVER_EXE = "python -m pbreports.report.barcode --resolved-tool-contract"
    C_BARCODE = 'barcode'
    C_NREADS = 'number_of_reads'
    C_NSUBREADS = 'number_of_subreads'
    C_NBASES = 'number_of_bases'
    LABEL_NONE = "Not barcoded"


def iter_reads_by_barcode(reads, barcodes):
    with openDataSet(reads) as ds:
        for er in ds.externalResources:
            if er.barcodes is not None and er.barcodes != barcodes:
                raise ValueError("Mismatch between external resource " +
                                 "barcodes and input BarcodeSet: " +
                                 "{a} != {b}".format(a=er.barcodes,
                                                     b=barcodes))
        assert ds.isIndexed
        zmws_by_barcode = defaultdict(set)
        reads_by_zmw = defaultdict(list)
        for rr in ds.resourceReaders():
            for i, (f, r, z, q) in enumerate(zip(rr.pbi.bcForward,
                                                 rr.pbi.bcReverse,
                                                 rr.pbi.holeNumber,
                                                 rr.pbi.qId)):
                movie = rr.readGroupInfo(q).MovieName
                zmws_by_barcode[(f,r)].add((movie, z))
                reads_by_zmw[(movie, z)].append((rr, i))
        with BarcodeSet(barcodes) as ds_bc:
            bc_ids = sorted(zmws_by_barcode.keys())
            bcs = [bc for bc in ds_bc]
            for i_bc, (barcode_fw, barcode_rev) in enumerate(bc_ids):
                if barcode_fw == -1:
                    barcode_id = Constants.LABEL_NONE
                else:
                    barcode_id = "{f}--{r}".format(f=bcs[barcode_fw].id,
                                                   r=bcs[barcode_rev].id)
                zmws = sorted(list(zmws_by_barcode[(barcode_fw,barcode_rev)]))
                for (movie, zmw) in zmws:
                    qlen = n_subreads = 0
                    for rr, i_read in reads_by_zmw[(movie, zmw)]:
                        qlen += rr.pbi.qEnd[i_read] - rr.pbi.qStart[i_read]
                        n_subreads += 1
                    yield barcode_id, (barcode_fw, barcode_rev), qlen, n_subreads


def run_to_report(reads, barcodes, subreads=True, dataset_uuids=()):
    """ Generate a Report instance from a SubreadSet and BarcodeSet.
    :param subreads: If the ccs fofn is given this needs to be set to False
    """

    class MyRow(object):

        def __init__(self, label):
            self.label = label
            self.bases = 0
            self.reads = 0
            self.subreads = 0

    label2row = {}

    for label, bcs, nbases, nsubreads in iter_reads_by_barcode(reads, barcodes):
        if not label in label2row:
            label2row[label] = MyRow(label)
        label2row[label].bases += nbases
        label2row[label].reads += 1
        label2row[label].subreads += nsubreads

    columns = [Column(Constants.C_BARCODE),
               Column(Constants.C_NREADS),
               Column(Constants.C_NBASES)]
    if subreads:
        columns.insert(2, Column(Constants.C_NSUBREADS))

    table = Table('barcode_table', columns=columns)
    labels = sorted(label2row.keys())
    if Constants.LABEL_NONE in labels:
        labels.remove(Constants.LABEL_NONE)
        labels.append(Constants.LABEL_NONE)
    for label in labels:
        row = label2row[label]
        table.add_data_by_column_id(Constants.C_BARCODE, label)
        table.add_data_by_column_id(Constants.C_NREADS, row.reads)
        if subreads:
            table.add_data_by_column_id(Constants.C_NSUBREADS, row.subreads)
        table.add_data_by_column_id(Constants.C_NBASES, row.bases)

    report = Report(spec.id, tables=[table],
                    dataset_uuids=dataset_uuids)
    return spec.apply_view(report)


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
    dataset_uuids = [
        openDataSet(rtc.task.input_files[0]).uuid,
        BarcodeSet(rtc.task.input_files[1]).uuid
    ]
    report = run_to_report(
        reads=rtc.task.input_files[0],
        barcodes=rtc.task.input_files[1],
        subreads=True,
        dataset_uuids=dataset_uuids)
    log.info(pformat(report.to_dict()))
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
    # TODO(nechols)(2016-03-15) not yet supported in SA 3.x
    # this is necessary for BasH5Reader to handle the differences between the
    # .ccs.h5 files and .bas.h5 files.
    ap = p.arg_parser.parser
    ap.add_argument('--ccs', action='store_true',
                    help='Use consensus reads instead of subreads.')
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
