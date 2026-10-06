from pathlib import Path
import sys
import unittest
import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_triangulation import triangulate_extraction


class TriangulationTests(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)

    def polygon(self, vertices):
        mesh = bpy.data.meshes.new('Synthetic extraction polygon')
        mesh.from_pydata(vertices, [], [tuple(range(len(vertices)))])
        obj = bpy.data.objects.new('Synthetic extraction', mesh)
        bpy.context.collection.objects.link(obj)
        return obj

    def test_exact_duplicate_edge_only(self):
        obj = self.polygon([(0, 0, 0), (.5, 0, 0), (.5, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)])
        before = {tuple(v.co) for v in obj.data.vertices}
        report = triangulate_extraction(obj, constrained=True)
        self.assertEqual(report['exact_zero_edge_vertices_welded'], 1)
        self.assertEqual({tuple(v.co) for v in obj.data.vertices}, before)
        obj.data.calc_loop_triangles()
        p = np.array([v.co[:] for v in obj.data.vertices], dtype=float)
        q = p[np.array([t.vertices[:] for t in obj.data.loop_triangles])]
        self.assertTrue(np.all(np.linalg.norm(np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0]), axis=1) > 0))

    def test_nearby_distinct_edge_not_welded(self):
        obj = self.polygon([(0, 0, 0), (.5, 0, 0), (.50000006, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)])
        before = {tuple(v.co) for v in obj.data.vertices}
        report = triangulate_extraction(obj, constrained=True)
        self.assertEqual(report['exact_zero_edge_vertices_welded'], 0)
        self.assertEqual({tuple(v.co) for v in obj.data.vertices}, before)

    def test_unresolved_polygon_rejected_without_source_change(self):
        obj = self.polygon([(0, 0, 0), (1, 1, 0), (0, 1, 0), (1, 0, 0)])
        before = ([v.co[:] for v in obj.data.vertices], [p.vertices[:] for p in obj.data.polygons])
        with self.assertRaises(ValueError):
            triangulate_extraction(obj, constrained=True)
        self.assertEqual(([v.co[:] for v in obj.data.vertices], [p.vertices[:] for p in obj.data.polygons]), before)


if __name__ == '__main__':
    unittest.main(argv=['native-triangulation-tests'])
