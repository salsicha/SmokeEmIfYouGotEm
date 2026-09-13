import sys
import importlib.util
from pathlib import Path
import unittest
import numpy as np
root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/'physics/scripts'),str(root/'tmp/south-fork-density-numerics')]
available=importlib.util.find_spec('scipy') is not None
if available:
    from liquid_contact_system import ContactSystem,unique_contact_rows
    from scipy import sparse
    from liquid_boundary_schur import solve,geometric_position_mobility
from liquid_boundary_displacement import compact_rows


@unittest.skipUnless(available,'Optional sparse reference dependency not installed')
class ContactSystemTest(unittest.TestCase):
    def fixture(self):
        b=np.zeros((8,8,8,4));b[...,3]=2;b[2:6,2:6,2:6,3]=0;b[2,3,3,3]=1
        t=np.zeros((8,8,8));t[3:5,3:5,3:5]=.2;m=geometric_position_mobility(b)
        p=np.array([[4,4,3.2],[3,4,3.4]])
        i,w=compact_rows(p,np.array([[.6,0,.8],[0,0,1.]]),[8]*3,[1]*3,m)
        return b,t,m,i,w,np.array([.05,.02])

    def test_appended_contact_cache_matches_full_reference(self):
        b,t,m,i,w,c=self.fixture();system=ContactSystem(b,[1]*3,m)
        _,first=system.solve(t,i[:1],w[:1],c[:1]);self.assertEqual(first['reused_schur_columns'],0)
        actual,report=system.solve(t,i,w,c);expected,old=solve(t,b,[1]*3,i,w,c,mobility=m)
        self.assertTrue(report['converged']);self.assertTrue(old['converged'])
        self.assertEqual(report['reused_schur_columns'],1)
        np.testing.assert_allclose(actual,expected,atol=1e-10)
        _,again=system.solve(t*.5,i,w,c)
        self.assertEqual(again['reused_schur_columns'],2)

    def test_changed_row_invalidates_cache_and_inputs_are_not_aliased(self):
        b,t,m,i,w,c=self.fixture();system=ContactSystem(b,[1]*3,m)
        system.solve(t,i,w,c);w*=.9
        actual,report=system.solve(t,i,w,c);expected,_=solve(t,b,[1]*3,i,w,c,mobility=m)
        self.assertEqual(report['reused_schur_columns'],0)
        np.testing.assert_allclose(actual,expected,atol=1e-10)

    def test_fixed_node_contact_rejected(self):
        b,t,m,i,w,c=self.fixture();system=ContactSystem(b,[1]*3,m)
        i[0,0]=((2*8+3)*8+3)*3;w[0,0]=1
        with self.assertRaisesRegex(ValueError,'fixed nodes'):system.solve(t,i,w,c)

    def test_empty_contacts_still_solve_density(self):
        b,t,m,i,w,c=self.fixture();actual,r=ContactSystem(b,[1]*3,m).solve(t,i[:0],w[:0],c[:0])
        expected,_=solve(t,b,[1]*3,i[:0],w[:0],c[:0],mobility=m)
        self.assertTrue(r['converged']);np.testing.assert_allclose(actual,expected,atol=1e-10)

    def test_only_exactly_identical_rows_share_strongest_bound(self):
        b=sparse.csr_matrix([[1.,0],[1,0],[1,1e-15],[1,0]])
        winners=unique_contact_rows(b,[.1,.3,.4,.2])
        np.testing.assert_array_equal(winners,[1,2])

    def test_duplicate_constraints_checked_in_full_and_cache_reused(self):
        b,t,m,i,w,c=self.fixture();system=ContactSystem(b,[1]*3,m)
        system.solve(t,i,w,c)
        ii=np.r_[i,i[:1]];ww=np.r_[w,w[:1]];cc=np.r_[c,c[:1]+1e-9]
        field,report=system.solve(t,ii,ww,cc)
        self.assertTrue(report['converged'],report)
        self.assertEqual(report['exact_duplicate_rows'],1)
        self.assertEqual(report['reused_schur_columns'],2)
        self.assertEqual(report['warm_contact_rows'],2)
        actual=np.sum(field.ravel()[ii]*ww,axis=1)
        self.assertTrue(np.all(actual>=cc-1e-7))

    def test_incompatible_attempt_does_not_corrupt_warm_cache(self):
        b,t,m,i,w,c=self.fixture();system=ContactSystem(b,[1]*3,m)
        system.solve(t,i,w,c)
        with self.assertRaisesRegex(ValueError,'incompatible'):system.solve(t,i[:1],np.zeros_like(w[:1]),[.1])
        _,r=system.solve(t,i,w,c)
        self.assertTrue(r['converged']);self.assertEqual(r['reused_schur_columns'],2)

    def test_relaxed_iteration_preserves_full_density_and_contact_solution(self):
        b,t,m,i,w,c=self.fixture()
        expected,old=ContactSystem(b,[1]*3,m).solve(t,i,w,c)
        actual,r=ContactSystem(b,[1]*3,m,relaxation=1.8).solve(t,i,w,c)
        self.assertTrue(old['converged']);self.assertTrue(r['converged'])
        np.testing.assert_allclose(expected,actual,atol=2e-7)
        self.assertLessEqual(r['full_contact_kkt_error_cm'],1e-7)

    def test_refined_system_preserves_all_original_constraints(self):
        b,t,m,i,w,c=self.fixture()
        field,r=ContactSystem(b,[1]*3,m,relaxation=1.8,active_set=True).solve(t,i,w,c,max_sweeps=1)
        self.assertTrue(r['converged'],r);self.assertTrue(r['active_set_refinement'])
        self.assertLessEqual(r['full_contact_kkt_error_cm'],1e-7)
        self.assertTrue(np.all(np.sum(field.ravel()[i]*w,axis=1)>=c-1e-7))


if __name__=='__main__':unittest.main()
