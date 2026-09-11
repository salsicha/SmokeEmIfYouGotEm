import sys
from pathlib import Path
import unittest
import json
import hashlib
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build_south_fork_liquid_initial_state import apportion_columns, resolved_wet_depth
from south_fork_registered_mesh import RegisteredMeshSampler


class LiquidInitialStateTest(unittest.TestCase):
    def test_dry_terrain_elevation_is_not_a_water_surface(self):
        depth=resolved_wet_depth([14.,7.,7.],[13.8,6.,8.],[0.,.01,1.])
        np.testing.assert_array_equal(depth,[0.,1.,0.])
        # No arbitrary wet threshold: even small positive native depth remains
        # eligible for exact-bed intersection and explicit volume quantization.
        np.testing.assert_array_equal(resolved_wet_depth([2.],[1.],[1e-12]),[1.])
        for native in ([-1.],[float('nan')]):
            with self.assertRaises(ValueError):resolved_wet_depth([2.],[1.],native)
        with self.assertRaises(ValueError):resolved_wet_depth([1,2],[1],[1])

    def test_equal_volume_quantization_and_dry_columns(self):
        volumes = np.array([0, .01, .22, .3, .55, 1.92])
        counts = apportion_columns(volumes, .1)
        self.assertEqual(counts[0], 0)
        self.assertLessEqual(abs(counts.sum()*.1-volumes.sum()), .05)
        self.assertTrue(np.all(abs(counts*.1-volumes) < .1))
        np.testing.assert_array_equal(counts, apportion_columns(volumes, .1))

    def test_zero_volume_is_empty(self):
        np.testing.assert_array_equal(apportion_columns(np.zeros(6), .1), np.zeros(6))

    def test_rejects_invalid_volumes(self):
        for values, size in [([1, -1], .1), ([np.nan], .1), ([1], 0), ([1], np.inf)]:
            with self.assertRaises(ValueError):
                apportion_columns(values, size)

    def test_generated_seed_table_stays_above_registered_triangles(self):
        root = Path(__file__).resolve().parents[2]
        directory = root/'unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908'
        profile = json.loads((directory/'hydraulic_initial_state.json').read_text())
        window = json.loads((directory/'manifest.json').read_text())
        geometry = json.loads((root/window['source_geometry_manifest']).read_text())
        mesh_path = root/geometry['mesh_path']
        self.assertEqual(hashlib.sha256(mesh_path.read_bytes()).hexdigest(), profile['source_geometry_sha256'])
        self.assertEqual(hashlib.sha256((directory/'native_source_profile.json').read_bytes()).hexdigest(), profile['native_source_profile_sha256'])
        positions = np.array(profile['positions_world_cm'])/100
        velocities = np.array(profile['velocities_world_cm_per_s'])
        self.assertEqual(positions.shape, velocities.shape)
        self.assertEqual(len(positions), profile['particle_count'])
        bed = RegisteredMeshSampler(np.load(mesh_path)).sample(positions[:, 0], positions[:, 1])
        self.assertTrue(np.all(positions[:, 2] > bed))
        self.assertTrue(np.isfinite(velocities).all())
        self.assertTrue(np.all(velocities[:, 2] == 0))
        self.assertLessEqual(abs(profile['volume_quantization_error_m3']), profile['nominal_particle_volume_m3']/2)
        self.assertFalse(profile['engine_particle_volume_calibrated'])


if __name__ == '__main__':
    unittest.main()
