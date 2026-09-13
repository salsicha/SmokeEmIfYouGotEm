import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_edge_visibility import edge_visibility_planes


class EdgeVisibilityTest(unittest.TestCase):
    def test_ridge_constraint_is_independent_of_crossing_time(self):
        p=np.array([[1.,0.,.6],[1.,0.,.6]])
        d=np.array([[2.,0.,.84],[4.,0.,1.68]])
        a=np.array([[2.,-1.,1.],[2.,-1.,1.]]);b=a+np.array([0,2,0])
        n,valid,t,_=edge_visibility_planes(p,d,a,b,np.array([.02,.02]))
        self.assertTrue(valid.all());np.testing.assert_allclose(t,[.5,.25])
        np.testing.assert_array_equal(n[0],n[1]);np.testing.assert_allclose(np.sum(n*d,axis=1),0,atol=1e-14)
        d[:,2]-=.1
        self.assertTrue((np.sum(n*d,axis=1)<0).all())

    def test_raised_sloping_edge_has_correct_clearance_sign(self):
        p=np.array([[0.,0.,.3]]);a=np.array([[1.,-1.,.5]]);b=np.array([[1.,1.,1.5]])
        for rise in (.5,1.,1.5):
            d=np.array([[2.,.2,rise]])
            n,valid,t,u=edge_visibility_planes(p,d,a,b,np.array([.02]))
            self.assertTrue(valid[0])
            actual=p[:,2]+t*d[:,2]-(a[:,2]+u*(b[:,2]-a[:,2]))-.02
            predicted=t*np.sum(n*d,axis=1)/n[:,2]
            np.testing.assert_allclose(predicted,actual,atol=1e-14)

    def test_parallel_and_outside_edge_intersections_are_not_used(self):
        p=np.array([[0.,0.,1.],[0.,3.,1.]])
        d=np.array([[0.,1.,0.],[2.,0.,0.]])
        a=np.array([[1.,-1.,0.],[1.,-1.,0.]]);b=a+np.array([0,2,0])
        _,valid,_,_=edge_visibility_planes(p,d,a,b,np.zeros(2))
        self.assertFalse(valid.any())


if __name__=='__main__':unittest.main()
