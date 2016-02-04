#!/usr/bin/env python

# XXX it would be better if we were generating code from a spec instead of
# vice-versa, but this allows us to see what is currently reported

"""
Script to automatically generate tables of attribute names and descriptions
in RST format from a collection of report modules.
"""

import logging
import os.path as op
import sys

from tabulate import tabulate

from pbreports.report import (mapping_stats, mapping_stats_ccs, ccs, sat,
    variants)

try:
    from pbtranscript.io import Summary
except ImportError:
    Summary = None

log = logging.getLogger(__name__)

TARGET = op.join(op.dirname(__file__), "report_specifications.rst")
HEADERS = ["Attribute ID", "Name", "Description"]

def run(args=()):
    with open(TARGET, "w") as f:
        f.write("""\
==================================================
pbreports specifications (automatically generated)
==================================================

""")
        def _write_report_info(k, m, n, doc=None):
            if doc is None:
                doc = m.__doc__
            f.write("\n\n\n")
            f.write("**{n}**:\n\n".format(n=n))
            f.write("{d}\n\n".format(d=doc))
            table = []
            for attr, label in k.ATTR_LABELS.iteritems():
                table.append((attr, k.ATTR_LABELS[attr],
                              k.ATTR_DESCRIPTIONS[attr]))
            f.write(tabulate(table, HEADERS, tablefmt="rst"))

        for m,c in [(mapping_stats, "MappingStatsCollector"),
                    (mapping_stats_ccs, "CCSMappingStatsCollector"),
                    (variants, "Constants"),
                    (sat, "Constants"),
                    (ccs, "Constants")]:
            klass = getattr(m, c)
            _write_report_info(klass, m, m.__name__)
        if Summary is not None:
            for m,c,n in [(Summary, "ClassifySummary", "isoseq_classify"),
                          (Summary, "ClusterSummary", "isoseq_cluster")]:
                klass = getattr(m, c)
                _write_report_info(klass, m, "pbreports.report.{n}".format(n=n),
                    doc="IsoSeq {r} report".format(r=c[:-7]))
        else:
            log.warn("Skipping IsoSeq reports")
    return 0

if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
