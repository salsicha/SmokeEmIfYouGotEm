import unittest
import numpy as np

from water_feature_surface_mac import SurfaceMacField


class SurfaceMacTests(unittest.TestCase):
    def field(self, n=18, h=.02, function=None, radius=2.5):
        origin = np.array((1., -2., 3.))
        ids = np.indices((n, n, n)).transpose(1, 2, 3, 0)
        centres = origin+(ids+.5)*h
        height = origin[2]+n*h*.53
        phi = (centres[..., 2]-height)/h
        velocity = np.empty((n, n, n, 3))
        function = function or (lambda xyz, a: 1+a+2*xyz[..., 0]-3*xyz[..., 1]+xyz[..., 2])
        for a in range(3):
            offset = np.full(3, .5)
            offset[a] = 0
            xyz = origin+(ids+offset)*h
            velocity[..., a] = function(xyz, a)/2
        field = SurfaceMacField(phi, np.ones_like(phi)*5, velocity, origin, (h, h, h), 2, radius_cells=radius)
        point = origin+np.array((n*.48*h, n*.44*h, n*.53*h))
        return field, point, function

    def test_affine_staggered_field_at_interface(self):
        field, p, function = self.field()
        self.assertIsNone(field.interior.sample(p))
        phi, gradient = field.surface(p)
        self.assertAlmostEqual(phi, 0, places=14)
        np.testing.assert_allclose(gradient, [0, 0, 1], atol=1e-12)
        velocity, report = field.sample(p)
        np.testing.assert_allclose(velocity, [function(p, a) for a in range(3)], atol=1e-12)
        self.assertFalse(report['accepted'])
        self.assertLess(max(r['weighted_rms_mps'] for r in report['components']), 1e-12)

    def test_unknown_air_velocity_never_used(self):
        field, p, _ = self.field()
        before = field.sample(p)[0]
        for a in range(3):
            field.interior.velocity[..., a][~field.interior.face_support[a]] = 9e9
        np.testing.assert_array_equal(field.sample(p)[0], before)

    def test_slanted_interface_affine_flow_and_normal(self):
        field, p, function = self.field()
        ids = np.indices(field.interior.phi.shape).transpose(1, 2, 3, 0)
        xyz = field.interior.origin+(ids+.5)*field.h
        normal = np.array((.2, -.3, 1.))
        normal /= np.linalg.norm(normal)
        phi = np.sum((xyz-p)*normal, axis=-1)/field.h
        tilted = SurfaceMacField(phi, field.interior.solid, field.interior.velocity,
                                 field.interior.origin, field.interior.spacing, 2.)
        np.testing.assert_allclose(tilted.surface(p)[1], normal, atol=1e-12)
        np.testing.assert_allclose(tilted.sample(p)[0], [function(p, a) for a in range(3)], atol=1e-12)

    def test_planar_quadratic_local_stencil_refinement(self):
        errors = []
        # Hold the local grid phase fixed; changing it can change the leading
        # error coefficient substantially. This is LOCAL stencil convergence,
        # not an entire changing native-fluid domain convergence claim.
        for h in (.02, .01, .005):
            f = lambda xyz, a: (xyz[..., 0]-1.1)**2+(a+1)*(xyz[..., 2]-3.1908)**2
            field, p, _ = self.field(18, h=h, function=f)
            errors.append(np.linalg.norm(field.sample(p)[0]-[f(p, a) for a in range(3)]))
        self.assertLess(errors[1], errors[0]*.35)
        self.assertLess(errors[2], errors[1]*.35)

    def test_obstacle_and_missing_support_are_not_zero_velocity(self):
        field, p, _ = self.field()
        field.interior.solid[:] = -1
        self.assertIsNone(field.surface(p))
        self.assertIsNone(field.sample(p))
        field, p, _ = self.field()
        for support in field.interior.face_support:
            support[:] = False
        self.assertIsNone(field.sample(p))

    def test_non_interface_and_outside_rejected(self):
        field, p, _ = self.field()
        self.assertIsNone(field.sample(p+[0, 0, .001]))
        self.assertIsNone(field.sample(field.interior.origin))
        self.assertIsNone(field.surface(p+[0, 0, .12]))
        with self.assertRaises(ValueError):
            field.sample([np.nan, 0, 0])
        with self.assertRaises(ValueError):
            field.sample(p, 0)

    def test_snapshot_adapter_does_not_invent_time_support(self):
        field, p, _ = self.field()
        phi, grad = field.manifold_surface([p], 0)
        np.testing.assert_allclose(phi, [0], atol=1e-14)
        np.testing.assert_allclose(grad, [[0, 0, 1]], atol=1e-12)
        with self.assertRaises(ValueError):
            field.manifold_surface([p], .01)

    def test_rank_deficient_single_liquid_layer_rejected(self):
        field, p, _ = self.field()
        field.interior.phi[:] = 1
        field.interior.phi[:, :, 8] = -.54
        field.interior.phi[:, :, 9] = .46
        field = SurfaceMacField(field.interior.phi, field.interior.solid, field.interior.velocity,
                                field.interior.origin, field.interior.spacing, 2)
        self.assertIsNone(field.sample(p))

    def test_surface_gradient_of_trilinear_polynomial(self):
        field, p, _ = self.field()
        ids = np.indices(field.interior.phi.shape).transpose(1, 2, 3, 0)
        q = ids+.5
        field.interior.phi[:] = .01*q[..., 0]*q[..., 1]-.1*q[..., 2]
        query = (p-field.interior.origin)/field.h
        value, grad = field.surface(p)
        self.assertAlmostEqual(value, field.h*(.01*query[0]*query[1]-.1*query[2]))
        np.testing.assert_allclose(grad, [.01*query[1], .01*query[0], -.1], atol=1e-12)


if __name__ == '__main__':
    unittest.main()
