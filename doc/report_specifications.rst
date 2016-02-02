==================================================
pbreports specifications (automatically generated)
==================================================

Mapping Statistics
------------------

**pbreports.report.pbreports.report.mapping_stats**:

==============================  =============================  =============================================================================================
Attribute ID                    Name                           Description
==============================  =============================  =============================================================================================
mapped_reads_n                  Mapped Reads                   The number of polymerase reads mapped to the reference sequence
mapped_readlength_mean          Mapped Polymerase Read Length  The mean length of polymerase reads that mapped to the reference sequence, including adapters
mapped_readlength_n50           Mapped N50                     50% of polymerase reads that mapped to the reference sequence are longer than this value
mapped_subreads_n               Mapped Subreads                The number of subreads mapped to the reference sequence
mapped_subread_bases_n          Mapped Subread Bases           The number of subread bases mapped to the reference sequence
mapped_subread_readlength_mean  Mapped Subread Length          The mean length of subreads that mapped to the reference sequence
mapped_subread_accuracy_mean    Mapped Subread Accuracy        The mean concordance of subreads that mapped to the reference sequence
==============================  =============================  =============================================================================================
**pbreports.report.pbreports.report.mapping_stats_ccs**:

=========================  ==============================  ===========================================================================
Attribute ID               Name                            Description
=========================  ==============================  ===========================================================================
mapped_reads_n             Mapped Consensus Reads          The number of CCS reads that mapped to the reference sequence
mapped_readlength_mean     Mapped Consensus Read Length    The mean length of CCS reads that mapped to the reference sequence
mapped_readlength_n50      Mapped N50                      50% of CCS reads that mapped to the reference sequence are longer than this
mapped_bases_n             Mapped Consensus Bases          The number of CCS read bases that mapped to the reference sequence
mapped_read_accuracy_mean  Mapped Consensus Read Accuracy  The mean accuracy of CCS reads that mapped to the reference sequence
=========================  ==============================  ===========================================================================