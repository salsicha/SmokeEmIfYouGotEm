"""Exact containment certificate for an unchanged actual box collider.

This only certifies fully covered faces. It does not approximate curved or
concave solids, discard small openings, change geometry, or compute apertures.
"""
import numpy as np


def certified_box_faces(vertices, triangles, shape, origin, cell_m):
    v, t = np.asarray(vertices, float), np.asarray(triangles)
    if (v.shape != (8, 3) or t.shape != (12, 3) or not np.issubdtype(t.dtype, np.integer)
            or t.min() < 0 or t.max() >= 8 or not np.isfinite(v).all()):
        raise ValueError('Actual eight-vertex closed axis-aligned box required')
    lo, hi = v.min(0), v.max(0)
    if np.any(hi <= lo) or not np.all((v == lo) | (v == hi)) or len(np.unique(v, axis=0)) != 8:
        raise ValueError('Not an actual axis-aligned box')
    face_triangles = {(a, float(b)): 0 for a in range(3) for b in (lo[a], hi[a])}
    for tri in t:
        p = v[tri]
        faces = [(a, float(b)) for a in range(3) for b in (lo[a], hi[a]) if np.all(p[:, a] == b)]
        if len(faces) != 1 or np.linalg.norm(np.cross(p[1]-p[0], p[2]-p[0])) == 0:
            raise ValueError('Triangle is not on one proper actual box face')
        face_triangles[faces[0]] += 1
    edges = np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    if any(c != 2 for c in face_triangles.values()) or np.any(counts != 2):
        raise ValueError('Box surface is not a closed two-triangle-per-face shell')
    origin = np.asarray(origin, float)
    if len(shape) != 3 or any(n < 2 for n in shape) or origin.shape != (3,) or cell_m <= 0:
        raise ValueError('Physical Cartesian lattice required')
    result = []
    for axis in range(3):
        dims = list(shape); dims[axis] += 1; covered = np.ones(dims, bool)
        for a in range(3):
            coordinate = origin[a]+np.arange(dims[a])*cell_m
            valid = (coordinate >= lo[a]) & (coordinate <= hi[a])
            if a != axis:
                # Match the represented rectangle used by original clipping.
                valid &= coordinate+cell_m <= hi[a]
            reshaped = [1, 1, 1]; reshaped[a] = dims[a]
            covered &= valid.reshape(reshaped)
        result.append(covered)
    return result
