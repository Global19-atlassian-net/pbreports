#!/usr/bin/env python

import os.path as op
import sys

from tabulate import tabulate

from pbreports.report import mapping_stats, mapping_stats_ccs

TARGET = op.join(op.dirname(__file__), "report_specifications.rst")
HEADERS = ["Attribute ID", "Name", "Description"]

def run(args=()):
    with open(TARGET, "w") as f:
        f.write("""\
==================================================
pbreports specifications (automatically generated)
==================================================

Mapping Statistics
------------------
""")
        for klass in [mapping_stats.MappingStatsCollector,
                      mapping_stats_ccs.CCSMappingStatsCollector]:
            f.write("\n**pbreports.report.{m}**:\n\n".format(
                m=klass.__module__))
            table = []
            for attr in klass.COLUMN_ATTR:
                table.append((attr, klass.ATTR_LABELS[attr],
                              klass.ATTR_DESCRIPTIONS[attr]))
            f.write(tabulate(table, HEADERS, tablefmt="rst"))
    return 0

if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
