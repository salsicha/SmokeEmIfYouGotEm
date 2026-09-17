"""Exact inner/outer bounds for SAME-TIME conditional inlet footprints.

In inlet coordinates the footprint is 0<=s<=k*R/B and
0<=age<=R^3-(B*s/k)^3. Chords of this concave upper boundary lie inside;
its tangents lie outside. Rational convex clipping therefore certifies
positive overlap or zero-area separation without sampling/depth cutoffs.
This does not supply a merged state, pressure interaction or time update.
"""
from dataclasses import replace
from fractions import Fraction as F

from subcell_inlet_sweep_geometry import InletSweep


def _cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def _clean(points):
    result = []
    for point in points:
        if not result or point != result[-1]:
            result.append(point)
    if len(result) > 1 and result[0] == result[-1]:
        result.pop()
    return tuple(result)


def signed_area(polygon):
    return sum((_cross(a, b) for a, b in zip(polygon, polygon[1:]+polygon[:1])), F(0))/2


def _clip(polygon, normal, constant):
    result = []
    for a, b in zip(polygon, polygon[1:]+polygon[:1]):
        da = constant+sum(x*y for x, y in zip(normal, a))
        db = constant+sum(x*y for x, y in zip(normal, b))
        if da >= 0:
            result.append(a)
        if (da >= 0) != (db >= 0):
            result.append(tuple(x+(y-x)*da/(da-db) for x, y in zip(a, b)))
    return _clean(result)


def intersection(first, second):
    if signed_area(first) == 0 or signed_area(second) == 0:
        return ()
    sign = 1 if signed_area(second) > 0 else -1
    result = first
    for a, b in zip(second, second[1:]+second[:1]):
        edge = (b[0]-a[0], b[1]-a[1])
        normal = (-sign*edge[1], sign*edge[0])
        result = _clip(result, normal, -sum(x*y for x, y in zip(normal, a)))
        if len(result) < 3:
            return ()
    return result


def footprint_bounds(sweep, segments, time_root=None):
    if type(segments) is not int or not 1 <= segments <= 4096:
        raise ValueError('Bounded integer footprint segment count 1..4096 required')
    root = sweep.time_root if time_root is None else F(time_root)
    if root <= 0 or sweep.height_scale*root > sweep.bed_span or (
            sweep.gravity*sweep.height_scale*root*sum(x*x for x in sweep.delta) > sweep.jacobian**2):
        raise ValueError('Footprint closure cannot exceed original outward/edge branch bounds')
    end, time = sweep.height_scale*root/sweep.bed_span, root**3
    coefficient = (sweep.bed_span/sweep.height_scale)**3
    positions = [end*F(i, segments) for i in range(segments+1)]
    inner = _clean(((F(0), F(0)), (end, F(0)))+tuple(
        (s, time-coefficient*s**3) for s in reversed(positions)))
    outer = ((F(0), F(0)), (end, F(0)), (end, time), (F(0), time))
    for s in positions:
        outer = _clip(outer, (-3*coefficient*s*s, F(-1)), time+2*coefficient*s**3)
    def project(polygon):
        return tuple(tuple(sweep.edge[0][j]+s*sweep.delta[j]+age*sweep.velocity[j]
                           for j in range(2)) for s, age in polygon)
    return project(inner), project(outer)


def support_margin(sweep, point, time_root=None):
    offset = tuple(F(point[j])-sweep.edge[0][j] for j in range(2))
    determinant = _cross(sweep.delta, sweep.velocity)
    s = _cross(offset, sweep.velocity)/determinant
    age = _cross(sweep.delta, offset)/determinant
    root = sweep.time_root if time_root is None else F(time_root)
    return s, age, root**3-(sweep.bed_span*s/sweep.height_scale)**3-age


