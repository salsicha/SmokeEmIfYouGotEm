"""Coupled nonlinear source-metric rate candidate on complete fixed wet support.

No topology transition, finite step, breaking, open or native acceptance. Uses
all source moments and weak original curvature; full continuum consistency must
be tested independently, not inferred from energy or local force identities.
"""
import numpy as np

from rational_primal_energy import K0
from subcell_auxiliary_transport import SourceAuxiliaryTransport, geometric_commutator, tensor_derivative_part
from subcell_source_curvature import SourceCurvatureTensor
from subcell_primal_metric_rate import metric_time_force, unscaled_operator_direction
from subcell_wet_pool_pressure import WetPoolPressureSystem, response as dual_response
from subcell_wet_pool_pressure_rate import WetPoolPressureRate
from subcell_wet_pool_primal_energy import evaluate
from subcell_wet_pool_transport import rates as base_rates
import subcell_metric_force_ledger as ledger


def stage(partition, physical_momentum=None, *, include_curvature=True):
    n = len(partition.pools)
    p = (np.array([pool['momentum'] for pool in partition.pools])[:, None, :]
         if physical_momentum is None else np.asarray(physical_momentum, float))
    if p.shape != (n, 1, 2) or not np.isfinite(p).all():
        raise ValueError('Finite original physical pool momentum required')
    if type(include_curvature) is not bool:
        raise ValueError('Explicit curvature comparison switch required')
    volume = np.array([pool['volume'] for pool in partition.pools])[:, None, None]
    root = np.sqrt(volume)
    u = p/volume
    base = base_rates(partition, p[:, 0], full_metric=False)
    if not base['complete_fixed_topology_base_rates']:
        raise ValueError('Complete original wet support required; source activation is unresolved')
    gravity = base_rates(partition, np.zeros((n, 2)), full_metric=False)
    vd = base['volume_rate'][:, None]
    primal = evaluate(partition, p)
    metric = metric_time_force(partition, u, vd)
    base_rhs = K0*(vd[:, :, None]*u-base['momentum_rate'][:, None, :])+(K0-1)*gravity['momentum_rate'][:, None, :]
    base_ledger = ledger.base(partition, base)*K0+ledger.base(partition, gravity)*(1-K0)
    metric_ledger, skew_ledger = ledger.zero(partition), ledger.zero(partition)
    skew = np.zeros_like(p)
    residuals = []
    curvature_scope = None
    for pole in primal['poles']:
        alpha, beta = pole['alpha'], pole['beta']
        s = WetPoolPressureSystem(partition, beta)
        t = WetPoolPressureRate(s, vd)
        transport = SourceAuxiliaryTransport(s, u)
        if transport.unresolved or transport.one_sided_owned_faces or transport.partially_shared_owned_faces:
            raise ValueError('One-sided or unequal wet support requires coupled front transport')
        curvature = SourceCurvatureTensor(s)
        curvature_scope = curvature.scope()
        if curvature.unresolved:
            raise ValueError('Original terrain-curvature front remains unresolved')
        z = pole['normalized_auxiliary_velocity']
        w = z/root
        ell = vd[:, :, None]/(2*volume)
        zt, info = s.solve(ell*root*u-beta*unscaled_operator_direction(t, z))
        wt = zt/root-ell*w
        metric_ledger = metric_ledger+ledger.metric_time(t, w, wt)*alpha
        residuals.extend((pole['relative_residual'], info['relative_residual']))

        def pullback(force):
            solution, solve = s.solve(force/root)
            residuals.append(solve['relative_residual'])
            return root*solution, solution/root

        def tensor(value):
            result = tensor_derivative_part(s, w, value)
            return result+curvature.action(w, value) if include_curvature else result

        difference = u-w
        middle = transport.factor_force(w)+geometric_commutator(t, w)
        difference_force = transport.difference_force(difference)/beta
        pulled, solution = pullback(middle+tensor(u))
        difference_pulled, difference_solution = pullback(difference_force)
        skew += alpha*(pulled-tensor(w)+difference_force-difference_pulled)
        # Direct geometric ledger, not a final-force remainder.
        tensor_ledger = ledger.tensor(s, curvature, w, difference)
        if not include_curvature:
            tensor_ledger.bed -= curvature.action(w, difference)[:, 0]
        skew_ledger = skew_ledger+(ledger.factor_transport(transport, w)+ledger.commutator(t, w)
            +tensor_ledger+ledger.gram(s, solution)*(-beta)+ledger.gram(s, difference_solution)*beta)*alpha

    rhs = base_rhs+.5*metric['auxiliary_force']+skew
    response = dual_response(partition, -rhs/root)
    ut = response['value']/root
    pt = volume*ut+vd[:, :, None]*u
    residuals.extend(pole['relative_residual'] for pole in response['poles'])
    acceleration = evaluate(partition, volume*ut)
    acceleration_ledger = ledger.zero(partition)
    for pole in acceleration['poles']:
        s = WetPoolPressureSystem(partition, pole['beta'])
        acceleration_ledger = acceleration_ledger+ledger.gram(s, pole['normalized_auxiliary_velocity']/root)*pole['alpha']
        residuals.append(pole['relative_residual'])
    physical_ledger = (base_ledger+acceleration_ledger*-1+metric_ledger*-.5+skew_ledger*-1)*(1/K0)
    energy_rate = float(primal['volume_gradient']@vd[:, 0]+np.sum(primal['canonical_velocity']*pt))
    errors = dict(local_momentum_ledger_error=float(np.max(abs(physical_ledger.action()-pt))),
                  metric_time_ledger_error=float(np.max(abs(metric_ledger.action()-metric['auxiliary_force']))),
                  skew_ledger_error=float(np.max(abs(skew_ledger.action()-skew))),
                  energy_rate=energy_rate, net_mass_rate=float(vd.sum()),
                  skew_energy_work=float(np.sum(u*skew)))
    if not np.isfinite(pt).all() or max(residuals) > 2e-5:
        raise ValueError('Original source pressure/finite range gate failed')
    if max(abs(value) for value in errors.values()) > 1e-10:
        raise ValueError(f'Coupled original-source local force/energy gate failed: {errors}')
    return dict(volume_rate=vd, physical_momentum_rate=pt, physical_acceleration=ut,
        physical_momentum_faces=physical_ledger.faces, bed_force=physical_ledger.bed,
        wall_force=physical_ledger.wall, curvature_scope=curvature_scope, include_curvature=include_curvature,
        maximum_solve_residual=max(residuals), **errors,
        full_continuum_or_topology_or_time_or_native_or_gameplay_accepted=False)
