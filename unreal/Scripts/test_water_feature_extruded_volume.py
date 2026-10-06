import unittest
import numpy as np
from water_feature_extruded_volume import ExtrudedSolidVolume, liquid_volume_bounds, open_intervals


class ExtrudedVolumeTests(unittest.TestCase):
    def test_empty_box_moments(self):
        v, m = ExtrudedSolidVolume([]).integrate([0, 1, 2], [2, 4, 6])
        self.assertEqual(v, 24.); np.testing.assert_array_equal(m, [24, 60, 96])

    def test_full_and_boundary_contact(self):
        g = ExtrudedSolidVolume([([0, 0, 0], [1, 1, 1])])
        self.assertEqual(g.integrate([0, 0, 0], [1, 1, 1])[0], 0.)
        self.assertEqual(g.integrate([1, 0, 0], [2, 1, 1])[0], 1.)

    def test_overlap_and_joint_coverage(self):
        g = ExtrudedSolidVolume([([0, 0, 0], [.75, 1, 1]), ([.25, 0, 0], [1, 1, 1])])
        self.assertEqual(g.integrate([0, 0, 0], [1, 1, 1])[0], 0.)
        self.assertEqual(open_intervals([(0, .5), (.5, 1)], 0, 1), [])

    def test_represented_tiny_opening_not_discarded(self):
        gap = 1.-np.nextafter(1., 0.)
        g = ExtrudedSolidVolume([([0, 0, 0], [np.nextafter(1., 0.), 1, 1])])
        self.assertEqual(g.integrate([0, 0, 0], [1, 1, 1])[0], gap)

    def test_sloped_roof_volume_and_centroid(self):
        g = ExtrudedSolidVolume([], (np.array([0., 1.]), np.array([0., 1.]), [0, 0, -1], [1, 1, 1]))
        v, m = g.integrate([0, 0, 0], [1, 1, 1])
        self.assertAlmostEqual(v, .5); np.testing.assert_allclose(m/v, [1/3, .5, 2/3], atol=1e-15)

    def test_roof_crosses_top_and_bottom(self):
        g = ExtrudedSolidVolume([], (np.array([0., 1.]), np.array([-.5, 1.5]), [0, 0, -1], [1, 1, 1.5]))
        self.assertAlmostEqual(g.integrate([0, 0, 0], [1, 1, 1])[0], .5)

    def test_box_and_roof_union_additivity(self):
        g = ExtrudedSolidVolume([([.3, .2, .4], [.8, .9, 1.3])],
             (np.array([0., .5, 1.]), np.array([.25, .7, .4]), [0, 0, -1], [1, 1, .7]))
        v, m = g.integrate([0, 0, 0], [1, 1, 1]); parts = []
        for i in (0, 1):
            for j in (0, 1):
                for k in (0, 1):
                    lo = np.array([i, j, k])*.5; parts.append(g.integrate(lo, lo+.5))
        self.assertAlmostEqual(v, sum(p[0] for p in parts), places=14)
        np.testing.assert_allclose(m, sum((p[1] for p in parts)), atol=1e-14)

    def test_constant_cut_channel_dual_volume(self):
        g = ExtrudedSolidVolume([([-1, .25, -1], [2, 2, 2]), ([-1, -1, -1], [2, 2, 0])])
        v, m = g.integrate([0, 0, -.5], [1, 1, .5])
        self.assertEqual(v, .125); np.testing.assert_array_equal(m/v, [.5, .125, .25])

    def test_contains_actual_roof_not_box(self):
        g = ExtrudedSolidVolume([], (np.array([0., 1.]), np.array([0., 1.]), [0, 0, -1], [1, 1, 1]))
        np.testing.assert_array_equal(g.contains([[.25, .5, .5], [.75, .5, .5]]), [False, True])

    def test_liquid_plane_bounds_refine(self):
        phi = np.indices((4, 4, 4), dtype=float)[2]+.5-1.3
        g = ExtrudedSolidVolume([]); widths = []
        for depth in (0, 1, 2, 3):
            r = liquid_volume_bounds(g, phi, [0, 0, 0], 1., [1, 1, 1], [2, 2, 2], depth)
            self.assertLessEqual(r['lower_m3'], .3+1e-14); self.assertGreaterEqual(r['upper_m3'], .3-1e-14)
            widths.append(r['width_m3'])
        self.assertTrue(all(b <= a for a, b in zip(widths, widths[1:])))
        self.assertLess(widths[-1], .07)

    def test_liquid_volume_uses_geometry_not_voxel_count(self):
        phi = np.full((4, 4, 4), -1.); g = ExtrudedSolidVolume([([1, 1, 1], [1.6, 2, 2])])
        r = liquid_volume_bounds(g, phi, [0, 0, 0], 1., [1, 1, 1], [2, 2, 2], 2)
        self.assertAlmostEqual(r['lower_m3'], .4); self.assertEqual(r['lower_m3'], r['upper_m3'])

    def test_multilinear_saddle_liquid_not_plane_fit(self):
        ijk = np.indices((3, 3, 3), dtype=float)
        phi = ijk[0]*ijk[1]-.25
        actual = .25*(1-np.log(.25))
        r = liquid_volume_bounds(ExtrudedSolidVolume([]), phi, [-.5, -.5, -.5], 1., [0, 0, 0], [1, 1, 1], 3)
        self.assertLessEqual(r['lower_m3'], actual); self.assertGreaterEqual(r['upper_m3'], actual)
        self.assertLess(r['width_m3'], .3)

    def test_sloped_solid_liquid_intersection_bounds(self):
        phi = np.indices((3, 3, 3), dtype=float)[2]-.75
        g = ExtrudedSolidVolume([], (np.array([0., 1.]), np.array([0., 1.]), [0, 0, -1], [1, 1, 1]))
        widths = []
        for depth in (1, 2, 3):
            r = liquid_volume_bounds(g, phi, [-.5, -.5, -.5], 1., [0, 0, 0], [1, 1, 1], depth)
            self.assertLessEqual(r['lower_m3'], .28125); self.assertGreaterEqual(r['upper_m3'], .28125)
            widths.append(r['width_m3'])
        self.assertTrue(all(b <= a for a, b in zip(widths, widths[1:])))
        self.assertLess(widths[-1], .2)

    def test_zero_level_set_remains_uncertain(self):
        r = liquid_volume_bounds(ExtrudedSolidVolume([]), np.zeros((3, 3, 3)), [0, 0, 0], 1., [1, 1, 1], [2, 2, 2], 1)
        self.assertEqual(r['lower_m3'], 0.); self.assertEqual(r['upper_m3'], 1.)

    def test_invalid_geometry_and_bound_domain_rejected(self):
        with self.assertRaises(ValueError):
            ExtrudedSolidVolume([([0, 0, 0], [1, 0, 1])])
        with self.assertRaises(ValueError):
            ExtrudedSolidVolume([], ([0, .5, .4], [0, 1, .5], [0, 0, -1], [.4, 1, 1]))
        with self.assertRaises(ValueError):
            liquid_volume_bounds(ExtrudedSolidVolume([]), np.ones((4, 4, 4)), [0, 0, 0], 1., [-1, 0, 0], [1, 1, 1])


if __name__ == '__main__':
    unittest.main()
