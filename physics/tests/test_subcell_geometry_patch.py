import unittest
import numpy as np
from subcell_geometry_patch import SubcellGeometryPatch
from test_triangle_face_section import sampler


class SubcellGeometryPatchTest(unittest.TestCase):
    def test_partial_wet_lake_over_rough_bed_stays_at_rest(self):
        terrain = sampler(lambda x, y: .6+.7*np.cos(x*2)*np.cos(y*2))
        patch = SubcellGeometryPatch(terrain, [-1.5, -1.5], (4, 4))
        volume, momentum = patch.state_from_stages(.7)
        original = volume.copy()
        for _ in range(12):
            volume, momentum = patch.advance(volume, momentum, .002)
        np.testing.assert_allclose(volume, original, atol=3e-14, rtol=0)
        np.testing.assert_allclose(momentum, 0, atol=3e-14, rtol=0)
        self.assertTrue((volume == 0).any())

    def test_periodic_flat_transport_conserves_mass_and_both_momenta(self):
        patch = SubcellGeometryPatch(sampler(lambda x, y: x*0), [-1.5, -1.5], (4, 4), periodic=(True, True))
        rng = np.random.default_rng(35)
        volume, momentum = patch.state_from_stages(.8+.3*rng.random((4, 4)), rng.normal(size=(4, 4, 2))*.2)
        total_v, total_p = volume.sum(), momentum.sum(axis=(0, 1))
        for _ in range(20):
            volume, momentum = patch.advance(volume, momentum, .005)
            self.assertGreater(volume.min(), 0)
        self.assertAlmostEqual(volume.sum(), total_v, places=12)
        np.testing.assert_allclose(momentum.sum(axis=(0, 1)), total_p, atol=2e-14)

    def test_wetting_without_depth_floor_or_postupdate_repair(self):
        patch = SubcellGeometryPatch(sampler(lambda x, y: x*0), [-.5, -.5], (2, 2))
        volume, momentum = patch.state_from_stages([[1., 0.], [1e-9, 0.]])
        before = volume.copy(), momentum.copy()
        for _ in range(12):
            _, _, limit = patch.rates(volume, momentum)
            volume, momentum = patch.advance(volume, momentum, min(.002, .45*limit))
            self.assertGreaterEqual(volume.min(), 0)
        self.assertTrue((volume > 0).all())
        self.assertAlmostEqual(volume.sum(), before[0].sum(), places=13)
        self.assertEqual(before[0][1, 0], 1e-9)

    def test_bad_timestep_rejects_without_mutating_input(self):
        patch = SubcellGeometryPatch(sampler(lambda x, y: x*0), [-.5, -.5], (2, 2))
        volume, momentum = patch.state_from_stages([[1., 0.], [1., 0.]])
        original = volume.copy(), momentum.copy()
        _, _, limit = patch.rates(volume, momentum)
        with self.assertRaisesRegex(ValueError, 'Timestep'):
            patch.advance(volume, momentum, 2*limit)
        np.testing.assert_array_equal(volume, original[0])
        np.testing.assert_array_equal(momentum, original[1])
        momentum[0, 1, 0] = 1e-12
        with self.assertRaisesRegex(ValueError, 'dry momentum'):
            patch.rates(volume, momentum)

    def test_nonperiodic_geometry_cannot_be_spliced_periodically(self):
        with self.assertRaisesRegex(ValueError, 'geometry differs'):
            SubcellGeometryPatch(sampler(lambda x, y: x+2), [-1.5, -1.5], (4, 4), periodic=(True, False))


if __name__ == '__main__':
    unittest.main()
