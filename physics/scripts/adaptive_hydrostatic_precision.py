"""Exact fallback for cancellation-prone CPU reference face polynomials.

This changes arithmetic precision, never a wet/dry threshold. The fast-path
error scale only chooses whether to evaluate the SAME reconstruction using
rational arithmetic on represented inputs. The exact result is rounded once
to the caller's dtype. This module does not consume GPU intermediates.
"""
from fractions import Fraction
import numpy as np


def refine_faces(depth, bed, axis, periodic, exterior, second_order, flattened,
                 hm, hp, ha, hb, reduced_a, reduced_b, before_a, before_b, *, slope_factors=None):
    # Conservative local roundoff scale for the short MC/bed-offset expression.
    # Use bed DIFFERENCES: translating the height datum must not trigger a
    # different arithmetic path. Deeply blocked faces do not need a fallback.
    scale = abs(depth).copy()
    for shift in (-1, 1):
        scale += abs(np.roll(depth, shift, axis))
        scale += abs(bed-np.roll(bed, shift, axis))
    eps = 64*np.finfo(depth.dtype).eps
    minus_risk = (depth > 0) & (abs(hm) <= eps*scale)
    plus_risk = (depth > 0) & (abs(hp) <= eps*scale)
    sa = np.concatenate((np.take(scale, [-1] if periodic else [0], axis), scale), axis)
    sb = np.concatenate((scale, np.take(scale, [0] if periodic else [-1], axis)), axis)
    owners_a = np.concatenate((np.take(depth, [-1] if periodic else [0], axis), depth), axis)
    owners_b = np.concatenate((depth, np.take(depth, [0] if periodic else [-1], axis)), axis)
    if exterior is not None:
        es, eb = exterior; ny, nx = depth.shape
        count, start = (ny, 0) if axis == 1 else (nx, 2*ny)
        for face, offset, which in ((0, start, 0), (-1, start+count, 1)):
            edge = [slice(None)]*2; edge[axis] = face; edge = tuple(edge)
            own = np.take(bed, 0 if face == 0 else -1, axis)
            ghost_scale = abs(es[offset:offset+count, 0])+abs(eb[offset:offset+count]-own)
            (sa if which == 0 else sb)[edge] = ghost_scale
            (owners_a if which == 0 else owners_b)[edge] = es[offset:offset+count, 0]
    bound = eps*(sa+sb)
    risk_a = (owners_a > 0) & (abs(before_a) <= bound)
    risk_b = (owners_b > 0) & (abs(before_b) <= bound)
    if slope_factors is not None:
        # Fractional slopes can cancel only after subtracting both owners'
        # reconstructed bed offsets. Near-equal reduced faces need the same
        # rational evaluation as near-zero ones; otherwise an exact resting
        # lake acquires a spurious pressure jump from separate roundings.
        # This selects precision only, never forces equality or changes state.
        equal_risk = ((owners_a > 0) | (owners_b > 0)) & (abs(reduced_a-reduced_b) <= bound)
        risk_a |= equal_risk; risk_b |= equal_risk
    if not (minus_risk.any() or plus_risk.any() or risk_a.any() or risk_b.any()):
        return
    n = depth.shape[axis]
    cache = {}

    def polynomial(point):
        if point in cache:
            return cache[point]
        coordinate = point[axis]
        if coordinate < 0 or coordinate >= n:
            if periodic:
                wrapped = list(point); wrapped[axis] %= n
                return polynomial(tuple(wrapped))
            if exterior is None:
                clamped = list(point); clamped[axis] = min(n-1, max(0, coordinate))
                return polynomial(tuple(clamped))
            ny, nx = depth.shape
            count, start = (ny, 0) if axis == 1 else (nx, 2*ny)
            index = start+(count if coordinate >= n else 0)+point[1-axis]
            return Fraction(float(exterior[0][index, 0])), Fraction(float(exterior[1][index])), Fraction(0), Fraction(0)
        h, z = Fraction(float(depth[point])), Fraction(float(bed[point]))
        dh = de = Fraction(0)
        if second_order and h > 0 and (periodic or 0 < coordinate < n-1) and not (flattened is not None and flattened[point]):
            p = list(point); q = list(point)
            p[axis] = (coordinate-1) % n; q[axis] = (coordinate+1) % n
            p, q = tuple(p), tuple(q)
            if depth[p] > 0 and depth[q] > 0:
                back = h-Fraction(float(depth[p])); front = Fraction(float(depth[q]))-h
                def limited(a, b):
                    if a > 0 and b > 0: return min(2*a, (a+b)/2, 2*b)
                    if a < 0 and b < 0: return max(2*a, (a+b)/2, 2*b)
                    return Fraction(0)
                dh = limited(back, front)
                de = limited(back+z-Fraction(float(bed[p])), front+Fraction(float(bed[q]))-z)
                if slope_factors is not None:
                    factor = Fraction(float(slope_factors[point]))
                    dh *= factor; de *= factor
        cache[point] = h, z, dh, de
        return cache[point]

    for sign, mask, target in ((-1, minus_risk, hm), (1, plus_risk, hp)):
        for point in map(tuple, np.argwhere(mask)):
            h, _, dh, _ = polynomial(point)
            target[point] = float(h+sign*dh/2)
    for face in map(tuple, np.argwhere(risk_a | risk_b)):
        p = list(face); p[axis] -= 1; p = tuple(p)
        q = tuple(face)
        lh, lz, ld, le = polynomial(p); rh, rz, rd, re = polynomial(q)
        # Nonperiodic endpoint polynomials are constant, including ghosts.
        left, right = lh+ld/2, rh-rd/2
        jump = rz-lz-(re-rd)/2-(le-ld)/2
        ha[face], hb[face] = float(left), float(right)
        reduced_a[face] = float(max(Fraction(0), left-max(Fraction(0), jump)))
        reduced_b[face] = float(max(Fraction(0), right-max(Fraction(0), -jump)))
