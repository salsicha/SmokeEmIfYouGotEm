"""Reject mixed/stale assembly evidence without modifying source artifacts."""
import unittest
from unittest.mock import patch

import prepare_south_fork_scene_assembly as assembly


class RapidRevisionBinding(unittest.TestCase):
    # Independent of the historical assembly's intentionally stale map hash:
    # each check must reach the render/collision/hydraulic identity comparison.
    def test_same_geometry_revision_accepted(self):
        assembly.validate_rapid_geometry_binding({'registered_rapid_sha256': 'a'*64},
            {'source_geometry_sha256': 'a'*64}, {'source_geometry_sha256': 'a'*64})

    def test_mutually_consistent_old_render_and_collision_are_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'Render rapid differs'):
            assembly.validate_rapid_geometry_binding({'registered_rapid_sha256': 'a'*64},
                {'source_geometry_sha256': 'b'*64}, {'source_geometry_sha256': 'b'*64})

    def test_new_render_with_old_collision_proof_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'Collision evidence belongs'):
            assembly.validate_rapid_geometry_binding({'registered_rapid_sha256': 'a'*64},
                {'source_geometry_sha256': 'a'*64}, {'source_geometry_sha256': 'b'*64})


class SceneAssemblyRejections(unittest.TestCase):
    def reject(self, suffix, mutate):
        original = assembly.read

        def changed(path):
            value = original(path)
            if path.as_posix().endswith(suffix):
                mutate(value)
            return value

        with patch.object(assembly, 'read', side_effect=changed), self.assertRaises(AssertionError):
            assembly.prepare(assembly.ROOT/'tmp/south-fork-runtime-atlas-600s-v1-20260912',
                assembly.REPORTS/'south-fork-normal-integration-inventory-v3-20260912.json')

    def test_changed_normal_map_is_not_overwritten(self):
        self.reject('south-fork-normal-integration-inventory-v3-20260912.json',
            lambda value: value['protected_files'].update({next(iter(value['protected_files'])): '0'*64}))

    def test_source_translation_cannot_drift_from_imported_collision(self):
        self.reject('Tiles/manifest.json', lambda value: value['tiles'][0]['actor_translation_cm'].__setitem__(0, 123.))

    def test_mixed_water_datum_rejected(self):
        self.reject('atlas/manifest.json', lambda value: value.update(source_elevation_datum_m=0.))

    def test_other_terrain_atlas_rejected(self):
        self.reject('export_audit.json', lambda value: value.update(source_manifest_sha256='0'*64))

    def test_finish_cannot_exceed_the_captured_route(self):
        self.reject('session_contracts.json', lambda value: value['sessions'][4].update(finish_m=48900.))


if __name__ == '__main__':
    unittest.main()
