"""Reconstruct native storage ownership from prepared geometry, not GPU routes.

The GPU's declared double-float-demote-v1 contract uploads the frame in float32,
evaluates its dot product with retained residuals, and rounds the result once.
Internal storage cuts must be compared in that frame. Survey geometry is a
separate comparison; callers must not use this to expand physical outer bounds.
"""
import numpy as np


def prepared_float_frame_owners(points,regions,residual_outer=False):
    points=np.asarray(points,dtype=float)
    if points.ndim!=2 or points.shape[1]!=3 or not np.isfinite(points).all() or not regions:
        raise ValueError('Finite positions and prepared regions required')
    bounds=np.asarray([r['bounds_station_lateral_m'] for r in regions],dtype=float)
    if bounds.shape!=(len(regions),2,2) or not np.isfinite(bounds).all() or np.any(bounds[:,1]<=bounds[:,0]):
        raise ValueError('Finite ordered prepared bounds required')
    frames=np.asarray([[r['axis_x_canonical'],r['axis_y_canonical']] for r in regions],dtype=float)
    if (frames.shape not in ((len(regions),2,2),(len(regions),2,3)) or not np.isfinite(frames).all() or
            not np.all(frames==frames[0]) or (frames.shape[-1]==3 and np.any(frames[:,:,2]))):
        raise ValueError('One common horizontal prepared frame required')
    axes=frames[0,:,:2]
    if not np.allclose(axes@axes.T,np.eye(2),atol=1e-9,rtol=0):
        raise ValueError('Orthonormal prepared frame required')
    if len({r['id'] for r in regions})!=len(regions):raise ValueError('Unique storage owners required')
    lower=bounds[:,0].min(axis=0)
    world_lower=((axes.T@(lower*100))*[1,-1]).astype('<f4').astype(float)
    world_axes=(axes*[1,-1]).astype('<f4').astype(float)
    q_exact=(points[:,:2]-world_lower)@world_axes.T
    q=q_exact.astype('<f4').astype(float)
    relative=((bounds-lower)*100).astype('<f4').astype(float)
    upper=relative[:,1].max(axis=0)
    result=np.full(len(points),-1,dtype=np.int64)
    for r,b in zip(regions,relative):
        inside=((q>=b[0])&((q<b[1])|((b[1]==upper)&(q<=b[1])))).all(axis=1)
        if np.any(inside & (result>=0)):raise ValueError('Overlapping uploaded-frame bounds')
        result[inside]=r['id']
    if residual_outer:
        # The outer decision retains the uploaded frame's residual. Internal
        # storage cuts retain their original single-rounded ownership contract.
        result[np.any((q_exact<0)|(q_exact>upper),axis=1)]=-1
    return result,q,q_exact,world_lower,world_axes
