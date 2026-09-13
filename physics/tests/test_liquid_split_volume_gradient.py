import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_split_volume_gradient import intervals_at_roots,integrate_gradient_split
from liquid_surface_volume_gradient import integrate_gradient


class SplitVolumeGradientTest(unittest.TestCase):
    def test_distinct_close_roots_and_empty_intervals(self):
        a=np.array([[1.,1.,0.,2.]]);b=np.array([[-1.,-1.+1e-10,0.,3.]])
        rows,lo,hi=intervals_at_roots(a,b)
        self.assertEqual(len(rows),3);self.assertGreater(hi[1]-lo[1],0)
        self.assertLess(hi[1]-lo[1],1e-9);self.assertEqual(lo[0],0);self.assertEqual(hi[-1],1)

    def test_affine_surface_gradient_and_sloped_bed(self):
        h=np.array([.7,.4,.3]);z,y,x=np.indices((12,8,9));phi=(z+.5)*h[2]-(1.23+.04*(x+.5)*h[0]-.03*(y+.5)*h[1])
        lo=np.array([.8,.5]);hi=np.array([4.8,2.4]);bed=lambda p:.2+.01*p[:,0]+.02*p[:,1];details={}
        g,r=integrate_gradient_split(phi,h,lo,hi,bed,orders=(2,4,8),diagnostics=details)
        ref,rr=integrate_gradient(phi,h,lo,hi,bed,orders=(8,16))
        self.assertAlmostEqual(r['volume'],rr['volume'],places=12)
        self.assertAlmostEqual(g.sum(),-np.prod(hi-lo),places=12)
        self.assertEqual(r['unresolved_columns'],0);self.assertEqual(len(details['unresolved_columns']),0)

    def test_split_handles_changing_vertical_slopes(self):
        z,y,x=np.indices((8,5,6));phi=(z+.5-3.3)*(1+.4*z)+.6*y-.4*x
        bed=lambda p:np.zeros(len(p));h=np.ones(3);lo=[1,1];hi=[4,3]
        g,r=integrate_gradient_split(phi,h,lo,hi,bed,orders=(4,8,16),gradient_tolerance=1e-7)
        direction=np.random.default_rng(9).normal(size=phi.shape);eps=1e-5
        _,a=integrate_gradient_split(phi+eps*direction,h,lo,hi,bed,orders=(8,16),gradient_tolerance=1e-8)
        _,b=integrate_gradient_split(phi-eps*direction,h,lo,hi,bed,orders=(8,16),gradient_tolerance=1e-8)
        self.assertAlmostEqual(float(np.sum(g*direction)),(a['volume']-b['volume'])/(2*eps),places=6)
        self.assertEqual(r['unresolved_columns'],0)

    def test_caps_detached_layers_and_fixed_bed(self):
        z,y,x=np.indices((7,5,6));phi=np.ones(z.shape);phi[1]=-.3+.1*y[1];phi[5:]=-.2
        bed=lambda p:np.full(len(p),.6)
        g,r=integrate_gradient_split(phi,np.ones(3),[1,1],[4,3],bed,orders=(4,8,16))
        reference,rr=integrate_gradient(phi,np.ones(3),[1,1],[4,3],bed,orders=(16,32))
        self.assertAlmostEqual(r['volume'],rr['volume'],places=6)
        self.assertAlmostEqual(r['upper_extrapolated_cap_volume'],rr['upper_extrapolated_cap_volume'],places=10)
        self.assertGreater(r['volume'],0)


if __name__=='__main__':unittest.main()
