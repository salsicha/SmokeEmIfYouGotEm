"""Independent retained-state CPU replay of actual queued GPU observations.

Compare at the GPU's captured committed instant, including failure snapshots.
Do not replace evolved interiors with later mean packets, extrapolate faces,
erase foam, repair state, or interpret a short parity check as scene acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import audit_live_temporal_evolution as temporal


def replay(record):
    if record.get('schema') != 'raftsim.live_nonlinear_owner_audit.v1':
        raise ValueError('Unsupported owner audit schema')
    raw = record['observations']
    if not 2 <= len(raw) <= 64:
        raise ValueError('Expected bounded paired observations')
    pairs = [temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
             first=a, second=b)) for a, b in zip(raw, raw[1:])]
    clock = np.asarray(record['progress'], dtype=float)
    if clock.shape != (4,) or not np.isfinite(clock).all() or clock[2] < 0:
        raise ValueError('Invalid GPU committed clock')
    target = float(clock[0]+clock[1])
    first = pairs[0][0]
    if not first['native_seconds'] <= target <= pairs[-1][1]['native_seconds']:
        raise ValueError('GPU clock outside retained observations')
    gpu = np.asarray(record['state'], dtype=float).reshape(first['ny'], first['nx'], 4)
    if not np.isfinite(gpu).all() or np.any(gpu[..., [0, 3]] < 0) or np.any(gpu[..., 3] != 0):
        raise ValueError('Invalid/nonzero-foam GPU state cannot use the zero-foam CPU control')
    state = first['state'][..., :3].copy()
    intervals = []
    report = dict(schema='raftsim.live_nonlinear_owner_comparison.v1', scope=__doc__,
                  gpu_failure=record['failure'], target_native_seconds=target,
                  first_native_seconds=first['native_seconds'], requested_seconds=target-first['native_seconds'],
                  cpu_completed=False, state_gates_passed=False, scene_accepted=False,
                  normal_solver_promoted=False, intervals=intervals)
    for a, b in pairs:
        if target <= a['native_seconds']:
            break
        duration, boundary = temporal.boundary_provider(a, b)
        requested = min(duration, target-a['native_seconds'])
        try:
            state, stats = temporal.bank.advance(state, a['bed'], a['cell_meters'], requested,
                max_trials=4096, boundary_at_time=boundary, breaking_model='hybrid_front', **temporal.KW)
            intervals.append(dict(first_native_seconds=a['native_seconds'], requested_seconds=requested, statistics=stats))
        except (temporal.bank.ReplayExhausted, temporal.bank.ReplayInvalidRate) as error:
            report.update(error=str(error), failure=error.diagnostics)
            return error.state, report
        except (ValueError, FloatingPointError) as error:
            report.update(error=str(error))
            return state, report
    error = state-gpu[..., :3]
    relative = [float(np.linalg.norm(error[..., k])/max(np.linalg.norm(state[..., k]), np.finfo(float).tiny))
                if np.any(state[..., k]) else float(np.linalg.norm(error[..., k])) for k in range(3)]
    maximum = float(np.max(np.abs(error)))
    ledger = np.asarray(record['cumulative_boundary_volume'], dtype=float).reshape(2*(first['nx']+first['ny']), 4)
    if not np.isfinite(ledger).all() or np.any(ledger[:, 3] != 0):
        raise ValueError('Invalid/nonzero-foam cumulative ledger')
    nx, ny, dx = first['nx'], first['ny'], first['cell_meters']
    signs = np.r_[-np.ones(ny), np.ones(ny), -np.ones(nx), np.ones(nx)]
    water_change = float(np.sum(gpu[..., 0]-first['state'][..., 0])*dx*dx)
    outward = float(np.sum(signs*ledger[:, 0])*dx)
    report.update(cpu_completed=True, relative_state_errors=relative, maximum_state_error=maximum,
                  state_gates_passed=maximum < 1e-4 and max(relative) < 2e-5,
                  gpu_water_change_m3=water_change, gpu_cumulative_outward_m3=outward,
                  gpu_float_balance_m3=water_change+outward)
    return state, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    state_path = args.report.with_suffix('.last-state.npy')
    if args.report.exists() or state_path.exists():
        raise FileExistsError(args.report)
    data = args.input.read_bytes()
    state, report = replay(json.loads(data))
    report['source_sha256'] = hashlib.sha256(data).hexdigest()
    report['implementation_hashes'] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('audit_live_nonlinear_owner.py', 'audit_live_temporal_evolution.py',
                     'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py', 'total_depth_nonlinear_pressure.py', 'breaking_front_reference.py')}
    with state_path.open('xb') as stream:
        np.save(stream, state)
    report['last_state'] = str(state_path.resolve())
    report['state_sha256'] = hashlib.sha256(state_path.read_bytes()).hexdigest()
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps(report, indent=2, allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
