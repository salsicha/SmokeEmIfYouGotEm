"""Conservative float32 world-position error boxes for contact constraints.

These boxes bound representation error, not a permission to penetrate terrain
or enlarge the river. Final quantized positions still need exact geometry and
density checks. No coordinates are clamped, jittered or independently pushed out.
"""
import numpy as np


def position_error_box(points,maximum_world_motion):
    p=np.asarray(points,float);radius=float(maximum_world_motion)
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all() or not np.isfinite(radius) or radius<=0:
        raise ValueError('Finite positions and positive bounded world displacement required')
    magnitude=np.abs(p)+radius
    if np.any(magnitude>=np.finfo(np.float32).max):raise ValueError('No finite float32 rounding envelope')
    # Round the largest absolute endpoint upward before selecting the binade.
    upper=np.nextafter(magnitude.astype('<f4'),np.float32(np.inf)).astype(float)
    if not np.isfinite(upper).all():raise ValueError('Float32 envelope overflow')
    return np.spacing(upper.astype('<f4')).astype(float)*.5


def quantized_endpoint(points,world_move,maximum_world_motion):
    p=np.asarray(points,float);d=np.asarray(world_move,float)
    error=position_error_box(p,maximum_world_motion)
    if d.shape!=p.shape or not np.isfinite(d).all() or (np.abs(d)>maximum_world_motion).any():
        raise ValueError('Trial movement escapes the represented error box')
    exact=p+d;stored=exact.astype('<f4').astype(float)
    if np.any(abs(stored-exact)>error):raise ValueError('Observed native rounding exceeds derived bound')
    return stored,error
