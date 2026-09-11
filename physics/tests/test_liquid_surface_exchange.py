import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_liquid_surface_exchange import sample_grid, wet_column_integrals


class SurfaceExchangeTest(unittest.TestCase):
    def test_trilinear_sampling_preserves_affine_xyz_field(self):
        z, y, x = np.meshgrid(np.arange(5)+.5, np.arange(6)+.5, np.arange(7)+.5, indexing='ij')
        values = (2*x+3*y-4*z)[..., None]
        points = np.array([[1.3, 2.1, 3.4], [5.5, 1.9, .8]])
        sampled = sample_grid(values, points, minimum=(0, 0, 0), extent=(7, 6, 5))[:, 0]
        np.testing.assert_allclose(sampled, points@np.array([2, 3, -4]))

    def test_partial_surface_and_bed_with_linear_velocity(self):
        z = np.array([0., 1., 2., 3.])
        sdf = (z-2.3)[:, None]
        velocity = (1+2*z)[:, None]
        depth, flux, top = wet_column_integrals(z, sdf, velocity, np.array([.4]))
        self.assertAlmostEqual(depth[0], 1.9)
        self.assertAlmostEqual(top[0], 2.3)
        self.assertAlmostEqual(flux[0], (2.3+2.3**2)-(.4+.4**2))

    def test_disconnected_intervals_do_not_fill_air_gap(self):
        z = np.arange(5.)
        sdf = np.array([1., -1., 1., -1., 1.])[:, None]
        depth, flux, top = wet_column_integrals(z, sdf, np.ones_like(sdf)*-3, np.array([0.]))
        self.assertEqual(depth[0], 2.)
        self.assertEqual(flux[0], -6.)
        self.assertEqual(top[0], 3.5)

    def test_empty_column_and_invalid_order(self):
        z = np.arange(3.)
        sdf = np.ones((3, 1))
        depth, flux, top = wet_column_integrals(z, sdf, sdf, np.array([0.]))
        self.assertEqual(depth[0], 0.)
        self.assertEqual(flux[0], 0.)
        self.assertFalse(np.isfinite(top[0]))
        with self.assertRaises(ValueError):
            wet_column_integrals(z[::-1], sdf, sdf, np.array([0.]))


if __name__ == '__main__':
    unittest.main()
