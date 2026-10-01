import unittest
import numpy as np
from water_feature_phase_samples import sample_centers


class PhaseSamplesTests(unittest.TestCase):
    def test_affine_field_matches_cell_center_coordinates(self):
        ids = np.indices((5, 6, 7))
        field = 2*ids[0]-3*ids[1]+4*ids[2]+5
        spacing, origin = np.array([.1, .2, .3]), np.array([-2., 3., 4.])
        cells = np.array([[1.25, 2.5, 3.7], [2., 3., 4.]])
        values, valid = sample_centers(field, origin+(cells+.5)*spacing, origin, spacing)
        np.testing.assert_allclose(values, 2*cells[:, 0]-3*cells[:, 1]+4*cells[:, 2]+5)
        self.assertTrue(valid.all())

    def test_outside_points_not_extended_or_clamped(self):
        values, valid = sample_centers(np.ones((3, 3, 3)), [[.1, 1, 1], [1, 1, 1], [4, 1, 1]], [0]*3, [1]*3)
        np.testing.assert_array_equal(valid, [False, True, False])
        self.assertTrue(np.isnan(values[[0, 2]]).all())
        self.assertEqual(values[1], 1.)

    def test_empty_and_invalid_inputs(self):
        values, valid = sample_centers(np.ones((3, 3, 3)), np.empty((0, 3)), [0]*3, [1]*3)
        self.assertEqual(len(values), 0)
        self.assertEqual(len(valid), 0)
        with self.assertRaises(ValueError):
            sample_centers(np.ones((3, 3, 3)), [[float('nan'), 0, 0]], [0]*3, [1]*3)


if __name__ == '__main__':
    unittest.main()
