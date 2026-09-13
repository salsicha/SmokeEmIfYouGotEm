"""Pull a geometric scalar-volume gradient through the same finite water map.

At destination y, departure x solves x+delta(x)=y. Its derivative is
dx/d(delta) = -(I+grad(delta))^-1 S_x. Thus the field-volume derivative is
S_x^T[-(I+grad(delta))^-T grad(phi_old(x)) dV/dphi_new(y)].
This differentiates the actual inverse/resampling path, not a surface-height
offset or unrelated velocity field. Exact scalar-knot branches are reported;
the final nonlinear volume must still be measured and line-searched.
"""
import numpy as np
from liquid_correction_map import inverse_map
from liquid_compatible_advection import sample_compact
from liquid_affine_transfer import stencil
from liquid_shared_density import compact_adjoint


def map_volume_gradient(old_phi,delta,spacing,selected,scalar_gradient,mobility,*,batch_size=8192):
    phi=np.asarray(old_phi,float);d=np.asarray(delta,float);h=np.asarray(spacing,float)
    chosen=np.asarray(selected);g=np.asarray(scalar_gradient,float);m=np.asarray(mobility,float)
    if (phi.ndim!=3 or d.shape!=(*phi.shape,3) or chosen.shape!=phi.shape or chosen.dtype!=bool or
            g.shape!=phi.shape or m.shape!=d.shape or not np.isfinite(phi).all() or not np.isfinite(g).all() or
            not isinstance(batch_size,int) or batch_size<1):
        raise ValueError('Finite matching scalar/field/gradient and selected grid required')
    z,y,x=np.nonzero(chosen&(g!=0));result=np.zeros_like(d);knots=0;inverse_error=0.;minimum_det=np.inf
    for first in range(0,len(x),batch_size):
        last=min(first+batch_size,len(x));zz,yy,xx=z[first:last],y[first:last],x[first:last]
        destinations=(np.column_stack((xx,yy,zz))+.5)*h
        departures,valid,proof=inverse_map(destinations,d,h,tolerance=1e-9)
        if not valid.all():raise ValueError('Volume derivative has invalid inverse map')
        inverse_error=max(inverse_error,proof['maximum_valid_inverse_residual'])
        q=departures/h-.5;knots+=int(np.any(q==np.floor(q),axis=1).sum())
        gradient=np.zeros_like(departures)
        for index,_,dw,_ in stencil(departures,np.array(phi.shape[::-1]),h):
            gradient+=phi[tuple(index[:,::-1].T)][:,None]*dw
        _,jac=sample_compact(departures,d.transpose(2,1,0,3),h,derivatives=True);jac+=np.eye(3)
        det=np.linalg.det(jac);minimum_det=min(minimum_det,float(det.min()))
        if (det<=0).any():raise ValueError('Folded volume derivative map')
        values=-np.linalg.solve(jac.transpose(0,2,1),gradient[...,None])[...,0]*g[zz,yy,xx,None]
        result+=compact_adjoint(departures,values,np.array(phi.shape[::-1]),h,m,batch_size=batch_size)
    return result,dict(nonzero_selected_scalar_gradients=len(x),departures_on_scalar_knots=knots,
        maximum_inverse_residual=inverse_error,minimum_sampled_determinant=None if not np.isfinite(minimum_det) else minimum_det,
        derivative_of_same_finite_map=True,nonlinear_volume_still_requires_verification=True)
