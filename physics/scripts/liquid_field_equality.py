"""Minimum-change shared field with one exact linearized volume equality.

Project into a.u=b, then solve the unchanged unilateral contacts within that
equality's null space. Schur matrix is B B^T-(B a)(B a)^T/(a.a).
There is no regularization, shifted terrain or independent particle pushout.
The equality is only a linearization; nonlinear surface volume must be checked.
"""
import numpy as np


def project_field_equality(base,indices,weights,lower,equality,rhs,*,max_sweeps=128):
    from scipy import sparse
    from liquid_contact_psor import solve_contact_psor
    from liquid_contact_active_set import polish_contact_dual
    v=np.asarray(base,float);a=np.asarray(equality,float);ii=np.asarray(indices);w=np.asarray(weights,float);c=np.asarray(lower,float)
    if (a.shape!=v.shape or not all(np.isfinite(x).all() for x in (v,a,w,c)) or not np.isfinite(rhs) or
            ii.ndim!=2 or not np.issubdtype(ii.dtype,np.integer) or w.shape!=ii.shape or c.shape!=(len(ii),) or
            (ii<0).any() or (ii>=v.size).any() or max_sweeps<1):
        raise ValueError('Finite matching equality/contact system required')
    aa=float(np.sum(a*a))
    if not np.isfinite(aa) or aa<=0:raise ValueError('Volume equality has no finite mobile field sensitivity')
    projected=v+a*((rhs-float(np.sum(a*v)))/aa)
    if not len(ii):
        error=abs(float(np.sum(a*projected))-rhs)
        return projected,dict(converged=error<=1e-7,equality_error=error,contact_rows=0,maximum_contact_violation_cm=0.)
    B=sparse.csr_matrix((w.ravel(),(np.repeat(np.arange(len(ii)),ii.shape[1]),ii.ravel())),shape=(len(ii),v.size))
    B.sum_duplicates();B.eliminate_zeros();ba=np.asarray(B@a.ravel()).ravel()
    S=(B@B.T).toarray()-np.outer(ba,ba)/aa;target=c-np.asarray(B@projected.ravel()).ravel()
    lam,seed=solve_contact_psor(S,target,max_sweeps=max_sweeps)
    refinement=None
    if not seed['converged']:lam,refinement=polish_contact_dual(S,target,lam)
    field=projected+np.asarray(B.T@lam).reshape(v.shape)-a*(float(ba@lam)/aa)
    gap=c-np.asarray(B@field.ravel()).ravel();kkt=float(np.max(np.where(lam>0,abs(gap),np.maximum(gap,0)),initial=0))
    error=abs(float(np.sum(a*field))-rhs);violation=float(np.maximum(gap,0).max(initial=0))
    return field,dict(converged=kkt<=1e-7 and error<=1e-7,equality_error=error,contact_rows=len(ii),
        maximum_contact_violation_cm=violation,contact_kkt_error_cm=kkt,coordinate_seed=seed,active_set_refinement=refinement)
