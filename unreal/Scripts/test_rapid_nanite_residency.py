"""Portable checks for the native geometry equality witness, not Nanite rendering."""
import copy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class ResidencyGeometryHashTest(unittest.TestCase):
    def setUp(self):
        point = lambda x, y, z: SimpleNamespace(x=x, y=y, z=z)
        self.data = [[point(0., 0., 0.), point(1., 0., 0.), point(0., 1., 0.)],
            [0, 1, 2], [point(0., 0., 1.) for _ in range(3)],
            [point(0., 0., 0.), point(1., 0., 0.), point(0., 1., 0.)], []]
        stub = SimpleNamespace(ProceduralMeshLibrary=SimpleNamespace(
            get_section_from_static_mesh=lambda *args: self.data))
        path = Path(__file__).with_name('replay_legacy_survey_nanite_residency_trial.py')
        spec = importlib.util.spec_from_file_location('residency_hash_test_subject', path)
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'unreal': stub}):
            spec.loader.exec_module(self.module)
        self.mesh = SimpleNamespace(get_num_lods=lambda: 1, get_num_sections=lambda lod: 1)

    def test_same_native_streams_are_exact(self):
        before = self.module.native_geometry_hashes(self.mesh)
        self.data = copy.deepcopy(self.data)
        self.assertEqual(before, self.module.native_geometry_hashes(self.mesh))
        self.assertEqual(before[0]['triangles'], 1)
        self.assertEqual(before[0]['vertices'], 3)

    def test_geometry_winding_normal_and_uv_changes_are_detected(self):
        original = copy.deepcopy(self.data)
        before = self.module.native_geometry_hashes(self.mesh)
        for field in ('position', 'winding', 'normal', 'uv'):
            with self.subTest(field=field):
                self.data = copy.deepcopy(original)
                if field == 'winding':
                    self.data[1] = [0, 2, 1]
                else:
                    stream = {'position': 0, 'normal': 2, 'uv': 3}[field]
                    self.data[stream][0].x += 1e-12
                self.assertNotEqual(before, self.module.native_geometry_hashes(self.mesh))

    def test_missing_native_geometry_is_not_equality(self):
        self.data[1] = []
        with self.assertRaises(AssertionError):
            self.module.native_geometry_hashes(self.mesh)


if __name__ == '__main__':
    unittest.main()
