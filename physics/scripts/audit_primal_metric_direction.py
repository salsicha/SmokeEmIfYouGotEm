"""Original moving-state metric derivative controls, NOT inferred river rates."""
import numpy as np

from subcell_primal_metric_rate import direction, metric_time_force
from subcell_wet_pool_primal_energy import evaluate
from subcell_wet_pool_pressure_rate import dual_direction


def audit_direction(pools):
    volume = np.array([p['volume'] for p in pools.pools])
    p = np.array([pool['momentum'] for pool in pools.pools])[:, None, :]
    u = p/volume[:, None, None]
    index = np.arange(len(volume))
    pattern = .2*np.sin(.73*index+.2)
    vd = volume*(pattern-float(np.sum(volume*pattern)/np.sum(volume)))
    ud = .1*np.stack((np.cos(.31*index), np.sin(.47*index)), axis=-1)[:, None, :]
    pd = vd[:, None, None]*u+volume[:, None, None]*ud
    analytic = direction(pools, p, vd[:, None], pd)
    metric = metric_time_force(pools, u, vd[:, None])
    inverse = dual_direction(pools, analytic['canonical_velocity'], vd[:, None], analytic['canonical_velocity_rate'])
    inverse_error = float(np.max(abs(inverse['physical_momentum_rate']-pd)/volume[:, None, None]))
    step = 1e-4
    for _ in range(24):
        try:
            pools.volume_probe(volume-step*vd)
            pools.volume_probe(volume+step*vd)
            break
        except ValueError as exc:
            if 'topology event' not in str(exc):
                raise
            step *= .5
    else:
        raise ValueError('No represented fixed-topology derivative verification interval')
    records = []
    for epsilon in (step, step/2, step/4):
        low_v, high_v = volume-epsilon*vd, volume+epsilon*vd
        low_pool, high_pool = pools.volume_probe(low_v), pools.volume_probe(high_v)
        low, high = evaluate(low_pool, p-epsilon*pd), evaluate(high_pool, p+epsilon*pd)
        canonical_fd = (high['canonical_velocity']-low['canonical_velocity'])/(2*epsilon)
        energy_fd = (high['total']-low['total'])/(2*epsilon)
        low_u, high_u = evaluate(low_pool, low_v[:, None, None]*u), evaluate(high_pool, high_v[:, None, None]*u)
        metric_fd = (high_v[:, None, None]*high_u['canonical_velocity']
                     -low_v[:, None, None]*low_u['canonical_velocity'])/(2*epsilon)
        records.append(dict(verification_step=epsilon,
            canonical_velocity_rate_error=float(np.max(abs(canonical_fd-analytic['canonical_velocity_rate']))),
            relative_energy_rate_error=abs(float(energy_fd-analytic['total_energy_rate']))/max(1., abs(analytic['total_energy_rate'])),
            metric_time_force_error_per_pool_volume=float(np.max(abs(metric_fd-metric['force'])/volume[:, None, None]))))
    passed = (inverse_error < 1e-6 and all(max(r[k] for k in r if k != 'verification_step') < 1e-6 for r in records))
    return dict(pool_count=len(volume), original_physical_momentum_preserved=True,
        direction_note='Original physical velocity; prescribed zero-sum volume and velocity directions are NOT computed mass/advection/acceleration rates.',
        verification_note='Perturbation intervals respect fixed source topology; they are NOT evolution timesteps.',
        volume_direction_sum=float(vd.sum()), probes=records,
        dual_inverse_derivative_error_per_pool_volume=inverse_error,
        energy_coordinate_error=analytic['energy_coordinate_error'], canonical_metric_local_error=analytic['canonical_metric_local_error'],
        metric_fixed_velocity_work_error=abs(metric['metric_energy_work']-metric['direction']['kinetic_energy_rate']),
        maximum_terrain_metric_rate=float(np.max(abs(metric['direction']['canonical_metric_local_terms']['terrain_metric']))),
        poles=analytic['poles'], metric_poles=metric['direction']['poles'],
        fixed_topology_metric_direction_controls_passed=passed,
        nonlinear_advection_or_complete_force_or_time_or_native_or_gameplay_accepted=False)
