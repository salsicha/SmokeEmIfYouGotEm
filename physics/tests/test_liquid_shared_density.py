import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_shared_density import compact_adjoint,shared_direction,constrained_field
from liquid_compatible_advection import sample_compact
from liquid_particle_density import objective
from liquid_correction_map import inverse_map
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_mesh_sampling import grid_triangles
from audit_liquid_coincident_particles import coincident_rows


class SharedDensityTest(unittest.TestCase):
    def fixture(self):
        h=np.array([.8,1.1,1.3]);cells=np.array([9,8,7])
        p=np.array([[3.12,3.84,4.17],[3.23,3.91,4.29],[3.31,3.73,4.21]])
        m=np.ones((*cells[::-1],3));m[2:4,2:4,1:4]=0
        solid=np.zeros(cells[::-1]);solid[2:4,2:4,1:4]=.57
        return p,cells,h,m,solid

    def test_adjoint_equals_actual_compact_interpolation(self):
        p,c,h,m,s=self.fixture();rng=np.random.default_rng(53)
        grid=rng.normal(size=m.shape)*m;v=rng.normal(size=p.shape)
        g=compact_adjoint(p,v,c,h,m,batch_size=2)
        self.assertAlmostEqual(float(np.sum(g*grid)),float(np.sum(v*sample_compact(p,grid.transpose(2,1,0,3),h))),places=13)
        np.testing.assert_array_equal(g[m==0],0)

    def test_chain_rule_all_density_nodes_anisotropic_partial_solid(self):
        p,c,h,m,s=self.fixture();volumes=np.array([2.1,2.3,2.2]);r=objective(p,c,h,volumes,s)
        self.assertGreater(r['energy'],0)
        g=compact_adjoint(p,r['gradient'],c,h,m)
        rng=np.random.default_rng(11);field=rng.normal(size=m.shape)*m
        move=sample_compact(p,field.transpose(2,1,0,3),h);eps=1e-6
        numerical=(objective(p+eps*move,c,h,volumes,s)['energy']-objective(p-eps*move,c,h,volumes,s)['energy'])/(2*eps)
        self.assertAlmostEqual(float(np.sum(g*field)),numerical,places=8)

    def test_descent_preserves_volumes_and_has_same_invertible_map(self):
        p,c,h,m,s=self.fixture();v=np.array([2.1,2.3,2.2]);r=objective(p,c,h,v,s)
        field,report=shared_direction(p,r['gradient'],c,h,m,max_cells=.02)
        self.assertLess(report['directional_derivative'],0)
        self.assertLessEqual(report['maximum_particle_displacement_cells'],.02+1e-15)
        moved=p+sample_compact(p,field.transpose(2,1,0,3),h)
        after=objective(moved,c,h,v,s)
        self.assertLess(after['energy'],r['energy']);self.assertAlmostEqual(after['deposited_volume'],v.sum(),places=12)
        inverse,valid,proof=inverse_map(moved,field,h,tolerance=1e-10)
        self.assertTrue(valid.all());np.testing.assert_allclose(inverse,p,atol=1e-10,rtol=0)

    def test_shared_contact_affects_other_particles_without_pushout(self):
        y,x=np.indices((5,5));x=x.astype(float);y=-y.astype(float)
        mesh=RegisteredMeshSampler(dict(east_m=x,north_m=y,z_m=np.full_like(x,1.48),triangles=grid_triangles(5,5),
            nominal_east_axis_m=x[0],nominal_north_axis_m=y[:,0]))
        p=np.array([[180.,200.,150.],[185.,202.,160.]])
        h=np.full(3,50.);m=np.ones((9,9,9,3));desired=np.zeros_like(m);desired[...,2]=-20.
        field,report=constrained_field(p,p,desired,np.eye(3),h,np.full(3,100.),np.full(3,350.),mesh,np.array([2.,2.]),m)
        self.assertTrue(report['converged']);self.assertGreater(report['constraints'],0)
        move=sample_compact(p,field.transpose(2,1,0,3),h)
        self.assertGreaterEqual(move[0,2],-1e-7)
        self.assertGreater(move[1,2],-10.)  # Same grid correction influences its neighbor.
        self.assertFalse(report['independent_particle_correction'])

    def test_reject_bad_mobility_support_and_fractional_grid(self):
        p,c,h,m,s=self.fixture()
        with self.assertRaises(ValueError):compact_adjoint(p,p,c+.1,h,m)
        m[0,0,0]=.5
        with self.assertRaises(ValueError):compact_adjoint(p,p,c,h,m)
        m[:]=1;p[0]=0
        with self.assertRaises(ValueError):compact_adjoint(p,p,c,h,m)

    def test_native_coincident_pair_cannot_be_separated_by_shared_map(self):
        p,c,h,m,s=self.fixture();p[1]=p[0]
        groups=coincident_rows(p);self.assertEqual(len(groups),1)
        np.testing.assert_array_equal(groups[0],[0,1])
        field=np.random.default_rng(3).normal(size=m.shape)*.01
        moved=p+sample_compact(p,field.transpose(2,1,0,3),h)
        np.testing.assert_array_equal(moved[0],moved[1])
        self.assertEqual(len(coincident_rows(moved)),1)

    def test_coincidence_detector_is_exact_not_distance_based(self):
        p=np.array([[1.,2.,3.],[np.nextafter(1.,2.),2.,3.]])
        self.assertEqual(coincident_rows(p),[])
        with self.assertRaises(ValueError):coincident_rows(np.full((1,3),np.nan))


if __name__=='__main__':unittest.main()
