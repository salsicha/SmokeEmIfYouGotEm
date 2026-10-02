"""Open volumes/moments of actual boxes and one piecewise-linear roof extrusion.

Integrates the solid UNION, directly accumulating open intervals rather than
subtracting a nearly full solid volume. Metric geometry only, not particle mass.
This laboratory representation does not approximate arbitrary meshes as boxes.
"""
import numpy as np


def physical_box(lower, upper):
    lo, hi = np.asarray(lower, float), np.asarray(upper, float)
    if lo.shape != (3,) or hi.shape != (3,) or not np.isfinite([lo, hi]).all() or np.any(hi <= lo):
        raise ValueError('Finite positive physical box required')
    return lo, hi


def open_intervals(blocked, lower, upper):
    """Exact represented interval union, including joint full coverage."""
    result = []; cursor = lower
    for a, b in sorted((max(a, lower), min(b, upper)) for a, b in blocked if b > lower and a < upper):
        if a > cursor:
            result.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < upper:
        result.append((cursor, upper))
    return result


class ExtrudedSolidVolume:
    def __init__(self, boxes, profile=None):
        self.boxes = [physical_box(a, b) for a, b in boxes]
        self.profile = None
        if profile is not None:
            xs, roof, lower, upper = profile
            lo, hi = physical_box(lower, upper); xs, roof = np.asarray(xs, float), np.asarray(roof, float)
            if (xs.ndim != 1 or len(xs) < 2 or roof.shape != xs.shape or not np.isfinite([xs, roof]).all()
                    or np.any(np.diff(xs) <= 0) or xs[0] != lo[0] or xs[-1] != hi[0]
                    or np.any(roof <= lo[2]) or roof.max() != hi[2]):
                raise ValueError('Complete finite actual roof extrusion required')
            self.profile = (xs, roof, lo, hi)

    def contains(self, points):
        p = np.asarray(points, float)
        if p.shape[-1] != 3 or not np.isfinite(p).all():
            raise ValueError('Finite world points required')
        solid = np.zeros(p.shape[:-1], bool)
        for lo, hi in self.boxes:
            solid |= np.all((p >= lo) & (p <= hi), axis=-1)
        if self.profile is not None:
            xs, roof, lo, hi = self.profile
            top = np.interp(p[..., 0], xs, roof)
            solid |= (np.all((p[..., :2] >= lo[:2]) & (p[..., :2] <= hi[:2]), axis=-1)
                      & (p[..., 2] >= lo[2]) & (p[..., 2] <= top))
        return solid

    @staticmethod
    def _strip(a, b, lower, upper, roof=None):
        """Integrals of open z length, x*length and vertical first moment."""
        if roof is None or max(roof) <= lower:
            length = upper-lower; volume = (b-a)*length
            return np.array([volume, volume*(a+b)/2, volume*(lower+upper)/2])
        if min(roof) >= upper:
            return np.zeros(3)
        ra, rb = roof; events = [a, b]
        if rb != ra:
            for height in (lower, upper):
                u = (height-ra)/(rb-ra)
                if 0 < u < 1:
                    events.append(a+(b-a)*u)
        result = np.zeros(3)
        for x0, x1 in zip(sorted(set(events)), sorted(set(events))[1:]):
            if x1 <= x0:
                continue
            # Three-point quadrature is exact for each polynomial branch.
            # Endpoint interpolation uses normalized source coordinates, not
            # a fitted intercept that can cancel a tiny represented opening.
            q = np.array([x0, x0+(x1-x0)/2, x1])
            r = ra+(rb-ra)*((q-a)/(b-a))
            bottom = np.minimum(upper, np.maximum(lower, r)); length = upper-bottom
            weights = np.array([1., 4., 1.])*(x1-x0)/6
            result += np.array([weights@length, weights@(q*length),
                                weights@(length*(upper+bottom)/2)])
        return result

    def integrate(self, lower, upper):
        """Return open volume m3 and first moment m4 in one arbitrary box."""
        lo, hi = physical_box(lower, upper)
        boxes = [(a, b) for a, b in self.boxes if np.all(b > lo) and np.all(a < hi)]
        profile = self.profile
        if profile is not None and not (np.all(profile[3] > lo) and np.all(profile[2] < hi)):
            profile = None
        if not boxes and profile is None:
            volume = float(np.prod(hi-lo))
            return volume, volume*(lo+hi)/2
        events = [{lo[a], hi[a]} for a in range(2)]
        for lower_box, upper_box in boxes:
            for axis in range(2):
                events[axis].update(x for x in (lower_box[axis], upper_box[axis]) if lo[axis] < x < hi[axis])
        if profile is not None:
            xs, roof, bedlo, bedhi = profile
            events[0].update(x for x in xs if lo[0] < x < hi[0])
            events[1].update(y for y in (bedlo[1], bedhi[1]) if lo[1] < y < hi[1])
        ex, ey = map(sorted, events); volume = 0.; moment = np.zeros(3)
        for a, b in zip(ex, ex[1:]):
            for c, d in zip(ey, ey[1:]):
                # Interval inclusion avoids midpoint rounding across adjacent
                # representable events. No epsilon welding or radius offset.
                blocked = [(lower_box[2], upper_box[2]) for lower_box, upper_box in boxes
                           if lower_box[0] <= a and upper_box[0] >= b
                           and lower_box[1] <= c and upper_box[1] >= d]
                bed = (profile is not None and bedlo[0] <= a and bedhi[0] >= b
                       and bedlo[1] <= c and bedhi[1] >= d)
                top = np.interp([a, b], xs, roof) if bed else None
                for z0, z1 in open_intervals(blocked, lo[2], hi[2]):
                    portions = [(z0, z1, None)]
                    if bed and z1 > bedlo[2]:
                        portions = []
                        if z0 < bedlo[2]:
                            portions.append((z0, bedlo[2], None))
                        portions.append((max(z0, bedlo[2]), z1, top))
                    for z0, z1, r in portions:
                        v, mx, mz = self._strip(a, b, z0, z1, r)
                        volume += (d-c)*v
                        moment += (d-c)*np.array([mx, v*(c+d)/2, mz])
        return float(volume), moment


