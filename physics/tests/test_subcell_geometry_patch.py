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

    def test_shallow_counterflow_requires_gross_donor_bound(self):
        # Two wet slivers meet at the bottom of z=abs(normal). Equal stages
        # imply zero net mass flux, but tangential Rusanov momentum exchange
        # remains. Each cell has V=eta^2/2; the shared face has area eta.
        # Independent analytic rate: du_t/dt = -2*sqrt(g*eta)/eta * u_t.
        for axis in (0, 1):
            shape = (1, 2) if axis == 0 else (2, 1)
            origin = [-.5, 0.] if axis == 0 else [0., -.5]
            terrain = sampler(lambda x, y: abs(x if axis == 0 else y))
            patch = SubcellGeometryPatch(terrain, origin, shape, periodic=(axis == 1, axis == 0))
            for eta in (1e-2, 1e-4, 1e-6):
                velocity = np.zeros((*shape, 2))
                velocity.reshape(2, 2)[:, 1-axis] = [1., -1.]
                volume, momentum = patch.state_from_stages(eta, velocity)
                dv, dp, limit, bounds = patch.rates(volume, momentum, diagnostics=True)
                np.testing.assert_allclose(volume, eta*eta/2, atol=0, rtol=1e-14)
                np.testing.assert_allclose(dv, 0, atol=0)
                expected_rate = -2*np.sqrt(9.81*eta)/eta*velocity[..., 1-axis]
                np.testing.assert_allclose(dp[..., 1-axis]/volume, expected_rate, atol=0, rtol=1e-13)
                old_dt = .45*min(bounds['net_drain_limit_seconds'], bounds['wave_limit_seconds'])
                old_velocity = (momentum+old_dt*dp)/volume[..., None]
                self.assertGreater(np.max(abs(old_velocity)), 2.)
                self.assertLess(limit, old_dt)
                limiting = bounds['limiting_donor_cell']
                self.assertEqual(limiting['row'], 0)
                self.assertEqual(limiting['col'], 0)
                self.assertAlmostEqual(limiting['volume_m3'], eta*eta/2)
                self.assertAlmostEqual(limiting['wet_area_m2'], eta)
                self.assertAlmostEqual(limiting['stage_m']-limiting['minimum_bed_m'], eta)
                self.assertAlmostEqual(limiting['incoming_discharge_m3s'], limiting['outgoing_discharge_m3s'])
                self.assertAlmostEqual(limiting['volume_m3']/limiting['gross_donor_coefficient_m3s'], limit)
                with self.assertRaisesRegex(ValueError, 'donor'):
                    patch.advance(volume, momentum, old_dt)
                fixed_v, fixed_p = patch.advance(volume, momentum, .45*limit)
                np.testing.assert_array_equal(fixed_v, volume)
                self.assertLessEqual(np.max(abs(fixed_p/fixed_v[..., None])), 1.)
                np.testing.assert_allclose(fixed_p.sum(axis=(0, 1)), 0, atol=1e-18)

    def test_dry_diagnostics_have_no_invented_limiting_cell(self):
        patch = SubcellGeometryPatch(sampler(lambda x, y: x*0), [-.5, -.5], (2, 2))
        volume, momentum = patch.state_from_stages(0.)
        dv, dp, limit, bounds = patch.rates(volume, momentum, diagnostics=True)
        self.assertIsNone(bounds['limiting_donor_cell'])
        self.assertTrue(np.isinf(limit))
        np.testing.assert_array_equal(dv, 0)
        np.testing.assert_array_equal(dp, 0)


if __name__ == '__main__':
    unittest.main()
