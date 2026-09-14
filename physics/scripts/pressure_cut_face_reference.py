"""Exact scalar integration of an existing quadratic pressure column.

This is a derivation/reference utility, NOT a new pressure solver or face flux.
For p(s)=alpha*(1-s)+beta*(1-s*s), alpha=4B-6P/H, beta=6P/H-3B,
integrate the top R of a column of height H. P is its integrated pressure and
B its bottom pressure, both per density. Supply nonhydrostatic values to inspect
only that contribution; this utility does not add hydrostatic gravity.

The transmitted integral is P*r*r*(3-2*r)-H*B*r*r*(1-r), r=R/H.
The lower/blocked part is retained, not discarded. Its integral is P minus
the transmitted integral. Neither is necessarily positive.

Exact rational arithmetic carries the represented scalar inputs through both
integrals and their directional derivatives, avoiding intermediate overflow and
underflow. This deliberately slow reference makes no GPU/performance claim.
It does not reconstruct a pressure profile at a face, choose a shared Riemann
flux, or supply the compatible pressure kinematics/adjoint solve.
"""
from dataclasses import dataclass
from fractions import Fraction
import math
from numbers import Real


def _exact(value):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError('Pressure column requires finite real scalars')
    if isinstance(value, Fraction):
        return value
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('Pressure column requires finite real scalars') from exc
    if not math.isfinite(value):
        raise ValueError('Pressure column requires finite real scalars')
    return Fraction.from_float(value)


def represented_float(value):
    """Round an exact result once; reject range loss rather than silently zero it."""
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError('Pressure integral exceeds float storage range') from exc
    if not math.isfinite(result) or (value != 0 and result == 0):
        raise ValueError('Pressure integral exceeds float storage range')
    return result


@dataclass(frozen=True)
class PressureCut:
    transmitted: Fraction
    blocked: Fraction
    transmitted_rate: Fraction
    blocked_rate: Fraction

    def as_floats(self):
        return {name: represented_float(getattr(self, name)) for name in
                ('transmitted', 'blocked', 'transmitted_rate', 'blocked_rate')}


def cut_pressure_column(height, integrated, bottom, retained_height, *,
                        height_rate=0., integrated_rate=0., bottom_rate=0.,
                        retained_height_rate=0.):
    """Integrals and exact chain-rule rates on a positive, possibly tiny column.

    At either end of 0 <= R <= H require a feasible right directional tangent.
    A dry H=0 has no normalized column and is rejected, not assigned a floor.
    Callers must supply an actual column/profile and its cut in the SAME vertical
    coordinates. Cell pressures are not automatically face-reconstructed here.
    """
    h, p, b, retained, ht, pt, bt, rt = map(_exact, (height, integrated, bottom,
        retained_height, height_rate, integrated_rate, bottom_rate, retained_height_rate))
    if h <= 0 or retained < 0 or retained > h:
        raise ValueError('Cut requires a positive column and 0 <= retained height <= height')
    if (retained == 0 and rt < 0) or (retained == h and rt > ht):
        raise ValueError('Cut tangent leaves the physical column')
    r = retained/h
    r_rate = (rt-r*ht)/h
    f = r*r*(3-2*r)
    g = -r*r*(1-r)
    transmitted = p*f+h*b*g
    # Algebraically complementary form retains a tiny blocked sliver in the
    # reference, even where float(P)-float(T) would cancel it away.
    blocked = p*(1-r)**2*(1+2*r)+h*b*r*r*(1-r)
    transmitted_rate = pt*f+(ht*b+h*bt)*g + (
        6*p*r*(1-r)+h*b*r*(3*r-2))*r_rate
    return PressureCut(transmitted, blocked, transmitted_rate, pt-transmitted_rate)
