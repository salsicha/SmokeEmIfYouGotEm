import unittest
from collections import Counter
import numpy as np
from water_feature_polygon import triangulate_polygon


class PolygonTests(unittest.TestCase):
    def check(self, xy, expected_area):
        points = np.array([(x, y, 0.) for x, y in xy])
        triangles = triangulate_polygon(points)
        self.assertEqual(len(triangles), len(points)-2)
        edges = Counter(tuple(sorted(edge)) for a, b, c in triangles for edge in ((a, b), (b, c), (c, a)))
        boundary = {tuple(sorted((i, (i+1) % len(points)))) for i in range(len(points))}
        self.assertEqual({edge for edge, n in edges.items() if n == 1}, boundary)
        corners = points[triangles]
        area = np.linalg.norm(np.cross(corners[:, 1]-corners[:, 0], corners[:, 2]-corners[:, 0]), axis=1)/2
        self.assertTrue(np.all(area > 0))
        self.assertAlmostEqual(float(area.sum()), expected_area, places=10)

    def test_collinear_boundary_not_skipped(self):
        self.check([(0, 0), (.2, 0), (1, 0), (1, 1), (0, 1)], 1.)

    def test_concave_both_windings(self):
        points = [(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)]
        self.check(points, 3.)
        self.check(points[::-1], 3.)

    def test_planar_rotation_and_translation(self):
        points = np.array([(0, 0, 0), (0, .2, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)], float)+1000
        self.assertEqual(len(triangulate_polygon(points)), 3)

    def test_invalid_and_self_touching_rejected(self):
        for points in [[], [(0, 0, 0)]*3, [(0, 0, 0), (1, 0, 0), (float('nan'), 1, 0)],
                       [(0, 0, 0), (1, 1, 0), (0, 1, 0), (1, 0, 0)]]:
            with self.assertRaises(ValueError):
                triangulate_polygon(points)

    def test_native_contact_projection_does_not_collapse_endpoints(self):
        # Exact saved frame192 polygon from polygon-boundaries-v1.json.
        # Endpoint0/8 differ in z only; the old dominant-axis projection
        # erased their separation. No nearby-point merge is permitted.
        points = np.array([
            (-2.25, .7112954258918762, -.9750000238418579),
            (-2.25, -.702656626701355, -.9750000238418579),
            (-2.250000238418579, -.702656626701355, -.9749999046325684),
            (-2.2687501907348633, -.7057584524154663, -.9656249284744263),
            (-2.278190851211548, -.7064032554626465, -.9609046578407288),
            (-2.2875001430511475, -.7099727988243103, -.9562499523162842),
            (-2.2972190380096436, -.7110126614570618, -.9513904452323914),
            (-2.252779006958008, .711070716381073, -.973610520362854),
            (-2.25, .7112954258918762, -.9749999642372131),
        ])
        original = points.copy()
        for coordinates in (points, points[::-1]):
            triangles = triangulate_polygon(coordinates)
            self.assertEqual(len(triangles), 7)
            corners = coordinates[triangles]
            areas = np.linalg.norm(np.cross(corners[:, 1]-corners[:, 0],
                                           corners[:, 2]-corners[:, 0]), axis=1)/2
            self.assertTrue(np.all(areas > 1e-12))
            edges = Counter(tuple(sorted(edge)) for a, b, c in triangles
                            for edge in ((a, b), (b, c), (c, a)))
            boundary = {tuple(sorted((i, (i+1) % 9))) for i in range(9)}
            self.assertEqual({edge for edge, n in edges.items() if n == 1}, boundary)
        np.testing.assert_array_equal(points, original)


if __name__ == '__main__':
    unittest.main()
