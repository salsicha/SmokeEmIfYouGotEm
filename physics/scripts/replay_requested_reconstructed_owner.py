"""Requested-endpoint reconstructed CPU replay, not the old failure-time prefix.

Read the requested endpoint/ownership from the original completed request whose
observations are byte-for-byte equivalent as parsed data. Evolve from the FIRST
original source state using every original boundary bracket and same-instant
transfer through that endpoint. Never shorten a step at the old failure clock.
No native, independent accuracy, outer-wave coupling or playable acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import audit_live_temporal_evolution as temporal
from audit_live_moving_owner import source, transfer
from reconstructed_pressure_adapter import reconstructed_pressure


def requested_replay(record, request, emit=lambda value: None):
    if (record.get('schema') != 'raftsim.live_nonlinear_owner_audit.v1'
            or record.get('shoreline_limiter') != 'unscaled'
            or not request.get('completed_requested_intervals')
            or record['observations'] != request['observations']
            or record['requested_moves'] != request['requested_moves']):
        raise ValueError('Matching original unscaled source and completed requested endpoint required')
    values = [source(raw) for raw in record['observations']]
    target = float(sum(request['progress'][:2])); expected_moves = request['requested_moves']
    if (not values or not values[0]['native_seconds'] <= target <= values[-1]['native_seconds']
            or target != request['completed_native_seconds']):
        raise ValueError('Requested clock differs from the original completed endpoint')
    state = values[0]['state'][..., :3].copy()
    current_time = values[0]['native_seconds']; current = values[0]; moves = 0
    result = dict(scope=__doc__, completed=False, target_native_seconds=target,
        source_start_native_seconds=current_time, reached_native_seconds=current_time,
        required_moves=expected_moves, completed_moves=0, intervals=[], moves=[])
    emit(dict(event='requested_history_start', native_seconds=current_time, target_native_seconds=target))
    for index, (a, b) in enumerate(zip(values, values[1:])):
        if a['native_seconds'] > target: break
        moved = (a['origin_x'], a['origin_y']) != (b['origin_x'], b['origin_y'])
        if moved:
            if b['native_seconds'] > target: break
            if current_time != a['native_seconds']: raise ValueError('Missing retained interval before move')
            state, _, stats = transfer(state, a, b)
            moves += 1; current = b
            result['moves'].append(dict(native_seconds=current_time, **stats))
            result['completed_moves'] = moves
            emit(dict(event='requested_history_move', native_seconds=current_time, **stats))
            continue
        if current_time >= target: continue  # A same-instant endpoint move may still follow.
        if current_time != a['native_seconds']: raise ValueError('Source interval is not contiguous')
        aa, bb = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
            first=record['observations'][index], second=record['observations'][index+1]))
        duration, boundary = temporal.boundary_provider(aa, bb)
        seconds = min(duration, target-current_time)
        def accepted(previous, next_state, stats):
            emit(dict(event='requested_history_accepted_step', interval=index,
                native_seconds=aa['native_seconds']+stats['elapsed_s'], **stats))
        try:
            state, stats = temporal.bank.advance(state, aa['bed'], aa['cell_meters'], seconds,
                max_trials=4096, boundary_at_time=boundary, breaking_model='hybrid_front',
                shoreline_limiter='unscaled', on_step=accepted, **temporal.KW)
        except (ValueError, FloatingPointError, temporal.bank.ReplayExhausted, temporal.bank.ReplayInvalidRate) as error:
            diagnostics = getattr(error, 'diagnostics', {})
            result.update(error=str(error), failure_diagnostics=diagnostics,
                reached_native_seconds=current_time+diagnostics.get('elapsed_s', 0.))
            return getattr(error, 'state', state), result
        current_time = aa['native_seconds']+seconds; current = b
        result['intervals'].append(dict(begin=aa['native_seconds'], requested_seconds=seconds, statistics=stats))
        result['reached_native_seconds'] = current_time
    if (current_time != target or moves != expected_moves
            or [current['origin_x'], current['origin_y']] != request['state_origin_meters']):
        raise ValueError('Requested endpoint and ownership were not reached')
    result.update(completed=True, completed_moves=moves,
        qualification='Requested CPU history completed only; independent physical/native/cost/playable qualification still required.')
    return state, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path); parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    state_path = args.report.with_suffix('.last-state.npy'); progress_path = args.report.with_suffix('.progress.jsonl')
    if any(p.exists() for p in (args.report, state_path, progress_path)): raise FileExistsError(args.report)
    data = args.input.read_bytes(); record = json.loads(data)
    request_path = Path(record['source_history']); request_data = request_path.read_bytes(); request = json.loads(request_data)
    files = ('replay_requested_reconstructed_owner.py', 'reconstructed_pressure_adapter.py',
        'reconstructed_nonlinear_pressure.py', 'reconstructed_acceleration_system.py', 'directional_pressure_geometry.py',
        'reconstructed_pressure_geometry.py', 'reconstructed_pressure_rates.py', 'pressure_cut_face_reference.py',
        'audit_live_moving_owner.py', 'audit_live_temporal_evolution.py', 'total_depth_bank_replay.py',
        'adaptive_hydrostatic_precision.py', 'continuous_shoreline_reconstruction.py',
        'total_depth_nonlinear_pressure.py', 'pressure_cg_range_reference.py', 'breaking_front_reference.py')
    digest = lambda data: hashlib.sha256(data).hexdigest()
    hashes = {name: digest(Path(__file__).with_name(name).read_bytes()) for name in files}
    begin = time.perf_counter(); calls = 0
    with progress_path.open('x') as progress:
        def emit(value):
            value['wall_seconds'] = time.perf_counter()-begin
            encoded = json.dumps(value, allow_nan=False)
            progress.write(encoded+'\n'); progress.flush(); print(encoded, flush=True)
        def stage(value):
            nonlocal calls
            calls += 1; emit(dict(event='requested_pressure_stage', pressure_calls=calls, **value))
        emit(dict(event='requested_source_provenance', source_sha256=digest(data),
            request_source_sha256=digest(request_data), implementation_hashes=hashes))
        with reconstructed_pressure(stage): state, history = requested_replay(record, request, emit)
        changed = [name for name, sha in hashes.items() if digest(Path(__file__).with_name(name).read_bytes()) != sha]
        result = dict(schema='raftsim.requested_reconstructed_owner.v1', scope=__doc__, source_sha256=digest(data),
            request_source=dict(path=str(request_path), sha256=digest(request_data)), implementation_hashes=hashes,
            implementation_files_changed_during_run=changed, pressure_calls=calls, history=history)
        emit(dict(event='requested_history_terminal', completed=history['completed'], error=history.get('error')))
    with state_path.open('xb') as out: np.save(out, state)
    result['last_state'] = dict(path=str(state_path.resolve()), sha256=digest(state_path.read_bytes()))
    with args.report.open('x') as out: json.dump(result, out, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))
    if changed or not history['completed']: raise SystemExit(1)


if __name__ == '__main__': main()
