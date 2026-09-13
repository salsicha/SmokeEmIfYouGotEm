import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_represented_retry import represented_retry
from solve_liquid_particle_density import constrained_direction
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_mesh_sampling import grid_triangles
from liquid_swept_bed import swept_clearance


class RepresentedRetryTest(unittest.TestCase):
    @staticmethod
    def project(indices,direction):
        return direction,dict(converged=True)

    def test_only_collision_members_change_direction(self):
        points=np.array([[10000.,200.,3002.],[10002.,200.,3002.],[12000.,200.,3002.]])
        direction=np.array([[1.,0,0],[-1.,0,0],[5.,2.,0]])
        copy=points.copy()
        move,actual,report=represented_retry(points,direction,direction,np.eye(3),80,self.project)
        self.assertTrue(report['converged']);self.assertEqual(report['retried_particles'],2)
        np.testing.assert_array_equal(move[:2],direction[:2]/2)
        np.testing.assert_array_equal(move[2],direction[2])
        np.testing.assert_array_equal(points,copy)
        self.assertEqual(len(np.unique(actual,axis=0)),3)
        self.assertFalse(report['geometry_or_density_acceptance'])

    def test_stationary_particle_is_not_pushed_or_jittered(self):
        points=np.array([[10000.,200.,3002.],[10002.,200.,3002.]])
        direction=np.array([[2.,0,0],[0.,0,0]])
        move,actual,report=represented_retry(points,direction,direction,np.eye(3),80,self.project)
        self.assertTrue(report['converged']);np.testing.assert_array_equal(actual[1],points[1])
        np.testing.assert_array_equal(move[0],[1,0,0])

    def test_new_collision_group_is_checked_on_next_retry(self):
        points=np.array([[10000.,200.,3002.],[10002.,200.,3002.],[10001.,200.,3002.]])
        direction=np.array([[2.,0,0],[0.,0,0],[0.,0,0]])
        move,actual,report=represented_retry(points,direction,direction,np.eye(3),80,self.project)
        self.assertTrue(report['converged']);self.assertEqual(len(report['retries']),2)
        self.assertEqual(move[0,0],.5);self.assertEqual(len(np.unique(actual,axis=0)),3)

    def test_failed_or_exhausted_projection_is_not_accepted(self):
        p=np.array([[10000.,200.,3002.],[10002.,200.,3002.]])
        d=np.array([[1.,0,0],[-1.,0,0]])
        _,_,r=represented_retry(p,d,d,np.eye(3),80,self.project,max_retries=0)
        self.assertFalse(r['converged'])
        _,_,r=represented_retry(p,d,d,np.eye(3),80,lambda i,v:(v,dict(converged=False)))
        self.assertFalse(r['converged'])

    def test_existing_coincidence_or_unrepresented_input_rejected(self):
        p=np.array([[10000.,200.,3002.],[10000.,200.,3002.]])
        with self.assertRaises(ValueError):represented_retry(p,np.zeros_like(p),np.zeros_like(p),np.eye(3),80,self.project)
        p[1,0]=10000.123456789
        with self.assertRaises(ValueError):represented_retry(p,np.zeros_like(p),np.zeros_like(p),np.eye(3),80,self.project)

    def test_actual_valley_contact_qp_preserves_both_paths_and_identities(self):
        y,x=np.indices((5,5));x=x.astype(float)+98;y=-y.astype(float)
        mesh=RegisteredMeshSampler(dict(east_m=x,north_m=y,z_m=abs(x-100),triangles=grid_triangles(5,5),
            nominal_east_axis_m=x[0],nominal_north_axis_m=y[:,0]))
        p=np.array([[9999.,200.,3.],[10001.,200.,3.]])
        d=np.array([[2.,0,-4],[-2.,0,-4]]);h=np.full(3,50.)
        def project(indices,direction):
            return constrained_direction(p[indices],p[indices],direction,np.eye(3),h,np.zeros(3),
                np.full(3,20000.),mesh,np.full(len(indices),2.),native_positions=True)
        move,contact=project(np.arange(2),d)
        self.assertTrue(contact['converged'])
        # Both independent contact projections land at the same valley point.
        self.assertEqual(len(np.unique((p+move).astype('<f4'),axis=0)),1)
        move,actual,report=represented_retry(p,move,d,np.eye(3),np.linalg.norm(h),project)
        self.assertTrue(report['converged']);self.assertEqual(len(np.unique(actual,axis=0)),2)
        self.assertGreaterEqual(len(report['retries']),2)
        clearance,_,_=swept_clearance(mesh,p*[1,-1,1]/100,actual*[1,-1,1]/100)
        self.assertTrue(np.all(100*clearance>=2.-1e-6))


if __name__=='__main__':unittest.main()
