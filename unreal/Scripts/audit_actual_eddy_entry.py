"""Read actual-map native receipts; never generate or interpolate boat states."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def validate_native_inputs(entry, motion):
    """Reject malformed provenance/physics observations before projecting states."""
    source = entry.get('physical_source')
    map_name = motion.get('map')
    if not isinstance(source, str) or not source or not isinstance(map_name, str) or not map_name:
        raise ValueError('Native physical owner and map required')
    if f'/{map_name}.{map_name}:' not in source:
        raise ValueError('Native physical owner belongs to another map')
    if motion.get('feature_kinematics_enabled') is not True:
        raise ValueError('Actual shared feature kinematics must be enabled')
    for field in ('maximum_shared_surface_error_mps', 'dry_became_wet'):
        value = motion.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f'Missing/nonfinite native physical observation: {field}')
    if motion['dry_became_wet'] != int(motion['dry_became_wet']):
        raise ValueError('Native dry violations must be an integer count')
    for field in ('world_seconds', 'owner_hydraulic_x_m', 'owner_hydraulic_y_m',
                  'owner_direction_x', 'owner_direction_y', 'inferred_radius_m',
                  'entry_local_x_radius', 'entry_local_y_radius'):
        value = entry.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f'Missing/nonfinite native initial condition: {field}')
    previous = -1.0
    for state in motion.get('actual_boat_motion', []):
        time = state.get('world_seconds')
        if isinstance(time, bool) or not isinstance(time, (int, float)) or not math.isfinite(time) or time <= previous:
            raise ValueError('All actual native state times must be finite and increasing')
        previous = time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry', type=Path, required=True)
    parser.add_argument('--motion', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('Use a fresh report; preserve earlier evidence')
    entry = json.loads(args.entry.read_text(encoding='utf-8-sig'))
    motion = json.loads(args.motion.read_text(encoding='utf-8-sig'))
    validate_native_inputs(entry, motion)
    radius = entry['inferred_radius_m']
    dx, dy = entry['owner_direction_x'], entry['owner_direction_y']
    if not math.isfinite(radius) or radius <= 0 or abs(math.hypot(dx, dy)-1) > 1e-5:
        raise ValueError('Finite positive radius and unit native owner direction required')
    rows = []
    for state in motion['actual_boat_motion']:
        # A timer on the placement frame can contain the pre-placement state.
        if state['world_seconds'] <= entry['world_seconds'] + 0.1:
            continue
        x = state['hydraulic_x_m']-entry['owner_hydraulic_x_m']
        y = state['hydraulic_y_m']-entry['owner_hydraulic_y_m']
        row = dict(world_seconds=state['world_seconds'],
                   along_m=x*dx+y*dy, across_m=-x*dy+y*dx,
                   along_velocity_mps=state['velocity_hydraulic_x_mps']*dx+
                       state['velocity_hydraulic_y_mps']*dy,
                   speed_mps=state['speed_mps'], roll_deg=state['roll_deg'])
        if not all(math.isfinite(v) for v in row.values()):
            raise ValueError('Nonfinite actual raft state')
        rows.append(row)
    if len(rows) < 8:
        raise ValueError('Incomplete native timer receipts')
    gaps = [b['world_seconds']-a['world_seconds'] for a, b in zip(rows, rows[1:])]
    if min(gaps) <= 0:
        raise ValueError('Native receipt times must increase')
    closest = min(rows, key=lambda r: r['along_m'])
    upstream = max(0, entry['entry_local_x_radius']*radius-closest['along_m'])
    result = dict(
        schema='raftsim.actual_map_eddy_entry_audit.v1',
        scope='Actual native world-timer states projected onto the recorded initial owner axis. '
              'No interpolation, fixed-step coverage, resolved CFD, pixel advection, or FPS acceptance.',
        entry_sha256=hashlib.sha256(args.entry.read_bytes()).hexdigest(),
        motion_sha256=hashlib.sha256(args.motion.read_bytes()).hexdigest(),
        physical_source=entry['physical_source'], map=motion['map'],
        samples=len(rows), maximum_sample_gap_seconds=max(gaps),
        inferred_radius_m=radius, upstream_displacement_m=upstream,
        minimum_along_velocity_mps=min(r['along_velocity_mps'] for r in rows),
        closest_along_radius=closest['along_m']/radius,
        actual_return_observed=upstream > 1 and min(r['along_velocity_mps'] for r in rows) < -0.1,
        actual_outward_downstream_exit_observed=any(
            r['world_seconds'] > closest['world_seconds'] and
            abs(r['across_m']) > radius and r['along_velocity_mps'] > 0.1 for r in rows),
        actual_head_reached=closest['along_m']/radius <= 2,
        maximum_shared_surface_error_mps=motion['maximum_shared_surface_error_mps'],
        dry_became_wet=motion['dry_became_wet'], rows=rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
