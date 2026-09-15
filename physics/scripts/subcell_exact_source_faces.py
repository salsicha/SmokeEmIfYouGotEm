"""Canonical Cartesian face cuts from original source triangles.

Intersections use exact rationals of represented mesh/box coordinates before a
single float conversion. Adjacent source triangles therefore share the SAME
intersection; no independently rounded polygon endpoints are welded or dropped.
"""
from fractions import Fraction as F
import numpy as np
from subcell_source_face_section import SourceFaceSection


def triangle_cut(triangle, center, spacing, axis, sign):
    other = 1-axis
    center = [F(float(x)) for x in center]
    half = [F(float(x))/2 for x in spacing]
    plane = center[axis]+sign*half[axis]
    xyz = [[F(float(x)) for x in v] for v in triangle]
    points = set()
    for a, b in zip(xyz, xyz[1:]+xyz[:1]):
        if a[axis] == plane:
            points.add((a[other], a[2]))
        if (a[axis] < plane < b[axis]) or (b[axis] < plane < a[axis]):
            ratio = (plane-a[axis])/(b[axis]-a[axis])
            points.add((a[other]+ratio*(b[other]-a[other]), a[2]+ratio*(b[2]-a[2])))
    if len(points) < 2:
        return None
    first, last = min(points), max(points)
    low = max(first[0], center[other]-half[other])
    high = min(last[0], center[other]+half[other])
    if low >= high:
        return None
    z = lambda t: first[1]+(t-first[0])*(last[1]-first[1])/(last[0]-first[0])
    segment = np.array([[float(t-center[other]), float(z(t))] for t in (low, high)])
    if segment[0, 0] >= segment[1, 0]:
        raise ValueError('Positive original source-face interval is not representable')
    segment.setflags(write=False)
    return segment


def source_faces(partition, parent, axis, sign):
    if axis not in (0, 1) or sign not in (-1, 1):
        raise ValueError('Cartesian source face direction required')
    key = (parent, axis, sign)
    if key not in partition.source_face_cache:
        row, col = divmod(parent, partition.patch.shape[1])
        center = partition.origin+partition.patch.spacing*[col, row]
        result = []
        cell = partition.patch.cells[parent]
        if hasattr(cell, 'fragments'):
            for fragment in cell.fragments:
                segment = fragment.face(axis, sign*F(float(partition.patch.spacing[axis]))/2)
                if segment is not None:
                    result.append((fragment.source_id, SourceFaceSection([segment])))
            partition.source_face_cache[key] = result
            return result
        for source in sorted(set(map(int, partition.patch.cells[parent].source_triangle_indices))):
            triangle = partition.sampler.xyz[partition.sampler.faces[source]]
            segment = triangle_cut(triangle, center, partition.patch.spacing, axis, sign)
            if segment is not None:
                result.append((source, segment))
        partition.source_face_cache[key] = result
    return partition.source_face_cache[key]
