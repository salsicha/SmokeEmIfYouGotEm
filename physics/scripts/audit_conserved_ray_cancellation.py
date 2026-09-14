"""Separate stored-state and primitive-velocity rounding on an actual dry ray.

No pressure rerun, repair or time advance. For dry (h,m)=(0,0), the exact
linear ray (epsilon*h_t, epsilon*m_t) has constant m/h and zero partial-time
velocity derivative. Rounded probe states need not lie exactly on that ray.
Inspect their actual mt-u*ht residual instead of silently setting it to zero.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_recorded_stages import read_records
from audit_pressure_wetting_edge import capture_hydro
from audit_recorded_evolution_steps import shoreline_model
from audit_retained_failure_rates import velocity
import audit_live_temporal_evolution as temporal


def cancellation(depth, momentum, mass_rate, momentum_rate, rounded_velocity):
    h, m, ht, mt, u = map(lambda x: F(float(x)), (depth, momentum, mass_rate, momentum_rate, rounded_velocity))
    if h <= 0: raise ValueError('A represented positive ray depth is required')
    exact_u = m/h
    stored = mt-exact_u*ht
    rounded = mt-u*ht
    return dict(stored_state_conservative_residual=float(stored),
        primitive_velocity_rounding_residual=float(rounded-stored),
        actual_rounded_velocity_conservative_residual=float(rounded),
        stored_state_velocity_time_rate=float(stored/h),
        rounded_velocity_time_rate=float(rounded/h))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('probe', type=Path)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    digest = lambda data: hashlib.sha256(data).hexdigest()
    probe_data, trace_data = args.probe.read_bytes(), args.trace.read_bytes()
    probe, trace = json.loads(probe_data), json.loads(trace_data)
    source_data = Path(trace['source']).read_bytes(); binary = Path(trace['binary']).read_bytes()
    source = json.loads(source_data)
    if (probe['trace_sha256'] != digest(trace_data) or probe['binary_sha256'] != digest(binary)
            or probe['source_sha256'] != digest(source_data) or not trace.get('final_state_exact_to_live')
            or not trace.get('retained_failure_exact') or shoreline_model(trace, source) != 'unscaled'):
        raise ValueError('Exact original source and retained-failure provenance required')
    matches = [r for r in read_records(trace, binary) if r[0] == probe['trial']]
    if len(matches) != 1: raise ValueError('Exact captured trial required')
    trial, stages, *_ = matches[0]
    alpha = probe['probes'][0]['alpha']
    start, end = [s['state'][..., :3].astype(float) for s in stages]
    state = start+alpha*(end-start)
    a, b = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
        first=source['observations'][trial['interval']], second=source['observations'][trial['interval']+1]))
    _, boundary = temporal.boundary_provider(a, b)
    elapsed = trial['begin']-a['native_seconds']+alpha*trial['attempted_dt']
    cpu, _ = capture_hydro(state, a, boundary, elapsed, tuple(probe['edge_yx']), probe['component'], 'unscaled')
    rate = cpu['rate']; rows = []
    for original in probe['probes'][0]['directional_pressure_limit']['probes']:
        epsilon = original['parameter_seconds']; later = state+epsilon*rate; u = velocity(later)
        cells = []
        for record in original['activations']:
            p = tuple(record['yx'])
            if (state[p][0] != 0 or np.any(state[p][1:] != 0) or rate[p][0] <= 0
                    or later[p][0] != record['depth'] or not np.array_equal(u[p], record['velocity'])):
                raise ValueError('Does not reproduce the saved dry-ray probe')
            cells.append(dict(yx=list(p), original_FV_rate=rate[p].tolist(), represented_probe_state=later[p].tolist(),
                exact_linear_ray_velocity_time_rate=[0., 0.],
                components=[cancellation(later[p][0], later[p][c+1], rate[p][0], rate[p][c+1], u[p][c]) for c in (0, 1)],
                saved_pressure_acceleration=[f/later[p][0] for f in record['pressure_force']]))
        rows.append(dict(parameter_seconds=epsilon, cells=cells))
    result = dict(schema='raftsim.conserved_ray_cancellation.v1', scope=__doc__,
        input_probe_sha256=digest(probe_data), trace_sha256=digest(trace_data),
        source_sha256=digest(source_data), binary_sha256=digest(binary), probes=rows,
        implementation_hashes={name: digest(Path(__file__).with_name(name).read_bytes()) for name in
            ('audit_conserved_ray_cancellation.py', 'audit_pressure_wetting_edge.py', 'total_depth_bank_replay.py',
             'adaptive_hydrostatic_precision.py', 'audit_retained_failure_rates.py')},
        qualification='Explains actual represented-ray arithmetic; no repaired residual, dry closure or evolved history.')
    with args.report.open('x') as out: json.dump(result, out, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
