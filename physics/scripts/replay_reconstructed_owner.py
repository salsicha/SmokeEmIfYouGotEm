"""Full original-start retained CPU history with reconstructed research pressure.

Only the process-scoped pressure model changes. Original source observations,
FV reconstruction/transport, adaptive SSP-RK2, CFL/minimum-dt/residual gates,
boundary interpolation and same-instant window transfer are reused unchanged.
Comparison to the retained FAILED old-model GPU endpoint is not new-model
accuracy qualification. No state reset, native integration or playable pass.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from audit_live_moving_owner import replay
from reconstructed_pressure_adapter import reconstructed_pressure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    state_path = args.report.with_suffix('.last-state.npy')
    progress_path = args.report.with_suffix('.progress.jsonl')
    if any(p.exists() for p in (args.report, state_path, progress_path)): raise FileExistsError(args.report)
    data = args.input.read_bytes(); record = json.loads(data)
    if record.get('shoreline_limiter') != 'unscaled': raise ValueError('Original unscaled history required')
    source_hash = hashlib.sha256(data).hexdigest()
    files = ('replay_reconstructed_owner.py', 'reconstructed_pressure_adapter.py',
        'reconstructed_nonlinear_pressure.py', 'reconstructed_acceleration_system.py',
        'directional_pressure_geometry.py', 'reconstructed_pressure_geometry.py',
        'reconstructed_pressure_rates.py', 'pressure_cut_face_reference.py',
        'audit_live_moving_owner.py', 'audit_live_temporal_evolution.py',
        'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py',
        'continuous_shoreline_reconstruction.py', 'total_depth_nonlinear_pressure.py',
        'pressure_cg_range_reference.py', 'breaking_front_reference.py')
    hashes = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in files}
    begin = time.perf_counter(); stages = 0
    with progress_path.open('x') as progress:
        def emit(value):
            value['wall_seconds'] = time.perf_counter()-begin
            encoded = json.dumps(value, allow_nan=False)
            progress.write(encoded+'\n'); progress.flush(); print(encoded, flush=True)
        def stage(value):
            nonlocal stages
            stages += 1
            emit(dict(event='reconstructed_pressure_stage', pressure_calls=stages, **value))
        def state_observed(state, native_seconds, origin):
            emit(dict(event='retained_history_endpoint', native_seconds=native_seconds,
                origin_meters=origin, maximum_depth=float(state[..., 0].max())))
        emit(dict(event='original_source_start', source_sha256=source_hash,
                  implementation_hashes=hashes, scope=__doc__))
        with reconstructed_pressure(stage):
            state, comparison = replay(record, on_state=state_observed)
        changed = [name for name, digest in hashes.items()
                   if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != digest]
        result = dict(schema='raftsim.reconstructed_owner_replay.v1', scope=__doc__,
            source_sha256=source_hash, implementation_hashes=hashes,
            implementation_files_changed_during_run=changed, pressure_calls=stages,
            wall_seconds=time.perf_counter()-begin, original_replay_report=comparison,
            qualification='CPU candidate history only; old failed GPU endpoint is not candidate accuracy truth. No physical/native/cost/playable acceptance.')
        emit(dict(event='reconstructed_history_terminal', cpu_completed=comparison['cpu_completed'],
                  error=comparison.get('error'), pressure_calls=stages))
    with state_path.open('xb') as out: np.save(out, state)
    result['last_state'] = dict(path=str(state_path.resolve()), sha256=hashlib.sha256(state_path.read_bytes()).hexdigest())
    with args.report.open('x') as out: json.dump(result, out, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))
    if changed or not comparison['cpu_completed']: raise SystemExit(1)


if __name__ == '__main__': main()
