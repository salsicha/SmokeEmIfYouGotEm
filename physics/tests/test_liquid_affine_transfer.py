import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_affine_transfer import to_grid,to_particles,stencil


class AffineTransferTest(unittest.TestCase):
    def test_quadratic_partition_first_and_second_moments(self):
        h=np.array([.3,.4,.5]);p=np.random.default_rng(21).uniform(1.01,5.99,(60,3))*h
        total=np.zeros(len(p));first=np.zeros_like(p);second=np.zeros((len(p),3,3))
        for _,w,_,r in stencil(p,(8,8,8),h,quadratic=True):
            total+=w;first+=w[:,None]*r;second+=w[:,None,None]*r[:,:,None]*r[:,None,:]
        np.testing.assert_allclose(total,1,atol=1e-14)
        np.testing.assert_allclose(first,0,atol=1e-14)
        np.testing.assert_allclose(second,np.broadcast_to(np.diag(h*h/4),second.shape),atol=1e-14)

    def test_quadratic_preserves_affine_fields(self):
        h=np.array([.3,.4,.5]);p=np.random.default_rng(22).uniform(1.01,5.99,(150,3))*h
        c=np.array([[.3,-1.2,.7],[1.1,-.4,.5],[-.2,.6,.1]])
        v=p@c.T+[2,-1,.3]
        grid,_=to_grid(p,v,np.broadcast_to(c,(len(p),3,3)),(8,8,8),h,quadratic=True)
        out,moment=to_particles(p,grid,h,quadratic=True)
        np.testing.assert_allclose(out,v,atol=2e-14)
        np.testing.assert_allclose(moment,np.broadcast_to(c,moment.shape),atol=3e-14)

    def test_quadratic_conserves_linear_and_angular_transfer_momentum(self):
        rng=np.random.default_rng(23);h=np.array([.3,.4,.5]);p=rng.uniform(1.01,5.99,(200,3))*h
        v=rng.normal(size=p.shape);c=rng.normal(size=(len(p),3,3))
        def angular(v,c):
            b=c*(h*h/4)[None,None,:]
            spin=np.stack((b[:,2,1]-b[:,1,2],b[:,0,2]-b[:,2,0],b[:,1,0]-b[:,0,1]),axis=-1)
            return np.sum(np.cross(p,v)+spin,axis=0)
        grid,mass=to_grid(p,v,c,(8,8,8),h,quadratic=True)
        nodes=(np.indices((8,8,8)).transpose(1,2,3,0)+.5)*h
        linear=(grid*mass[...,None]).sum(axis=(0,1,2))
        rotation=np.cross(nodes,grid*mass[...,None]).sum(axis=(0,1,2))
        np.testing.assert_allclose(linear,v.sum(axis=0),atol=1e-12)
        np.testing.assert_allclose(rotation,angular(v,c),atol=1e-12)
        out,moment=to_particles(p,grid,h,quadratic=True)
        np.testing.assert_allclose(out.sum(axis=0),linear,atol=1e-12)
        np.testing.assert_allclose(angular(out,moment),rotation,atol=1e-12)

    def test_quadratic_moment_does_not_jump_at_tent_cell_boundary(self):
        grid=np.random.default_rng(24).normal(size=(8,8,8,3))
        p=np.array([[3.5-1e-7,3.2,3.1],[3.5+1e-7,3.2,3.1]])
        _,linear=to_particles(p,grid,[1]*3)
        _,quadratic=to_particles(p,grid,[1]*3,quadratic=True)
        self.assertGreater(np.max(abs(linear[0]-linear[1])),.1)
        self.assertLess(np.max(abs(quadratic[0]-quadratic[1])),1e-5)

    def test_nonuniform_particles_preserve_affine_grid_field(self):
        rng=np.random.default_rng(9);spacing=np.array([.328125,.328125,1/3])
        p=rng.uniform(1,6,(180,3))*spacing
        c=np.array([[.3,-1.2,.7],[1.1,-.4,.5],[-.2,.6,.1]])
        v=p@c.T+[2,-1,.3]
        grid,mass=to_grid(p,v,np.broadcast_to(c,(len(p),3,3)),(8,8,8),spacing)
        nodes=(np.indices((8,8,8)).transpose(1,2,3,0)+.5)*spacing
        np.testing.assert_allclose(grid[mass>0],(nodes@c.T+[2,-1,.3])[mass>0],atol=2e-14)
        out,gradient=to_particles(p,grid,spacing)
        np.testing.assert_allclose(out,v,atol=2e-14)
        np.testing.assert_allclose(gradient,np.broadcast_to(c,gradient.shape),atol=3e-14)

    def test_repeated_rotation_transfer_retains_motion(self):
        rng=np.random.default_rng(12);p=rng.uniform(1,6,(300,3));center=np.array([3.5]*3)
        c=np.array([[0.,0.,1.5],[0.,0.,0.],[-1.5,0.,0.]])
        v=(p-center)@c.T;affine=np.broadcast_to(c,(len(p),3,3)).copy()
        apic=v.copy();pic=v.copy()
        for _ in range(30):
            grid,_=to_grid(p,apic,affine,(8,8,8),[1]*3);apic,affine=to_particles(p,grid,[1]*3)
            grid,_=to_grid(p,pic,np.zeros_like(affine),(8,8,8),[1]*3);pic,_=to_particles(p,grid,[1]*3)
        np.testing.assert_allclose(apic,v,atol=1e-12)
        self.assertLess(np.sum(pic**2),.5*np.sum(v**2))

    def test_grid_nodes_and_faces_are_finite_without_inverse(self):
        points=np.array([[2.5,2.5,2.5],[2.5,2.7,2.8],[2.2,2.5,2.5]])
        grid=np.indices((6,6,6)).transpose(1,2,3,0)+.5
        velocity,c=to_particles(points,grid,[1]*3)
        np.testing.assert_allclose(velocity,points)
        np.testing.assert_allclose(c,np.broadcast_to(np.eye(3),c.shape),atol=1e-14)

    def test_partition_and_linear_momentum(self):
        rng=np.random.default_rng(8);p=rng.uniform(1,5,(100,3));v=rng.normal(size=p.shape)
        c=rng.normal(size=(len(p),3,3))
        grid,mass=to_grid(p,v,c,(7,7,7),[1]*3)
        self.assertAlmostEqual(mass.sum(),len(p))
        np.testing.assert_allclose(np.sum(grid*mass[...,None],axis=(0,1,2)),v.sum(axis=0),atol=1e-12)

    def test_incomplete_support_rejected(self):
        with self.assertRaises(ValueError):list(stencil([[0,0,0]],(6,6,6),[1]*3))


if __name__=='__main__':unittest.main()
