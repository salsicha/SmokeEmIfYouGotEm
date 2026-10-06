"""Build explicit normal-input experiments; never modifies a playable river.

Lateral coordinates are metres river-left. Routes are authored hypotheses,
not surveyed safe lines. Gates measure the requested centre line; actual
rotated-hull clearance must be checked using native ground contacts.
Run with run_rapid_assessment.ps1 -PreparedTrials -PlansPath <output>.
"""
import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / 'unreal/Tests/Data/rapid_assessment_reaches.json'


def gate(name, station, lo=None, hi=None):
    row = dict(id=name, station_m=station)
    if lo is not None:
        row['min_lateral_m'] = lo
    if hi is not None:
        row['max_lateral_m'] = hi
    return row


def build():
    reaches = {r['river']: r for r in json.loads(INVENTORY.read_text())}
    out = {}

    def trial(river, rapid, variant, route=None, gates=(), **kwargs):
        reach = reaches[river]
        if river not in out:
            out[river] = {k: copy.deepcopy(v) for k, v in reach.items() if k != 'trials'}
            out[river].update(trials=[], seconds_per_trial=1800,capture_gate_frames=True,
                calibration_scope='Authored route hypotheses. Native observed outcomes decide acceptance, not catalog class.')
        row = copy.deepcopy(next(t for t in reach['trials'] if t['id'] == rapid))
        row.update(id=rapid+'--'+variant, rapid_id=rapid, variant=variant,
                   strict_route=True, normal_rescue_inputs=False, lane_m=0,
                   input_interval_s=.85, gates=list(gates), wall_limit_s=2400)
        if route is not None:
            row['route_laterals'] = route
        row.update(kwargs)
        out[river]['trials'].append(row)
        return row

    # Two midstream rocks, inferred/authored geometry: first +3/r=3,
    # second -3/r=12. Nominal half-width + clearance = 2 m (not a proof of
    # clearance for a rotated or deformed production hull). The centre of the
    # boat must be <= -2 then >= +9; merely crossing the finish is not enough.
    # Corrected live crop: the -5 m approach cleared the hull but crossed the
    # first measuring plane at -1.61 m, outside its unchanged -2 m margin.
    # Give the first rock more room; do not relax the measuring gate.
    # v10 cleared both rocks without impulses, but returning to centre at
    # 2085 crossed the shallow runout at 2082.7. Hold the wet left exit lane.
    pinball = [[1950,-7],[2000,-7],[2026,12],[2052,12],[2085,12]]
    pin_gates = [gate('rock_1_right',2010,None,-2),gate('rock_2_left',2050,9,None)]
    trial('pacuare','lower_pinball','linked',pinball,pin_gates)
    trial('pacuare','lower_pinball','first-only',pinball,pin_gates,
          steering_end_m=2010)
    trial('pacuare','lower_pinball','late-second',pinball,pin_gates,
          steering_blackouts=[[2010,2038]])
    trial('pacuare','lower_pinball','hands-off',[[1950,-7],[2085,-7]],pin_gates)

    # Matched early/late/absent steering, all use identical forward command.
    # Each starts on a genuinely different right-side approach. No scouting
    # or blocked-start centring can erase the treatment.
    hance_gates = [gate('entry_ferry',745,-7,7),gate('above_giants',815,2,18),gate('tail',935)]
    for entry in (-8,-14,-20):
        route = [[620,entry],[685,entry],[755,6],[810,9],[880,14],[940,5]]
        for timing, start, disable in [('early',640,False),('late',720,False),('absent',620,True)]:
            trial('colorado','hance_main',f'{timing}-entry{entry}',route,hance_gates,
                  start_m=620, steering_start_m=start, disable_steering=disable)

    # Expanded envelopes cover the source description / all authored features,
    # rather than the old crux-only checkpoint. Extents remain inferred.
    for rapid, start, finish, route in [
        ('meat_grinder',765,1205,[[765,0],[890,-4],[970,3],[1040,-3],[1205,0]]),
        ('troublemaker',8185,8520,next(t for t in reaches['south-fork']['trials'] if t['id']=='troublemaker')['route_laterals'])]:
        gates = [gate('entry',start+40),gate('crux',next(t for t in reaches['south-fork']['trials'] if t['id']==rapid)['control_m']),gate('whole_rapid_exit',finish-1)]
        for variant, angle, rescue, lane in [('line',0,True,0),('diagonal',45,False,0),
                ('diagonal-high-side',45,True,0),('left-clearance',0,True,3),('right-clearance',0,True,-3)]:
            row=trial('south-fork',rapid,variant,route,gates,start_m=start,finish_m=finish,
                  initial_heading_deg=0,normal_rescue_inputs=rescue,lane_m=lane,
                  coverage_note='Whole-description test envelope; approximate bounds, not measured rapid endpoints.')
            if angle:
                row.update(heading_start_m=row['control_m']-45,heading_end_m=row['control_m']+35,
                           heading_offset_deg=angle,
                           heading_scope='Normal guide/crew strokes hold an attempted diagonal through the crux; actual heading is measured, never imposed.')
        for variant,rescue in [('rock-impact',False),('rock-impact-high-side',True)]:
            trial('south-fork',rapid,variant,route,gates,start_m=start,finish_m=finish,
                  target_physical_rock=True,rock_approach_version=3,normal_rescue_inputs=rescue,
                  simulation_limit_s=240,wall_limit_s=1200,
                  contact_scope='Inspect actual streamed owners throughout the upstream approach, complete the lateral ferry before broadside alignment, and stop sideways forward propulsion once aligned. Use normal controls and record actual component-owned full-hull impulses. No spawned obstacle, forced pose, or inferred wake-radius clearance. Missing owner or missed collision is not a pin test pass.')

    # The cooked entrance at station 840 is wet only to about +9 m. Do not
    # start at +14 on the bank, then mislabel rejected placement as difficulty.
    # Begin the rightward transition above T2: waiting until 1400 sent the
    # native linked trial broadside into the left surge at 1446, washing all
    # four paddlers out despite passing the first four measuring planes.
    # The corrected-crop native run crossed the Typewriter plane at +3.1 m,
    # just outside the unchanged +4 m minimum. Keep a little left margin
    # through that exit before continuing the rightward setup for Khyber.
    terminator = [[840,4],[1040,16],[1125,24],[1160,24],[1220,24],[1275,26],[1320,9],[1345,6],[1380,-9],[1480,-9],[1550,-9],[1720,-10],[1795,0]]
    tg = [gate('entry_channel',1100,12,None),gate('offset_holes',1180,19,None),
          gate('crux_setup',1240,21,None),gate('typewriter_exit',1340,4,22),gate('khyber_setup',1650,None,-4)]
    for variant, route in [('linked',terminator),('first-only',terminator),
            ('missed-crux',[[s,0 if 1180<=s<=1320 else l] for s,l in terminator])]:
        row=trial('futaleufu','terminator_core',variant,route,tg,start_m=840,finish_m=1795,
                  normal_rescue_inputs=True,continuous_sequence=True)
        if variant=='first-only':row['steering_end_m']=1180
        if variant=='missed-crux':
            # The retained v10 driver stalled at 1466 m in 5.58 m depth,
            # slow water and zero crew stamina while repeatedly turning.
            # Keep its wrong-line approach, then explicitly rest and ferry
            # downstream using normal inputs. No refill or progress reset.
            row['stall_recovery']=dict(after_station_m=1380,stall_seconds=15,
                                       rest_seconds=12,lookahead_m=45)

    gulliver = [[5930,-10],[6060,-12],[6140,0],[6180,0],[6260,0],[6390,2],[6565,0]]
    gg = [gate('indicator_exit',6050,None,-3),gate('directors_exit',6160,-4,10),
          gate('crease_gap',6260,-10,10),gate('giants_exit',6500)]
    # Keep the complete intended route identical. The driver's 12 m lookahead
    # reads beyond a shared prefix before reaching its last waypoint: even
    # matching that prefix can alter the first move. Only omit steering.
    for variant, route in [('linked',gulliver),('first-only',gulliver),
            ('late-second',gulliver)]:
        row=trial('zambezi','rapid_7',variant,route,gg,start_m=5930,finish_m=6565,
                  normal_rescue_inputs=True,coverage_note='Includes Indicator Rock at catalog station 5990, missed by the previous 6090 start.')
        # Holding -12 m with corrective strokes can itself counter Director's
        # leftward shove. A no-second-move control must omit those strokes.
        if variant=='first-only':row['steering_end_m']=6060
        if variant=='late-second':row['steering_blackouts']=[[6060,6160]]

    def continuous(river, first, last, variant='continuous', route=None):
        rs = reaches[river]['trials']; a = next(i for i,t in enumerate(rs) if t['id']==first)
        b = next(i for i,t in enumerate(rs) if t['id']==last)
        sections = rs[a:b+1]
        gates = [gate(t['id']+'_exit',t['finish_m']-1) for t in sections]
        return trial(river,first,variant,route,gates,start_m=sections[0]['start_m'],
                     finish_m=sections[-1]['finish_m'],continuous_sequence=True,
                     normal_rescue_inputs=True,strict_route=False,
                     section_ids=[t['id'] for t in sections],wall_limit_s=3600,
                     rescue_drill_station_m=sections[0]['finish_m']+10,
                     rescue_scope='One explicitly induced overboard drill between sections. Recovery and subsequent descent use normal controls, with no reset. Not a natural washout or class-grade observation.')

    continuous('colorado','hance_main','son_of_hance')
    continuous('south-fork','lost_hat','son_of_satan')
    continuous('futaleufu','terminator_entrance','khyber_pass',route=terminator)
    continuous('chilko','bidwell','white_mile')
    return list(out.values())


def validate(plans):
    ids=set()
    for reach in plans:
        for t in reach['trials']:
            key=reach['river'],t['id']
            assert key not in ids,key
            ids.add(key)
            assert t['start_m']<t['finish_m'],key
            route=t.get('route_laterals',[])
            assert all(a[0]<b[0] for a,b in zip(route,route[1:])),key
            gates=t['gates']
            assert len({g['id'] for g in gates})==len(gates),key
            assert all(t['start_m']<g['station_m']<t['finish_m'] for g in gates),key
            assert all(g.get('min_lateral_m',-1e9)<=g.get('max_lateral_m',1e9) for g in gates),key
            assert all(t['start_m']<=a<b<=t['finish_m'] for a,b in t.get('steering_blackouts',[])),key
    return len(ids)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    plans=build(); count=validate(plans)
    if args.out.exists():
        raise SystemExit('Fresh plan path required')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(plans,indent=2)+'\n')
    print(f'{count} explicit trials across {len(plans)} maps: {args.out}')
