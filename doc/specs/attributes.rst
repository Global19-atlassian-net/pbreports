==================================================
pbreports specifications (automatically generated)
==================================================




**pbreports.report.mapping_stats**:


Generates a report of statistics for subreads mapped to a reference genome with
Blasr/pbalign.


===============================  ====================================  =====================================================================================================================================
Attribute ID                     Name                                  Description
===============================  ====================================  =====================================================================================================================================
mapped_subread_concordance_mean  Mean Mapped Concordance               The mean concordance of subreads that mapped to the reference sequence
mapped_subreads_n                Number of Subreads (mapped)           The number of subreads mapped to the reference sequence
mapped_subread_bases_n           Number of Subread Bases (mapped)      The number of subread bases mapped to the reference sequence
mapped_subread_readlength_mean   Subread Length Mean (mapped)          The mean length of subreads that mapped to the reference sequence
mapped_subreadlength_n50         Subread Length N50 (mapped)           The subread length at which 50% of the mapped bases are in subreads longer than, or equal to, this value
mapped_subreadlength_q95         Subread Length 95% (mapped)           The 95th percentile of length of subreads that mapped to the reference sequence
mapped_subread_readlength_max    Subread Length Max (mapped)           The maximum length of subreads that mapped to the reference sequence
mapped_reads_n                   Number of Polymerase Reads (mapped)   The number of polymerase reads mapped to the reference sequence
mapped_readlength_mean           Polymerase Read Length Mean (mapped)  The approximate mean length of polymerase reads that mapped to the reference sequence (including adapters and other unmapped regions)
mapped_readlength_n50            Polymerase Read N50 (mapped)          The read length at which 50% of the mapped bases are in polymerase reads longer than, or equal to, this value
mapped_readlength_q95            Polymerase Read Length 95% (mapped)   The 95th percentile of read length of polymerase reads that mapped to the reference sequence
mapped_readlength_max            Polymerase Read Length Max (mapped)   The maximum length of polymerase reads that mapped to the reference sequence
===============================  ====================================  =====================================================================================================================================


**pbreports.report.mapping_stats_ccs**:


Generates a report of statistics for CCS reads mapped to a reference genome
with Blasr/pbalign.


============================  ================================  ===========================================================================================
Attribute ID                  Name                              Description
============================  ================================  ===========================================================================================
mapped_read_concordance_mean  Mapped CCS Read Mean Concordance  The mean concordance of CCS reads that mapped to the reference sequence
mapped_reads_n                Number of CCS Reads (mapped)      The number of CCS reads that mapped to the reference sequence
mapped_bases_n                Number of CCS Bases (mapped)      The number of CCS read bases that mapped to the reference sequence
mapped_readlength_mean        CCS Read Length Mean (mapped)     The mean length of CCS reads that mapped to the reference sequence
mapped_readlength_n50         CCS Read Length N50 (mapped)      The read length at which 50% of the bases are in reads longer than, or equal to, this value
mapped_readlength_q95         CCS Read Length 95% (mapped)      The 95th percentile of length of CCS reads that mapped to the reference sequence
mapped_readlength_max         CCS Read Length Max (mapped)      The maximum length of CCS reads that mapped to the reference sequence
============================  ================================  ===========================================================================================


**pbreports.report.coverage**:


Generates a report showing coverage plots for the top 25 contigs of the
supplied reference.


===================  =================  ============================================
Attribute ID         Name               Description
===================  =================  ============================================
depth_coverage_mean  Mean Coverage      Mean depth of coverage over entire reference
missing_bases_pct    Missing Bases (%)  Percent of reference bases without coverage
===================  =================  ============================================


**pbreports.report.variants**:


Generates a table showing consensus stats and a report showing variants plots
for the top 25 contigs of the supplied reference.


==========================  ======================================  ======================================================================================
Attribute ID                Name                                    Description
==========================  ======================================  ======================================================================================
weighted_mean_concordance   Reference Consensus Concordance (mean)  The percent accuracy (concordance) of the consensus sequence compared to the reference
mean_contig_length          Reference Contig Length (mean)          Mean length of reference sequence contigs
longest_contig_name         Longest Reference Contig                The FASTA header ID of the longest reference contig
weighted_mean_bases_called  Percent Reference Bases Called (mean)   Percentage of the reference sequence for which consensus bases were called
weighted_mean_coverage      Reference Coverage (mean)               The mean depth of coverage across the reference sequence
==========================  ======================================  ======================================================================================


