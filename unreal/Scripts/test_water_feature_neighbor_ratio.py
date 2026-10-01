import unittest
import numpy as np
from water_feature_neighbor_ratio import occupancy_ratio, phase_bits, complete_omitted_fluid_cells


class NeighborRatioTests(unittest.TestCase):
    def test_planar_interface_is_a_cell_band_not_a_surface_constraint(self):
        flags = np.full((16, 16, 16), 4, np.int32)
        flags[:, :, :8] = 1
        ratio, _, active = occupancy_ratio(flags, 2, 1, 2)
        self.assertAlmostEqual(float(ratio[8, 8, 7]), 74/124)
        self.assertAlmostEqual(float(ratio[8, 8, 6]), 99/124)
        np.testing.assert_array_equal(phase_bits(ratio[8, 8, [6, 7, 8]]), [4, 8, 2])
        self.assertTrue(active[8, 8, 7])
        self.assertFalse(active[8, 8, 8])

    def test_obstacles_excluded_not_counted_as_air(self):
        flags = np.full((9, 9, 9), 1, np.int32)
        flags[5, 4, 4] = 2
        ratio, total, _ = occupancy_ratio(flags, 1, 1, 2)
        self.assertEqual(total[4, 4, 4], 25)
        self.assertEqual(ratio[4, 4, 4], 1)

    def test_no_wrap_or_unsupported_kernel_centres(self):
        flags = np.ones((9, 9, 9), np.int32)
        ratio, total, active = occupancy_ratio(flags, 2, 1, 2)
        self.assertEqual(total[2, 2, 2], 63)
        self.assertEqual(ratio[2, 2, 2], 1)
        self.assertFalse(active[1, 4, 4])
        self.assertEqual(ratio[1, 4, 4], 0)

    def test_strict_thresholds_and_invalid_inputs(self):
        np.testing.assert_array_equal(phase_bits([.3999, .4, .77, .7701]), [2, 8, 8, 4])
        with self.assertRaises(ValueError):
            occupancy_ratio(np.ones((5, 5, 5)), 1, 1, 2)
        with self.assertRaises(ValueError):
            phase_bits([float('nan')])

    def test_completion_changes_only_omitted_fluid_centres(self):
        flags = np.ones((9, 9, 9), np.int32)
        flags[[0, -1], :, :] = 2
        flags[:, [0, -1], :] = 2
        flags[:, :, [0, -1]] = 2
        ratio, _, _ = occupancy_ratio(flags, 2, 1, 2)
        completed, changed = complete_omitted_fluid_cells(flags, ratio, 2, 1, 2)
        self.assertEqual(ratio[1, 4, 4], 0)
        self.assertEqual(completed[1, 4, 4], 1)
        self.assertEqual(completed[4, 4, 4], 1)
        self.assertFalse(changed[0, 4, 4])
        np.testing.assert_array_equal(completed[~changed], ratio[~changed])

    def test_disagreement_is_not_silently_repaired(self):
        flags = np.ones((9, 9, 9), np.int32)
        ratio, _, _ = occupancy_ratio(flags, 2, 1, 2)
        ratio[4, 4, 4] = .5
        with self.assertRaises(AssertionError):
            complete_omitted_fluid_cells(flags, ratio, 2, 1, 2)


if __name__ == '__main__':
    unittest.main()
