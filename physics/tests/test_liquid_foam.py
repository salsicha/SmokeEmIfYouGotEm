import sys
import unittest
from pathlib import Path
import numpy as np
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_foam_reference import advance_foam
from analyze_liquid_foam import audit


class FoamTransportTest(unittest.TestCase):
    def test_foam_moves_with_water_and_decays(self):
        history = np.zeros((3, 3, 9)); history[1, 1, 3] = 1
        velocity = np.zeros((*history.shape, 3)); velocity[..., 0] = 100
        result = advance_foam(history, velocity, np.zeros_like(history), .1, [90, 30, 30], 1)
        expected = np.zeros_like(history); expected[1, 1, 4] = np.exp(-.1/4)
        np.testing.assert_allclose(result, expected, atol=1e-12)
        self.assertEqual(history[1, 1, 3], 1)  # Previous frame is never overwritten.

    def test_combined_generation_decay_is_timestep_consistent(self):
        h = np.full((3, 3, 3), .3); velocity = np.zeros((*h.shape, 3)); source = np.full_like(h, 1.4)
        whole = advance_foam(h, velocity, source, .2, [30]*3, 1)
        half = advance_foam(h, velocity, source, .1, [30]*3, 1)
        twice = advance_foam(half, velocity, source, .1, [30]*3, 1.1)
        np.testing.assert_allclose(whole, twice, atol=1e-12)

    def test_reset_and_open_boundary_never_reuse_stale_foam(self):
        h = np.ones((3, 3, 3)); velocity = np.zeros((*h.shape, 3)); rate = np.zeros_like(h)
        np.testing.assert_array_equal(advance_foam(h, velocity, rate, .1, [30]*3, .1), 0)
        velocity[..., 0] = 10000
        np.testing.assert_array_equal(advance_foam(h, velocity, rate, .1, [30]*3, 1), 0)

    def test_bounded_under_large_source_and_step(self):
        h = np.ones((3, 3, 3))*2; velocity = np.zeros((*h.shape, 3))
        result = advance_foam(h, velocity, h*1000, 2, [30]*3, 10)
        self.assertTrue(np.all((result >= 0) & (result <= 1)))
        with self.assertRaises(ValueError):
            advance_foam(h, velocity, h, 0, [30]*3, 1)

    def test_audit_rejects_foam_misbound_as_sdf(self):
        foam = np.full((48, 136, 136, 1), .02)
        with patch('analyze_liquid_foam.load_fields', return_value={'RiverFoam': foam, 'SDF': foam}), patch('pathlib.Path.read_text', return_value='{}'):
            self.assertFalse(audit('unused')['channel_sanity_passed'])

    def test_audit_does_not_equate_scratch_with_renderer_or_visual_acceptance(self):
        foam = np.full((48, 136, 136, 1), .02)
        sdf = np.ones_like(foam); sdf[:12] = -1
        with patch('analyze_liquid_foam.load_fields', return_value={'RiverFoam': foam, 'SDF': sdf}), patch('pathlib.Path.read_text', return_value='{}'):
            report = audit('unused')
            self.assertTrue(report['channel_sanity_passed'])
            self.assertFalse(report['renderer_channels_verified'])
            self.assertFalse(report['pipeline_storage_passed'])
            self.assertFalse(report['production_or_visual_acceptance'])


if __name__ == '__main__':
    unittest.main()
