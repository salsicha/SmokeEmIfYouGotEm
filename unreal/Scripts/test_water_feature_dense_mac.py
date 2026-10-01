import unittest
import numpy as np
from water_feature_dense_mac import DenseMacField, trilinear


class DenseMacTests(unittest.TestCase):
    def field(self, function):
        shape, origin, spacing = (8, 9, 10), np.array((1., -2., 3.)), np.array((.2, .3, .4))
        velocity = np.zeros((*shape, 3))
        indices = np.indices(shape).transpose(1, 2, 3, 0)
        for axis in range(3):
            offsets = np.full(3, .5)
            offsets[axis] = 0
            xyz = origin+(indices+offsets)*spacing
            velocity[..., axis] = function(xyz, axis)
        return DenseMacField(-np.ones(shape), np.ones(shape), velocity, origin, spacing, 2.)

    def test_constant_and_linear_staggered_anisotropic(self):
        field = self.field(lambda xyz, axis: 1.+axis+xyz[..., 0]+2*xyz[..., 1]-xyz[..., 2])
        point = np.array((1.72, -.89, 4.43))
        expected = 2*(1.+np.arange(3)+point[0]+2*point[1]-point[2])
        np.testing.assert_allclose(field.sample(point), expected, atol=1e-12)

    def test_rotation(self):
        field = self.field(lambda xyz, axis: (-xyz[..., 1] if axis == 0 else
                                             xyz[..., 0] if axis == 1 else np.zeros(xyz.shape[:-1])))
        point = np.array((1.72, -.89, 4.43))
        np.testing.assert_allclose(field.sample(point), 2*np.array((-point[1], point[0], 0)), atol=1e-12)

    def test_support_and_solid_require_all_neighbors(self):
        field = self.field(lambda xyz, axis: np.ones(xyz.shape[:-1]))
        point = field.origin+np.array((3.7, 3.7, 3.7))*field.spacing
        self.assertIsNotNone(field.sample(point))
        field.phi[4, 4, 4] = .1
        self.assertIsNone(field.sample(point))
        field.phi[4, 4, 4] = -1
        field.solid[4, 4, 4] = -.1
        self.assertIsNone(field.sample(point))
        self.assertIsNone(field.sample(field.origin))

    def test_mac_face_needs_both_liquid_adjacent_centers(self):
        field = self.field(lambda xyz, axis: np.ones(xyz.shape[:-1]))
        point = field.origin+np.array((3.7, 3.7, 3.7))*field.spacing
        phi = field.phi.copy()
        phi[2, 3, 3] = .1  # Outside point's center stencil, inside x-face stencil.
        supported = DenseMacField(phi, field.solid, field.velocity, field.origin, field.spacing, 2.)
        self.assertTrue((phi[3:5, 3:5, 3:5] < 0).all())
        self.assertIsNone(supported.sample(point))

    def test_invalid_data_and_no_outer_extension(self):
        self.assertIsNone(trilinear(np.ones((3, 3, 3)), (-.1, 1, 1)))
        with self.assertRaises(ValueError):
            DenseMacField(np.ones((3, 3, 3)), np.ones((3, 3, 3)),
                          np.ones((3, 3, 3, 3)), (0, 0, 0), (1, 0, 1), 1)


if __name__ == '__main__':
    unittest.main()
