"""Double-precision diagnostics of unchanged native object-space coordinates."""
import numpy as np


def world_coordinates(vertices, matrix):
    points, transform = np.asarray(vertices, dtype=np.float64), np.asarray(matrix, dtype=np.float64)
    if (points.ndim != 2 or points.shape[1] != 3 or transform.shape != (4, 4)
            or not np.isfinite(points).all() or not np.isfinite(transform).all()
            or not np.array_equal(transform[3], [0., 0., 0., 1.])):
        raise ValueError('Finite vertices and affine native object transform required')
    return points @ transform[:3, :3].T + transform[:3, 3]
