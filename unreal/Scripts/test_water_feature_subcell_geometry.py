import unittest
import numpy as np
from water_feature_subcell_geometry import section_mesh, union_area, face_apertures


def rectangle(a, b):
    return np.array([[a[0], a[1]], [b[0], a[1]], [b[0], b[1]], [a[0], b[1]]], float)


def box(a, b):
    v = np.array([[a[0], a[1], a[2]], [b[0], a[1], a[2]], [b[0], b[1], a[2]], [a[0], b[1], a[2]],
                  [a[0], a[1], b[2]], [b[0], a[1], b[2]], [b[0], b[1], b[2]], [a[0], b[1], b[2]]], float)
    t = np.array([[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
                  [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]])
    return v, t


class SubcellGeometryTests(unittest.TestCase):
    def test_rectangle_and_duplicate_union(self):
        p = rectangle([.2, .1], [.8, .6])
        self.assertAlmostEqual(union_area([[p], [p]], [0, 0], [1, 1]), .3, places=14)

    def test_overlapping_groups_not_double_counted(self):
        a = rectangle([0, 0], [.75, .75]); b = rectangle([.25, .25], [1, 1])
        self.assertAlmostEqual(union_area([[a], [b]], [0, 0], [1, 1]), .875, places=14)

    def test_hole_parity(self):
        a = rectangle([0, 0], [1, 1]); b = rectangle([.25, .25], [.75, .75])
        self.assertAlmostEqual(union_area([[a, b]], [0, 0], [1, 1]), .75, places=14)

    def test_oblique_triangle_exact_area(self):
        p = np.array([[0., 0.], [1., 0.], [0., 1.]])
        self.assertAlmostEqual(union_area([[p]], [0, 0], [1, 1]), .5, places=14)
        self.assertAlmostEqual(union_area([[p]], [.25, .25], [.75, .75]), .125, places=14)

    def test_crossing_union_edges(self):
        a = np.array([[0., 0.], [1., 0.], [0., 1.]])
        b = np.array([[0., 1.], [1., 1.], [1., 0.]])
        self.assertAlmostEqual(union_area([[a], [b]], [0, 0], [1, 1]), 1., places=14)

    def test_concave_disconnected_clipping(self):
        # U-shaped polygon; clipping the top half must NOT fill the central gap.
        p = np.array([[0., 0.], [3., 0.], [3., 3.], [2., 3.], [2., 1.], [1., 1.], [1., 3.], [0., 3.]])
        self.assertAlmostEqual(union_area([[p]], [0, 2], [3, 3]), 2., places=14)

    def test_translation_and_ring_orientation(self):
        p = np.array([[0., 0.], [1., 0.], [0., 1.]])
        shift = np.array([27., -51.])
        self.assertAlmostEqual(union_area([[p[::-1]+shift]], shift, shift+1), .5, places=14)

    def test_box_sections_including_coplanar(self):
        v, t = box([0, 0, 0], [1, 1, 1])
        for axis in range(3):
            for plane in [0., .3, 1.]:
                groups, proof = section_mesh(v, t, axis, plane)
                self.assertAlmostEqual(union_area(groups, [0, 0], [1, 1]), 1., places=14)
                self.assertFalse(proof['moved_vertices'])
            groups, _ = section_mesh(v, t, axis, 1.1)
            self.assertEqual(groups, [])

    def test_oblique_box_section(self):
        v, t = box([0, 0, 0], [1, 1, 1]); v[:, 2] += .5*v[:, 0]
        groups, _ = section_mesh(v, t, 2, .25)
        self.assertAlmostEqual(union_area(groups, [0, 0], [1, 1]), .5, places=14)

    def test_open_section_rejected(self):
        v, t = box([0, 0, 0], [1, 1, 1])
        with self.assertRaises(ValueError):
            section_mesh(v, t[:-2], 0, .5)

    def test_adjacent_float_events_have_no_midpoint(self):
        end = np.nextafter(1., 2.)
        p = np.array([[0., 0.], [end, 0.], [1., 1.]])
        self.assertAlmostEqual(union_area([[p]], [0, 0], [2, 2]), end/2, places=15)

    def test_all_faces_and_half_cut(self):
        v, t = box([.5, 0, 0], [2, 2, 2])
        arrays, _ = face_apertures({'box': (v, t)}, (2, 2, 2), [0, 0, 0], 1.)
        self.assertEqual([a.shape for a in arrays], [(3, 2, 2), (2, 3, 2), (2, 2, 3)])
        np.testing.assert_array_equal(arrays[0][0], 1.)
        np.testing.assert_array_equal(arrays[0][1:], 0.)
        np.testing.assert_allclose(arrays[1][0], .5, atol=1e-14)
        np.testing.assert_allclose(arrays[2][0], .5, atol=1e-14)

    def test_translated_closed_faces_are_nonnegative(self):
        v, t = box([-2, -2, -2], [2, 2, 2])
        arrays, _ = face_apertures({'box': (v, t)}, (2, 2, 2), [-.375, -1.1625, -.3374999284744262], .075)
        for area in arrays:
            np.testing.assert_array_equal(area, 0.)


if __name__ == '__main__':
    unittest.main()
