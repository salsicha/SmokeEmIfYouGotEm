"""Inspect recorded pre-failure rates without re-evolving or repairing state.

The capture must reproduce the retained failed state's bytes, clock, counters
and diagnostics from the original source start. A completed diagnostic capture
is NOT a successful simulation, independent CPU accuracy or playable acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_recorded_stages import read_records
from audit_recorded_evolution_steps import shoreline_model


def velocity(state):
    state = np.asarray(state, dtype=np.float64)
    if (not np.isfinite(state).all() or np.any(state[..., 0] < 0) or
            np.any(state[..., 1:3][state[..., 0] == 0] != 0)):
        raise ValueError('Invalid retained wet/dry state')
    return np.divide(state[..., 1:3], state[..., :1],
        out=np.zeros_like(state[..., 1:3]), where=state[..., :1] > 0)


def state_summary(state):
    speed = np.linalg.norm(velocity(state), axis=-1)
    at = np.unravel_index(speed.argmax(), speed.shape)
    return dict(maximum_speed_mps=float(speed[at]), fastest_yx=list(map(int, at)),
        fastest_state=np.asarray(state[at], dtype=float).tolist())


def cell_rates(stage, point):
    state = np.asarray(stage['state'][point], dtype=float)
    hydro = np.asarray(stage['rate'][point], dtype=float)
    pressure = np.asarray(stage['force'][point], dtype=float)
    if not np.isfinite(hydro).all() or not np.isfinite(pressure).all():
        raise ValueError('Nonfinite recorded rate')
    u = velocity(state)
    row = dict(yx=list(point), state=state.tolist(), velocity_mps=u.tolist(),
        hydro_rate=hydro.tolist(), pressure_momentum_rate=pressure.tolist(),
        dispersion_fraction=float(stage['fraction'][point]), pairs=int(stage['pairs'][point]))
    # du/dt = (d(hu)/dt - u*dh/dt)/h. Dry cells have no defined
    # acceleration: do not add a depth floor to manufacture one.
    row['hydro_acceleration_mps2'] = ((hydro[1:3]-u*hydro[0])/state[0]).tolist() if state[0] > 0 else None
    row['pressure_acceleration_mps2'] = (pressure/state[0]).tolist() if state[0] > 0 else None
    for name in ('raw_x', 'raw_y', 'slope_x', 'slope_y'):
        if name in stage:
            row[name] = stage[name][point].astype(float).tolist()
    return row


def analyze(metadata, binary, source, points):
    if (not metadata.get('completed') or not metadata.get('final_state_exact_to_live') or
            not metadata.get('source_evolution_failed') or not metadata.get('retained_failure_exact') or
            source.get('summary', [0, 0, 0])[2] != 2 or not source.get('failure')):
        raise ValueError('Exact retained-failure capture required; not a completed simulation')
    limiter = shoreline_model(metadata, source)
    if not points or any(len(p) != 2 or any(type(v) is not int or not 0 <= v < 128 for v in p) for p in points):
        raise ValueError('Selected cells must lie inside the captured grid')
    rows = []
    for trial, stages, final, clock, info, diagnostics in read_records(metadata, binary):
        rows.append(dict(trial=trial, stages=[dict(state_summary=state_summary(stage['state']),
            selected_cells=[cell_rates(stage, tuple(p)) for p in points]) for stage in stages],
            final_state_summary=state_summary(final), progress=clock.astype(float).tolist(),
            info=info.astype(float).tolist(), diagnostics=diagnostics.astype(int).tolist()))
    retained = np.array(source['state'], dtype=float).reshape(128, 128, 4)
    return dict(schema='raftsim.retained_failure_rates.v1', scope=__doc__,
        shoreline_limiter=limiter, source_failure=source['failure'],
        source_clock=source['progress'], source_summary=source['summary'],
        retained_state_summary=state_summary(retained), trials=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('--yx', type=int, nargs=2, action='append', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    data = args.trace.read_bytes(); metadata = json.loads(data)
    binary = Path(metadata['binary']).read_bytes(); source = Path(metadata['source']).read_bytes()
    report = analyze(metadata, binary, json.loads(source), args.yx)
    report.update(trace_sha256=hashlib.sha256(data).hexdigest(),
        binary_sha256=hashlib.sha256(binary).hexdigest(), source_sha256=hashlib.sha256(source).hexdigest(),
        implementation_hashes={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_retained_failure_rates.py', 'audit_recorded_stages.py', 'audit_recorded_evolution_steps.py')})
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps({key: value for key, value in report.items() if key != 'trials'}, indent=2))


if __name__ == '__main__':
    main()
