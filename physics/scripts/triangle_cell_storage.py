"""Exact hydrostatic storage on source triangles clipped to a Cartesian cell.

Geometry primitive for conservative subcell coupling, not an evolution solver.
No resampled bed, displaced vertex, depth floor, or global volume adjustment.
"""
import numpy as np


def clip_polygon(polygon, axis, bound, keep_greater):
    """Clip an XYZ polygon to one XY half-plane; interpolate full source edges."""
    output = []
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        da, db = a[axis]-bound, b[axis]-bound
        inside_a = da >= 0 if keep_greater else da <= 0
        inside_b = db >= 0 if keep_greater else db <= 0
        if inside_a:
            output.append(a)
        if inside_a != inside_b:
            output.append(a+(b-a)*(da/(da-db)))
    return np.asarray(output, float).reshape(-1, 3)


def cell_triangles(sampler, center, size):
    """Intersect the original registered mesh with a rectangular FV footprint.

    The bounded candidate search uses the same half-nominal-cell displacement
    guarantee enforced by RegisteredMeshSampler. Coverage must equal cell area;
    missing source is an error, never a clamped/fabricated bank.
    """
    center, size = np.asarray(center, float), np.asarray(size, float)
    if center.shape != (2,) or size.shape != (2,) or not np.isfinite([center, size]).all() or (size <= 0).any():
        raise ValueError('Finite cell center and positive XY size required')
    low, high = center-size/2, center+size/2
    c0 = int(np.floor((low[0]-sampler.east[0])/sampler.dx))-1
    c1 = int(np.floor((high[0]-sampler.east[0])/sampler.dx))+1
    r0 = int(np.floor((sampler.north[0]-high[1])/sampler.dy))-1
    r1 = int(np.floor((sampler.north[0]-low[1])/sampler.dy))+1
    output = []
    for row in range(max(0, r0), min(sampler.rows-2, r1)+1):
        for col in range(max(0, c0), min(sampler.cols-2, c1)+1):
            quad = row*(sampler.cols-1)+col
            for face in (quad, quad+sampler.quads):
                polygon = sampler.xyz[sampler.faces[face]].copy()
                # Translate XY first to avoid large-map-coordinate cancellation.
                polygon[:, :2] -= center
                for axis in (0, 1):
                    polygon = clip_polygon(polygon, axis, -size[axis]/2, True)
                    polygon = clip_polygon(polygon, axis, size[axis]/2, False)
                for index in range(1, len(polygon)-1):
                    output.append(polygon[[0, index, index+1]])
    triangles = np.asarray(output, float).reshape(-1, 3, 3)
    areas = projected_areas(triangles)
    triangles, areas = triangles[areas > 0], areas[areas > 0]
    if abs(areas.sum()-size.prod()) > 1e-9*size.prod():
        raise ValueError('Cell footprint not fully covered by original mesh')
    return triangles


def projected_areas(triangles):
    a, b = triangles[:, 1, :2]-triangles[:, 0, :2], triangles[:, 2, :2]-triangles[:, 0, :2]
    return abs(a[:, 0]*b[:, 1]-a[:, 1]*b[:, 0])/2


class TriangleCellStorage:
    def __init__(self, triangles):
        triangles = np.asarray(triangles, float)
        if triangles.ndim != 3 or triangles.shape[1:] != (3, 3) or not len(triangles) or not np.isfinite(triangles).all():
            raise ValueError('Finite nonempty XYZ triangles required')
        self.areas = projected_areas(triangles)
        if (self.areas <= 0).any():
            raise ValueError('Degenerate projected triangle')
        self.levels = np.sort(triangles[:, :, 2], axis=1)
        self.area = float(self.areas.sum())

    def volume_and_wet_area(self, stage):
        """Integral of max(stage-bed,0) and strictly positive-depth wet area.

        Wet area is the stage derivative away from a flat triangle's dry level;
        at that nondifferentiable level it is the left derivative (zero).

        Below the middle vertex the submerged triangle scales by two edge
        fractions. Above it subtract the complementary dry triangle. Repeated
        vertex heights use only branches with nonzero denominators.
        """
        if not np.isfinite(stage):
            raise ValueError('Finite stage required')
        a, b, c = self.levels.T
        volume, wet = np.zeros(len(a)), np.zeros(len(a))
        full = stage > a
        full &= stage >= c
        volume[full] = (stage-self.levels[full]).mean(axis=1)
        wet[full] = 1
        lower = (stage > a) & (stage <= b) & (stage < c)
        t = stage-a[lower]
        denominator = (b[lower]-a[lower])*(c[lower]-a[lower])
        volume[lower] = t**3/(3*denominator)
        wet[lower] = t**2/denominator
        upper = (stage > b) & (stage < c)
        # Expand from b using positive terms, not full signed volume plus a
        # complementary dry volume: that subtraction loses shallow water when
        # a == b and eta is tiny compared with the upper vertex elevation.
        t = stage-b[upper]
        span, remaining = c[upper]-a[upper], c[upper]-b[upper]
        lower_span = b[upper]-a[upper]
        volume[upper] = (lower_span**2/3+t*lower_span+t*t*(1-t/(3*remaining)))/span
        wet[upper] = (lower_span+t*(2-t/remaining))/span
        return float(self.areas@volume), float(self.areas@wet)

    def stage_for_volume(self, volume):
        """Invert the monotone local storage relation; zero volume stays dry."""
        if not np.isfinite(volume) or volume < 0:
            raise ValueError('Finite nonnegative volume required')
        low = float(self.levels.min())
        if volume == 0:
            return low
        high = float(self.levels.max())+volume/self.area
        for _ in range(128):
            middle = (low+high)/2
            if middle == low or middle == high:
                break
            if self.volume_and_wet_area(middle)[0] < volume:
                low = middle
            else:
                high = middle
        return (low+high)/2
