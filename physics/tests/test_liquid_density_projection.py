import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_density_projection import tent_cdf,solid_kernel_fraction,density_target,solve
from liquid_compatible_projection import divergence


class DensityProjectionTest(unittest.TestCase):
    def test_tent_integral_symmetry_and_support(self):
        x=np.linspace(-2,2,41);v=tent_cdf(x)
        np.testing.assert_allclose(v+tent_cdf(-x),1,atol=1e-15)
        self.assertEqual(v[0],0);self.assertEqual(v[-1],1)
        self.assertTrue((np.diff(v)>=0).all())

    def test_flat_bed_exact_and_rotated_sloped_plane_converges(self):
        xy=np.array([[2.,3.],[4.,5.]])
        h=np.array([.5,.7,.3]);z=np.array([-.5,-.1,0,.1,.5])
        flat=solid_kernel_fraction(lambda x,y:np.zeros_like(x),xy,z,h,np.eye(2),3)
        np.testing.assert_allclose(flat,np.broadcast_to(tent_cdf(-z[:,None]/h[2]),flat.shape),atol=1e-14)
        angle=.3;axes=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        bed=lambda x,y:.1*x+.15*y
        a=solid_kernel_fraction(bed,xy,np.array([.65,1.15]),h,axes,4)
        b=solid_kernel_fraction(bed,xy,np.array([.65,1.15]),h,axes,8)
        self.assertLess(np.max(abs(a-b)),1e-5)
        self.assertAlmostEqual(a[0,0],.5,places=12)

    def test_boundary_deficiency_does_not_create_false_attraction(self):
        b=np.zeros((8,8,8,4));b[0,:,:,3]=2
        rho=np.full((8,8,8),.7);solid=np.full_like(rho,.3)
        target,report=density_target(rho,solid,b)
        np.testing.assert_array_equal(target,0)
        solid[:]=0;target,_=density_target(rho,solid,b)
        np.testing.assert_array_equal(target[1],0)
        self.assertTrue((target[3]<0).all())
        np.testing.assert_array_equal(rho,.7)

    def test_compression_moves_outward_without_clipping_measured_density(self):
        b=np.zeros((12,12,12,4));b[...,3]=2;b[2:-2,2:-2,2:-2,3]=0
        rho=np.ones((12,12,12));rho[5:7,5:7,5:7]=8
        delta,p,report=solve(rho,np.zeros_like(rho),b,[1,1,1],tolerance=1e-10)
        self.assertTrue(report['solver']['converged'])
        target,_=density_target(rho,np.zeros_like(rho),b)
        np.testing.assert_allclose(divergence(delta,[1,1,1])[b[...,3]==0],target[b[...,3]==0],atol=1e-9)
        self.assertGreater(delta[6,6,7,0],0);self.assertLess(delta[6,6,4,0],0)
        self.assertEqual(report['maximum_actual_particle_density'],8)
        self.assertEqual(rho[5,5,5],8)

    def test_rest_state_and_fixed_wall_are_unchanged(self):
        b=np.zeros((10,10,10,4));b[:2,...,3]=1;b[-2:,...,3]=2
        rho=np.ones((10,10,10))
        delta,_,report=solve(rho,np.zeros_like(rho),b,[1,1,1])
        np.testing.assert_array_equal(delta,0)
        self.assertEqual(report['solver']['maximum_fixed_velocity_change_cm_s'],0)

    def test_invalid_solid_and_missing_bed_are_rejected(self):
        with self.assertRaises(ValueError):density_target(np.ones((4,4,4)),np.full((4,4,4),1.1),np.zeros((4,4,4,4)))
        with self.assertRaises(ValueError):solid_kernel_fraction(lambda x,y:np.full_like(x,np.nan),np.zeros((1,2)),np.ones(1),np.ones(3),np.eye(2))


if __name__=='__main__':unittest.main()
