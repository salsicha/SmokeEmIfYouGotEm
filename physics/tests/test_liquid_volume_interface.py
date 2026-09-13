import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_volume_interface import deposit_volume, sample_centred, implicit_from_volume, measure_interface


class VolumeInterfaceTest(unittest.TestCase):
    def test_mass_conservation_anisotropic(self):
        points = np.random.default_rng(8).uniform([.5, .5, .34], [3.5, 3.5, 2.3], (200, 3))
        mass = deposit_volume(points, (8, 8, 8), (.5, .5, 1/3), 1/48)
        self.assertAlmostEqual(mass.sum(), 200/48, places=12)

    def test_boundary_mass_not_renormalized(self):
        mass = deposit_volume([[0, 1, 1]], (4, 4, 4), (.5, .5, .5), .2)
        self.assertAlmostEqual(mass.sum(), .1)

    def test_linear_field_sampling(self):
        z, y, x = np.indices((8, 8, 8))
        field = 2*(x+.5)*.5+3*(y+.5)*.25-4*(z+.5)/3
        p = np.array([[1.2, .7, 1.3], [2, 1, 2]])
        values, valid = sample_centred(field, p, (.5, .25, 1/3))
        self.assertTrue(valid.all())
        np.testing.assert_allclose(values, p @ [2, 3, -4], atol=1e-14)

    def test_incomplete_stencil_visible(self):
        values, valid = sample_centred(np.ones((4, 4, 4)), [[0, 1, 1]], (.5, .5, .5))
        self.assertFalse(valid[0])
        self.assertTrue(np.isnan(values[0]))

    def test_resolved_bulk(self):
        z, y, x = np.meshgrid(np.arange(.5, 6, 1/3), np.arange(.625, 4, .25), np.arange(.625, 4, .25), indexing='ij')
        p = np.stack((x.ravel(), y.ravel(), z.ravel()), axis=-1)
        h = (.5, .5, 1/3)
        mass = deposit_volume(p, (10, 10, 21), h, 1/48)
        phi = implicit_from_volume(mass, h)
        np.testing.assert_allclose(phi[4:15, 3:6, 3:6], -.5, atol=1e-14)

    def test_thin_sheet_loss_is_reported_not_repaired(self):
        # One sparse water layer at the actual South Fork horizontal pitch.
        # This is a failure-mode test, not proof of real river reconstruction.
        y, x = np.meshgrid(np.arange(.625, 4, .25), np.arange(.625, 4, .25), indexing='ij')
        p = np.column_stack((x.ravel(), y.ravel(), np.full(x.size, 1.)))
        h = (.5, .5, 1/3)
        mass = deposit_volume(p, (10, 10, 9), h, .0625*.1)
        result = measure_interface(mass, h, p)
        self.assertEqual(result['particles_outside_candidate_interface'], len(p))
        self.assertGreater(result['supported_columns_without_candidate_water'], 0)

    def test_invalid_inputs(self):
        for h in ((0, 1, 1), (np.nan, 1, 1)):
            with self.assertRaises(ValueError):
                implicit_from_volume(np.ones((3, 3, 3)), h)
        with self.assertRaises(ValueError):
            deposit_volume([[1, 1, 1]], (3.5, 4, 4), (1, 1, 1), 1)


if __name__ == '__main__':
    unittest.main()
