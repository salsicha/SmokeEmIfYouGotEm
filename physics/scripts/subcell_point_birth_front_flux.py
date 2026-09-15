"""Original nondispersive dry-Riemann flux on a point source's growing face.

Closed branch integration, not quadrature or a new Riemann model. Original
source faces and the birth knot are retained. This supplies secondary-front
flux coefficients, NOT full rational pressure/force/time/gameplay acceptance.
"""
from fractions import Fraction as F
import math
import numpy as np

from subcell_source_face_section import SourceFaceSection, stage_difference


def point_front_flux(birth, section, height, velocity, normal, gravity=9.81, energy_datum=0.):
    birth.check_height(height)
    if birth.volume_power != 3 or not isinstance(section, SourceFaceSection):
        raise ValueError('Original exact point-source storage and face required')
    face_bound = birth.face_next_height(section)
    if face_bound is not None and F(height) >= face_bound:
        raise ValueError('Point-face probe crosses an original positive face knot')
    u, n = np.asarray(velocity, float), np.asarray(normal, float)
    if (u.shape != (2,) or n.shape != (2,) or not np.isfinite([u, n]).all()
            or abs(float(n@n)-1.) > 1e-12 or not np.isfinite([gravity, energy_datum]).all() or gravity <= 0):
        raise ValueError('Finite velocity, unit outward normal and positive gravity required')
    width_per_height = F(0)
    for first, second in section.source_segments:
        low, high = sorted((first[1]-birth.datum, second[1]-birth.datum))
        if low < 0 or (low == 0 and high == 0):
            raise ValueError('Point-source face must retain its sloping original minimum')
        if low == 0:
            width_per_height += (second[0]-first[0])/high
        elif F(float(height)) >= low:
            raise ValueError('Point-face probe crosses an original positive face knot')
    tangent = np.array([-n[1], n[0]])
    un, ut = F(float(u@n)), F(float(u@tangent))
    g = F(float(gravity))
    h = float(height)
    if F(height) > 0 and h == 0:
        raise ValueError('Positive point-front height underflows represented range')
    # Match the original represented c=sqrt(g*h). Fractions prevent loss of
    # small nonzero velocity coefficients or cancellation between fan powers.
    top = F(math.sqrt(gravity*h))
    wet_top = min(top, un) if un > 0 else F(0)
    fan_low = max(F(0), un if un >= 0 else -un/2)
    wet_mass = width_per_height*un*wet_top**4/(2*g*g)
    wet_pressure = width_per_height*wet_top**6/(6*g*g)

    def fan_moment(power):
        if top <= fan_low:
            return F(0)
        # Integral mass*c^power ds: ds=2*L*c/g dc and
        # mass=(un+2*c)^3/(27*g), only inside its original fan branch.
        return width_per_height*F(2, 27)/(g*g)*sum(
            (F(math.comb(3, j))*un**(3-j)*2**j
             *(top**(j+power+2)-fan_low**(j+power+2))/(j+power+2) for j in range(4)), F(0))

    m0, m1, m2 = (fan_moment(power) for power in range(3))
    mass = wet_mass+m0
    pn = un*wet_mass+wet_pressure+un*m0/2+m1
    pressure = wet_pressure+m1-un*m0/2
    eta = F(stage_difference(0., energy_datum, h, birth.datum))
    energy = wet_mass*((un*un+ut*ut)/2+g*eta)
    energy += m0*(ut*ut/2+g*eta+un*un/6)+F(2, 3)*un*m1-m2/3
    flux = np.r_[float(mass), float(pn)*n+float(ut*mass)*tangent]
    force = float(pressure)*n
    if not np.isfinite(flux).all() or not np.isfinite(force).all() or not math.isfinite(float(energy)):
        raise ValueError('Original point-front flux exceeds represented range')
    if mass < 0 or (mass > 0 and flux[0] == 0):
        raise ValueError('Positive original point-front flux underflows represented range')
    if width_per_height == 0:
        branch, power, coefficient = 'no-immediate-contact', None, 0.
        branch_bound = birth.face_contact(section)['height_above_source_minimum']
    elif un > 0:
        branch, power = 'outward-wet', 2.
        coefficient = float(width_per_height*un/2)
        branch_bound = un*un/g
    elif un == 0:
        branch, power = 'zero-normal-fan', 2.5
        coefficient = float(width_per_height)*16*math.sqrt(gravity)/135
        branch_bound = None
    else:
        branch, power, coefficient = 'receding-dry', None, 0.
        branch_bound = un*un/(4*g)
    if width_per_height > 0 and un >= 0 and coefficient == 0:
        raise ValueError('Nonzero original front coefficient underflows represented range')
    fan_depth = max(F(0), top*top-fan_low*fan_low)/g
    wet_depth = wet_top*wet_top/g
    dry_depth = max(F(0), min(top, fan_low)**2-wet_top**2)/g
    return dict(flux=flux, nonadvective_momentum_flux=force, energy_flux=float(energy),
        face_width_per_height=width_per_height, normal_velocity=float(un),
        branch_projected_widths=dict(wet=float(width_per_height*wet_depth),
                                    fan=float(width_per_height*fan_depth), dry=float(width_per_height*dry_depth)),
        asymptotic_branch=branch, mass_height_power=power, mass_height_coefficient=coefficient,
        asymptotic_branch_height_bound=branch_bound,
        complete_rational_front_or_time_or_native_or_gameplay_accepted=False)
