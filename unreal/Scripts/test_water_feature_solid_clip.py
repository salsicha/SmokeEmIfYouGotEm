"""Native exact-CSG checks; no solver/cache changes or saves."""
from pathlib import Path
import sys
import unittest
import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_water_feature_lab import box
from water_feature_solid_clip import clipped_surface, remove_surface
from audit_water_feature_mesh_contact import topology


def geometry(obj):
    mesh = obj.data
    return ([v.co[:] for v in mesh.vertices], [p.vertices[:] for p in mesh.polygons],
            [list(row) for row in obj.matrix_world])


class SolidClipTests(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.liquid = box('synthetic closed liquid', (0., 0., 0.), (2., 2., 2.))

    def check(self, lower, upper, expected):
        solid = box('shared synthetic solid', lower, upper)
        original = (geometry(self.liquid), geometry(solid))
        evaluated = self.liquid.evaluated_get(bpy.context.evaluated_depsgraph_get())
        derived = clipped_surface(evaluated, [solid])
        try:
            mesh = derived.data
            mesh.calc_loop_triangles()
            vertices = np.array([derived.matrix_world @ v.co for v in mesh.vertices])
            triangles = np.array([t.vertices[:] for t in mesh.loop_triangles])
            self.assertEqual(topology(triangles), dict(boundary_edges=0, nonmanifold_edges=0))
            corners = vertices[triangles]
            volume = np.sum(np.einsum('ij,ij->i', corners[:, 0], np.cross(corners[:, 1], corners[:, 2])))/6
            self.assertAlmostEqual(volume, expected, places=6)
            self.assertEqual((geometry(self.liquid), geometry(solid)), original)
            return vertices.copy()
        finally:
            remove_surface(derived)

    def test_shared_solid_cuts_contact_without_moving_raw_geometry(self):
        vertices = self.check((1., -1., -1.), (3., 3., 3.), 4.)
        self.assertLessEqual(vertices[:, 0].max(), 1.+1e-6)

    def test_disjoint_solid_preserves_volume(self):
        self.check((3., 0., 0.), (4., 2., 2.), 8.)

    def test_overlapping_union_preserves_originals(self):
        solids = [box('shared x solid', (1., -1., -1.), (3., 3., 3.)),
                  box('shared y solid', (-1., 1., -1.), (3., 3., 3.))]
        originals = [geometry(obj) for obj in [self.liquid, *solids]]
        derived = clipped_surface(self.liquid.evaluated_get(bpy.context.evaluated_depsgraph_get()),
                                  solids, union_solids=True)
        try:
            derived.data.calc_loop_triangles()
            vertices = np.array([derived.matrix_world @ v.co for v in derived.data.vertices])
            triangles = np.array([t.vertices[:] for t in derived.data.loop_triangles])
            self.assertEqual(topology(triangles), dict(boundary_edges=0, nonmanifold_edges=0))
            corners = vertices[triangles]
            volume = np.sum(np.einsum('ij,ij->i', corners[:, 0], np.cross(corners[:, 1], corners[:, 2])))/6
            self.assertAlmostEqual(volume, 2., places=6)
            self.assertEqual([geometry(obj) for obj in [self.liquid, *solids]], originals)
        finally:
            remove_surface(derived)

    def test_contact_shader_transfer_does_not_change_geometry(self):
        water = bpy.data.materials.new('Synthetic water boundary')
        stone = bpy.data.materials.new('Synthetic shared solid boundary')
        self.liquid.data.materials.append(water)
        solid = box('Shared shaded solid', (1., -1., -1.), (3., 3., 3.))
        solid.data.materials.append(stone)
        originals = [geometry(obj) for obj in (self.liquid, solid)]
        baseline = clipped_surface(self.liquid.evaluated_get(bpy.context.evaluated_depsgraph_get()),
                                   [solid], union_solids=True)
        shaded = clipped_surface(self.liquid.evaluated_get(bpy.context.evaluated_depsgraph_get()),
                                 [solid], union_solids=True, contact_materials=True)
        try:
            self.assertEqual(geometry(shaded), geometry(baseline))
            self.assertIn(stone, list(shaded.data.materials))
            used = {shaded.data.materials[p.material_index] for p in shaded.data.polygons}
            self.assertIn(stone, used)
            self.assertIn(water, used)
            self.assertEqual([geometry(obj) for obj in (self.liquid, solid)], originals)
            self.assertEqual(list(self.liquid.data.materials), [water])
            self.assertEqual(list(solid.data.materials), [stone])
        finally:
            remove_surface(shaded)
            remove_surface(baseline)


if __name__ == '__main__':
    unittest.main(argv=['native-solid-clip-tests'])
