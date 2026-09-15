"""Original section-integrated Rusanov base flux with positive donor records.

Nondispersive wet-front research component, not the full rational dynamics.
Unlike pressure-secant central advection, both mass/momentum donor coefficients
are nonnegative. Exact original linear-bed area and pressure moments are used.
"""
import math
import numpy as np


def flux(section, left_stage, left_velocity, right_stage, right_velocity, normal,
         gravity=9.81, left_datum=0., right_datum=0.):
    n = np.asarray(normal, float)
    if n.shape != (2,) or not np.isfinite(n).all() or abs(float(n@n)-1.) > 1e-12:
        raise ValueError('Finite unit face normal required')
    velocities = np.asarray([left_velocity, right_velocity], float)
    if (velocities.shape != (2, 2) or not np.isfinite(velocities).all()
            or not math.isfinite(gravity) or gravity <= 0):
        raise ValueError('Finite velocities and positive gravity required')
    basis = np.array([n, [-n[1], n[0]]])
    ul, ur = velocities@basis.T
    al, i2l, _ = section.moments(left_stage, left_datum)
    ar, i2r, _ = section.moments(right_stage, right_datum)
    cl = math.sqrt(gravity)*math.sqrt(section.maximum_depth(left_stage, left_datum))
    cr = math.sqrt(gravity)*math.sqrt(section.maximum_depth(right_stage, right_datum))
    # Preserve the bound as two terms: subtracting velocity from an already
    # rounded |u|+c erases representable return flow when c is sub-ulp in |u|.
    if math.fsum([abs(ul[0]), cl, -abs(ur[0]), -cr]) >= 0:
        advection, celerity = abs(ul[0]), cl
    else:
        advection, celerity = abs(ur[0]), cr
    left_speed = .5*math.fsum([advection, celerity, ul[0]])
    right_speed = .5*math.fsum([advection, celerity, -ur[0]])
    left, right = left_speed*al, right_speed*ar
    if min(left, right) < 0 or not np.isfinite([left, right]).all():
        raise ValueError('Donor face coefficients must be nonnegative and finite')
    if (left == 0 and left_speed > 0 and al > 0) or (right == 0 and right_speed > 0 and ar > 0):
        raise ValueError('Positive donor flux underflows represented range; no deletion')
    # Assemble the original mathematical Rusanov flux from these same donors,
    # not from a second cancellation-prone central-minus-diffusive expression.
    pressure = .25*gravity*(i2l+i2r)
    value = np.array([left-right,
        math.fsum([left*ul[0], -right*ur[0], pressure]),
        math.fsum([left*ul[1], -right*ur[1]])])
    return np.r_[value[0], basis.T@value[1:]], dict(left_pressure=.5*gravity*i2l,
        right_pressure=.5*gravity*i2r, left_donor=float(left), right_donor=float(right),
        velocity_exchange=float(min(left, right)), signal_speed=advection+celerity,
        signal_advection=float(advection), signal_celerity=celerity)
