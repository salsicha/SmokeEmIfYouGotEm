import unittest
import numpy as np
from water_feature_extruded_volume import ExtrudedSolidVolume
from water_feature_phase_faces import PhaseFaces, liquid_face_bounds
from qualify_water_feature_shared_phase_support import half_lattice, ranges


class PhaseFaceTests(unittest.TestCase):
    def test_empty_and_jointly_blocked_faces(self):
        empty = PhaseFaces(ExtrudedSolidVolume([])); self.assertEqual(empty.area(0, .5, [0, 0], [1, 1]), 1.)
        g = ExtrudedSolidVolume([([0, 0, 0], [1, .6, 1]), ([0, .4, 0], [1, 1, 1])])
        self.assertEqual(PhaseFaces(g).area(0, .5, [0, 0], [1, 1]), 0.)

    def test_box_corner_all_axes(self):
        g = ExtrudedSolidVolume([([0, .75, 0], [1, 1, 1]), ([0, 0, -.5], [1, 1, 0])]); f = PhaseFaces(g)
        self.assertEqual(f.area(0, .5, [0, -.5], [1, .5]), .375)
        self.assertEqual(f.area(1, .5, [0, -.5], [1, .5]), .5)
        self.assertEqual(f.area(2, .25, [0, 0], [1, 1]), .75)

    def test_actual_sloped_roof_sections(self):
        g = ExtrudedSolidVolume([], ([0, 1], [0, 1], [0, 0, -1], [1, 1, 1])); f = PhaseFaces(g)
        self.assertEqual(f.area(0, .25, [0, 0], [1, 1]), .75)
        self.assertAlmostEqual(f.area(1, .25, [0, 0], [1, 1]), .5)
        self.assertEqual(f.area(2, .25, [0, 0], [1, 1]), .25)

    def test_roof_box_union_and_partition(self):
        g = ExtrudedSolidVolume([([0, .25, .25], [1, 1, 1])], ([0, 1], [0, 1], [0, 0, -1], [1, 1, 1])); f = PhaseFaces(g)
        whole = f.area(1, .5, [0, 0], [1, 1]); self.assertAlmostEqual(whole, .03125)
        parts = sum(f.area(1, .5, [i*.5, j*.5], [(i+1)*.5, (j+1)*.5]) for i in (0, 1) for j in (0, 1))
        self.assertAlmostEqual(whole, parts)

    def test_small_opening_not_thresholded(self):
        q = np.nextafter(1., 0.); f = PhaseFaces(ExtrudedSolidVolume([([0, 0, 0], [1, q, 1])]))
        self.assertEqual(f.area(0, .5, [0, 0], [1, 1]), 1.-q)

    def test_plane_liquid_bounds_refine(self):
        phi = np.indices((3, 3, 3), dtype=float)[1]-.3; f = PhaseFaces(ExtrudedSolidVolume([])); widths = []
        for depth in (0, 1, 2, 3):
            r = liquid_face_bounds(f, phi, [-.5, -.5, -.5], 1, 0, .5, [0, 0], [1, 1], depth)
            self.assertLessEqual(r['lower_m2'], .3); self.assertGreaterEqual(r['upper_m2'], .3); widths.append(r['width_m2'])
        self.assertTrue(all(b <= a for a, b in zip(widths, widths[1:])))

    def test_false_center_free_surface_actual_open_face_wet(self):
        # The cell center is inside a wall, but all actual open face is liquid.
        phi = np.indices((3, 3, 3), dtype=float)[1]-.35
        f = PhaseFaces(ExtrudedSolidVolume([([0, .2, 0], [2, 2, 2])]))
        r = liquid_face_bounds(f, phi, [-.5, -.5, -.5], 1, 0, .5, [0, 0], [1, 1], 3)
        self.assertAlmostEqual(r['lower_m2'], .2); self.assertAlmostEqual(r['upper_m2'], .2)

    def test_saddle_liquid_not_plane_fit(self):
        ids = np.indices((3, 3, 3), dtype=float); phi = ids[1]*ids[2]-.25
        f = PhaseFaces(ExtrudedSolidVolume([])); true_area = .25*(1-np.log(.25))
        r = liquid_face_bounds(f, phi, [-.5, -.5, -.5], 1, 0, .5, [0, 0], [1, 1], 3)
        self.assertLessEqual(r['lower_m2'], true_area); self.assertGreaterEqual(r['upper_m2'], true_area)

    def test_invalid_face_rejected(self):
        with self.assertRaises(ValueError):
            PhaseFaces(ExtrudedSolidVolume([])).area(0, .5, [0, 0], [1, 0])

    def test_independent_half_lattice_including_outer_halves(self):
        shape = (3, 4, 5); ids = np.indices(shape, dtype=float); phi = ids[0]+2*ids[1]-3*ids[2]
        actual = half_lattice(phi); q = np.indices(actual.shape, dtype=float)/2-.5
        expected = np.clip(q[0], 0, 2)+2*np.clip(q[1], 0, 3)-3*np.clip(q[2], 0, 4)
        np.testing.assert_array_equal(actual, expected)

    def test_n_plus_one_face_range_coverage(self):
        shape = (3, 4, 5); phi = np.arange(np.prod(shape), dtype=float).reshape(shape)
        half = half_lattice(phi); lo, hi = ranges(half, shape)
        self.assertEqual(lo.shape, shape); self.assertTrue(np.all(lo <= hi))
        for axis in range(3):
            dims = list(shape); dims[axis] += 1; lo, hi = ranges(half, tuple(dims), axis)
            self.assertEqual(lo.shape, tuple(dims)); self.assertTrue(np.all(lo <= hi))


if __name__ == '__main__':
    unittest.main()
