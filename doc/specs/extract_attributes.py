import logging
import os
import os.path as op
import sys
from tabulate import tabulate

from pbreports.report.report_spec import (MetaAttribute, MetaPlotGroup, MetaPlot,
                                          MetaColumn, MetaTable, MetaReport)

log = logging.getLogger(__name__)

TARGET = op.join(op.dirname(__file__), "attributes.rst")
_DIR_NAME = os.path.dirname(os.path.abspath(__file__))
SPEC_DIR = os.path.join(_DIR_NAME, '../../pbreports/report/specs/')

blacklist = ["control", "filter_subread", "overview"]

def run(args=()):
    with open(TARGET, "w") as f:
        f.write("""\
==================================================
pbreports specifications (automatically generated)
==================================================

""")

        for spec in os.listdir(SPEC_DIR):
            specfile = op.join(SPEC_DIR, spec)
            meta_rpt = MetaReport.from_json(specfile)
            if meta_rpt.id in blacklist:
            	continue
            if meta_rpt.attributes:
                f.write("\n\n\n")
                f.write(
                    "**{t}** ({d}):\n\n".format(t=meta_rpt.title, d=meta_rpt.id))
                f.write("{n}\n\n".format(n=meta_rpt.description))
                table = []
                for attr in meta_rpt.attributes:
                    row = [attr.id, attr.name, attr.description]
                    table.append(row)
                HEADERS = ["Attribute ID", "Name", "Description"]
                f.write(tabulate(table, HEADERS, tablefmt="rst"))

    return 0

if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
