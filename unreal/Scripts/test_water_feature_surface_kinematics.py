import unittest
import numpy as np
from water_feature_surface_kinematics import kinematic_condition


class SurfaceKinematicsTests(unittest.TestCase):
    def test_translating_plane_and_tangential_motion(self):
        dt, speed = .04, .7
        phi = [-speed*t for t in (-2*dt, -dt, 0, dt, 2*dt)]
        r = kinematic_condition(*phi, dt, [0, 0, 1], [2., -.3, speed])
        self.assertAlmostEqual(r['required_surface_normal_velocity_mps'], speed)
        self.assertAlmostEqual(r['signed_normal_mismatch_mps'], 0)
        self.assertAlmostEqual(r['temporal_stencil_disagreement_mps'], 0)
        self.assertFalse(r['accepted'])

    def test_static_interface_exposes_normal_flow_instead_of_removing_it(self):
        u = np.array([2., .3, .2])
        r = kinematic_condition(0., 0., 0., 0., 0., .04, [0, 0, 1], u)
        self.assertEqual(r['signed_normal_mismatch_mps'], .2)
        self.assertEqual(r['required_surface_normal_velocity_mps'], 0)
        np.testing.assert_array_equal(u, [2., .3, .2])

    def test_scaled_levelset_tilted_plane_has_same_normal_speed(self):
        n = np.array([1., 2., 3.]); n /= np.linalg.norm(n)
        speed, dt, scaling = -.43, .03, 2.7
        tangent = np.cross(n, [1., 0., 0.])
        phi = [-scaling*speed*t for t in (-2*dt, -dt, 0, dt, 2*dt)]
        r = kinematic_condition(*phi, dt, scaling*n, speed*n+5*tangent)
        self.assertAlmostEqual(r['required_surface_normal_velocity_mps'], speed)
        self.assertAlmostEqual(r['signed_normal_mismatch_mps'], 0)

    def test_expanding_sphere_uses_local_actual_normal_speed(self):
        dt, radial_speed, acceleration = .025, .16, .21
        phi = [-radial_speed*t-.5*acceleration*t*t for t in (-2*dt, -dt, 0, dt, 2*dt)]
        r = kinematic_condition(*phi, dt, [1, 0, 0], [radial_speed, .3, -.1])
        self.assertAlmostEqual(r['signed_normal_mismatch_mps'], 0)
        self.assertAlmostEqual(r['temporal_stencil_disagreement_mps'], 0)

    def test_cubic_time_control_reports_second_order_stencil_error(self):
        errors = []
        for dt in (.08, .04, .02):
            a, cubic = .2, .3
            phi = [-a*t-cubic*t**3 for t in (-2*dt, -dt, 0, dt, 2*dt)]
            r = kinematic_condition(*phi, dt, [0, 0, 1], [0, 0, a])
            error = r['required_surface_normal_velocity_mps']-a
            self.assertAlmostEqual(error, cubic*dt*dt)
            self.assertAlmostEqual(r['temporal_stencil_disagreement_mps'], 3*error)
            errors.append(error)
        self.assertAlmostEqual(errors[0]/errors[1], 4)
        self.assertAlmostEqual(errors[1]/errors[2], 4)

    def test_unsupported_geometry_time_and_values_fail_explicitly(self):
        args = [0., 0., 0., 0., 0., .04, [0, 0, 1], [1, 0, 0]]
        for index, value in [(0, np.nan), (2, .001), (5, 0), (5, -1),
                             (6, [0, 0, 0]), (6, [0, 1]), (7, [np.inf, 0, 0])]:
            with self.subTest(index=index, value=value), self.assertRaises(ValueError):
                changed = args.copy(); changed[index] = value
                kinematic_condition(*changed)


if __name__ == '__main__':
    unittest.main()