def sample_phi(phi, points, origin, cell_m):
    """Cached center-field trilinear interpolation, constant outer half cells."""
    field = np.asarray(phi); p = np.asarray(points, float)
    c = (p-np.asarray(origin))/cell_m-.5
    c = np.minimum(np.array(field.shape)-1, np.maximum(0., c))
    base = np.floor(c).astype(int); upper = np.minimum(base+1, np.array(field.shape)-1); t = c-base
    result = np.zeros(p.shape[:-1])
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                bit = np.array([i, j, k]); ids = np.where(bit, upper, base)
                result += np.prod(np.where(bit, t, 1-t), axis=-1)*field[ids[..., 0], ids[..., 1], ids[..., 2]]
    return result


def liquid_volume_bounds(geometry, phi, origin, cell_m, lower, upper, depth=3, sign_guard=1e-12):
    """Bound reconstructed liquid intersected with exact authored solids.

    Split at all cached-center planes so each box has one multilinear phi.
    Its corner extrema classify liquid/dry; uncertain boxes are refined.
    Geometric open volume, not voxel occupancy, weights every subbox.
    This is a floating-point sign-guard bound, not an interval-arithmetic proof
    of unknown physical liquid or conserved particle mass.
    """
    lo, hi = physical_box(lower, upper); phi = np.asarray(phi, float); origin = np.asarray(origin, float)
    if (phi.ndim != 3 or min(phi.shape) < 2 or not np.isfinite(phi).all() or origin.shape != (3,)
            or not np.isfinite(origin).all() or not np.isfinite(cell_m) or cell_m <= 0
            or not isinstance(depth, int) or depth < 0 or sign_guard < 0 or not np.isfinite(sign_guard)
            or np.any(lo < origin) or np.any(hi > origin+np.array(phi.shape)*cell_m)):
        raise ValueError('Finite cached lattice, contained region and nonnegative refinement required')
    bits = np.array([(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)])
    breaks = []
    for a in range(3):
        centers = origin[a]+(np.arange(phi.shape[a])+.5)*cell_m
        breaks.append(sorted({lo[a], hi[a], *centers[(centers > lo[a]) & (centers < hi[a])]}))
    lower_sum = upper_sum = 0.; visited = uncertain = 0
    stack = [(np.array([x, y, z]), np.array([xx, yy, zz]), 0)
             for x, xx in zip(breaks[0], breaks[0][1:])
             for y, yy in zip(breaks[1], breaks[1][1:])
             for z, zz in zip(breaks[2], breaks[2][1:])]
    while stack:
        a, b, level = stack.pop(); visited += 1; volume, _ = geometry.integrate(a, b)
        if volume == 0:
            continue
        values = sample_phi(phi, np.where(bits, b, a), origin, cell_m)
        if values.max() < -sign_guard:
            lower_sum += volume; upper_sum += volume
        elif values.min() > sign_guard:
            continue
        elif level == depth:
            upper_sum += volume; uncertain += 1
        else:
            mid = a+(b-a)/2
            if np.any((mid == a) | (mid == b)):
                upper_sum += volume; uncertain += 1
                continue
            stack.extend((np.where(bit, mid, a), np.where(bit, b, mid), level+1) for bit in bits)
    return dict(lower_m3=float(lower_sum), upper_m3=float(upper_sum), width_m3=float(upper_sum-lower_sum),
                depth=depth, visited_boxes=visited, uncertain_boxes=uncertain, sign_guard=sign_guard,
                scope='Cached multilinear liquid intersected with actual laboratory solids, not conserved mass')
