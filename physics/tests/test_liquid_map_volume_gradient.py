import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_map_volume_gradient import map_volume_gradient
from liquid_surface_volume_gradient import integrate_gradient
from liquid_interface_volume import integrate
from liquid_correction_map import transport_interface


class MapVolumeGradientTest(unittest.TestCase):
    def test_full_inverse_scalar_volume_chain_rule(self):
        h=np.array([.7,1.1,.9]);z,y,x=np.indices((10,10,10))
        phi=(z+.5)*h[2]-4.13+.03*x+.006*y*y
        selected=np.zeros(phi.shape,bool);selected[2:-2,2:-2,2:-2]=True
        mobility=np.repeat(selected[...,None],3,axis=-1).astype(float)
        rng=np.random.default_rng(82);delta=rng.uniform(.02,.05,size=mobility.shape)*mobility*h
        current,proof=transport_interface(phi,delta,h,selected,tolerance=1e-11);self.assertTrue(proof['candidate_valid'])
        lo=np.array([2.7,2.7])*h[:2];hi=np.array([6.2,6.2])*h[:2];bed=lambda p:np.full(len(p),.5)
        scalar_g,_=integrate_gradient(current,h,lo,hi,bed,orders=(4,8),gradient_tolerance=1e-8)
        field_g,report=map_volume_gradient(phi,delta,h,selected,scalar_g,mobility)
        direction=rng.normal(size=delta.shape)*mobility*.03*h;eps=1e-4
        a,pa=transport_interface(phi,delta+eps*direction,h,selected,tolerance=1e-11)
        b,pb=transport_interface(phi,delta-eps*direction,h,selected,tolerance=1e-11)
        self.assertTrue(pa['candidate_valid'] and pb['candidate_valid'])
        va=integrate(a,h,lo,hi,bed,orders=(4,8))['volume'];vb=integrate(b,h,lo,hi,bed,orders=(4,8))['volume']
        self.assertAlmostEqual(float(np.sum(field_g*direction)),(va-vb)/(2*eps),places=7)
        self.assertEqual(report['departures_on_scalar_knots'],0)
        np.testing.assert_array_equal(field_g[mobility==0],0)

    def test_no_selected_gradient_does_not_invent_volume_force(self):
        phi=np.ones((8,8,8));delta=np.zeros((*phi.shape,3));selected=np.zeros_like(phi,dtype=bool)
        g,r=map_volume_gradient(phi,delta,np.ones(3),selected,np.ones_like(phi),np.ones_like(delta))
        np.testing.assert_array_equal(g,0);self.assertEqual(r['nonzero_selected_scalar_gradients'],0)


if __name__=='__main__':unittest.main()
