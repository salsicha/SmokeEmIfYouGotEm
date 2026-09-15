"""Source-topological wet components inside one exact Cartesian cell.

Connectivity uses original mesh vertex IDs and positive wet edge length, never
rounded-coordinate welding, point contact or a cell-center wet flag. Geometry
predicates use exact rationals of the represented source coordinates/stage.
This identifies fixed-state components; it does not evolve separate pool levels.
"""
from fractions import Fraction as F
import numpy as np


def shared_wet_edge(sampler, edge, center, size, cell_datum, relative_stage):
    """Whether an original shared edge has positive wet length inside the cell."""
    a, b = sampler.xyz[list(edge)]
    if np.array_equal(a[:2], b[:2]):
        return False
    lower, upper = F(0), F(1)
    for axis in (0, 1):
        origin = F(float(center[axis]))
        half = F(float(size[axis]))/2
        x = F(float(a[axis]))-origin
        step = F(float(b[axis]))-F(float(a[axis]))
        if step == 0:
            if not -half <= x <= half:
                return False
            continue
        first, last = (-half-x)/step, (half-x)/step
        if first > last:
            first, last = last, first
        lower, upper = max(lower, first), min(upper, last)
        if lower >= upper:
            return False
    if lower >= upper:
        return False
    z = F(float(a[2]))-F(cell_datum)
    dz = F(float(b[2]))-F(float(a[2]))
    eta = F(float(relative_stage))
    # An affine depth is positive on a positive-length interval iff at least
    # one endpoint is strictly positive. A level-dry edge is not a bridge.
    return max(eta-z-lower*dz, eta-z-upper*dz) > 0


def components(sampler, cell, center, size, relative_stage):
    if cell.source_triangle_indices is None:
        raise ValueError('Original source triangle IDs required for wet connectivity')
    center, size = np.asarray(center, float), np.asarray(size, float)
    if (center.shape != (2,) or size.shape != (2,) or not np.isfinite([center, size]).all()
            or (size <= 0).any() or not np.isfinite(relative_stage)):
        raise ValueError('Finite source footprint and relative stage required')
    volumes, wet_areas = cell._triangle_volume_and_wet_area(relative_stage, cell.relative_levels)
    active = sorted(set(map(int, cell.source_triangle_indices[wet_areas > 0])))
    adjacency = {index: set() for index in active}
    owners = {}
    for index in active:
        face = sampler.faces[index]
        for i in range(3):
            key = tuple(sorted((int(face[i]), int(face[(i+1)%3]))))
            owners.setdefault(key, []).append(index)
    connected_edges = 0
    for edge, faces in owners.items():
        if len(faces) > 2:
            raise ValueError('Nonmanifold original source edge')
        if len(faces) == 2 and shared_wet_edge(sampler, edge, center, size,
                getattr(cell, 'source_datum', cell.datum), relative_stage):
            a, b = faces
            adjacency[a].add(b); adjacency[b].add(a)
            connected_edges += 1
    remaining, result = set(active), []
    while remaining:
        pending = [min(remaining)]; found = set()
        while pending:
            index = pending.pop()
            if index in found:
                continue
            found.add(index)
            pending.extend(adjacency[index]-found)
        remaining -= found
        mask = np.isin(cell.source_triangle_indices, list(found))
        result.append(dict(source_triangle_indices=sorted(found),
            volume_m3=float(np.sum(volumes[mask])), wet_area_m2=float(np.sum(wet_areas[mask]))))
    return dict(components=result, component_count=len(result), shared_wet_source_edges=connected_edges,
        total_volume_m3=float(np.sum(volumes)), total_wet_area_m2=float(np.sum(wet_areas)),
        one_pressure_unknown_per_cell_supported=len(result) <= 1,
        time_or_wet_front_or_gameplay_accepted=False)
