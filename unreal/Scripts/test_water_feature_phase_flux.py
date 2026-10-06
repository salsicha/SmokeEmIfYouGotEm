import unittest
import numpy as np
from water_feature_phase_flux import cartesian_flux_bounds


class PhaseFluxTests(unittest.TestCase):
    def fixture(self):
        shape = (3, 3, 3); areas = []
        for a in range(3):
            dims = list(shape); dims[a] += 1; areas.append(np.zeros(dims))
        return np.zeros((*shape, 3)), areas

    def test_shared_face_equal_opposite_and_boundary(self):
        v, a = self.fixture(); a[0][1, 1, 1] = .25; v[1, 1, 1, 0] = 2.
        lo, hi, boundary = cartesian_flux_bounds(v, a, a)
        self.assertEqual(lo[0, 1, 1], .5); self.assertEqual(lo[1, 1, 1], -.5)
        np.testing.assert_array_equal(lo, hi); self.assertEqual(float(lo.sum()), 0.); self.assertEqual(boundary, [0., 0.])

    def test_negative_velocity_interval_orientation(self):
        v, a = self.fixture(); upper = [x.copy() for x in a]; a[0][1, 1, 1] = .1; upper[0][1, 1, 1] = .2; v[1, 1, 1, 0] = -3.
        lo, hi, _ = cartesian_flux_bounds(v, a, upper)
        self.assertAlmostEqual(lo[0, 1, 1], -.6); self.assertAlmostEqual(hi[0, 1, 1], -.3)
        self.assertAlmostEqual(lo[1, 1, 1], .3); self.assertAlmostEqual(hi[1, 1, 1], .6)

    def test_whole_flux_boundary_not_sum_of_uncorrelated_bounds(self):
        v, a = self.fixture(); upper = [x.copy() for x in a]; upper[0][1, 1, 1] = .2; v[1, 1, 1, 0] = 2.
        lo, hi, boundary = cartesian_flux_bounds(v, a, upper)
        self.assertLess(lo.sum(), 0.); self.assertGreater(hi.sum(), 0.)
        self.assertEqual(boundary, [0., 0.])

    def test_missing_outer_velocity_rejected(self):
        v, a = self.fixture(); a[0][-1, 1, 1] = .1
        with self.assertRaises(ValueError):
            cartesian_flux_bounds(v, a, a)

    def test_nonfinite_and_wrong_area_shape_rejected(self):
        v, a = self.fixture(); v[0, 0, 0, 0] = np.nan
        with self.assertRaises(ValueError):
            cartesian_flux_bounds(v, a, a)
        v[:] = 0.; a[1] = np.zeros((3, 3, 3))
        with self.assertRaises(ValueError):
            cartesian_flux_bounds(v, a, a)


if __name__ == '__main__':
    unittest.main()
