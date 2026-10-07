import unittest
import numpy as np
from continue_colorado_catalog_cook import restart_state, roughness_sensitivity


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.bed = np.arange(6.).reshape(2, 3)+900.
        h = np.array([[0., 2., 3.], [1e-7, .1, 4.]])
        self.frame = dict(h=h, eta=self.bed+h, u=h*.23, v=h*-.12,
                          hu=h*h*.23, hv=h*h*-.12, wet=(h>1e-6).astype(float))
        self.grid = dict(ny=2, nx=3)

    def test_preserve_every_value_including_dry_films(self):
        state = restart_state(self.frame, self.bed, self.grid)
        for name in state:
            np.testing.assert_array_equal(state[name], self.frame['h' if name == 'depth' else name])
            self.assertTrue(state[name].flags.c_contiguous)

    def test_changed_bed_refused_not_remapped(self):
        with self.assertRaisesRegex(ValueError, 'bed changed'):
            restart_state(self.frame, self.bed+.01, self.grid)

    def test_nonfinite_state_refused(self):
        self.frame['u'][0, 0] = float('nan')
        with self.assertRaisesRegex(ValueError, 'Nonfinite'):
            restart_state(self.frame, self.bed, self.grid)

    def test_mismatched_shape_refused(self):
        with self.assertRaisesRegex(ValueError, 'shape'):
            restart_state(self.frame, self.bed, dict(ny=3, nx=2))

    def test_sensitivity_changes_only_roughness_and_preserves_source(self):
        original = dict(roughness=.04, grid=dict(nx=3), boundaries=[dict(kind='outflow', stage=905.)])
        result, receipt = roughness_sensitivity(original, .035)
        self.assertEqual(original['roughness'], .04)
        self.assertEqual(result, dict(original, roughness=.035))
        self.assertEqual(receipt['original'], .04)
        self.assertEqual(receipt['candidate'], .035)
        result['boundaries'][0]['stage'] = 99
        self.assertEqual(original['boundaries'][0]['stage'], 905.)

    def test_invalid_sensitivity_refused(self):
        for value in (float('nan'), float('inf'), .01, .09):
            with self.assertRaisesRegex(ValueError, 'bounded'):
                roughness_sensitivity(dict(roughness=.04), value)

    def test_no_sensitivity_retains_exact_configuration(self):
        original = dict(roughness=.04, boundaries=[])
        result, receipt = roughness_sensitivity(original, None)
        self.assertEqual(result, original)
        self.assertIsNone(receipt)


if __name__ == '__main__':
    unittest.main()
