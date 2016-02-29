
from pbreports.util import (validate_fofn, validate_file,
                            add_plot_options, add_base_options)

from pbreports.report.adapter import make_adapter_report
from pbreports.report.loading import make_loading_report
from pbreports.report.coverage import make_coverage_report
from pbreports.report.control import make_control_report
from pbreports.report.top_variants import make_topvariants_report
from pbreports.report.polished_assembly import make_polished_assembly_report
from pbreports.report.variants import make_variants_report
from pbreports.report.modifications import make_modifications_report
from pbreports.report.sat import make_sat_report
import os


VARIANTS = 'variants'
TOP_VARIANTS = 'topvariants'
MINOR_TOP_VARIANTS = 'minor-topvariants'
ADAPTER = 'adapter'
LOADING = 'loading'
COVERAGE = 'coverage'
CONTROL = 'control'
POLISHED_ASSEMBLY = 'polished-assembly'
MODIFICATIONS = 'modifications'
SAT = 'sat'

# All Available Parser will be registered here dynamically.
registered_subparser_classes = {}


class _RegisterParserMetaKlass(type):

    def __new__(cls, name, parent, dct):
        """Validate the config class

        The Subclass must define
        1. 'SUBCOMMAND' as class var.
        2. help property
        2. add_args(self, subparser) method

        """
        _EXCLUDE_BASE_CLASSES = (
            'SubParserHelper', 'PlotParserHelper', 'RegisterParser')
        _REQUIRED_CLASS_VARS = ('SUBCOMMAND', 'help', 'run_report')

        if name not in _EXCLUDE_BASE_CLASSES:
            # validation
            for var in _REQUIRED_CLASS_VARS:
                if var not in dct:
                    raise KeyError(
                        "Class {n} must define {v}.".format(n=name, v=var))

            subcommand = dct['SUBCOMMAND']
            # keep backward compatibility with the property. FIXME. Remove
            # This.
            dct['subcommand'] = subcommand
            if subcommand in registered_subparser_classes:
                raise KeyError("Duplicated subparser {n} with subcommand {s}.".format(
                    n=name, s=subcommand))
            else:
                klass = super(_RegisterParserMetaKlass, cls).__new__(
                    cls, name, parent, dct)
                registered_subparser_classes[subcommand] = klass
        else:
            # excluded subclasses
            klass = super(_RegisterParserMetaKlass, cls).__new__(
                cls, name, parent, dct)

        return klass


class RegisterParser(object):
    __metaclass__ = _RegisterParserMetaKlass
    # This must be supplied for every subclass except for the plot and
    # subparser helper
    SUBCOMMAND = None


class SubParserHelper(RegisterParser):

    """
    Base class for specific report sub-parsers.
    Store args and opts common across all report parsers.
    """

    def add_args(self, subparser):
        return add_base_options(subparser)


class PlotParserHelper(SubParserHelper):

    """
    Base class for reports that take common plot args.
    """

    def add_args(self, subparser):
        SubParserHelper.add_args(self, subparser)
        add_plot_options(subparser)


class AdapterParserHelper(PlotParserHelper):
    SUBCOMMAND = ADAPTER

    @property
    def help(self):
        return 'Generates adapter related statistics which are helpful in quantifying ' + \
            'the presence of adapter dimers.'

    def add_args(self, subparser):
        PlotParserHelper.add_args(self, subparser)
        subparser.add_argument("fofn", type=validate_fofn,
                               help="file containing list of bas.h5 file names")

    @staticmethod
    def run_report(args):
        return make_adapter_report(args.fofn, args.report, args.output, args.dpi, args.dumpdata)


class LoadingParserHelper(SubParserHelper):
    SUBCOMMAND = LOADING

    @property
    def help(self):
        return 'Generates a report exposing summary stats for the ' + \
            'Productivity metric from primary.'

    def add_args(self, subparser):
        SubParserHelper.add_args(self, subparser)
        subparser.add_argument(
            "csv", help="filtered_summary.csv", type=validate_file)

    @staticmethod
    def run_report(args):
        return make_loading_report(args.csv, args.report, args.output)


class CoverageParserHelper(PlotParserHelper):
    SUBCOMMAND = COVERAGE

    @property
    def help(self):
        return 'Generates a report showing coverage plots for the top 25 contigs of the supplied reference.'

    def add_args(self, subparser):
        PlotParserHelper.add_args(self, subparser)
        subparser.add_argument("reference",
                               help="reference file or directory",
                               type=str)
        subparser.add_argument("gff",
                               help="alignment_summary.gff",
                               type=validate_file)
        subparser.add_argument("--maxContigs", action="store",
                               default=25,
                               help="Max number of contigs to plot. Defaults to 25.")

    @staticmethod
    def run_report(args):
        return make_coverage_report(args.gff, args.reference, args.maxContigs,
                                    args.report, args.output, args.dpi, args.dumpdata)


