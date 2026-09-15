"""Original-source clipping and integrals without a float-vertex round trip.

This reference representation retains every positive rational fragment, even
when its float XYZ projection is degenerate. It is not yet the evolving pool
storage/face API. Coordinates are exact rationals of the supplied binary data,
not claims of additional measurement precision.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math

import numpy as np

from triangle_cell_storage import TriangleCellStorage


def clip(vertices, axis, bound, greater):
    output = []
    for a, b in zip(vertices, vertices[1:]+vertices[:1]):
        da, db = a[axis]-bound, b[axis]-bound
        inside_a, inside_b = (da >= 0, db >= 0) if greater else (da <= 0, db <= 0)
        if inside_a:
            output.append(a)
        if inside_a != inside_b:
            output.append(tuple(x+(y-x)*da/(da-db) for x, y in zip(a, b)))
    # Only exact duplicate vertices are removed; no distance tolerance.
    result = []
    for point in output:
        if not result or point != result[-1]:
            result.append(point)
    if len(result) > 1 and result[0] == result[-1]:
        result.pop()
    return tuple(result)


def area(triangle):
    a, b, c = triangle
    return abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2


def triangulate(polygon):
    return tuple(t for i in range(1, len(polygon)-1)
                 if area(t := (polygon[0], polygon[i], polygon[i+1])) > 0)


@dataclass(frozen=True)
class SourceFragment:
    source_id: int
    polygon: tuple
    gradient: tuple

    @property
    def triangles(self):
        return triangulate(self.polygon)

    @property
    def area(self):
        return sum(map(area, self.triangles), F(0))

    def face(self, axis, coordinate):
        points = sorted(set((v[1-axis], v[2]) for v in self.polygon if v[axis] == coordinate))
        return (points[0], points[-1]) if len(points) >= 2 and points[0][0] < points[-1][0] else None

    def depth_moments(self, stage):
        """Exact integrals of h**0..3 on strictly wet original geometry."""
        stage = F(stage)
        if not self.polygon or stage <= min(v[2] for v in self.polygon):
            return (F(0),)*4
        wet = triangulate(clip(self.polygon, 2, stage, False))
        result = [F(0)]*4
        for triangle in wet:
            h = [stage-v[2] for v in triangle]
            for power in range(4):
                polynomial = sum((h[0]**i*h[1]**j*h[2]**(power-i-j)
                                  for i in range(power+1) for j in range(power+1-i)), F(0))
                result[power] += 2*area(triangle)*polynomial/((power+1)*(power+2))
        return tuple(result)


def source_fragment(triangle, center, spacing, source_id):
    triangle = np.asarray(triangle, float)
    center, spacing = np.asarray(center, float), np.asarray(spacing, float)
    if (triangle.shape != (3, 3) or center.shape != (2,) or spacing.shape != (2,)
            or not all(np.isfinite(x).all() for x in (triangle, center, spacing)) or (spacing <= 0).any()):
        raise ValueError('Finite original triangle, center and positive spacing required')
    origin = tuple(map(F, map(float, center)))
    half = tuple(F(float(x))/2 for x in spacing)
    xyz = tuple(tuple(F(float(x))-(origin[j] if j < 2 else 0) for j, x in enumerate(v)) for v in triangle)
    a, b = (tuple(x-y for x, y in zip(v, xyz[0])) for v in xyz[1:])
    determinant = a[0]*b[1]-a[1]*b[0]
    if determinant == 0:
        raise ValueError('Degenerate original source triangle')
    gradient = ((a[2]*b[1]-b[2]*a[1])/determinant, (a[0]*b[2]-b[0]*a[2])/determinant)
    polygon = xyz
    for axis in (0, 1):
        polygon = clip(polygon, axis, -half[axis], True)
        polygon = clip(polygon, axis, half[axis], False)
    fragment = SourceFragment(int(source_id), polygon, gradient)
    return fragment if fragment.area > 0 else None


def cell_fragments(sampler, center, spacing):
    """Bounded original-mesh search; require exact full projected coverage."""
    center, spacing = np.asarray(center, float), np.asarray(spacing, float)
    if (center.shape != (2,) or spacing.shape != (2,) or not np.isfinite([center, spacing]).all()
            or (spacing <= 0).any()):
        raise ValueError('Finite cell center and positive spacing required')
    low, high = center-spacing/2, center+spacing/2
    c0 = math.floor((low[0]-sampler.east[0])/sampler.dx)-1
    c1 = math.floor((high[0]-sampler.east[0])/sampler.dx)+1
    r0 = math.floor((sampler.north[0]-high[1])/sampler.dy)-1
    r1 = math.floor((sampler.north[0]-low[1])/sampler.dy)+1
    result = []
    for row in range(max(0, r0), min(sampler.rows-2, r1)+1):
        for col in range(max(0, c0), min(sampler.cols-2, c1)+1):
            quad = row*(sampler.cols-1)+col
            for source in (quad, quad+sampler.quads):
                fragment = source_fragment(sampler.xyz[sampler.faces[source]], center, spacing, source)
                if fragment is not None:
                    result.append(fragment)
    if sum((f.area for f in result), F(0)) != F(float(spacing[0]))*F(float(spacing[1])):
        raise ValueError('Original mesh does not exactly cover the requested footprint')
    return tuple(result)


class SourceRelativeStorage(TriangleCellStorage):
    """Local hydrostatic/kinetic metrics derived before coordinate rounding.

    The numerical storage datum is zero. Its actual elevation is retained as
    ``source_datum`` (a Fraction); face consumers must subtract that exact datum
    BEFORE converting their relative heights. This is deliberately not a drop-in
    replacement for pool code that currently adds/subtracts float datums.
    """
    def __init__(self, fragments):
        self.fragments = tuple(fragments)
        if not self.fragments:
            raise ValueError('Positive original source fragments required')
        self.source_datum = min(v[2] for f in self.fragments for v in f.polygon)
        levels, areas, gradients, ids = [], [], [], []
        for fragment in self.fragments:
            for triangle in fragment.triangles:
                areas.append(float(area(triangle)))
                levels.append(sorted(float(v[2]-self.source_datum) for v in triangle))
                gradients.append(tuple(map(float, fragment.gradient)))
                ids.append(fragment.source_id)
        self.areas = np.asarray(areas)
        self.levels = np.asarray(levels)
        self.relative_levels = self.levels
        self.bed_gradients = np.asarray(gradients)
        self.source_triangle_indices = np.asarray(ids, dtype=np.int64)
        if (not all(np.isfinite(v).all() for v in (self.areas, self.levels, self.bed_gradients))
                or np.any(self.areas <= 0)):
            raise ValueError('Positive source metrics exceed represented range; no fragment deletion')
        for values in (self.areas, self.levels, self.bed_gradients, self.source_triangle_indices):
            values.setflags(write=False)
        self.datum = 0.
        self.area = math.fsum(areas)

    @property
    def triangles(self):
        raise ValueError('Exact source storage cannot be exported through a rounded-vertex storage API')

    def subset_sources(self, source_ids):
        requested = set(source_ids)
        selected = tuple(f for f in self.fragments if f.source_id in requested)
        if {f.source_id for f in selected} != requested:
            raise ValueError('Subset contains an unrepresented original source')
        return type(self)(selected)
