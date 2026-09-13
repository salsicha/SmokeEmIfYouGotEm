import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_liquid_particle_routes import storage_owners
from liquid_native_ownership import prepared_float_frame_owners


def regions():
    xs=(-113.5,-48.5,15.5,79.5,133.5);ys=(-41.5,-8.5,23.5,41.5)
    return [dict(id=4*y+x,bounds_station_lateral_m=[[xs[x],ys[y]],[xs[x+1],ys[y+1]]],
                 axis_x_canonical=[-.9299998355760436,.36755993501540923,0],
                 axis_y_canonical=[-.36755993501540923,-.9299998355760436,0])
            for y in range(3) for x in range(4)]


class NativeOwnershipTest(unittest.TestCase):
    def test_captured_internal_cut_keeps_both_comparisons(self):
        p=np.array([[-8605.787109375,-874.3470458984375,467.80419921875]])
        native,survey=storage_owners(p,regions(),'double-float-demote-v1')
        self.assertEqual(native.tolist(),[11]);self.assertEqual(survey.tolist(),[7])
        _,q,exact,lower,_=prepared_float_frame_owners(p,regions())
        self.assertEqual(q[0,1],6500)
        self.assertGreater(exact[0,1],6500)
        self.assertEqual(lower.tolist(),[12080.8720703125,312.3059387207031])

    def test_legacy_and_unknown_models_are_explicit(self):
        p=np.array([[-8605.787109375,-874.3470458984375,467.80419921875]])
        native,survey=storage_owners(p,regions())
        np.testing.assert_array_equal(native,survey)
        with self.assertRaises(ValueError):storage_owners(p,regions(),'unknown')

    def test_rounding_cannot_expand_physical_exterior(self):
        r=[dict(id=0,bounds_station_lateral_m=[[.123456795,0],[1,1]],
                axis_x_canonical=[1,0,0],axis_y_canonical=[0,1,0])]
        p=np.array([[float(np.float32(.123456795*100)),-50,10]])
        self.assertEqual(prepared_float_frame_owners(p,r)[0].tolist(),[0])
        with self.assertRaises(ValueError):storage_owners(p,r,'double-float-demote-v1')

    def test_disagreeing_prepared_frames_are_rejected(self):
        r=regions();r[1]['axis_x_canonical']=[1,0,0]
        with self.assertRaises(ValueError):prepared_float_frame_owners(np.zeros((1,3)),r)

    def test_actual_stratified_run_outlet_residual_cannot_be_rounded_inside(self):
        p=np.array([[-13401.5703125,-2411.96533203125,493.69671630859375]])
        owner,q,exact,_,_=prepared_float_frame_owners(p,regions())
        self.assertEqual(owner.tolist(),[11]);self.assertEqual(q[0,0],24700)
        self.assertGreater(exact[0,0],24700)
        # Preserve the strict external-domain gate even for a nanometre-scale
        # observed discrepancy. Its cause must be fixed in native classification.
        with self.assertRaises(ValueError):storage_owners(p,regions(),'double-float-demote-v1')

    def test_residual_outer_preserves_internal_cut_and_rejects_actual_exit(self):
        p=np.array([[-13401.5703125,-2411.96533203125,493.69671630859375],
                    [-8605.787109375,-874.3470458984375,467.80419921875]])
        native,survey=storage_owners(p,regions(),'double-float-residual-outer-v2')
        self.assertEqual(native.tolist(),[-1,11]);self.assertEqual(survey.tolist(),[-1,7])

    def test_residual_model_does_not_waive_uploaded_frame_error(self):
        r=[dict(id=0,bounds_station_lateral_m=[[.123456795,0],[1,1]],
                axis_x_canonical=[1,0,0],axis_y_canonical=[0,1,0])]
        p=np.array([[float(np.float32(.123456795*100)),-50,10]])
        with self.assertRaises(ValueError):storage_owners(p,r,'double-float-residual-outer-v2')


if __name__=='__main__':unittest.main()