class ControlParserHelper(PlotParserHelper):
    SUBCOMMAND = CONTROL

    @property
    def help(self):
        return 'Generates a report showing control quality and readlength information.'

    def add_args(self, subparser):
        PlotParserHelper.add_args(self, subparser)
        subparser.add_argument("cntrCmpH5",
                               help="control_reads.cmp.h5",
                               type=validate_file)
        subparser.add_argument("csv",
                               help="filtered_summary.csv",
                               type=validate_file)

    @staticmethod
    def run_report(args):
        return make_control_report(args.cntrCmpH5, args.csv,
                                   args.report, args.output, args.dpi, args.dumpdata)


class TopVariantParserHelper(SubParserHelper):

    """
    Create a top variant report
    """
    SUBCOMMAND = TOP_VARIANTS

    @property
    def help(self):
        return 'Generates a report showing a table of top variants sorted by confidence.'

    def _get_gff_help(self):
        return "variants.gff (can be gzip'ed)"

    def add_args(self, subparser):
        SubParserHelper.add_args(self, subparser)
        subparser.add_argument("gff",
                               help=self._get_gff_help())
        subparser.add_argument("reference",
                               help="reference file or directory",
                               type=str)
        subparser.add_argument("--how_many", default=100,
                               help="number of top variants to show (default=100)")
        subparser.add_argument("--batch_sort_size", default=10000,
                               help="Intermediate sort size parameter (default=10000)")

    @staticmethod
    def run_report(args):
        return make_topvariants_report(args.gff, args.reference,
                                       args.how_many, args.batch_sort_size, args.report, args.output)


class MinorTopVariantParserHelper(TopVariantParserHelper):

    """
    Create a top variant report
    """
    SUBCOMMAND = MINOR_TOP_VARIANTS

    @property
    def help(self):
        return 'Generates a report showing a table of minor top variants sorted by confidence.'

    def _get_gff_help(self):
        return "rare_variants.gff (can be gzip'ed)"

    @staticmethod
    def run_report(args):
        return make_topvariants_report(args.gff, args.reference,
                                       args.how_many, args.batch_sort_size, args.report, args.output, True)


class PolishedAssemblyParserHelper(SubParserHelper):

    """
    Create a polished assembly report
    """
    SUBCOMMAND = POLISHED_ASSEMBLY

    @property
    def help(self):
        return 'Generates a report assembly statistics.'

    def add_args(self, subparser):
        SubParserHelper.add_args(self, subparser)
        subparser.add_argument("gff",
                               help='Path to alignment_summary.gff file',
                               type=validate_file)
        subparser.add_argument("fastq",
                               help='Path to polished assembly FASTQ file',
                               type=validate_file)

    @staticmethod
    def run_report(args):
        return make_polished_assembly_report(args.report, args.gff, args.fastq, args.output)


class VariantsParserHelper(PlotParserHelper):
    SUBCOMMAND = VARIANTS

    @property
    def help(self):
        return 'Generates a table showing consensus stats and a ' + \
            'report showing variants plots for the top 25 contigs of the supplied reference.'

    def add_args(self, subparser):
        PlotParserHelper.add_args(self, subparser)
        subparser.add_argument("reference",
                               help="reference file or directory",
                               type=str)
        subparser.add_argument("aln_summ_gff",
                               help="alignment_summary.gff",
                               type=validate_file)
        subparser.add_argument("variants_gff",
                               help="variants.gff.gz",
                               type=validate_file)
        subparser.add_argument("--maxContigs", action="store",
                               default=25,
                               help="Max number of contigs to plot. Defaults to 25.")

    @staticmethod
    def run_report(args):
        return make_variants_report(args.aln_summ_gff, args.variants_gff, args.reference, args.maxContigs,
                                    args.report, args.output, args.dpi, args.dumpdata)


class ModificationsParserHelper(PlotParserHelper):
    SUBCOMMAND = MODIFICATIONS

    @property
    def help(self):
        return 'Finds DNA Modifications from their kinetic signature.'

    def add_args(self, subparser):
        PlotParserHelper.add_args(self, subparser)
        subparser.add_argument("csv",
                               help="modifications.csv.gz",
                               type=validate_file)

    @staticmethod
    def run_report(args):
        return make_modifications_report(args.csv, args.report, args.output, args.dpi, args.dumpdata)


class SatParserHelper(SubParserHelper):
    SUBCOMMAND = SAT

    @property
    def help(self):
        return 'Generates the SAT metric performance attributes'

    def add_args(self, subparser):
        SubParserHelper.add_args(self, subparser)
        subparser.add_argument("h5",
                               help="aligned_reads.cmp.h5",
                               type=validate_file)
        subparser.add_argument("var_rpt",
                               help="The variants report - i.e., variants_report.json",
                               type=validate_file)
        subparser.add_argument("mapping_stats_rpt",
                               help="The mapping stats report - i.e., mapping_stats_report.json",
                               type=validate_file)

    @staticmethod
    def run_report(args):
        return make_sat_report(args.h5,  args.mapping_stats_rpt, args.var_rpt, args.report, args.output)


def get_subparser_helpers():
    """
    Get a list of subparser helpers defined in this module.
    """
    return [klass() for klass in registered_subparser_classes.values()]
