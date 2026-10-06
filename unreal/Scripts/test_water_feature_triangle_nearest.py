import unittest
import numpy as np
import test_water_feature_mesh_interface as fixtures
from water_feature_mesh_interface import brute_nearest, closest_triangle
from water_feature_triangle_nearest import TriangleNearest


class TriangleNearestTests(unittest.TestCase):
    def test_cube_matches_independent_all_triangle_distances(self):
        vertices, triangles = fixtures.cube()
        nearest = TriangleNearest(vertices, triangles)
        queries = np.random.default_rng(940).uniform(-3, 3, (80, 3))
        for p in queries:
            q, face = nearest(p)
            expected, expected_face = brute_nearest(vertices, triangles, p)
            np.testing.assert_allclose(q, expected, atol=1e-13, rtol=0)
            self.assertEqual(face, expected_face)

    def test_captured_thin_triangle_is_not_omitted(self):
        # Unchanged captured triangle17078, frame192. Blender's float BVH
        # omitted it even from the padded candidate set; actual distance is0.
        vertices = np.array([[.9937558174133301, .39375001192092896, .46875],
                             [.9937500953674316, .4312499761581421, .4682307243347168],
                             [.9937500953674316, .39400482177734375, .46875]])
        p = np.array([.9937521765512243, .4039704384100914, .46860976625479833])
        nearest = TriangleNearest(vertices, np.array([[0, 1, 2]], dtype=np.int64))
        q, face = nearest(p)
        self.assertEqual(face, 0)
        self.assertLess(np.linalg.norm(p-q), 1e-14)
        normal = np.cross(vertices[1]-vertices[0], vertices[2]-vertices[0])
        normal /= np.linalg.norm(normal)
        for distance in (-.0001, .0001):
            offset = p+distance*normal
            result, _ = nearest(offset)
            np.testing.assert_allclose(result, p, atol=1e-14, rtol=0)
            self.assertAlmostEqual(np.linalg.norm(offset-result), abs(distance), delta=1e-14)

    def test_box_seed_is_not_assumed_to_be_nearest_triangle(self):
        # The first triangle's box contains p but the triangle does not.
        vertices = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                             [.8, .8, .01], [.95, .8, .01], [.8, .95, .01]])
        triangles = np.array([[0, 1, 2], [3, 4, 5]], np.int64)
        p = np.array([.85, .85, 0.])
        q, face = TriangleNearest(vertices, triangles)(p)
        self.assertEqual(face, 1)
        np.testing.assert_allclose(q, [.85, .85, .01], atol=1e-14)

    def test_duplicate_ties_and_extreme_aspect_ratio(self):
        vertices = np.array([[0., 0., 0.], [1., 0., 0.], [.5, 1e-10, 0.]])
        triangles = np.array([[0, 1, 2], [0, 1, 2]], np.int64)
        p = np.array([.5, 5e-11, .02])
        q, face = TriangleNearest(vertices, triangles)(p)
        self.assertEqual(face, 0)
        np.testing.assert_allclose(q, [.5, 5e-11, 0.], atol=1e-14)

    def test_invalid_inputs_fail_and_original_geometry_is_unchanged(self):
        vertices, triangles = fixtures.cube()
        v_before, t_before = vertices.copy(), triangles.copy()
        nearest = TriangleNearest(vertices, triangles)
        for query in ([np.nan, 0, 0], [0, 0], [0, np.inf, 0]):
            with self.assertRaises(ValueError):
                nearest(query)
        for points, ids in [(vertices, triangles.astype(float)),
                            (vertices, np.array([[0, 0, 1]])),
                            (vertices, np.array([[-1, 1, 2]]))]:
            with self.assertRaises(ValueError):
                TriangleNearest(points, ids)
        nearest([.7, .23, 1.])
        np.testing.assert_array_equal(vertices, v_before)
        np.testing.assert_array_equal(triangles, t_before)
        self.assertFalse(nearest.xyz.flags.writeable)


if __name__ == '__main__':
    unittest.main()
