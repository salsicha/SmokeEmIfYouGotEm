import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_affine_transfer import to_particles,velocity_derivative
from liquid_compatible_projection import divergence


class InterpolatedDivergenceTest(unittest.TestCase):
    def test_derivative_matches_finite_difference_on_nonlinear_field(self):
        grid=np.random.default_rng(41).normal(size=(8,8,8,3));h=np.array([.3,.4,.5])
        points=np.array([[3.2,3.7,4.1],[2.8,4.3,3.6]])*h
        for quadratic in (False,True):
            actual=velocity_derivative(points,grid,h,quadratic)
            expected=np.empty_like(actual)
            for axis in range(3):
                delta=np.eye(3)[axis]*1e-6
                a,_=to_particles(points+delta,grid,h,quadratic)
                b,_=to_particles(points-delta,grid,h,quadratic)
                expected[:,:,axis]=(a-b)/2e-6
            np.testing.assert_allclose(actual,expected,atol=1e-8)

    def test_collocated_checkerboard_has_zero_grid_divergence_but_not_flow_divergence(self):
        grid=np.zeros((8,8,8,3));grid[...,0]=(-1.)**np.indices((8,8,8))[0]
        discrete=divergence(grid.transpose(2,1,0,3),[1]*3)
        np.testing.assert_array_equal(discrete[1:-1,1:-1,1:-1],0)
        for quadratic in (False,True):
            jac=velocity_derivative([[3.2,3.7,4.1]],grid,[1]*3,quadratic)
            self.assertGreater(abs(np.trace(jac[0])),.5)


if __name__=='__main__':unittest.main()
