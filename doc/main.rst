Design Model
-----------------------------

A report is composed of model objects whose classes are defined in pbreports.model. Typically, a report object is created and then attributes, tables, or plotGroups are
added to the report. Lastly, the report is serialized as json to a file.

The objects that comprise a report extend BaseReportElement. All report elements have an id. When the
report is converted to a dictionary before serialization, each report element's id is prepended with its parent id, 
which has also been prepended. For example, given the nested elements of report --> plotGroup --> plot, with respective ids "r", "pg", and "p",
the plot id would be "r.pg.p" in the dictionary.

For a list of available attributes, see:
   `Secondary Metric List <http://smrtanalysis-docs/metrics.html>`_



Report
-------------

Report is the root class of the model hierarchy. It's instantiated with an id (should be a short string), which defines its namespace. 
This example shows how a report is with one attribute, plotGroup, and table is created and written.

.. code-block:: python

    import os
    import logging

    from pbreports.model.model import Report, Attribute, PlotGroup, Table

    log = logging.getLogger(__name__)
   
    def make_report():
        """Write a simple report"""
        table = create_table() #Not shown
        attribute = create_attribute() #Not shown
        plotGroup = create_plotGroup() #Not shown

        r = Report('loading', attributes=[attribute], plotgroups=[plotGroup], tables=[table])

        #or
        r.add_table(table)
        r.add_attribute(attribute)
        r.add_plotGroup(plotGroup)

        r.write_json('/my/file.json')
            

.. autoclass:: pbreports.model.model.Report
    :members:
    :special-members:
	
	
Attribute
-------------

An attribute represents a key-value pair with an optional name. The id is the key. A report contains
a list of attributes.

.. code-block:: python

    import os
    import logging

    from pbreports.model.model import Attribute

    log = logging.getLogger(__name__)
   
    def create_attribute():
        """Return an attribute"""
        a = Attribute('myid', name='some name')
        return a
            

.. autoclass:: pbreports.model.model.Attribute
    :members:
    :special-members:
	
	
Table
-------------

A table contains a list of column objects and has an optional title and id. A report contains a list of tables.
In general, the paradigm for creating a table is to instantiate a table and a series of columns. Add the 
columns to the table in the desired order. Finally, iterate over your data set and append data to the
columns by index.
 
.. code-block:: python

    import os
    import logging
    import random

    from pbreports.model.model import Table, Column

    log = logging.getLogger(__name__)
   
    def create_table():
        """Return a table with 2 columns"""
        columns = [Column( 'c1id', header='C1 header'),\
        	Column('c2id', header='C2 header')]

        t = Table('myid', title='some title', columns=columns)

        #Now append data to the columns
        #Assume data is a list of tuples of len == 2
        datum = [(c.id, random.random()) for c in columns]
        for column_id, value in datum:
            t.add_data_by_column_id(column_id, value)

        return t
            
.. autoclass:: pbreports.model.model.Table
    :members:
    :special-members:
	
.. autoclass:: pbreports.model.model.Column
    :members:
    :special-members:

	
PlotGroup
-------------

A plotGroup represents a collection of plots that convey related information, such coverage across
5 contigs. A plotGroup has an id, an optional thumbnail (to represent the group in SMRTPortal in a 
preview), an optional legend and a list of plots 
 
.. code-block:: python

    import os
    import logging

    from pbreports.model.model import PlotGroup, Plot

    log = logging.getLogger(__name__)
   
    def create_plotGroup():
        """Return a PlotGroup with 1 plot"""

        plot = Plot('plot_id', image='/my/image.png', caption='this is a plot')
        p = PlotGroup('myid', title='some title', legend='/my/legend.png', thumbnail='/my/thumb.png', plots=[plot])

        # or p.add_plot(plot)
        return p
            
.. autoclass:: pbreports.model.model.PlotGroup
    :members:
    :special-members:
	
.. autoclass:: pbreports.model.model.Plot
    :members:
    :special-members: