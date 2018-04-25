
"""
Functions to generate various specific plots.
"""

from pbreports.plot.helper import *


def plot_subread_lengths(subreads, png_file_name, dpi=300):
    """
    Plot subread lengths using the SubreadSet indices (.pbi files).
    """
    fig, axes = get_fig_axes_lpr()
    subread_lengths = subreads.index.qEnd - subreads.index.qStart
    axes.hist(subread_lengths,
              bins=40,
              color=get_green(0),
              edgecolor=get_green(0),
              rwidth=0.9)
    axes.set_xlabel("Subread Length")
    axes.set_ylabel("Number of Subreads")
    png, thumb = save_figure_with_thumbnail(fig, png_file_name, dpi=dpi)
    return (png, thumb)


def plot_stats_xml_distribution(dist, xlabel, ylabel, png_file_name, dpi=300):
    """
    Plot a distribution extracted from the SubreadSet sts.xml.
    """
    fig, axes = get_fig_axes_lpr()
    axes.bar(dist.labels, dist.bins,
             color=get_green(0),
             edgecolor=get_green(0),
             width=(dist.binWidth * 0.75))
    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    png, thumb = save_figure_with_thumbnail(fig, png_file_name, dpi=dpi)
    return (png, thumb)
