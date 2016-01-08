import random
import unittest

from pbreports.report.summarize_coverage import interval_tree


class TestIntervalTree(unittest.TestCase):
    """Test the IntervalTree class.

    It only provides two things worth testing: its constructor
    and the find_overlapping method.
    """
    
    def test_random_intervals(self):
        """Test random interval lists."""

        n_cases = 1000
        full_interval_size = 10000
        n_regions_to_test = 50
        max_intervals = 50

        for case in xrange(n_cases):
            n_intervals = random.randrange(1, max_intervals)
            interval_list = []
            for i in xrange(n_intervals):
                ival_length = random.randrange(full_interval_size/10)
                ival_start = random.randrange(full_interval_size - ival_length)
                ival_end = ival_start + ival_length
                interval_list.append(interval_tree.Interval(ival_start, ival_end))
            
            itree = interval_tree.IntervalTree(interval_list)
            
            test_region_starts = random.sample(range(full_interval_size), n_regions_to_test)
            for test_region_start in test_region_starts:
                test_region_length = random.randrange(full_interval_size - test_region_start)
                test_region_end = test_region_start + test_region_length

                true_overlapping_intervals = []
                for interval in interval_list:
                    if interval.start < test_region_end and test_region_start < interval.stop:
                        true_overlapping_intervals.append(interval)
                
                itree_overlapping_intervals = []
                itree.find_overlapping(test_region_start, test_region_end, itree_overlapping_intervals)
                
                self.assertEqual(len(true_overlapping_intervals), len(itree_overlapping_intervals))

                for o_ival in true_overlapping_intervals:
                    self.assertIn(o_ival, itree_overlapping_intervals)




    def test_boundaries(self):
        """Test that intervals in the IntervalTree are interpreted
        as the usual half-open [start, end) intervals.
        """

        interval_list = []
        interval_list.append(interval_tree.Interval(5, 10))
        interval_list.append(interval_tree.Interval(5, 11))
        interval_list.append(interval_tree.Interval(10, 15))
        interval_list.append(interval_tree.Interval(20, 25))
        
        itree = interval_tree.IntervalTree(interval_list)

        ivals = []
        itree.find_overlapping(25, 26, ivals)
        self.assertEqual(len(ivals), 0)

        ivals = []
        itree.find_overlapping(20, 21, ivals)
        self.assertEqual(len(ivals), 1)
        self.assertEqual(ivals[0].start, 20)
        self.assertEqual(ivals[0].stop, 25)

        ivals = []
        itree.find_overlapping(5, 10, ivals)
        self.assertEqual(len(ivals), 2)
        self.assertEqual(ivals[0].start, 5)
        self.assertEqual(ivals[0].stop, 10)
        self.assertEqual(ivals[1].start, 5)
        self.assertEqual(ivals[1].stop, 11)
        
        ivals = []
        itree.find_overlapping(10, 11, ivals)
        self.assertEqual(len(ivals), 2)
        self.assertEqual(ivals[0].start, 5)
        self.assertEqual(ivals[0].stop, 11)
        self.assertEqual(ivals[1].start, 10)
        self.assertEqual(ivals[1].stop, 15)

if __name__ == '__main__':
    unittest.main()
