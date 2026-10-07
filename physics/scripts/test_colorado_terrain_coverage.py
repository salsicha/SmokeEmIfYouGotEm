import unittest
import numpy as np
from blend_colorado_terrain_coverage import combine


class CoverageTests(unittest.TestCase):
    def test_valid_fine_values_preserved_and_fallback_labelled(self):
        a=np.array([[900.,0.,np.nan,901.]])
        values,resolution=combine(a,[[True,True,True,False]],np.array([[800.,810.,820.,830.]]),10)
        np.testing.assert_array_equal(values,[[900.,810.,820.,830.]])
        np.testing.assert_array_equal(resolution,[[1.,10.,10.,10.]])
        self.assertEqual(a[0,1],0.)

    def test_missing_fallback_cannot_fill_a_gap(self):
        for value in (0.,np.nan):
            with self.assertRaises(ValueError):combine([[0.]],[[True]],[[value]],10)

    def test_missing_fallback_does_not_replace_valid_fine_source(self):
        values,resolution=combine([[900.]],[[True]],[[np.nan]],10)
        self.assertEqual(values[0,0],900.)
        self.assertEqual(resolution[0,0],1.)

    def test_absent_fine_coverage_uses_only_labelled_coarse_data(self):
        values,resolution=combine([[0.,np.nan]],[[True,False]],[[800.,810.]],10)
        np.testing.assert_array_equal(values,[[800.,810.]])
        np.testing.assert_array_equal(resolution,[[10.,10.]])

    def test_different_grids_refused(self):
        with self.assertRaisesRegex(ValueError,'grids'):combine([[900.]],[[True]],[[900.,901.]],10)


if __name__=='__main__':unittest.main()
