"""Independent finite-volume probes of a fixed-topology pressure direction."""
import numpy as np

from finite_depth_pressure_reference import LENGTHS
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_pressure_rate import WetPoolPressureRate, dual_direction


def audit_direction(pools):
    volume = np.array([p['volume'] for p in pools.pools])
    index = np.arange(len(volume))
    pattern = .2*np.sin(.73*index+.2)
    vd = volume*(pattern-float(np.sum(volume*pattern)/np.sum(volume)))
    # This deliberately distinguishes same-cell pools. It is NOT a computed
    # mass flux or a physical acceleration from the captured velocity state.
    v = np.array([p['momentum']/p['volume'] for p in pools.pools])[:, None, :]
    vt = .1*np.stack((np.cos(.31*index), np.sin(.47*index)), axis=-1)[:, None, :]
    q = np.sqrt(volume)[:, None, None]*v
    analytic = dual_direction(pools, v, vd[:, None], vt)
    directions = [WetPoolPressureRate(WetPoolPressureSystem(pools, float(length)), vd[:, None]) for length in LENGTHS]
    step = 1e-4
    # Only the verification perturbation shrinks to respect source topology.
    # This is never reported as an evolution timestep or stability result.
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
        raise ValueError('No representable fixed-topology verification interval')
    records = []
    for epsilon in (step, step/2, step/4):
        low = pools.volume_probe(volume-epsilon*vd)
        high = pools.volume_probe(volume+epsilon*vd)
        low_value = dual_direction(low, v-epsilon*vt, vd[:, None]*0)
        high_value = dual_direction(high, v+epsilon*vt, vd[:, None]*0)
        errors = {}
        for key in ('kinetic', 'potential', 'total', 'physical_momentum'):
            fd = (high_value[key]-low_value[key])/(2*epsilon)
            actual = analytic[key+'_rate']
            errors[key] = float(np.max(abs(fd-actual))/max(1., float(np.max(abs(actual)))))
            if key == 'physical_momentum':
                errors['momentum_rate_error_per_pool_volume'] = float(np.max(abs(fd-actual)/volume[:, None, None]))
        pole_errors = []
        for length, rate in zip(LENGTHS, directions):
            ls, hs = WetPoolPressureSystem(low, float(length)), WetPoolPressureSystem(high, float(length))
            fd = (hs.apply(q)-ls.apply(q))/(2*epsilon)
            expected = rate.apply(q)
            pole_errors.append(dict(length=float(length),
                scaled_action_error=float(np.max(abs(fd-expected))/max(1., float(np.max(abs(expected))))),
                maximum_pool_scaled_action_error=float(np.max(abs(fd-expected)/np.maximum(1., abs(expected))))))
        records.append(dict(verification_step=epsilon, errors=errors, poles=pole_errors,
            perturbed_pole_solves=[dict(side=side, poles=value['poles']) for side, value in (('low', low_value), ('high', high_value))]))
    # These bound differential consistency only. Full dynamical conservation
    # and the existing nonlinear gates are deliberately neither run nor waived.
    passed = all(max(r['errors'].values()) < 1e-6
                 and all(max(p['scaled_action_error'], p['maximum_pool_scaled_action_error']) < 1e-6 for p in r['poles'])
                 for r in records)
    return dict(pool_count=len(volume), direction='Controlled zero-sum volume direction and prescribed velocity direction; NOT evolution',
        volume_direction_sum=float(np.sum(vd)), volume_direction_m3=vd.tolist(),
        volume_direction_relative_min_max=[float(np.min(vd/volume)), float(np.max(vd/volume))],
        analytic_energy={k: analytic[k] for k in ('kinetic', 'potential', 'total', 'kinetic_rate', 'potential_rate', 'total_rate')},
        original_poles=analytic['poles'], probes=records, fixed_topology_direction_controls_passed=passed,
        nonlinear_or_wetting_or_time_or_gameplay_accepted=False)
