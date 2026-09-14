"""Inspect pressure geometry and optional directional solves on a recorded edge.

Uses the existing source-exact bracket, original unscaled MC reconstruction and
one unchanged pressure field from the OLD left-side solve. This is a static
sensitivity probe, not an evolved history. The baseline frozen action uses
homogeneous algebraic rows; prescribed velocity/time-rate traces are checked
separately through their affine boundary work. Optional manufactured linear
and full-state directional nonlinear solves are explicitly scoped subreports,
not base dry-transition closure, transparent boundaries or playable acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_pressure_cut_face import digest
from audit_pressure_wetting_edge import capture_hydro
from audit_recorded_stages import read_records
from audit_recorded_evolution_steps import shoreline_model
from audit_retained_failure_rates import velocity
import audit_live_temporal_evolution as temporal
import total_depth_nonlinear_pressure as pressure
from reconstructed_pressure_geometry import ReconstructedPressureGeometry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('probe', type=Path)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--pressure-trace', choices=('mean_column', 'integrated_column'), default='mean_column')
    parser.add_argument('--bed-quadrature', choices=('polynomial', 'shared_bottom'), default='polynomial')
    parser.add_argument('--mass-tangent', action='store_true', help='Inspect actual FV geometry rates and Q/C; not a new pressure solve')
    parser.add_argument('--dry-limit-probe', action='store_true', help='Diagnose unsupported exactly-dry activations without dropping their mass rates')
    parser.add_argument('--acceleration-form', action='store_true', help='Manufactured linear solves on this geometry, NOT the physical nonlinear RHS')
    parser.add_argument('--directional-pressure-limit', action='store_true', help='Read-only nonlinear solves along the original full FV direction; no evolved history')
    parser.add_argument('--analytic-wetting', action='store_true', help='Compare analytic zero-depth directional force with the represented-ray probes')
    args = parser.parse_args()
    if args.mass_tangent and (args.pressure_trace != 'integrated_column' or args.bed_quadrature != 'shared_bottom'):
        raise ValueError('Mass tangent requires integrated/shared-bottom research geometry')
    if args.dry_limit_probe and not args.mass_tangent:
        raise ValueError('Dry-limit diagnosis requires the actual-mass tangent check')
    if args.analytic_wetting and not args.directional_pressure_limit:
        raise ValueError('Analytic comparison requires the directional pressure audit')
    if args.report.exists():
        raise FileExistsError(args.report)
    probe_data = args.probe.read_bytes(); probe = json.loads(probe_data)
    trace_data = args.trace.read_bytes(); trace = json.loads(trace_data)
    if (probe.get('schema') != 'raftsim.pressure_wetting_edge_probe.v1' or not trace.get('completed')
            or not trace.get('final_state_exact_to_live') or not trace.get('retained_failure_exact')):
        raise ValueError('Source-exact failed-history wetting probe required')
    source_data = Path(trace['source']).read_bytes(); source = json.loads(source_data)
    binary = Path(trace['binary']).read_bytes()
    hashes = dict(trace_sha256=hashlib.sha256(trace_data).hexdigest(),
        source_sha256=hashlib.sha256(source_data).hexdigest(), binary_sha256=hashlib.sha256(binary).hexdigest())
    if any(probe[k] != v for k, v in hashes.items()) or shoreline_model(trace, source) != 'unscaled':
        raise ValueError('Source provenance/model does not match the wetting probe')
    wanted = probe['trial']
    matches = [r for r in read_records(trace, binary) if
               (r[0]['interval'], r[0]['trial']) == (wanted['interval'], wanted['trial'])]
    if len(matches) != 1 or matches[0][0] != wanted:
        raise ValueError('Exact original captured trial required')
    trial, stages, *_ = matches[0]
    first, second = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
        first=source['observations'][trial['interval']], second=source['observations'][trial['interval']+1]))
    _, boundary = temporal.boundary_provider(first, second)
    point = tuple(probe['edge_yx']); component = probe['component']
    alpha = probe['wetting_limit']['alpha_bracket']
    start, end = [stage['state'].astype(float) for stage in stages]
    states = [start+a*(end-start) for a in alpha]
    elapsed = trial['begin']-first['native_seconds']+alpha[0]*trial['attempted_dt']
    old, _ = capture_hydro(states[0], first, boundary, elapsed, point, component, 'unscaled')
    _, exterior_bed, trace_boundary = boundary(elapsed, None)
    bed, dx = first['bed'], first['cell_meters']
    slope = pressure.geometric_bed_slope(bed, dx, exterior_bed=exterior_bed)
    pairs = [(old['pairs'] & 1) != 0, (old['pairs'] & 2) != 0]
    u = velocity(states[0]); poles = []
    pressure.nonlinear_pressure_force(states[0][..., 0], bed, u, np.zeros_like(u), pairs, dx,
        interpolation='depth_weighted', formulation='kinematic', mass_rate=old['rate'][..., 0],
        momentum_rate=old['rate'][..., 1:3], bed_slope=slope, dispersion_fraction=old['fraction'],
        boundary_velocity=trace_boundary, on_pressure=lambda values: poles.extend(values))
    p = sum(pole['weight']*pole['pressure'] for pole in poles)
    b = sum(pole['weight']*pole['bottom_pressure'] for pole in poles)
    originals = [value.copy() for value in (*states, bed, u, p, b)]
    for value in (*states, bed, u, p, b):
        value.flags.writeable = False
    geometries = [ReconstructedPressureGeometry(s[..., 0], bed, dx, pressure_trace=args.pressure_trace,
        bed_quadrature=args.bed_quadrature, exterior_bed=boundary(
            trial['begin']-first['native_seconds']+a*trial['attempted_dt'], None)[1])
        for a, s in zip(alpha, states)]
    actions = [g.gradient_traction(p, b) for g in geometries]
    kinematics = [g.kinematic_components(u) for g in geometries]
    rows = []
    tangent_fields = []
    for a, g, action, (d, e) in zip(alpha, geometries, actions, kinematics):
        edge = g.edges[component]; poly = g.polynomials[component]
        lhs = float(np.sum(u*action)); rhs = float(-np.sum(p*d)+np.sum(b*e))
        rows.append(dict(alpha=a, owner_gradient_traction=action[point].tolist(),
            owner_kinematics=[float(d[point]), float(e[point])],
            pressure_transfer_coefficients={name: float(edge[name][point]) for name in edge},
            original_polynomial={name: float(poly[name][point]) for name in ('ha', 'hb', 'fa', 'fb', 'dh', 'deta')},
            signed_adjoint_absolute_error=abs(lhs-rhs),
            signed_adjoint_relative_error=abs(lhs-rhs)/max(abs(lhs), abs(rhs)) if lhs or rhs else 0.))
        probe_elapsed = trial['begin']-first['native_seconds']+a*trial['attempted_dt']
        probe_trace = boundary(probe_elapsed, None)[2]
        lift = g.prescribed_divergence_lift(probe_trace)
        affine_work = float(np.sum(u*action)+np.sum(p*(d+lift[..., 0]))-np.sum(b*e))
        expected_work = float(np.sum(p*lift[..., 0]))
        rows[-1]['prescribed_boundary'] = dict(maximum_velocity_lift=float(abs(lift[..., 0]).max()),
            maximum_time_rate_lift=float(abs(lift[..., 1]).max()), affine_work=affine_work,
            expected_boundary_work=expected_work, boundary_work_error=abs(affine_work-expected_work),
            scope='Original packed velocity/time-rate trace; same homogeneous pressure adjoint, not transparent-wave qualification')
        if args.directional_pressure_limit and len(rows) == 1:
            from audit_directional_pressure_limit import directional_pressure_limit
            # The captured fourth channel is separate from the three hydraulic
            # conserved variables returned by capture_hydro. Preserve it in the
            # immutable original capture; do not fabricate a fourth FV rate.
            limit_state = states[0][..., :3]
            limit_cpu, _ = capture_hydro(limit_state, first, boundary, elapsed, point, component, 'unscaled')
            rows[-1]['directional_pressure_limit'] = directional_pressure_limit(g, limit_state, limit_cpu['rate'],
                limit_cpu['fraction'], trace_boundary, exterior_bed=exterior_bed, analytic=args.analytic_wetting)
        if args.acceleration_form:
            from audit_reconstructed_acceleration import inspect_system
            state = states[len(rows)-1]
            system_cpu, _ = capture_hydro(state, first, boundary,
                trial['begin']-first['native_seconds']+a*trial['attempted_dt'], point, component, 'unscaled')
            rows[-1]['acceleration_system'] = inspect_system(g, system_cpu['fraction'], velocity(state))
        if args.mass_tangent:
            from reconstructed_pressure_rates import PressureGeometryRate, DryGeometryTransition, kinematic_forcing
            state = states[len(rows)-1]
            cpu, _ = capture_hydro(state, first, boundary,
                trial['begin']-first['native_seconds']+a*trial['attempted_dt'], point, component, 'unscaled')
            own_velocity = velocity(state)
            try:
                tangent = PressureGeometryRate(g, bed, cpu['rate'][..., 0])
            except DryGeometryTransition as error:
                active = np.argwhere((g.h == 0) & (cpu['rate'][..., 0] > 0))
                rows[-1]['mass_tangent'] = dict(status='unsupported_dry_transition', reason=str(error),
                    exactly_dry_cells=int(np.sum(g.h == 0)), activating_dry_cells=len(active),
                    activations=[dict(yx=position.tolist(), actual_cpu_mass_rate=float(cpu['rate'][tuple(position)][0]),
                        recorded_stage_mass_rates=[float(stage['rate'][tuple(position)][0]) for stage in stages])
                        for position in active])
                if args.dry_limit_probe and len(rows) == 1:
                    from audit_dry_pressure_geometry import dry_mass_limit
                    rows[-1]['dry_limit'] = dry_mass_limit(g, cpu['rate'][..., 0], own_velocity, p, b,
                        exterior_bed=boundary(trial['begin']-first['native_seconds']+a*trial['attempted_dt'], None)[1])
                tangent_fields.append(None)
                continue
            q, c, adv = kinematic_forcing(g, tangent, own_velocity)
            dt, et = tangent.kinematic_rate(own_velocity)
            tangent_fields.append((q, c, dt, et))
            rows[-1]['mass_tangent'] = dict(
                status='computed_on_stationary_dry_set',
                scope='Actual independently recomputed FV mass rate at this probe, before pressure. Geometry derivatives hold velocity fixed; Q/C use this probe velocity.',
                exactly_dry_cells=int(np.sum(g.h == 0)),
                activating_dry_cells=int(np.sum((g.h == 0) & (cpu['rate'][..., 0] > 0))),
                exact_polynomial_value_discrepancy_upper_bounds=tangent.maximum_value_discrepancy,
                maximum_coefficient_rates={name: max(float(abs(edge[name]).max()) for edge in tangent.edges)
                    for name in ('aa', 'ab', 'ca', 'cb', 'own', 'other', 'shared_b')},
                owner_Q=float(q[point]), owner_C=float(c[point]), owner_advective=adv[point].tolist(),
                owner_D_t_u=float(dt[point]), owner_E_t_u=float(et[point]))
    if any(not np.array_equal(before, after) for before, after in zip(originals, (*states, bed, u, p, b))):
        raise RuntimeError('Static pressure geometry modified a source input')
    result = dict(schema='raftsim.recorded_pressure_geometry_probe.v1', scope=__doc__, **hashes,
        pressure_trace=args.pressure_trace, bed_quadrature=args.bed_quadrature,
        input_probe_sha256=hashlib.sha256(probe_data).hexdigest(), trial=trial,
        edge_yx=list(point), component=component, probes=rows,
        maximum_state_difference=float(abs(states[1]-states[0]).max()),
        frozen_pressure_geometry_action_change_at_owner=(actions[1][point]-actions[0][point]).tolist(),
        maximum_frozen_pressure_geometry_action_change=float(abs(actions[1]-actions[0]).max()),
        maximum_frozen_velocity_kinematics_changes=[float(abs(kinematics[1][j]-kinematics[0][j]).max()) for j in (0, 1)],
        qualification='Baseline frozen action and boundary-work check, with any optional solves scoped in their own subreports. No base dry-transition closure, evolved history or promotion.',
        implementation_hashes={name: digest(Path(__file__).with_name(name)) for name in
            ('audit_recorded_pressure_geometry.py', 'reconstructed_pressure_geometry.py',
                'pressure_cut_face_reference.py', 'total_depth_bank_replay.py', 'adaptive_hydrostatic_precision.py',
                'total_depth_nonlinear_pressure.py')})
    if args.mass_tangent:
        result['implementation_hashes']['reconstructed_pressure_rates.py'] = digest(Path(__file__).with_name('reconstructed_pressure_rates.py'))
        result['mass_tangent_computed_for_all_probes'] = all(v is not None for v in tangent_fields)
        if result['mass_tangent_computed_for_all_probes']:
            result['mass_tangent_changes'] = {name: dict(maximum=float(abs(right-left).max()),
                owner=float(right[point]-left[point])) for name, left, right in zip(
                    ('Q', 'C', 'D_t_u', 'E_t_u'), tangent_fields[0], tangent_fields[1])}
    if args.dry_limit_probe:
        result['implementation_hashes']['audit_dry_pressure_geometry.py'] = digest(Path(__file__).with_name('audit_dry_pressure_geometry.py'))
    if args.acceleration_form:
        for name in ('reconstructed_acceleration_system.py', 'audit_reconstructed_acceleration.py', 'pressure_cg_range_reference.py'):
            result['implementation_hashes'][name] = digest(Path(__file__).with_name(name))
    if args.directional_pressure_limit:
        for name in ('audit_directional_pressure_limit.py', 'reconstructed_nonlinear_pressure.py',
                     'reconstructed_pressure_rates.py', 'reconstructed_acceleration_system.py', 'pressure_cg_range_reference.py'):
            result['implementation_hashes'][name] = digest(Path(__file__).with_name(name))
    if args.analytic_wetting:
        result['implementation_hashes']['directional_pressure_geometry.py'] = digest(Path(__file__).with_name('directional_pressure_geometry.py'))
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))
    if args.mass_tangent and not result['mass_tangent_computed_for_all_probes']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
