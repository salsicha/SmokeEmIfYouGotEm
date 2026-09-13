import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_interface_transport import advect


class InterfaceTransportTest(unittest.TestCase):
    def setUp(self):
        self.h = np.array([50., 50., 100/3])
        z, y, x = np.indices((8, 10, 12))
        self.phi = (z+.5)*self.h[2]-.1*(x+.5)*self.h[0]+.2*(y+.5)*self.h[1]-120
        self.v = np.zeros((*self.phi.shape, 3))
        self.lo, self.hi = [2, 2, 2], [10, 8, 6]

    def test_stationary_and_preserved_halos(self):
        out, d = advect(self.phi, self.v, self.h, 1/60, self.lo, self.hi)
        np.testing.assert_allclose(out, self.phi, atol=1e-12)
        self.assertTrue(d['candidate_step_valid'])

    def test_metric_plane_translation(self):
        self.v[:] = [130, -75, 21]
        out, d = advect(self.phi, self.v, self.h, 1/60, self.lo, self.hi)
        expected = self.phi[2:6, 2:8, 2:10]-(np.dot([-.1, .2, 1], [130, -75, 21]))/60
        np.testing.assert_allclose(out[2:6, 2:8, 2:10], expected, atol=1e-12)
        np.testing.assert_array_equal(out[:2], self.phi[:2])
        self.assertTrue(d['candidate_step_valid'])

    def test_midpoint_uses_velocity_at_midpoint(self):
        z, y, x = np.indices(self.phi.shape)
        self.v[..., 0] = .2*(x+.5)*self.h[0]
        dt = .1
        out, d = advect(self.phi, self.v, self.h, dt, self.lo, self.hi)
        back_x = (x+.5)*self.h[0]*(1-.2*dt+.5*(.2*dt)**2)
        expected = self.phi+.1*((x+.5)*self.h[0]-back_x)
        np.testing.assert_allclose(out[2:6, 2:8, 2:10], expected[2:6, 2:8, 2:10], atol=1e-12)
        self.assertTrue(d['candidate_step_valid'])

    def test_outside_trace_is_failure_not_clamped_success(self):
        self.v[:] = [100000, 0, 0]
        out, d = advect(self.phi, self.v, self.h, 1, self.lo, self.hi)
        self.assertFalse(d['candidate_step_valid'])
        self.assertEqual(d['rejected_trace_cells'], 192)
        self.assertIsNone(d['max_valid_trace_distance_cells'])
        self.assertGreater(d['max_midpoint_trace_distance_cells'], 1)
        np.testing.assert_array_equal(out, self.phi)

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            advect(self.phi, self.v, self.h, -.1, self.lo, self.hi)
        with self.assertRaises(ValueError):
            advect(self.phi, self.v, self.h, .1, [2.5, 2, 2], self.hi)

    def test_compact_translation_and_caller_owned_edges(self):
        self.v[:]=[130,-75,21]
        out,d=advect(self.phi,self.v,self.h,1/60,self.lo,self.hi,True)
        np.testing.assert_allclose(out[2:6,2:8,2:10],self.phi[2:6,2:8,2:10]-np.dot([-.1,.2,1],[130,-75,21])/60,atol=1e-12)
        np.testing.assert_array_equal(out[:2],self.phi[:2])
        self.assertTrue(d['candidate_step_valid'])

    def test_compact_normal_checkerboard_does_not_move_interface(self):
        x=np.indices(self.phi.shape)[2]
        self.v[...,0]=100*(-1.)**x
        out,d=advect(self.phi,self.v,self.h,1/60,self.lo,self.hi,True)
        np.testing.assert_allclose(out,self.phi,atol=1e-12)
        self.assertTrue(d['candidate_step_valid'])

    def test_compact_incomplete_trace_is_not_clamped(self):
        self.v[:]=[100000,0,0]
        out,d=advect(self.phi,self.v,self.h,1,self.lo,self.hi,True)
        np.testing.assert_array_equal(out,self.phi)
        self.assertFalse(d['candidate_step_valid'])
        self.assertEqual(d['rejected_trace_cells'],192)


if __name__ == '__main__':
    unittest.main()
