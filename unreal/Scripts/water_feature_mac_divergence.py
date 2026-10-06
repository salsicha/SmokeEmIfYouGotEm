"""Native lower-face MAC differences; no interface or mass correction."""
import numpy as np


def mac_divergence(velocity, spacing):
    v = np.asarray(velocity, dtype=np.float64)
    h = np.asarray(spacing, dtype=np.float64)
    if v.ndim != 4 or v.shape[-1] != 3 or min(v.shape[:3]) < 2:
        raise ValueError('Expected nondegenerate (x,y,z,3) MAC field')
    if not np.isfinite(v).all() or h.shape != (3,) or not np.isfinite(h).all() or not (h > 0).all():
        raise ValueError('Need finite velocities and positive finite spacing')
    base = v[:-1, :-1, :-1]
    return ((v[1:, :-1, :-1, 0]-base[..., 0])/h[0]
            +(v[:-1, 1:, :-1, 1]-base[..., 1])/h[1]
            +(v[:-1, :-1, 1:, 2]-base[..., 2])/h[2])


def interior_liquid_mask(phi, solid, margin=1.):
    """Exclude interfaces, obstacles and cells lacking six liquid neighbors.

    Margin uses the cached level-set units, not assumed world meters.
    """
    p, s = np.asarray(phi), np.asarray(solid)
    if p.ndim != 3 or p.shape != s.shape or min(p.shape) < 3 or margin < 0:
        raise ValueError('Need matching 3D fields and nonnegative margin')
    if not np.isfinite(p).all() or not np.isfinite(s).all():
        raise ValueError('Nonfinite level set')
    mask = (p < -margin) & (s > margin)
    support = np.pad((p < 0) & (s >= 0), 1, constant_values=False)
    nx, ny, nz = p.shape
    for axis in range(3):
        for offset in (-1, 1):
            start = [1, 1, 1]
            start[axis] += offset
            mask &= support[start[0]:start[0]+nx, start[1]:start[1]+ny, start[2]:start[2]+nz]
    return mask[:-1, :-1, :-1]
