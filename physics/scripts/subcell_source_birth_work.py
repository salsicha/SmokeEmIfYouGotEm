"""Analytic leading pressure work at simultaneous point births, NOT a force.

For original source heights k_i*e, bounded newborn physical velocities and fixed
old V/P, derive e^2*dE/dV_i and e*dE/dP_i. These are boundary coefficients of
the original Hamiltonian. No energy projection, finite-difference force, dry
inverse mass, extra water, accepted flux or time step is supplied.
"""
import math
import numpy as np

from subcell_simultaneous_birth_pressure import point_limits, birth_faces, harmonic_height_coefficient
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_frames import face_section
from subcell_wet_pool_pressure_rate import _harmonic_interval_rate


def harmonic_coefficient_partials(section, datum, left_scale, right_scale):
    """Original integrated stage partials, including the vanishing wet edge.

    The moving boundary contributes zero because the harmonic column vanishes
    there. Equal scales use the continuous .5/.5 stage partials, not a selected
    minimum's derivative. The original small-difference series is retained.
    """
    harmonic_height_coefficient(section, datum, left_scale, right_scale)
    swapped = left_scale > right_scale
    low, high = sorted((left_scale, right_scale))
    partials = [[], []]
    for first, second in section.source_segments:
        a, b = sorted((first[1]-datum, second[1]-datum))
        if a != 0:
            continue
        width = float((second[0]-first[0])/b)*low
        for axis in range(2):
            partials[axis].append(_harmonic_interval_rate(0., low, low, width, high-low,
                                                         float(axis == 0), float(axis == 1)))
    result = np.array([math.fsum(p) for p in partials])
    return result[::-1] if swapped else result


def point_work(context, requests):
    requests = list(requests)
    limit = point_limits(context, requests)
    keys, scales = limit['source_keys'], limit['stage_scales']
    coefficients = limit['volume_path_coefficients']
    roots, count = np.sqrt(coefficients), len(keys)
    births = [SourceBirthGeometry(context.partition.patch.cells[p].subset_sources([s])) for p, s in keys]
    lookup = {key: i for i, key in enumerate(keys)}
    # dM/dk: only new/new faces depend on relative stage scales. Old-wet and
    # physical-wall self rows and each original source-cone factor are constant.
    derivatives = np.zeros((count, count, 3, 2*count))
    face_records = []
    for face in birth_faces(context.partition, keys):
        li = lookup.get((face['left_parent'], face['left_source']))
        ri = lookup.get((face['right_parent'], face['right_source']))
        if li is None or ri is None or li == ri or births[li].datum != births[ri].datum:
            continue
        section = face_section(face['segment'])
        area = harmonic_height_coefficient(section, births[li].datum, scales[li], scales[ri])
        if area == 0:
            continue
        partials = harmonic_coefficient_partials(section, births[li].datum, scales[li], scales[ri])
        face_records.append(dict(left=li, right=ri, area_coefficient=area, stage_partials=partials))
        for parameter, area_rate in zip((li, ri), partials):
            for owner in (li, ri):
                for target, sign in ((li, -1.), (ri, 1.)):
                    # M coefficient = sign*k_owner*A/(2*sqrt(R_owner*R_target)).
                    # Keep both roots, even when owner == target.
                    rate = area_rate
                    if parameter == owner:
                        rate -= .5*area/scales[owner]
                    if parameter == target:
                        rate -= 1.5*area/scales[target]
                    rate *= sign*scales[owner]/(2*roots[owner]*roots[target])
                    derivatives[parameter, owner, 0, 2*target:2*target+2] += rate*face['normal']
    mappings, factors = limit['newborn_jet_maps'], limit['newborn_scaled_factors']
    old_columns = limit['old_divergence_column_sqrt_path_coefficient']
    gradient = np.zeros(count)
    canonical = np.zeros((count, 2))
    poles = []
    for (original, stress), pole in zip(context.poles, limit['poles']):
        if original['beta'] != pole['beta']:
            raise ValueError('Matching original pressure poles required')
        alpha, beta = pole['alpha'], pole['beta']
        x = pole['coupled_response'].ravel()
        coupling = old_columns.T@stress
        stage_gradient = np.empty(count)
        for parameter in range(count):
            start = 2*parameter
            cross_work = .5*float(coupling[start:start+2]@x[start:start+2])/scales[parameter]
            # .5*x.T*D_k*x = sum (F*M*x).(F*M_k*x), no differentiated solve.
            principal_work = math.fsum(float((factor@(mapping@x))@(factor@(derivative@x)))
                for factor, mapping, derivative in zip(factors, mappings, derivatives[parameter]))
            stage_gradient[parameter] = -alpha*beta*cross_work+alpha*beta*beta*principal_work
        gradient += stage_gradient
        canonical += alpha*pole['coupled_response']/roots[:, None]
        poles.append(dict(beta=beta, alpha=alpha, energy_stage_scale_gradient=stage_gradient,
                          original_coupled_pressure_residual=pole['relative_residual']))
    volume_gradient = gradient*scales/(3*coefficients)
    slope = limit['fixed_old_state_energy_path_slope']
    homogeneous_error = abs(float(scales@gradient)-slope)
    if not all(np.isfinite(v).all() for v in (derivatives, gradient, volume_gradient, canonical)):
        raise ValueError('Original singular birth work exceeds represented range')
    if homogeneous_error > 1e-10:
        raise ValueError('Original pressure-birth homogeneity/chain-rule gate failed')
    return dict(limit=limit, new_face_stage_partials=face_records,
        energy_stage_scale_gradient=gradient, volume_gradient_path_squared_limit=volume_gradient,
        canonical_velocity_path_limit=canonical, poles=poles, homogeneity_error=homogeneous_error,
        # Conditional test direction: V_i=R_i*t, e=t^(1/3). R_i need not be a
        # physical receipt. This is NOT a suggested integrator or accepted flux.
        fixed_old_bounded_velocity_mass_direction_work_coefficient=float(coefficients@volume_gradient),
        energy_rate_time_power=-2/3,
        bounded_physical_momentum_rates_cannot_cancel_leading_work=bool(slope != 0.),
        full_metric_front_force_or_time_or_gameplay_accepted=False)
