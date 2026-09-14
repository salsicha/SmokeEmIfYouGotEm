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
            intersection = a+(b-a)*(da/(da-db))
            # The computed intersection lies on this mathematical plane.
            # Assign it exactly so neighboring cells share the same face;
            # the original vertices and interpolated other coordinates stay.
            intersection[axis] = bound
            output.append(intersection)
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
        self.datum = float(self.levels.min())
        self.relative_levels = self.levels-self.datum
        self.area = float(self.areas.sum())
        a, b = triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0]
        determinant = a[:, 0]*b[:, 1]-a[:, 1]*b[:, 0]
        self.bed_gradients = np.stack(((a[:, 2]*b[:, 1]-b[:, 2]*a[:, 1])/determinant,
                                      (a[:, 0]*b[:, 2]-b[:, 0]*a[:, 2])/determinant), axis=1)

    def volume_and_wet_area(self, stage):
        """Integral of max(stage-bed,0) and strictly positive-depth wet area.

        Wet area is the stage derivative away from a flat triangle's dry level;
        at that nondifferentiable level it is the left derivative (zero).

        Below the middle vertex the submerged triangle scales by two edge
        fractions. Above it subtract the complementary dry triangle. Repeated
        vertex heights use only branches with nonzero denominators.
        """
        volume, wet = self._triangle_volume_and_wet_area(stage)
        return float(volume.sum()), float(wet.sum())

    def hydrostatic_bed_force(self, stage, gravity=9.81, relative=False):
        """Exact -g integral(depth * grad(bed)) over the original triangles.

        Units are m^4/s^2, consistent with integrated cell momentum V*u.
        No face-pressure residual is used to manufacture a rest balance.
        """
        if not np.isfinite(gravity) or gravity <= 0:
            raise ValueError('Positive finite gravity required')
        volume, _ = self._triangle_volume_and_wet_area(stage, self.relative_levels if relative else self.levels)
        return -gravity*np.sum(volume[:, None]*self.bed_gradients, axis=0)

    def _triangle_volume_and_wet_area(self, stage, levels=None):
        if not np.isfinite(stage):
            raise ValueError('Finite stage required')
        levels = self.levels if levels is None else levels
        a, b, c = levels.T
        volume, wet = np.zeros(len(a)), np.zeros(len(a))
        full = stage > a
        full &= stage >= c
        volume[full] = (stage-levels[full]).mean(axis=1)
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
        return self.areas*volume, self.areas*wet

    def relative_volume_and_wet_area(self, height):
        volume, wet = self._triangle_volume_and_wet_area(height, self.relative_levels)
        return float(volume.sum()), float(wet.sum())

    def relative_stage_for_volume(self, volume):
        """Return height ABOVE the cell minimum, never add its datum to physics.

        Scale the lower-interval bracket using its exact leading power. A
        fixed 128 halvings of a metre-sized interval cannot resolve 1e-100 m.
        No positive volume is replaced by zero or a minimum represented stage.
        """
        if not np.isfinite(volume) or volume < 0:
            raise ValueError('Finite nonnegative volume required')
        if volume == 0:
            return 0.
        levels = self.relative_levels
        positive = levels[levels > 0]
        ceiling = float(positive.min()) if positive.size else np.inf
        high = float(levels.max())+volume/self.area
        if not positive.size:
            height = volume/self.area
            if height == 0 or not np.isfinite(height):
                raise ValueError('Positive volume has no representable local stage')
            return height
        if volume <= self.relative_volume_and_wet_area(ceiling)[0]:
            a, b, c = levels.T
            at_minimum = a == 0
            flat = at_minimum & (c == 0)
            edge = at_minimum & (b == 0) & (c > 0)
            corner = at_minimum & (b > 0)
            leading = (float(self.areas[flat].sum()),
                       float(np.sum(self.areas[edge]/c[edge])),
                       float(np.sum(self.areas[corner]/(3*b[corner]*c[corner]))))
            power, coefficient = next((i+1, x) for i, x in enumerate(leading) if x > 0)
            # Logarithms avoid underflow before taking the root.
            high = min(ceiling, float(np.exp((np.log(volume)-np.log(coefficient))/power))*2)
            if high == 0:
                raise ValueError('Positive volume has no representable local stage')
            while self.relative_volume_and_wet_area(high)[0] < volume:
                if high == ceiling:
                    raise ValueError('Cannot bracket represented positive volume')
                high = min(ceiling, 2*high)
        low = 0.
        for _ in range(128):
            middle = (low+high)/2
            if middle == low or middle == high:
                break
            if self.relative_volume_and_wet_area(middle)[0] < volume:
                low = middle
            else:
                high = middle
        return (low+high)/2

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
