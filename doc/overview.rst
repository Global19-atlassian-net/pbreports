Overview
----------

The pbreports package is used to create reports in a structured json format for end-user
visualization.

The package is organized as:


.. code-block:: bash

    pbreports$ tree -L 2 -d
	.
	|-- bin
	|-- docs
	|   |-- build
	|   `-- source
	|-- pbreports
	|   |-- io
	|   |-- plot
	|   `-- report
	`-- tests
	    |-- cram
	    `-- unit

	




The relevant packages for secondary developers are:

#. `pbreports` python library root namespace
#. `pbreports.io` contains readers for secondary data files, if not in pbcore.
#. `pbreports.plot` matplotlib functions for creating plots
#. `pbreports.report` entry point from the bin script. There should be one report module per report.
#. `pbreports.bin` location of pbreport.py script. 

Note that `pbreports.model` has moved to `pbcommand.models.report`.
