from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp/south-fork-geospatial-deps'))
sys.path.insert(0, str(ROOT / 'physics/scripts'))
import numpy as np
from audit_south_fork_regional_settling import interval_rates, partition_masks, largest_masked_cells
from cook_troublemaker_survey_hydraulics import physical_grid


class RegionalSettlingTests(unittest.TestCase):
    def test_hotspot_coordinates_exclude_dry_cells_and_keep_order(self):
        scores = np.array([[99., 2.], [3., 1.]])
        mask = np.array([[False, True], [True, True]])
        self.assertEqual(largest_masked_cells(scores, mask, 2), [(1, 0), (0, 1)])
        self.assertEqual(largest_masked_cells(scores, np.zeros_like(mask)), [])
        with self.assertRaises(ValueError): largest_masked_cells(scores * np.nan, mask)

    def test_masks_partition_both_grids_at_same_physical_edges(self):
        areas = []
        for cell in (1., .5):
            edges, masks = partition_masks(physical_grid(cell))
            self.assertEqual(edges, [-135.5, -80.5, -25.5, 25.5, 80.5, 135.5])
            self.assertTrue(np.all(np.sum(masks, axis=0) == 1))
            np.testing.assert_array_equal([m.sum() * cell**2 for m in masks], np.diff(edges) * 161)
            areas.append(sum(m.sum() * cell**2 for m in masks))
        self.assertEqual(areas, [271 * 161, 271 * 161])

    def test_interval_rate_keeps_partial_final_interval(self):
        np.testing.assert_array_equal(interval_rates([0, 10, 13], [100, 110, 116]), [1, 2])

    def test_rates_are_additive_across_regions(self):
        values = np.array([[1., 5.], [3., 7.], [4., 9.]])
        np.testing.assert_array_equal(interval_rates([0, 1, 2], values).sum(axis=1),
                                      interval_rates([0, 1, 2], values.sum(axis=1)))

    def test_reject_invalid_times_and_values(self):
        for times, values in (([0, 0], [1, 2]), ([1, 0], [1, 2]), ([0, 1], [1, np.nan]),
                              ([0], [1]), ([0, 1], [1])):
            with self.subTest(times=times):
                with self.assertRaises(ValueError): interval_rates(times, values)


if __name__ == '__main__': unittest.main()
