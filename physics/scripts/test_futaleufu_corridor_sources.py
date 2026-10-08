import unittest
import numpy as np

from build_futaleufu_corridor_sources import crop_bounds, optical_crop, aligned_dsm_bounds, bilinear_dsm, BANDS


class CropBounds(unittest.TestCase):
    meta = dict(x0=1000., y0=4000., cell_m=10, shape=[300,300])

    def test_native_edges_and_outward_rounding(self):
        self.assertEqual(crop_bounds(self.meta, [[1501,3501],[1709,3709]],100), (19,60,40,81))

    def test_exact_edges_do_not_grow_an_extra_pixel(self):
        self.assertEqual(crop_bounds(self.meta, [[1500,3500],[1700,3700]],100), (20,60,40,80))

    def test_refuses_missing_extent_instead_of_clamping(self):
        with self.assertRaisesRegex(ValueError,'outside'):
            crop_bounds(self.meta, [[1000,3500],[1700,3700]],100)

    def test_refuses_invalid_input(self):
        for xy,buffer in (([[1500,np.nan],[1700,3700]],100), ([[1500,3500]],100),
                          ([[1500,3500],[1700,3700]],0), ([[1500,3500],[1700,3700]],np.inf)):
            with self.assertRaises(ValueError):
                crop_bounds(self.meta,xy,buffer)

    def test_preserves_missing_dn_and_requires_all_bands_for_validity(self):
        arrays = {name:np.full((4,4),2000,dtype=np.uint16) for name in BANDS}
        arrays['nir'][1,2] = 0
        arrays['blue'][2,1] = 0
        result = optical_crop(arrays,dict(shape=[4,4]),(1,3,1,3))
        np.testing.assert_array_equal(result['valid'], [[True,False],[False,True]])
        self.assertEqual(result['nir'][0,1],0)
        self.assertEqual(result['green'][0,1],2000)

    def test_rejects_preconverted_source(self):
        arrays = {name:np.ones((4,4),dtype=np.float32) for name in BANDS}
        with self.assertRaises(ValueError):
            optical_crop(arrays,dict(shape=[4,4]),(1,3,1,3))

    def test_dsm_preserves_half_pixel_origin(self):
        transform = (1/3600,0,-73-1/7200,0,-1/3600,-43+1/7200)
        bounds = (-72.073, -43.37, -71.959, -43.30)
        w,s,e,n = aligned_dsm_bounds(bounds,transform)
        self.assertLessEqual(w,bounds[0]); self.assertLessEqual(s,bounds[1])
        self.assertGreaterEqual(e,bounds[2]); self.assertGreaterEqual(n,bounds[3])
        for x in (w,e):
            self.assertAlmostEqual((x-transform[2])/transform[0],round((x-transform[2])/transform[0]),places=7)
        for y in (s,n):
            self.assertAlmostEqual((y-transform[5])/transform[4],round((y-transform[5])/transform[4]),places=7)

    def test_reject_rotated_dsm_lattice(self):
        with self.assertRaises(ValueError):
            aligned_dsm_bounds((0,0,1,1),(1,.1,0,0,-1,10))

    def test_bilinear_uses_sample_centres_not_pixel_edges(self):
        values = np.array([[0,10],[20,30]],dtype=np.float32)
        transform = (1,0,-.5,0,-1,1.5)
        np.testing.assert_array_equal(bilinear_dsm(values,transform,[0,1,.5],[1,0,.5]),[0,30,15])

    def test_bilinear_refuses_outside_and_unknown_support(self):
        transform = (1,0,-.5,0,-1,1.5)
        with self.assertRaises(ValueError):
            bilinear_dsm(np.zeros((2,2)),transform,1.001,0)
        with self.assertRaises(ValueError):
            bilinear_dsm(np.array([[1,np.nan],[2,3]]),transform,.1,.1)


if __name__ == '__main__':
    unittest.main()
