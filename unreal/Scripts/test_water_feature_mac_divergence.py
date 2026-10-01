import unittest
import numpy as np
from water_feature_mac_divergence import mac_divergence, interior_liquid_mask


class MacDivergenceTests(unittest.TestCase):
    def test_linear_anisotropic_and_constant(self):
        h = np.array([.2, .3, .4])
        indices = np.indices((4, 5, 6)).transpose(1, 2, 3, 0)
        v = indices*h*np.array([2., -1., 3.])
        np.testing.assert_allclose(mac_divergence(v, h), 4., atol=1e-14)
        np.testing.assert_array_equal(mac_divergence(np.ones_like(v), h), 0.)

    def test_divergence_free_rotation(self):
        x, y, z = np.indices((4, 5, 6))
        v = np.stack([-y, x, z*0], axis=-1)
        np.testing.assert_array_equal(mac_divergence(v, (1., 1., 1.)), 0.)

    def test_interface_obstacle_and_neighbor_exclusion(self):
        phi = np.full((5, 5, 5), -3.)
        solid = -phi
        mask = interior_liquid_mask(phi, solid)
        self.assertEqual(int(mask.sum()), 27)
        phi[2, 2, 2] = 1.
        mask = interior_liquid_mask(phi, solid)
        self.assertEqual(int(mask.sum()), 20)
        self.assertFalse(mask[1, 2, 2])
        phi.fill(-3)
        solid[2, 2, 2] = -1.
        self.assertEqual(int(interior_liquid_mask(phi, solid).sum()), 20)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            mac_divergence(np.zeros((3, 3, 3, 3)), (1., 0., 1.))
        with self.assertRaises(ValueError):
            interior_liquid_mask(np.ones((3, 3, 3)), np.ones((3, 3, 2)))


if __name__ == '__main__':
    unittest.main()
