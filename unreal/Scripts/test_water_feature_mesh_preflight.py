import unittest
from water_feature_mesh_preflight import validate_completed_data_settings


class MeshPreflightTests(unittest.TestCase):
    def setUp(self):
        self.before = dict(cache_frame_pause_data=0, has_cache_baked_data=False,
                           has_cache_baked_any=False, has_cache_baked_mesh=False,
                           resolution_max=80, mesh_particle_radius=2., flip_ratio=.95)
        self.after = dict(self.before, cache_frame_pause_data=288,
                          has_cache_baked_data=True, has_cache_baked_any=True)

    def test_exact_data_completion_only(self):
        transitions = validate_completed_data_settings(self.before, self.after, 288)
        self.assertEqual(len(transitions), 3)
        self.assertEqual(self.before['cache_frame_pause_data'], 0)

    def test_physical_changes_and_partial_data_rejected(self):
        for key, value in [('resolution_max', 96), ('mesh_particle_radius', 1.8),
                           ('flip_ratio', .9), ('has_cache_baked_mesh', True),
                           ('cache_frame_pause_data', 287), ('has_cache_baked_data', False)]:
            with self.assertRaises(ValueError):
                validate_completed_data_settings(self.before, dict(self.after, **{key: value}), 288)

    def test_missing_added_and_nonpristine_keys_rejected(self):
        for before, after in [(dict(self.before, has_cache_baked_data=True), self.after),
                              (self.before, dict(self.after, extra_flag=True)),
                              (self.before, {k: v for k, v in self.after.items() if k != 'flip_ratio'})]:
            with self.assertRaises(ValueError):
                validate_completed_data_settings(before, after, 288)


if __name__ == '__main__':
    unittest.main()
