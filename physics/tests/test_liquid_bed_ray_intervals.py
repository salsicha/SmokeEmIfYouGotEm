import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_mesh_sampling import grid_triangles
from liquid_bed_ray_intervals import bed_ray_intervals


class BedRayIntervalsTest(unittest.TestCase):
    def fixture(self):
        y,x=np.indices((6,6));x=x.astype(float);y=-y.astype(float)
        z=np.maximum(0,1-abs(x-2))+.1*y
        return RegisteredMeshSampler(dict(east_m=x,north_m=y,z_m=z,triangles=grid_triangles(6,6),
            nominal_east_axis_m=x[0],nominal_north_axis_m=y[:,0]))

    def test_ridge_and_shared_edge_integrate_once(self):
        sampler=self.fixture();a=np.array([[.75,-2],[1,-1.2],[2,-2.]]);b=np.array([[3.25,-2],[3,-3.3],[2,-2.]])
        rows,lo,hi,z0,z1=bed_ray_intervals(sampler,a,b)
        np.testing.assert_allclose(np.bincount(rows,hi-lo,minlength=3),1,atol=1e-14)
        for t in (.13,.49,.83):
            fraction=lo+t*(hi-lo);xy=a[rows]+fraction[:,None]*(b-a)[rows]
            np.testing.assert_allclose(z0+t*(z1-z0),sampler.sample(xy[:,0],xy[:,1]),atol=1e-13)
        integral=np.bincount(rows,.5*(z0+z1)*(hi-lo))
        self.assertAlmostEqual(integral[0],1/2.5-.2,places=13)

    def test_rotated_registered_vertices(self):
        y,x=np.indices((6,6));x=x.astype(float);y=-y.astype(float)
        ex=x+.15*np.sin(x+y);ny=y+.12*np.cos(x-y);z=.1*ex*ny+.5*np.sin(ex)
        sampler=RegisteredMeshSampler(dict(east_m=ex,north_m=ny,z_m=z,triangles=grid_triangles(6,6),
            nominal_east_axis_m=x[0],nominal_north_axis_m=y[:,0]))
        a=np.array([[.8,-1],[2.2,-.8]]);b=np.array([[4.1,-3.8],[1.1,-4.1]])
        rows,lo,hi,z0,z1=bed_ray_intervals(sampler,a,b)
        np.testing.assert_allclose(np.bincount(rows,hi-lo),1,atol=1e-14)
        xy=a[rows]+(lo+.37*(hi-lo))[:,None]*(b-a)[rows]
        np.testing.assert_allclose(z0+.37*(z1-z0),sampler.sample(xy[:,0],xy[:,1]),atol=1e-13)

    def test_rejects_unsupported_ray(self):
        with self.assertRaises(ValueError):bed_ray_intervals(self.fixture(),np.array([[0.,-2]]),np.array([[3.,-2]]))
        with self.assertRaises(ValueError):bed_ray_intervals(self.fixture(),np.array([[.6,-2]]),np.array([[4.4,-2]]),maximum_nominal_span=1)


if __name__=='__main__':unittest.main()
