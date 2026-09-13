import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_surface_volume_gradient import negative_length_gradient,integrate_gradient
from liquid_interface_volume import negative_lengths,integrate


class SurfaceVolumeGradientTest(unittest.TestCase):
    def test_all_crossings_and_bed_cut_match_finite_differences(self):
        z=np.array([0.,.4,1.,1.7,2.]);v=np.array([[1.,-1.],[-.7,1.],[.4,-.3],[-.2,1.],[1.,-1.]])
        bed=np.array([.1,.5]);length,g,_=negative_length_gradient(v,z,bed,0,2)
        eps=1e-6
        for i in range(len(z)):
            for j in range(2):
                a=v.copy();b=v.copy();a[i,j]+=eps;b[i,j]-=eps
                diff=(negative_lengths(a,z,bed,0,2)[j]-negative_lengths(b,z,bed,0,2)[j])/(2*eps)
                self.assertAlmostEqual(g[i,j],diff,places=9)
        np.testing.assert_array_equal(length,negative_lengths(v,z,bed,0,2))

    def test_affine_plane_derivative_with_sloping_bed(self):
        h=np.array([.7,.4,.3]);z,y,x=np.indices((12,8,9));phi=(z+.5)*h[2]-(1.23+.04*(x+.5)*h[0]-.03*(y+.5)*h[1])
        lo=np.array([.8,.5]);hi=np.array([4.8,2.4]);bed=lambda p:.2+.01*p[:,0]+.02*p[:,1]
        g,r=integrate_gradient(phi,h,lo,hi,bed,orders=(4,8))
        reference=integrate(phi,h,lo,hi,bed,orders=(4,8))
        self.assertAlmostEqual(r['volume'],reference['volume'],places=12)
        self.assertAlmostEqual(float(g.sum()),-np.prod(hi-lo),places=12)
        self.assertEqual(r['unresolved_columns'],0)
        # Volume is invariant under positive rescaling of the implicit scalar.
        self.assertAlmostEqual(float(np.sum(g*phi)),0,places=12)

    def test_nodal_derivative_including_explicit_caps(self):
        h=np.array([.8,.6,.3]);z,y,x=np.indices((6,6,7));phi=(z+.5)*h[2]-1.72+.01*x
        lo=np.array([.7,.6]);hi=np.array([4.3,2.5]);bed=lambda p:np.zeros(len(p))
        g,r=integrate_gradient(phi,h,lo,hi,bed,orders=(6,8));self.assertGreater(r['upper_extrapolated_cap_volume'],0)
        direction=np.random.default_rng(31).normal(size=phi.shape);eps=1e-6
        a=integrate(phi+eps*direction,h,lo,hi,bed,orders=(6,8))['volume']
        b=integrate(phi-eps*direction,h,lo,hi,bed,orders=(6,8))['volume']
        self.assertAlmostEqual(float(np.sum(g*direction)),(a-b)/(2*eps),places=7)

    def test_fully_buried_surface_has_zero_sensitivity(self):
        z,y,x=np.indices((5,5,5));phi=z+.5-1.2
        g,r=integrate_gradient(phi,np.ones(3),[1,1],[3,3],lambda p:np.full(len(p),2.))
        self.assertEqual(r['volume'],0);np.testing.assert_array_equal(g,0)

    def test_zero_scalar_and_invalid_inputs_are_not_hidden(self):
        _,_,r=negative_length_gradient(np.zeros((3,1)),np.arange(3.),np.zeros(1),0,2)
        self.assertEqual(r['zero_endpoint_rays'],1)
        with self.assertRaises(ValueError):integrate_gradient(np.ones((4,4,4)),[1,0,1],[1,1],[2,2],lambda p:np.zeros(len(p)))


if __name__=='__main__':unittest.main()
