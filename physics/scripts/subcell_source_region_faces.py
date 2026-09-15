"""Original mesh edges between source-supported regions inside one grid cell.

Clipping and side predicates use exact rationals of represented coordinates.
No coordinate welding or point-contact connection; hydraulic length is the
horizontal projection, not the sloping three-dimensional edge length.
"""
from fractions import Fraction as F
import math
import numpy as np


def clipped_edge(sampler, edge, center, spacing):
    a, b = sampler.xyz[list(edge)]
    start = [F(float(a[j])) for j in range(3)]
    delta = [F(float(b[j]))-start[j] for j in range(3)]
    if delta[0] == 0 and delta[1] == 0:
        return None
    low, high = F(0), F(1)
    for j in range(2):
        origin, half = F(float(center[j])), F(float(spacing[j]))/2
        offset = start[j]-origin
        if delta[j] == 0:
            # An edge on the box itself belongs to the Cartesian face path.
            if not -half < offset < half:
                return None
        else:
            first, last = (-half-offset)/delta[j], (half-offset)/delta[j]
            low, high = max(low, min(first, last)), min(high, max(first, last))
    if low >= high:
        return None
    length = math.hypot(float((high-low)*delta[0]), float((high-low)*delta[1]))
    if not math.isfinite(length) or length <= 0:
        raise ValueError('Positive internal source edge exceeds represented range')
    xyz = np.array([[float(start[j]+t*delta[j]-(F(float(center[j])) if j < 2 else 0))
                     for j in range(3)] for t in (low, high)])
    return xyz, length


def internal_faces(partition):
    source = partition.sampler
    result = []
    for parent, cell in enumerate(partition.patch.cells):
        owner = {}
        for index in partition.parent_pools[parent]:
            for face in partition.pools[index]['source_triangle_indices']:
                if face in owner:
                    raise ValueError('Original source face has multiple region owners')
                owner[face] = index
        if not owner:
            continue
        adjacent = {}
        for face in sorted(set(map(int, cell.source_triangle_indices))):
            vertices = source.faces[face]
            for j in range(3):
                edge = tuple(sorted((int(vertices[j]), int(vertices[(j+1)%3]))))
                adjacent.setdefault(edge, []).append(face)
        row, col = divmod(parent, partition.patch.shape[1])
        center = partition.origin+partition.patch.spacing*[col, row]
        for edge, faces in adjacent.items():
            if len(faces) > 2:
                raise ValueError('Nonmanifold original source edge')
            if len(faces) != 2:
                continue
            left, right = faces
            li, ri = owner.get(left), owner.get(right)
            if li == ri:
                continue
            clipped = clipped_edge(source, edge, center, partition.patch.spacing)
            if clipped is None:
                continue
            xyz, length = clipped
            a, b = source.xyz[list(edge)]
            third = source.xyz[next(int(v) for v in source.faces[left] if int(v) not in edge)]
            dx, dy = F(float(b[0]))-F(float(a[0])), F(float(b[1]))-F(float(a[1]))
            cross = dx*(F(float(third[1]))-F(float(a[1])))-dy*(F(float(third[0]))-F(float(a[0])))
            if cross == 0:
                raise ValueError('Degenerate projected original source face')
            normal = np.array([float(dy), -float(dx)])
            normal /= math.hypot(*normal)
            if cross < 0:
                normal *= -1
            result.append(dict(parent=parent, left=li, right=ri, left_source=left, right_source=right,
                edge_vertex_ids=list(edge), normal=normal,
                xyz=xyz, segment=np.column_stack(([0., length], xyz[:, 2]))))
    return result
