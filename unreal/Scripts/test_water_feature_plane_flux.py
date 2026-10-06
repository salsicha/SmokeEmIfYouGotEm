"""Analytic face-quadrature checks; no hydraulic acceptance claim."""
import unittest
import numpy as np
from water_feature_plane_flux import partial_face_flux


class FaceFluxTests(unittest.TestCase):
    def test_full_anisotropic_domain(self):
        phi = -np.ones((3, 4))
        row = partial_face_flux(phi, -phi, np.full_like(phi, 2), (.2, .3))
        self.assertAlmostEqual(row['liquid_area_m2'], .6*1.2)
        self.assertAlmostEqual(row['signed_downward_flux_m3s'], 2*.6*1.2)
        self.assertAlmostEqual(row['covered_domain_area_m2'], .6*1.2)

    def test_liquid_obstacle_partial_intersection(self):
        x, y = np.meshgrid((np.arange(5)+.5)*.2, (np.arange(6)+.5)*.3, indexing='ij')
        row = partial_face_flux(x-.6, y-.45, np.full_like(x, 2), (.2, .3), 8)
        self.assertAlmostEqual(row['liquid_area_m2'], .6*(1.8-.45))
        self.assertAlmostEqual(row['signed_downward_flux_m3s'], 2*.6*(1.8-.45))

    def test_bidirectional_linear_velocity(self):
        phi = -np.ones((2, 3))
        velocity = np.array([[2., 2., 2.], [-1., -1., -1.]])
        row = partial_face_flux(phi, -phi, velocity, (1, 1), 32)
        self.assertAlmostEqual(row['signed_downward_flux_m3s'], 3)
        self.assertLess(abs(row['downward_only_flux_m3s']-5), .003)
        self.assertLess(abs(row['upward_only_flux_m3s']-2), .003)

    def test_empty_and_invalid(self):
        a = np.ones((3, 4))
        row = partial_face_flux(a, a, a, (1, 1))
        self.assertEqual(row['signed_downward_flux_m3s'], 0)
        self.assertIsNone(row['mean_downward_velocity_mps'])
        with self.assertRaises(ValueError):
            partial_face_flux(a, a, a, (0, 1))
        a[0, 0] = np.nan
        with self.assertRaises(ValueError):
            partial_face_flux(a, a, a, (1, 1))


if __name__ == '__main__':
    unittest.main()
