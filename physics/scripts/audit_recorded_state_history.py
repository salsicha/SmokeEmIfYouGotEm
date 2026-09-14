"""Locate independent CPU/GPU error at recorded source endpoints, without resets.

The complete original CPU evolution and default timesteps are unchanged.
Only exact-time, exact-origin GPU stage inputs from the SAME live source are
compared. Missing endpoint captures are unavailable, not interpolated states.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_recorded_stages import read_records
from audit_live_moving_owner import replay


def recorded_endpoints(paths, source_bytes):
    source = json.loads(source_bytes); expected_hash = hashlib.sha256(source_bytes).hexdigest()
    values = {}; provenance = []
    for path in paths:
        data = path.read_bytes(); metadata = json.loads(data)
        if not metadata.get('completed') or not metadata.get('final_state_exact_to_live'):
            raise ValueError('Unqualified recorded trace')
        if hashlib.sha256(Path(metadata['source']).read_bytes()).hexdigest() != expected_hash:
            raise ValueError('Recorded trace belongs to another live source history')
        if metadata.get('shoreline_limiter', 'binary') != source.get('shoreline_limiter', 'binary'):
            raise ValueError('Recorded endpoint uses a different shoreline model')
        binary = Path(metadata['binary']).read_bytes()
        for trial, stages, *_ in read_records(metadata, binary):
            index = trial['interval']
            if type(index) is not int or not 0 <= index < len(source['observations'])-1:
                raise ValueError('Recorded stage interval outside observed source pairs')
            if type(trial['trial']) is not int or trial['trial'] < 0:
                raise ValueError('Invalid recorded trial index')
            if trial['trial'] != 0: continue
            origin = source['observations'][index]
            if trial['begin'] != origin['native_seconds']:
                raise ValueError('Recorded first trial is not at the observed interval start')
            key = (trial['begin'], (origin['origin_x'], origin['origin_y']))
            value = stages[0]['state'][..., :3].astype(float)
            if key in values and not np.array_equal(values[key], value):
                raise ValueError('Overlapping endpoint captures differ')
            values[key] = value
        provenance.append(dict(trace=str(path.resolve()), trace_sha256=hashlib.sha256(data).hexdigest(),
                               binary_sha256=hashlib.sha256(binary).hexdigest()))
    if not values: raise ValueError('No recorded source endpoints')
    return values, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path); parser.add_argument('traces', nargs='+', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--states', type=Path,
                        help='Optional fresh NPZ of independent CPU states at captured endpoints')
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    if args.states is not None and args.states.exists(): raise FileExistsError(args.states)
    source_bytes = args.input.read_bytes()
    endpoints, provenance = recorded_endpoints(args.traces, source_bytes)
    checkpoints = []; saved_states = {}
    def compare(state, time, origin):
        key = (time, origin)
        if key not in endpoints: return
        gpu = endpoints[key]; error = abs(state-gpu)
        worst = np.unravel_index(error.argmax(), error.shape)
        row = dict(native_seconds=time, origin_meters=list(origin),
            maximum_state_error=float(error.max()), cells_over_1e_minus_4=int(np.sum(error.max(axis=-1)>=1e-4)),
            worst_yxc=list(map(int, worst)), expected=float(state[worst]), actual=float(gpu[worst]))
        checkpoints.append(row); print(json.dumps(row), flush=True)
        if args.states is not None:
            saved_states['checkpoint_'+str(len(checkpoints)-1)] = state.copy()
    _, final = replay(json.loads(source_bytes), on_state=compare)
    if final['cpu_completed'] and len(checkpoints) != len(endpoints):
        raise ValueError('CPU replay did not visit every captured endpoint exactly once')
    report = dict(schema='raftsim.recorded_state_history.v1', scope=__doc__,
        source_sha256=hashlib.sha256(source_bytes).hexdigest(), traces=provenance,
        checkpoints=checkpoints, final=final, available_endpoints=len(endpoints),
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    report['implementation_hashes']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('audit_recorded_state_history.py','audit_recorded_stages.py','audit_live_moving_owner.py',
                     'audit_live_temporal_evolution.py','total_depth_bank_replay.py','adaptive_hydrostatic_precision.py','continuous_shoreline_reconstruction.py',
                     'total_depth_nonlinear_pressure.py','pressure_cg_range_reference.py','breaking_front_reference.py')}
    if args.states is not None:
        with args.states.open('xb') as stream:
            np.savez(stream, **saved_states, source_sha256=np.array(report['source_sha256']),
                     checkpoints_json=np.array(json.dumps(checkpoints)))
        report['independent_states'] = dict(path=str(args.states.resolve()),
            sha256=hashlib.sha256(args.states.read_bytes()).hexdigest())
    with args.report.open('x') as stream: json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps(dict(report=str(args.report), checkpoints=len(checkpoints),
        final_maximum_state_error=final.get('maximum_state_error'), state_gates_passed=final['state_gates_passed'])), flush=True)


if __name__ == '__main__': main()
