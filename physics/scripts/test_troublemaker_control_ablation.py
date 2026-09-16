import unittest
import numpy as np
from prepare_troublemaker_control_ablation import ablate
from compare_troublemaker_control_ablation import centered_wet_slopes


class ControlAblationTest(unittest.TestCase):
    def fixture(self):
        original = dict(east_m=np.arange(6.).reshape(2, 3), north_m=np.ones((2, 3)),
                        z_m=np.full((2, 3), 3., dtype=np.float32),
                        source_surface_m=np.full((2, 3), 5., dtype=np.float32),
                        authority=np.array([[1, 2, 2], [2, 2, 2]], dtype=np.uint8))
        mesh = {k: v.copy() for k, v in original.items()}
        mesh['authority'] = np.array([[1, 2, 3], [4, 5, 2]], dtype=np.uint8)
        mesh['z_m'][1, :2] = [4., 6.]
        mesh['triangles'] = np.array([[0, 1, 3], [1, 4, 3]])
        return mesh, original, np.ones((2, 3), np.float32), original['z_m'].copy()

    def test_only_unchanged_original_prior_can_change(self):
        mesh, original, baseline, controlled = self.fixture()
        saved = {k: v.copy() for k, v in mesh.items()}
        result, changed = ablate(mesh, original, baseline, controlled)
        np.testing.assert_array_equal(changed, mesh['authority'] == 2)
        np.testing.assert_array_equal(result['z_m'][~changed], mesh['z_m'][~changed])
        for k in mesh:
            np.testing.assert_array_equal(mesh[k], saved[k])
            if k != 'z_m':
                np.testing.assert_array_equal(result[k], mesh[k])

    def test_changed_current_source_refused(self):
        for key in ('east_m', 'north_m', 'z_m', 'source_surface_m'):
            with self.subTest(key=key):
                mesh, original, baseline, controlled = self.fixture()
                mesh[key][0, 1] += .125
                with self.assertRaisesRegex(ValueError, 'no longer equals'):
                    ablate(mesh, original, baseline, controlled)

    def test_wrong_reconstruction_refused_even_on_now_protected_vertex(self):
        args = self.fixture()
        args[3][1, 0] += .125
        with self.assertRaisesRegex(ValueError, 'reproduce'):
            ablate(*args)

    def test_captured_vertex_cannot_be_relabelled_as_prior(self):
        args = self.fixture()
        args[0]['authority'][0, 0] = 2
        with self.assertRaisesRegex(ValueError, 'not an original'):
            ablate(*args)

    def test_nonfinite_baseline_refused(self):
        args = self.fixture()
        args[2][0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, 'finite prior'):
            ablate(*args)

    def test_centered_slope_retains_physical_spacing(self):
        y, x = np.indices((5, 5))*2.
        slope, wet = centered_wet_slopes(.3*x+.4*y, np.ones((5, 5)), 2.)
        np.testing.assert_allclose(slope, np.degrees(np.arctan(.5)))
        self.assertTrue(wet.all())

    def test_dry_neighbor_excludes_stencil_not_flattened_as_water(self):
        h = np.ones((5, 5)); h[2, 2] = 0
        _, wet = centered_wet_slopes(np.zeros_like(h), h, 1.)
        np.testing.assert_array_equal(wet, [[True,False,True],[False,False,False],[True,False,True]])


if __name__ == '__main__':
    unittest.main()
