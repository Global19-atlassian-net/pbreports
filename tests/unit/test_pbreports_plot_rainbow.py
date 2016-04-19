
# TODO(nechols)(2016-04-18) this needs better coverage

import unittest

import pbcore.data

from pbreports.plot.rainbow import _read_in_file, _read_in_indexed_alignmentset

class TestRainbowPlot(unittest.TestCase):

    def test__read_in_file(self):
        bam = pbcore.data.getBamAndCmpH5()[0]
        data = _read_in_file(bam)
        self.assertTrue(all([row[2]==254 for row in data]))
        self.assertEqual(data[-1][0], 605)
        self.assertTrue(0.927 < data[-1][1] < 0.928)

    def test__read_in_indexed_alignmentset(self):
        bam = pbcore.data.getBamAndCmpH5()[0]
        data = _read_in_indexed_alignmentset(bam)
        self.assertTrue(all([row[2]==254 for row in data]))
        print data
        self.assertEqual(data[-1][0], 605)
        self.assertTrue(0.927 < data[-1][1] < 0.928)
