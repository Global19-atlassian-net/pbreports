**ZMW Read**

The ZMW read is the run of basecalls generated from the full output of a particular ZMW. This run of basecalls is subject to errors due to optical and other limitations. A ZMW read could contain basecalls that are made from analyzing background noise, or from two sequencing reactions happening simultaneously within the ZMW. In the standard mode of operation, a ZMW read is processed during post-primary analysis so that only a high-quality region of the ZMW read is provided to secondary analysis.

**Polymerase Read**

The polymerase read is the high-quality region of a ZMW read. This is the longest contiguous sequence of basecalls from a ZMW that we are confident is representative of a single piece of DNA and has accurate basecalls. The polymerase read will include every component of the smrtbell: the DNA insert, adapters, and barcodes in the case of a multiplexed sample. 

**HQ Region**

The HQ region is the region of the ZMW Read that defines the polymerase read. It is defined using basecalling pulse metrics to identify a maximal span of single-polymerase activity. 

**Subread**

A subread is a section of a polymerase read which we believe represents the DNA insert. Most polymerase reads will contain multiple passes around the smrtbell, and therefore there will be multiple subreads per ZMW. These subreads are typically used to create a single consensus read. Subreads are contained in ``*.subreads.bam`` files. The tenth column of a ``*.subreads.bam`` file contains the subread. 

The first column contains a string like ``m54008_160219_003234/4194415/379_5478`` where ``379`` and ``5478`` are the positions of the first and last bases of the subread in polymerase read coordinates. 

**Consensus Read**

The consensus read is the best estimate of the DNA insert sequence, and it is based on analyzing all the subreads associated with a single ZMW. Consensus reads are produced by CCS2: ``pbsmrtpipe.pipelines.sa3_ds_ccs``. CCS2 produces a bam file with one sequence per line representing the best estimate of the DNA insert sequence. 

**Barcode**

The barcode is a piece of DNA that is used to identify the origin of a DNA Insert. It is used for multiplexing. Barcode sequences can be found in the ``*.scraps.bam`` file.

**Adapter**

The Adapter is a piece of DNA that circularizes the DNA Insert and optional barcode. It enables the formation of the SMRTBell. Adapter sequences can be found in the ``*.scraps.bam`` file.

**DNA Insert**

The DNA Insert is the piece of DNA extracted from the user's biological sample, which is then prepped for sequencing with the addition of adapters and optional barcodes. 

**Mapped Subread Length**

The mapped subread length is the length of the portion of the subread that mapped. In other words, it is the number of subread bases that are contained in the alignment. 

**Mapped Polymerase Read Length**

The mapped polymerase read length is the length of the portion of the polymerase read that contains subreads that mapped, starting from the first mapped base to the last mapped base. It is computed in terms of polymerase read coordinates. Taking the position of the last mapped base of the last mapped subread, and subtracting from that the position of the first mapped base of the first mapped subread yields the mapped polymerase read length. Note that this will contain all the subreads, adapters, and potentially barcodes in between. The purpose of the mapped polymerase read length is to compute the length of the polymerase read that was actually useful. It is therefore an important metric in the quality of the sequencing results. 

**Concordance**

Concordance quantifies the degree to which a subread matches with the reference sequence within the aligned portion of the subread. It is computed by diving the number of mismatches and indels in the alignment by the number of bases in the aligned portion of the subread and subtracting from one. Thus, if there are no mismatches or indels, concordance will be 1. On the other hand, because deletions could be very large, and are not included in the subread length, concordance could be a large negative number. The formula for concordance is:

``1 - (num_mismatches + num_Insertions + num_Deletions)/length_of_aligned_portion_of_subread``
