"""Coupled point-birth limit of original metric/geometry-time force terms.

This is the leading half-M_e*u plus sum alpha*T.T*J_e*w contribution to
the existing nonlinear stage. Auxiliary advection, terrain-curvature/front
work and complete dynamics are NOT supplied or enabled by this coefficient.
"""
import numpy as np

from pressure_cg_range_reference import solve as range_cg
from subcell_point_birth_metric_force import point_metric_force
from subcell_simultaneous_birth_pressure import BirthLimitSystem
from subcell_wet_pool_pressure import WetPoolPressureSystem


def point_connection(context, requests):
    metric = point_metric_force(context, requests)
    limit = metric['limit']
    part = context.partition
    roots = np.sqrt(limit['volume_path_coefficients'])
    scales = limit['stage_scales']
    columns = limit['old_divergence_column_sqrt_path_coefficient']
    # Physical D_new,new = N/e, recovered with both original volume roots.
    nmap = (limit['newborn_jet_maps'][:, 0]*np.repeat(roots, 2)[None, :]
            /(roots*scales)[:, None])
    # Original cross Gram coefficient Gamma_D,u = e^4*c.
    cross = (limit['volume_path_coefficients']*scales)[:, None]*limit['newborn_scaled_grams'][:, 0, 1:]
    old_total = .5*metric['old_force_limit']
    new_total = .5*metric['newborn_force_over_path_limit']
    records = []
    for pole, (_, stress) in zip(limit['poles'], context.poles):
        beta, alpha = pole['beta'], pole['alpha']
        system = WetPoolPressureSystem(part, beta)
        birth_system = BirthLimitSystem(limit['newborn_jet_maps'], limit['newborn_scaled_factors'],
                                        limit['volume_path_coefficients'], beta)
        x = pole['coupled_response']
        newborn_auxiliary = -beta*x/roots[:, None]  # lim e*w_new
        coupling = (columns.T@stress).reshape(-1, 2)

        def old_cross_action(value):
            divergence = columns@value.ravel()
            return system.factor_transpose([p['form']['factor'][:, 0]*d
                                            for p, d in zip(part.pools, divergence)])

        # Direct original J=.5(F.T*H*F_e-F_e.T*H*F), including the
        # changing depth factor. New-source skew cross work survives at O(e).
        old_j = -beta*system.root[:, None]*old_cross_action(x)[:, 0]
        d = nmap@newborn_auxiliary.ravel()
        contraction = np.sum(cross*newborn_auxiliary, axis=1)
        new_j = -roots[:, None]*coupling+.5*(cross*d[:, None]
                    -(nmap.T@contraction).reshape(-1, 2))
        old_w = next(p['normalized_auxiliary_velocity'] for p in context.primal['poles']
                     if p['beta'] == beta)[:, 0]/system.root[:, None]
        skew_work = float(np.sum(old_w*old_j)+np.sum(newborn_auxiliary*new_j))
        if not all(np.isfinite(v).all() for v in (old_j, new_j)) or not np.isfinite(skew_work):
            raise ValueError('Point geometry-time connection exceeds represented range')
        if abs(skew_work) > 1e-10:
            raise ValueError('Original point geometry-time skew work gate failed')
        # Original T.T=R*(I+beta Q)^-1/R. Its new RHS is O(e^-1/2),
        # so the old/new coupling contributes at order one to the old force.
        y, new_stats = range_cg(birth_system, (new_j/roots[:, None])[:, None], 40, preconditioner='block')
        y = y[:, 0]
        pulled, old_stats = system.solve(old_j[:, None]/system.root[:, None, None]
                                         -beta*old_cross_action(y))
        if max(new_stats['relative_residual'], old_stats['relative_residual']) > 2e-5:
            raise ValueError('Original 40-CG point connection pullback residual gate failed')
        old_pulled = system.root[:, None]*pulled[:, 0]
        new_pulled = roots[:, None]*y
        if not all(np.isfinite(v).all() for v in (old_pulled, new_pulled)):
            raise ValueError('Point connection pullback exceeds represented range')
        old_total += alpha*old_pulled
        new_total += alpha*new_pulled
        records.append(dict(alpha=alpha, beta=beta, old_commutator_limit=old_j,
            newborn_commutator_over_path_limit=new_j, old_pulled_commutator_limit=old_pulled,
            newborn_pulled_commutator_over_path_limit=new_pulled, skew_work_limit=skew_work,
            old_pullback_solve=old_stats, newborn_pullback_solve=new_stats))
    if not all(np.isfinite(v).all() for v in (old_total, new_total)):
        raise ValueError('Combined point geometry-time force exceeds represented range')
    return dict(metric=metric, old_connection_limit=old_total,
                newborn_connection_over_path_limit=new_total, poles=records,
                complete_front_transport_or_force_or_time_or_native_or_gameplay_accepted=False)
