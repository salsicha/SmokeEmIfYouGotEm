"""The installer must preserve all retained source transforms, not regenerate them."""
import copy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class CanopyExclusionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        helper = types.ModuleType('install_futaleufu_continuous_canopy')
        helper.ROOT = Path('D:/repos/SmokeEmIfYouGotEm')
        helper.LEVEL = 'test'
        helper.sha = None
        terrain = types.ModuleType('update_futaleufu_native_buffers')
        terrain.snapshot = terrain.write = None
        spec = importlib.util.spec_from_file_location('canopy_target',
            Path(__file__).resolve().parents[1]/'update_futaleufu_buffer_canopy.py')
        cls.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'unreal': types.ModuleType('unreal'), helper.__name__: helper, terrain.__name__: terrain}):
            spec.loader.exec_module(cls.module)

    def setUp(self):
        self.row = dict(mesh=0, location_cm=[1, 2, 3], scale_xyz=[1, 1, 1], yaw_deg=30,
                        ground_cm=3, source_water_clearance_m=20)
        self.old = dict(chunks=[dict(instances=[self.row]*251317)], meshes=[dict(asset='mesh')])
        retained = dict(self.row, source_water_clearance_m=21)
        self.new = dict(chunks=[dict(instances=[retained]*251275)], hydraulic_buffer_update=dict(
            excluded_instances=[dict(parent_flat_index=i) for i in range(42)]))

    def test_clearance_metadata_only_changes_are_permitted(self):
        result = self.module.exclusion_contract(self.old, self.new)
        self.assertEqual(42, len(result['remove']))
        self.assertEqual(251275, result['retained_instances'])

    def test_shifted_retained_instance_is_rejected(self):
        self.new['chunks'][0]['instances'][0] = dict(self.row, location_cm=[1, 2, 4])
        with self.assertRaisesRegex(RuntimeError, 'Retained source transform'):
            self.module.exclusion_contract(self.old, self.new)

    def test_duplicate_exclusion_is_rejected(self):
        self.new['hydraulic_buffer_update']['excluded_instances'][1]['parent_flat_index'] = 0
        with self.assertRaisesRegex(RuntimeError, 'exactly 42'):
            self.module.exclusion_contract(self.old, self.new)

    def test_incomplete_retained_set_is_rejected(self):
        self.new['chunks'][0]['instances'].pop()
        with self.assertRaisesRegex(RuntimeError, 'Complete original/new canopy'):
            self.module.exclusion_contract(self.old, self.new)

    def actor(self, name):
        return types.SimpleNamespace(get_package=lambda: types.SimpleNamespace(get_name=lambda: name))

    def test_unrelated_initial_editor_residency_is_not_selected(self):
        targets = [self.actor('/target1'), self.actor('/target2'), self.actor('/target3')]
        initial = [self.actor('/initial%d' % i) for i in range(4)]
        actual = self.module.select_requested_actors(initial+targets, ['/target1', '/target2', '/target3'])
        self.assertEqual(targets, actual)
        self.assertEqual(3, len(actual))

    def test_same_count_wrong_package_does_not_replace_missing_target(self):
        with self.assertRaisesRegex(RuntimeError, 'Incomplete requested foliage residency'):
            self.module.select_requested_actors([self.actor('/target1'), self.actor('/unrelated')],
                                                ['/target1', '/target2'])

    def test_duplicate_or_empty_requests_refuse(self):
        for requested in ([], ['/target1', '/target1']):
            with self.subTest(requested=requested), self.assertRaisesRegex(RuntimeError, 'Nonempty unique'):
                self.module.select_requested_actors([self.actor('/target1')], requested)

    def test_duplicate_resident_target_refuses(self):
        with self.assertRaisesRegex(RuntimeError, 'Incomplete requested foliage residency'):
            self.module.select_requested_actors([self.actor('/target1'), self.actor('/target1')], ['/target1'])


if __name__ == '__main__':
    unittest.main()
