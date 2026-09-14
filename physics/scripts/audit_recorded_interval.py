"""Isolate one observed interval from its recorded evolved GPU input.

This deliberately resets only a diagnostic CPU control to a captured GPU state.
It cannot qualify uninterrupted evolution or replace the full-history comparison.
Boundary history, independent equations and default physical timesteps are intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import audit_live_temporal_evolution as temporal
from audit_recorded_state_history import recorded_endpoints
from audit_recorded_evolution_steps import shoreline_model


def isolate(source, endpoints, interval):
    limiter=shoreline_model(source,source)
    raw = source['observations']
    if type(interval) is not int or not 0 <= interval < len(raw)-1:
        raise ValueError('Interval outside observed source pairs')
    a, b = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
                                     first=raw[interval], second=raw[interval+1]))
    def captured(value):
        return endpoints[(value['native_seconds'], (value['origin_x'], value['origin_y']))]
    initial, expected = captured(a), captured(b)
    duration, boundary = temporal.boundary_provider(a, b)
    state, stats = temporal.bank.advance(initial.copy(), a['bed'], a['cell_meters'], duration,
        max_trials=4096, boundary_at_time=boundary, breaking_model='hybrid_front', shoreline_limiter=limiter, **temporal.KW)
    error = abs(state-expected); worst = np.unravel_index(error.argmax(), error.shape)
    return state, dict(interval=interval, begin=a['native_seconds'], end=b['native_seconds'],
        maximum_state_error=float(error.max()), cells_over_1e_minus_4=int(np.sum(error.max(-1)>=1e-4)),
        worst_yxc=list(map(int, worst)), cpu=float(state[worst]), gpu=float(expected[worst]),
        statistics=stats, shoreline_limiter=limiter, full_history_qualified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('trace', type=Path)
    parser.add_argument('--interval', type=int, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(); output = args.report.with_suffix('.last-state.npy')
    if args.report.exists() or output.exists(): raise FileExistsError(args.report)
    data = args.source.read_bytes()
    endpoints, provenance = recorded_endpoints([args.trace], data)
    state, report = isolate(json.loads(data), endpoints, args.interval)
    report.update(schema='raftsim.recorded_interval_comparison.v1', scope=__doc__,
        source_sha256=hashlib.sha256(data).hexdigest(), traces=provenance,
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with output.open('xb') as stream: np.save(stream, state)
    with args.report.open('x') as stream: json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps(report, indent=2, allow_nan=False), flush=True)


if __name__ == '__main__': main()
