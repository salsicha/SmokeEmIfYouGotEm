"""Source-clipped geometry of a conditional, constant-velocity inlet sweep.

The inlet depth is k*t**(1/3)-B*s, with s the ORIGINAL edge fraction.
Entry time is r**3. At time R**3 a parcel is at A+s*D+u*(R**3-r**3).
This is the leading outward advective geometry, not a shallow-water or
rational-pressure time integrator. In particular a fan is NOT advected with
a guessed constant speed. No receiving-source minimum is used to place water.

All geometry and integration bounds are rational in represented source data.
Unresolved polynomial switches have explicit measure bounds, never deleted
slivers. Exact arithmetic is not additional surveyed precision.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from math import comb

from subcell_exact_geometry import SourceFragment, clip


def _add(a, b):
    return tuple((a[i] if i < len(a) else F(0))+(b[i] if i < len(b) else F(0))
                 for i in range(max(len(a), len(b))))


def _scale(a, factor):
    return tuple(x*factor for x in a)


def _mul(a, b):
    result = [F(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i+j] += x*y
    return tuple(result)


def _power(a, n):
    result = (F(1),)
    for _ in range(n):
        result = _mul(result, a)
    return result


def _value(a, x):
    result = F(0)
    for c in reversed(a):
        result = result*x+c
    return result


def _integral(a, lo, hi):
    return sum((c*(hi**(i+1)-lo**(i+1))/(i+1) for i, c in enumerate(a)), F(0))


def polynomial_bounds(a, lo, hi):
    """Exact Bernstein convex-hull bound on a rational interval."""
    n = len(a)-1
    shifted = [sum((a[i]*comb(i, j)*lo**(i-j)*(hi-lo)**j
                    for i in range(j, n+1)), F(0)) for j in range(n+1)]
    controls = [sum((shifted[j]*F(comb(i, j), comb(n, j))
                     for j in range(i+1)), F(0)) for i in range(n+1)]
    return min(controls), max(controls)


def _cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def shared_inlet_edge(first, second):
    """Recover a shared original boundary without rounded XYZ face exports."""
    matches = set()
    for a, b in zip(first.polygon, first.polygon[1:]+first.polygon[:1]):
        delta = tuple(y-x for x, y in zip(a, b))
        axis = 0 if abs(delta[0]) >= abs(delta[1]) else 1
        if delta[axis] == 0:
            continue
        for c, d in zip(second.polygon, second.polygon[1:]+second.polygon[:1]):
            if any(_cross(delta, (p[0]-a[0], p[1]-a[1])) != 0 for p in (c, d)):
                continue
            parameters = [(p[axis]-a[axis])/delta[axis] for p in (c, d)]
            low, high = max(F(0), min(parameters)), min(F(1), max(parameters))
            if low >= high:
                continue
            if any(a[2]+t*delta[2] != p[2] for p, t in zip((c, d), parameters)):
                raise ValueError('Original shared boundary bed elevations disagree')
            endpoints = tuple(tuple(x+t*y for x, y in zip(a, delta)) for t in (low, high))
            matches.add(tuple(sorted(endpoints)))
    if len(matches) != 1:
        raise ValueError('One positive original shared boundary required; point contact is insufficient')
    return next(iter(matches))


@dataclass(frozen=True)
class InletSweep:
    """One non-overlapping inlet stream; all coordinates share one XY frame.

    Callers must route EVERY source-clipped part and retain out-of-domain
    mass. Multiple sweeps cannot be superposed as separate physical water
    without resolving overlaps and their momentum/pressure interactions.
    """
    edge: tuple
    velocity: tuple
    height_scale: F
    time_root: F
    gravity: F = F(9.81)

    def __post_init__(self):
        if len(self.edge) != 2 or any(len(p) != 3 for p in self.edge) or len(self.velocity) != 2:
            raise ValueError('Two original XYZ endpoints and an XY velocity required')
        edge = tuple(tuple(F(x) for x in p) for p in self.edge)
        edge = tuple(sorted(edge, key=lambda p: p[2]))
        object.__setattr__(self, 'edge', edge)
        object.__setattr__(self, 'velocity', tuple(F(x) for x in self.velocity))
        for name in ('height_scale', 'time_root', 'gravity'):
            object.__setattr__(self, name, F(getattr(self, name)))
        if min(self.height_scale, self.time_root, self.gravity, self.bed_span) <= 0:
            raise ValueError('Positive original sloping inlet, scale, time and gravity required')
        if self.jacobian == 0:
            raise ValueError('Nonzero transverse inlet velocity required')
        if self.height_scale*self.time_root >= self.bed_span:
            raise ValueError('Inlet sweep reaches the original positive edge knot')
        length_squared = sum(x*x for x in self.delta)
        if self.gravity*self.height_scale*self.time_root*length_squared >= self.jacobian**2:
            raise ValueError('Constant-velocity sweep does not cover the original fan branch')

    @property
    def delta(self):
        return tuple(self.edge[1][j]-self.edge[0][j] for j in range(2))

    @property
    def bed_span(self):
        return self.edge[1][2]-self.edge[0][2]

    @property
    def jacobian(self):
        return abs(_cross(self.delta, self.velocity))

    def point(self, r, s):
        """Exact XY and depth, not a minimum-centered hydrostatic stage."""
        r, s = F(r), F(s)
        if not 0 <= r <= self.time_root or not 0 <= s <= self.height_scale*r/self.bed_span:
            raise ValueError('Point lies outside inlet entry-time/depth support')
        xy = tuple(self.edge[0][j]+s*self.delta[j]
                   +self.velocity[j]*(self.time_root**3-r**3) for j in range(2))
        return xy, self.height_scale*r-self.bed_span*s

    def validate_receiver(self, fragment):
        """Reject a reversed inlet velocity instead of reflecting its water."""
        found = False
        for a, b in zip(fragment.polygon, fragment.polygon[1:]+fragment.polygon[:1]):
            delta = tuple(y-x for x, y in zip(a, b))
            axis = 0 if abs(delta[0]) >= abs(delta[1]) else 1
            if delta[axis] == 0:
                continue
            parameters = [(p[axis]-a[axis])/delta[axis] for p in self.edge]
            if all(0 <= t <= 1 and all(a[j]+t*delta[j] == p[j] for j in range(3))
                   for p, t in zip(self.edge, parameters)):
                found = True
        if not found:
            raise ValueError('Sweep inlet must be an original receiving boundary')
        side = sum((_cross(self.delta, (p[0]-self.edge[0][0], p[1]-self.edge[0][1]))
                    for p in fragment.polygon), F(0))
        if side*_cross(self.delta, self.velocity) <= 0:
            raise ValueError('Inlet velocity does not enter the original receiver')

    def full_moment(self, power, lo=F(0), hi=None):
        if power not in range(4):
            raise ValueError('Depth moment power must be 0..3')
        lo, hi = F(lo), self.time_root if hi is None else F(hi)
        if not 0 <= lo <= hi <= self.time_root:
            raise ValueError('Entry-time interval is outside sweep')
        return (3*self.jacobian*self.height_scale**(power+1)
                *(hi**(power+4)-lo**(power+4))/(self.bed_span*(power+1)*(power+4)))

    def _constraints(self, fragment):
        if not isinstance(fragment, SourceFragment) or fragment.area <= 0:
            raise ValueError('Positive exact original source fragment required')
        polygon = fragment.polygon
        orientation = sum((_cross(a, b) for a, b in zip(polygon, polygon[1:]+polygon[:1])), F(0))
        if orientation == 0:
            raise ValueError('Degenerate original polygon')
        sign = 1 if orientation > 0 else -1
        lower, upper, vertical = [(F(0),)], [(F(0), self.height_scale/self.bed_span)], []
        for a, b in zip(polygon, polygon[1:]+polygon[:1]):
            e = (b[0]-a[0], b[1]-a[1])
            if any(sign*_cross(e, (p[0]-a[0], p[1]-a[1])) < 0 for p in polygon):
                raise ValueError('Convex original source polygon required')
            coefficient = sign*_cross(e, self.delta)
            start = tuple(self.edge[0][j]+self.velocity[j]*self.time_root**3-a[j] for j in range(2))
            polynomial = (sign*_cross(e, start), F(0), F(0), -sign*_cross(e, self.velocity))
            if coefficient > 0:
                lower.append(_scale(polynomial, -1/coefficient))
            elif coefficient < 0:
                upper.append(_scale(polynomial, -1/coefficient))
            else:
                vertical.append(polynomial)
        return lower, upper, vertical

    def moments(self, fragment, relative_bound=F(1, 10**12), max_depth=48):
        """Certified bounds for integrals h**0..3 on this ORIGINAL source.

        Stable envelope intervals integrate exactly. Each unresolved switch
        contributes [0, full-strip integral on that interval]. Bounds must
        meet the requested fraction of each incoming moment or this raises.
        This does not normalize fragment totals to hide lost/overlapping water.
        """
        relative_bound = F(relative_bound)
        if not 0 < relative_bound < 1 or not isinstance(max_depth, int) or not 1 <= max_depth <= 128:
            raise ValueError('Strict relative integration bound and depth 1..128 required')
        lower, upper, vertical = self._constraints(fragment)
        exact, uncertainty = [F(0)]*4, [F(0)]*4
        pending = [(F(0), self.time_root, 0)]
        visited, switches = 0, 0
        while pending:
            lo, hi, depth = pending.pop()
            visited += 1
            middle = (lo+hi)/2
            low = max(lower, key=lambda p: _value(p, middle))
            high = min(upper, key=lambda p: _value(p, middle))
            width = _add(high, _scale(low, -1))
            vertical_ranges = [polynomial_bounds(p, lo, hi) for p in vertical]
            if any(b < 0 for a, b in vertical_ranges) or polynomial_bounds(width, lo, hi)[1] <= 0:
                continue
            stable = (all(a >= 0 for a, b in vertical_ranges)
                and polynomial_bounds(width, lo, hi)[0] >= 0
                and all(polynomial_bounds(_add(low, _scale(p, -1)), lo, hi)[0] >= 0 for p in lower)
                and all(polynomial_bounds(_add(p, _scale(high, -1)), lo, hi)[0] >= 0 for p in upper))
            if stable:
                hlow = _add((F(0), self.height_scale), _scale(low, -self.bed_span))
                hhigh = _add((F(0), self.height_scale), _scale(high, -self.bed_span))
                for power in range(4):
                    polynomial = _add(_power(hlow, power+1), _scale(_power(hhigh, power+1), -1))
                    value = _integral((F(0), F(0))+polynomial, lo, hi)*3*self.jacobian/(self.bed_span*(power+1))
                    if value < 0:
                        raise ValueError('Negative certified source moment')
                    exact[power] += value
            elif depth == max_depth:
                switches += 1
                for power in range(4):
                    uncertainty[power] += self.full_moment(power, lo, hi)
            else:
                pending.extend(((lo, middle, depth+1), (middle, hi, depth+1)))
        if any(uncertainty[p] > relative_bound*self.full_moment(p) for p in range(4)):
            raise ValueError('Source clipping integration bound unresolved; no sliver deletion')
        return dict(source_id=fragment.source_id,
                    lower=tuple(exact), upper=tuple(x+y for x, y in zip(exact, uncertainty)),
                    intervals_visited=visited, bounded_switch_intervals=switches,
                    full_force_or_time_or_native_or_gameplay_accepted=False)

    def initial_wet_support_moments(self, fragment, stage_offset, datum,
                                    relative_bound=F(1, 10**12), max_depth=48):
        """Partition incoming moments by the ORIGINAL hydrostatic wet support.

        Owning a source triangle does not make its entire footprint wet. Clip
        the original bed polygon at datum+offset BEFORE any float conversion.
        These are moments of incoming depth, not existing-pool depth, and not
        a merged physical state. Both disjoint portions and uncertainty remain.
        """
        whole = self.moments(fragment, relative_bound, max_depth)
        try:
            surface = F(datum)+F(stage_offset)
        except (ValueError, TypeError, OverflowError, ZeroDivisionError) as exc:
            raise ValueError('Finite exact original stage offset and datum required') from exc
        levels = [p[2] for p in fragment.polygon]
        zero = dict(source_id=fragment.source_id, lower=(F(0),)*4, upper=(F(0),)*4,
                    intervals_visited=0, bounded_switch_intervals=0,
                    full_force_or_time_or_native_or_gameplay_accepted=False)
        if surface <= min(levels):
            wet, dry = zero, whole
        elif surface >= max(levels):
            wet, dry = whole, zero
        else:
            parts = [SourceFragment(fragment.source_id, clip(fragment.polygon, 2, surface, greater),
                                    fragment.gradient) for greater in (False, True)]
            wet, dry = [self.moments(part, relative_bound, max_depth) if part.area > 0 else zero
                        for part in parts]
        # The common shoreline has zero projected area, except a constant-bed
        # polygon at exactly its stage, handled as strictly dry above.
        for p in range(4):
            lower = wet['lower'][p]+dry['lower'][p]
            upper = wet['upper'][p]+dry['upper'][p]
            if lower > whole['upper'][p] or upper < whole['lower'][p]:
                raise ValueError('Wet/dry support partition violates original incoming moments')
        return dict(source_id=fragment.source_id, original_stage=surface,
                    original_source_moments=whole, on_initial_wet_support=wet,
                    on_initial_dry_support=dry,
                    positive_initial_wet_overlap_proven=wet['lower'][1] > 0,
                    positive_initial_wet_overlap_possible=wet['upper'][1] > 0,
                    merged_state_or_force_or_time_or_gameplay_accepted=False)
