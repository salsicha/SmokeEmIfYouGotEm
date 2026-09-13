import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_adaptive_terrain_volume import adaptive_bed_columns,integrate_gradient_terrain


class AdaptiveTerrainVolumeTest(unittest.TestCase):
    def test_cross_ray_clipping_conserves_original_error_budget(self):
        # phi=z-x, fixed bed=.87319 creates a derivative transition in X.
        z=np.arange(4)+.5;c=np.stack((z-.5,z-1.5,z-.5,z-1.5),axis=-1)[None,...]
        def bed(a,b):
            n=len(a)
            return np.arange(n),np.zeros(n),np.ones(n),np.full(n,.87319),np.full(n,.87319)
        args=(c,np.array([[0,0]]),np.array([[1.,1.]]),np.array([[.5,.5]]),np.ones(3),bed)
        v,g,d,r=adaptive_bed_columns(*args,max_depth=18)
        self.assertEqual(r['unresolved_columns'],0)
        self.assertLessEqual(d['volume_difference'][0],1e-4);self.assertLessEqual(d['gradient_difference'][0],1e-4)
        self.assertAlmostEqual(v[0,0],.5*(1.5-.87319)**2,places=7)
        self.assertAlmostEqual(g.sum(),-(1.5-.87319),places=12)
        # The explicit X bed-contact split resolves this discontinuity exactly.
        self.assertEqual(d['leaf_count'][0],1)

    def test_curved_contact_subdivides_and_depth_exhaustion_fails(self):
        z=np.arange(4)+.5;c=np.stack((z-.25,z-.75,z-.75,z-2.25),axis=-1)[None,...];height=.87319
        def bed(a,b):
            n=len(a)
            return np.arange(n),np.zeros(n),np.ones(n),np.full(n,height),np.full(n,height)
        args=(c,np.array([[0,0]]),np.array([[1.,1.]]),np.array([[.5,.5]]),np.ones(3),bed)
        controls=dict(orders=(2,4),column_tolerance=1e-6,gradient_tolerance=1e-6)
        v,g,d,r=adaptive_bed_columns(*args,max_depth=14,**controls)
        primitive=lambda x:.5625*x*x-1.5*height*x+.5*height*height*np.log(x)
        self.assertEqual(r['unresolved_columns'],0)
        self.assertAlmostEqual(v[0,0],primitive(1.5)-primitive(height/1.5),places=6)
        self.assertAlmostEqual(g.sum(),-(2.25-height-height*np.log(2.25/height)),places=5)
        self.assertLessEqual(d['volume_difference'][0],1e-6);self.assertLessEqual(d['gradient_difference'][0],1e-6)
        self.assertGreater(d['leaf_count'][0],1)
        _,_,d0,r0=adaptive_bed_columns(*args,max_depth=0,**controls)
        self.assertEqual(r0['unresolved_columns'],1);self.assertGreater(d0['gradient_difference'][0],1e-6)

    def test_planar_surface_needs_no_subdivision(self):
        z=np.arange(4)+.5;c=np.broadcast_to((z-1.21)[None,:,None],(1,4,4)).copy()
        def bed(a,b):
            n=len(a)
            return np.arange(n),np.zeros(n),np.ones(n),np.zeros(n),np.zeros(n)
        v,g,d,r=adaptive_bed_columns(c,np.array([[0,0]]),np.array([[1.,1.]]),np.array([[.5,.5]]),np.ones(3),bed)
        self.assertAlmostEqual(v[0,0],1.21,places=13);self.assertAlmostEqual(g.sum(),-1.,places=13)
        self.assertEqual(r['unresolved_columns'],0);self.assertEqual(d['leaf_count'][0],1)

    def test_full_grid_partial_edges_and_gradient_scatter(self):
        h=np.array([.3,.7,.2]);z,y,x=np.indices((8,5,6))
        phi=(z+.5)*h[2]-(.72+.03*(x+.5)*h[0]-.02*(y+.5)*h[1])
        def bed(a,b):
            n=len(a)
            return np.arange(n),np.zeros(n),np.ones(n),np.full(n,.1),np.full(n,.1)
        lo=np.array([.4,.9]);hi=np.array([1.4,2.6]);details={}
        g,r=integrate_gradient_terrain(phi,h,lo,hi,bed,diagnostics=details)
        mid=(hi+lo)/2;area=np.prod(hi-lo)
        self.assertAlmostEqual(r['volume'],area*(.62+.03*mid[0]-.02*mid[1]),places=12)
        self.assertAlmostEqual(g.sum(),-area,places=12);self.assertEqual(r['unresolved_columns'],0)
        self.assertEqual(len(details['unresolved_columns']),0)
        self.assertAlmostEqual(float(details['volume_by_column'][:,0].sum()),r['volume'],places=13)


if __name__=='__main__':unittest.main()
