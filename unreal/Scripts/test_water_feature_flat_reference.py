import unittest
import numpy as np
from water_feature_flat_reference import planar_phi,lattice_particle_phi,flat_lattice_radius,root_height


class FlatReferenceTests(unittest.TestCase):
    def test_exact_planar_reference(self):
        phi=planar_phi((32,24,24),12)
        self.assertEqual(root_height(list(range(9,16)),phi[5,5,9:16]),12.)

    def test_stock_radius_has_geometric_bias(self):
        levels=list(range(9,16));height=root_height(levels,lattice_particle_phi(levels,12,1.))
        self.assertGreater(height-12,.5);self.assertLess(height-12,.6)

    def test_derived_radius_preserves_only_this_plane(self):
        levels=list(range(9,16));factor=flat_lattice_radius()
        self.assertAlmostEqual(factor,.718713553878169,places=12)
        self.assertAlmostEqual(root_height(levels,lattice_particle_phi(levels,12,factor)),12.,places=12)

    def test_prediction_is_translation_invariant_for_integer_levels(self):
        a=lattice_particle_phi(list(range(9,16)),12,1.)
        b=lattice_particle_phi(list(range(12,19)),15,1.)
        np.testing.assert_array_equal(a,b)

    def test_bad_dimensions_and_radius_rejected(self):
        for shape,height in (((8,24,24),12),((32,24,24),12.5),((32,24,24),23)):
            with self.assertRaises(ValueError):planar_phi(shape,height)
        with self.assertRaises(ValueError):lattice_particle_phi([11,12],12,float('nan'))

    def test_missing_crossing_is_not_fabricated(self):
        with self.assertRaises(ValueError):root_height([9,10,11],[1.,2.,3.])


if __name__=='__main__':unittest.main()
