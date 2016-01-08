#!/usr/bin/env bash

TC_DIR=./tool_contracts


python -m pbreports.report.sat --emit-tool-contract > $TC_DIR/pbreports_report_sat_tool_contract.json
python -m pbreports.report.mapping_stats --emit-tool-contract > $TC_DIR/mapping_stats_tool_contract.json
python -m pbreports.report.variants --emit-tool-contract > $TC_DIR/pbreports_report_variants_tool_contract.json
python -m pbreports.report.top_variants --emit-tool-contract > $TC_DIR/pbreports_report_top_variants_tool_contract.json
python -m pbreports.report.modifications --emit-tool-contract > $TC_DIR/pbreports_report_modifications_tool_contract.json
python -m pbreports.report.motifs --emit-tool-contract > $TC_DIR/pbreports_report_motifs_tool_contract.json
python -m pbreports.report.summarize_coverage.summarize_coverage --emit-tool-contract > $TC_DIR/pbreports_report_summarize_coverage_tool_contract.json
python -m pbreports.report.loading_xml --emit-tool-contract > $TC_DIR/pbreports_report_loading_xml_tool_contract.json
python -m pbreports.report.adapter_xml --emit-tool-contract > $TC_DIR/pbreports_report_adapter_xml_tool_contract.json
python -m pbreports.report.filter_stats_xml --emit-tool-contract > $TC_DIR/pbreports_report_filter_stats_xml_tool_contract.json
python -m pbreports.report.isoseq_classify --emit-tool-contract > $TC_DIR/pbreports_report_isoseq_classify_tool_contract.json
python -m pbreports.report.isoseq_cluster --emit-tool-contract > $TC_DIR/pbreports_report_isoseq_cluster_tool_contract.json
python -m pbreports.report.polished_assembly --emit-tool-contract > $TC_DIR/pbreports_report_polished_assembly_tool_contract.json
python -m pbreports.report.preassembly --emit-tool-contract > $TC_DIR/pbreports_report_preassembly_tool_contract.json
