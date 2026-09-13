import sys
import importlib.util
from pathlib import Path
import unittest
import numpy as np
root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/'physics/scripts'),str(root/'tmp/south-fork-density-numerics')]
available=importlib.util.find_spec('scipy') is not None
if available:from liquid_boundary_schur import solve,geometric_position_mobility
from liquid_boundary_displacement import compact_rows
from liquid_compatible_projection import constrain_velocity,divergence


@unittest.skipUnless(available,'Optional sparse CPU reference dependency not installed')
class BoundarySchurTest(unittest.TestCase):
    def fixture(self):
        b=np.zeros((8,8,8,4));b[...,3]=2;b[2:6,2:6,2:6,3]=0
        target=np.zeros((8,8,8));target[3:5,3:5,3:5]=.2
        _,m,fluid=constrain_velocity(np.zeros((8,8,8,3)),b)
        p=np.array([[4,4,3.2],[4,4,3.2]])
        i,w=compact_rows(p,np.tile([0,0,1.],(2,1)),np.array([8]*3),np.ones(3),m)
        return b,target,i,w,fluid

    def test_dependent_contacts_are_unilateral_not_forced_equal(self):
        b,t,i,w,f=self.fixture()
        delta,r=solve(t,b,np.ones(3),i,w,np.array([0.,-.1]))
        self.assertTrue(r['converged'],r)
        self.assertEqual(r['active_contact_rows'],1)
        np.testing.assert_allclose(divergence(delta,np.ones(3))[f],t[f],atol=1e-11)
        self.assertGreaterEqual(np.sum(delta.ravel()[i[0]]*w[0]),-1e-10)

    def test_nonbinding_contact_adds_no_artificial_force(self):
        b,t,i,w,f=self.fixture()
        delta,r=solve(t,b,np.ones(3),i,w,np.array([-100.,-100.]))
        self.assertTrue(r['converged'],r);self.assertEqual(r['active_contact_rows'],0)
        np.testing.assert_allclose(divergence(delta,np.ones(3))[f],t[f],atol=1e-11)

    def test_exact_contact_mobility_does_not_free_solid_nodes(self):
        b,t,i,w,f=self.fixture();b[2,3,3,3]=1
        m=geometric_position_mobility(b)
        np.testing.assert_array_equal(m[2,3,3],0)
        np.testing.assert_array_equal(m[3,3,3],1)
        _,old,_=constrain_velocity(np.zeros_like(m),b)
        self.assertEqual(old[3,3,3,2],0)

    def test_geometric_mobility_solves_density_and_oblique_contact_together(self):
        b,t,_,_,_=self.fixture();b[2,3,3,3]=1
        m=geometric_position_mobility(b);f=np.rint(b[...,3])==0
        p=np.array([[4.,4.,3.2]])
        i,w=compact_rows(p,np.array([[.6,0.,.8]]),np.array([8]*3),np.ones(3),m)
        delta,r=solve(t,b,np.ones(3),i,w,np.array([.05]),mobility=m)
        self.assertTrue(r['converged'],r)
        np.testing.assert_allclose(divergence(delta,np.ones(3))[f],t[f],atol=1e-10)
        np.testing.assert_array_equal(delta[2,3,3],0)
        self.assertGreaterEqual(np.sum(delta.ravel()[i[0]]*w[0]),.05-1e-10)

    def test_invalid_target_and_mobility_rejected(self):
        b,t,i,w,f=self.fixture()
        with self.assertRaises(ValueError):solve(t,b,[0,1,1],i,w,[0,0])
        bad=t.copy();bad[0,0,0]=1
        with self.assertRaises(ValueError):solve(bad,b,np.ones(3),i,w,[0,0])
        with self.assertRaises(ValueError):solve(t,b,np.ones(3),i,w,[0,0],mobility=np.full((8,8,8,3),.5))


if __name__=='__main__':unittest.main()
