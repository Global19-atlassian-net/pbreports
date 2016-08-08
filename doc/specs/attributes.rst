==================================================
pbreports specifications (automatically generated)
==================================================




**Adapter Report** (adapter_xml_report):

None

==============  ==========================  ============================================
Attribute ID    Name                        Description
==============  ==========================  ============================================
adapter_dimers  Adapter Dimers (0-10bp) %   Percentage of Prod1 ZMWs with adapter dimers
short_inserts   Short Inserts (11-100bp) %  Percentage of Prod1 ZMWs with short inserts
==============  ==========================  ============================================


**CCS Report** (ccs):

None

=========================  =======================  =============================================================================
Attribute ID               Name                     Description
=========================  =======================  =============================================================================
number_of_ccs_reads        CCS reads                The number of CCS reads
total_number_of_ccs_bases  Number of CCS bases      Total number of consensus bases in all CCS reads
mean_ccs_readlength        CCS Read Length (mean)   Mean length of CCS reads
mean_accuracy              CCS Read Score (mean)    Mean CCS read score
mean_ccs_num_passes        Number of Passes (mean)  Mean number of complete subreads per CCS read, rounded to the nearest integer
=========================  =======================  =============================================================================


**Control Report** (control):

None

================================  ==================================  =============
Attribute ID                      Name                                  Description
================================  ==================================  =============
control_sequence                  Control Sequence
n_control_reads                   Number of Control Reads
frac_control_reads                Fraction Control Reads
control_subread_accuracy          Control Subread Accuracy
control_n50                       Control Polymerase Read Length N50
control_95_percentile_readlength  Control Polymerase Read Length 95%
control_mean_readlength           Control Polymerase Read Length
================================  ==================================  =============


**Coverage** (coverage):

None

===================  =================  ============================================
Attribute ID         Name               Description
===================  =================  ============================================
depth_coverage_mean  Mean Coverage      Mean depth of coverage over entire reference
missing_bases_pct    Missing Bases (%)  Percent of reference bases without coverage
===================  =================  ============================================


**Raw Data Report** (raw_data_report):

None

==============  =============================  =============
Attribute ID    Name                           Description
==============  =============================  =============
nbases          Polymerase Read Bases
nreads          Polymerase Reads
read_n50        Polymerase Read N50
read_length     Polymerase Read Length (mean)
insert_length   Insert Length (mean)
==============  =============================  =============


**Subread filtering** (filter_subread):

None

=====================  =====================  =============
Attribute ID           Name                     Description
=====================  =====================  =============
filter_subread_nbases  Total Number of Bases
filter_subread_nreads  Number of Reads
filter_subread_mean    Mean Subread Length
filter_subread_n50     N50
=====================  =====================  =============


**Transcript Classification** (isoseq_classify):

None

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


**Transcript Clustering** (isoseq_cluster):

None

============================  ======================================================  ==========================================================================================================
Attribute ID                  Name                                                    Description
============================  ======================================================  ==========================================================================================================
num_consensus_isoforms        Number of unpolished consensus isoforms                 Total number of consensus isoforms, both high- and low-quality
num_polished_hq_isoforms      Number of polished high-quality isoforms                The number of consensus isoforms that have an estimated accuracy above the specified cutoff (0.99 default)
num_polished_lq_isoforms      Number of polished low-quality isoforms                 The number of consensus isoforms that have an estimated accuracy below the specified cutoff
avg_consensus_isoform_length  Mean unpolished consensus isoforms read length          The average length of all consensus isoforms, both high- and low-quality
num_total_bases               Total number of bases in unpolished consensus isoforms  Total number of bases in unpolished consensus isoforms
============================  ======================================================  ==========================================================================================================


**Mapping Report** (mapping_stats):

Create a Mapping Report from a Aligned BAM or Alignment DataSet

