import unittest
import hashlib
import json
from pathlib import Path
from build_rapid_calibration import build, validate
from report_rapid_calibration import summarize, compare_pinball, collect_latest, definition_hash, validate_completion


class CalibrationTests(unittest.TestCase):
    def test_changed_native_dependencies_cannot_be_reported_as_a_stable_run(self):
        good=dict(exit_code=0,stable_dependencies=True,changed_dependencies=[])
        self.assertEqual(validate_completion(good),good)
        for bad in (good|dict(exit_code=1),good|dict(stable_dependencies=False),
                    good|dict(changed_dependencies=['map']),{}):
            with self.assertRaises(ValueError):validate_completion(bad)

    def test_only_missed_crux_opts_into_downstream_rest_exit(self):
        rows=[t for r in build() for t in r['trials'] if 'stall_recovery' in t]
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['id'],'terminator_core--missed-crux')
        self.assertGreater(rows[0]['stall_recovery']['after_station_m'],1340)
        self.assertEqual(rows[0]['stall_recovery']['rest_seconds'],12)

    def test_rest_policy_cannot_be_credited_to_a_driver_without_it(self):
        t=self.sample();t.update(stall_recovery={},assessment_protocol_version=14)
        self.assertFalse(summarize(t)['valid'])
        t['assessment_protocol_version']=15
        self.assertTrue(summarize(t)['valid'])
        self.assertFalse(summarize(t)['recovery_commands_observed'])
        t['rest_exit_recovery_started']=True
        self.assertTrue(summarize(t)['recovery_commands_observed'])

    def test_bank_overshoot_remains_a_contact_even_past_a_one_sided_gate(self):
        rows=[]
        for v in ('linked','first-only','late-second','hands-off'):
            t=self.sample();t['variant']=v;t['full_hull_impulses']=0 if v=='linked' else 10
            rows.append(summarize(t))
        self.assertTrue(compare_pinball(rows)['prepared_line_avoids_contacts_seen_in_both_omission_controls'])
        self.assertFalse(compare_pinball(rows)['accepted'])

    def test_settled_cook_exports_use_matching_runtime_closure(self):
        root=Path(__file__).resolve().parents[2]
        for package in ('pacuare_river_costa_rica/scenario_huacas_evidence_2017',
                        'colorado_river_grand_canyon_rowing/scenario_hance_evidence_2021',
                        'futaleufu_river_chile/scenario_terminator_evidence_2026'):
            directory=root/'physics/data/real_world'/package
            path=directory/'cooked_flow_fields/manifest.json'
            manifest=json.loads(path.read_text())
            stream=json.loads((directory/'runtime/moving_water_streaming.json').read_text())
            self.assertEqual(manifest['solver']['runtime_crop_boundary_mode'],'cooked_ghost',package)
            self.assertEqual(stream['full_reach_transit_seed']['cooked_fields_manifest_sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertTrue(all(0<b['manning_n']<=.2 for b in manifest['bands']))

    def test_trial_definition_hash_detects_a_revised_route(self):
        a=dict(id='same-id',route_laterals=[[0,0],[100,5]])
        b=dict(id='same-id',route_laterals=[[0,0],[100,-5]])
        self.assertNotEqual(definition_hash(a),definition_hash(b))
        self.assertEqual(definition_hash(a),definition_hash(dict(reversed(list(a.items())))))

    def test_explicit_matrix(self):
        plans=build()
        self.assertEqual(validate(plans),37)
        self.assertEqual({r['river'] for r in plans},{'pacuare','colorado','south-fork','futaleufu','zambezi','chilko'})

    def test_hance_treatments_are_matched(self):
        trials=next(r for r in build() if r['river']=='colorado')['trials']
        for entry in (-8,-14,-20):
            rows=[t for t in trials if t['variant'].endswith(f'entry{entry}')]
            self.assertEqual(len(rows),3)
            self.assertTrue(all(t['strict_route'] for t in rows))
            self.assertEqual(len({tuple(map(tuple,t['route_laterals'])) for t in rows}),1)
            self.assertEqual(sum(t['disable_steering'] for t in rows),1)

    def test_continuous_sections_are_one_trial(self):
        rows=[t for r in build() for t in r['trials'] if t['variant']=='continuous']
        self.assertEqual(len(rows),4)
        self.assertTrue(all(t['continuous_sequence'] and t['normal_rescue_inputs'] and len(t['section_ids'])>=2 for t in rows))
        self.assertEqual(next(t for t in rows if t['rapid_id']=='bidwell')['finish_m'],3975)
        self.assertTrue(all(t['start_m']<t['rescue_drill_station_m']<t['finish_m'] for t in rows))

    def test_indicator_rock_is_inside_gullivers(self):
        rows=next(r for r in build() if r['river']=='zambezi')['trials']
        self.assertTrue(all(t['start_m']<5990<t['finish_m'] for t in rows))

    def test_revised_rock_setup_cannot_reuse_old_target_receipts(self):
        rows=[t for r in build() for t in r['trials'] if t.get('target_physical_rock')]
        self.assertEqual(len(rows),4)
        self.assertTrue(all(t['rock_approach_version']==3 for t in rows))

    def test_gullivers_controls_share_the_whole_first_move(self):
        rows=next(r for r in build() if r['river']=='zambezi')['trials']
        first=rows[0]['route_laterals']
        self.assertTrue(all(t['route_laterals']==first for t in rows))

    def test_lookahead_cannot_change_approach_before_steering_treatment(self):
        for river in ('pacuare','futaleufu','zambezi'):
            rows=next(r for r in build() if r['river']==river)['trials']
            linked=next(t for t in rows if t['variant']=='linked')
            controls=[t for t in rows if t['variant'] in ('first-only','late-second')]
            self.assertTrue(all(t['route_laterals']==linked['route_laterals'] for t in controls),river)

    def test_first_only_omits_later_corrections_instead_of_holding_a_lane(self):
        for river,cutoff in [('pacuare',2010),('futaleufu',1180),('zambezi',6060)]:
            rows=next(r for r in build() if r['river']==river)['trials']
            control=next(t for t in rows if t['variant']=='first-only')
            self.assertEqual(control['steering_end_m'],cutoff)
        zam=next(r for r in build() if r['river']=='zambezi')['trials']
        self.assertEqual(next(t for t in zam if t['variant']=='late-second')['steering_blackouts'],[[6060,6160]])

    def test_native_must_actually_apply_the_steering_blackout(self):
        t=self.sample();t.update(steering_blackouts=[[10,20]],
            samples=[dict(station_m=15,missed_turn_active=False)])
        self.assertFalse(summarize(t)['valid'])
        t['samples'][0]['missed_turn_active']=True
        self.assertTrue(summarize(t)['valid'])
        self.assertTrue(summarize(t)['steering_schedule_exercised'])

    def test_unreached_blackout_is_not_exercised(self):
        t=self.sample();t.update(steering_end_m=20,samples=[dict(station_m=15,missed_turn_active=False)])
        self.assertFalse(summarize(t)['steering_schedule_exercised'])

    def sample(self):
        return dict(id='example',rapid_id='lower_pinball',variant='linked',finite=True,
                    actual_start_m=0,actual_start_lateral_m=0,elapsed_s=100,
                    assessment_protocol_version=12,outcome='section_cleared',
                    independent_trial_state_reset=True,initial_crew_energy=1,initial_guide_stamina=1,
                    initial_fabric_integrity=1,initial_pressure_fraction=1,initial_permanent_crease_m=0,
                    initial_crew_stamina={'guide':1,'paddler_1':1},
                    gates=[dict(id='first'),dict(id='second')],
                    gate_receipts=[dict(id='first',inside_requested_lane=True),dict(id='second',inside_requested_lane=True)])

    def test_finish_is_not_route_success(self):
        t=self.sample();t['gate_receipts'][1]['inside_requested_lane']=False
        r=summarize(t)
        self.assertTrue(r['reached_finish'])
        self.assertFalse(r['requested_line_completed'])
        self.assertFalse(r['physical_consequence_observed'])

    def test_reset_cannot_be_recovery(self):
        t=self.sample();t['checkpoint_restores_during_trial']=1
        self.assertFalse(summarize(t)['valid'])

    def test_inherited_fatigue_or_damage_invalidates_comparison(self):
        for key,value in [('initial_crew_energy',.07),('initial_guide_stamina',.5),
                          ('initial_fabric_integrity',.82),('initial_permanent_crease_m',.1),
                          ('initial_crew_stamina',{'guide':1,'paddler_1':.4}),
                          ('assessment_protocol_version',11)]:
            t=self.sample();t[key]=value
            self.assertFalse(summarize(t)['valid'],key)

    def test_continuous_descent_can_finish_tired(self):
        t=self.sample();t.update(continuous_sequence=True,final_crew_energy=.07)
        self.assertTrue(summarize(t)['valid'])

    def test_refused_step_is_not_rapid_difficulty(self):
        t=self.sample();t['outcome']='physics_step_refused_not_rapid_outcome'
        self.assertFalse(summarize(t)['valid'])

    def test_inactive_named_features_cannot_qualify_the_challenge(self):
        t=self.sample();t['outcome']='named_water_features_not_exercised'
        r=summarize(t)
        self.assertFalse(r['valid'])
        self.assertFalse(r['clean_finish'])

    def test_exit_with_swimmers_is_not_clean(self):
        t=self.sample();t['outcome']='exit_with_unrecovered_crew';t['max_swimmers']=2
        r=summarize(t)
        self.assertTrue(r['reached_finish']);self.assertFalse(r['clean_finish'])

    def test_absent_rivers_are_missing_not_silently_complete(self):
        r=collect_latest([],build())
        self.assertEqual(r['expected_trials'],37)
        self.assertEqual(r['observed_trials'],0)
        self.assertFalse(r['complete_coverage'])

    def test_no_swim_is_not_rescue_validation(self):
        r=summarize(self.sample())
        self.assertFalse(r['rescue_observed'])
        self.assertTrue(r['recovery_not_exercised'])

    def test_requested_diagonal_or_high_side_is_not_observed_action(self):
        t=self.sample();t.update(heading_start_m=10,heading_end_m=20,heading_offset_deg=45,
                                normal_rescue_inputs=True,samples=[dict(station_m=15,heading_relative_to_river_deg=0)])
        r=summarize(t)
        self.assertEqual(r['attempted_diagonal_samples'],1)
        self.assertEqual(r['diagonal_within_15deg_samples'],0)
        self.assertFalse(r['high_side_actually_exercised'])

    def test_downstream_contact_cannot_qualify_a_targeted_rock_pin(self):
        t=self.sample();t.update(target_physical_rock=True,full_hull_impulses=9000,pin_seconds=8)
        r=summarize(t)
        self.assertFalse(r['target_collision_attribution_available'])
        self.assertFalse(r['target_collision_observed'])
        t.update(assessment_protocol_version=13,target_owner_impulses=5)
        r=summarize(t)
        self.assertFalse(r['target_collision_observed']) # could be elsewhere on a large terrain tile
        t.update(assessment_protocol_version=14,target_is_localized_rock=True,target_owner_attribution_supported=True)
        r=summarize(t)
        self.assertTrue(r['target_collision_observed'])
        self.assertFalse(r['target_pin_contact_observed'])
        t['pin_while_target_contact_sampled_seconds']=.2
        self.assertTrue(summarize(t)['target_pin_contact_observed'])

    def test_contact_duration_and_depth_are_retained_without_calling_them_clearance(self):
        t=self.sample();t.update(grounded_seconds=.5,full_hull_impulse_steps=60,
            ground_contact_scope='Committed impulse steps, not minimum clearance',
            samples=[dict(station_m=10,depth_m=.2,full_hull_impulses=3),
                     dict(station_m=11,depth_m=1.5,full_hull_impulses=3)])
        r=summarize(t)
        self.assertEqual(r['native_depth_range_m'],[.2,1.5])
        self.assertEqual(r['grounded_seconds'],.5)
        self.assertEqual(r['full_hull_impulse_steps'],60)
        self.assertIsNone(r['minimum_center_clearance_m'])
        self.assertEqual(r['contact_station_range_m'],[10,10])

    def test_drill_cannot_be_called_natural_washout(self):
        t=self.sample();t.update(controlled_overboard_drill=True,max_swimmers=1,completed_rescues=1)
        r=summarize(t)
        self.assertTrue(r['rescue_observed'])
        self.assertFalse(r['natural_consequence_qualified'])

    def test_legacy_pin_zero_cannot_clear_captured_terrain(self):
        t=self.sample();t.update(pin_seconds=0,full_hull_impulses=9000,grounded_seconds=50)
        r=summarize(t)
        self.assertEqual(r['pin_seconds'],0)
        self.assertFalse(r['absence_of_physical_pinning_established'])
        self.assertIn('dedicated-rock-actor',r['pin_counter_scope'])
        self.assertTrue(r['physical_consequence_observed'])

    def test_contact_alone_does_not_claim_recovery_input(self):
        t=self.sample();t.update(full_hull_impulses=4,grounded_seconds=.2)
        r=summarize(t)
        self.assertFalse(r['recovery_commands_observed'])
        self.assertTrue(r['recovery_not_exercised'])
        self.assertIn('NOT hull-to-rock',r['center_clearance_scope'])
        t['backstroke_seconds']=2
        self.assertTrue(summarize(t)['recovery_commands_observed'])
        self.assertFalse(summarize(t)['recovery_not_exercised'])

    def test_diagonal_heading_must_coincide_with_contact_interval(self):
        t=self.sample();t.update(heading_offset_deg=45,samples=[
            dict(station_m=1,heading_hold_active=True,heading_relative_to_river_deg=45,full_hull_impulses=0),
            dict(station_m=2,heading_hold_active=True,heading_relative_to_river_deg=0,full_hull_impulses=4)])
        self.assertEqual(summarize(t)['diagonal_heading_and_contact_intervals'],0)
        t['samples'].append(dict(station_m=3,heading_hold_active=True,heading_relative_to_river_deg=40,full_hull_impulses=5))
        self.assertEqual(summarize(t)['diagonal_heading_and_contact_intervals'],1)

    def test_missing_gate_is_not_pass(self):
        t=self.sample();t['gate_receipts'].pop()
        r=summarize(t);self.assertEqual(r['missing_gates'],['second'])
        self.assertFalse(r['requested_line_completed'])

    def test_actual_target_contact_angle_is_not_a_command_flag(self):
        t=self.sample();t.update(assessment_protocol_version=14,target_is_localized_rock=True,
            heading_offset_deg=80,samples=[
                dict(station_m=1,heading_hold_active=False,heading_relative_to_river_deg=87,target_owner_impulses=17),
                dict(station_m=2,heading_hold_active=False,heading_relative_to_river_deg=103,target_owner_impulses=21)])
        r=summarize(t)
        self.assertEqual(r['localized_target_contact_headings_deg'],[87,103])
        self.assertEqual(r['localized_target_contact_within_15deg_intervals'],1)
        t['target_is_localized_rock']=False
        self.assertEqual(summarize(t)['localized_target_contact_headings_deg'],[])

    def test_failed_placement_is_not_valid_navigation(self):
        t=self.sample();del t['actual_start_m'];t['outcome']='destination_water_unavailable'
        self.assertFalse(summarize(t)['valid'])

    def test_terminator_first_move_is_matched(self):
        rows=next(r for r in build() if r['river']=='futaleufu')['trials']
        linked=next(t for t in rows if t['variant']=='linked')
        first=next(t for t in rows if t['variant']=='first-only')
        self.assertEqual(linked['route_laterals'],first['route_laterals'])
        self.assertEqual(linked['route_laterals'][0],[840,4])

    def test_painted_gate_cannot_accept_physics(self):
        rows=[]
        for v in ('linked','first-only','late-second','hands-off'):
            t=self.sample();t['variant']=v
            if v!='linked': t['gate_receipts'][1]['inside_requested_lane']=False
            rows.append(summarize(t))
        result=compare_pinball(rows)
        self.assertTrue(result['linked_route_distinguished'])
        self.assertFalse(result['accepted'])
        self.assertEqual(result['status'],'physical_validation_required')


if __name__=='__main__': unittest.main()
