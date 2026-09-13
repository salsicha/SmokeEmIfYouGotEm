import sys
import importlib.util
from pathlib import Path
import unittest
import numpy as np
root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/'physics/scripts'),str(root/'tmp/south-fork-density-numerics')]
available=importlib.util.find_spec('scipy') is not None
if available:from liquid_contact_active_set import polish_contact_dual
from liquid_contact_dual import solve_contact_dual


@unittest.skipUnless(available,'Optional sparse reference dependency not installed')
class ContactActiveSetTest(unittest.TestCase):
    def test_nearly_parallel_contacts(self):
        s=np.array([[1.,.999999],[.999999,1.]])
        lam,r=polish_contact_dual(s,[1.,.9999999],[1.,0.])
        self.assertTrue(r['converged'],r)
        np.testing.assert_allclose(s@lam,[1.,.9999999],atol=1e-12)
        self.assertTrue((lam>=0).all())

    def test_rank_deficient_linear_part_moves_to_bound(self):
        lam,r=polish_contact_dual([[1.,1],[1,1]],[1,.5],[.5,.5])
        self.assertTrue(r['converged'],r);self.assertGreaterEqual(r['active_set_rank_deficient_steps'],1)
        np.testing.assert_allclose(lam,[1,0],atol=1e-12)

    def test_contradictory_contacts_are_not_regularized(self):
        _,r=polish_contact_dual([[1.,-1],[-1,1]],[1,1],[0,0])
        self.assertFalse(r['converged']);self.assertIn('incompatible',r['active_set_failure'])

    def test_random_system_matches_coordinate_reference(self):
        rng=np.random.default_rng(861);a=rng.normal(size=(32,40));s=a@a.T;r=rng.normal(size=32)
        cold,old=solve_contact_dual(s,r);warm,_=solve_contact_dual(s,r,max_sweeps=3)
        actual,new=polish_contact_dual(s,r,warm)
        self.assertTrue(old['converged']);self.assertTrue(new['converged'],new)
        np.testing.assert_allclose(s@actual,s@cold,atol=2e-7)

    def test_invalid_start_and_bounded_nonconvergence(self):
        with self.assertRaises(ValueError):polish_contact_dual([[1]],[1],[-1])
        _,r=polish_contact_dual([[2,1],[1,2]],[1,1],[0,0],max_pivots=1)
        self.assertFalse(r['converged'])


if __name__=='__main__':unittest.main()
