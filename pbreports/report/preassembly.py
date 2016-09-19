#!/usr/bin/env python2.7
"""Generate a preassembly report based on inputs.

Called by functions in:

    pbfalcon.report_preassembly

Those consume the result of:

    python -m falcon_kit.mains.report_pre_assembly

For HGAP4, there is a pbcommands wrapper.
For HGAP5, the Report generator is part of another pbsmrtpipe Task.
"""

import logging
import os
import sys

from pbcommand.models.report import (Report, Attribute)
#from pbcommand.common_options import add_debug_option
#from pbcommand.models import FileTypes, get_pbparser
#from pbcommand.cli import pbparser_runner
#from pbcommand.utils import setup_log

log = logging.getLogger(__name__)

__all__ = []

class Constants(object):
    #TOOL_ID = "pbreports.tasks.polished_assembly"
    R_ID = "preassembly"

#spec = load_spec(Constants.R_ID)


def produce_report(
        genome_length,
        raw_reads,
        raw_mean,
        raw_n50,
        raw_p95,
        raw_bases,
        raw_coverage,
        length_cutoff,
        seed_reads,
        seed_bases,
        seed_mean,
        seed_n50,
        seed_p95,
        seed_coverage,
        preassembled_reads,
        preassembled_mean,
        preassembled_n50,
        preassembled_p95,
        preassembled_bases,
        preassembled_coverage,
        preassembled_yield,
        preassembled_seed_fragmentation,
        preassembled_seed_truncation,
        **ignored
    ):
    """Return a preassembly report as JSON string.
    Parameters are as defined in the spec-file.
    Extra parameters are ignored, so that the caller may be
    augmented in a separate commit prior to updates here.
    (That facilitates cross-team collaboration.)
    """
    log.info("Starting {f!r}".format(
        f=os.path.basename(__file__)))

    # Report Attributes
    attrs = []
    attrs.append(Attribute('genome_length', genome_length, name="Genome Length (user input)"))
    attrs.append(Attribute('raw_reads', raw_reads, name="Number of Raw Reads"))
    attrs.append(Attribute('raw_mean', raw_mean, name="Raw Read Length Mean"))
    attrs.append(Attribute('raw_n50', raw_n50, name="Raw Read Length (N50)"))
    attrs.append(Attribute('raw_p95', raw_p95, name="Raw Read Length 95%"))
    attrs.append(Attribute('raw_bases', raw_bases, name="Number of Raw Bases (total)"))
    attrs.append(Attribute('raw_coverage', raw_coverage, name="Raw Coverage (bases/genome_size)"))
    attrs.append(Attribute('length_cutoff', length_cutoff, name="Length Cutoff (user input or auto-calc)"))
    attrs.append(Attribute('seed_reads', seed_reads, name="Number of Seed Reads"))
    attrs.append(Attribute('seed_mean', seed_mean, name="Seed Read Length Mean"))
    attrs.append(Attribute('seed_n50', seed_n50, name="Seed Read Length (N50)"))
    attrs.append(Attribute('seed_p95', seed_p95, name="Seed Read Length 95%"))
    attrs.append(Attribute('seed_bases', seed_bases, name="Number of Seed Bases (total)"))
    attrs.append(Attribute('seed_coverage', seed_coverage, name="Seed Coverage (bases/genome_size)"))
    attrs.append(Attribute('preassembled_reads', preassembled_reads, name="Number of Pre-Assembled Reads"))
    attrs.append(Attribute('preassembled_mean', preassembled_mean, name="Pre-Assembled Read Length Mean"))
    attrs.append(Attribute('preassembled_n50', preassembled_n50, name="Pre-Assembled Read Length (N50)"))
    attrs.append(Attribute('preassembled_p95', preassembled_p95, name="Pre-Assembled Read Length 95%"))
    attrs.append(Attribute('preassembled_bases', preassembled_bases, name="Number of Pre-Assembled Bases (total)"))
    attrs.append(Attribute('preassembled_coverage', preassembled_coverage, name="Pre-Assembled Coverage (bases/genome_size)"))
    attrs.append(Attribute('preassembled_yield', preassembled_yield, name="Pre-Assembled Yield (bases/seed_bases)"))
    attrs.append(Attribute('preassembled_seed_fragmentation', preassembled_seed_fragmentation, name="Avg number of reads that each seed is broken into."))
    attrs.append(Attribute('preassembled_seed_truncation', preassembled_seed_truncation, name="Avg number of bases lost from each seed."))

    report = Report(Constants.R_ID, title='Preassembly', attributes=attrs)

    from pbreports.io.specs import load_spec
    spec = load_spec(Constants.R_ID)
    report = spec.apply_view(report)

    return report.to_json()
