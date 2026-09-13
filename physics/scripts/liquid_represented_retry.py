"""Local trust-region retries for non-injective represented contact directions.

Only a rejected trial direction is changed. Re-solve its original contact QP
at a smaller trust radius for each colliding member; never move stored points
apart, jitter, delete, merge or hide a marker. The caller must still check the
whole-domain density objective and every path before committing any position.
This is a numerical descent strategy, not an added physical repulsion force.
"""
import numpy as np
from liquid_particle_quantization import quantized_endpoint


def represented_retry(points, move, direction, axes, radius, project_subset, *, max_retries=16):
    p=np.asarray(points,float);d=np.array(move,dtype=float,copy=True)
    target=np.asarray(direction,float);a=np.asarray(axes,float)
    if (p.ndim!=2 or p.shape[1]!=3 or d.shape!=p.shape or target.shape!=p.shape or a.shape!=(3,3) or
            not all(np.isfinite(x).all() for x in (p,d,target,a)) or
            not np.allclose(a@a.T,np.eye(3),rtol=0,atol=1e-12) or
            not isinstance(max_retries,int) or max_retries<0):
        raise ValueError('Finite complete particle directions, orthonormal frame and retry count required')
    if not np.array_equal(p,p.astype('<f4').astype(float)) or len(np.unique(p,axis=0))!=len(p):
        raise ValueError('Distinct native-representable original positions required')
    scales=np.ones(len(p));history=[];failure=None
    for iteration in range(max_retries+1):
        updated,_=quantized_endpoint(p,d@a,radius)
        _,inverse,counts=np.unique(updated,axis=0,return_inverse=True,return_counts=True)
        selected=np.flatnonzero(counts[inverse]>1)
        if not len(selected):break
        if iteration==max_retries:
            failure='Represented contact trial remains non-injective';break
        scales[selected]*=.5
        revised,contact=project_subset(selected,target[selected]*scales[selected,None])
        history.append(dict(iteration=iteration,collision_groups=int((counts>1).sum()),
            indices=selected.tolist(),direction_scales=scales[selected].tolist(),contact=contact))
        if not contact['converged']:
            failure='Smaller local contact direction is not verified feasible';break
        revised=np.asarray(revised,float)
        if revised.shape!=(len(selected),3) or not np.isfinite(revised).all():
            raise ValueError('Incomplete projected subset direction')
        d[selected]=revised
    return d,updated,dict(converged=failure is None,failure=failure,retries=history,
        retried_particles=int((scales<1).sum()),minimum_direction_scale=float(scales.min(initial=1)),
        geometry_or_density_acceptance=False)
