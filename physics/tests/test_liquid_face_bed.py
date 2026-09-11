import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from south_fork_registered_mesh import RegisteredMeshSampler
from build_liquid_face_bed import face_bed


class FaceBedTest(unittest.TestCase):
    def mesh(self):
        x,y=np.meshgrid(np.arange(5.),np.arange(4.,-1.,-1.))
        z=2+.2*x+.3*y;z[2,2]+=1.7
        a=(np.arange(4)[:,None]*5+np.arange(4)).ravel()
        return RegisteredMeshSampler(dict(east_m=x,north_m=y,z_m=z,nominal_east_axis_m=np.arange(5.),
            nominal_north_axis_m=np.arange(4.,-1.,-1.),triangles=np.r_[np.c_[a,a+1,a+5],np.c_[a+1,a+6,a+5]]))

    def test_rotated_mesh_faces_preserve_corners(self):
        sampler=self.mesh();angle=.31
        axes=np.array([[np.cos(angle),np.sin(angle)],[-np.sin(angle),np.cos(angle)]])
        lower=axes@np.array([2.,2.])-[1.,1.];extent=np.array([2.,2.])
        faces=face_bed(sampler,axes,lower,extent)
        for face,record in enumerate(faces):
            normal=face//2;tangent=1-normal
            t=np.linspace(0,2,117);local=np.zeros((len(t),2));local[:,normal]=2 if face%2 else 0;local[:,tangent]=t
            en=(local+lower)@axes;knots=np.asarray(record['knots_cm'])/100
            np.testing.assert_allclose(np.interp(t,knots[:,0],knots[:,1]),sampler.sample(en[:,0],en[:,1]),atol=1e-10,rtol=0)

    def test_aligned_mesh_edges_and_vertices(self):
        faces=face_bed(self.mesh(),np.eye(2),[1,1],[2,2])
        self.assertTrue(all(np.all(np.diff(np.asarray(f['knots_cm'])[:,0])>0) for f in faces))

    def test_missing_coverage_rejected(self):
        with self.assertRaises(ValueError):face_bed(self.mesh(),np.eye(2),[-1,0],[2,2])

    def test_invalid_frame_rejected(self):
        with self.assertRaises(ValueError):face_bed(self.mesh(),[[1,0],[1,1]],[0,0],[2,2])


if __name__=='__main__':unittest.main()
