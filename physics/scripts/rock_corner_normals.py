"""Authored crease-aware shading only; never reconstruct or move source geometry."""
import math
import numpy as np


def corner_normals(vertices, triangles, face_kind, crease_degrees):
    """Angle-weighted normals within edge-connected, provenance-separated fans.

    Sharp, boundary, nonmanifold and differently classified edges split fans.
    Coincident positions are never welded. The crease angle is an art parameter,
    not a measured fracture angle. Input arrays are never modified.
    """
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(triangles)
    kinds = np.asarray(face_kind)
    if (v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all() or
            f.ndim != 2 or f.shape[1] != 3 or not len(f) or
            not np.issubdtype(f.dtype, np.integer) or
            f.min() < 0 or f.max() >= len(v) or kinds.shape != (len(f),)):
        raise ValueError('Finite indexed triangles and one provenance kind per face required')
    if not math.isfinite(crease_degrees) or not 0 < crease_degrees < 90:
        raise ValueError('Crease angle must be strictly between zero and 90 degrees')
    points = v[f]
    cross = np.cross(points[:, 1]-points[:, 0], points[:, 2]-points[:, 0])
    length = np.linalg.norm(cross, axis=1)
    if not np.isfinite(length).all() or np.any(length == 0):
        raise ValueError('Degenerate triangle cannot define a shading normal')
    normals = cross / length[:, None]
    parent = np.arange(f.size)

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    edges = {}
    for face, triangle in enumerate(f):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            edges.setdefault(tuple(sorted((int(triangle[a]), int(triangle[b])))), []).append((face, a, b))
    smooth_edges = 0
    cosine = math.cos(math.radians(crease_degrees))
    for adjacent in edges.values():
        if len(adjacent) != 2:
            continue
        (i, a, b), (j, c, d) = adjacent
        # Require oppositely directed manifold edges, not coincident sheets.
        if (f[i, a] != f[j, d] or f[i, b] != f[j, c] or
                kinds[i] != kinds[j] or normals[i] @ normals[j] < cosine):
            continue
        for left, right in ((i*3+a, j*3+d), (i*3+b, j*3+c)):
            parent[root(right)] = root(left)
        smooth_edges += 1
    angles = np.empty((len(f), 3))
    for corner in range(3):
        a = points[:, (corner+1) % 3]-points[:, corner]
        b = points[:, (corner+2) % 3]-points[:, corner]
        angles[:, corner] = np.arctan2(np.linalg.norm(np.cross(a, b), axis=1), np.einsum('ij,ij->i', a, b))
    roots = np.array([root(i) for i in range(f.size)])
    sums = np.zeros((f.size, 3))
    np.add.at(sums, roots, (normals[:, None, :]*angles[:, :, None]).reshape(-1, 3))
    result = sums[roots]
    magnitudes = np.linalg.norm(result, axis=1)
    if not np.isfinite(magnitudes).all() or np.any(magnitudes == 0):
        raise ValueError('Invalid shading fan')
    result = (result / magnitudes[:, None]).reshape(-1, 3, 3)
    return result, dict(crease_degrees=float(crease_degrees), smooth_edge_count=smooth_edges,
                        split_edge_count=len(edges)-smooth_edges,
                        shading_fan_count=int(len(np.unique(roots))),
                        authored_shading=True, measured_geometry_changed=False)
