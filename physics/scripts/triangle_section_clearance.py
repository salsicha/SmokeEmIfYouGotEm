"""Exact one-dimensional clearance on the common UE Landscape triangle grid.

This does not establish boat-footprint clearance or a physically solved stage.
The sampler must use the NW-SE diagonal and the supplied common grid origin.
"""
import numpy as np


def section_knots(center, direction, bounds, origin, spacing):
    center, direction, origin = [np.asarray(v, dtype=float) for v in (center, direction, origin)]
    bounds = np.asarray(bounds, dtype=float)
    if (any(v.shape != (2,) or not np.isfinite(v).all() for v in (center, direction, origin, bounds))
            or not np.isfinite(spacing) or spacing <= 0 or bounds[0] >= bounds[1]
            or not np.isclose(np.linalg.norm(direction), 1., rtol=0, atol=1e-10)):
        raise ValueError('Finite geometry, ordered bounds, unit direction and positive grid spacing required')
    base = (center-origin)/spacing
    delta = direction/spacing
    knots = [float(bounds[0]), float(bounds[1])]
    # Northing increases opposite to UE row. Thus row=column diagonals lie
    # on integer east+north grid coordinates, not east-north coordinates.
    for offset, slope in ((base[0], delta[0]), (base[1], delta[1]), (base.sum(), delta.sum())):
        if abs(slope) < 1e-14:
            continue
        ends = offset+slope*bounds
        count = int(np.floor(max(ends))-np.ceil(min(ends))+1)
        if count > 1000000:
            raise ValueError('Unbounded section request')
        if count > 0:
            values = (np.arange(np.ceil(min(ends)), np.floor(max(ends))+1)-offset)/slope
            knots.extend(values[(values > bounds[0]) & (values < bounds[1])].tolist())
    return np.unique(knots)


def supported_intervals(knots, heights, maximum_bed):
    knots, heights = [np.asarray(v, dtype=float) for v in (knots, heights)]
    if (knots.ndim != 1 or len(knots) < 2 or heights.shape != knots.shape
            or not np.isfinite(knots).all() or not np.isfinite(heights).all()
            or np.any(np.diff(knots) <= 0) or not np.isfinite(maximum_bed)):
        raise ValueError('Finite ordered section required; missing terrain cannot pass')
    intervals = []
    for a, b, za, zb in zip(knots[:-1], knots[1:], heights[:-1], heights[1:]):
        if za > maximum_bed and zb > maximum_bed:
            continue
        if za > maximum_bed or zb > maximum_bed:
            crossing = a+(b-a)*(maximum_bed-za)/(zb-za)
            if za > maximum_bed:
                a = crossing
            else:
                b = crossing
        if b <= a:
            continue
        if intervals and a <= intervals[-1][1]+1e-10:
            intervals[-1][1] = float(b)
        else:
            intervals.append([float(a), float(b)])
    return intervals


def evaluate_section(sampler, center, direction, bounds, origin, spacing, stage, depth=.3):
    if not np.isfinite(stage) or not np.isfinite(depth) or depth < 0:
        raise ValueError('Finite stage and nonnegative depth required')
    knots = section_knots(center, direction, bounds, origin, spacing)
    xy = np.asarray(center)+knots[:, None]*np.asarray(direction)
    bed = sampler(xy)
    intervals = supported_intervals(knots, bed, stage-depth)
    # Catch a mismatched diagonal/grid or sampler before claiming exactness.
    mid = (knots[1:]+knots[:-1])/2
    actual = sampler(np.asarray(center)+mid[:, None]*np.asarray(direction))
    if not np.allclose(actual, (bed[1:]+bed[:-1])/2, rtol=0, atol=1e-7):
        raise ValueError('Sampler is not linear on the declared triangle segments')
    return dict(knots_m=knots.tolist(), bed_m=bed.tolist(), supported_intervals_m=intervals,
                continuous_width_m=max((b-a for a, b in intervals), default=0.))
