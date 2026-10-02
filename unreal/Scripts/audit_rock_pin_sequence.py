"""Validate recorded native rock-pin states, not a simulation or pose generator."""
import argparse
import json
import math
import re
from pathlib import Path

from evaluate_flip_demo import evaluate


def mechanism(report):
    rows = report['motion']
    cap = report['first_capsize_seconds']
    keys = ('downstream_minus_upstream_tube_height_m', 'scoop_wet_upper_faces',
            'scoop_upper_face_surface_offset_m', 'scoop_incoming_normal_mps',
            'candidate_pressure_force_n', 'scoop_longitudinal_torque_nm',
            'omega_x_rad_s', 'omega_y_rad_s', 'omega_z_rad_s')
    if any(k not in r or not math.isfinite(r[k]) for r in rows for k in keys):
        raise ValueError('Missing/non-finite native pinning load evidence')
    raised = [r for r in rows if r['seconds'] < cap and r['contact_impulses'] > 0
              and r['up_z'] > 0 and r['downstream_minus_upstream_tube_height_m'] > .1]
    scoop = []
    for r in rows:
        if r['seconds'] >= cap or r['up_z'] <= 0:
            continue
        x, y, z, w = (r['quat_'+axis] for axis in 'xyzw')
        forward = (1-2*(y*y+z*z), 2*(x*y+w*z), 2*(x*z-w*y))
        spin = sum(a*r['omega_'+axis+'_rad_s'] for a, axis in zip(forward, 'xyz'))
        if (r['scoop_wet_upper_faces'] > 0 and r['scoop_upper_face_surface_offset_m'] < -1e-6
                and r['scoop_incoming_normal_mps'] > 0 and r['candidate_pressure_force_n'] > 0
                and r['scoop_longitudinal_torque_nm']*spin > 0):
            scoop.append(r)
    if not raised or not scoop or raised[0]['seconds'] >= scoop[0]['seconds']:
        raise ValueError('No ordered contact lift -> dipped upstream face -> reinforcing scoop before inversion')
    return dict(first_downstream_lift_seconds=raised[0]['seconds'],
                first_reinforcing_scoop_seconds=scoop[0]['seconds'],
                scoop_samples_before_vertical=len(scoop),
                maximum_pre_vertical_scoop_force_n=max(r['candidate_pressure_force_n'] for r in scoop),
                minimum_pre_vertical_upper_face_offset_m=min(r['scoop_upper_face_surface_offset_m'] for r in scoop),
                first_capsize_seconds=cap,
                scope='Reduced upper-patch pressure reinforces native rotation. Not proof that scoop alone caused the flip.')


def audit(paths, minimum_fps=20.):
    if not math.isfinite(minimum_fps) or minimum_fps < 20:
        raise ValueError('Rock-pin acceptance retains the 20 FPS floor')
    results, reports = [], {}
    for path in paths:
        report = json.loads(path.read_text(encoding='utf-8-sig'))
        result = evaluate(path)
        if result['scene'] in reports:
            raise ValueError('Duplicate scene receipt')
        reports[result['scene']] = report
        launch = json.loads((path.parent/'launch.json').read_text(encoding='utf-8-sig'))
        log = (path.parent/'engine.log').read_text(encoding='utf-8-sig')
        if launch.get('exit_code') != 0 or re.search(r'Log\w+: (?:Error|Fatal):', log):
            raise ValueError('Native engine run failed')
        if '-RaftSimRockPinArcCandidate' not in launch['arguments']:
            raise ValueError('Missing linked native full-hull candidate provenance')
        result['native_raft_dll_sha256'] = launch['raft_dll_sha256']
        result['native_physics_dll_sha256'] = launch['physics_dll_sha256']
        for row in report['motion']:
            for crew in row['crew_motion']:
                if any(not math.isfinite(crew[k]) for k in ('surface_offset_m', 'vertical_velocity_mps', 'time_in_water_s')):
                    raise ValueError('Non-finite native swimmer trajectory')
        if 'vertices=26610 triangles=38344 max_error_m=0' not in log:
            raise ValueError('Missing full original hull/render agreement')
        if result['rendered_fps_mean'] < minimum_fps or not math.isfinite(result['rendered_fps_mean']):
            raise ValueError(f"{result['scene']} misses {minimum_fps:g} FPS: {result['rendered_fps_mean']:.2f}")
        if (result['initial_up_z'] != 1 or result['initial_omega_rad_s'] != 0
                or result['initial_roll_degrees'] != 0 or result['initial_roll_rate_rad_s'] != 0
                or result['timed_pose_transition_used'] is not False):
            raise ValueError('Not an upright unseeded native entry')
        if result['maximum_pose_step_rad'] > result['maximum_omega_rad_s']/120.+1e-5:
            raise ValueError('Pose discontinuity exceeds integrated angular travel')
        results.append(result)
    if not {'rock_pin_broadside', 'rock_pin_calm'}.issubset(reports):
        raise ValueError('Require actual tall-rock flow and calm recordings')
    calm = reports['rock_pin_calm']
    if calm['first_capsize_seconds'] >= 0 or any(r['swimmers'] for r in calm['motion']):
        raise ValueError('Calm pin control unexpectedly flips/ejects crew')
    wedge = reports.get('rock_pillow_broadside')
    if wedge is not None and (wedge['first_capsize_seconds'] >= 0 or any(r['swimmers'] for r in wedge['motion'])):
        raise ValueError('Low-wedge ride-over control unexpectedly flips/ejects crew')
    pin = reports['rock_pin_broadside']
    if (pin['first_capsize_seconds'] < 0 or pin['contact_impulses'] <= 0
            or pin['maximum_submerged_crew'] != 5 or pin['minimum_swimmer_surface_offset_m'] > -.2):
        raise ValueError('Missing physical contact flip and submerged five-passenger release')
    cap = next(r for r in pin['motion'] if r['mode'] == 1)
    if cap['up_z'] > math.cos(math.radians(100)):
        raise ValueError('Crew lifecycle starts before physical 100-degree inversion')
    crew = pin['motion'][-1]['crew_motion']
    if len(crew) != 5 or any(not math.isfinite(c['surface_offset_m']) or abs(c['surface_offset_m']) > .03 for c in crew):
        raise ValueError('Five passengers did not resurface at actual local water datum')
    if not any(len(r['crew_motion']) == 5 and all(c['surface_offset_m'] < -.1 for c in r['crew_motion']) for r in pin['motion']):
        raise ValueError('No actual sampled simultaneous five-passenger submersion')
    return dict(schema='raftsim.native_rock_pin_audit.v1', scenes=results,
                sequence=mechanism(pin),
                scope='Actual indexed-hull engine lab; authored rock/current, not measured rafting thresholds or full-map acceptance. An empty raft may roll back upright.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('receipts', nargs='+', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.receipts)
    if args.output.exists():
        raise ValueError('Preserve prior audit; choose fresh output')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
