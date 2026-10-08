import copy
import unittest
from continue_chilko_corridor_cook import validate_parent
from chilko_native_friction import friction_contract


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        c=friction_contract(.045)
        self.s=dict(roughness=c['native_roughness_coefficient'],feature_count=0,
            metadata=dict(scenario_id='test',generator='build_chilko_corridor_scenario.py',
                provenance=dict(continuous_terrain=dict(manning_n=.045),friction=c)),
            boundaries=[dict(edge='east',kind='outflow',stage=100.)])
        self.n=dict(solver_mode='finite_volume',boundary_mode='scenario',flux_scheme='hll',spatial_order=2,
            cfl=.2,feature_strength_scale=0,roughness_scale=1,bed_slope_source_scale=1,
            preserve_initial_mass=False,disable_fixture_calibrations=True,experimental_west_discharge_m3s=-1,
            experimental_west_supercritical_stage=False,scenario_id='test')
        self.v=dict(passed=True,finite_state=True,velocity_limit_reached=False)
        self.hashes={'bed.npy':'bed_hash'}
        self.r=dict(schema='raftsim.chilko_continuous_cook_review.v1',name='test',input_files_sha256=self.hashes,
            native_manifest=self.n,native_validation=self.v,comparison_frames=['first.csv','last.csv'],
            frame_sha256={'last.csv':'frame_hash'},construction_screen_passed=False)

    def check(self,r=None,s=None,n=None,v=None):
        validate_parent(r or self.r,self.hashes,s or self.s,n or self.n,v or self.v,'last.csv','frame_hash')

    def test_unsettled_review_is_not_hidden_or_declared_accepted(self):
        self.check()
        self.assertFalse(self.r['construction_screen_passed'])

    def test_changed_receipt_or_frame_refused(self):
        for k,value in [('input_files_sha256',{}),('native_manifest',{}),('native_validation',{}),
                ('comparison_frames',['older.csv']),('frame_sha256',{}),('name','another')]:
            r=copy.deepcopy(self.r);r[k]=value
            with self.subTest(k=k),self.assertRaises(ValueError):self.check(r=r)

    def test_clipped_forced_or_changed_coefficient_refused(self):
        v=dict(self.v,velocity_limit_reached=True)
        with self.assertRaises(ValueError):self.check(v=v)
        n=dict(self.n,feature_strength_scale=1)
        with self.assertRaises(ValueError):self.check(n=n)
        s=copy.deepcopy(self.s);s['roughness']=.045
        with self.assertRaises(ValueError):self.check(s=s)

    def test_time_varying_boundaries_and_features_refused(self):
        for field,value in [('feature_count',1),('cascading',True),
                ('boundaries',[dict(edge='west',kind='discharge_profile',time_series=[1,2])])]:
            s=copy.deepcopy(self.s);s[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.check(s=s)


if __name__=='__main__':unittest.main()
