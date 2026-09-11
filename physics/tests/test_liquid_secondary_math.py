import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_secondary_math import metric_curl,expected_emission,update,shared_surface_ready,constrained_foam_position,endpoint_surface_distance


class SecondaryMathTest(unittest.TestCase):
    def test_endpoint_phase_tracks_rising_water(self):
        # The droplet's endpoint is above yesterday's plane but underwater at
        # the new time. A pre-integration label cannot represent that impact.
        phi=endpoint_surface_distance([0,0,5],1/60,lambda p:[0,0,600],lambda p:p[2])
        self.assertAlmostEqual(phi,-5)

    def test_endpoint_prediction_translates_a_wave(self):
        velocity=np.array([200.,50.,0]);p=np.array([31.,22.,14.]);dt=.016
        sdf=lambda q:q[2]-10*np.sin(q[0]/20)-3*np.cos(q[1]/40)
        self.assertAlmostEqual(endpoint_surface_distance(p,dt,lambda q:velocity,sdf),sdf(p-velocity*dt))
        self.assertEqual(endpoint_surface_distance(p,0,lambda q:velocity,sdf),sdf(p))

    def test_endpoint_prediction_rejects_invalid_history(self):
        with self.assertRaises(ValueError):endpoint_surface_distance([0,0,0],.3,lambda p:[0,0,0],lambda p:0)
        with self.assertRaises(ValueError):endpoint_surface_distance([0,0,0],.01,lambda p:[0,np.nan,0],lambda p:0)

    def test_shared_surface_freshness_and_reset(self):
        self.assertTrue(shared_surface_ready(11.9833984375,12,1/60))
        for surface,age,dt in ((0,0,1/60),(12,.01,1/60),(1,2,1/60),(1,1,float('nan'))):
            self.assertFalse(shared_surface_ready(surface,age,dt))

    def test_interface_constraint_uses_normal_and_world_basis(self):
        rotation=np.array([[0.,1,0],[-1,0,0],[0,0,1]])
        # Local +X maps to world +Y; this is not a fixed upward offset.
        p=constrained_foam_position([1,2,3],[10,20,30],-2,[1,0,0],rotation,.1)
        np.testing.assert_allclose(p,[2,6,6])
        np.testing.assert_array_equal(constrained_foam_position([1,2,3],[10,20,30],-2,[0,0,0],rotation,0),[1,2,3])
        with self.assertRaises(ValueError):
            constrained_foam_position([1,2,3],[10,20,30],-2,[0,0,0],rotation,.1)

    def test_curl_each_axis_and_anisotropic_grid(self):
        z,y,x=np.indices((5,7,9));p=np.stack([x*20,y*30,z*50],axis=-1)
        for axis in np.eye(3):
            v=np.cross(axis,p)
            np.testing.assert_allclose(metric_curl(v,[180,210,250]),np.broadcast_to(2*axis,v.shape),atol=1e-12)

    def test_steady_translation_has_no_curl(self):
        v=np.broadcast_to([120.,240.,30.],(4,5,6,3))
        np.testing.assert_array_equal(metric_curl(v,[600,1000,1200]),0.)

    def test_emission_is_elapsed_time_additive(self):
        full=expected_emission(-10,2,250,[30,40,50],.2)
        self.assertGreater(full,0)
        self.assertAlmostEqual(full,12*expected_emission(-10,2,250,[30,40,50],.2/12))

    def test_surface_and_flow_gates(self):
        for phi,curl,speed,dt in ((1,4,250,.1),(-51,4,250,.1),(-10,1,250,.1),(-10,4,40,.1),(-10,4,250,0)):
            self.assertEqual(expected_emission(phi,curl,speed,[30,40,50],dt),0)

    def test_motion_subdivision_invariant(self):
        for phi in (-50,0,50):
            args=([120,80,0],[0,0,-980],[0,0,150],phi,10)
            p=np.array([2.,4.,6.]);v=np.array([10.,20.,30.])
            direct=update(p,v,*args,.2)
            for _ in range(12):p,v=update(p,v,*args,.2/12)
            np.testing.assert_allclose(p,direct[0],atol=1e-11)
            np.testing.assert_allclose(v,direct[1],atol=1e-11)

    def test_pause_and_invalid_dt(self):
        args=([1,2,3],[4,5,6],[120,80,0],[0,0,-980],[0,0,150],50,10)
        p,v=update(*args,0)
        np.testing.assert_array_equal(p,args[0]);np.testing.assert_array_equal(v,args[1])
        for dt in (-1,.3,float('nan')):
            with self.assertRaises(ValueError):update(*args,dt)
