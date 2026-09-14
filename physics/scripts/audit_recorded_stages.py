"""Compare recorded GPU stages on identical represented inputs; no gate changes."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from breaking_front_reference import dispersion_fraction
import audit_live_temporal_evolution as temporal
from total_depth_nonlinear_pressure import nonlinear_pressure_force


N = 128*128
STAGE_BYTES = N*56
RECORD_BYTES = N*128+48
POLYNOMIAL_RECORD_BYTES = N*256+48


def read_records(metadata, binary):
    schema = metadata.get('schema')
    if schema not in ('raftsim.recorded_nonlinear_stages.v1', 'raftsim.recorded_nonlinear_stages.v2'):
        raise ValueError('Invalid recorded-stage schema')
    polynomials = schema == 'raftsim.recorded_nonlinear_stages.v2'
    record_bytes = POLYNOMIAL_RECORD_BYTES if polynomials else RECORD_BYTES
    if not 1 <= len(metadata['trials']) <= (64 if polynomials else 128):
        raise ValueError('Invalid bounded stage count')
    if len(binary) != len(metadata['trials'])*record_bytes:
        raise ValueError('Incomplete/trailing recorded stage binary')
    for index, raw in enumerate(metadata['trials']):
        if raw['byte_offset'] != index*record_bytes:
            raise ValueError('Unexpected stage offset')
        at = raw['byte_offset']
        def field(components, dtype='<f4'):
            nonlocal at
            data = np.frombuffer(binary, dtype=dtype, count=N*components, offset=at)
            at += N*components*4
            return data.reshape(128, 128, components) if components > 1 else data.reshape(128, 128)
        stages = []
        for _ in range(2):
            stages.append(dict(state=field(4), rate=field(4), geometry=field(2),
                               pairs=field(1, '<u4'), fraction=field(1), force=field(2)))
            if polynomials:
                for name in ('raw_x', 'raw_y', 'slope_x', 'slope_y'):
                    stages[-1][name] = field(4)
        final = field(4)
        progress = np.frombuffer(binary, dtype='<f4', count=4, offset=at)
        info = np.frombuffer(binary, dtype='<f4', count=4, offset=at+16)
        diagnostics = np.frombuffer(binary, dtype='<u4', count=4, offset=at+32)
        yield raw, stages, final, progress, info, diagnostics


def analyze(metadata, binary):
    results = []
    for trial, stages, final, progress, info, diagnostics in read_records(metadata, binary):
        for k, stage in enumerate(stages):
            geometry, rate = stage['geometry'].astype(float), stage['rate'].astype(float)
            pairs = [(stage['pairs'] & 1) != 0, (stage['pairs'] & 2) != 0]
            expected, stats = dispersion_fraction(geometry[..., 0], geometry[..., 1], rate[..., 0], pairs, .5)
            error = abs(expected-stage['fraction'])
            worst = np.unravel_index(error.argmax(), error.shape)
            results.append(dict(interval=trial['interval'], trial=trial['trial'], stage=k,
                begin=trial['begin'], dt=trial['attempted_dt'], maximum_fraction_error=float(error.max()),
                cells_over_2e_minus_5=int(np.sum(error >= 2e-5)), worst_yx=list(map(int, worst)),
                expected=float(expected[worst]), actual=float(stage['fraction'][worst]),
                front_statistics=stats))
    return dict(schema='raftsim.recorded_stage_comparison.v1', scope=__doc__,
                final_state_exact_to_live=metadata['final_state_exact_to_live'],
                maximum_fraction_error=max(r['maximum_fraction_error'] for r in results), stages=results)


def operators(metadata, binary, source):
    # Imported here because the shared model validator also uses read_records.
    from audit_recorded_evolution_steps import shoreline_model
    limiter = shoreline_model(metadata, source)
    raw = source['observations']
    indices = {trial['interval'] for trial in metadata['trials']}
    if any(not isinstance(i, int) or not 0 <= i < len(raw)-1 for i in indices):
        raise ValueError('Recorded stage interval outside observed source pairs')
    # Validate only brackets actually used by captured stages. Future queued
    # windows are not this fixed-domain operator's inputs.
    pairs = {i: temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1', first=raw[i], second=raw[i+1]))
             for i in indices}
    results = []
    for trial, stages, final, progress, info, diagnostics in read_records(metadata, binary):
        a, b = pairs[trial['interval']]
        _, boundary = temporal.boundary_provider(a, b)
        for k, gpu in enumerate(stages):
            elapsed = trial['begin']-a['native_seconds']+(trial['attempted_dt'] if k else 0.)
            es, eb, trace = boundary(elapsed, None)
            state = gpu['state'][..., :3].astype(float)
            captured = {}
            original = temporal.bank.nonlinear_pressure_force
            def capture(*args, **kwargs):
                captured.update(pairs=[v.copy() for v in args[4]], fraction=kwargs['dispersion_fraction'].copy(),
                                slope=kwargs['bed_slope'].copy())
                return np.zeros_like(args[2]), [dict(relative_residual=0., iterations=0)]
            try:
                temporal.bank.nonlinear_pressure_force = capture
                hydro, _ = temporal.bank.rate(state, a['bed'], .5, exterior=(es, eb), pressure_boundary=trace,
                    breaking_model='hybrid_front', shoreline_limiter=limiter, **temporal.KW)
            finally:
                temporal.bank.nonlinear_pressure_force = original
            packed = captured['pairs'][0].astype(np.uint32)+2*captured['pairs'][1].astype(np.uint32)
            h = state[..., 0]
            velocity = np.divide(state[..., 1:], h[..., None], out=np.zeros_like(state[..., 1:]), where=h[..., None]>0)
            actual_pairs = [(gpu['pairs'] & 1) != 0, (gpu['pairs'] & 2) != 0]
            force, stats = nonlinear_pressure_force(h, a['bed'], velocity, np.zeros_like(velocity), actual_pairs, .5,
                interpolation='depth_weighted', formulation='kinematic',
                mass_rate=gpu['rate'][..., 0].astype(float), momentum_rate=gpu['rate'][..., 1:3].astype(float),
                bed_slope=captured['slope'].astype(np.float32).astype(float),
                dispersion_fraction=gpu['fraction'].astype(float), boundary_velocity=trace)
            rate_error = np.abs(hydro-gpu['rate'][..., :3])
            force_error = np.abs(force-gpu['force'])
            worst = np.unravel_index(force_error.argmax(), force_error.shape)
            classification_error = np.abs(captured['fraction']-gpu['fraction'])
            results.append(dict(interval=trial['interval'], trial=trial['trial'], stage=k, begin=trial['begin'],
                hydro_max_error=float(rate_error.max()), hydro_component_max=rate_error.max(axis=(0, 1)).tolist(),
                graph_mismatches=int(np.sum(packed != gpu['pairs'])),
                classification_from_cpu_fv_max_error=float(classification_error.max()),
                force_max_error=float(force_error.max()), force_worst_yxc=list(map(int, worst)),
                force_expected=float(force[worst]), force_actual=float(gpu['force'][worst]),
                force_cluster_max_error=float(force_error[76:80,70:75].max()),
                pressure_stats=stats))
    return dict(schema='raftsim.recorded_operators_comparison.v1',
                shoreline_limiter=limiter,
                scope='Independent CPU FV on each recorded GPU state; independent CPU pressure on recorded GPU rate/graph/fraction. No state repair or gate changes.',
                stages=results, maximum_force_error=max(v['force_max_error'] for v in results),
                maximum_hydro_error=max(v['hydro_max_error'] for v in results))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--operators', action='store_true')
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    data = args.trace.read_bytes(); metadata = json.loads(data)
    if (not metadata.get('completed') or not metadata.get('final_state_exact_to_live') or
            (metadata.get('source_evolution_failed') and not metadata.get('retained_failure_exact'))):
        raise ValueError('Exact completed diagnostic capture required')
    binary_path = Path(metadata['binary']); binary = binary_path.read_bytes()
    report = operators(metadata, binary, json.loads(Path(metadata['source']).read_bytes())) if args.operators else analyze(metadata, binary)
    report.update(source_evolution_failed=metadata.get('source_evolution_failed', False),
                  retained_failure_exact=metadata.get('retained_failure_exact', False),
                  source_sha256=hashlib.sha256(Path(metadata['source']).read_bytes()).hexdigest(),
                  trace_sha256=hashlib.sha256(data).hexdigest(), binary_sha256=hashlib.sha256(binary).hexdigest(),
                  implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in report.items() if k != 'stages'}, indent=2))
    key = 'force_max_error' if args.operators else 'maximum_fraction_error'
    print(json.dumps(sorted(report['stages'], key=lambda x: x[key], reverse=True)[:5], indent=2))


if __name__ == '__main__':
    main()
