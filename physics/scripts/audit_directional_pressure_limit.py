"""Read-only nonlinear pressure limit along a captured FV state direction.

Probe state+epsilon*FV_rate with BOTH mass and momentum, never depth alone.
Hold that original tangent, supplied boundary traces and dispersion fractions
fixed while epsilon tends to zero. These are local directional probes, NOT
accepted evolution steps or recomputed-FV history. Exactly dry activations are
not discarded. The default solver rejects these base dry transitions; an
explicit analytic comparison can evaluate the research directional extension.
"""
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_nonlinear_pressure import nonlinear_pressure
from audit_retained_failure_rates import velocity


def directional_pressure_limit(geometry, state, rate, fraction, boundary_velocity, *, exterior_bed=None,
                               analytic=False):
    state, rate = np.asarray(state, dtype=float), np.asarray(rate, dtype=float)
    if (state.shape != (*geometry.h.shape, 3) or rate.shape != state.shape
            or not np.isfinite(state).all() or not np.isfinite(rate).all()
            or not np.array_equal(state[..., 0], geometry.h)):
        raise ValueError('Original geometry, state and full FV tangent must match')
    activations = np.argwhere((geometry.h == 0) & (rate[..., 0] > 0))
    if not len(activations): raise ValueError('Actual dry activations required for the directional probe')
    if np.any((geometry.h == 0) & (rate[..., 0] < 0)): raise ValueError('Negative dry mass rate; no repair')
    analytic_force = analytic_result = None
    if analytic:
        analytic_force, analytic_result = nonlinear_pressure(geometry, velocity(state), rate[..., 0], rate[..., 1:3],
            dispersion_fraction=fraction, boundary_velocity=boundary_velocity, preconditioner='block',
            dry_treatment='directional_limit')
    rows, forces = [], []
    for epsilon in (1e-8, 1e-16, 1e-24):
        later = state+epsilon*rate
        if (not np.isfinite(later).all() or np.any(later[..., 0] < 0)
                or np.any(later[..., 0][tuple(activations.T)] <= 0)):
            raise ValueError('Probe leaves physical/storage range; no repair')
        g = ReconstructedPressureGeometry(later[..., 0], geometry.bed, geometry.dx,
            periodic=geometry.periodic, pressure_trace=geometry.pressure_trace,
            bed_quadrature=geometry.bed_quadrature, exterior_bed=exterior_bed)
        u = velocity(later)
        force, result = nonlinear_pressure(g, u, rate[..., 0], rate[..., 1:3],
            dispersion_fraction=fraction, boundary_velocity=boundary_velocity, preconditioner='block')
        stats = [dict(length=p['length'], weight=p['weight'], iterations=p['iterations'],
            relative_residual=p['relative_residual'], physical_relative_residual=p.get('physical_relative_residual', 0.))
            for p in result['poles']]
        worst = tuple(np.unravel_index(abs(force).argmax(), force.shape))
        rows.append(dict(parameter_seconds=epsilon, maximum_state_change=float(abs(later-state).max()),
            activations=[dict(yx=p.tolist(), depth=float(later[tuple(p)][0]), velocity=u[tuple(p)].tolist(),
                              pressure_force=force[tuple(p)].tolist()) for p in activations],
            maximum_pressure_force=float(abs(force).max()), worst_force_yxc=list(map(int, worst)),
            maximum_Q=float(abs(result['quadratic']).max()), maximum_C=float(abs(result['curvature']).max()),
            poles=stats))
        forces.append(force)
    comparisons = []
    for i in range(1, len(forces)):
        delta = forces[i]-forces[i-1]
        worst = tuple(np.unravel_index(abs(delta).argmax(), delta.shape))
        comparisons.append(dict(left_parameter=rows[i-1]['parameter_seconds'], right_parameter=rows[i]['parameter_seconds'],
            maximum_pressure_force_change=float(abs(delta).max()), worst_change_yxc=list(map(int, worst)),
            change_at_worst=float(delta[worst])))
    result = dict(scope=__doc__, probes=rows, successive_changes=comparisons,
        qualification='Nonlinear directional probes only; no base dry-transition closure, trajectory, gate relaxation or native/playable acceptance.')
    if analytic:
        worst = tuple(np.unravel_index(abs(analytic_force).argmax(), analytic_force.shape))
        result['analytic_limit'] = dict(scope='Analytic directional research force on original exact-zero depths; not epsilon initialization or an evolved history.',
            maximum_pressure_force=float(abs(analytic_force).max()), worst_force_yxc=list(map(int, worst)),
            dry_pressure_force_maximum=float(abs(analytic_force[geometry.h == 0]).max()),
            activating_dry_cells=analytic_result['activating_dry_cells'],
            source_depth_unchanged=bool(np.array_equal(geometry.h, state[..., 0])),
            exact_geometry_limit_discrepancy=analytic_result['geometry_value_discrepancy_bounds'],
            poles=[dict(length=p['length'], weight=p['weight'], iterations=p['iterations'],
                relative_residual=p['relative_residual'],
                physical_relative_residual=p.get('physical_relative_residual', 0.))
                for p in analytic_result['poles']],
            comparisons=[])
        for row, force in zip(rows, forces):
            delta = force-analytic_force
            at = tuple(np.unravel_index(abs(delta).argmax(), delta.shape))
            result['analytic_limit']['comparisons'].append(dict(parameter_seconds=row['parameter_seconds'],
                maximum_pressure_force_difference=float(abs(delta).max()), worst_yxc=list(map(int, at)),
                difference_at_worst=float(delta[at])))
        result['qualification'] = 'Analytic directional force compared to represented-ray probes only; no original-history, native, physical accuracy or playable acceptance.'
    return result
