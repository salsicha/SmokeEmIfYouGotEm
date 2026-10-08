import unittest
import numpy as np
from audit_futaleufu_native_continuation import boundary_balance, validate_receipt, closed_wet_faces


class ContinuationAuditTests(unittest.TestCase):
    def setUp(self):
        self.probes = [dict(tile_index=0, edge='west', role='upstream', branch='azul'),
                       dict(tile_index=1, edge='north', role='upstream', branch='main'),
                       dict(tile_index=2, edge='south', role='downstream', branch='outlet')]
        self.budget = dict(azul=dict(target_m3s=30.), main=dict(target_m3s=370.))

    def test_native_flux_sign_and_unsettled_storage(self):
        result = boundary_balance(self.probes, [30., 370., -80.], self.budget)
        self.assertEqual(result['total_outlet_m3s'], 80.)
        self.assertEqual(result['instantaneous_storage_rate_m3s'], 320.)
        self.assertEqual(result['outlet_to_inlet_ratio'], .2)
        self.assertFalse(result['reverse_outlet_flow'])

    def test_reverse_outlet_is_not_hidden_by_absolute_value(self):
        result = boundary_balance(self.probes, [30., 370., 10.], self.budget)
        self.assertTrue(result['reverse_outlet_flow'])
        self.assertEqual(result['instantaneous_storage_rate_m3s'], 410.)

    def test_bad_discharge_receipts_rejected(self):
        for fluxes in ([30., 369., -80.], [30., 370.], [30., 370., np.nan]):
            with self.assertRaises(ValueError): boundary_balance(self.probes, fluxes, self.budget)
        with self.assertRaises(ValueError):
            boundary_balance(self.probes+self.probes[:1], [30., 370., -80., 30.], self.budget)

    def test_restart_clock_and_unchanged_mass_gate(self):
        receipt = dict(step=300, time_seconds=5., volume_m3=100., boundary_volume_m3=10.,
                       conservation_residual_m3=1e-9, maximum_step_residual_m3=1e-9, snapshot=True)
        validate_receipt(receipt, 300, 2., .01)
        for change in (dict(time_seconds=3.), dict(snapshot=False),
                       dict(maximum_step_residual_m3=1e-4), dict(volume_m3=np.nan)):
            with self.assertRaises(ValueError): validate_receipt({**receipt, **change}, 300, 2., .01)

    def test_internal_faces_are_not_exterior_and_closed_wet_faces_reported(self):
        h = np.zeros((6, 3))
        h[1, -1] = 1.
        h[4, 0] = 1.
        keys = [(0, 0), (1, 0)]
        self.assertFalse(closed_wet_faces(h, keys, 3, []))
        h[0, 1] = .06
        self.assertEqual(closed_wet_faces(h, keys, 3, [])[0]['edge'], 'south')
        self.assertFalse(closed_wet_faces(h, keys, 3, [dict(tile_index=0, edge='south')]))


if __name__ == '__main__': unittest.main()
