import os
import logging
import unittest
import tempfile

from pbreports.plot.helper import get_fig_axes_lpr, apply_histogram_data, save_figure_with_thumbnail

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
