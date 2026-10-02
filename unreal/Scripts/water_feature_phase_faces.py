"""Shared actual-solid open area and bounded cached-liquid area on physical faces.

Laboratory box/roof representation; no arbitrary mesh bounding-box surrogate.
Open interval union is integrated directly, preserving actual small openings.
"""
import numpy as np
from water_feature_extruded_volume import open_intervals, sample_phi


class PhaseFaces:
    def __init__(self, geometry):
        self.geometry = geometry; self.cache = {}

    def pieces(self, axis, plane):
        key = (axis, float(plane))
        if key in self.cache:
            return self.cache[key]
        others = [a for a in range(3) if a != axis]; pieces = []
        # Each piece is horizontal interval, vertical lower bound and endpoint
        # roof heights. Relative interpolation avoids a cancelling intercept.
        for lo, hi in self.geometry.boxes:
            if lo[axis] <= plane <= hi[axis]:
                pieces.append((lo[others[0]], hi[others[0]], lo[others[1]], hi[others[1]], hi[others[1]]))
        if self.geometry.profile is not None:
            xs, roof, lo, hi = self.geometry.profile
            if lo[axis] <= plane <= hi[axis]:
                if axis == 0:
                    top = float(np.interp(plane, xs, roof)); pieces.append((lo[1], hi[1], lo[2], top, top))
                else:
                    for a, b, c, d in zip(xs, xs[1:], roof, roof[1:]):
                        if axis == 1:
                            pieces.append((a, b, lo[2], c, d))
                        elif max(c, d) >= plane:
                            if min(c, d) < plane:
                                crossing = a+(plane-c)*(b-a)/(d-c)
                                if c < plane:
                                    a = crossing
                                else:
                                    b = crossing
                            if b > a:
                                pieces.append((a, b, lo[1], hi[1], hi[1]))
        self.cache[key] = pieces
        return pieces

    @staticmethod
    def top(piece, x):
        a, b, _, c, d = piece
        return c+(d-c)*((x-a)/(b-a))

    def area(self, axis, plane, lower, upper):
        lo, hi = np.asarray(lower, float), np.asarray(upper, float)
        if (axis not in (0, 1, 2) or lo.shape != (2,) or hi.shape != (2,)
                or not np.isfinite([lo, hi]).all() or not np.isfinite(plane) or np.any(hi <= lo)):
            raise ValueError('Finite positive physical face required')
        pieces = [p for p in self.pieces(axis, plane) if p[1] > lo[0] and p[0] < hi[0]
                  and p[2] < hi[1] and max(p[3:]) > lo[1]]
        if not pieces:
            return float(np.prod(hi-lo))
        events = {lo[0], hi[0]}; levels = {lo[1], hi[1], *[p[2] for p in pieces]}
        for p in pieces:
            a, b = max(lo[0], p[0]), min(hi[0], p[1]); events.update((a, b))
            ya, yb = self.top(p, a), self.top(p, b)
            if ya != yb:
                for level in levels:
                    u = (level-ya)/(yb-ya)
                    if 0 < u < 1:
                        events.add(a+(b-a)*u)
        for i, p in enumerate(pieces):
            for q in pieces[i+1:]:
                a, b = max(lo[0], p[0], q[0]), min(hi[0], p[1], q[1])
                if b <= a:
                    continue
                ya, yb = self.top(p, a)-self.top(q, a), self.top(p, b)-self.top(q, b)
                if ya != yb:
                    u = -ya/(yb-ya)
                    if 0 < u < 1:
                        events.add(a+(b-a)*u)
        events = sorted(events); area = 0.
        for a, b in zip(events, events[1:]):
            active = [p for p in pieces if p[0] <= a and p[1] >= b]
            # All union topology events were split: open length is affine.
            lengths = [sum(d-c for c, d in open_intervals([(p[2], self.top(p, x)) for p in active], lo[1], hi[1]))
                       for x in (a, b)]
            area += (b-a)*sum(lengths)/2
        return float(area)


def liquid_face_bounds(faces, phi, origin, h, axis, plane, lower, upper, depth=2, guard=1e-12):
    """Guarded bounds for cached bilinear face liquid intersected with actual solids.

    Split at center planes, not a fitted flat interface or area-fraction cutoff.
    Uncertainty stays explicit. These do not prove physical liquid accuracy.
    """
    lo, hi = np.asarray(lower, float), np.asarray(upper, float); origin = np.asarray(origin, float)
    if (axis not in (0, 1, 2) or lo.shape != (2,) or hi.shape != (2,) or np.any(hi <= lo)
            or not np.isfinite([lo, hi]).all() or not np.isfinite(plane)
            or not isinstance(depth, int) or depth < 0 or not np.isfinite(guard) or guard < 0):
        raise ValueError('Finite face and nonnegative refinement/sign guard required')
    others = [a for a in range(3) if a != axis]; bits = np.array([(0, 0), (0, 1), (1, 0), (1, 1)])
    events = []
    for a, world_axis in enumerate(others):
        centers = origin[world_axis]+(np.arange(phi.shape[world_axis])+.5)*h
        events.append(sorted({lo[a], hi[a], *centers[(centers > lo[a]) & (centers < hi[a])]}))
    pending = [(np.array([a, c]), np.array([b, d]), 0)
               for a, b in zip(events[0], events[0][1:]) for c, d in zip(events[1], events[1][1:])]
    lower_sum = upper_sum = 0.; uncertain = visited = 0
    while pending:
        a, b, level = pending.pop(); visited += 1; area = faces.area(axis, plane, a, b)
        if area == 0:
            continue
        points = np.empty((4, 3)); points[:, axis] = plane; points[:, others] = np.where(bits, b, a)
        values = sample_phi(phi, points, origin, h)
        if values.max() < -guard:
            lower_sum += area; upper_sum += area
        elif values.min() > guard:
            continue
        elif level == depth:
            upper_sum += area; uncertain += 1
        else:
            mid = a+(b-a)/2
            if np.any((mid == a) | (mid == b)):
                upper_sum += area; uncertain += 1
            else:
                pending.extend((np.where(bit, mid, a), np.where(bit, b, mid), level+1) for bit in bits)
    return dict(lower_m2=float(lower_sum), upper_m2=float(upper_sum), width_m2=float(upper_sum-lower_sum),
                depth=depth, visited_patches=visited, uncertain_patches=uncertain, sign_guard=guard)
