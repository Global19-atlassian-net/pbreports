import os
import unittest
import logging
import random

from pbreports.model.aggregators import (MaxAggregator, MinAggregator,
                                         MeanAggregator, CountAggregator,
                                         SumAggregator, HistogramAggregator)

log = logging.getLogger(__name__)


class Record(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        # this what the aggregators with use
        setattr(self, name, value)


class TestAggregators(unittest.TestCase):

    def setUp(self):
        self.record_name = 'my_record'
        self.values = [23.0, 1.0, 22.0, 20.0, 19.5]
        self.records = [Record(self.record_name, v) for v in self.values]

    def test_max_aggregator(self):
        a = MaxAggregator(self.record_name)
        for record in self.records:
            a.apply(record)
        self.assertEqual(a.value, max(self.values))

    def test_min_aggregator(self):
        a = MinAggregator(self.record_name)
        for record in self.records:
            a.apply(record)
        self.assertEqual(a.value, min(self.values))

    def test_mean_aggregator(self):
        a = MeanAggregator(self.record_name)
        for record in self.records:
            a.apply(record)

        total = sum(self.values)
        mean = total / len(self.values)
        self.assertEqual(a.total, total)
        self.assertEqual(a.mean, mean)

    def test_count_aggregator(self):
        a = CountAggregator(self.record_name)
        for record in self.records:
            a.apply(record)
        self.assertEqual(a.total, len(self.values))

    def test_sum_aggregator(self):
        a = SumAggregator(self.record_name)
        for record in self.records:
            a.apply(record)
        self.assertEqual(a.total, sum(self.values))

    def test_histogram_aggregator(self):
        a = HistogramAggregator(self.record_name, 0.0, dx=1)
        for record in self.records:
            a.apply(record)

        nbins = 26
        self.assertEqual(a.nbins, nbins)
        self.assertEqual(a.max_value, max(self.values) + 3)
