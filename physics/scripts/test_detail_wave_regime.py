import unittest
import numpy as np
from audit_detail_wave_regime import analyze, phase_speeds


class DetailWaveRegimeTest(unittest.TestCase):
    def test_shallow_and_deep_limits(self):
        sw, airy = phase_speeds([1e-6], 10)
        np.testing.assert_allclose(sw, airy, rtol=1e-12)
        _, airy = phase_speeds([100], 2)
        self.assertAlmostEqual(float(airy[0]), np.sqrt(9.81 / np.pi), places=12)

    def test_scaling_and_wavelength_dependence(self):
        sw, a = phase_speeds([.2, 1, 2], 4)
        sw2, a2 = phase_speeds([.8, 4, 8], 16)
        np.testing.assert_allclose(sw2, 2 * sw)
        np.testing.assert_allclose(a2, 2 * a)
        self.assertTrue(np.all(sw >= a))
        _, longer = phase_speeds([.2, 1, 2], 8)
        self.assertTrue(np.all(longer > a))

    def test_dry_cells_excluded_and_quiet_state_not_evidence(self):
        flow = np.zeros((2, 2, 4)); state = flow.copy()
        flow[0, 0, 0] = 1
        result = analyze(flow, state, .5, [2])
        self.assertEqual(result["wet_cells"], 1)
        self.assertIsNone(result["probes"][0]["squared_displacement_weighted_excess"])
        state[0, 0, 0] = .02
        result = analyze(flow, state, .5, [2])
        self.assertAlmostEqual(result["detail_rms_m"], .02)
        self.assertAlmostEqual(result["probes"][0]["squared_displacement_weighted_excess"],
                               result["probes"][0]["median_relative_speed_excess"])

    def test_invalid_inputs(self):
        for depth, wavelength in (([0], 2), ([-1], 2), ([np.nan], 2), ([1], 0), ([1], np.inf)):
            with self.assertRaises(ValueError):
                phase_speeds(depth, wavelength)
        good = np.zeros((2, 2, 4)); good[..., 0] = 1
        for bad in (np.zeros((2, 4)), np.full((2, 2, 4), np.nan)):
            with self.assertRaises(ValueError):
                analyze(good, bad, .5, [2])
        with self.assertRaises(ValueError):
            analyze(np.zeros_like(good), good, .5, [2])


if __name__ == "__main__":
    unittest.main()
