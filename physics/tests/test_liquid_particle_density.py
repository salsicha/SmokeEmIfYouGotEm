import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_particle_density import objective,descent_direction
from solve_liquid_particle_density import constrained_direction
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_mesh_sampling import grid_triangles
from liquid_swept_bed import swept_clearance
from liquid_particle_contacts import project_contacts


class ParticleDensityTest(unittest.TestCase):
    def fixture(self):
        p=np.array([[2.12,3.24,4.17],[2.23,3.11,4.29],[2.31,3.33,4.21]])
        h=np.array([.8,1.1,1.3]);cells=np.array([8,7,6])
        s=np.zeros(cells[::-1]);s[2:4,2:4,1:4]=.57
        return p,cells,h,np.array([2.1,2.3,2.2]),s

    def test_exact_particle_gradient_in_anisotropic_partial_solid_support(self):
        p,c,h,v,s=self.fixture();r=objective(p,c,h,v,s)
        self.assertGreater(r['energy'],0);eps=1e-6
        for i in range(len(p)):
            for axis in range(3):
                a=p.copy();b=p.copy();a[i,axis]+=eps;b[i,axis]-=eps
                numerical=(objective(a,c,h,v,s,derivatives=False)['energy']-
                           objective(b,c,h,v,s,derivatives=False)['energy'])/(2*eps)
                self.assertAlmostEqual(r['gradient'][i,axis],numerical,places=8)

    def test_diagonal_matches_density_jacobian(self):
        p,c,h,v,s=self.fixture();r=objective(p,c,h,v,s);active=r['particle_density']+s>1;eps=1e-6
        for i in range(len(p)):
            for axis in range(3):
                a=p.copy();b=p.copy();a[i,axis]+=eps;b[i,axis]-=eps
                jac=(objective(a,c,h,v,s,derivatives=False)['particle_density']-
                     objective(b,c,h,v,s,derivatives=False)['particle_density'])/(2*eps)
                self.assertAlmostEqual(r['gauss_newton_diagonal'][i,axis],float(np.sum(jac[active]**2)),places=8)

    def test_all_particle_volume_survives_scatter_and_descent(self):
        p,c,h,v,s=self.fixture();r=objective(p,c,h,v,s);direction=descent_direction(r,h)
        self.assertLess(float(np.sum(r['gradient']*direction)),0)
        self.assertLessEqual(np.linalg.norm(direction/h,axis=1).max(),.25+1e-15)
        after=objective(p+.05*direction,c,h,v,s)
        self.assertLess(after['energy'],r['energy'])
        self.assertAlmostEqual(after['deposited_volume'],v.sum(),places=12)
        self.assertAlmostEqual(r['deposited_volume'],v.sum(),places=12)

    def test_underfilled_free_surface_is_not_attracted(self):
        p,c,h,v,s=self.fixture();r=objective(p,c,h,v*.001,np.zeros_like(s))
        self.assertEqual(r['energy'],0);self.assertTrue(np.all(r['gradient']==0))
        self.assertTrue(np.all(descent_direction(r,h)==0))

    def test_solid_overlap_is_not_excluded_by_grid_phase(self):
        p,c,h,v,s=self.fixture();r=objective(p,c,h,v,s)
        # Only a bed fraction enters the equation; no phase array can mask it.
        no_bed=objective(p,c,h,v,np.zeros_like(s))
        self.assertGreater(r['energy'],no_bed['energy'])
        self.assertFalse(np.array_equal(r['gradient'],no_bed['gradient']))

    def test_off_grid_volume_and_invalid_support_are_rejected(self):
        p,c,h,v,s=self.fixture();p[0]=0
        with self.assertRaises(ValueError):objective(p,c,h,v,s)
        p,c,h,v,s=self.fixture();s[0,0,0]=1.1
        with self.assertRaises(ValueError):objective(p,c,h,v,s)
        with self.assertRaises(ValueError):objective(p,c+.1,h,v,np.zeros_like(s))

    def contact_fixture(self,ridge=False):
        y,x=np.indices((5,5));x=x.astype(float);y=-y.astype(float)
        z=np.maximum(0,1-abs(x-2)) if ridge else np.zeros_like(x)
        return RegisteredMeshSampler(dict(east_m=x,north_m=y,z_m=z,triangles=grid_triangles(5,5),
            nominal_east_axis_m=x[0],nominal_north_axis_m=y[:,0]))

    def test_particle_contact_projection_preserves_bed_and_outer_box(self):
        mesh=self.contact_fixture();p=np.array([[100.,200.,2.],[250.,200.,100.]])
        d=np.array([[0.,0.,-20.],[100.,0.,0.]])
        move,report=constrained_direction(p,p,d,np.eye(3),np.array([50.,50.,30.]),
            np.array([50.,50.,0.]),np.array([300.,350.,200.]),mesh,np.array([2.,2.]))
        self.assertTrue(report['converged'])
        np.testing.assert_allclose(move,[[0,0,0],[50,0,0]],atol=1e-10)
        self.assertLessEqual(np.linalg.norm(move[1]),np.linalg.norm(d[1]))

    def test_particle_contact_projection_catches_intermediate_ridge(self):
        mesh=self.contact_fixture(True);p=np.array([[100.,200.,60.]])
        d=np.array([[200.,0.,0.]])
        move,report=constrained_direction(p,p,d,np.eye(3),np.full(3,50.),
            np.full(3,50.),np.array([350.,350.,250.]),mesh,np.array([2.]))
        self.assertTrue(report['converged']);self.assertGreater(report['constraints'],0)
        clearance,_,_=swept_clearance(mesh,p*[1,-1,1]/100,(p+move)*[1,-1,1]/100)
        self.assertGreaterEqual(clearance[0],.02-1e-8)
        self.assertGreater(move[0,2],0)

    def test_particle_contact_projection_does_not_accept_exhausted_geometry(self):
        mesh=self.contact_fixture();p=np.array([[100.,200.,2.]])
        _,report=constrained_direction(p,p,np.array([[0.,0.,-20.]]),np.eye(3),np.full(3,50.),
            np.zeros(3),np.full(3,350.),mesh,np.array([2.]),iterations=1)
        self.assertFalse(report['converged'])

    def test_nearly_parallel_contacts_and_separate_particles(self):
        base=np.array([[2.,-1.,0.],[1.,2.,3.]])
        indices=np.array([[0,1,2],[0,1,2],[3,4,5]])
        weights=np.array([[-1.,.001,0.],[-1.,-.001,0.],[0.,0.,-1.]])
        out,report=project_contacts(base,indices,weights,np.array([0.,0.,-1.]))
        self.assertLessEqual(report['maximum_constraint_violation_cm'],1e-7)
        self.assertAlmostEqual(out[1,2],1.);self.assertAlmostEqual(out[0,0],-.000997999002001,places=10)
        np.testing.assert_allclose(out[1,:2],base[1,:2])

    def test_redundant_planes_preserve_strongest_and_infeasible_rejects(self):
        indices=np.tile([0,1,2],(3,1));w=np.array([[1.,0,0],[1.,0,0],[0.,1.,0]])
        out,_=project_contacts(np.array([[-3.,-4.,5.]]),indices,w,np.array([1.,2.,0.]))
        np.testing.assert_allclose(out,[[2.,0.,5.]],atol=1e-12)
        with self.assertRaises(ValueError):project_contacts(np.zeros((1,3)),indices[:2],
            np.array([[1.,0,0],[-1.,0,0]]),np.ones(2))


if __name__=='__main__':unittest.main()
