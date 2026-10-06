"""Compare observed decision trials; missing measurements never become passes."""
import argparse
import json
from pathlib import Path
from build_rapid_decision_campaign import build
from report_rapid_calibration import summarize, validate_completion


def clean(t):
    s=summarize(t)
    return (s['valid'] and s['clean_finish'] and not s['natural_consequence_qualified']
            and t.get('full_hull_impulses')==0 and t.get('dry_center_seconds')==0)


def compare(contract, trials):
    result=dict(contract,observed_trials=len(trials),catalog_class_match='not_established')
    result['successful_route_width_m']=None
    result['successful_route_width_status']='Not measured; passing track spread is not a continuous full-hull clearance corridor.'
    result['steering_timing_observations']=[]
    result['mistake_observations']=[]
    result['recoverability_observations']=[]
    for t in trials:
        s=summarize(t)
        facts={k:s.get(k) for k in ('id','outcome','valid','elapsed_s','full_hull_impulses',
              'grounded_seconds','max_swimmers','capsized_during_trial','checkpoint_restores_during_trial',
              'recovered_route_at_s','completed_rescues','remaining_swimmers','named_challenge_sites_seen')}
        facts['clean_physical_finish']=clean(t)
        facts['requested_delay_s']=t.get('mistake_seconds',0)
        facts['actual_delay_trigger_station_m']=t.get('mistake_actual_start_station_m')
        facts['delayed_move_exercised']=t.get('mistake_start_s',-1)>=0
        facts['loaded_sites_in_section']=t.get('named_challenge_sites_loaded_in_section')
        facts['relief_footprints_crossed']=t.get('named_challenge_footprints_crossed')
        facts['evidence']=t['_evidence']
        result['steering_timing_observations'].append(facts)
        # Station-bounded omissions and sustained bad headings are deliberate
        # mistakes too. A finish after bank contact must not disappear from
        # the consequence comparison just because it used no timed blackout.
        if (t.get('disable_steering') or t.get('mistake_seconds',0)>0
                or abs(t.get('initial_heading_deg',0))>0
                or t.get('steering_blackouts') or 'steering_end_m' in t
                or abs(t.get('heading_offset_deg',0))>0
                or t.get('variant')=='hands-off'):
            result['mistake_observations'].append(facts)
        if t.get('normal_rescue_inputs'):
            result['recoverability_observations'].append(facts|dict(
                recovery_input_exercised=s['recovery_commands_observed'],
                # A recovery-enabled clean run with no mistake/incident is
                # not evidence of rescue or a saved high-side.
                physical_incident_observed=s['natural_consequence_qualified']))
    offsets=sorted((t['lane_m'],clean(t)) for t in trials if t['variant'].startswith('offset'))
    result['sampled_offset_outcomes']=offsets
    result['sampled_offset_scope']='Independent route offsets, not a guarantee about unsampled lanes or intermediate obstructions.'
    prepared=next((t for t in trials if t['variant']=='prepared'),None)
    absent=next((t for t in trials if t['variant']=='absent'),None)
    compatible=bool(prepared and absent and prepared.get('_launch',{}).get('sha256')
        and prepared['_launch']['sha256']==absent.get('_launch',{}).get('sha256'))
    result['same_runtime_for_prepared_absent_pair']=compatible
    if compatible and clean(prepared) and clean(absent):
        result['finding']='The tested approach does not demonstrate a need to steer; compare legitimate bypasses before changing hazards.'
    elif prepared and not clean(prepared):
        result['finding']='The proposed good line is not yet a clean control. Diagnose the route, driver or geometry before grading.'
    elif trials:
        result['finding']='Native route observations available; width/timing brackets and matched mistake/recovery controls still required.'
    else:
        result['finding']='No current native comparison.'
    return result


def collect(roots):
    found={}
    for root in roots:
        for folder in root.iterdir():
            if not folder.is_dir() or not (folder/'plan.json').exists(): continue
            completion=folder/'completion.json'
            if not completion.exists(): continue  # still running, not stable evidence
            validate_completion(json.loads(completion.read_text(encoding='utf-8-sig')))
            plan=json.loads((folder/'plan.json').read_text(encoding='utf-8-sig'))
            launch=json.loads((folder/'launch.json').read_text(encoding='utf-8-sig'))
            for definition in plan['trials']:
                file=folder/(definition['id']+'.json')
                if not file.exists(): continue
                trial=json.loads(file.read_text(encoding='utf-8-sig'))
                if any(trial.get(k)!=v for k,v in definition.items()):
                    raise ValueError(f'Trial does not match its input definition: {file}')
                trial['_evidence']=str(file.resolve())
                trial['_launch']=launch
                found[plan['river'],trial['id']]=trial
    contracts,_=build()
    return [compare(c,[t for (river,_),t in found.items()
                       if river==c.get('assessment_river',c['river']) and t.get('rapid_id')==c.get('rapid_id')]) for c in contracts]


def markdown(rows):
    lines=['# Every-rapid decision comparison', '',
           'This is a measurement ledger, not a completed difficulty certification. '
           'Catalog class matching has not been established by these trials. '
           'No missing section, failed native step, gate crossing or untested lane counts as a pass.', '',
           'The named hydraulic additions are authored reconstructions through the production '
           'render/foam/hull-current path. They do not create missing solid rocks, riverbed drops '
           'or missing maps. Numerical test routes are hypotheses, not real-world navigation advice.', '',
           '## Coverage', '',
           f'{len(rows)} indexed entries; {sum(r["status"]=="missing_playable_section" for r in rows)} '
           'have no playable test section. Upper Gorge duplicates are reported separately.', '',
           '## Per-entry results', '']
    for r in rows:
        lines += [f'### {r["river"]}: {r["name"]} — catalog {r["catalog_class"]}', '',
                  f'Flow: {r["flow"]}. **Class match: not established.**']
        if r['status']=='missing_playable_section':
            lines += ['', 'Missing playable section; width, timing, consequences and recovery cannot yet be tested.', '']
            continue
        lines += ['',f'Documented feature/decision: {r["decision"]}. [Source]({r["source"]}).', '',
                  f'- Route width: {r["successful_route_width"]}. Measured safe width: **not established**.',
                  f'- Timing: {r["steering_timing"]}.',
                  f'- Mistake: {r["mistake_consequences"]}.',
                  f'- Recovery: {r["recoverability"]}.', '',r['finding'], '']
        for t in r['steering_timing_observations']:
            lines += [f'- `{t["id"]}`: {t["outcome"]}; valid={t["valid"]}; '
                      f'hull impulses={t["full_hull_impulses"]}; swimmers={t["max_swimmers"]}; '
                      f'clean physical finish={t["clean_physical_finish"]}.']
        if r['steering_timing_observations']: lines += ['']
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('roots',type=Path,nargs='+');p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists(): raise SystemExit('Fresh report path required')
    rows=collect(args.roots)
    args.out.write_text(markdown(rows), encoding='utf-8')
    args.out.with_suffix('.json').write_text(json.dumps(rows,indent=2)+'\n', encoding='utf-8')
    print(f'{len(rows)} entries; {sum(r["observed_trials"] for r in rows)} observations; no automatic class acceptance')
