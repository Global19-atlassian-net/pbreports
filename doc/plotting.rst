Generating Plot Images
-----------------------

The relevant package is pbreports.plot

The code is structured as a set of static functions in helper.py. The general strategy for any plot type is to 
get a figure/axis tuple, then to pass the axis into a plot function, and to finally pass the figure into a save
function.

.. code-block:: python

    from pbreports.plot.helper import get_fig_axes_lpr, apply_histogram_data, save_figure_with_thumbnail

    def _save_histogram(data):
        """ Example showing how to save a histogram.
        data: numpy array
        """
        axis_labels = ('X Label', 'Y Label')
        bins = np.logspace(0, 4, 50)
        fig, ax = get_fig_axes_lpr()
        ax.set_xscale('log')
        apply_histogram_data(ax, mas, bins, axis_labels=axis_labels, \
                            barcolor='#505050', xlim=(0, 20000) )
    
        png_fn = os.path.join(output_dir, "adapter_" + pg_id + ".png" )
        png_fn, thumb = save_figure_with_thumbnail(fig, '/my/fig.png')
	
	
.. automodule:: pbreports.plot.helper
    :members: