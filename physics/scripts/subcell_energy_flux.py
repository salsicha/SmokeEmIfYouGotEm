"""Joint nondispersive mass/pressure flux on exact shared terrain sections.

Semidiscrete research component, NOT the two-pole, wet-front time integrator or
playable solver. For pressure J(eta)=g/2 integral(h^2 ds), mass uses the secant
[J]/(g[eta]). Together with arithmetic-mean velocity and pressure this cancels
face energy work, including the independently integrated cell bed force.
Optional conservative dissipation has an explicit nonpositive energy rate.
"""
import math
import numpy as np


def pressure_secant_area(section, left_stage, right_stage, left_datum=0., right_datum=0.):
    """Integral of the exact pressure divided difference, without J subtraction.

    Split each original linear segment at the two wet levels. Both-wet pieces
    integrate mean depth; singly-wet pieces integrate h^2/(2*[eta]). Equal
    stages take the derivative (wet face area), not a small-difference cutoff.
    """
    if not np.isfinite([left_stage, right_stage, left_datum, right_datum]).all():
        raise ValueError('Finite datum-relative stages required')
    delta = math.fsum((right_datum, -left_datum, right_stage, -left_stage))
    if delta == 0:
        return section.moments(left_stage, left_datum)[0]
    if delta < 0:
        left_stage, right_stage = right_stage, left_stage
        left_datum, right_datum = right_datum, left_datum
        delta = -delta
    total = 0.
    for (low, high), width in zip(section.levels, section.lengths):
        a = math.fsum((left_stage, left_datum, -float(low)))
        b = math.fsum((right_stage, right_datum, -float(low)))
        span = high-low
        if b <= 0:
            continue
        if span == 0:
            mean = .5*(a+b) if a >= 0 else .5*b*(b/delta)
        else:
            # Bed coordinate t runs from 0 to span along this segment.
            common = min(max(a, 0.), span)
            mean = (common/span)*.5*(a+b-common) if common > 0 else 0.
            start, end = max(a, 0.), min(b, span)
            if end > start:
                begin_depth, end_depth = b-start, b-end
                # Divide before multiplying the small depths: no avoidable
                # cubic underflow for a representable thin-water face area.
                square_mean = (begin_depth*(begin_depth/delta)+begin_depth*(end_depth/delta)
                               +end_depth*(end_depth/delta))/6
                mean += ((end-start)/span)*square_mean
        total += width*mean
    if not math.isfinite(total) or total < 0:
        raise ValueError('Unrepresentable pressure secant')
    return float(total)


def face_flux(section, left_stage, left_velocity, right_stage, right_velocity, axis,
              gravity=9.81, left_datum=0., right_datum=0., dissipative=False):
    left, right = np.asarray(left_velocity, float), np.asarray(right_velocity, float)
    if (axis not in (0, 1) or left.shape != (2,) or right.shape != (2,)
            or not np.isfinite([left, right]).all() or not math.isfinite(gravity) or gravity <= 0):
        raise ValueError('Finite velocities, positive gravity and XY face normal required')
    al, i2l, _ = section.moments(left_stage, left_datum)
    ar, i2r, _ = section.moments(right_stage, right_datum)
    area = pressure_secant_area(section, left_stage, right_stage, left_datum, right_datum)
    average = .5*(left+right)
    minimum = float(section.levels.min())
    signal = max(abs(left[axis])+math.sqrt(gravity*max(left_stage-(minimum-left_datum), 0)),
                 abs(right[axis])+math.sqrt(gravity*max(right_stage-(minimum-right_datum), 0)))
    # The extra advective bound prevents an exactly dry face from donating
    # volume for the secant-based flux. It is not a pressure/time-step proof.
    speed = max(signal, 2*abs(average[axis])) if dissipative else 0.
    mass = average[axis]*area
    momentum = mass*average
    momentum[axis] += .25*gravity*(i2l+i2r)
    mass -= .5*speed*(ar-al)
    momentum -= .5*speed*(ar*right-al*left)
    delta = math.fsum((right_datum, -left_datum, right_stage, -left_stage))
    work = -.5*speed*(gravity*delta*(ar-al)+.5*(al+ar)*float(np.sum((right-left)**2)))
    result = np.r_[mass, momentum]
    if not np.isfinite(result).all() or not math.isfinite(work):
        raise ValueError('Flux exceeds represented physical range')
    return result, dict(expected_energy_work=work, signal_speed=signal,
                        dissipation_speed=speed, pressure_secant_area=area,
                        left_pressure=.5*gravity*i2l, right_pressure=.5*gravity*i2r)


def rates(patch, volumes, momenta, gravity=9.81, dissipative=False):
    """Closed/periodic exact-geometry patch; no clipping, repair or time update."""
    v, p = np.asarray(volumes, float), np.asarray(momenta, float)
    if (v.shape != patch.shape or p.shape != (*patch.shape, 2) or (v < 0).any()
            or not np.isfinite(v).all() or not np.isfinite(p).all() or np.any(p[v == 0] != 0)):
        raise ValueError('Finite physical volumes/momenta; exactly dry momentum must be zero')
    v, p = v.ravel(), p.reshape(-1, 2)
    # Always use datum-relative storage, irrespective of the legacy patch flag.
    eta = np.array([c.relative_stage_for_volume(q) for c, q in zip(patch.cells, v)])
    datums = np.array([c.datum for c in patch.cells])
    velocity = np.divide(p, v[:, None], out=np.zeros_like(p), where=v[:, None] > 0)
    dv = np.zeros_like(v)
    bed = np.array([c.hydrostatic_bed_force(e, gravity, True) for c, e in zip(patch.cells, eta)])
    dp = bed.copy()
    expected = 0.
    for left, right, axis, section in patch.faces:
        li, ri = (right if left < 0 else left), (left if right < 0 else right)
        ul, ur = velocity[li].copy(), velocity[ri].copy()
        if left < 0:
            ul[axis] *= -1
        if right < 0:
            ur[axis] *= -1
        flux, audit = face_flux(section, eta[li], ul, eta[ri], ur, axis, gravity,
                                datums[li], datums[ri], dissipative)
        if left >= 0:
            dv[left] -= flux[0]
            dp[left] -= flux[1:]
        if right >= 0:
            dv[right] += flux[0]
            dp[right] += flux[1:]
        # Reflection duplicates the same cell on both sides: only its half
        # of the face work belongs to the physical domain.
        expected += audit['expected_energy_work']*(.5 if min(left, right) < 0 else 1.)
    gradient = gravity*((datums-datums.min())+eta)-.5*np.sum(velocity*velocity, axis=1)
    energy_rate = float(gradient@dv+np.sum(velocity*dp))
    return dict(volume_rate=dv.reshape(patch.shape), momentum_rate=dp.reshape((*patch.shape, 2)),
                energy_rate=energy_rate, expected_energy_rate=float(expected),
                energy_identity_error=abs(energy_rate-expected),
                bed_force=bed.reshape((*patch.shape, 2)),
                time_or_two_pole_or_gameplay_accepted=False)
