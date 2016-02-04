==================================================
pbreports specifications (automatically generated)
==================================================




**pbreports.report.mapping_stats**:


Generates a report of statistics for subreads mapped to a reference genome with
Blasr/pbalign.


==============================  =================================  =====================================================================================================================================
Attribute ID                    Name                               Description
==============================  =================================  =====================================================================================================================================
mapped_reads_n                  Mapped Reads                       The number of polymerase reads mapped to the reference sequence
mapped_subreads_n               Mapped Subreads                    The number of subreads mapped to the reference sequence
mapped_bases_n                  Mapped Polymerase Bases            The number of polymerase bases spanning all mapped subreads (including adapters and other unmapped regions)
mapped_subread_bases_n          Mapped Subread Bases               The number of subread bases mapped to the reference sequence
mapped_readlength_mean          Mapped Polymerase Read Length      The approximate mean length of polymerase reads that mapped to the reference sequence (including adapters and other unmapped regions)
mapped_subread_readlength_mean  Mapped Subread Length              The mean length of subreads that mapped to the reference sequence
mapped_readlength_q95           Mapped Polymerase Read Length 95%  The 95th percentile of read length of polymerase reads that mapped to the reference sequence
mapped_readlength_max           Mapped Polymerase Read Length Max  The maximum length of polymerase reads that mapped to the reference sequence
mapped_subreadlength_n50        Mapped Subread N50                 50% of full subreads that mapped to the reference sequence are longer than this value
mapped_readlength_n50           Mapped Read N50                    50% of polymerase reads that mapped to the reference sequence are longer than this value
==============================  =================================  =====================================================================================================================================


**pbreports.report.mapping_stats_ccs**:


Generates a report of statistics for CCS reads mapped to a reference genome
with Blasr/pbalign.


=========================  ================================  ================================================================================
Attribute ID               Name                              Description
=========================  ================================  ================================================================================
mapped_read_accuracy_mean  Mapped Consensus Read Accuracy    The mean accuracy of CCS reads that mapped to the reference sequence
mapped_reads_n             Mapped Consensus Reads            The number of CCS reads that mapped to the reference sequence
mapped_bases_n             Mapped Consensus Bases            The number of CCS read bases that mapped to the reference sequence
mapped_readlength_mean     Mapped Consensus Read Length      The mean length of CCS reads that mapped to the reference sequence
mapped_readlength_q95      Mapped Consensus Read Length 95%  The 95th percentile of length of CCS reads that mapped to the reference sequence
mapped_readlength_max      Mapped Consensus Read Length Max  The maximum length of CCS reads that mapped to the reference sequence
mapped_readlength_n50      Mapped N50                        50% of CCS reads that mapped to the reference sequence are longer than this
=========================  ================================  ================================================================================


**pbreports.report.variants**:


Generates a table showing consensus stats and a report showing variants plots
for the top 25 contigs of the supplied reference.


==========================  =======================================  ======================================================================================
Attribute ID                Name                                     Description
==========================  =======================================  ======================================================================================
mean_contig_length          Average Reference Length                 Average length of reference sequence contigs
weighted_mean_bases_called  Average Reference Bases Called           Percentage of the reference sequence for which consensus bases were called
weighted_mean_concordance   Average Reference Consensus Concordance  The percent accuracy (concordance) of the consensus sequence compared to the reference
weighted_mean_coverage      Average Reference Coverage               The mean depth of coverage across the reference sequence
longest_contig_name         Longest Reference Contig                 The FASTA header ID of the longest reference contig
==========================  =======================================  ======================================================================================


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


=========================  =================================  =============================================================================
Attribute ID               Name                               Description
=========================  =================================  =============================================================================
number_of_ccs_reads        Consensus (CCS) reads              The number of CCS reads
total_number_of_ccs_bases  Number of consensus bases          Total number of consensus bases in all CCS reads
mean_ccs_readlength        Mean Consensus Read Length         Mean length of CCS reads
mean_accuracy              Mean Consensus Predicted Accuracy  Mean predicted accuracy of CCS reads
mean_qv                    Mean Consensus Predicted QV        Phred log-scale QV, equivalent to mean accuracy
mean_ccs_num_passes        Mean Number of Passes              Mean number of complete subreads per CCS read, rounded to the nearest integer
=========================  =================================  =============================================================================


**pbreports.report.isoseq_classify**:

IsoSeq Classify report

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
avg_flnc_len              Average full-length non-chimeric read length  Average length of full-length, non-artificial-concatemer CCS reads
num_nflnc                 Number of non-full-length non-chimeric reads  The number of non-full-length non-artificial-concatemer CCS reads
num_nflc                  Number of non-full-length chimeric reads      The number of non-full-length reads that are artificial concatemers
num_flnc_bases            Number of full-length non-chimeric bases      Total number of bases in full-length non-artificial-concatemer CCS reads
========================  ============================================  =====================================================================================================================


**pbreports.report.isoseq_cluster**:

IsoSeq Cluster report

============================  ======================================================  ==========================================================================================================
Attribute ID                  Name                                                    Description
============================  ======================================================  ==========================================================================================================
num_consensus_isoforms        Number of unpolished consensus isoforms                 Total number of consensus isoforms, both high- and low-quality
num_polished_hq_isoforms      Number of polished high-quality isoforms                The number of consensus isoforms that have an estimated accuracy above the specified cutoff (0.99 default)
num_polished_lq_isoforms      Number of polished low-quality isoforms                 The number of consensus isoforms that have an estimated accuracy below the specified cutoff
avg_consensus_isoform_length  Average unpolished consensus isoforms read length       The average length of all consensus isoforms, both high- and low-quality
num_total_bases               Total number of bases in unpolished consensus isoforms  Total number of bases in unpolished consensus isoforms
============================  ======================================================  ==========================================================================================================