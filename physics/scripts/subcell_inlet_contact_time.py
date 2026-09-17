"""Certified first contact with STATIC original wet support, not a front law.

At X=A+s*D+u*age the inlet sweep is positive exactly when s,age>=0 and
time > (B*s/k)**3+age. Minimize this convex cubic on the transformed wet
polygon. Its age derivative is one, so minima lie on polygon edges. Original
data stay rational; quadratic stationary roots receive explicit bounds.
This conditional construction does not evolve existing water or pressure.
"""
from fractions import Fraction as F
from math import isqrt

from subcell_exact_geometry import SourceFragment, clip, triangulate, area


def _cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def _sqrt_bounds(value, bits):
    n, d = value.numerator, value.denominator
    root = isqrt(n*d)
    if root*root == n*d:
        return F(root, d), F(root, d)
    denominator = d*(1 << bits)
    root = isqrt(n*d*(1 << (2*bits)))
    return F(root, denominator), F(root+1, denominator)


def first_contact(sweep, fragment, relative_bound=F(1, 10**12), max_bits=256):
    """Infimum time of positive footprint overlap with one convex polygon.

    Boundary contact alone has zero volume. A zero-area reachable polygon is
    not reported as a future positive intersection. Times beyond the sweep's
    own outward/edge branch are retained but explicitly unqualified.
    """
    bound = F(relative_bound)
    if not 0 < bound < 1 or type(max_bits) is not int or not 16 <= max_bits <= 4096:
        raise ValueError('Strict contact-time relative bound and 16..4096 bits required')
    sweep._constraints(fragment)  # Validate positive, convex ORIGINAL support.
    origin, direction, velocity = sweep.edge[0], sweep.delta, sweep.velocity
    determinant = _cross(direction, velocity)
    transformed = []
    for point in fragment.polygon:
        offset = (point[0]-origin[0], point[1]-origin[1])
        transformed.append((_cross(offset, velocity)/determinant,
                            _cross(direction, offset)/determinant, point[2]))
    polygon = clip(clip(tuple(transformed), 0, F(0), True), 1, F(0), True)
    if sum(map(area, triangulate(polygon)), F(0)) == 0:
        return dict(positive_contact_possible=False, time_lower=None, time_upper=None,
                    within_sweep_own_branch_bound=False, physical_update_accepted=False)
    coefficient = (sweep.bed_span/sweep.height_scale)**3
    endpoints = [coefficient*p[0]**3+p[1] for p in polygon]
    stationary = []
    for a, b in zip(polygon, polygon[1:]+polygon[:1]):
        ds, da = b[0]-a[0], b[1]-a[1]
        if ds == 0:
            continue
        q = -da/(3*coefficient*ds)
        if q > 0 and min(a[0], b[0])**2 < q < max(a[0], b[0])**2:
            # At s=sqrt(q), c*s^3+age = intercept-2*c*q*sqrt(q).
            stationary.append((a[1]-da*a[0]/ds, q))
    for bits in range(16, max_bits+1, 16):
        lower = upper = min(endpoints)
        for intercept, q in stationary:
            lo, hi = _sqrt_bounds(q, bits)
            lower = min(lower, intercept-2*coefficient*q*hi)
            upper = min(upper, intercept-2*coefficient*q*lo)
        # Objective is nonnegative on the exact clipped quadrant.
        lower = max(F(0), lower)
        if upper-lower <= bound*upper:
            break
    else:
        raise ValueError('Contact-time bound unresolved; no guessed contact or lost interval')
    height_limit = min(sweep.bed_span, sweep.jacobian**2/
                       (sweep.gravity*sum(x*x for x in direction)))
    time_limit = (height_limit/sweep.height_scale)**3
    return dict(positive_contact_possible=True, time_lower=lower, time_upper=upper,
                contact_relative_bound=bound, stationary_candidates=len(stationary), root_bits=bits,
                sweep_own_branch_time_limit=time_limit,
                within_sweep_own_branch_bound=upper < time_limit,
                physical_update_accepted=False)


def initial_wet_contact(sweep, fragment, stage_offset, datum, **options):
    """Use actual wet support, not ownership of a partially wet triangle."""
    sweep._constraints(fragment)
    try:
        surface = F(datum)+F(stage_offset)
    except (ValueError, TypeError, OverflowError, ZeroDivisionError) as exc:
        raise ValueError('Finite exact original stage offset and datum required') from exc
    if surface <= min(p[2] for p in fragment.polygon):
        return dict(positive_contact_possible=False, time_lower=None, time_upper=None,
                    within_sweep_own_branch_bound=False, physical_update_accepted=False)
    wet = SourceFragment(fragment.source_id, clip(fragment.polygon, 2, surface, False), fragment.gradient)
    return first_contact(sweep, wet, **options)
