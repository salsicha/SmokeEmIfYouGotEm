"""Close a bounded observed fixed-step velocity budget, not a physics validation.

Support combines gravity, buoyancy, water drag and heave damping. Queued external
impulses are not assumed to be exclusively paddles. Contact is the measured
post-integration delta, including small height contacts missed by a 5 mm audit.
Logging changes frame timing and trajectory: this is never an FPS comparison.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

VECTOR_KEYS = ('inertia', 'before_v', 'before_w', 'retained_force', 'retained_torque',
               'obstacle_force_cumulative', 'obstacle_torque_cumulative', 'force', 'torque',
               'linear_impulse', 'angular_impulse', 'pre_contact_v', 'pre_contact_w', 'after_v', 'after_w')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def add(a, b):
    return [x+y for x, y in zip(a, b)]


def sub(a, b):
    return [x-y for x, y in zip(a, b)]


def analyze(rows):
    require(bool(rows), 'No dynamics rows')
    totals = {k: dict(linear=[0., 0., 0.], angular=[0., 0., 0.], absolute_yaw_delta=0.)
              for k in ('retained', 'obstacle', 'support', 'external_impulse', 'angular_damping', 'ground_response')}
    maximum = 0.
    contacts = 0
    previous_time, previous_frame = -math.inf, -1
    for index, r in enumerate(rows):
        require(type(r['sequence']) in (int, float) and r['sequence'] == index+1,
                'Missing, duplicate or reordered sequence')
        for k in VECTOR_KEYS:
            require(isinstance(r[k], list) and len(r[k]) == 3 and all(map(finite, r[k])), f'Invalid {k}')
        for k in ('world_s', 'frame', 'dt', 'mass_kg', 'angular_damping', 'ground_points', 'penetration_m'):
            require(finite(r[k]), f'Invalid {k}')
        require(type(r['invalid_state']) is bool and not r['invalid_state'], 'Invalid state observed')
        require(type(r['alternate_contact']) is bool and not r['alternate_contact'], 'Alternate contact mode')
        require(26 <= r['world_s'] < 34 and r['world_s'] >= previous_time and r['frame'] >= previous_frame,
                'Out of range or reordered samples')
        require(r['frame'] % 1 == 0 and r['ground_points'] % 1 == 0 and 0 <= r['ground_points'] <= 6,
                'Invalid frame/contact count')
        require(0 < r['dt'] <= .02 and r['mass_kg'] > 0 and min(r['inertia']) > 0
                and 0 <= r['angular_damping'] <= 1 and r['penetration_m'] >= 0, 'Invalid integration values')
        previous_time, previous_frame = r['world_s'], r['frame']
        if index:
            require(max(abs(a-b) for a, b in zip(r['before_v']+r['before_w'], rows[index-1]['after_v']+rows[index-1]['after_w'])) <= 1e-9,
                    'State changed outside recorded integration stages')
        dt, mass, inertia = r['dt'], r['mass_kg'], r['inertia']
        expected_v = [v+j/mass+f/mass*dt for v, j, f in zip(r['before_v'], r['linear_impulse'], r['force'])]
        undamped_w = [w+j/i+t/i*dt for w, j, t, i in zip(r['before_w'], r['angular_impulse'], r['torque'], inertia)]
        expected_w = [w*r['angular_damping'] for w in undamped_w]
        error = max(abs(a-b) for a, b in zip(expected_v+expected_w, r['pre_contact_v']+r['pre_contact_w']))
        require(error <= 1e-9, 'Observed integration budget does not close')
        maximum = max(maximum, error)
        stages = {}
        for k, force, torque in (
                ('retained', r['retained_force'], r['retained_torque']),
                ('obstacle', sub(r['obstacle_force_cumulative'], r['retained_force']), sub(r['obstacle_torque_cumulative'], r['retained_torque'])),
                ('support', sub(r['force'], r['obstacle_force_cumulative']), sub(r['torque'], r['obstacle_torque_cumulative']))):
            stages[k] = ([f/mass*dt for f in force], [t/i*dt for t, i in zip(torque, inertia)])
        stages['external_impulse'] = ([j/mass for j in r['linear_impulse']], [j/i for j, i in zip(r['angular_impulse'], inertia)])
        stages['angular_damping'] = ([0., 0., 0.], sub(r['pre_contact_w'], undamped_w))
        stages['ground_response'] = (sub(r['after_v'], r['pre_contact_v']), sub(r['after_w'], r['pre_contact_w']))
        contacts += int(r['ground_points'] > 0)
        for k, (v, w) in stages.items():
            totals[k]['linear'] = add(totals[k]['linear'], v)
            totals[k]['angular'] = add(totals[k]['angular'], w)
            totals[k]['absolute_yaw_delta'] += abs(w[2])
    # Coverage gate tolerates the first/last rendered-frame boundary, not a
    # missing multi-second slice. Retain count and duration; no full-run claim.
    seconds = sum(r['dt'] for r in rows)
    require(rows[0]['world_s'] < 26.25 and rows[-1]['world_s'] >= 33.75 and 7.7 <= seconds <= 8.3,
            'Incomplete bounded interval')
    return dict(schema='raftsim.dynamics_stage_budget.v1', scope=__doc__, rows=len(rows),
                first_world_s=rows[0]['world_s'], last_world_s=rows[-1]['world_s'],
                integrated_seconds=seconds, ground_contact_substeps=contacts,
                maximum_penetration_m=max(r['penetration_m'] for r in rows),
                maximum_pre_contact_budget_error=maximum, stages=totals,
                initial_omega=rows[0]['before_w'], final_omega=rows[-1]['after_w'],
                budget_passed=True, physics_accepted=False, performance_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    require(not args.report.exists(), 'Fresh output required')
    text = args.log.read_text(encoding='utf-8-sig')
    require('Error:' not in text and 'Log file closed' in text, 'Runtime errors or incomplete log')
    rows = [json.loads(line.split('DynamicsStageAudit ', 1)[1]) for line in text.splitlines() if 'DynamicsStageAudit {' in line]
    result = analyze(rows)
    result['log_sha256'] = hashlib.sha256(args.log.read_bytes()).hexdigest()
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
