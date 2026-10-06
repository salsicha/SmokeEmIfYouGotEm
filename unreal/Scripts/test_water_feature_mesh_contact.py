"""Run inside Blender: native BVH parity including a concave stepped solid."""
from pathlib import Path
import sys
import unittest
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_water_feature_mesh_contact import interior_distance, topology
from liquid_review_geometry import height_volume_geometry


class ContactTests(unittest.TestCase):
    def tree(self, heights):
        vertices, faces = height_volume_geometry([heights, heights],
                                                 [[-1.]*len(heights)]*2, 1., 2.)
        return BVHTree.FromPolygons(vertices, faces)

    def test_box_inside_outside_and_contact(self):
        tree = self.tree([1., 1.])
        self.assertAlmostEqual(interior_distance(tree, (.5, 1., 0.)), .5)
        self.assertEqual(interior_distance(tree, (2., 1., 0.)), 0.)
        self.assertEqual(interior_distance(tree, (.5, 1., 1.)), 0.)

    def test_concave_height_volume(self):
        tree = self.tree([1., 0., 1.])
        self.assertGreater(interior_distance(tree, (1., 1., -.5)), 0.)
        self.assertEqual(interior_distance(tree, (1., 1., .5)), 0.)
        self.assertGreater(interior_distance(tree, (.2, 1., .5)), 0.)

    def test_open_and_closed_topology(self):
        self.assertEqual(topology([(0, 1, 2)])['boundary_edges'], 3)
        self.assertEqual(topology([(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)]),
                         dict(boundary_edges=0, nonmanifold_edges=0))


if __name__ == '__main__':
    unittest.main(argv=['native-mesh-contact-tests'])
