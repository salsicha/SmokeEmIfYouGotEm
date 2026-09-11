import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_native_transfer import reference, reference_batched, reduce_reference


class NativeTransferReferenceTest(unittest.TestCase):
    def setUp(self):
        self.record = dict(cells=[8, 8, 8], world_origin_cm=[0, 0, 0],
                           world_axis_x=[0.6, 0.8, 0], world_axis_y=[-0.8, 0.6, 0],
                           extent_cm=[400, 400, 200], particle_volume_m3=0.125)

    def test_rotated_anisotropic_partition_and_momentum(self):
        p = np.array([[0, 0, 100], [13, -17, 85]], dtype=float)
        v = np.array([[100, -40, 3], [-70, 130, 17]], dtype=float)
        values, bound = reference(self.record, p, v)
        self.assertAlmostEqual(values[..., 3].sum(), 0.25)
        axes = np.array([[.6, .8, 0], [-.8, .6, 0], [0, 0, 1]])
        np.testing.assert_allclose(values[..., :3].sum(axis=(0, 1, 2)), v.sum(axis=0)@axes.T*.125)
        self.assertTrue(np.all(bound >= 0))

    def test_empty_has_no_phantom_support_or_tolerance(self):
        values, bound = reference(self.record, np.empty((0, 3)), np.empty((0, 3)))
        self.assertFalse(np.any(values)); self.assertFalse(np.any(bound))

    def test_nonorthogonal_frame_rejected(self):
        self.record['world_axis_x'] = [1, 1, 0]
        with self.assertRaises(ValueError): reference(self.record, [], [])

    def test_batched_reference_matches_scalar_with_borders_and_rotation(self):
        rng=np.random.default_rng(42)
        p=rng.uniform([-300,-300,-40],[300,300,240],(100,3));v=rng.uniform(-200,200,(100,3))
        slow,slow_error=reference(self.record,p,v)
        for chunk in (7,8192):
            fast,fast_error=reference_batched(self.record,p,v,chunk)
            np.testing.assert_allclose(fast,slow,atol=1e-12,rtol=1e-12)
            np.testing.assert_allclose(fast_error,slow_error,atol=1e-12,rtol=1e-12)

    def test_batched_large_population_conserves_interior_mass(self):
        p=np.tile([0.,0.,100.],(129,1));v=np.tile([100.,-40.,3.],(129,1))
        values,_=reference(self.record,p,v)
        self.assertAlmostEqual(values[...,3].sum(),129*.125)

    def test_corner_sums_raw_not_average_velocity(self):
        raw = {i: np.zeros((4, 8, 8, 4), dtype='<f4') for i in range(4)}
        raw[0][:, 2, 2] = [1, 0, 0, 1]
        raw[1][:, 0, 0] = [18, 0, 0, 9]
        raw[2][:, 1, 0] = [-4, 0, 0, 2]
        columns = [(0, 1, 2, 2, 0, 0), (0, 2, 2, 2, 0, 1), (0, 3, 2, 2, 1, 0)]
        total = reduce_reference(raw, columns)
        np.testing.assert_array_equal(total[0][0, 2, 2], [15, 0, 0, 12])
        np.testing.assert_array_equal(total[3][:, 0, 1], total[0][:, 2, 2])
        np.testing.assert_array_equal(raw[0][0, 2, 2], [1, 0, 0, 1])
        with self.assertRaises(ValueError): reduce_reference(raw, columns*2)
        with self.assertRaises(ValueError): reduce_reference(raw, columns+[(0, 1, 2, 2, 1, 0)])


if __name__ == '__main__': unittest.main()
