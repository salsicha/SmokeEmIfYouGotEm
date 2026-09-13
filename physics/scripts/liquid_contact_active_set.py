"""Active-set refinement of the same nonnegative contact quadratic.

Rank-deficient active systems retain their linear residual. A curvature-aware
descent step reaches a feasible bound or line minimum; it never assumes that
an inexact least-squares residual is an exact null vector.
Every candidate is judged by the full original KKT residual.
"""
import numpy as np
from scipy.linalg import lstsq


def polish_contact_dual(matrix,rhs,initial,*,tolerance=1e-7,max_pivots=128):
    s=np.asarray(matrix,float);r=np.asarray(rhs,float);lam=np.asarray(initial,float).copy()
    if (r.ndim!=1 or s.shape!=(len(r),len(r)) or lam.shape!=r.shape or
        not all(np.isfinite(a).all() for a in (s,r,lam)) or (lam<0).any() or
        not np.isfinite(tolerance) or tolerance<=0 or max_pivots<1):
        raise ValueError('Finite contact system and feasible nonnegative initial multipliers required')
    passive=lam>0;history=[];failure=None;rank_deficient=0
    for pivot in range(max_pivots):
        residual=r-s@lam
        kkt=float(np.max(np.where(lam>0,abs(residual),np.maximum(residual,0)),initial=0))
        if kkt<=tolerance:break
        if not passive.any():
            if not np.any(residual>tolerance):failure='No improving contact pivot';break
            passive[int(np.argmax(residual))]=True
        active=np.flatnonzero(passive);a=s[np.ix_(active,active)];b=r[active]
        z,_,rank,_=lstsq(a,b,lapack_driver='gelsy',check_finite=False)
        linear_residual=b-a@z;linear_error=float(abs(linear_residual).max(initial=0))
        history.append(dict(pivot=pivot,active_rows=len(active),rank=int(rank),linear_error_cm=linear_error,kkt_error_cm=kkt))
        if linear_error>tolerance:
            rank_deficient+=1
            gradient=a@lam[active]-b;direction=linear_residual
            derivative=float(gradient@direction)
            if derivative>=0:direction=-gradient;derivative=-float(gradient@gradient)
            if not np.isfinite(derivative) or derivative>=0:failure='No descending direction for unresolved active system';break
            curvature=float(direction@(a@direction))
            downhill=np.flatnonzero(direction<0)
            null_error=float(abs(a@direction).max(initial=0))
            null_scale=max(float(np.linalg.norm(a,ord=np.inf))*float(abs(direction).max(initial=0)),1e-30)
            verified_null=null_error<=1e-10*null_scale
            history[-1]['verified_numerical_null']=verified_null
            if verified_null and not len(downhill):failure='Unbounded contact dual: incompatible primal constraints';break
            ratios=lam[active[downhill]]/(-direction[downhill])
            boundary_step=float(ratios.min()) if len(ratios) else np.inf
            line_step=-derivative/curvature if curvature>0 else np.inf
            step=min(boundary_step,line_step)
            if not np.isfinite(step):failure='Unbounded contact dual: incompatible primal constraints';break
            energy_change=step*derivative+.5*step*step*curvature
            if not np.isfinite(energy_change) or energy_change>0:failure='Unresolved active step does not decrease the quadratic';break
            history[-1].update(descent_step=step,directional_curvature=curvature,predicted_energy_change=energy_change)
            lam[active]=np.maximum(0,lam[active]+step*direction)
            if boundary_step<=line_step:
                blocked=active[downhill[ratios==boundary_step]];lam[blocked]=0;passive[blocked]=False
            continue
        negative=np.flatnonzero(z<0)
        if len(negative):
            ratios=lam[active[negative]]/(lam[active[negative]]-z[negative]);first=int(np.argmin(ratios));step=float(ratios[first])
            lam[active]=np.maximum(0,lam[active]+step*(z-lam[active]))
            blocked=active[negative[ratios==step]];lam[blocked]=0;passive[blocked]=False
            continue
        lam[:]=0;lam[active]=z
        residual=r-s@lam;inactive=np.flatnonzero(~passive)
        if len(inactive) and residual[inactive].max(initial=0)>tolerance:
            passive[inactive[int(np.argmax(residual[inactive]))]]=True
        elif float(abs(residual[active]).max(initial=0))>tolerance:
            failure='Active linear accuracy insufficient';break
    residual=r-s@lam;kkt=float(np.max(np.where(lam>0,abs(residual),np.maximum(residual,0)),initial=0))
    if kkt>tolerance and failure is None:failure='Active-set iteration limit reached'
    return lam,dict(converged=failure is None and kkt<=tolerance,active_set_pivots=len(history),
        active_set_rank_deficient_steps=rank_deficient,active_set_failure=failure,
        recomputed_dual_kkt_error_cm=kkt,active_set_history=history)
