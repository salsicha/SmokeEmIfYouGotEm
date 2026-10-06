import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_particle_quantization import position_error_box,quantized_endpoint
from solve_liquid_particle_density import constrained_direction
from south_fork_registered_mesh import RegisteredMeshSampler
from south_fork_mesh_sampling import grid_triangles


class ParticleQuantizationTest(unittest.TestCase):
    def test_error_box_covers_signed_coordinates_and_binade_boundaries(self):
        rng=np.random.default_rng(47)
        p=rng.uniform(-30000,30000,(5000,3));p[:3]=[[8192,0,-8192],[16383.999,1,-16384],[.001,-.001,0]]
        d=rng.uniform(-80,80,p.shape);stored,error=quantized_endpoint(p,d,80)
        self.assertTrue(np.all(abs(stored-(p+d))<=error))
        np.testing.assert_array_equal(stored,stored.astype('<f4').astype(float))

    def test_trial_outside_envelope_and_overflow_rejected(self):
        with self.assertRaises(ValueError):quantized_endpoint(np.zeros((1,3)),np.array([[2.,0,0]]),1)
        with self.assertRaises(ValueError):position_error_box(np.full((1,3),np.finfo(np.float32).max),1)
        with self.assertRaises(ValueError):position_error_box(np.zeros((1,3)),0)

    def test_contact_bound_prevents_rounding_through_sloping_skin(self):
        y,x=np.indices((5,5));x=x.astype(float)+98;y=-y.astype(float);z=.3*x
        mesh=RegisteredMeshSampler(dict(east_m=x,north_m=y,z_m=z,triangles=grid_triangles(5,5),
            nominal_east_axis_m=x[0],nominal_north_axis_m=y[:,0]))
        p=np.array([[10000.,200.,3002.]]);d=np.array([[.03,0,.009]])
        naive=(p+d).astype('<f4').astype(float)
        clearance=naive[:,2]-100*mesh.sample(naive[:,0]/100,-naive[:,1]/100)
        self.assertLess(clearance[0],2.-1e-6)
        move,report=constrained_direction(p,p,d,np.eye(3),np.full(3,50.),np.zeros(3),np.full(3,20000.),
            mesh,np.array([2.]),native_positions=True)
        self.assertTrue(report['converged']);self.assertGreater(report['constraints'],0)
        actual,_=quantized_endpoint(p,move,np.linalg.norm(np.full(3,50.)))
        clearance=actual[:,2]-100*mesh.sample(actual[:,0]/100,-actual[:,1]/100)
        self.assertGreaterEqual(clearance[0],2.-1e-6)

    def test_exact_native_position_does_not_move_when_direction_is_zero(self):
        p=np.array([[10000.,200.,3002.]])
        stored,_=quantized_endpoint(p,np.zeros_like(p),80)
        np.testing.assert_array_equal(stored,p)


if __name__=='__main__':unittest.main()
