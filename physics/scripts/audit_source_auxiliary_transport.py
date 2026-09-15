"""Original-moving-state source mode controls; no full force/rate acceptance."""
import numpy as np

from subcell_auxiliary_transport import SourceAuxiliaryTransport, geometric_commutator, tensor_derivative_part
from subcell_pressure_kinetic_geometry import quadrature
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_pressure_rate import WetPoolPressureRate
from subcell_wet_pool_primal_energy import evaluate


def integrated_kinematic_pair(tangent, left, right):
    """Independent original wet-triangle quadrature of v^T J u."""
    s = tangent.system
    dl, dr = s.divergence(left[:, 0]), s.divergence(right[:, 0])
    dtl, dtr = tangent.divergence_rate(left[:, 0]), tangent.divergence_rate(right[:, 0])
    result = 0.
    for i, pool in enumerate(s.partition.pools):
        weights, h, slope = quadrature(pool['storage'], pool['form']['stage_offset'])
        eta_t = tangent.volume_rate[i, 0]/pool['form']['wet_area']
        fl, fr = h*dl[i]-1.5*(slope@left[i, 0]), h*dr[i]-1.5*(slope@right[i, 0])
        ftl, ftr = eta_t*dl[i]+h*dtl[i], eta_t*dr[i]+h*dtr[i]
        result += .5*float(np.sum(weights*h*(fl*ftr-ftl*fr)))
    return result


def audit_components(partition):
    volume = np.array([p['volume'] for p in partition.pools])
    momentum = np.array([p['momentum'] for p in partition.pools])[:, None, :]
    root = np.sqrt(volume)[:, None, None]
    velocity = momentum/volume[:, None, None]
    pattern = .2*np.sin(.73*np.arange(len(volume))+.2)
    volume_rate = volume*(pattern-float(volume@pattern)/float(volume.sum()))
    response = evaluate(partition, momentum)
    records = []
    scope = None
    original_copy = momentum.copy()
    for pole in response['poles']:
        s = WetPoolPressureSystem(partition, pole['beta'])
        tangent = WetPoolPressureRate(s, volume_rate[:, None])
        transport = SourceAuxiliaryTransport(s, velocity)
        scope = transport.scope()
        w = pole['normalized_auxiliary_velocity']/root
        r = velocity-w
        jw = geometric_commutator(tangent, w)
        j_pair = float(np.sum(r*jw))
        direct_pair = integrated_kinematic_pair(tangent, r, w)
        factor_force = transport.factor_force(w)
        difference_force = transport.difference_force(r)/pole['beta']
        nu = tensor_derivative_part(s, w, velocity)
        nw = tensor_derivative_part(s, w, w)
        solved, solve = s.solve((factor_force+jw+nu)/root)
        difference_solved, difference_solve = s.solve(difference_force/root)
        # Component only, including the derivative part of T^T N-N T.
        # Its missing original-terrain curvature part is NOT called zero in a
        # complete equation. Front work and a full mass/force stage are absent.
        component = pole['alpha']*(root*solved-nw+difference_force-root*difference_solved)
        work = float(np.sum(velocity*component))
        pair_error = abs(j_pair-direct_pair)
        tensor_pair_error = abs(float(np.sum(w*nu)-np.sum(velocity*nw)))
        residual = max(pole['relative_residual'], solve['relative_residual'], difference_solve['relative_residual'])
        records.append(dict(beta=pole['beta'], alpha=pole['alpha'],
            factor_energy_work=float(np.sum(w*factor_force)),
            difference_energy_work=float(np.sum(r*difference_force)),
            commutator_energy_work=float(np.sum(w*jw)),
            commutator_quadrature_pair_error=pair_error,
            tensor_derivative_pair_error=tensor_pair_error,
            pulled_component_energy_work=work,
            maximum_component_force=float(np.max(abs(component))), maximum_solve_residual=residual,
            controls_passed=bool(max(abs(work), abs(float(np.sum(w*factor_force))),
                                    abs(float(np.sum(r*difference_force))), abs(float(np.sum(w*jw))),
                                    pair_error, tensor_pair_error) < 1e-10 and residual < 2e-5)))
    if not np.array_equal(np.array([p['momentum'] for p in partition.pools])[:, None, :], original_copy):
        raise RuntimeError('Original physical source momentum changed during component audit')
    return dict(pools=len(volume), scope=scope, poles=records,
                volume_direction='prescribed zero-sum coefficient direction, NOT evolved mass flux',
                volume_direction_sum=float(volume_rate.sum()),
                source_auxiliary_component_controls_passed=all(r['controls_passed'] for r in records),
                full_tensor_or_front_or_nonlinear_or_time_or_native_or_gameplay_accepted=False)
