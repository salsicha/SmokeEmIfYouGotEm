"""Original section-integrated Rusanov base flux with positive donor records.

Nondispersive wet-front research component, not the full rational dynamics.
Unlike pressure-secant central advection, both mass/momentum donor coefficients
are nonnegative. Exact original linear-bed area and pressure moments are used.
"""
import numpy as np


def flux(section, left_stage, left_velocity, right_stage, right_velocity, normal,
         gravity=9.81, left_datum=0., right_datum=0.):
    n = np.asarray(normal, float)
    if n.shape != (2,) or not np.isfinite(n).all() or abs(float(n@n)-1.) > 1e-12:
        raise ValueError('Finite unit face normal required')
    basis = np.array([n, [-n[1], n[0]]])
    ul, ur = basis@np.asarray(left_velocity, float), basis@np.asarray(right_velocity, float)
    value, speed = section.flux(left_stage, ul, right_stage, ur, 0, gravity, left_datum, right_datum)
    al, i2l, _ = section.moments(left_stage, left_datum)
    ar, i2r, _ = section.moments(right_stage, right_datum)
    left, right = .5*(speed+ul[0])*al, .5*(speed-ur[0])*ar
    if min(left, right) < 0 or not np.isfinite([left, right]).all():
        raise ValueError('Donor face coefficients must be nonnegative and finite')
    return np.r_[value[0], basis.T@value[1:]], dict(left_pressure=.5*gravity*i2l,
        right_pressure=.5*gravity*i2r, left_donor=float(left), right_donor=float(right),
        velocity_exchange=float(min(left, right)), signal_speed=speed)
