"""Float64 triangle nearest query with complete conservative AABB candidates.

Does not rely on Blender's float BVH retaining thin positive-area facets.
Vectorized all-triangle AABB scan, then the independently defined bounded
point/triangle distance. No geometric repair, smoothing or query projection
outside the mathematical nearest-point calculation. This is not an exact-
arithmetic proof or a self-intersection/orientation check.
"""
import numpy as np

from water_feature_mesh_interface import closest_triangle


class TriangleNearest:
    def __init__(self, vertices, triangles):
        vertices, triangles = np.asarray(vertices), np.asarray(triangles)
        if (vertices.ndim != 2 or vertices.shape[1] != 3
                or not np.isfinite(vertices).all() or triangles.ndim != 2
                or triangles.shape[1] != 3 or len(triangles) == 0
                or not np.issubdtype(triangles.dtype, np.integer)
                or np.any(triangles < 0) or np.any(triangles >= len(vertices))):
            raise ValueError('Finite vertices and nonempty indexed triangles required')
        self.xyz = np.array(vertices[triangles], dtype=float, copy=True)
        if np.any(np.linalg.norm(np.cross(self.xyz[:, 1]-self.xyz[:, 0],
                                         self.xyz[:, 2]-self.xyz[:, 0]), axis=1) <= 0):
            raise ValueError('Zero-area triangles are not repaired')
        self.lower, self.upper = self.xyz.min(axis=1), self.xyz.max(axis=1)
        self.coordinate_scale = max(1., float(np.max(np.abs(self.xyz))))
        self.xyz.flags.writeable = False
        self.lower.flags.writeable = self.upper.flags.writeable = False
        self.queries, self.maximum_candidates = 0, 0

    def __call__(self, point):
        p = np.asarray(point, float)
        if p.shape != (3,) or not np.isfinite(p).all():
            raise ValueError('Finite 3D nearest query required')
        # Every triangle is inside its AABB. Its box distance is a lower bound
        # for its actual triangle distance; no float-BVH candidate omission.
        delta = np.maximum(0., np.maximum(self.lower-p, p-self.upper))
        lower_squared = np.einsum('ij,ij->i', delta, delta)
        face = int(np.argmin(lower_squared))
        best = closest_triangle(p, self.xyz[face])
        best_squared = float(np.sum((p-best)**2))
        # Conservative floating-coordinate margin, not a contact allowance or
        # a displacement of the point/triangles. Candidate inclusion only.
        rounding = 64*np.finfo(float).eps*max(self.coordinate_scale, float(np.max(np.abs(p))))
        bound = (np.sqrt(best_squared)+rounding)**2
        candidates = np.flatnonzero(lower_squared <= bound)
        self.queries += 1
        self.maximum_candidates = max(self.maximum_candidates, len(candidates))
        for other in candidates:
            if other == face or lower_squared[other] > (np.sqrt(best_squared)+rounding)**2:
                continue
            q = closest_triangle(p, self.xyz[other])
            squared = float(np.sum((p-q)**2))
            if (squared, int(other)) < (best_squared, face):
                best, best_squared, face = q, squared, int(other)
        return best, face
