import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_map_injectivity import compact_map_bound
from liquid_compatible_advection import sample_compact


class MapInjectivityTest(unittest.TestCase):
    def test_zero_and_small_maps_certify(self):
        h=np.array([50.,30.,20.]);d=np.zeros((8,9,10,3))
        r=compact_map_bound(d,h);self.assertTrue(r['continuous_map_globally_injective'])
        self.assertEqual(r['lipschitz_upper_bound'],0)
        d[...,0]=2.
        r=compact_map_bound(d,h);self.assertTrue(r['continuous_map_globally_injective'])
        # X-normal extension edge .02, transverse Y/Z edges .04 each.
        self.assertAlmostEqual(r['lipschitz_upper_bound'],.1)

    def test_anisotropic_bound_dominates_sampled_jacobians(self):
        h=np.array([.7,1.3,2.1]);rng=np.random.default_rng(63)
        d=rng.normal(size=(10,11,12,3))*.04*h
        p=rng.uniform([2,2,2],[9,8,7],size=(500,3))*h
        _,j=sample_compact(p,d.transpose(2,1,0,3),h,derivatives=True)
        j=j*h[None,None,:]/h[None,:,None]
        r=compact_map_bound(d,h);bound=np.array(r['derivative_absolute_bounds_cell_metric'])
        self.assertTrue(np.all(abs(j)<=bound+1e-14))
        self.assertTrue(r['continuous_map_globally_injective'])

    def test_large_shear_not_certified_by_positive_point_determinants(self):
        d=np.zeros((8,8,8,3));d[3,3,3,0]=5
        r=compact_map_bound(d,np.ones(3));self.assertFalse(r['continuous_map_globally_injective'])
        self.assertIsNone(r['minimum_cell_metric_separation_factor'])

    def test_invalid_metric_rejected(self):
        with self.assertRaises(ValueError):compact_map_bound(np.zeros((8,8,8,3)),[1,0,1])
        with self.assertRaises(ValueError):compact_map_bound(np.full((8,8,8,3),np.nan),np.ones(3))


if __name__=='__main__':unittest.main()
