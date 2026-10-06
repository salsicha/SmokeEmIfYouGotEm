from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tmp/south-fork-geospatial-deps'),str(ROOT/'physics/scripts')]
import numpy as np
from register_captured_rock_vertices import oriented_quad_triangles
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_mesh_sampling import grid_triangles, sample_triangles


def fixture(moved=False):
    x=np.array([[0.,1.],[0.,1.]])
    y=np.array([[0.,0.],[-1.,-1.]])
    if moved:
        x[:]=[[.49,.51],[-.49,1.]]
        y[:]=[[-.49,.49],[-.51,-1.]]
    faces,stats=oriented_quad_triangles(x,y)
    return dict(east_m=x,north_m=y,z_m=2*x+3*y+5,triangles=faces,
        nominal_east_axis_m=np.array([0.,1.]),nominal_north_axis_m=np.array([0.,-1.])),stats


class RegisteredRockMeshTests(unittest.TestCase):
    def test_exact_upward_triangle_normals(self):
        for moved in (False,True):
            data,_=fixture(moved);sampler=RegisteredMeshSampler(data)
            xyz=sampler.xyz[data['triangles']].mean(axis=1)
            heights,normals=sampler.sample(xyz[:,0],xyz[:,1],with_normals=True)
            np.testing.assert_allclose(heights,xyz[:,2],atol=1e-12)
            np.testing.assert_allclose(normals,np.broadcast_to(np.array([-2,-3,1])/np.sqrt(14),normals.shape),atol=1e-12)
            _,single=sampler.sample(xyz[0,0],xyz[0,1],with_normals=True)
            self.assertEqual(single.shape,(3,))

    def test_regular_mesh_keeps_existing_diagonal_and_sampling(self):
        data,stats=fixture()
        np.testing.assert_array_equal(data['triangles'],grid_triangles(2,2))
        self.assertEqual(stats['changed_quad_diagonals'],0)
        data['z_m']=np.array([[0.,0.],[0.,4.]])
        sampler=RegisteredMeshSampler(data)
        x=np.array([0.,.2,.5,.8,1.]);y=-x
        np.testing.assert_allclose(sampler.sample(x,y),sample_triangles(data['z_m'],-y,x))

    def test_folded_old_diagonal_changes_without_moving_measurements(self):
        data,stats=fixture(True)
        self.assertEqual(stats['changed_quad_diagonals'],1)
        np.testing.assert_array_equal(data['triangles'],[[0,1,3],[0,3,2]])
        sampler=RegisteredMeshSampler(data)
        np.testing.assert_allclose(sampler.sample(data['east_m'],data['north_m']),data['z_m'],atol=1e-12)
        xyz=sampler.xyz[data['triangles']]
        for weights in ([1/3]*3,[.01,.49,.5],[.5,.5,0],[0,.5,.5]):
            points=np.einsum('tij,i->tj',xyz,weights)
            np.testing.assert_allclose(sampler.sample(points[:,0],points[:,1]),points[:,2],atol=1e-12)

    def test_invalid_queries_are_not_clamped(self):
        data,_=fixture();sampler=RegisteredMeshSampler(data)
        for x,y in ((-1,0),(2,0),(0,2),(np.nan,0),(0,np.inf)):
            with self.subTest(x=x,y=y),self.assertRaises(ValueError):sampler.sample(x,y)

    def test_invalid_meshes_are_rejected(self):
        for key in ('east_m','north_m','z_m'):
            data,_=fixture();data[key][0,0]=np.nan
            with self.subTest(key=key),self.assertRaises(ValueError):RegisteredMeshSampler(data)
        data,_=fixture();data['east_m'][0,0]=.6
        with self.assertRaises(ValueError):RegisteredMeshSampler(data)
        data,_=fixture();data['triangles'][1]=[0,1,3]
        with self.assertRaises(ValueError):RegisteredMeshSampler(data)
        with self.assertRaises(ValueError):oriented_quad_triangles(np.zeros((2,2)),np.zeros((2,2)))


if __name__=='__main__':unittest.main()
