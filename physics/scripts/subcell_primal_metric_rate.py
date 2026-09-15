"""Changing-volume inverse metric on exact wet pools, research coefficient.

This differentiates the original physical/canonical map, not a chosen mass
flux or nonlinear force. Both pressure factors, their geometry directions,
both volume normalizations and the original 40-CG gates are retained.
"""
import numpy as np

from rational_primal_energy import K0
from subcell_wet_pool_primal_energy import evaluate
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_pressure_rate import WetPoolPressureRate


def unscaled_operator_direction(tangent, normalized):
    """Q_dot*z directly, without first multiplying by the pole length.

    Recovering it as A_dot*z / beta needlessly loses range/precision before
    the inverse-factor weights use it. Geometry and both roots are unchanged.
    """
    system = tangent.system
    u = system._vector(normalized)[:, 0]/system.root[:, None]
    ud = -tangent.ell[:, None]*u
    jet = np.column_stack((system.divergence(u), u))
    jet_rate = np.column_stack((tangent.divergence_rate(u)+system.divergence(ud), ud))
    gram = np.array([pool['form']['gram'] for pool in system.partition.pools])
    stress = np.einsum('nij,nj->ni', gram, jet)
    stress_rate = np.einsum('nij,nj->ni', tangent.gram_rate, jet)+np.einsum('nij,nj->ni', gram, jet_rate)
    value = system.divergence_transpose(stress[:, 0])+stress[:, 1:]
    rate = tangent.transpose_rate(stress[:, 0])+system.divergence_transpose(stress_rate[:, 0])+stress_rate[:, 1:]
    return ((rate-tangent.ell[:, None]*value)/system.root[:, None])[:, None, :]


def direction(partition, physical_momentum, volume_rate, physical_momentum_rate, gravity=9.81):
    response = evaluate(partition, physical_momentum, gravity)
    volume = np.array([p['volume'] for p in partition.pools])[:, None, None]
    p = np.asarray(physical_momentum, float)
    pd = np.asarray(physical_momentum_rate, float)
    vd = np.asarray(volume_rate, float)
    if pd.shape != p.shape or vd.shape != (len(volume), 1) or not all(np.isfinite(x).all() for x in (pd, vd)):
        raise ValueError('Matching finite physical momentum and volume directions required')
    root = np.sqrt(volume)
    ell = vd[:, :, None]/(2*volume)
    q = p/root
    qd = pd/root-ell*q
    mapped_rate = K0*qd
    divergence_rate = np.zeros_like(p)
    divergence_geometry_rate = np.zeros_like(p)
    bed_metric_rate = np.zeros_like(p)
    poles = []
    for pole in response['poles']:
        system = WetPoolPressureSystem(partition, pole['beta'])
        tangent = WetPoolPressureRate(system, vd)
        z = pole['normalized_auxiliary_velocity']
        qtz = unscaled_operator_direction(tangent, z)
        zd, stats = system.solve(qd-pole['beta']*qtz)
        if max(stats['relative_residual'], pole['relative_residual']) > 2e-5:
            raise ValueError('Original inverse-metric 40-CG direction residual gate failed')
        # Direct Q actions retain near-constant modes; never subtract z from
        # the solved RHS and divide the cancelled difference by beta.
        qzd = system.factor_transpose(system.factor_action(zd))
        mapped_rate += pole['alpha']*(qtz+qzd)
        auxiliary = z[:, 0]/root[:, 0]
        auxiliary_rate = zd[:, 0]/root[:, 0]-ell[:, 0]*auxiliary
        jet = np.column_stack((system.divergence(auxiliary), auxiliary))
        jet_rate = np.column_stack((tangent.divergence_rate(auxiliary)
                                   +system.divergence(auxiliary_rate), auxiliary_rate))
        gram = np.array([pool['form']['gram'] for pool in partition.pools])
        stress = np.einsum('nij,nj->ni', gram, jet)
        stress_rate = np.einsum('nij,nj->ni', tangent.gram_rate, jet)+np.einsum('nij,nj->ni', gram, jet_rate)
        divergence_rate[:, 0] += pole['alpha']*system.divergence_transpose(stress_rate[:, 0])
        divergence_geometry_rate[:, 0] += pole['alpha']*tangent.transpose_rate(stress[:, 0])
        bed_metric_rate[:, 0] += pole['alpha']*stress_rate[:, 1:]
        poles.append(dict(beta=pole['beta'], alpha=pole['alpha'], solve_residual=pole['relative_residual'],
                          direction_solve=stats))
    canonical = response['canonical_velocity']
    canonical_rate = mapped_rate/root-ell*canonical
    canonical_momentum_rate = vd[:, :, None]*canonical+volume*canonical_rate
    local_terms = dict(base_momentum=K0*pd, divergence_stress=divergence_rate,
                       changing_divergence=divergence_geometry_rate, terrain_metric=bed_metric_rate)
    local_error = float(np.max(abs(sum(local_terms.values())-canonical_momentum_rate)))
    kinetic_rate = .5*float(np.sum(pd*canonical+p*canonical_rate))
    potential_rate = float(response['volume_gradient_terms']['potential']@vd[:, 0])
    gradient_work = float(response['volume_gradient']@vd[:, 0]+np.sum(canonical*pd))
    coordinate_error = abs(kinetic_rate+potential_rate-gradient_work)
    if not np.isfinite(canonical_rate).all() or not np.isfinite(canonical_momentum_rate).all():
        raise ValueError('Inverse-metric direction exceeds represented range')
    if coordinate_error > 1e-10:
        raise ValueError('Inverse-metric physical energy chain rule failed')
    if local_error > 1e-10:
        raise ValueError('Changing-volume canonical metric local ledger failed')
    return dict(canonical_velocity=canonical, canonical_velocity_rate=canonical_rate,
        canonical_momentum_rate=canonical_momentum_rate, kinetic_energy_rate=kinetic_rate,
        potential_energy_rate=potential_rate, total_energy_rate=kinetic_rate+potential_rate,
        physical_gradient_work=gradient_work, energy_coordinate_error=coordinate_error, poles=poles,
        canonical_metric_local_terms=local_terms, canonical_metric_local_error=local_error,
        nonlinear_advection_or_bed_force_or_topology_or_native_or_gameplay_accepted=False)


def metric_time_force(partition, physical_velocity, volume_rate):
    """M_dot*u at FIXED physical u, M=R*K*R, including terrain reactions.

    The nonlinear transport equation needs this term as well as auxiliary
    advection and terrain work. Applying it alone is NOT the full dynamics.
    """
    volume = np.array([p['volume'] for p in partition.pools])[:, None, None]
    u, vd = np.asarray(physical_velocity, float), np.asarray(volume_rate, float)
    if u.shape != (len(volume), 1, 2) or vd.shape != (len(volume), 1):
        raise ValueError('Pool-shaped physical velocity and volume direction required')
    result = direction(partition, volume*u, vd, vd[:, :, None]*u)
    force = result['canonical_momentum_rate']
    work = .5*float(np.sum(u*force))
    return dict(force=force, auxiliary_force=force-K0*vd[:, :, None]*u,
                metric_energy_work=work, direction=result,
                nonlinear_advection_or_full_force_or_gameplay_accepted=False)
