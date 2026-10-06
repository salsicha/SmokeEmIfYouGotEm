"""Welded tessellation of actual quadratic tetrahedral liquid boundaries.

No smoothing, expanded skin, heightfield restriction, clipping or liquid edits.
Interpolation positions are exact samples; planar triangle chords approximate
the curved boundary and their volume error must be measured separately.
"""
from collections import Counter
import numpy as np


def surface_weights(vertex_cells, cells, velocity_nodes, subdivisions=8):
    t = np.asarray(vertex_cells); c = np.asarray(cells)
    if (t.ndim != 2 or t.shape[1] != 4 or c.shape != (len(t), 10) or not np.issubdtype(t.dtype, np.integer)
            or not np.issubdtype(c.dtype, np.integer) or not isinstance(subdivisions, int) or not 1 <= subdivisions <= 16
            or np.any(c < 0) or np.any(c >= velocity_nodes) or not np.array_equal(t, c[:, :4])):
        raise ValueError('Complete quadratic tetrahedral topology required')
    owners = {}
    for ci, tet in enumerate(t):
        for opposite in range(4):
            corners = [j for j in range(4) if j != opposite]
            if opposite % 2:
                corners[1], corners[2] = corners[2], corners[1]
            key = tuple(sorted(int(tet[j]) for j in corners))
            owners.setdefault(key, []).append((ci, corners))
    if any(len(x) > 2 for x in owners.values()):
        raise ValueError('Nonmanifold material boundary')
    keys = {}; weights = []; triangles = []; r = subdivisions
    pairs = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    for entries in owners.values():
        if len(entries) != 1:
            continue
        ci, corners = entries[0]; ids = {}
        for i in range(r+1):
            for j in range(r+1-i):
                numerators = (i, j, r-i-j)
                key = tuple(sorted((int(t[ci, corner]), q) for corner, q in zip(corners, numerators) if q))
                if key not in keys:
                    keys[key] = len(weights); l = np.zeros(4)
                    for corner, q in zip(corners, numerators):
                        l[corner] = q/r
                    n = np.array([l[k]*(2*l[k]-1) for k in range(4)]+[4*l[a]*l[b] for a, b in pairs])
                    row = np.zeros(velocity_nodes); row[c[ci]] = n; weights.append(row)
                ids[(i, j)] = keys[key]
        for i in range(r):
            for j in range(r-i):
                triangles.append([ids[i, j], ids[i+1, j], ids[i, j+1]])
                if i+j < r-1:
                    triangles.append([ids[i+1, j], ids[i+1, j+1], ids[i, j+1]])
    result = np.array(weights); triangles = np.array(triangles, int)
    edges = Counter(tuple(sorted((int(a), int(b)))) for tri in triangles for a, b in zip(tri, np.roll(tri, -1)))
    if not len(result) or any(n != 2 for n in edges.values()) or not np.allclose(result.sum(axis=1), 1., rtol=0., atol=1e-14):
        raise ValueError('Boundary coverage/welding failed')
    return result, triangles


def triangle_volume(positions, triangles):
    p = np.asarray(positions, float); tris = p[np.asarray(triangles, int)]
    if not np.isfinite(tris).all():
        raise ValueError('Finite sampled liquid boundary required')
    center = p.mean(axis=0); a, b, c = (tris[:, i]-center for i in range(3))
    return float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum()/6)
