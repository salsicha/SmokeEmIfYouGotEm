import unittest
import numpy as np
from water_feature_native_mac_extension import reconstruct_extension, corner_provenance


class NativeMacExtensionTests(unittest.TestCase):
    def fixture(self, shape=(13, 7, 7)):
        return np.full(shape, 4, np.int32), np.full((*shape, 3), 999, np.float32)

    def test_planar_extension_has_exact_layers_and_finite_reach(self):
        flags, velocity = self.fixture()
        flags[2, :, :] = 1
        velocity[2:4, :, :, 0] = 3.25
        result = reconstruct_extension(flags, velocity, distance=4)
        np.testing.assert_array_equal(result['layers'][:, 3, 3, 0], [0, 2, 1, 1, 2, 3, 4, 5, 0, 0, 0, 0, 0])
        np.testing.assert_array_equal(result['velocity'][1:8, 3, 3, 0], np.full(7, 3.25))
        self.assertEqual(result['velocity'][8, 3, 3, 0], 999)
        self.assertFalse(result['boundary_supported'])

    def test_seed_requires_either_adjacent_fluid_cell_not_both(self):
        flags, velocity = self.fixture((7, 7, 7))
        flags[3, 3, 3] = 1 | 8
        result = reconstruct_extension(flags, velocity, distance=0)
        self.assertEqual(int((result['layers'] == 1).sum()), 6)
        for component in range(3):
            upper = [3, 3, 3]; upper[component] += 1
            self.assertEqual(result['layers'][(*upper, component)], 1)
        self.assertFalse(result['physical_accuracy_accepted'])

    def test_numeric_unsupported_cache_values_never_create_seeds(self):
        flags, velocity = self.fixture()
        result = reconstruct_extension(flags, velocity)
        self.assertFalse(result['layers'].any())
        np.testing.assert_array_equal(result['velocity'], velocity)

    def test_layer_barrier_does_not_recurse_in_the_same_pass(self):
        flags, velocity = self.fixture()
        flags[2, :, :] = 1
        result = reconstruct_extension(flags, velocity, distance=1)
        self.assertEqual(result['layers'][4, 3, 3, 0], 2)
        self.assertEqual(result['layers'][5, 3, 3, 0], 0)

    def test_neighbor_sum_is_float32_in_native_order(self):
        flags, velocity = self.fixture((7, 7, 7))
        # Six native seed parents around an initially empty target x-face.
        for p, value in zip(((4, 3, 3), (2, 3, 3), (3, 4, 3),
                              (3, 2, 3), (3, 3, 4), (3, 3, 2)),
                             (1e8, 1, -1e8, 3, 4, 5)):
            # Select fluid on the away side to keep the target non-seed.
            q = list(p); q[0] -= int(p[0] <= 3)
            flags[tuple(q)] = 1
            velocity[(*p, 0)] = value
        result = reconstruct_extension(flags, velocity, distance=1)
        self.assertEqual(result['layers'][3, 3, 3, 0], 2)
        self.assertEqual(result['velocity'][3, 3, 3, 0], np.float32(2))

    def test_native_obstacle_propagation_is_labeled_not_silently_filtered(self):
        flags, velocity = self.fixture()
        flags[2, :, :] = 1
        flags[3:6, :, :] = 2
        velocity[2:4, :, :, 0] = 2
        result = reconstruct_extension(flags, velocity)
        self.assertEqual(result['layers'][6, 3, 3, 0], 4)
        self.assertTrue(result['obstacle_contact_lineage'][6, 3, 3, 0])
        into = reconstruct_extension(flags, velocity, into_obstacle=True)
        self.assertEqual(into['layers'][3, 3, 3, 0], 2)
        self.assertTrue(into['obstacle_contact_lineage'][3, 3, 3, 0])

    def test_stencil_provenance_and_boundary_or_outside_support(self):
        flags, velocity = self.fixture()
        flags[2, :, :] = 1
        result = reconstruct_extension(flags, velocity)
        info = corner_provenance(result, [4.5, 3.5, 3.5])
        self.assertTrue(info['all_corners_supported'])
        self.assertEqual(info['components'][0]['extrapolated_corners'], 8)
        self.assertFalse(info['accepted'])
        self.assertFalse(corner_provenance(result, [.5, 3.5, 3.5])['all_corners_supported'])
        self.assertIsNone(corner_provenance(result, [-1, 3.5, 3.5]))

    def test_immutable_inputs_and_explicit_invalid_inputs(self):
        flags, velocity = self.fixture()
        a, b = flags.copy(), velocity.copy()
        reconstruct_extension(flags, velocity)
        np.testing.assert_array_equal(a, flags)
        np.testing.assert_array_equal(b, velocity)
        for f, v, d in ((flags.astype(float), velocity, 4), (flags, velocity.astype(float), 4),
                         (flags, velocity, -1), (flags, velocity, 1.5), (flags, velocity, True)):
            with self.assertRaises(ValueError):
                reconstruct_extension(f, v, distance=d)
        velocity[2, 2, 2, 0] = np.nan
        with self.assertRaises(ValueError):
            reconstruct_extension(flags, velocity)


if __name__ == '__main__':
    unittest.main()
