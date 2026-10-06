import unittest
import numpy as np
from audit_water_feature_stage_regions import changes, partitions


class RegionTests(unittest.TestCase):
    def test_partitions_cover_each_interval_once(self):
        groups = partitions((6, 7, 8))
        np.testing.assert_array_equal(sum(mask.astype(int) for mask in groups.values()),
                                      np.ones((7, 8, 9), int))
        self.assertTrue(groups['outer_half_cells'][0, 3, 3])
        self.assertTrue(groups['outer_center_adjacent_full_intervals'][1, 3, 3])
        self.assertTrue(groups['interior_intervals'][2, 3, 3])

    def test_boundary_change_does_not_mark_interior(self):
        before = np.ones((6, 7, 8))
        after = before.copy()
        after[0, :, :] = -1
        row = changes(before, after)
        self.assertEqual(row['changed_centers'], 56)
        self.assertEqual(row['changed_non_outermost_centers'], 0)
        self.assertEqual(row['sign_gained_centers'], 56)
        self.assertEqual(row['sign_lost_centers'], 0)
        after[3, 3, 3] = -1
        self.assertEqual(changes(before, after)['changed_non_outermost_centers'], 1)
        self.assertIsNone(changes(before, before)['index_bounds'])
        solid = np.ones_like(before)
        solid[0, :, :] = -1
        self.assertEqual(changes(before, after, solid)['outside_solid_sign_gained_centers'], 1)


if __name__ == '__main__':
    unittest.main()