**pbreports.report.sat**:


Generates the SAT metric performance attributes


======================  =======================  ==================================================================================
Attribute ID            Name                     Description
======================  =======================  ==================================================================================
instrument              Instrument ID            ID of the Sequel or RSII instrument on which the data were collected
coverage                Genome Coverage          Percentage of the genome for which consensus bases were called
accuracy                Consensus Accuracy       Percent accuracy of the consensus sequence versus the reference
mapped_readlength_mean  Mean Mapped Read Length  Mean length of polymerase reads mapped to the reference genome, including adapters
reads_in_cell           Reads in cell            Number of polymerase reads that could be mapped to the reference genome
======================  =======================  ==================================================================================


**pbreports.report.ccs**:


Generate a report summarizing Circular Consensus Read (CCS) results.


=========================  =======================  =============================================================================
Attribute ID               Name                     Description
=========================  =======================  =============================================================================
number_of_ccs_reads        CCS reads                The number of CCS reads
total_number_of_ccs_bases  Number of CCS bases      Total number of consensus bases in all CCS reads
mean_ccs_readlength        CCS Read Length (mean)   Mean length of CCS reads
mean_accuracy              CCS Read Score (mean)    Mean predicted accuracy of CCS reads
mean_ccs_num_passes        Number of Passes (mean)  Mean number of complete subreads per CCS read, rounded to the nearest integer
=========================  =======================  =============================================================================


**pbreports.report.polished_assembly**:

Generate a report based on the polished assembly

==================  =====================  =========================================
Attribute ID        Name                   Description
==================  =====================  =========================================
polished_contigs    Polished Contigs       Number of assembled contigs
max_contig_length   Maximum Contig Length  Length of longest contig
n_50_contig_length  N50 Contig Length      50% of contigs are longer than this value
sum_contig_lengths  Sum of Contig Lengths  Total length of all contigs
==================  =====================  =========================================


**pbreports.report.isoseq_classify**:

Iso-Seq Classify report

========================  ============================================  =====================================================================================================================
Attribute ID              Name                                          Description
========================  ============================================  =====================================================================================================================
num_reads                 Number of consensus reads                     Total number of CCS reads in the input file; this will be identical to the value in the CCS report
num_5_seen                Number of five prime reads                    The number of CCS reads with a 5-prime signal detected
num_3_seen                Number of three prime reads                   The number of CCS reads with a 3-prime signal detected
num_polya_seen            Number of poly-A reads                        The number of CCS reads with poly-A and 3-prime signals detected
num_filtered_short_reads  Number of filtered short reads                The number of CCS reads whose read length is less than the specified minimum sequence length
num_nfl                   Number of non-full-length reads               The number of non-full-length CCS reads; these are missing the poly-A tail and/or a terminal signal
num_fl                    Number of full-length reads                   The number of full-length CCS reads. (Full-length reads are reads which have both prime signals and poly-A detected.)
num_flnc                  Number of full-length non-chimeric reads      The number of full-length CCS reads that are not artificial concatemers
avg_flnc_len              Mean full-length non-chimeric read length     Mean length of full-length, non-artificial-concatemer CCS reads
num_nflnc                 Number of non-full-length non-chimeric reads  The number of non-full-length non-artificial-concatemer CCS reads
num_nflc                  Number of non-full-length chimeric reads      The number of non-full-length reads that are artificial concatemers
num_flnc_bases            Number of full-length non-chimeric bases      Total number of bases in full-length non-artificial-concatemer CCS reads
========================  ============================================  =====================================================================================================================


**pbreports.report.isoseq_cluster**:

Iso-Seq Cluster report

============================  ======================================================  ==========================================================================================================
Attribute ID                  Name                                                    Description
============================  ======================================================  ==========================================================================================================
num_consensus_isoforms        Number of unpolished consensus isoforms                 Total number of consensus isoforms, both high- and low-quality
num_polished_hq_isoforms      Number of polished high-quality isoforms                The number of consensus isoforms that have an estimated accuracy above the specified cutoff (0.99 default)
num_polished_lq_isoforms      Number of polished low-quality isoforms                 The number of consensus isoforms that have an estimated accuracy below the specified cutoff
avg_consensus_isoform_length  Mean unpolished consensus isoforms read length          The average length of all consensus isoforms, both high- and low-quality
num_total_bases               Total number of bases in unpolished consensus isoforms  Total number of bases in unpolished consensus isoforms
============================  ======================================================  ==========================================================================================================
