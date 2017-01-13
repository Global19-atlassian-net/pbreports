#!/usr/bin/env python

import subprocess
import importlib
import argparse
import os
import sys

"""
Regenerate tool contracts for all applicable pbreports modules, written to
the specified dir_name
"""

MODULES = [
    "adapter_xml",
    "amplicon_analysis_consensus",
    "amplicon_analysis_input",
    "barcode",
    "ccs",
    "coverage",
    "coverage_hgap",
    "filter_stats_xml",
    "isoseq_classify",
    "isoseq_cluster",
    "loading_xml",
    "mapping_stats_ccs",
    "mapping_stats_hgap",
    "mapping_stats",
    "modifications",
    "motifs",
    "polished_assembly",
    "sat",
    "summarize_coverage.ccs",
    "summarize_coverage.summarize_coverage",
    "top_variants",
    "variants"
]


def run(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dir_name")
    args = p.parse_args(argv)
    for module_name in MODULES:
        module_path = "pbreports.report.{m}".format(m=module_name)
        m = importlib.import_module(module_path)
        c = getattr(m, "Constants", None)
        if c is None:
            raise AttributeError("Can't find 'Constants' in {m}".format(
                                 m=module_path))
        tc_json = "{t}_tool_contract.json".format(t=c.TOOL_ID)
        tc_file = os.path.join(args.dir_name, tc_json)
        cmd = "python -m {m} --emit-tool-contract > {f}".format(
            m=module_path, f=tc_file)
        print cmd
        assert subprocess.call(cmd, shell=True) == 0

if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
