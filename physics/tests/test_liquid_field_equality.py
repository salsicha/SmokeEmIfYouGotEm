import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_field_equality import project_field_equality


class FieldEqualityTest(unittest.TestCase):
    def test_equality_and_wall_share_one_field(self):
        v=np.array([-2.,0.,5.]);a=np.array([1.,1.,0.])
        field,r=project_field_equality(v,np.array([[0]]),np.array([[1.]]),np.array([1.]),a,0.)
        self.assertTrue(r['converged']);np.testing.assert_allclose(field,[1,-1,5],atol=1e-7)
        self.assertLessEqual(r['equality_error'],1e-7)

    def test_no_contact_exact_projection(self):
        v=np.array([1.,2.,3.]);a=np.array([2.,-1.,.5]);rhs=7.
        field,r=project_field_equality(v,np.empty((0,1),int),np.empty((0,1)),np.empty(0),a,rhs)
        expected=v+a*(rhs-a@v)/(a@a);np.testing.assert_allclose(field,expected,atol=1e-13)
        self.assertTrue(r['converged'])

    def test_incompatible_no_sensitivity_rejected(self):
        with self.assertRaises(ValueError):project_field_equality(np.ones(3),np.empty((0,1),int),np.empty((0,1)),np.empty(0),np.zeros(3),1.)

    def test_exact_duplicate_contact_does_not_double_strength(self):
        field,r=project_field_equality(np.array([-2.,0.]),np.array([[0],[0]]),np.ones((2,1)),np.array([1.,1.]),np.ones(2),0.)
        self.assertTrue(r['converged']);np.testing.assert_allclose(field,[1,-1],atol=1e-7)


if __name__=='__main__':unittest.main()
