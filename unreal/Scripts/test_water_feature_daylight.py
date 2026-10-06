from pathlib import Path
import sys
import unittest
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_daylight import daylight_study


class DaylightTests(unittest.TestCase):
    def test_light_only_change_preserves_geometry_material_and_exposure(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        for name in ('Key', 'Rim'):
            data = bpy.data.lights.new(name, 'AREA')
            lamp = bpy.data.objects.new(name, data)
            bpy.context.collection.objects.link(lamp)
        bpy.ops.mesh.primitive_cube_add()
        water = bpy.context.object
        mat = bpy.data.materials.new('Synthetic water')
        mat.use_nodes = True
        water.data.materials.append(mat)
        shader = mat.node_tree.nodes['Principled BSDF']
        before = ([v.co[:] for v in water.data.vertices], shader.inputs['IOR'].default_value,
                  shader.inputs['Base Color'].default_value[:], bpy.context.scene.view_settings.exposure,
                  bpy.context.scene.gravity[:], bpy.context.scene.render.fps)
        report = daylight_study(bpy.context.scene)
        after = ([v.co[:] for v in water.data.vertices], shader.inputs['IOR'].default_value,
                 shader.inputs['Base Color'].default_value[:], bpy.context.scene.view_settings.exposure,
                 bpy.context.scene.gravity[:], bpy.context.scene.render.fps)
        self.assertEqual(before, after)
        self.assertEqual(report['model'], 'MULTIPLE_SCATTERING')
        self.assertEqual(report['parameters']['sun_intensity'], 1.)
        self.assertEqual(report['world_strength'], 1.)
        self.assertFalse(report['measured_lighting'])
        self.assertTrue(all(bpy.data.objects[name].hide_render for name in ('Key', 'Rim')))


if __name__ == '__main__':
    unittest.main(argv=['native-daylight-tests'])
