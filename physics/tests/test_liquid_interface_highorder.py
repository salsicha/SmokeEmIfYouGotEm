import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from liquid_interface_highorder import advect_limited
from liquid_interface_transport import advect


class InterfaceHighOrderTest(unittest.TestCase):
    def setUp(self):
        z,y,x=np.indices((10,10,48));self.x=x+.5;self.z=z+.5
        self.phi=self.z-4-.7*np.exp(-((self.x-14)/2)**2)
        self.velocity=np.zeros((*self.phi.shape,3));self.velocity[...,0]=.3
        self.lo=[2,2,2];self.hi=[46,8,8]

    def test_stationary_preserves_input_and_boundaries(self):
        original=self.phi.copy()
        result,r=advect_limited(self.phi,self.velocity*0,[1,1,1],1,self.lo,self.hi,True)
        np.testing.assert_array_equal(result,self.phi);np.testing.assert_array_equal(original,self.phi)
        self.assertTrue(r['candidate_step_valid'])

    def test_affine_metric_translation(self):
        h=np.array([.7,1.2,.6]);phi=self.z*.6+.2*self.x*.7
        v=self.velocity.copy();v[...,1]=-.1;v[...,2]=.15
        result,r=advect_limited(phi,v,h,.2,self.lo,self.hi,True)
        expected=phi-(.15+.2*.3)*.2
        np.testing.assert_allclose(result[2:8,2:8,2:46],expected[2:8,2:8,2:46],atol=1e-12)
        np.testing.assert_array_equal(result[:2],phi[:2]);self.assertTrue(r['candidate_step_valid'])

    def test_repeated_translation_preserves_crest_better_than_linear(self):
        low=self.phi.copy();high=self.phi.copy()
        for step in range(24):
            low,a=advect(low,self.velocity,[1,1,1],1,self.lo,self.hi)
            high,b=advect_limited(high,self.velocity,[1,1,1],1,self.lo,self.hi)
            self.assertTrue(a['candidate_step_valid'] and b['candidate_step_valid'])
        expected=self.z-4-.7*np.exp(-((self.x-14-24*.3)/2)**2)
        sample=(4,4,slice(10,36))
        error_low=np.linalg.norm(low[sample]-expected[sample]);error_high=np.linalg.norm(high[sample]-expected[sample])
        self.assertLess(error_high,.5*error_low)
        self.assertGreater(b['second_order_cells'],0)

    def test_discontinuous_scalar_has_no_new_extrema(self):
        phi=np.where(self.x<20,-1.,2.)
        result,r=advect_limited(phi,self.velocity,[1,1,1],1,self.lo,self.hi)
        self.assertTrue(r['candidate_step_valid']);self.assertGreater(r['extrema_limited_cells'],0)
        self.assertGreaterEqual(result.min(),-1);self.assertLessEqual(result.max(),2)

    def test_zero_weight_vertical_donors_cannot_authorize_horizontal_extrema(self):
        result,r=advect_limited(self.phi,self.velocity,[1,1,1],1,self.lo,self.hi)
        # The neighbouring Z layer differs by 1, but its interpolation weight
        # is zero. It must not relax the bound for this horizontal movement.
        old=self.phi[4,4];actual=result[4,4,2:46]
        self.assertTrue(np.all(actual>=np.minimum(old[1:45],old[2:46])))
        self.assertTrue(np.all(actual<=np.maximum(old[1:45],old[2:46])))

    def test_forward_failure_is_not_hidden_by_fallback(self):
        v=self.velocity*10000
        result,r=advect_limited(self.phi,v,[1,1,1],1,self.lo,self.hi,True)
        self.assertFalse(r['candidate_step_valid']);self.assertGreater(r['rejected_forward_trace_cells'],0)
        np.testing.assert_array_equal(result,self.phi)

    def test_solid_neighborhood_reverts_and_bad_mask_rejected(self):
        mask=np.ones(self.phi.shape,bool)
        low,_=advect(self.phi,self.velocity,[1,1,1],1,self.lo,self.hi)
        result,r=advect_limited(self.phi,self.velocity,[1,1,1],1,self.lo,self.hi,solid=mask)
        np.testing.assert_array_equal(low,result);self.assertEqual(r['second_order_cells'],0)
        with self.assertRaises(ValueError):advect_limited(self.phi,self.velocity,[1,1,1],1,self.lo,self.hi,solid=mask.astype(int))


if __name__=='__main__':unittest.main()
