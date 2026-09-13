"""Projected over-relaxation for the unchanged contact quadratic.

For one unconstrained coordinate, the quadratic energy change is
(-omega + omega**2/2) * gradient**2 / diagonal. A nonnegative-bound clamp
shortens that step, so 0 < omega < 2 still descends along the coordinate.
This does not waive any original primal or dual convergence check.
"""
import numpy as np


def solve_contact_psor(matrix,rhs,*,relaxation=1.8,max_sweeps=30000,tolerance=1e-7,initial=None):
    s=np.asfortranarray(matrix,dtype=float);r=np.asarray(rhs,float)
    if (r.ndim!=1 or s.shape!=(len(r),len(r)) or not np.isfinite(s).all() or not np.isfinite(r).all() or
        not np.isfinite(relaxation) or not 0<relaxation<2 or max_sweeps<1 or not np.isfinite(tolerance) or tolerance<=0):
        raise ValueError('Finite contact system, relaxation in (0,2), and positive controls required')
    d=np.diag(s)
    if np.any((d<=0)&(r>1e-8)):raise ValueError('Wall constraint incompatible with divergence and fixed geometry')
    lam=np.zeros(len(r)) if initial is None else np.asarray(initial,float).copy()
    if lam.shape!=r.shape or not np.isfinite(lam).all() or (lam<0).any():raise ValueError('Finite nonnegative warm multipliers required')
    residual=r-s@lam if initial is not None else r.copy();work=np.empty_like(r)
    for sweep in range(max_sweeps):
        for row in range(len(r)):
            if d[row]<=0:continue
            updated=max(0,lam[row]+relaxation*residual[row]/d[row]);change=updated-lam[row]
            if change:
                lam[row]=updated;np.multiply(s[:,row],change,out=work);np.subtract(residual,work,out=residual)
        kkt=float(np.max(np.where(lam>0,abs(residual),np.maximum(residual,0)),initial=0))
        if kkt<=tolerance:break
    actual=r-s@lam
    actual_kkt=float(np.max(np.where(lam>0,abs(actual),np.maximum(actual,0)),initial=0))
    return lam,dict(converged=kkt<=tolerance and actual_kkt<=tolerance,relaxation=relaxation,
        dual_sweeps=sweep+1,dual_kkt_error_cm=kkt,recomputed_dual_kkt_error_cm=actual_kkt,
        incremental_residual_drift_cm=float(abs(actual-residual).max(initial=0)))
