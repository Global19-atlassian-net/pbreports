#!/usr/bin/env python
""" PreAssembly Report.

Output of Original Report

<?xml version="1.0" encoding="UTF-8"?>
<report>
  <layout onecolumn="true"/>
  <title>Pre-Assembly</title>
  <attributes>
    <attribute id="1" name="Polymerase Read Bases" value="125856600" hidden="true">125856600</attribute>
    <attribute id="2" name="Length Cutoff" value="6000" hidden="true">6000</attribute>
    <attribute id="3" name="Seed Bases" value="18610" hidden="true">18610</attribute>
    <attribute id="4" name="Pre-Assembled Bases" value="3628" hidden="true">3628</attribute>
    <attribute id="5" name="Pre-Assembled Yield" value=".194" hidden="true">.194</attribute>
    <attribute id="6" name="Pre-Assembled Reads" value="3" hidden="true">3</attribute>
    <attribute id="7" name="Pre-Assembled Read Length" value="1209" hidden="true">1209</attribute>
    <attribute id="8" name="Pre-Assembled N50" value="1300" hidden="true">1300</attribute>
  </attributes>
</report>



"""
from __future__ import division
import sys
import os
import logging

from pbcommand.models.report import Report, Attribute
from pbcommand.models import FileTypes, get_pbparser
from pbcommand.cli import pbparser_runner
from pbcommand.utils import setup_log
from pbcommand.common_options import add_debug_option

from pbreports.util import get_fasta_readlengths, \
    compute_n50_from_file

log = logging.getLogger(__name__)

__version__ = '0.1'


class Constants(object):
    TOOL_ID = "pbreports.tasks.preassembly"
    LENGTH_CUTOFF_ID = "pbreports.task_options.length_cutoff"
    # This is just put in the report as an attribute... this is a stand-in for
    # what should be "None"
    LENGTH_CUTOFF = -1


class FastaContainer(object):

    def __init__(self, nreads, total, file_name):
        self.nreads = nreads
        self.total = total
        self.file_name = file_name

    @staticmethod
    def from_file(file_name):
        #        nreads, total = _compute_values(file_name)
        read_lens = get_fasta_readlengths(file_name)
        nreads = len(read_lens)
        total = sum(read_lens)
        return FastaContainer(nreads, total, file_name)

    def __str__(self):
        return "N {n} Total {t} File: {f}".format(n=self.nreads, t=self.total, f=self.file_name)


def _validate_file(file_name):
    if os.path.isfile(file_name):
        return os.path.abspath(file_name)
    else:
        msg = "Unable to find {f}".format(f=file_name)
        log.error(msg)
        raise IOError(msg)


def to_report(filtered_subreads, filtered_longreads, corrected_reads, length_cutoff=None):
    """
    All inputs are paths to fasta files.
    """
    subreads = FastaContainer.from_file(filtered_subreads)
    longreads = FastaContainer.from_file(filtered_longreads)
    creads = FastaContainer.from_file(corrected_reads)

    fastas = [subreads, longreads, creads]
    for f in fastas:
        log.info(f)

    yield_ = creads.total / longreads.total
    rlength = int(creads.total / creads.nreads)
#    n50 = _compute_n50(corrected_reads, creads.total)
    n50 = compute_n50_from_file(corrected_reads)

    # Report Attributes
    attrs = []
    attrs.append(Attribute('polymerase_read_bases',
                           value=subreads.total, name="Polymerase Read Bases"))
    if length_cutoff is not None:
        attrs.append(Attribute('length_cutoff',
                               length_cutoff, name="Length Cutoff"))
    attrs.append(Attribute('seed_bases', longreads.total, name="Seed Bases"))
    attrs.append(Attribute('preassembled_bases',
                           creads.total, name="Pre-Assembled bases"))
    attrs.append(Attribute('preassembled_yield',
                           yield_, name="Pre-Assembled Yield"))
    attrs.append(Attribute('presssembled_reads',
                           creads.nreads, name="Pre-Assembled Reads"))
    attrs.append(Attribute('presssembled_readlength',
                           rlength, name="Pre-Assembled Reads Length"))
    attrs.append(Attribute('preassembled_n50', n50, name="Pre-Assembled N50"))

    report = Report('preassembly', attributes=attrs)
    return report


def make_preassembly_report(filtered_subreads, filtered_longreads,
                            corrected_reads, length_cutoff, output_json):
    if length_cutoff == -1:
        length_cutoff = None
    report = to_report(filtered_subreads, filtered_longreads, corrected_reads,
                       length_cutoff=length_cutoff)
    with open(output_json, 'w') as fh:
        log.info("Writing report to {r}.".format(r=output_json))
        fh.write(report.to_json())
    return 0


def args_runner(args):
    filtered_subreads = args.filtered_subreads_fasta
    filtered_longreads = args.filtered_longreads_fasta
    corrected_reads = args.corrected_reads
    length_cutoff = args.length_cutoff
    output_json = args.output_json
    make_preassembly_report(filtered_subreads, filtered_longreads,
                            corrected_reads, length_cutoff, output_json)
    return 0


def resolved_tool_contract_runner(resolved_tool_contract):
    rtc = resolved_tool_contract
    make_preassembly_report(
        rtc.task.input_files[0],
        rtc.task.input_files[1],
        rtc.task.input_files[2],
        rtc.task.options[Constants.LENGTH_CUTOFF_ID],
        rtc.task.output_files[0])
    return 0


def _add_options_to_parser(p):
    p.add_input_file_type(
        FileTypes.FASTA,
        file_id="filtered_subreads_fasta",
        name="Filtered Subreads Fasta",
        description="Filtered Subreads Fasta")
    p.add_input_file_type(
        FileTypes.FASTA,
        file_id="filtered_longreads_fasta",
        name="Filtered Longreads Fasta",
        description="Filtered Longreads Fasta")
    p.add_input_file_type(
        FileTypes.FASTA,
        file_id="corrected_reads",
        name="Corrected Fasta",
        description="Corrected Fasta")
    p.add_int(
        option_id=Constants.LENGTH_CUTOFF_ID,
        option_str="length_cutoff",
        default=Constants.LENGTH_CUTOFF,
        name="Length cutoff",
        description="Length cutoff to insert into report")
    p.add_output_file_type(
        FileTypes.REPORT,
        file_id="output_json",
        name="Preassembly Report",
        description="Preassembly Report",
        default_name="preassembly_report.json")


def add_options_to_parser(p):
    """
    API function for extending main pbreport arg parser (independently of
    tool contract interface).
    """
    p_wrap = _get_parser_core()
    p_wrap.arg_parser.parser = p
    p.description = __doc__
    add_debug_option(p)
    _add_options_to_parser(p_wrap)
    p.set_defaults(func=args_runner)
    return p


def _get_parser_core():
    driver_exe = ("python -m "
                  "pbreports.report.preassembly "
                  "--resolved-tool-contract ")
    p = get_pbparser(
        Constants.TOOL_ID,
        __version__,
        "Preassembly",
        __doc__,
        driver_exe)
    return p


def get_parser():
    p = _get_parser_core()
    _add_options_to_parser(p)
    return p


def main(argv=sys.argv):
    mp = get_parser()
    return pbparser_runner(argv[1:],
                           mp,
                           args_runner,
                           resolved_tool_contract_runner,
                           log,
                           setup_log)

# for 'python -m pbreports.report.preassembly ...'
if __name__ == "__main__":
    sys.exit(main())
