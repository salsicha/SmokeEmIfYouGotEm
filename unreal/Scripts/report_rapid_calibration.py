"""Summarize native calibration receipts without turning gate misses into flips.

Exit arrival, requested line, physical consequence and rescue evidence are
separate observations. A gate is a measuring plane, never a gameplay obstacle.
"""
import argparse
import hashlib
import json
from pathlib import Path


def definition_hash(trial):
    """The saved input plan, not a subset chosen after seeing an outcome."""
    return hashlib.sha256(json.dumps(trial,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate_completion(receipt):
    if (receipt.get('exit_code') != 0 or receipt.get('stable_dependencies') is not True
            or receipt.get('changed_dependencies') != []):
        raise ValueError('Native run did not finish with unchanged dependencies')
    return receipt


def summarize(t):
    gates=t.get('gate_receipts',[])
    expected=t.get('gates',[])
    present={g['id'] for g in gates}
    missing=[g['id'] for g in expected if g['id'] not in present]
    started=all(k in t for k in ('actual_start_m','actual_start_lateral_m','elapsed_s'))
    fresh=(t.get('independent_trial_state_reset',False)
           and t.get('initial_crew_energy',0)>=.999 and t.get('initial_guide_stamina',0)>=.999
           and t.get('initial_fabric_integrity',0)>=.999 and t.get('initial_pressure_fraction',0)>=.999
           and t.get('initial_permanent_crease_m',1)<=1.e-6
           and bool(t.get('initial_crew_stamina'))
           and all(v>=.999 for v in t['initial_crew_stamina'].values()))
    invalid=(not started or not fresh or not t.get('finite',False) or t.get('assessment_protocol_version',0)<12
             or t.get('checkpoint_restores_during_trial',0)!=0
             or t.get('minimum_center_clearance_m',0)<-2
             or t.get('outcome') in ('physics_step_refused_not_rapid_outcome','oar_input_not_verified','nonfinite_state','physical_rock_owner_unavailable','named_water_features_not_exercised','invalid_trial_time_limit','invalid_stall_recovery_policy','invalid_steering_schedule')
             or ('stall_recovery' in t and t.get('assessment_protocol_version',0)<15))
    cleared=t.get('outcome')=='section_cleared'
    arrived=t.get('outcome') in ('section_cleared','exit_with_unrecovered_crew')
    line=cleared and not invalid and bool(expected) and not missing and all(g['inside_requested_lane'] for g in gates)
    physical=(t.get('max_swimmers',0)>0 or t.get('capsized_during_trial',False)
              or t.get('pin_seconds',0)>0 or t.get('grounded_seconds',0)>0)
    # A diagonal request does not prove the boat achieved that angle, and
    # enabling rescue/high-side does not prove an intervention occurred.
    heading=t.get('heading_offset_deg')
    samples=t.get('samples',[])
    scheduled=any(k in t for k in ('steering_start_m','steering_end_m','steering_blackouts','disable_steering'))
    suppressed=[s for s in samples if t.get('disable_steering',False)
        or s.get('station_m',0)<t.get('steering_start_m',-float('inf'))
        or s.get('station_m',0)>=t.get('steering_end_m',float('inf'))
        or any(a<=s.get('station_m',0)<b for a,b in t.get('steering_blackouts',[]))]
    schedule_ignored=any(s.get('missed_turn_active') is not True for s in suppressed)
    invalid=invalid or schedule_ignored
    invalid=invalid or t.get('outcome')=='named_water_features_not_loaded_in_section'
    invalid=invalid or ('mistake_trigger_m' in t and t.get('assessment_protocol_version',0)<16)
    line=line and not invalid
    commanded=[s for s in samples if heading is not None and s.get('heading_hold_active',
               t.get('heading_start_m',float('inf'))<=s.get('station_m',0)<t.get('heading_end_m',-float('inf')))]
    aligned=[s for s in commanded if abs((s.get('heading_relative_to_river_deg',0)-heading+180)%360-180)<=15]
    contact_stations=[]; diagonal_contact_intervals=0; previous=0
    target_contact_headings=[]; previous_target=0
    for s in samples:
        total=s.get('full_hull_impulses',previous)
        if total>previous:
            contact_stations.append(s.get('station_m'))
            if s in aligned:diagonal_contact_intervals+=1
        previous=total
        target_total=s.get('target_owner_impulses',previous_target)
        if (target_total>previous_target and t.get('target_is_localized_rock',False)
                and t.get('assessment_protocol_version',0)>=14):
            target_contact_headings.append(s.get('heading_relative_to_river_deg'))
        previous_target=target_total
    return {k:t.get(k) for k in ('id','rapid_id','variant','outcome','flow_band','start_m','finish_m',
             'actual_start_m','actual_start_lateral_m','actual_start_yaw_deg','elapsed_s',
             'max_abs_roll_deg','max_abs_pitch_deg','max_speed_mps','minimum_center_clearance_m',
             'capsized_during_trial','pin_seconds','grounded_seconds','max_swimmers',
             'high_side_responses','reflip_requests','rescue_attempts','completed_rescues',
             'continuous_sequence','checkpoint_restores_during_trial','controlled_overboard_drill',
             'overboard_drill_actual_station_m','overboard_drill_subject','full_hull_impulses',
             'full_hull_impulse_steps','ground_contact_scope',
             'target_rock_source','target_rock_station_m','target_rock_lateral_m','named_challenge_sites_seen',
             'target_owner_impulses','target_owner_attribution_supported','target_is_localized_rock','closest_target_center_distance_m','target_owner_wake_radius_m',
             'pin_while_target_contact_sampled_seconds','rock_approach_version',
             'mistake_start_s','recovered_route_at_s','maximum_route_error_m',
             'rest_exit_recovery_started','rest_exit_recovery_started_at_s',
             'rest_exit_recovery_start_station_m','rest_exit_recovery_rest_completed_at_s',
             'crew_energy_before_recovery_rest','crew_energy_after_recovery_rest',
             'guide_strokes','crew_command_changes','turn_command_seconds','backstroke_seconds')} | dict(
        fresh_initial_state_verified=fresh,
        steering_suppressed_samples=len(suppressed),steering_schedule_ignored=schedule_ignored,
        steering_schedule_exercised=scheduled and bool(suppressed) and not schedule_ignored,
        attempted_diagonal_samples=len(commanded),diagonal_within_15deg_samples=len(aligned),
        diagonal_heading_and_contact_intervals=diagonal_contact_intervals,
        localized_target_contact_headings_deg=target_contact_headings,
        localized_target_contact_within_15deg_intervals=sum(
            a is not None and heading is not None and abs((a-heading+180)%360-180)<=15
            for a in target_contact_headings),
        localized_target_heading_scope='Actual sampled heading when the selected localized component impulse total increased. Does not require the steering hold to be active; the ferry can arrive broadside. These are observation intervals, not exact collision-time angles.',
        diagonal_contact_scope='Actual sampled heading within 15 degrees of the request and an impulse-count increase since the previous sample; not an exact collision-time heading.',
        contact_station_range_m=[min(contact_stations),max(contact_stations)] if contact_stations else None,
        native_depth_range_m=[min(s['depth_m'] for s in samples),max(s['depth_m'] for s in samples)]
            if samples and all('depth_m' in s for s in samples) else None,
        high_side_actually_exercised=t.get('high_side_responses',0)>0,
        pin_counter_scope='D4 dedicated-rock-actor wrap/pin classifier only. Captured terrain full-hull holding contacts are not classified by this counter; zero does not establish absence of physical pinning.',
        absence_of_physical_pinning_established=False,
        center_clearance_scope='Raft datum minus sampled water-surface height; NOT hull-to-rock clearance.',
        recovery_commands_observed=t.get('rest_exit_recovery_started',False) or any(t.get(k,0)>0 for k in
            ('high_side_responses','reflip_requests','rescue_attempts','backstroke_seconds')),
        target_collision_attribution_available='target_owner_impulses' in t and t.get('assessment_protocol_version',0)>=14
            and t.get('target_owner_attribution_supported',False) and t.get('target_is_localized_rock',False),
        target_collision_observed=t.get('target_owner_impulses',0)>0 and t.get('target_is_localized_rock',False),
        target_pin_contact_observed=t.get('target_owner_impulses',0)>0 and t.get('target_is_localized_rock',False)
            and t.get('pin_while_target_contact_sampled_seconds',0)>0,
        initial_crew_energy=t.get('initial_crew_energy'), final_crew_energy=t.get('final_crew_energy'),
        initial_guide_stamina=t.get('initial_guide_stamina'), final_guide_stamina=t.get('final_guide_stamina'),
        valid=not invalid, started=started, reached_finish=arrived, clean_finish=cleared, requested_line_completed=line,
        gates=gates,missing_gates=missing,physical_consequence_observed=physical,
        rescue_observed=t.get('completed_rescues',0)>0,
        full_hull_contact_measured=t.get('assessment_protocol_version',0)>=11 and 'full_hull_impulses' in t,
        remaining_swimmers=t.get('samples',[{}])[-1].get('swimmers') if t.get('samples') else None,
        natural_consequence_qualified=physical and not t.get('controlled_overboard_drill',False),
        recovery_not_exercised=not (t.get('rest_exit_recovery_started',False) or any(t.get(k,0)>0 for k in
            ('high_side_responses','reflip_requests','rescue_attempts','backstroke_seconds'))
            or t.get('recovered_route_at_s',-1)>=0),
        scope='Game observations, not a real-world rapid grade or performance benchmark')


def compare_pinball(rows):
    by={r['variant']:r for r in rows if r['rapid_id']=='lower_pinball'}
    wanted={'linked','first-only','late-second','hands-off'}
    if not wanted.issubset(by):
        return dict(status='incomplete_controls')
    linked=by['linked']; missed=[by[v] for v in ('first-only','late-second')]
    distinguishes=linked['requested_line_completed'] and all(not r['requested_line_completed'] for r in missed)
    consequence=any(r['physical_consequence_observed'] or not r['reached_finish'] for r in missed)
    # The bank can be beyond the requested side of a one-sided gate. Such an
    # overshoot is a real contact outcome even though it crossed that plane.
    contact_contrast=(linked['valid'] and linked['requested_line_completed']
        and not linked.get('full_hull_impulses')
        and all(r['valid'] and (r.get('full_hull_impulses') or 0)>0 for r in missed))
    return dict(status='physical_validation_required' if distinguishes and not consequence else 'review_native_evidence',
                linked_route_distinguished=distinguishes,missed_move_has_physical_consequence=consequence,
                prepared_line_avoids_contacts_seen_in_both_omission_controls=contact_contrast,
                accepted=False,
                reason='A failed measuring gate alone cannot demonstrate a demanding playable rapid.')


def collect(root):
    rivers=[]
    for directory in sorted(root.iterdir()):
        if not directory.is_dir() or not (directory/'plan.json').exists():
            continue
        plan=json.loads((directory/'plan.json').read_text(encoding='utf-8-sig'))
        rows=[]; missing=[]
        for t in plan['trials']:
            path=directory/(t['id']+'.json')
            if not path.exists():
                missing.append(t['id']);continue
            row=summarize(json.loads(path.read_text(encoding='utf-8-sig')))
            row['trial_definition_sha256']=definition_hash(t)
            row['evidence']=str(path)
            row['evidence_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append(row)
        launch=json.loads((directory/'launch.json').read_text(encoding='utf-8-sig'))
        completion=directory/'completion.json'
        if completion.exists():
            launch['completion']=validate_completion(json.loads(completion.read_text(encoding='utf-8-sig')))
        else:
            launch['completion']=None  # Older runner: no retroactive stability claim.
        snapshot_path=root/'native-runtime-snapshot.json'
        if snapshot_path.exists():
            snapshot=json.loads(snapshot_path.read_text(encoding='utf-8-sig'))
            native_hash=launch['sha256']['unreal/Binaries/Win64/UnrealEditor-SmokeEmIfYouGotEm.dll']
            source_hash=hashlib.sha256((root/snapshot['driver_snapshot']).read_bytes()).hexdigest()
            if native_hash.upper()!=snapshot['game_dll_sha256'].upper() or source_hash.upper()!=snapshot['driver_sha256'].upper():
                raise ValueError('Compiled driver snapshot does not match the recorded native runtime')
            launch['compiled_driver_provenance']=snapshot
        item=dict(river=plan['river'],trials=rows,missing_trials=missing,launch=launch)
        if plan['river']=='pacuare':
            item['slalom_comparison']=compare_pinball(rows)
        if plan['river']=='colorado':
            entries=[r for r in rows if str(r['variant']).startswith('early-entry') and r['valid']]
            lats=sorted(r['actual_start_lateral_m'] for r in entries if r['actual_start_lateral_m'] is not None)
            item['distinct_approaches_verified']=len(lats)==3 and min(b-a for a,b in zip(lats,lats[1:]))>=3.
        rivers.append(item)
    return dict(schema='raftsim.rapid_calibration_observations.v1',rivers=rivers,
                acceptance='Native controls require review; no automatic catalog-class or packaged-FPS acceptance.')


def collect_latest(roots, expected):
    """Last supplied receipt wins even when it fails; never cherry-pick a pass."""
    latest={};launches=[]
    for root in roots:
        for river in collect(root)['rivers']:
            launches.append(dict(root=str(root),river=river['river'],launch=river['launch']))
            for row in river['trials']:
                latest[river['river'],row['id']]=row
    rivers=[]
    for plan in expected:
        rows=[];missing=[]
        for t in plan['trials']:
            row=latest.get((plan['river'],t['id']))
            if row is None:missing.append(t['id'])
            else:
                row=dict(row)
                row['matches_expected_trial']=row.get('trial_definition_sha256')==definition_hash(t)
                if not row['matches_expected_trial']:
                    row['valid']=False
                    row['invalid_reason']='Receipt is from a different trial definition; do not merge an old route into a revised experiment.'
                rows.append(row)
        rivers.append(dict(river=plan['river'],trials=rows,missing_trials=missing))
    return dict(schema='raftsim.rapid_calibration_campaign.v1',rivers=rivers,launches=launches,
                expected_trials=sum(len(p['trials']) for p in expected),
                observed_trials=sum(len(r['trials']) for r in rivers),
                complete_coverage=all(not r['missing_trials'] for r in rivers),
                acceptance='Coverage is not acceptance. Invalid trials, unsuccessful recovery, route misses and missing physical consequences remain visible.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path,nargs='+');parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--plans',type=Path,help='Expected campaign; reports entirely absent rivers too')
    args=parser.parse_args()
    if args.out.exists():
        raise SystemExit('Fresh report path required')
    result=collect_latest(args.root,json.loads(args.plans.read_text(encoding='utf-8-sig'))) if args.plans else collect(args.root[0])
    if len(args.root)>1 and not args.plans:parser.error('Multiple roots require --plans')
    args.out.write_text(json.dumps(result,indent=2)+'\n')
