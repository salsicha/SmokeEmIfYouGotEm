"""Independent retained-state replay across explicit same-instant window moves.

This verifies the finite moving control volume, not persistence or coupling of
departed waves/foam into the outer solver, visuals, sustained capacity or FPS.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import audit_live_temporal_evolution as temporal


def source(raw):
    nx, ny = raw['nx'], raw['ny']
    if not isinstance(nx, int) or not isinstance(ny, int) or not (2 <= nx <= 512 and 2 <= ny <= 512):
        raise ValueError('Invalid source dimensions')
    out = {key: raw[key] for key in ('nx', 'ny', 'cell_meters', 'origin_x', 'origin_y', 'native_seconds', 'revision')}
    if not all(np.isfinite(v) for v in out.values()) or out['cell_meters'] <= 0 or out['revision'] <= 0:
        raise ValueError('Invalid source registration')
    for key, shape in [('state', (ny, nx, 4)), ('bed', (ny, nx)), ('exterior_state', (2*(nx+ny), 4)),
                       ('exterior_bed', (2*(nx+ny),)), ('face_normal_velocity', (2*(nx+ny),))]:
        out[key] = np.asarray(raw[key], dtype=float).reshape(shape)
        if not np.isfinite(out[key]).all(): raise ValueError('Nonfinite source '+key)
    for key in ('state', 'exterior_state'):
        s = out[key]
        if np.any(s[..., 0] < 0) or np.any(s[..., 3] != 0) or np.any(s[..., 1:3][s[..., 0] == 0] != 0):
            raise ValueError('Invalid depth/momentum or nonzero foam in zero-foam control')
        with np.errstate(over='ignore', invalid='ignore'):
            u = np.divide(s[..., 1:3], s[..., 0, None], out=np.zeros_like(s[..., 1:3]), where=s[..., 0, None]>0)
        if not np.isfinite(u).all(): raise ValueError('Invalid source velocity')
    return out


def transfer(state, closing, opening):
    if any(closing[k] != opening[k] for k in ('nx', 'ny', 'cell_meters', 'native_seconds')):
        raise ValueError('Move must preserve grid and exact physical instant')
    if opening['revision'] <= closing['revision']: raise ValueError('Move revision must increase')
    shift = (np.array([opening['origin_x'], opening['origin_y']])-np.array([closing['origin_x'], closing['origin_y']]))/closing['cell_meters']
    nx, ny = closing['nx'], closing['ny']
    if not np.isfinite(shift).all() or np.any(shift != np.floor(shift)) or np.all(shift == 0) or np.any(abs(shift) >= [nx, ny]):
        raise ValueError('Move requires exact nonzero integer overlap')
    sx, sy = map(int, shift)
    new = (slice(max(0, -sy), min(ny, ny-sy)), slice(max(0, -sx), min(nx, nx-sx)))
    old = (slice(max(0, sy), min(ny, ny+sy)), slice(max(0, sx), min(nx, nx+sx)))
    for key in ('state', 'bed'):
        if not np.array_equal(opening[key][new], closing[key][old]):
            raise ValueError('Same-instant overlap differs: '+key)
    result = opening['state'][..., :3].copy()
    result[new] = state[old]
    entering = opening['state'][..., :3].copy(); entering[new] = 0
    departing = state.copy(); departing[old] = 0
    return result, entering-departing, dict(shift_xy=[sx, sy], overlap_cells=state[old].shape[0]*state[old].shape[1])


def replay(record, *, on_state=None):
    if record.get('schema') != 'raftsim.live_nonlinear_owner_audit.v1': raise ValueError('Invalid owner schema')
    limiter = record.get('shoreline_limiter', 'binary')
    if limiter not in ('binary', 'continuous', 'unscaled'): raise ValueError('Invalid captured shoreline model')
    summary = record.get('summary')
    if limiter != 'binary' and summary is None:
        raise ValueError('Candidate history requires persisted evolution mode')
    if summary is not None and (len(summary) != 4 or summary[3] != {'binary':1,'continuous':3,'unscaled':5}[limiter]):
        raise ValueError('Captured shoreline model differs from persisted evolution mode')
    inputs = record['observations']
    if not 2 <= len(inputs) <= 256: raise ValueError('Unbounded/missing observations')
    values = [source(r) for r in inputs]
    clock = np.asarray(record['progress'], dtype=float)
    if clock.shape != (4,) or not np.isfinite(clock).all() or clock[2] < 0: raise ValueError('Invalid clock')
    target = float(clock[0]+clock[1]); first = values[0]
    if not first['native_seconds'] <= target <= values[-1]['native_seconds']: raise ValueError('Clock outside source range')
    moves = int(record['completed_moves'])
    if moves != record['completed_moves'] or not 0 <= moves < len(values): raise ValueError('Invalid move count')
    state = first['state'][..., :3].copy(); exchange = np.zeros_like(state)
    def observe_state(time, domain):
        if on_state is not None:
            view = state.view(); view.flags.writeable = False
            on_state(view, time, (domain['origin_x'], domain['origin_y']))
    observe_state(first['native_seconds'], first)
    current = first; completed_moves = 0
    report = dict(schema='raftsim.live_moving_owner_comparison.v1', scope=__doc__, gpu_failure=record['failure'],
                  cpu_completed=False, state_gates_passed=False, scene_accepted=False, normal_solver_promoted=False,
                  target_native_seconds=target, intervals=[], moves=[])
    report['shoreline_limiter'] = limiter
    for index, (a, b) in enumerate(zip(values, values[1:])):
        moved = (a['origin_x'], a['origin_y']) != (b['origin_x'], b['origin_y'])
        if moved:
            if b['native_seconds'] > target or completed_moves == moves: break
            state, delta, stats = transfer(state, a, b); exchange += delta
            completed_moves += 1; current = b; report['moves'].append(dict(native_seconds=b['native_seconds'], **stats))
            observe_state(b['native_seconds'], b)
            continue
        if target <= a['native_seconds']: break
        # Reuse the strict independent temporal-bracket validator, never a
        # synthetic source time or resampled boundary at a moved location.
        aa, bb = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1', first=inputs[index], second=inputs[index+1]))
        duration, boundary = temporal.boundary_provider(aa, bb)
        requested = min(duration, target-aa['native_seconds'])
        try:
            state, stats = temporal.bank.advance(state, aa['bed'], aa['cell_meters'], requested,
                max_trials=4096, boundary_at_time=boundary, breaking_model='hybrid_front', shoreline_limiter=limiter, **temporal.KW)
        except (ValueError, FloatingPointError, temporal.bank.ReplayExhausted, temporal.bank.ReplayInvalidRate) as error:
            report['error'] = str(error)
            return getattr(error, 'state', state), report
        report['intervals'].append(dict(begin=aa['native_seconds'], requested_seconds=requested, statistics=stats)); current = b
        observe_state(aa['native_seconds']+requested, a)
    if completed_moves != moves or [current['origin_x'], current['origin_y']] != record['state_origin_meters']:
        raise ValueError('Replayed ownership does not match captured state origin/move count')
    gpu = np.asarray(record['state'], dtype=float).reshape(first['ny'], first['nx'], 4)
    if not np.isfinite(gpu).all() or np.any(gpu[..., 0] < 0) or np.any(gpu[..., 3] != 0): raise ValueError('Invalid/nonzero-foam GPU state')
    error = state-gpu[..., :3]
    relative = [float(np.linalg.norm(error[..., k])/max(np.linalg.norm(state[..., k]), np.finfo(float).tiny)) for k in range(3)]
    window = np.asarray(record['window_exchange'], dtype=float).reshape(first['ny'], first['nx'], 4)
    faces = np.asarray(record['cumulative_boundary_volume'], dtype=float).reshape(2*(first['nx']+first['ny']), 4)
    if not np.isfinite(window).all() or not np.isfinite(faces).all() or np.any(window[..., 3] != 0) or np.any(faces[:, 3] != 0):
        raise ValueError('Invalid/nonzero-foam inventory')
    signs = np.r_[-np.ones(first['ny']), np.ones(first['ny']), -np.ones(first['nx']), np.ones(first['nx'])]
    dx = first['cell_meters']
    residual = np.sum(gpu[..., 0]-first['state'][..., 0]-window[..., 0])*dx*dx+np.sum(signs*faces[:, 0])*dx
    report.update(cpu_completed=True, state_gates_passed=bool(abs(error).max()<1e-4 and max(relative)<2e-5),
                  maximum_state_error=float(abs(error).max()), relative_state_errors=relative,
                  maximum_window_inventory_error=float(abs(exchange-window[..., :3]).max()),
                  gpu_float_water_balance_m3=float(residual))
    return state, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path); parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(); output = args.report.with_suffix('.last-state.npy')
    if args.report.exists() or output.exists(): raise FileExistsError(args.report)
    data = args.input.read_bytes()
    observed = 0
    def progress(state, time, origin):
        nonlocal observed
        observed += 1
        if observed == 1 or observed % 8 == 0:
            print(json.dumps(dict(event='independent_history_progress',states=observed,
                native_seconds=time,origin_meters=origin)),flush=True)
    record = json.loads(data)
    provenance = None
    if 'source_history' in record:
        original_bytes = Path(record['source_history']).read_bytes()
        original = json.loads(original_bytes)
        if record['observations'] != original['observations']:
            raise ValueError('Replayed source observations differ from the original captured history')
        if (record['completed_moves'] != original['completed_moves'] or
            record['completed_intervals'] != original['completed_intervals'] or
            sum(record['progress'][:2]) != sum(original['progress'][:2]) or
            record['state_origin_meters'] != original['state_origin_meters']):
            raise ValueError('Replayed endpoint/ownership differs from original captured history')
        provenance = dict(path=record['source_history'], sha256=hashlib.sha256(original_bytes).hexdigest())
    state, report = replay(record,on_state=progress)
    if provenance is not None: report['original_history'] = provenance
    report.update(source_sha256=hashlib.sha256(data).hexdigest(), implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    report['implementation_hashes'] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('audit_live_moving_owner.py', 'audit_live_temporal_evolution.py',
                     'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py', 'continuous_shoreline_reconstruction.py',
                     'total_depth_nonlinear_pressure.py', 'pressure_cg_range_reference.py', 'breaking_front_reference.py')}
    serialized = json.dumps(report, indent=2, allow_nan=False)
    with output.open('xb') as stream: np.save(stream, state)
    with args.report.open('x') as stream: stream.write(serialized)
    print(serialized)


if __name__ == '__main__': main()
