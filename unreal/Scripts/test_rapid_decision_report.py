import copy
import unittest
import test_rapid_calibration as calibration
from report_rapid_decision_campaign import clean, compare
from build_rapid_decision_campaign import build


class DecisionReportTests(unittest.TestCase):
    def sample(self,variant='prepared'):
        return calibration.CalibrationTests().sample()|dict(variant=variant,_evidence='test-only',
            _launch=dict(sha256={'game':'same'}),full_hull_impulses=0,dry_center_seconds=0)

    def contract(self):
        return next(c for c in build()[0] if c.get('rapid_id')=='lower_pinball')

    def test_missing_counters_are_not_zero_contact_proof(self):
        t=self.sample();self.assertTrue(clean(t))
        for key in ('full_hull_impulses','dry_center_seconds'):
            incomplete=dict(t);del incomplete[key]
            self.assertFalse(clean(incomplete))

    def test_mixed_runtime_does_not_qualify_a_steering_comparison(self):
        a=self.sample();b=self.sample('absent')
        r=compare(self.contract(),[a,b])
        self.assertTrue(r['same_runtime_for_prepared_absent_pair'])
        self.assertIn('does not demonstrate',r['finding'])
        b['_launch']={'sha256':{'game':'other'}}
        self.assertFalse(compare(self.contract(),[a,b])['same_runtime_for_prepared_absent_pair'])

    def test_missing_features_are_a_test_fault_not_class_six(self):
        t=self.sample();t['outcome']='named_water_features_not_loaded_in_section'
        r=compare(self.contract(),[t])
        self.assertFalse(r['steering_timing_observations'][0]['valid'])
        self.assertEqual(r['catalog_class_match'],'not_established')

    def test_contact_finish_and_unexercised_recovery_are_not_clean_success(self):
        t=self.sample();t.update(full_hull_impulses=20,normal_rescue_inputs=True)
        r=compare(self.contract(),[t])
        self.assertFalse(r['steering_timing_observations'][0]['clean_physical_finish'])
        self.assertFalse(r['recoverability_observations'][0]['recovery_input_exercised'])

    def test_old_protocol_cannot_claim_new_decision_trigger(self):
        t=self.sample();t['mistake_trigger_m']=2010
        self.assertFalse(clean(t))
        t['assessment_protocol_version']=16
        self.assertTrue(clean(t))

    def test_station_omissions_and_held_heading_are_mistakes(self):
        for options in (dict(steering_end_m=2010),dict(steering_blackouts=[[2010,2038]]),
                        dict(heading_offset_deg=60),dict(variant='hands-off')):
            t=self.sample('first-only')|options|dict(full_hull_impulses=124)
            r=compare(self.contract(),[t])
            self.assertEqual(len(r['mistake_observations']),1)
            self.assertFalse(r['mistake_observations'][0]['clean_physical_finish'])

    def test_offset_samples_never_fill_unsampled_lanes(self):
        a=self.sample('offset-4');a['lane_m']=-4
        b=self.sample('offset4');b['lane_m']=4
        r=compare(self.contract(),[a,b])
        self.assertIsNone(r['successful_route_width_m'])
        self.assertEqual(r['sampled_offset_outcomes'],[(-4,True),(4,True)])


if __name__=='__main__': unittest.main()
