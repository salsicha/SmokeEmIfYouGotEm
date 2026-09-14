"""Evolve two nearby recorded starts with each shoreline reconstruction.

This measures sensitivity, not accuracy against truth. Both controls use their
own evolving interior and the unchanged observed boundaries/default timestep.
The continuous option is an experimental CPU candidate, never a GPU parity gate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import audit_live_temporal_evolution as temporal
from audit_recorded_state_history import recorded_endpoints
from audit_recorded_evolution_steps import checkpoint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('endpoints', type=Path)
    parser.add_argument('checkpoints', type=Path); parser.add_argument('--interval', type=int, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--limiters',nargs='+',choices=('binary','continuous','unscaled'),default=['binary','continuous'])
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    source_bytes = args.source.read_bytes(); source = json.loads(source_bytes)
    initial_cpu, provenance = checkpoint(args.checkpoints, source_bytes, args.interval)
    recorded, traces = recorded_endpoints([args.endpoints], source_bytes)
    a, b = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
        first=source['observations'][args.interval], second=source['observations'][args.interval+1]))
    initial_gpu = recorded[(a['native_seconds'], (a['origin_x'], a['origin_y']))]
    duration, boundary = temporal.boundary_provider(a, b)
    results = []
    for limiter in args.limiters:
        finals, runs = [], []
        for name, initial in (('independent_cpu', initial_cpu), ('represented_gpu', initial_gpu)):
            final, stats = temporal.bank.advance(initial, a['bed'], a['cell_meters'], duration,
                max_trials=4096, boundary_at_time=boundary, breaking_model='hybrid_front',
                shoreline_limiter=limiter, **temporal.KW)
            finals.append(final); runs.append(dict(initial=name, statistics=stats))
            print(json.dumps(dict(limiter=limiter, initial=name, statistics=stats)), flush=True)
        error = abs(finals[0]-finals[1]); at = np.unravel_index(error.argmax(), error.shape)
        results.append(dict(limiter=limiter, maximum_difference=float(error.max()),
            worst_yxc=list(map(int, at)), independent_cpu=float(finals[0][at]),
            represented_gpu=float(finals[1][at]), cells_over_1e_minus_4=int(np.sum(error.max(-1)>=1e-4)), runs=runs))
    report = dict(schema='raftsim.reconstruction_interval_pair.v1', scope=__doc__,
        interval=args.interval, begin=a['native_seconds'], end=b['native_seconds'],
        maximum_initial_difference=float(abs(initial_cpu-initial_gpu).max()), results=results,
        source_sha256=hashlib.sha256(source_bytes).hexdigest(), checkpoint=provenance, traces=traces,
        accuracy_qualified=False, gameplay_qualified=False)
    report['implementation_hashes'] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('audit_reconstruction_interval_pair.py', 'audit_recorded_state_history.py',
            'audit_recorded_evolution_steps.py', 'audit_recorded_stages.py', 'audit_live_temporal_evolution.py',
            'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py', 'continuous_shoreline_reconstruction.py',
            'total_depth_nonlinear_pressure.py', 'pressure_cg_range_reference.py', 'breaking_front_reference.py')}
    with args.report.open('x') as stream: json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps(dict(report=str(args.report), results=[{k:v for k,v in r.items() if k!='runs'} for r in results])))


if __name__=='__main__': main()
