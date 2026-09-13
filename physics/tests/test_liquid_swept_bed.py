import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_mesh_sampling import grid_triangles
from liquid_swept_bed import swept_clearance,swept_contact_planes


def fixture(ridge=False):
    y,x=np.indices((5,5));x=x.astype(float);y=-y.astype(float)
    z=np.maximum(0,1-abs(x-2)) if ridge else .2*x+.3*y
    return RegisteredMeshSampler(dict(east_m=x,north_m=y,z_m=z,triangles=grid_triangles(5,5),
        nominal_east_axis_m=x[0],nominal_north_axis_m=y[:,0]))


class SweptBedTest(unittest.TestCase):
    def test_ridge_penetration_between_safe_endpoints(self):
        mesh=fixture(True);a=np.array([[1.,-2.,.6]]);b=np.array([[3.,-2.,.6]])
        self.assertGreater(a[0,2]-mesh.sample(a[0,0],a[0,1]),0)
        self.assertGreater(b[0,2]-mesh.sample(b[0,0],b[0,1]),0)
        clearance,t,faces=swept_clearance(mesh,a,b)
        np.testing.assert_allclose(clearance,[-.4],atol=1e-14)
        np.testing.assert_allclose(t,[.5],atol=1e-14);self.assertTrue((faces>=0).all())

    def test_planar_and_vertical_paths(self):
        mesh=fixture();a=np.array([[1.,-1.,1.],[2,-2,1.]])
        b=np.array([[3.,-3.,.4],[2,-2,.3]])
        result,_,_=swept_clearance(mesh,a,b)
        expected=np.minimum(a[:,2]-mesh.sample(a[:,0],a[:,1]),b[:,2]-mesh.sample(b[:,0],b[:,1]))
        np.testing.assert_allclose(result,expected,atol=1e-14)

    def test_stationary_paths_on_edges(self):
        mesh=fixture(True);a=np.array([[2.,-2.,1.02],[1.,-2.,.02]])
        actual,_,_=swept_clearance(mesh,a,a)
        np.testing.assert_allclose(actual,[.02,.02],atol=1e-14)

    def test_no_off_mesh_or_long_segment_fallback(self):
        mesh=fixture();a=np.array([[.1,-2,1.]])
        with self.assertRaises(ValueError):swept_clearance(mesh,a,a)
        with self.assertRaises(ValueError):swept_clearance(mesh,np.array([[.6,-2,1.]]),np.array([[3.4,-2,1.]]),maximum_nominal_span=1)

    def test_swept_contact_row_rejects_ridge_crossing(self):
        mesh=fixture(True);p=np.array([[100.,200.,60.]]);d=np.array([[200.,0.,0.]])
        selected,jacobian,lower,report,fraction,faces=swept_contact_planes(mesh,p,d,np.eye(3),np.array([2.]))
        np.testing.assert_array_equal(selected,[0]);np.testing.assert_allclose(fraction,[.5])
        self.assertLess(float(jacobian[0]@d[0]),lower[0])
        self.assertEqual(report['particles_with_swept_bed_penetration'],1)
        self.assertEqual(report['edge_visibility_contacts'],1)
        self.assertEqual(lower[0],0.)
        # At the detected half-time, an 84 cm full displacement lifts the
        # particle from 60 to 102 cm, precisely the required ridge clearance.
        fixed=d.copy();fixed[0,2]=84
        np.testing.assert_allclose(jacobian[0]@fixed[0],lower[0],atol=1e-12)
        # The same row remains valid when the crossing time changes.
        np.testing.assert_allclose(jacobian[0]@(2*fixed[0]),lower[0],atol=1e-12)

    def test_clearance_at_start_cannot_be_repaired_by_future_motion(self):
        mesh=fixture(True)
        with self.assertRaisesRegex(ValueError,'Initial particle'):
            swept_contact_planes(mesh,np.array([[200.,200.,90.]]),np.array([[0.,0.,50.]]),np.eye(3),np.array([2.]))


if __name__=='__main__':unittest.main()
