"""Conservative Cartesian face-flux interval of shared liquid area fields.

This excludes internal free-surface flux and emission/removal; it is not a
complete mass budget or a claim of liquid incompressibility.
"""
import numpy as np


def cartesian_flux_bounds(velocity, area_lower, area_upper):
    v = np.asarray(velocity, float)
    if v.ndim != 4 or v.shape[-1] != 3 or not np.isfinite(v).all() or len(area_lower) != 3 or len(area_upper) != 3:
        raise ValueError('Finite native-layout world velocity and three physical area pairs required')
    shape = v.shape[:3]; lower = np.zeros(shape); upper = np.zeros(shape); boundary = [0., 0.]
    for axis in range(3):
        a, b = np.asarray(area_lower[axis], float), np.asarray(area_upper[axis], float)
        dims = list(shape); dims[axis] += 1
        if a.shape != tuple(dims) or b.shape != a.shape or not np.isfinite([a, b]).all() or np.any(a < 0) or np.any(b < a):
            raise ValueError('Complete nonnegative N+1 liquid area bounds required')
        # Native lower-face MAC has no velocity for the final N+1 plane.
        # Its flux is zero ONLY when its liquid area is proved zero.
        if np.any(np.take(b, -1, axis=axis) != 0):
            raise ValueError('Missing outer-face velocity with possibly wet area; do not invent it')
        component = np.zeros(a.shape); sl = [slice(None)]*3; sl[axis] = slice(0, shape[axis])
        component[tuple(sl)] = v[..., axis]
        qa, qb = component*a, component*b; qlo, qhi = np.minimum(qa, qb), np.maximum(qa, qb)
        lo = [slice(None)]*3; hi = list(lo); lo[axis] = slice(None, -1); hi[axis] = slice(1, None)
        # Outward flux, m3/s. One shared face is used by both neighbors.
        lower += qlo[tuple(hi)]-qhi[tuple(lo)]; upper += qhi[tuple(hi)]-qlo[tuple(lo)]
        boundary[0] += float(np.take(qlo, -1, axis=axis).sum()-np.take(qhi, 0, axis=axis).sum())
        boundary[1] += float(np.take(qhi, -1, axis=axis).sum()-np.take(qlo, 0, axis=axis).sum())
    return lower, upper, boundary
