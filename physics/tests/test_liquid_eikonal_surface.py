import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_eikonal_surface import redistance


class EikonalSurfaceTest(unittest.TestCase):
    def test_affine_surface_distance_on_anisotropic_grid(self):
        # Pad the analytic plane so the finite-domain boundary condition does
        # not contaminate this unbounded-plane accuracy check. Converge this
        # fixture explicitly; the production-reference iteration cap is tested
        # separately against captured fields, not called analytically exact.
        z,y,x=np.meshgrid((np.arange(48)-16+.5)*.15,(np.arange(48)-16+.5)*.1,(np.arange(48)-16+.5)*.2,indexing='ij')
        phi=z+.2*x-.1*y-1.3
        sdf,_=redistance(phi,[.15,.1,.2],iterations=32)
        exact=np.clip(phi/np.sqrt(1.05),-.5,.5)
        interior=np.s_[16:32,20:28,20:28]
        np.testing.assert_allclose(sdf[interior],exact[interior],atol=1e-12)

    def test_scalar_scaling_does_not_change_surface(self):
        z,y,x=np.indices((12,12,12))*.1
        phi=(x-.5)**2+(y-.5)**2+(z-.5)**2-.3**2
        a,_=redistance(phi,[.1]*3)
        b,_=redistance(phi*100,[.1]*3)
        np.testing.assert_allclose(a,b,atol=1e-12)
        self.assertTrue(np.array_equal(a<=0,phi<=0))

    def test_empty_full_and_monotone_iteration(self):
        for sign in (-1,1):
            sdf,report=redistance(np.full((5,5,5),float(sign)),[.1]*3)
            np.testing.assert_allclose(sdf,sign*.5)
            self.assertEqual(report['seed_count'],0)
        phi=np.indices((10,10,10))[0]*.1-.47
        a,_=redistance(phi,[.1]*3,iterations=1)
        b,_=redistance(phi,[.1]*3,iterations=8)
        self.assertTrue((abs(b)<=abs(a)+1e-12).all())

    def test_invalid_parameters_rejected(self):
        for spacing,bandwidth,iterations in (([0,1,1],.5,8),([1,1,1],-.5,8),([1,1,1],.5,0)):
            with self.assertRaises(ValueError):
                redistance(np.ones((4,4,4)),spacing,bandwidth,iterations)


if __name__=='__main__':
    unittest.main()
