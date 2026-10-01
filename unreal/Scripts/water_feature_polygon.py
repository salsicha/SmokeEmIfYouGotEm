"""Constrained ear clipping retaining collinear polygon boundary vertices."""
import numpy as np


def triangulate_polygon(coordinates):
    points = np.asarray(coordinates, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 3 or not np.isfinite(points).all():
        raise ValueError('Finite 3D polygon required')
    points = points-points[0]
    normal = np.sum(np.cross(points, np.roll(points, -1, axis=0)), axis=0)
    normal_length = np.linalg.norm(normal)
    if normal_length == 0:
        raise ValueError('Zero-area polygon')
    normal = normal/normal_length
    # Dropping a coordinate can collapse distinct endpoints on slightly
    # nonplanar native contact polygons. Project onto an orthonormal basis
    # of the area-normal plane instead; never move the original 3D vertices.
    reference = np.eye(3)[int(np.argmin(np.abs(normal)))]
    tangent = np.cross(reference, normal)
    tangent /= np.linalg.norm(tangent)
    bitangent = np.cross(normal, tangent)
    xy = np.column_stack((points @ tangent, points @ bitangent))
    signed_twice_area = np.sum(xy[:, 0]*np.roll(xy[:, 1], -1)-xy[:, 1]*np.roll(xy[:, 0], -1))
    winding = 1. if signed_twice_area > 0 else -1.
    tolerance = np.finfo(float).eps*max(float(np.ptp(xy, axis=0).max())**2, 1e-30)*8

    def orient(a, b, c):
        ab, ac = b-a, c-a
        return ab[..., 0]*ac[..., 1]-ab[..., 1]*ac[..., 0]

    remaining, triangles = list(range(len(points))), []
    while len(remaining) > 3:
        ears = []
        for index, b in enumerate(remaining):
            a, c = remaining[index-1], remaining[(index+1) % len(remaining)]
            area = winding*orient(xy[a], xy[b], xy[c])
            if area <= tolerance:
                continue
            others = [i for i in remaining if i not in (a, b, c)]
            q = xy[others]
            # Inclusive boundary checks protect collinear vertices on the
            # proposed diagonal. No boundary vertex is dropped or bypassed.
            inside = ((winding*orient(xy[a], xy[b], q) >= -tolerance)
                      & (winding*orient(xy[b], xy[c], q) >= -tolerance)
                      & (winding*orient(xy[c], xy[a], q) >= -tolerance))
            if not np.any(inside):
                ears.append((float(area), index, (a, b, c)))
        if not ears:
            raise ValueError('No valid constrained ear; self-touching or numerically unresolved polygon')
        _, index, triangle = max(ears)
        triangles.append(triangle)
        remaining.pop(index)
    if winding*orient(*xy[remaining]) <= tolerance:
        raise ValueError('Degenerate final ear; preserve original evidence')
    triangles.append(tuple(remaining))
    return triangles
