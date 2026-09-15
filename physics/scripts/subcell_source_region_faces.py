"""Original mesh edges between source-supported regions inside one grid cell.

Clipping and side predicates use exact rationals of represented coordinates.
No coordinate welding or point-contact connection; hydraulic length is the
horizontal projection, not the sloping three-dimensional edge length.
"""
from fractions import Fraction as F
import math
import numpy as np
from subcell_source_face_section import SourceFaceSection


def clipped_edge(sampler, edge, center, spacing, with_exact=False):
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
    exact = tuple(tuple(start[j]+t*delta[j]-(F(float(center[j])) if j < 2 else 0)
                        for j in range(3)) for t in (low, high))
    xyz = np.asarray(exact, float)
    return (xyz, length, exact) if with_exact else (xyz, length)


def internal_faces(partition, additional_owners=None):
    """Enumerate original edges, optionally with geometry-only birth labels.

    Additional labels do not create water or alter the partition. They expose
    dry/dry edges needed by one-sided simultaneous-birth analysis.
    """
    additional_owners = {} if additional_owners is None else dict(additional_owners)
    for (parent, face), index in additional_owners.items():
        if (not isinstance(parent, (int, np.integer)) or not 0 <= parent < len(partition.patch.cells)
                or not isinstance(face, (int, np.integer))
                or face not in partition.patch.cells[parent].source_triangle_indices
                or not isinstance(index, (int, np.integer)) or index < len(partition.pools)):
            raise ValueError('Explicit unowned original source and new geometry label required')
    source = partition.sampler
    result = []
    for parent, cell in enumerate(partition.patch.cells):
        owner = {}
        for index in partition.parent_pools[parent]:
            for face in partition.pools[index]['source_triangle_indices']:
                if face in owner:
                    raise ValueError('Original source face has multiple region owners')
                owner[face] = index
        for (p, face), index in additional_owners.items():
            if p == parent:
                if face in owner:
                    raise ValueError('Birth geometry label cannot replace an existing owner')
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
            exact_sources = hasattr(cell, 'fragments')
            clipped = clipped_edge(source, edge, center, partition.patch.spacing, with_exact=exact_sources)
            if clipped is None:
                continue
            xyz, length = clipped[:2]
            segment = (SourceFaceSection([[(F(0), clipped[2][0][2]), (F(length), clipped[2][1][2])]])
                       if exact_sources else np.column_stack(([0., length], xyz[:, 2])))
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
                xyz=xyz, segment=segment))
    return result
