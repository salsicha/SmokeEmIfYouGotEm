import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_contact_dual import solve_contact_dual
from liquid_contact_psor import solve_contact_psor


class ContactPSORTest(unittest.TestCase):
    def test_unit_relaxation_matches_current_solver(self):
        rng=np.random.default_rng(412);a=rng.normal(size=(24,32));s=a@a.T;r=rng.normal(size=24)
        expected,old=solve_contact_dual(s,r);actual,new=solve_contact_psor(s,r,relaxation=1.)
        np.testing.assert_array_equal(expected,actual);self.assertEqual(old['dual_sweeps'],new['dual_sweeps'])

    def test_near_parallel_constraints_accelerate_without_changing_answer(self):
        s=np.array([[1.,.999],[.999,1.]]);r=np.array([1.,1.])
        expected,old=solve_contact_dual(s,r)
        actual,new=solve_contact_psor(s,r,relaxation=1.8)
        self.assertTrue(old['converged']);self.assertTrue(new['converged'])
        self.assertLess(new['dual_sweeps'],old['dual_sweeps'])
        np.testing.assert_allclose(s@expected,s@actual,atol=2e-7)

    def test_original_unilateral_bounds_still_hold(self):
        s=np.array([[1.,1.],[1.,1.]])
        lam,r=solve_contact_psor(s,[1,.5],relaxation=1.9)
        self.assertTrue(r['converged']);self.assertTrue(np.all(lam>=0))
        np.testing.assert_allclose(lam,[1,0],atol=1e-7)

    def test_invalid_relaxation_or_fixed_system_rejected(self):
        for omega in (0,2,np.nan):
            with self.assertRaises(ValueError):solve_contact_psor([[1]],[1],relaxation=omega)
        with self.assertRaises(ValueError):solve_contact_psor([[0]],[1])


if __name__=='__main__':unittest.main()
