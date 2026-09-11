import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_compatible_advection import sample,midpoint
from liquid_affine_transfer import to_particles
from liquid_compatible_projection import divergence


class CompatibleAdvectionTest(unittest.TestCase):
    def test_affine_field_and_derivative(self):
        h=np.array([.3,.4,.5]);nodes=(np.indices((12,12,12)).transpose(1,2,3,0)+.5)*h
        c=np.array([[.2,-.6,.3],[.7,-.1,.2],[-.4,.5,-.1]])
        grid=nodes@c.T+[1,2,3];points=np.array([[4.2,5.7,6.1],[6.9,7.4,3.3]])*h
        v,j=sample(points,grid,h,True)
        np.testing.assert_allclose(v,points@c.T+[1,2,3],atol=1e-13)
        np.testing.assert_allclose(j,np.broadcast_to(c,j.shape),atol=1e-13)

    def test_divergence_commutes_for_random_nonlinear_grid(self):
        rng=np.random.default_rng(46);grid=rng.normal(size=(12,12,12,3));h=np.array([.3,.4,.5])
        points=rng.uniform(3,9,(80,3))*h
        div=divergence(grid.transpose(2,1,0,3),h).transpose(2,1,0)
        expected,_=to_particles(points,np.repeat(div[...,None],3,axis=-1),h,True)
        _,j=sample(points,grid,h,True)
        np.testing.assert_allclose(np.trace(j,axis1=1,axis2=2),expected[:,0],atol=1e-13)

    def test_checkerboard_normal_mode_does_not_compress_transport(self):
        grid=np.zeros((12,12,12,3));grid[...,0]=(-1.)**np.indices((12,12,12))[0]
        v,j=sample([[5.2,6.7,4.1]],grid,[1]*3,True)
        np.testing.assert_allclose(v,0,atol=1e-14)
        np.testing.assert_allclose(j,0,atol=1e-14)

    def test_midpoint_rotation_reduces_euler_area_error(self):
        nodes=np.indices((16,16,16)).transpose(1,2,3,0)+.5
        grid=np.stack((-(nodes[...,1]-8),nodes[...,0]-8,np.zeros((16,16,16))),axis=-1)
        p=np.array([[8,8,8],[9,8,8],[8,9,8]],float);dt=.1
        euler=p+dt*sample(p,grid,[1]*3);rk=midpoint(p,grid,[1]*3,dt)
        area=lambda a:np.linalg.norm(np.cross(a[1]-a[0],a[2]-a[0]))
        self.assertLess(abs(area(rk)-1),abs(area(euler)-1)/100)

    def test_incomplete_support_is_not_silently_clamped(self):
        with self.assertRaises(ValueError):sample([[.1,4,4]],np.zeros((8,8,8,3)),[1]*3)


if __name__=='__main__':unittest.main()
