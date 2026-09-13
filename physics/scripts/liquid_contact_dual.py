"""Memory-local coordinate solve for the unilateral contact Schur problem.

This is the same dual iteration as the slow reference, with contiguous columns
and a reusable update buffer. No residual gate or contact constraint is relaxed.
"""
import numpy as np


def solve_contact_dual(matrix,rhs,*,max_sweeps=30000,tolerance=1e-7,initial=None):
    s=np.asfortranarray(matrix,dtype=float);r=np.asarray(rhs,float)
    if (r.ndim!=1 or s.shape!=(len(r),len(r)) or not np.isfinite(s).all() or
        not np.isfinite(r).all() or max_sweeps<1 or not np.isfinite(tolerance) or tolerance<=0):
        raise ValueError('Finite square contact system and positive iteration controls required')
    diagonal=np.diag(s)
    incompatible=np.flatnonzero((diagonal<=0)&(r>1e-8))
    if len(incompatible):
        row=int(incompatible[0])
        raise ValueError(f'Wall constraint incompatible with divergence and fixed geometry: row={row}, diagonal={diagonal[row]}, required={r[row]} cm')
    lam=np.zeros(len(r)) if initial is None else np.asarray(initial,float).copy()
    if lam.shape!=r.shape or not np.isfinite(lam).all() or (lam<0).any():raise ValueError('Finite nonnegative warm multipliers required')
    residual=r-s@lam if initial is not None else r.copy();work=np.empty_like(r);kkt=0.
    for sweep in range(max_sweeps):
        for row in range(len(r)):
            if diagonal[row]<=0:continue
            updated=max(0,lam[row]+residual[row]/diagonal[row]);change=updated-lam[row]
            if change:
                lam[row]=updated
                np.multiply(s[:,row],change,out=work)
                np.subtract(residual,work,out=residual)
        kkt=float(np.max(np.where(lam>0,abs(residual),np.maximum(residual,0)),initial=0))
        if kkt<=tolerance:break
    # Recompute independently: incremental residual drift must not turn a
    # numerically inconsistent solution into a convergence claim.
    actual=r-s@lam
    actual_kkt=float(np.max(np.where(lam>0,abs(actual),np.maximum(actual,0)),initial=0))
    return lam,dict(converged=kkt<=tolerance and actual_kkt<=tolerance,
        dual_sweeps=sweep+1,dual_kkt_error_cm=kkt,recomputed_dual_kkt_error_cm=actual_kkt,
        incremental_residual_drift_cm=float(abs(actual-residual).max(initial=0)))
