"""Exact centered-tent particle density objective, including partial solid support.

This is a position-level CPU reference, not a native pressure solver. It uses
every grid node touched by the conserved particle volumes. A fluid/air/solid
label cannot hide over-density. The fixed solid term is the actual bed-kernel
integral, not additional liquid. Underfilled surface support is not attracted.
"""
import numpy as np
from liquid_affine_transfer import stencil


def objective(points,cells,spacing,volumes,solid,*,derivatives=True):
    p=np.asarray(points,float);h=np.asarray(spacing,float);c=np.asarray(cells)
    v=np.asarray(volumes,float);s=np.asarray(solid,float)
    if (p.ndim!=2 or p.shape[1]!=3 or c.shape!=(3,) or h.shape!=(3,) or
            not np.isfinite(c).all() or (c!=np.floor(c)).any() or (c<2).any() or
            not np.isfinite(h).all() or (h<=0).any() or v.shape!=(len(p),) or
            not np.isfinite(v).all() or (v<=0).any() or s.shape!=tuple(c[::-1]) or
            not np.isfinite(s).all() or (s<0).any() or (s>1).any()):
        raise ValueError('Complete grid, positive conserved volumes and bed-kernel fractions required')
    c=c.astype(int);scale=v/np.prod(h);rho=np.zeros_like(s)
    for index,w,_,_ in stencil(p,c,h):
        np.add.at(rho,tuple(index[:,::-1].T),scale*w)
    residual=np.maximum(rho+s-1,0)
    result=dict(energy=.5*float(np.sum(residual**2)),particle_density=rho,
        represented_volume=float(v.sum()),deposited_volume=float(rho.sum()*np.prod(h)),
        maximum_total_density=float((rho+s).max(initial=0)),
        maximum_particle_density=float(rho.max(initial=0)),
        particles_on_tent_knots=int(np.any(p/h-.5==np.floor(p/h-.5),axis=1).sum()))
    if derivatives:
        gradient=np.zeros_like(p);diagonal=np.zeros_like(p)
        for index,_,dw,_ in stencil(p,c,h):
            key=tuple(index[:,::-1].T);jacobian=scale[:,None]*dw
            gradient+=residual[key][:,None]*jacobian
            # Diagonal of J_active^T J_active, not a new physical stiffness or
            # an epsilon-regularized Hessian. Zero-sensitivity axes stay zero.
            diagonal+=(residual[key]>0)[:,None]*jacobian**2
        result.update(gradient=gradient,gauss_newton_diagonal=diagonal)
    return result


def descent_direction(result,spacing,max_cells=.25,*,diagonal=False):
    """Mass-preserving direction; actual nonlinear energy/contact need line search."""
    g=np.asarray(result['gradient'],float);d=np.asarray(result['gauss_newton_diagonal'],float)
    h=np.asarray(spacing,float)
    if (g.ndim!=2 or g.shape[1]!=3 or d.shape!=g.shape or h.shape!=(3,) or
            not np.isfinite(g).all() or not np.isfinite(d).all() or (d<0).any() or
            not np.isfinite(h).all() or (h<=0).any() or not np.isfinite(max_cells) or max_cells<=0):
        raise ValueError('Finite derivatives, nonnegative sensitivity and positive step bound required')
    if np.any((d==0)&(g!=0)):raise ValueError('Nonzero gradient has zero sensitivity')
    direction=np.divide(-g,d,out=np.zeros_like(g),where=d>0) if diagonal else -g*h*h
    maximum=float(np.linalg.norm(direction/h,axis=1).max(initial=0))
    # One shared trust radius; no independent particle movement/volume clipping.
    if maximum>max_cells:direction*=max_cells/maximum
    return direction
