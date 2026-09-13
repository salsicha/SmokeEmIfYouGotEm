import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_contact_dual import solve_contact_dual


def original(s,r,max_sweeps=30000,tolerance=1e-7):
    diagonal=np.diag(s);lam=np.zeros(len(r));residual=r.copy()
    for sweep in range(max_sweeps):
        for row in range(len(r)):
            if diagonal[row]<=0:continue
            updated=max(0,lam[row]+residual[row]/diagonal[row]);change=updated-lam[row]
            if change:lam[row]=updated;residual-=s[:,row]*change
        kkt=float(np.max(np.where(lam>0,abs(residual),np.maximum(residual,0)),initial=0))
        if kkt<=tolerance:break
    return lam,sweep+1,kkt


class ContactDualTest(unittest.TestCase):
    def test_matches_original_iteration_with_contiguous_columns(self):
        rng=np.random.default_rng(704);a=rng.normal(size=(48,60))
        s=a@a.T;r=rng.normal(size=48)
        expected,n,kkt=original(s,r);actual,report=solve_contact_dual(s,r)
        np.testing.assert_array_equal(actual,expected)
        self.assertEqual(report['dual_sweeps'],n)
        self.assertEqual(report['dual_kkt_error_cm'],kkt)
        self.assertTrue(report['converged'])

    def test_redundant_contacts_remain_unilateral(self):
        lam,r=solve_contact_dual([[1,1],[1,1]],[1,.5])
        np.testing.assert_array_equal(lam,[1,0]);self.assertTrue(r['converged'])

    def test_incompatible_fixed_contact_rejected(self):
        with self.assertRaisesRegex(ValueError,'incompatible'):solve_contact_dual([[0]],[1e-4])

    def test_empty_contact_set(self):
        lam,r=solve_contact_dual(np.empty((0,0)),np.empty(0))
        self.assertEqual(len(lam),0);self.assertTrue(r['converged'])

    def test_bounded_nonconvergence_is_not_accepted(self):
        _,r=solve_contact_dual([[2,1],[1,2]],[1,1],max_sweeps=1,tolerance=1e-12)
        self.assertFalse(r['converged'])

    def test_warm_start_recomputes_residual_for_changed_rhs(self):
        s=np.array([[2.,1],[1,2]])
        a,_=solve_contact_dual(s,[1,1]);before=a.copy()
        warm,report=solve_contact_dual(s,[1.1,1],initial=a)
        cold,other=solve_contact_dual(s,[1.1,1])
        self.assertTrue(report['converged']);self.assertTrue(other['converged'])
        np.testing.assert_allclose(warm,cold,atol=1e-7);np.testing.assert_array_equal(a,before)
        with self.assertRaises(ValueError):solve_contact_dual(s,[1,1],initial=[-1,0])


if __name__=='__main__':unittest.main()
