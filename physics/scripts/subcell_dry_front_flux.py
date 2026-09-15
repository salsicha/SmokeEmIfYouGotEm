"""One-sided nondispersive dry-bed Riemann flux on a source terrain edge.

This is not the rational dispersive front model. The dry side has zero water,
not a chosen artificial water level. Wet-side velocity is constant on the face;
depth follows its original linear terrain segments. Four-point Gauss in wave
speed integrates the branch polynomials exactly up to floating-point error.
"""
import math
import numpy as np
from subcell_source_face_section import stage_difference


def flux(section, stage, datum, velocity, normal, gravity=9.81, energy_datum=0.):
    u, n = np.asarray(velocity, float), np.asarray(normal, float)
    if (u.shape != (2,) or n.shape != (2,) or not np.isfinite([u, n]).all()
            or abs(float(n@n)-1.) > 1e-12 or not all(math.isfinite(v) for v in (stage, datum, gravity, energy_datum))
            or gravity <= 0):
        raise ValueError('Finite wet state, unit outward normal and positive gravity required')
    tangent = np.array([-n[1], n[0]])
    un, ut = float(u@n), float(u@tangent)
    eta = stage_difference(0., energy_datum, stage, datum)
    nodes, weights = np.polynomial.legendre.leggauss(4)
    result = np.zeros(4)  # volume, XY momentum, energy relative to fixed datum
    direct_force = np.zeros(2)
    branch_widths = dict(dry=0., wet=0., fan=0.)
    def at(c):
        front = un+2*c
        if front <= 0:
            return np.zeros(4), 'dry', np.zeros(2)
        h = c*(c/gravity)
        if un >= c:
            mass = h*un
            pn = mass*un+.5*gravity*h*h
            force = .5*gravity*h*h
            energy = mass*(.5*(un*un+ut*ut)+gravity*eta)
            branch = 'wet'
        else:
            star = front/3
            hs = star*(star/gravity)
            mass = hs*star
            pn = 1.5*mass*star
            force = mass*(c-.5*un)
            # h+b=eta on the original wet side; b need not be flattened.
            energy = mass*(1.5*star*star+.5*ut*ut+gravity*eta-c*c)
            branch = 'fan'
        return np.r_[mass, pn*n+mass*ut*tangent, energy], branch, force*n
    for (b, a), span, width in zip(section.depth_intervals(stage, datum), section.bed_spans, section.lengths):
        if b <= 0:
            continue
        if a < 0:
            width *= b/span
            a = 0.
        ca, cb = math.sqrt(gravity*a), math.sqrt(gravity*b)
        if ca == cb:
            value, branch, force = at(ca)
            result += width*value
            direct_force += width*force
            branch_widths[branch] += float(width)
            continue
        knots = [ca, cb]
        switch = un if un > 0 else -un/2
        if ca < switch < cb:
            knots.append(switch)
        knots.sort()
        for first, last in zip(knots, knots[1:]):
            part = width*((last-first)/(cb-ca))*((last+first)/(cb+ca))
            cs = .5*(first+last)+.5*(last-first)*nodes
            for c, weight in zip(cs, weights):
                value, branch, force = at(float(c))
                ds = part*weight*c/(first+last)
                result += ds*value
                direct_force += ds*force
                branch_widths[branch] += float(ds)
    if not np.isfinite(result).all() or not np.isfinite(direct_force).all() or result[0] < 0:
        raise ValueError('Dry-front flux exceeds represented range')
    if result[0] == 0 and branch_widths['wet']+branch_widths['fan'] > 0:
        raise ValueError('Positive dry-front flux underflows represented range')
    if result[0] == 0 and np.any(result[1:] != 0):
        raise ValueError('Unrepresentable zero-mass dry-front momentum/energy')
    return result[:3], dict(energy_flux=float(result[3]), branch_projected_widths=branch_widths,
                            nonadvective_momentum_flux=direct_force.tolist(),
                            dispersive_front_or_time_or_gameplay_accepted=False)
