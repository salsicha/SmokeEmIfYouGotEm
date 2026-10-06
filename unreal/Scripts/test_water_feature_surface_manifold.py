"""Independent exact moving-plane/geodesic tests, not hydraulic validation."""
import unittest
import numpy as np
from water_feature_surface_manifold import initialize, step


def plane(points, time):
    return points[:, 2]-.002*np.sin(3*time), np.tile([0., 0., 1.], (len(points), 1))


def sphere(points, time):
    length = np.linalg.norm(points, axis=1)
    return length-.03, points/length[:, None]


class ManifoldTests(unittest.TestCase):
    def test_moving_plane_exact_flow_and_count(self):
        state = initialize([[0., 0., 0.], [.01, .02, 0.]], [[.01, 0., .006]]*2, plane)
        initial = state.positions.copy()
        for index in range(240):
            state, report = step(state, plane, index/120, 1/120)
        expected = initial+np.array([.02, 0., .002*np.sin(6.)])
        np.testing.assert_allclose(state.positions, expected, atol=1e-12)
        np.testing.assert_allclose(state.tangent_speed, .01, atol=1e-12)
        self.assertEqual(report['count'], 2)

    def test_sphere_geodesic_step_halving_and_no_speed_loss(self):
        errors = []
        for steps in (120, 240, 480):
            state = initialize([[.03, 0., 0.]], [[0., .03, 0.]], sphere)
            for index in range(steps):
                state, report = step(state, sphere, index/steps, 1/steps)
            expected = .03*np.array([[np.cos(1.), np.sin(1.), 0.]])
            errors.append(float(np.linalg.norm(state.positions-expected)))
            np.testing.assert_allclose(state.tangent_speed, .03, atol=1e-12)
            self.assertLess(report['maximum_residual_m'], 1e-10)
        self.assertLess(errors[1], errors[0]/3.8)
        self.assertLess(errors[2], errors[1]/3.8)

    def test_uniform_tangent_acceleration(self):
        flat = lambda p,t: (p[:, 2], np.tile([0., 0., 1.], (len(p), 1)))
        state = initialize([[0., 0., 0.]], [[0., 0., 0.]], flat)
        for index in range(100):
            state, _ = step(state, flat, index/100, .01, acceleration=[[.1, 0., -9.80665]])
        np.testing.assert_allclose(state.velocities, [[.1, 0., 0.]], atol=1e-12)
        np.testing.assert_allclose(state.positions, [[.0505, 0., 0.]], atol=1e-12)

    def test_rejects_buried_initial_marker(self):
        with self.assertRaisesRegex(ValueError, 'already lie'):
            initialize([[0., 0., -.01]], [[0., 0., 0.]], plane)

    def test_rejects_large_motion_without_fallback(self):
        state = initialize([[0., 0., 0.]], [[0., 0., 0.]], plane)
        with self.assertRaisesRegex(ValueError, 'correction bound'):
            step(state, plane, 0., .25, maximum_correction=1e-5)

    def test_rejects_unsupported_field(self):
        state = initialize([[0., 0., 0.]], [[0., 0., 0.]], plane)
        with self.assertRaisesRegex(ValueError, 'Finite supported'):
            step(state, lambda p,t: (np.full(len(p), np.nan), np.ones_like(p)), 0., .01)

    def test_state_is_not_mutated_by_success_or_failure(self):
        state = initialize([[0., 0., 0.]], [[.01, 0., 0.]], plane)
        before = [value.copy() for value in (state.positions, state.velocities, state.tangent_speed)]
        step(state, plane, 0., .01)
        with self.assertRaises(ValueError):
            step(state, plane, 0., .25, maximum_correction=1e-5)
        for value, original in zip((state.positions, state.velocities, state.tangent_speed), before):
            np.testing.assert_array_equal(value, original)

    def test_rejects_empty_state_and_nonfinite_time(self):
        with self.assertRaises(ValueError):
            initialize(np.empty((0, 3)), np.empty((0, 3)), plane)
        state = initialize([[.03, 0., 0.]], [[0., .03, 0.]], sphere)
        with self.assertRaises(ValueError):
            step(state, sphere, np.nan, .01)


if __name__ == '__main__':
    unittest.main()
