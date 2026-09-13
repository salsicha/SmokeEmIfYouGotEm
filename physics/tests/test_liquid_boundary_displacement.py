import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_boundary_displacement import compact_rows,project_rows,coupled_projection
from liquid_compatible_advection import sample_compact


class BoundaryDisplacementTest(unittest.TestCase):
    def test_rows_equal_actual_shared_interpolant(self):
        cells=np.array([8,9,10]);h=np.array([.5,.7,.3]);rng=np.random.default_rng(112)
        p=np.array([[3.2,4.4,3.1],[4.1,3.8,4.6]])*h
        n=np.array([[.6,0,.8],[0,1,0.]])
        field=rng.normal(size=(*cells[::-1],3));mobility=np.ones_like(field)
        i,w=compact_rows(p,n,cells,h,mobility)
        actual=np.sum(sample_compact(p,field.transpose(2,1,0,3),h)*n,axis=1)
        np.testing.assert_allclose(np.sum(field.ravel()[i]*w,axis=1),actual,atol=1e-14)

    def test_overlapping_rows_project_field_not_particle_positions(self):
        cells=np.array([8,8,8]);h=np.ones(3);p=np.array([[3.8,4,4],[4,4,4.]])
        n=np.tile([0,0,1.],(2,1));field=np.zeros((8,8,8,3));field[...,2]=-2
        i,w=compact_rows(p,n,cells,h,np.ones_like(field))
        result,dual,error=project_rows(field,i,w,np.zeros(2),sweeps=100)
        self.assertLess(error,1e-8)
        np.testing.assert_array_equal(field[...,2],-2)
        sampled=sample_compact(p,result.transpose(2,1,0,3),h)
        self.assertTrue((sampled[:,2]>=-1e-8).all())
        self.assertTrue((dual>=0).all())

    def test_fixed_support_and_incompatible_constraint(self):
        p=np.array([[4.,4.,4.]]);cells=np.array([8]*3);field=np.zeros((8,8,8,3))
        i,w=compact_rows(p,np.array([[0,0,1.]]),cells,np.ones(3),np.zeros_like(field))
        with self.assertRaises(ValueError):project_rows(field,i,w,np.ones(1))
        result,_,_=project_rows(field,i,w,np.zeros(1))
        np.testing.assert_array_equal(result,0)

    def test_incomplete_support_is_not_silently_clipped(self):
        with self.assertRaises(ValueError):compact_rows(np.array([[0,0,0.]]),np.array([[0,0,1.]]),np.array([8]*3),np.ones(3),np.ones((8,8,8,3)))

    def test_joint_density_and_off_grid_contact_constraints(self):
        from liquid_compatible_projection import constrain_velocity,divergence
        cells=np.array([8]*3);b=np.zeros((8,8,8,4));b[...,3]=2;b[2:6,2:6,2:6,3]=0
        target=np.zeros((8,8,8));target[3:5,3:5,3:5]=.2
        _,m,fluid=constrain_velocity(np.zeros((8,8,8,3)),b)
        points=np.array([[4,4,3.2],[4.3,4,3.2]]);normals=np.tile([0,0,1.],(2,1))
        i,w=compact_rows(points,normals,cells,np.ones(3),m)
        delta,report=coupled_projection(target,b,np.ones(3),i,w,np.zeros(2))
        self.assertTrue(report['converged'],report)
        np.testing.assert_allclose(divergence(delta,np.ones(3))[fluid],target[fluid],atol=1e-8)
        self.assertGreaterEqual(np.sum(delta.ravel()[i]*w,axis=1).min(),-1e-8)


if __name__=='__main__':unittest.main()
