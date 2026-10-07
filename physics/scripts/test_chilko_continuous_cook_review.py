import copy
import unittest
import numpy as np
from review_chilko_continuous_cook import validate_native,validate_frame


class ChilkoCookReview(unittest.TestCase):
    def setUp(self):
        self.scenario=dict(metadata=dict(scenario_id='chilko_native'))
        self.native=dict(solver_mode='finite_volume',boundary_mode='scenario',flux_scheme='hll',spatial_order=2,
            cfl=.2,feature_strength_scale=0,roughness_scale=1,bed_slope_source_scale=1,
            preserve_initial_mass=False,disable_fixture_calibrations=True,experimental_west_discharge_m3s=-1,
            experimental_west_supercritical_stage=False,scenario_id='chilko_native')
        self.validation=dict(passed=True,finite_state=True,velocity_limit_reached=False)

    def test_only_reviewed_native_configuration_allowed(self):
        validate_native(self.native,self.validation,self.scenario)
        for key,value in [('solver_mode','reference'),('feature_strength_scale',1),
                ('spatial_order',1),('preserve_initial_mass',True),('disable_fixture_calibrations',False),
                ('scenario_id','another'),('bed_slope_source_scale',0),('roughness_scale',2),
                ('experimental_west_discharge_m3s',45),('experimental_west_supercritical_stage',True)]:
            native=dict(self.native);native[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'Unreviewed'):
                validate_native(native,self.validation,self.scenario)

    def test_failed_or_clipped_native_state_refused(self):
        for key,value in [('passed',False),('finite_state',False),('velocity_limit_reached',True)]:
            validation=dict(self.validation);validation[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'validation failed'):
                validate_native(self.native,validation,self.scenario)

    def test_same_shape_different_bed_or_world_position_is_not_same_cook(self):
        bed=np.full((3,4),950.);r,c=np.indices(bed.shape)
        grid=dict(origin_x=0,origin_y=-2,dx=2,dy=2)
        frame=dict(x=c*2.,y=r*2.-2,h=np.ones(bed.shape),eta=bed+1)
        validate_frame(frame,bed,grid)
        for key in ('x','y','eta','h'):
            bad=copy.deepcopy(frame);bad[key][1,1]+=.01
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'input grid and bed'):
                validate_frame(bad,bed,grid)


if __name__=='__main__':unittest.main()
