import os
from setuptools import setup, find_packages


version = __import__('pbreports').get_version()

_REQUIREMENTS_FILE = 'REQUIREMENTS.txt'


def _get_local_file(file_name):
    return os.path.join(os.path.dirname(__file__), file_name)


def _get_requirements(file_name):
    with open(file_name, 'r') as f:
        lines = f.readlines()
    reqs = [l for l in lines if not l.startswith("#")]
    return reqs


setup(
    name='pbreports',
    version=version,
    author='pbiDevNet',
    author_email='pbiDevNet@pacificbiosciences.com',
    license='LICENSE.txt',
    packages=find_packages(),
    zip_safe=False,
    install_requires=_get_requirements(_get_local_file(_REQUIREMENTS_FILE)),
    entry_points={'console_scripts': [
        'overview_report = pbreports.report.overview:main',
        'ccs_report = pbreports.report.ccs:main',
        'preassembly_report = pbreports.report.preassembly:main',
        'barcode_report = pbreports.report.barcode:main',
        'filter_subread_summary = pbreports.report.filter_subread_summary:main',
        'filter_stats = pbreports.report.filter_stats:main',
        'filter_subread = pbreports.report.filter_subread:main',
        'amplicon_analysis_consensus_report = pbreports.report.amplicon_analysis_consensus:main',
        'amplicon_analysis_input_report = pbreports.report.amplicon_analysis_input:main',
        'amplicon_analysis_timing_report = pbreports.report.amplicon_analysis_timing:main',
        'mapping_stats = pbreports.report.mapping_stats:main',
        'mapping_stats_poc = pbreports.report.mapping_stats_poc:main',
        'isoseq_classify_report = pbreports.report.isoseq_classify:main',
        'isoseq_cluster_report = pbreports.report.isoseq_cluster:main',
        'motifs_report = pbreports.report.motifs:main',
        'summarize_compare_by_movie = pbreports.report.summarize_compare_by_movie:main',
        'summarize_coverage = pbreports.report.summarize_coverage.summarize_coverage:main',
        'filter_stats_xml = pbreports.report.filter_stats_xml:main',
        'loading_xml = pbreports.report.loading_xml:main',
        'adapter_xml = pbreports.report.adapter_xml:main',
        ]}
)
