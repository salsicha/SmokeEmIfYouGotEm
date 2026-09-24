import unittest
import numpy as np
from audit_troublemaker_spectral_context import ndvi, intersecting_pixels, summary


class SpectralContextTest(unittest.TestCase):
    def test_unsigned_bands_do_not_overflow(self):
        result=ndvi(np.array([200,220,0],dtype=np.uint8),np.array([220,200,0],dtype=np.uint8))
        np.testing.assert_allclose(result[:2],[20/420,-20/420])
        self.assertTrue(np.isnan(result[2]))

    def test_invalid_input_is_not_classified(self):
        for red,nir in (([1],[1,2]),([-1],[2]),([np.nan],[1])):
            with self.assertRaises(ValueError):ndvi(red,nir)
        self.assertIsNone(summary([np.nan])['minimum'])

    def test_uncertainty_includes_intersecting_pixel_not_just_centre(self):
        mask=intersecting_pixels((0,0),np.array([0.,1.]),np.array([0.,1.]),1.,.6)
        np.testing.assert_array_equal(mask,[[True,True],[True,False]])

    def test_zero_radius_and_invalid_radius(self):
        np.testing.assert_array_equal(intersecting_pixels((0,0),np.array([0.,1.]),np.array([0.]),1.,0),[[True,False]])
        with self.assertRaises(ValueError):intersecting_pixels((0,0),np.array([0]),np.array([0]),1.,-1)


if __name__=='__main__':unittest.main()