===============================  ====================================  ====================================================================================================================================================================================================================
Attribute ID                     Name                                  Description
===============================  ====================================  ====================================================================================================================================================================================================================
mapped_subread_concordance_mean  Mean Concordance (mapped)             The mean concordance of subreads that mapped to the reference sequence
mapped_subreads_n                Number of Subreads (mapped)           The number of subreads mapped to the reference sequence
mapped_subread_bases_n           Number of Subread Bases (mapped)      The number of subread bases mapped to the reference sequence
mapped_subread_readlength_mean   Subread Length Mean (mapped)          The mean length of the mapped portion of subreads which mapped to the reference sequence
mapped_subreadlength_n50         Subread Length N50 (mapped)           The subread length at which 50% of the mapped bases are in subreads longer than, or equal to, this value
mapped_subreadlength_q95         Subread Length 95% (mapped)           The 95th percentile of length of subreads that mapped to the reference sequence
mapped_subread_readlength_max    Subread Length Max (mapped)           The maximum length of subreads that mapped to the reference sequence
mapped_reads_n                   Number of Polymerase Reads (mapped)   The number of polymerase reads mapped to the reference sequence
mapped_readlength_mean           Polymerase Read Length Mean (mapped)  The approximate mean length of polymerase reads that mapped to the reference sequence starting from the first mapped base of the first mapped subread and ending at the last mapped base of the last mapped subread.
mapped_readlength_n50            Polymerase Read N50 (mapped)          The read length at which 50% of the mapped bases are in polymerase reads longer than, or equal to, this value
mapped_readlength_q95            Polymerase Read Length 95% (mapped)   The 95th percentile of read length of polymerase reads that mapped to the reference sequence
mapped_readlength_max            Polymerase Read Length Max (mapped)   The maximum length of polymerase reads that mapped to the reference sequence
===============================  ====================================  ====================================================================================================================================================================================================================


**CCS Mapping Statistics** (mapping_stats_report):

None

============================  ================================  ===========================================================================================
Attribute ID                  Name                              Description
============================  ================================  ===========================================================================================
mapped_read_concordance_mean  Mapped CCS Read Mean Concordance  The mean concordance of CCS reads that mapped to the reference sequence
mapped_reads_n                Number of CCS Reads (mapped)      The number of CCS reads that mapped to the reference sequence
mapped_bases_n                Number of CCS Bases (mapped)      The number of CCS read bases that mapped to the reference sequence
mapped_readlength_mean        CCS Read Length Mean (mapped)     The mean length of CCS reads that mapped to the reference sequence
mapped_readlength_n50         CCS Read Length N50 (mapped)      The read length at which 50% of the bases are in reads longer than, or equal to, this value
mapped_readlength_q95         CCS Read Length 95% (mapped)      The 95th percentile of length of CCS reads that mapped to the reference sequence
mapped_readlength_max         CCS Read Length Max (mapped)      The maximum length of CCS reads that mapped to the reference sequencee
============================  ================================  ===========================================================================================


**Overview** (overview):

None

==============  ==========  =============
Attribute ID    Name          Description
==============  ==========  =============
ncells          SMRT Cells
nmovies         Movies
==============  ==========  =============


**Polished Assembly** (polished_assembly):

None

==================  =====================  ==========================================
Attribute ID        Name                   Description
==================  =====================  ==========================================
polished_contigs    Polished Contigs       The number of polished contigs.
max_contig_length   Maximum Contig Length  Length of longest contig
n_50_contig_length  N50 Contig Length      50% of contigs are longer than this value.
sum_contig_lengths  Sum of Contig Lengths  Total length of all contigs.
==================  =====================  ==========================================


**Site Acceptance Test Report** (sat):

Generates the SAT metric performance attributes

======================  ====================================  =====================================================================================================================================
Attribute ID            Name                                  Description
======================  ====================================  =====================================================================================================================================
instrument              Instrument ID                         ID of the Sequel or RSII instrument on which the data were collected
coverage                Genome Coverage                       Percentage of the genome for which consensus bases were called
concordance             Consensus Concordance                 Percent concordance of the consensus sequence versus the reference
mapped_readlength_mean  Polymerase Read Length Mean (mapped)  The approximate mean length of polymerase reads that mapped to the reference sequence (including adapters and other unmapped regions)
reads_in_cell           Number of Polymerase Reads (mapped)   Number of polymerase reads that could be mapped to the reference genome
======================  ====================================  =====================================================================================================================================


**Consensus Variants** (variants):

None

==========================  ======================================  ===========================================================================
Attribute ID                Name                                    Description
==========================  ======================================  ===========================================================================
weighted_mean_concordance   Reference Consensus Concordance (mean)  The percent concordance of the consensus sequence compared to the reference
mean_contig_length          Reference Contig Length (mean)          Mean length of reference sequence contigs
longest_contig_name         Longest Reference Contig                The FASTA header ID of the longest reference contig
weighted_mean_bases_called  Percent Reference Bases Called (mean)   Percentage of the reference sequence for which consensus bases were called
weighted_mean_coverage      Reference Coverage (mean)               The mean depth of coverage across the reference sequence
==========================  ======================================  ===========================================================================