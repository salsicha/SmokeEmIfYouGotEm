import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_inlet_advection import normal_update_roundoff_bound


class InletRoundoffTest(unittest.TestCase):
    def test_bound_uses_prescribed_term_before_cancellation(self):
        gamma=32*2**-24/(1-32*2**-24)
        self.assertEqual(normal_update_roundoff_bound([1,0,0],[1,0,0],100),gamma*102)

    def test_observed_target_is_not_bounded_by_small_result(self):
        v=np.array([.8650977611541748,-3.285482883453369,1.2089343070983887])
        n=np.array([-.9299998355760436,-.36755993501540923,0])
        bound=normal_update_roundoff_bound(v,n,102.15877856663143)
        self.assertGreater(bound,1.944529194508604e-5)
        self.assertLess(bound,.0002)

    def test_reversing_coordinate_sign_does_not_change_bound(self):
        self.assertEqual(normal_update_roundoff_bound([1,2,3],[.6,.8,0],20),
                         normal_update_roundoff_bound([-1,-2,3],[-.6,-.8,0],20))
