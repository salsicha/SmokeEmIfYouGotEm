import unittest
import numpy as np
from export_colorado_catalog_runtime import landscape_grid,landscape_sample


class RuntimeTerrainTests(unittest.TestCase):
    def test_chaos_diagonal_is_not_bilinear(self):
        a=np.array([[0.,0.],[0.,4.]])
        np.testing.assert_allclose(landscape_sample(a,[.5,.75,.25],[.5,.25,.75]),[2,1,1])

    def test_triangle_sampler_preserves_edges_and_missing_coverage(self):
        a=np.array([[1.,2.],[3.,4.]])
        np.testing.assert_allclose(landscape_sample(a,[0,0,1,1],[0,1,0,1]),[1,2,3,4])
        self.assertTrue(np.isnan(landscape_sample(a,[0,-.1,np.nan],[1.1,0,0])).all())

    def test_ue_height_quantization_uses_65536_not_65535(self):
        bed=np.array([[910.,912.],[914.,918.]])
        encoded,decoded,lo,relief=landscape_grid(bed,9)
        self.assertEqual(int(encoded.min()),0)
        self.assertEqual(int(encoded.max()),65535)
        self.assertAlmostEqual(lo+65535*relief/65536,918.)
        self.assertAlmostEqual(decoded[0,0],910.)
        self.assertAlmostEqual(decoded[-1,-1],918.)

    def test_no_missing_or_flat_terrain_accepted(self):
        for a in (np.ones((4,4)),np.array([[1.,np.nan],[2.,3.]]),np.ones((1,4))):
            with self.assertRaises(ValueError):landscape_grid(a,9)

    def test_registered_edges_keep_half_cell_border(self):
        bed=np.tile(np.arange(4.),(4,1))
        _,decoded,_,relief=landscape_grid(bed,9)
        np.testing.assert_allclose(decoded[4],[0,0,.5,1,1.5,2,2.5,3,3],atol=relief/65536)


if __name__=='__main__':unittest.main()
