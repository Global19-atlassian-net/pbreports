import os
import logging
import traceback
import json
import tempfile
import unittest
import shutil
import ConfigParser
from pprint import pformat
from jinja2 import Environment, FileSystemLoader

from pbreports.serializers import dict_to_report
from base_test_case import _NOSE_REPORT_CFG, ROOT_DATA_DIR, BaseTestCase

log = logging.getLogger(__name__)


class TestMetricsDocumenter(unittest.TestCase):

    """
    This class does not really test anything. It uses the unittest infrastructure 
    to find data and generate reports, which are then processed into html documentation.
    """

    def setUp(self):
        """
        Before *every* test
        """
        self._output_dir = tempfile.mkdtemp(suffix="metrics_reports")

        nosecfg = ConfigParser.SafeConfigParser()
        nosecfg.readfp(open(_NOSE_REPORT_CFG), 'r')

        # Set the template dir
        self._jinja_tmpls = self._expanded_abs_path(
            nosecfg.get('doc', 'jinja-templates'))
        log.info('Using jinja templates {j}'.format(j=self._jinja_tmpls))
        if not os.path.exists(self._jinja_tmpls):
            raise IOError(
                'Cannot find templates {j}.\nExiting metrics documentation!'.format(j=self._jinja_tmpls))

        # Set location to write the generated html. By default, same location as sphinx target.
        # Note: run sphinx documentation first, so the dir is there
        self._html_dir = self._expanded_abs_path(
            nosecfg.get('doc', 'html-dir'))
        if not os.path.isdir(self._html_dir):
            raise IOError(('No such directory to which to write metrics.html {j}.'
                           '\nExiting metrics documentation!').format(j=self._jinja_tmpls))

    def tearDown(self):
        """
        After *every* test
        """
        if os.path.exists(self._output_dir):
            shutil.rmtree(self._output_dir)

    def _expanded_abs_path(self, f):
        return os.path.abspath(os.path.expanduser(f))

    def _get_version(self):
        import pbreports
        version = pbreports.get_version()
        changelist = pbreports.get_changelist()
        return '{v}.{c}'.format(v=version, c=changelist)

    def _current_time(self):
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _num_reports(self):
        import pkgutil
        names = [name for _, name,
                 _ in pkgutil.iter_modules(['pbreports/report'])]
        log.info('report modules: {m}'.format(m=','.join(names)))
        return len(names)

    def test_make_docs(self):
        """
        This 'test' is the entry to documentation of all report attributes.
        Why is this documentation logic in a test?
        - Reports need to be generated off real data, and unit tests should provide consistent real data

        All reports should be represented here. Currently 5 reports (the last 5) only generate tables which we need
        to figure out how to incorporate in this metric list context.
        This affects: long_amplicon_analysis/modifications/topvariants/barcode/loading
        """

        reports = []
        # Add all reports here
        reports.append(self._create_variants_report())
        reports.append(self._create_reads_of_insert_report())
        reports.append(self._create_preassembly_report())
        reports.append(self._create_polished_assembly_report())
        reports.append(self._create_mapping_stats_report())
        reports.append(self._create_filter_stats_report())
        reports.append(self._create_filter_subread_report())
        reports.append(self._create_filter_subread_summary_report())
        reports.append(self._create_control_report())
        reports.append(self._create_adapter_report())
        reports.append(self._create_coverage_report())
        reports.append(self._create_overview_report())
       # reports.append(self._create_long_amplicon_report())
       # reports.append(self._create_modifications_report())
       # reports.append(self._create_top_variants_report())
       # reports.append(self._create_barcode_report())
       # reports.append(self._create_loading_report())

        # Generate html off jinja templates stored in doc/report-metrics
        env = Environment(loader=FileSystemLoader(self._jinja_tmpls))
        template = env.get_template('metrics.html')
        reports_with_attributes, reports_without_attributes = [], []
        [reports_with_attributes.append(i.id) for i in reports if i.attributes != []]
        #[reports_without_attributes.append(i.id) for i in reports if i.attributes == []]

        final_html = os.path.join(self._html_dir, 'metrics.html')
        num_rpt_modules = self._num_reports()
        num_documented = len(reports)
        num_with_attributes = len(reports_with_attributes)
        num_without_attributes = num_rpt_modules - num_with_attributes
        template_params = {'reports': reports,
                           'version': self._get_version(),
                           'when': self._current_time(),
                           'numreports': num_rpt_modules,
                           'numwithattributes': num_with_attributes,
                           'numwithoutattributes': num_without_attributes,
                           'numdocumented': num_documented}

        if num_with_attributes + num_without_attributes < num_rpt_modules:
            template_params[
                'warning'] = 'More documentation needs to be added!'

        template.stream(template_params).dump(final_html)

        log.info('Finished writing metrics html: {h}'.format(h=final_html))

    def _create_variants_report(self):
        """
        Creates and returns a variants report.
        """
        from pbreports.report.variants import make_variants_report
        from test_pbreports_report_variants import VARIANTS_DATA as datadir
        log.info(
            'Creating variants report using datadir {d}'.format(d=datadir))

        als = os.path.join(datadir, 'alignment_summary.gff')
        variants = os.path.join(datadir, 'variants.gff.gz')
        ref = os.path.join(datadir, 'ecoliK12_pbi_March2013')

        make_variants_report(als, variants, ref, 25,
                             'variants.json', self._output_dir, 60, False)
        return self._deserialize_report(os.path.join(self._output_dir, 'variants.json'))

    def _create_reads_of_insert_report(self):
        """
        Creates and returns a Reads of Insert report.
        """
        from pbreports.report.reads_of_insert import fofn_to_files, to_report
        from test_pbreports_report_reads_of_insert import _DATA_DIR as datadir
        log.info(
            'Creating reads_of_insert report using datadir {d}'.format(d=datadir))

        bas_files = fofn_to_files(os.path.join(datadir, 'reads_of_insert.fofn'))
        output_json = os.path.join(self._output_dir, 'reads_of_insert.json')
        report = to_report(bas_files, self._output_dir)
        pformat(report.to_dict())
        report.write_json(output_json)

        return self._deserialize_report(output_json)

    def _create_preassembly_report(self):
        """
        Creates and returns a Preassembly report.
        """
        from pbreports.report.preassembly import to_report
        from test_pbreports_report_preassembler import _DATA_DIR as datadir
        log.info(
            'Creating preassembly report using datadir {d}'.format(d=datadir))

        filtered_reads = os.path.join(datadir, 'filtered_subreads.fasta')
        filtered_longreads = os.path.join(datadir, 'filtered_longreads.fasta')
        corrected_reads = os.path.join(datadir, 'corrected.fasta')
        output_json = os.path.join(self._output_dir, 'preassembly_report.json')

        length_cutoff = 6000

        report = to_report(
            filtered_reads, filtered_longreads, corrected_reads, length_cutoff=None)
        pformat(report.to_dict())
        report.write_json(output_json)

        return self._deserialize_report(output_json)

    def _create_polished_assembly_report(self):
        """
        Creates and returns a Polished Assembly report
        """
        from pbreports.report.polished_assembly import make_polished_assembly_report
        datadir = os.path.join(ROOT_DATA_DIR, 'polished_assembly')
        log.info(
            'Creating Polished Assembly report using datadir {d}'.format(d=datadir))
        gff = os.path.join(
            ROOT_DATA_DIR, 'polished_assembly', 'alignment_summary.gff')
        fastq = os.path.join(
            ROOT_DATA_DIR, 'polished_assembly', 'polished_assembly.fastq')
        make_polished_assembly_report('polished_assembly.json', gff, fastq, self._output_dir)

        return self._deserialize_report(os.path.join(self._output_dir, 'polished_assembly.json'))

    def _create_mapping_stats_report(self):
        """
        Creates and returns a Mapping Stats report
        """
        from pbreports.report.mapping_stats import to_report, bas_fofn_to_bas_files
        from test_pbreports_report_mapping_stats import _IO_DATA_DIR as datadir

        log.info(
            'Creating Mapping Stats report using datadir {d}'.format(d=datadir))

        _to_p = lambda x: os.path.join(datadir, x)

        filtered_regions_fofn = _to_p('filtered_regions.fofn')
        filtered_summary = _to_p('filtered_summary.csv')
        input_fofn = _to_p('input.fofn')
        aligned_reads_cmph5 = _to_p('aligned_reads.cmp.h5')

        mode = "external"
        report_json = 'mapping_report.json'
        output_json = os.path.join(self._output_dir, 'mapping_report.json')
        bas_files = bas_fofn_to_bas_files(input_fofn)
        region_files = bas_fofn_to_bas_files(filtered_regions_fofn)

        report = to_report(bas_files, region_files,
                           aligned_reads_cmph5, report_json,
                           self._output_dir,
                           filter_summary_csv=filtered_summary,
                           mode=mode)

        pformat(report.to_dict())
        report.write_json(output_json)

        return self._deserialize_report(output_json)

    def _create_mapping_stats_gmap_report(self):
        """
        Creates and returns a Mapping Stats gmap report
        """
        from pbreports.report.mapping_stats import to_report, bas_fofn_to_bas_files
        from test_pbreports_report_mapping_stats import _GMAP_DATA_DIR as datadir

        log.info(
            'Creating Mapping Stats gmap report using datadir {d}'.format(d=datadir))

        _to_p = lambda x: os.path.join(datadir, x)

        filtered_regions_fofn = _to_p('filtered_regions.fofn')
        filtered_summary = _to_p('filtered_summary.csv')
        input_fofn = _to_p('input.fofn')
        aligned_reads_cmph5 = _to_p('aligned_reads.cmp.h5')

        mode = "external"
        report_json = 'mapping_report.json'
        output_json = os.path.join(self._output_dir, 'mapping_report.json')
        bas_files = bas_fofn_to_bas_files(input_fofn)
        region_files = bas_fofn_to_bas_files(filtered_regions_fofn)

        report = to_report(bas_files, region_files,
                           aligned_reads_cmph5, report_json,
                           self._output_dir,
                           filter_summary_csv=filtered_summary,
                           mode=mode)

        pformat(report.to_dict())
        report.write_json(output_json)

        return self._deserialize_report(output_json)

    def _create_filter_stats_report(self):
        """
        Creates and returns a Filter Stats report
        """
        from pbreports.report.filter_stats import to_report
        from test_pbreports_report_filter_stats import _DATA_DIR_NAME
        datadir = os.path.join(ROOT_DATA_DIR, _DATA_DIR_NAME)

        log.info(
            'Creating Filter Stats report using datadir {d}'.format(d=datadir))

        output_name = 'filter_stats.json'
        filtered_summary = os.path.join(datadir, 'filtered_summary.csv')
        output_json = os.path.join(self._output_dir, output_name)

        report = to_report(filtered_summary, self._output_dir, output_name)
        pformat(report)
        report.write_json(output_json)
        return self._deserialize_report(output_json)

    def _create_filter_subread_summary_report(self):
        """
        Creates and returns a Filter Subreads report
        """
        from pbreports.report.filter_subread import to_report

        datadir = os.path.join(ROOT_DATA_DIR, 'filter_subread')
        log.info(
            'Creating Filter subread summary report using datadir {d}'.format(d=datadir))

        output_name = 'filter_subread_summary.json'
        filtered_subread_summary = os.path.join(
            datadir, 'filtered_subread_summary.csv')
        output_json = os.path.join(self._output_dir, output_name)

        report = to_report(filtered_subread_summary, self._output_dir)
        pformat(report)
        report.write_json(output_json)
        return self._deserialize_report(output_json)

    def _create_filter_subread_report(self):
        """
        Creates and returns a Filter Subreads report
        """
        from pbreports.report.filter_subread import to_report
        from test_pbreports_report_filter_subread import ROOT_DATA_DIR, _DATA_DIR_NAME
        datadir = os.path.join(ROOT_DATA_DIR, _DATA_DIR_NAME)
        log.info(
            'Creating Filter subreads report using datadir {d}'.format(d=datadir))

        output_name = 'filter_subread.json'
        filtered_summary = os.path.join(
            datadir, 'filtered_subread_summary.csv')
        output_json = os.path.join(self._output_dir, output_name)
        report = to_report(filtered_summary, self._output_dir)
        pformat(report)
        report.write_json(output_json)
        return self._deserialize_report(output_json)

    def _create_control_report(self):
        """
        Creates and returns a Control Report
        """
        from pbreports.report.control import make_control_report

        datadir = os.path.join(ROOT_DATA_DIR, 'control')
        log.info('Creating Control report using datadir {d}'.format(d=datadir))

        cmph5 = os.path.join(datadir, 'control_reads.cmp.h5')
        csv = os.path.join(datadir, 'filtered_summary.csv')
        report_json = 'control.json'
        output_json = os.path.join(self._output_dir, report_json)
        dpi = 60
        dumpdata = False
        make_control_report(
            cmph5, csv, report_json, self._output_dir, dpi, dumpdata)
        return self._deserialize_report(output_json)

    def _create_adapter_report(self):
        """
        Creates and returns an Adapter Report
        """
        from pbreports.report.adapter import make_adapter_report
        from test_pbreports_report_adapters import DataCache as d

        BaseTestCase.setUpClass()
        d.data_dir = BaseTestCase.get_data_dir()

        log.info(
            'Creating adapter report using datadir {d}'.format(d=d.data_dir))

        fofn = os.path.join(self._output_dir, 'test.fofn')

        d.write_fofn(fofn)
        dpi = 60
        dumpdata = False
        output_json = os.path.join(self._output_dir, 'adapter.json')
        make_adapter_report(
            fofn, 'adapter.json', self._output_dir, dpi, dumpdata)

        return self._deserialize_report(output_json)

    def _create_overview_report(self):
        """
        Creates and returns an Overview report
        """
        from pbreports.report.overview import run, bas_fofn_to_bas_files
        from test_pbreports_report_overview import _DATA_DIR as datadir
        log.info(
            'Creating Overview report using datadir {d}'.format(d=datadir))

        input_name = 'input.fofn'
        input_fofn = os.path.join(datadir, input_name)
        bas_files = bas_fofn_to_bas_files(input_fofn)
        report_json = 'overview.json'
        output_json = os.path.join(self._output_dir, report_json)
        report = run(bas_files)
        pformat(report.to_dict())
        report.write_json(output_json)

        return self._deserialize_report(output_json)

    def _create_coverage_report(self):
        """
        Creates and returns a coverage report
        """
        from pbreports.report.coverage import make_coverage_report
        datadir = os.path.join(ROOT_DATA_DIR, 'coverage')

        log.info(
            'Creating Coverage report using datadir {d}'.format(d=datadir))

        ref = os.path.join(datadir, 'references', 'lambda')
        gff = os.path.join(datadir, 'alignment_summary.lambda.gff')
        max_contigs_to_plot = 25
        dpi = 60
        dumpdata = False
        report_json = 'coverage.json'
        output_json = os.path.join(self._output_dir, report_json)

        make_coverage_report(gff, ref, max_contigs_to_plot,
                             report_json, self._output_dir, dpi, dumpdata)

        return self._deserialize_report(output_json)

    def _create_loading_report(self):
        """
        Creates and returns a variants report.
        """
        from pbreports.report.loading import make_loading_report

        datadir = os.path.join(ROOT_DATA_DIR, 'loading')
        log.info('Creating loading report using datadir {d}'.format(d=datadir))
        csv = os.path.join(datadir, 'filtered_summary.csv')
        report_json = 'loading.json'
        output_json = os.path.join(self._output_dir, report_json)
        make_loading_report(csv, report_json, self._output_dir)

        return self._deserialize_report(output_json)

    def _create_long_amplicon_report(self):
        """
        Creates a Long Amplicon Report
        """
        from pbreports.report.long_amplicon_analysis import run_to_report
        from test_pbreports_report_long_amplicon_analysis import DATA_DIR as datadir

        log.info(
            'Creating Long Amplicon report using datadir {d}'.format(d=datadir))

        input_name = 'amplicon_assembly.csv'
        file_name = os.path.join(datadir, input_name)
        report_json = 'long_amplicon.json'
        output_json = os.path.join(self._output_dir, report_json)
        report = run_to_report(file_name)
        pformat(report.to_dict())
        report.write_json(output_json)

        return self._deserialize_report(output_json)

    def _create_modifications_report(self):
        """
        Creates a Base Modifications report
        """
        from pbreports.report.modifications import make_modifications_report
        datadir = os.path.join(ROOT_DATA_DIR, 'modifications')
        log.info(
            'Creating modifications report using datadir {d}'.format(d=datadir))

        csv = os.path.join(datadir, 'modifications.csv.gz')
        report_json = 'modifications.json'
        output_json = os.path.join(self._output_dir, report_json)
        dpi = 60
        dumpdata = False

        make_modifications_report(
            csv, report_json, self._output_dir, dpi, dumpdata)

        return self._deserialize_report(output_json)

    def _create_barcode_report(self):
        """
        Creates and returns a Barcode Report
        """
        from pbreports.report.barcode import run_to_report, _to_tuple_list
        from test_pbreports_report_barcode import _DATA_DIR as datadir
        log.info('Creating Barcode report using datadir {d}'.format(d=datadir))

        bas_h5_fofn = os.path.join(datadir, 'bash5.fofn')
        barcode_h5_fofn = os.path.join(datadir, 'barcodeh5.fofn')
        bas_barcode_list = _to_tuple_list(bas_h5_fofn, barcode_h5_fofn)
        report_json = 'barcode.json'
        output_json = os.path.join(self._output_dir, report_json)
        use_subreads = True
        report = run_to_report(bas_barcode_list, subreads=use_subreads)
        pformat(report.to_dict())
        report.write_json(output_json)
        return self._deserialize_report(output_json)

    def _create_top_variants_report(self):
        """
        Creates and returns a Top Variants report.
        """
        from pbreports.report.top_variants import make_topvariants_report
        datadir = os.path.join(ROOT_DATA_DIR, 'topvariants')
        log.info(
            'Creating top variants report using datadir {d}'.format(d=datadir))

        ref = os.path.join(datadir, 'ecoliK12_pbi_March2013')
        gff = os.path.join(datadir, 'variants.gff.gz')
        how_many = 100
        batch_sort_size = 10000
        report = 'topvariants.json'
        output_json = os.path.join(self._output_dir, report)

        make_topvariants_report(gff, ref, how_many, batch_sort_size, report,
                                self._output_dir)

        return self._deserialize_report(output_json)

    def _deserialize_report(self, rptfile):
        """
        Read json report from file, return pbreports.model.Report
        """
        s = None
        with open(os.path.join(rptfile), 'r') as f:
            s = json.load(f)

        return dict_to_report(s)
