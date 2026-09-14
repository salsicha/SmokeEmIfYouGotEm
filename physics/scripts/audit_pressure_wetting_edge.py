"""Isolate one pressure-graph edge on actual recorded wetting-stage inputs.

The toggled edge is a counterfactual operator probe, NEVER an evolved state or
proposed dry threshold. Source geometry, h/hu/hv, FV rates, breaking fraction and
boundary traces are held fixed. No history, physics gate or playable path changes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import audit_live_temporal_evolution as temporal
from audit_recorded_stages import read_records
from audit_recorded_evolution_steps import shoreline_model
from audit_retained_failure_rates import velocity
import total_depth_nonlinear_pressure as pressure


def toggle_edge(pairs, depth, point, component):
    depth = np.asarray(depth)
    if depth.ndim != 2 or not depth.size or not np.isfinite(depth).all() or np.any(depth < 0):
        raise ValueError('Invalid pressure edge depth')
    if (type(component) is not int or component not in (0, 1) or len(point) != 2 or len(pairs) != 2 or
            any(type(v) is not int or not 0 <= v < n for v, n in zip(point, depth.shape))):
        raise ValueError('Invalid pressure edge')
    axis = 1-component
    neighbor = list(point); neighbor[axis] += 1; neighbor = tuple(neighbor)
    if neighbor[axis] >= depth.shape[axis] or depth[point] <= 0 or depth[neighbor] <= 0:
        raise ValueError('Probe requires an interior edge joining positive-depth cells')
    if any(np.shape(p) != depth.shape or np.asarray(p).dtype != bool for p in pairs):
        raise ValueError('Invalid boolean pressure graph')
    result = [p.copy() for p in pairs]
    result[component][point] = not result[component][point]
    return result, neighbor


def evaluate(gpu, bed, dx, trace, slope, pairs, points):
    state = gpu['state'].astype(float); h = state[..., 0]; u = velocity(state)
    rate = gpu['rate'].astype(float); captured = []
    force, stats = pressure.nonlinear_pressure_force(h, bed, u, np.zeros_like(u), pairs, dx,
        interpolation='depth_weighted', formulation='kinematic', mass_rate=rate[..., 0],
        momentum_rate=rate[..., 1:3], bed_slope=slope, dispersion_fraction=gpu['fraction'].astype(float),
        boundary_velocity=trace, on_pressure=lambda values: captured.extend(values))
    weights = pressure.depth_weights(h)
    integrated = sum(pole['weight']*pole['pressure'] for pole in captured)
    bottom = sum(pole['weight']*pole['bottom_pressure'] for pole in captured)
    divergence = -pressure.gradient(integrated, pairs, dx, weights)
    traction = -bottom[..., None]*slope
    column = pressure.pressure_column(h, integrated, bottom)
    matrix_densities = []
    for pole in captured:
        system = pressure.AccelerationSystem(h, bed, pairs, dx, pole['length'],
            interpolation='depth_weighted', bed_slope=slope, dispersion_fraction=gpu['fraction'].astype(float))
        scaled_velocity = system.root[..., None]*u
        matrix_densities.append(.5*pole['length']*system.fraction*(system.w(scaled_velocity)**2+
            .75*np.sum(system.b*scaled_velocity, axis=-1)**2))
    rows = []
    for point in points:
        rows.append(dict(yx=list(point), h=float(h[point]), velocity=u[point].tolist(),
            force=force[point].tolist(), acceleration=(force[point]/h[point]).tolist(),
            pressure_divergence=divergence[point].tolist(), bottom_traction=traction[point].tolist(),
            integrated_nonhydrostatic=float(integrated[point]), bottom_nonhydrostatic=float(bottom[point]),
            minimum_gauge_pressure=float(column['minimum'][point]),
            minimum_pressure_sigma=float(column['minimum_sigma'][point]),
            dispersive_matrix_quadratic_density_per_pole=[float(value[point]) for value in matrix_densities],
            poles=[{key: np.asarray(pole[key][point]).tolist() for key in
                ('quadratic', 'curvature', 'base', 'rhs', 'correction', 'pressure', 'bottom_pressure')}
                for pole in captured]))
    return force, dict(cells=rows, pressure_stats=stats,
        matrix_quadratic_scope='Per-pole positive quadratic form at the input velocity, not a proven invariant of the rational two-pole evolution or an energy acceptance gate.',
        dispersive_matrix_quadratic_integral_per_pole=[float(value.sum()*dx*dx) for value in matrix_densities],
        pressure_divergence_plus_traction_error=float(abs(force-divergence-traction).max()))


def capture_hydro(state, endpoint, boundary, elapsed, point, component, limiter):
    bed = endpoint['bed']; dx = endpoint['cell_meters']
    es, eb, trace = boundary(elapsed, None)
    original_faces = temporal.bank.hydrostatic_faces
    original_pressure = temporal.bank.nonlinear_pressure_force
    faces = []; cpu_pressure = {}
    def capture_faces(*args, **kwargs):
        value = original_faces(*args, **kwargs)
        if args[4] == 1-component:
            at = list(point); at[1-component] += 1; at = tuple(at)
            faces.append(dict(reconstructed_a=float(value[2][at]), reconstructed_b=float(value[3][at]),
                hydrostatic_a=float(value[4][at]), hydrostatic_b=float(value[5][at])))
        return value
    def capture_pressure(*args, **kwargs):
        cpu_pressure.update(pairs=[p.copy() for p in args[4]], fraction=kwargs['dispersion_fraction'].copy())
        return np.zeros_like(args[2]), [dict(relative_residual=0.)]
    try:
        temporal.bank.hydrostatic_faces = capture_faces
        temporal.bank.nonlinear_pressure_force = capture_pressure
        hydro, _ = temporal.bank.rate(state[..., :3], bed, dx, exterior=(es, eb), pressure_boundary=trace,
            breaking_model='hybrid_front', shoreline_limiter=limiter, **temporal.KW)
    finally:
        temporal.bank.hydrostatic_faces = original_faces
        temporal.bank.nonlinear_pressure_force = original_pressure
    result = dict(state=state.copy(), rate=hydro, force=np.zeros((*bed.shape, 2)),
        fraction=cpu_pressure['fraction'], pairs=cpu_pressure['pairs'][0].astype(np.uint32)+
            2*cpu_pressure['pairs'][1].astype(np.uint32))
    return result, faces


def stage_probe(gpu, endpoint, boundary, elapsed, point, component, limiter):
    state = gpu['state'].astype(float); bed = endpoint['bed']; dx = endpoint['cell_meters']
    _, eb, trace = boundary(elapsed, None)
    pairs = [(gpu['pairs'] & 1) != 0, (gpu['pairs'] & 2) != 0]
    changed, neighbor = toggle_edge(pairs, state[..., 0], point, component)
    slope = pressure.geometric_bed_slope(bed, dx, exterior_bed=eb).astype(np.float32).astype(float)
    cpu, faces = capture_hydro(state, endpoint, boundary, elapsed, point, component, limiter)
    actual, actual_report = evaluate(gpu, bed, dx, trace, slope, pairs, [point, neighbor])
    counter, counter_report = evaluate(gpu, bed, dx, trace, slope, changed, [point, neighbor])
    return dict(original_edge_open=bool(pairs[component][point]), hydrostatic_face_passes=faces,
        cpu_graph_matches_native=np.array_equal(cpu['pairs'], gpu['pairs']),
        same_input_native_hydro_max_error=float(abs(cpu['rate']-gpu['rate'][..., :3]).max()),
        same_input_native_force_max_error=float(abs(actual-gpu['force']).max()),
        actual=actual_report, one_edge_toggled_counterfactual=counter_report,
        toggled_minus_actual_force_at_owner=(counter[point]-actual[point]).tolist())


def bracket_transition(sample, is_open, iterations=48):
    """Find a closed/open bracket, not necessarily the first transition."""
    if type(iterations) is not int or not 1 <= iterations <= 52:
        raise ValueError('Invalid bounded transition iterations')
    left, right = (0., sample(0.)), (1., sample(1.))
    if is_open(left[1]) or not is_open(right[1]):
        raise ValueError('Input endpoints must bracket a closed/open edge')
    for _ in range(iterations):
        alpha = .5*(left[0]+right[0]); middle = (alpha, sample(alpha))
        if is_open(middle[1]): right = middle
        else: left = middle
    return left, right


def wetting_limit(stages, endpoint, boundary, elapsed, dt, point, component, limiter):
    """Coherent CPU operator on nearby interpolated states; never a history reset.

    Interpolation is only a sensitivity probe between the recorded stage inputs.
    Recompute the hydro rate, graph and breaking fraction for each probe. The
    source boundary is sampled inside the same original temporal bracket.
    """
    a, b = [stage['state'].astype(float) for stage in stages]
    def sample(alpha):
        return capture_hydro(a+alpha*(b-a), endpoint, boundary, elapsed+alpha*dt,
            point, component, limiter)
    opened = lambda value: bool(value[0]['pairs'][point] & (1 << component))
    low, high = bracket_transition(sample, opened)
    center = .5*(low[0]+high[0]); rows = []
    cases = [(max(0., center-gap), min(1., center+gap)) for gap in (1e-3, 1e-6, 1e-9)]
    cases.append((low[0], high[0]))
    for left_alpha, right_alpha in cases:
        inputs = [sample(alpha) for alpha in (left_alpha, right_alpha)]; forces = []; reports = []
        for alpha, (stage, faces) in zip((left_alpha, right_alpha), inputs):
            _, eb, trace = boundary(elapsed+alpha*dt, None)
            slope = pressure.geometric_bed_slope(endpoint['bed'], endpoint['cell_meters'], exterior_bed=eb)
            pairs = [(stage['pairs'] & 1) != 0, (stage['pairs'] & 2) != 0]
            _, neighbor = toggle_edge(pairs, stage['state'][..., 0], point, component)
            force, report = evaluate(stage, endpoint['bed'], endpoint['cell_meters'], trace, slope, pairs, [point, neighbor])
            forces.append(force); reports.append(dict(alpha=alpha, edge_open=opened((stage, faces)),
                hydrostatic_face_passes=faces, pressure=report))
        rows.append(dict(maximum_state_difference=float(abs(inputs[1][0]['state']-inputs[0][0]['state']).max()),
            maximum_hydro_difference=float(abs(inputs[1][0]['rate']-inputs[0][0]['rate']).max()),
            changed_graph_cells=int(np.count_nonzero(inputs[1][0]['pairs'] != inputs[0][0]['pairs'])),
            force_jump_at_owner=(forces[1][point]-forces[0][point]).tolist(), probes=reports))
    return dict(scope=wetting_limit.__doc__, alpha_bracket=[low[0], high[0]], cases=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('--interval', type=int, required=True); parser.add_argument('--trial', type=int, required=True)
    parser.add_argument('--yx', type=int, nargs=2, required=True)
    parser.add_argument('--component', type=int, choices=(0, 1), required=True)
    parser.add_argument('--limit-probe', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    data = args.trace.read_bytes(); meta = json.loads(data)
    if (not meta.get('completed') or not meta.get('final_state_exact_to_live') or
            (meta.get('source_evolution_failed') and not meta.get('retained_failure_exact'))):
        raise ValueError('Exact completed diagnostic capture required')
    source_bytes = Path(meta['source']).read_bytes(); source = json.loads(source_bytes)
    limiter = shoreline_model(meta, source); binary = Path(meta['binary']).read_bytes()
    matches = [r for r in read_records(meta, binary) if r[0]['interval'] == args.interval and r[0]['trial'] == args.trial]
    if len(matches) != 1: raise ValueError('Exactly one captured trial required')
    trial, stages, *_ = matches[0]
    a, b = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
        first=source['observations'][args.interval], second=source['observations'][args.interval+1]))
    _, boundary = temporal.boundary_provider(a, b)
    results = [stage_probe(gpu, a, boundary,
        trial['begin']-a['native_seconds']+(trial['attempted_dt'] if k else 0.), tuple(args.yx), args.component, limiter)
        for k, gpu in enumerate(stages)]
    report = dict(schema='raftsim.pressure_wetting_edge_probe.v1', scope=__doc__, shoreline_limiter=limiter,
        trial=trial, edge_yx=args.yx, component=args.component, stages=results,
        trace_sha256=hashlib.sha256(data).hexdigest(), binary_sha256=hashlib.sha256(binary).hexdigest(),
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        implementation_hashes={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_pressure_wetting_edge.py', 'audit_retained_failure_rates.py', 'audit_recorded_stages.py',
                'audit_recorded_evolution_steps.py', 'audit_live_temporal_evolution.py', 'total_depth_bank_replay.py',
                'total_depth_nonlinear_pressure.py', 'pressure_cg_range_reference.py', 'adaptive_hydrostatic_precision.py')})
    if args.limit_probe:
        report['wetting_limit'] = wetting_limit(stages, a, boundary, trial['begin']-a['native_seconds'],
            trial['attempted_dt'], tuple(args.yx), args.component, limiter)
    with args.report.open('x') as stream: json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps(dict(schema=report['schema'], trial=trial, report=str(args.report),
        stages=[dict(open=row['original_edge_open'], owner_acceleration=row['actual']['cells'][0]['acceleration'],
            counterfactual_acceleration=row['one_edge_toggled_counterfactual']['cells'][0]['acceleration']) for row in results],
        wetting_limit_summary=[{key: value for key, value in case.items() if key != 'probes'}
            for case in report.get('wetting_limit', {}).get('cases', [])]), indent=2))


if __name__ == '__main__': main()
