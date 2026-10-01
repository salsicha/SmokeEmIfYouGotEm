import unittest
import numpy as np
from water_feature_grid_alignment import aligned_domain


class AlignmentTests(unittest.TestCase):
    def test_measured_eddy_allocation_and_center_preserved(self):
        result = aligned_domain((0, -.8, -.1), (6, .8, 2.8), 80)
        self.assertEqual(result['expected_grid_cells'], [80, 21, 39])
        np.testing.assert_allclose(result['dimensions_m'], (6, 1.575, 2.925))
        np.testing.assert_allclose(result['center_m'], (3, 0, 1.35))
        np.testing.assert_allclose(result['lower_m'], (0, -.7875, -.1125))
        np.testing.assert_allclose(result['upper_m'], (6, .7875, 2.8125))

    def test_froth_allocation_and_isotropic_mapping(self):
        result = aligned_domain((0, -.8, -.1), (2, .8, 2.8), 96)
        self.assertEqual(result['expected_grid_cells'], [66, 53, 96])
        spacing = np.array(result['dimensions_m'])/result['expected_grid_cells']
        np.testing.assert_allclose(spacing, np.full(3, 2.9/96))

    def test_idempotence_bounds_and_invalid_inputs(self):
        result = aligned_domain((0, -.8, -.1), (6, .8, 2.8), 80)
        repeated = aligned_domain(result['lower_m'], result['upper_m'], 80)
        np.testing.assert_allclose(repeated['dimensions_m'], result['dimensions_m'])
        original = np.array((6, 1.6, 2.9))
        self.assertTrue((np.abs(np.array(result['dimensions_m'])-original) <= result['isotropic_cell_m']/2+1e-12).all())
        for lo, hi, resolution in [((0, 0, 0), (1, 1, 1), 2),
                ((0, 0, 0), (1, -1, 1), 80), ((0, 0, 0), (1, 1, float('nan')), 80),
                ((0, 0, 0), (10, .01, 1), 80)]:
            with self.assertRaises(ValueError):
                aligned_domain(lo, hi, resolution)


if __name__ == '__main__':
    unittest.main()