def overlap(first, second, *, domain=None, max_segments=128, closure_time_root=None):
    if closure_time_root is None and first.time_root != second.time_root:
        raise ValueError('Original streams must be evaluated at the SAME physical time')
    # The explicit endpoint closure only bounds earlier conditional footprints;
    # it does not take a physical step at an excluded branch equality.
    root = first.time_root if closure_time_root is None else F(closure_time_root)
    if type(max_segments) is not int or not 1 <= max_segments <= 4096:
        raise ValueError('Explicit bounded segment budget 1..4096 required')
    if domain is not None:
        domain = tuple(tuple(F(x) for x in point) for point in domain)
        if any(len(p) != 2 for p in domain) or signed_area(domain) == 0:
            raise ValueError('Positive convex exact domain required')
        sign = 1 if signed_area(domain) > 0 else -1
        for a, b in zip(domain, domain[1:]+domain[:1]):
            e = (b[0]-a[0], b[1]-a[1])
            if any(sign*_cross(e, (p[0]-a[0], p[1]-a[1])) < 0 for p in domain):
                raise ValueError('Positive convex exact domain required')
    segments = 1
    while True:
        a, b = footprint_bounds(first, segments, root), footprint_bounds(second, segments, root)
        low, high = intersection(a[0], b[0]), intersection(a[1], b[1])
        if domain is not None:
            low, high = intersection(low, domain), intersection(high, domain)
        lower, upper = abs(signed_area(low)), abs(signed_area(high))
        if lower > upper:
            raise ValueError('Inconsistent exact footprint bounds')
        status = 'positive-overlap' if lower > 0 else 'disjoint' if upper == 0 else 'unresolved'
        if status != 'unresolved' or segments == max_segments:
            break
        segments = min(2*segments, max_segments)
    witness = None
    witness_earlier_time = None
    if lower > 0:
        witness = tuple(sum((p[j] for p in low), F(0))/len(low) for j in range(2))
        margins = [support_margin(sweep, witness, root) for sweep in (first, second)]
        if any(min(margin) <= 0 for margin in margins):
            raise ValueError('Positive-area witness is not inside both original curved supports')
        witness_earlier_time = root**3-min(m[2] for m in margins)/2
    return dict(status=status, time_seconds=root**3, area_lower=lower, area_upper=upper,
                segments=segments, witness_xy=witness, physical_update_accepted=False,
                closure_bound_only=closure_time_root is not None,
                positive_witness_strictly_earlier_time=witness_earlier_time,
                scope='Same-time conditional footprint intersection only; not a merged state or pressure/time law.')


def simultaneous_pairs(records, *, domain=None, window_closure=False):
    """Pairwise common admissible times, retaining sub-float exact streams.

    Each pair uses the earlier ORIGINAL time root, never compares different
    clocks or extrapolates either stream beyond its existing geometry window.
    Pair-specific times are not one globally evolved multi-stream state.
    """
    if type(window_closure) is not bool:
        raise ValueError('Explicit boolean window-closure mode required')
    streams, unsupported = [], []
    for index, record in enumerate(records):
        if 'constant_inlet_velocity_mps' not in record:
            if record.get('status') == 'receding-or-fan-requires-coupled-front-law':
                unsupported.append(index)
                continue
            raise ValueError('Original conditional stream provenance is missing; cannot omit it')
        streams.append((index, InletSweep(record['original_inlet_xyz'], record['constant_inlet_velocity_mps'],
                                         record['primary_height_scale'], record['time_root'])))
    results = []
    for i, (first_index, first) in enumerate(streams):
        for second_index, second in streams[i+1:]:
            if window_closure:
                limits = [F(records[index]['original_isolated_geometry_time_root_limit'])
                          for index in (first_index, second_index)]
                if any(limit < stream.time_root for limit, stream in zip(limits, (first, second))):
                    raise ValueError('Original isolated window cannot precede its retained observation')
                root = min(limits)
                result = overlap(first, second, domain=domain, closure_time_root=root)
            else:
                root = min(first.time_root, second.time_root)
                result = overlap(replace(first, time_root=root), replace(second, time_root=root), domain=domain)
            results.append(dict(first_record=first_index, second_record=second_index, **result))
    return dict(pairs=results, represented_conditional_streams=len(streams), window_closure_bound_only=window_closure,
                unsupported_original_records=unsupported,
                counts={name: sum(r['status'] == name for r in results)
                        for name in ('positive-overlap', 'disjoint', 'unresolved')},
                all_pair_classifications_resolved=all(r['status'] != 'unresolved' for r in results),
                merged_state_or_force_or_time_or_gameplay_accepted=False)
