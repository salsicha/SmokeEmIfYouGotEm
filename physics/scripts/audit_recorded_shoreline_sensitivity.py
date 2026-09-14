"""Diagnose shoreline-polynomial continuity between independent and GPU states.

Interpolated states are explicitly diagnostic probes, never runtime replacements
or an accuracy oracle. The original captured inputs and reference are unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import audit_live_temporal_evolution as temporal
from audit_recorded_stages import read_records
from diagnose_recorded_polynomials import exact_face, exact_slopes


def probe(state, bed, dx, exterior, *, limiter='binary'):
    """Observe the actual reference's raw/flattened reconstructions, without edits."""
    captures = []
    original = temporal.bank.hydrostatic_faces
    def capture(*args, **kwargs):
        value = original(*args, **kwargs)
        captures.append(dict(axis=args[4], raw=kwargs.get('flattened') is None and kwargs.get('slope_factors') is None,
            h=state[..., 0], dh=args[2].copy(), deta=args[3].copy(),
            positive=np.take(value[4], range(1, value[4].shape[args[4]]), axis=args[4]),
            negative=np.take(value[5], range(value[5].shape[args[4]]-1), axis=args[4])))
        return value
    try:
        temporal.bank.hydrostatic_faces = capture
        rate, _ = temporal.bank.rate(state, bed, dx, second_order=True, exterior=exterior, shoreline_limiter=limiter)
    finally:
        temporal.bank.hydrostatic_faces = original
    raw = {r['axis']: r for r in captures if r['raw']}
    return rate, raw


def compare(cpu, gpu, bed, dx, exterior):
    cpu_rate, cpu_raw = probe(cpu, bed, dx, exterior)
    gpu_rate, gpu_raw = probe(gpu, bed, dx, exterior)
    difference = abs(cpu_rate-gpu_rate)
    worst = np.unravel_index(difference.argmax(), difference.shape)
    decisions = []
    for axis in (1, 0):
        left, right = cpu_raw[axis], gpu_raw[axis]
        def partial(row):
            return (row['h'] > 0) & ((row['positive'] == 0) | (row['negative'] == 0))
        for point in map(tuple, np.argwhere(partial(left) != partial(right))):
            cases = []
            for name, row in (('cpu', left), ('gpu', right)):
                dh, de = exact_slopes(row['h'], bed, *point, axis)
                pos = exact_face(row['h'], bed, *point, axis, 1)
                neg = exact_face(row['h'], bed, *point, axis, -1)
                cases.append(dict(name=name, depth=float(row['h'][point]),
                    dh=float(dh), deta=float(de), positive=float(row['positive'][point]),
                    negative=float(row['negative'][point]), exact_positive=float(pos),
                    exact_negative=float(neg), flattened=bool(partial(row)[point])))
            decisions.append(dict(axis=axis, yx=list(map(int, point)), cases=cases))
    return dict(maximum_input_error=float(abs(cpu-gpu).max()), maximum_rate_error=float(difference.max()),
        worst_yxc=list(map(int, worst)), cpu_rate=float(cpu_rate[worst]), gpu_rate=float(gpu_rate[worst]),
        changed_shoreline_decisions=decisions), cpu_rate, gpu_rate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path); parser.add_argument('states', type=Path)
    parser.add_argument('--interval', type=int, required=True); parser.add_argument('--trial', type=int, required=True)
    parser.add_argument('--stage', type=int, choices=(0, 1), required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    trace_bytes = args.trace.read_bytes(); metadata = json.loads(trace_bytes)
    if not metadata.get('completed') or not metadata.get('final_state_exact_to_live'):
        raise ValueError('Unqualified recorded trace')
    source_bytes = Path(metadata['source']).read_bytes(); source = json.loads(source_bytes)
    binary = Path(metadata['binary']).read_bytes()
    if not 0 <= args.interval < len(source['observations'])-1 or args.trial < 0:
        raise ValueError('Invalid recorded trial')
    trial, stages, *_ = next(r for r in read_records(metadata, binary)
        if r[0]['interval']==args.interval and r[0]['trial']==args.trial)
    a, b = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
        first=source['observations'][args.interval], second=source['observations'][args.interval+1]))
    _, boundary = temporal.boundary_provider(a, b)
    es, eb, _ = boundary(trial['begin']-a['native_seconds']+(trial['attempted_dt'] if args.stage else 0), None)
    with np.load(args.states, allow_pickle=False) as archive:
        if archive['source_sha256'].item()!=hashlib.sha256(source_bytes).hexdigest():
            raise ValueError('CPU states belong to another live source')
        cpu = archive[str(args.trial)+('_stage' if args.stage else '_input')].copy()
    gpu = stages[args.stage]['state'][..., :3].astype(float)
    result, _, gpu_rate = compare(cpu, gpu, a['bed'], a['cell_meters'], (es, eb))
    result['represented_gpu_rate_error'] = float(abs(gpu_rate-stages[args.stage]['rate'][..., :3]).max())
    candidate_cpu, _ = probe(cpu, a['bed'], a['cell_meters'], (es, eb), limiter='continuous')
    candidate_gpu, _ = probe(gpu, a['bed'], a['cell_meters'], (es, eb), limiter='continuous')
    error = abs(candidate_cpu-candidate_gpu); at = np.unravel_index(error.argmax(), error.shape)
    result['continuous_candidate'] = dict(maximum_rate_error=float(error.max()),
        worst_yxc=list(map(int, at)), cpu_rate=float(candidate_cpu[at]), gpu_rate=float(candidate_gpu[at]),
        scope='CPU evaluation on both nearby inputs with experimental limiter; NOT a GPU implementation or full-history gate')
    result.update(schema='raftsim.recorded_shoreline_sensitivity.v1', scope=__doc__, trial=trial, stage=args.stage,
        source_sha256=hashlib.sha256(source_bytes).hexdigest(), trace_sha256=hashlib.sha256(trace_bytes).hexdigest(),
        binary_sha256=hashlib.sha256(binary).hexdigest(), states_sha256=hashlib.sha256(args.states.read_bytes()).hexdigest())
    result['implementation_hashes'] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('audit_recorded_shoreline_sensitivity.py', 'audit_recorded_stages.py',
            'audit_live_temporal_evolution.py', 'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py',
            'diagnose_recorded_polynomials.py', 'continuous_shoreline_reconstruction.py')}
    with args.report.open('x') as stream: json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__=='__main__': main()
