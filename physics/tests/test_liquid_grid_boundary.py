import sys
from pathlib import Path
import unittest
import json
import hashlib
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build_south_fork_liquid_grid_boundary import remap_flux, remap_wet_flux, vector_boundary_velocity
from analyze_liquid_vector_boundary import expected_inflow, audit as audit_vector_boundary


class LiquidGridBoundaryTest(unittest.TestCase):
    def test_full_velocity_keeps_native_tangent_and_discrete_normal(self):
        momentum = np.array([[6., -4.], [4., 2.]])
        depth = np.array([2., 1.])
        speed = np.array([1., -3.])
        for face in range(4):
            velocity = vector_boundary_velocity(momentum, depth, speed, face)
            axis, sign = (0, 1) if face == 0 else (0, -1) if face == 1 else (1, 1) if face == 2 else (1, -1)
            np.testing.assert_allclose(sign*velocity[:, axis], speed)
            np.testing.assert_allclose(velocity[:, 1-axis], (momentum/depth[:, None])[:, 1-axis])
            np.testing.assert_array_equal(velocity[:, 2], 0)

    def test_vector_boundary_rejects_invalid_native_momentum(self):
        with self.assertRaises(ValueError):
            vector_boundary_velocity([[1, 2]], [0], [1], 0)
        with self.assertRaises(ValueError):
            vector_boundary_velocity([[1, 2]], [1], [1], 4)
        with self.assertRaises(ValueError):
            vector_boundary_velocity([[float('nan'), 2]], [1], [1], 0)
        np.testing.assert_array_equal(vector_boundary_velocity([[0, 0]], [0], [0], 0), [[0, 0, 0]])

    def test_uniform_overlap_conserves_signed_flux(self):
        for count in (3, 16, 64):
            actual = remap_flux([3., -2., .5, -1.], count)
            self.assertAlmostEqual(actual.sum(), .5, places=12)

    def test_wet_overlap_does_not_inject_dry_columns(self):
        actual = remap_wet_flux([3., -2.], [0., 2., 3., 0.])
        np.testing.assert_allclose(actual, [0., 3., -2., 0.])
        with self.assertRaises(ValueError):
            remap_wet_flux([3., -2.], [0., 0., 3., 0.])

    def test_unresolved_noise_is_opt_in(self):
        with self.assertRaises(ValueError):
            remap_wet_flux([1e-8, 1.], [0., 1.])
        np.testing.assert_allclose(remap_wet_flux([1e-8, 1.], [0., 1.], 1e-7), [0., 1.])

    def test_generated_discrete_face_flux(self):
        root = Path(__file__).resolve().parents[2]
        data = json.loads((root/'unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908/grid_boundary_profile.json').read_text())
        audit = root/'docs/reconstruction-review-2026-09-07/liquid-native-face-flux/report.json'
        self.assertEqual(hashlib.sha256(audit.read_bytes()).hexdigest(), data['native_flux_report_sha256'])
        self.assertEqual(json.loads(audit.read_text())['source_geometry_sha256'], data['source_geometry_sha256'])
        packed = np.asarray(data['packed_vectors'])
        self.assertEqual(packed.shape, (260, 3))
        self.assertTrue(np.isfinite(packed).all())
        dx, dz, floor = packed[2, 0]/100, packed[3, 0]/100, packed[2, 2]/100
        z = floor+(np.arange(24)+.5)*dz
        for index, face in enumerate(data['faces']):
            rows = packed[4+64*index:4+64*(index+1)]/100
            wet = (z[None, :] > rows[:, 0, None]) & (z[None, :] < rows[:, 1, None])
            area = wet.sum(axis=1)*dx*dz
            np.testing.assert_allclose(area, face['wet_area_m2'], atol=1e-12)
            np.testing.assert_allclose(area*rows[:, 2], face['inward_flux_m3s'], atol=1e-12)
            self.assertLess(abs(face['unresolved_native_flux_m3s']), 1e-7)
        self.assertFalse(data['engine_flux_verified'])

    def test_generated_vector_profile_preserves_normal_profile(self):
        root = Path(__file__).resolve().parents[2]/'unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908'
        baseline = json.loads((root/'grid_boundary_profile.json').read_text())
        vector = json.loads((root/'grid_vector_boundary_profile.json').read_text())
        self.assertEqual(vector['baseline_profile_sha256'], hashlib.sha256((root/'grid_boundary_profile.json').read_bytes()).hexdigest())
        data = np.array(vector['packed_vectors'])
        self.assertEqual(data.shape, (516, 3))
        np.testing.assert_array_equal(data[:260], baseline['packed_vectors'])
        for face in range(4):
            axis, sign = (0, 1) if face == 0 else (0, -1) if face == 1 else (1, 1) if face == 2 else (1, -1)
            np.testing.assert_array_equal(sign*data[260+face*64:260+(face+1)*64, axis], data[4+face*64:4+(face+1)*64, 2])

    def test_actual_vector_audit_detects_missing_tangent(self):
        path = Path(__file__).resolve().parents[2]/'unreal/SourceArt/RaftSim/SouthForkLiquidWindow20260908/grid_vector_boundary_profile.json'
        profile = json.loads(path.read_text())
        selected, expected, face_id = expected_inflow(profile)
        boundary = np.zeros((*selected.shape, 4))
        boundary[..., :3] = expected.astype(np.float16).astype(float)
        boundary[..., 3] = selected
        fields = {'SolidVelocity_Boundary': boundary, 'Velocity': boundary[..., :3].copy()}
        self.assertTrue(audit_vector_boundary(fields, profile)['boundary_binding_verified'])
        source32 = expected.astype(np.float32)
        nearest = source32.astype(np.float16)
        boundary[..., :3] = np.where(np.abs(nearest.astype(float)) > np.abs(source32),
            np.nextafter(nearest, np.float16(0)), nearest).astype(float)
        result = audit_vector_boundary(fields, profile)
        self.assertTrue(result['boundary_binding_verified'])
        self.assertEqual(result['component_count_matching_toward_zero'], result['compared_component_count'])
        boundary[..., 1][face_id == 0] = 0
        self.assertFalse(audit_vector_boundary(fields, profile)['boundary_binding_verified'])


if __name__ == '__main__':
    unittest.main()
