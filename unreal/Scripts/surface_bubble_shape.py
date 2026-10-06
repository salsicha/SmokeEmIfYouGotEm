"""Small isolated floating-bubble approximation; SI units, not full foam CFD.

Patel & Zhu, JFM 1026 A19 (2026), doi:10.1017/jfm.2025.11003,
equations 3.8, 3.4 (zero-rim first approximation), 3.14 and 3.16.
Original implementation. The spherical cavity is an approximation Rb=R0;
its enclosed gas volume is audited, never silently normalized.
"""
import math
import numpy as np


def bessel_k(order, x, nodes=128):
    """Integral definition of K_0/K_1, Gauss-Legendre quadrature, positive x."""
    x = np.asarray(x, dtype=float)
    if order not in (0, 1) or np.any(x <= 0):
        raise ValueError('Only K0/K1 at positive arguments supported')
    end = np.maximum(8., np.arccosh(np.maximum(45/x, 1.)))
    q, w = np.polynomial.legendre.leggauss(nodes)
    t = end[..., None]*(q+1)/2
    return end/2*np.sum(w*np.exp(-x[..., None]*np.cosh(t))*np.cosh(order*t), axis=-1)


def rim_balance(phi, bond):
    root = math.sqrt(1-phi)
    return phi*(bond/16*(1+root)+.5)-bond/12*(1+root)


def shape(radius, density=998., tension=.072, gravity=9.80665):
    if min(radius, density, tension, gravity) <= 0:
        raise ValueError('Positive physical parameters required')
    bond = 4*density*gravity*radius**2/tension
    if not 0 < bond <= .6:
        raise ValueError('This approximation is restricted to small isolated bubbles, Bo <= 0.6')
    lo, hi = 0., 1.
    for _ in range(60):
        mid = (lo+hi)/2
        if rim_balance(mid, bond) > 0:
            hi = mid
        else:
            lo = mid
    phi = (lo+hi)/2
    rim = radius*math.sqrt(phi)
    depth_zero_rim = radius*(1+math.sqrt(1-phi))
    cap = radius/(.5+bond/16*depth_zero_rim/radius)
    cap_height = rim**2/(cap+math.sqrt(cap**2-rim**2))
    length = math.sqrt(tension/(density*gravity))
    slope = rim/math.sqrt(cap**2-rim**2)
    amplitude = length*slope/float(bessel_k(1, rim/length))
    rim_height = amplitude*float(bessel_k(0, rim/length))
    # Sphere below rim plus spherical film cap, both share precisely one rim.
    lower_height = depth_zero_rim
    cavity_volume = math.pi*lower_height**2*(radius-lower_height/3)
    film_volume = math.pi*cap_height**2*(cap-cap_height/3)
    gas_volume = cavity_volume+film_volume
    nominal_volume = 4/3*math.pi*radius**3
    return dict(gas_radius_m=radius, density_kg_m3=density, tension_N_m=tension,
                gravity_m_s2=gravity, bond=bond, rim_radius_m=rim,
                cap_curvature_radius_m=cap, cap_height_above_rim_m=cap_height,
                rim_height_m=rim_height, capillary_length_m=length,
                meniscus_amplitude_m=amplitude, rim_slope=slope,
                cavity_center_z_m=rim_height-radius*math.sqrt(1-phi),
                gas_volume_m3=gas_volume, nominal_gas_volume_m3=nominal_volume,
                relative_gas_volume_error=gas_volume/nominal_volume-1,
                dimensionless_rim_balance_residual=rim_balance(phi, bond))


def meniscus(r, model):
    r = np.asarray(r, dtype=float)
    if np.any(r < model['rim_radius_m']*(1-1e-12)):
        raise ValueError('Meniscus is defined outside the bubble rim')
    return model['meniscus_amplitude_m']*bessel_k(0, r/model['capillary_length_m'])
