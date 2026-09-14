"""Experimental dynamically normalized PCG, same operator and 40-iteration budget.

Residual/search direction share a moving power-of-two scale. The iterate stays
in original units. This is only an arithmetic change to CG; it does not discard
small RHS components or alter the physical matrix. No global initial-RHS norm
early exit is used: that exit hides important forces in captured thin cases.
"""
import numpy as np


def solve(system,rhs,iterations=40,*,preconditioner='diagonal',arithmetic=np.float64):
    if iterations!=40 or rhs.shape!=(*system.h.shape,2) or not np.isfinite(rhs).all():
        raise ValueError('Invalid range-PCG input or iteration budget')
    cast=lambda value:np.asarray(value,dtype=arithmetic)
    peak=float(abs(rhs).max())
    if peak==0:return np.zeros_like(rhs),dict(iterations=0,relative_residual=0.)
    scale=float(np.ldexp(1.,np.frexp(peak)[1]-1))
    value=cast(np.zeros_like(rhs));residual=cast(rhs/scale)
    z=cast(system.precondition(residual,preconditioner));direction=z.copy()
    rz=float(np.sum(cast(residual*z),dtype=arithmetic));completed=0
    scales=[scale]
    for _ in range(iterations):
        if rz==0:break
        applied=cast(system.apply(direction))
        denominator=float(np.sum(cast(direction*applied),dtype=arithmetic))
        if not np.isfinite(denominator) or denominator<=0:raise ValueError('Invalid range-PCG direction')
        alpha=cast(rz/denominator)
        value=cast(value+cast(cast(alpha*direction)*scale))
        residual=cast(residual-cast(alpha*applied));completed+=1
        peak=float(abs(residual).max())
        if not np.isfinite(peak):raise ValueError('Nonfinite range-PCG residual')
        if peak==0:break
        ratio=float(np.ldexp(1.,np.frexp(peak)[1]-1))
        residual=cast(residual/ratio);scale*=ratio;scales.append(scale)
        z=cast(system.precondition(residual,preconditioner))
        next_rz=float(np.sum(cast(residual*z),dtype=arithmetic))
        # p_new=(z_old+beta*p_old)/ratio, beta=ratio^2*rz_new/rz_old.
        direction=cast(z+cast(cast(ratio*next_rz/rz)*direction));rz=next_rz
    initial_peak=float(abs(rhs).max())
    true_residual=system.apply(value.astype(float))/initial_peak-rhs/initial_peak
    normalized_rhs=rhs/initial_peak
    relative=float(np.linalg.norm(true_residual.ravel())/np.linalg.norm(normalized_rhs.ravel()))
    root=np.sqrt(system.h);root_scale=float(root.max()) or 1.
    physical_error=(root/root_scale)[...,None]*true_residual
    physical_rhs=(root/root_scale)[...,None]*normalized_rhs
    physical_scale=max(float(abs(physical_error).max()),float(abs(physical_rhs).max())) or 1.
    physical_norm=float(np.linalg.norm((physical_rhs/physical_scale).ravel()))
    return value.astype(float),dict(iterations=completed,relative_residual=relative,
        physical_relative_residual=float(np.linalg.norm((physical_error/physical_scale).ravel())/(physical_norm or 1)),
        minimum_recurrence_scale=min(scales),maximum_recurrence_scale=max(scales))
