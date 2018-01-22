import os
import logging
import unittest
import tempfile

from pbreports.plot.helper import get_fig_axes_lpr, apply_histogram_data, save_figure_with_thumbnail, make_2d_histogram, DEFAULT_DPI

log = logging.getLogger(__name__)


class TestPlotHelper(unittest.TestCase):

    def test_save_histograms(self):
        """Save std histograms."""
        tmpdir = tempfile.mkdtemp(prefix='pbreport_output')

        fig, ax = get_fig_axes_lpr()

        dump = os.path.join(tmpdir, 'dmp.data')

        log.debug('dmp file is {d}'.format(d=dump))

        apply_histogram_data(ax, [1, 2, 3, 4, 5, 6], 2,
                             axis_labels=('foo', 'bar'),
                             barcolor='#505050', xlim=(0, 20000),
                             data_file=dump)

        self.assertTrue(os.path.exists(dump))
        log.info("Writing temp histogram to {t}".format(t=tmpdir))

        save_figure_with_thumbnail(fig, os.path.join(tmpdir, 'foo.png'))
        self.assertTrue(os.path.exists(os.path.join(tmpdir, 'foo.png')))
        self.assertTrue(os.path.exists(os.path.join(tmpdir, 'foo_thumb.png')))

    def test_make_2d_histogram(self):
        x = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3]
        y = [4, 4, 3, 1, 2, 5, 6, 3, 3, 2, 4, 5, 6, 1, 3, 3, 4, 6, 5, 1]
        fig, ax = make_2d_histogram(
            x, y, [3, 6], "Number of Reads", "Imaginary read metric", "Some other metric")
        fig.savefig("fake_hist2d.png", dpi=DEFAULT_DPI)
