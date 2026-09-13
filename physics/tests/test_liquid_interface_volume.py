import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_interface_volume import negative_lengths,sample_columns,integrate


class InterfaceVolumeTest(unittest.TestCase):
    def test_multiple_liquid_intervals_and_bed_cut(self):
        v=np.array([[1.,1],[-1.,-1],[1.,1],[-1.,-1],[1.,1]])
        np.testing.assert_allclose(negative_lengths(v,np.arange(5.),np.array([0,1.]),0,4),[2,1.5])

    def test_all_zero_is_not_assumed_to_be_a_volume(self):
        np.testing.assert_array_equal(negative_lengths(np.zeros((3,1)),np.arange(3.),np.zeros(1),0,2),[0])

    def test_affine_surface_sloping_bed_anisotropic_grid(self):
        h=np.array([.7,.4,.3]);z,y,x=np.indices((12,10,12))
        phi=(z+.5)*h[2]-(1.2+.04*(x+.5)*h[0]-.03*(y+.5)*h[1])
        lo=np.array([.8,.5]);hi=np.array([6.2,3.1])
        bed=lambda p:.2+.01*p[:,0]+.02*p[:,1]
        r=integrate(phi,h,lo,hi,bed)
        center=(lo+hi)/2;expected=np.prod(hi-lo)*(1+.03*center[0]-.05*center[1])
        self.assertAlmostEqual(r['volume'],expected,places=12)
        self.assertEqual(r['unresolved_columns'],0);self.assertEqual(r['lower_extrapolated_cap_volume'],0)
        self.assertEqual(r['upper_extrapolated_cap_volume'],0)

    def test_explicit_caps_are_separately_accounted(self):
        z,y,x=np.indices((5,5,5));phi=z+.5-4.8
        r=integrate(phi,np.ones(3),[1,1],[3,3],lambda p:np.zeros(len(p)))
        self.assertAlmostEqual(r['volume'],4*4.8,places=12)
        self.assertAlmostEqual(r['lower_extrapolated_cap_volume'],2,places=12)
        self.assertAlmostEqual(r['upper_extrapolated_cap_volume'],1.2,places=12)
        self.assertAlmostEqual(r['resolved_z_volume'],16,places=12)

    def test_thin_sheet_kept_and_two_planes_not_joined(self):
        z,y,x=np.indices((9,5,5));phi=np.ones(z.shape);phi[2]=-.1;phi[6]=-.2
        r=integrate(phi,np.ones(3),[1,1],[3,3],lambda p:np.zeros(len(p)))
        self.assertAlmostEqual(r['volume'],4*(2*.1/1.1+2*.2/1.2),places=12)

    def test_incomplete_data_and_reversed_bounds_rejected(self):
        with self.assertRaises(ValueError):sample_columns(np.ones((4,4,4)),[1,1,1],[[0,1]])
        with self.assertRaises(ValueError):negative_lengths(np.ones((3,1)),[0,1,2],[0],2,1)
        with self.assertRaises(ValueError):integrate(np.ones((4,4,4)),[1,1,1],[1,1],[2,2],lambda p:np.full(len(p),np.nan))

    def test_unresolved_bed_quadrature_is_reported_not_certified(self):
        r=integrate(-np.ones((5,5,5)),np.ones(3),[1,1],[3,3],
            lambda p:np.where(p[:,0]<1.1,0.,1.),orders=(2,4),column_tolerance=1e-10)
        self.assertGreater(r['unresolved_columns'],0)
        self.assertTrue(r['quadrature_estimated_not_certified'])


if __name__=='__main__':unittest.main()
