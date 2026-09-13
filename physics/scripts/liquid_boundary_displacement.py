"""Geometric inequality constraints on the shared compact displacement field.

Rows constrain interpolated particle displacement, not individual positions.
This is a CPU reference for coupling exact bed/outer constraints to density
projection. It does not itself integrate native particles or prove convergence.
"""
from itertools import product
import numpy as np
from liquid_compatible_advection import b2
from liquid_compatible_projection import gradient,divergence,shift,constrain_velocity


def compact_rows(points, normals, cells, spacing, mobility):
    """Sparse B rows with B delta = n dot compact_sample(delta, position)."""
    p=np.asarray(points,float);n=np.asarray(normals,float);cells=np.asarray(cells,int);h=np.asarray(spacing,float)
    m=np.asarray(mobility,float)
    if (p.ndim!=2 or p.shape[1]!=3 or n.shape!=p.shape or cells.shape!=(3,) or h.shape!=(3,) or
        m.shape!=(*cells[::-1],3) or (h<=0).any() or not all(np.isfinite(a).all() for a in (p,n,h,m))):
        raise ValueError('Finite matching compact constraint field and geometry required')
    q=p/h-.5;low=np.floor(q).astype(int)-1
    if ((low<0)|(low+3>=cells)).any():raise ValueError('Complete boundary constraint interpolation support required')
    indices=[];weights=[]
    for bit in product(range(4),repeat=3):
        if sum(a in (0,3) for a in bit)>1:continue
        i=low+bit;r=i-q;w=np.maximum(1-abs(r),0);normal=.5*(b2(r-.5)+b2(r+.5))
        coefficients=np.column_stack((normal[:,0]*w[:,1]*w[:,2],w[:,0]*normal[:,1]*w[:,2],w[:,0]*w[:,1]*normal[:,2]))*n
        flat=((i[:,2]*cells[1]+i[:,1])*cells[0]+i[:,0])*3
        for c in range(3):
            index=flat+c;indices.append(index);weights.append(coefficients[:,c]*m.ravel()[index])
    return np.column_stack(indices),np.column_stack(weights)


def project_rows(field,indices,weights,lower,dual=None,sweeps=1):
    """Sequential Dykstra projections of B field >= lower, with warm duals.

    Each update modifies the shared field using B transpose. Overlapping
    particles therefore feel the correction; no direct particle pushout occurs.
    """
    v=np.asarray(field,float).copy();i=np.asarray(indices,int);w=np.asarray(weights,float);c=np.asarray(lower,float)
    if (i.ndim!=2 or w.shape!=i.shape or c.shape!=(len(i),) or (i<0).any() or (i>=v.size).any() or
        not all(np.isfinite(a).all() for a in (v,w,c))):raise ValueError('Finite valid sparse boundary constraints required')
    lam=np.zeros(len(i)) if dual is None else np.asarray(dual,float).copy()
    if lam.shape!=c.shape or not np.isfinite(lam).all():raise ValueError('Matching finite constraint dual required')
    norm=(w*w).sum(axis=1);flat=v.ravel()
    for sweep in range(sweeps):
        for row in range(len(i)):
            # Dykstra: undo this row's previous projection, then project again.
            value=flat[i[row]]-lam[row]*w[row]
            need=c[row]-float(value@w[row])
            if norm[row]==0:
                if need>1e-9:raise ValueError('Exact geometry constraint has no mobile grid support')
                continue
            change=max(need,0)/norm[row]
            flat[i[row]]=value+change*w[row];lam[row]=change
    violation=np.maximum(c-np.sum(flat[i]*w,axis=1),0)
    return v,lam,float(violation.max(initial=0))


def coupled_projection(target,boundary,spacing,indices,weights,lower,max_iterations=800,max_active_sets=24):
    """Minimum-norm field satisfying D delta=target and B delta>=lower.

    Solve the joint pressure/contact Schur system C M C^T with C=[D;B].
    An active set removes tensile contact multipliers and adds violated rows.
    This retains the full off-grid B/B^T pair rather than projecting particles
    or alternating many independent pressure solves. No native integration yet.
    """
    t=np.asarray(target,float);b=np.asarray(boundary,float);h=np.asarray(spacing,float)
    _,m,fluid=constrain_velocity(np.zeros((*t.shape,3)),b)
    i=np.asarray(indices,int);w=np.asarray(weights,float);c=np.asarray(lower,float)
    if t.shape!=fluid.shape or np.any(t[~fluid]!=0) or not np.isfinite(t).all():raise ValueError('Target on active fluid cells required')
    f=np.flatnonzero(fluid);diagonal=sum((shift(m[...,a],1,2-a)+shift(m[...,a],-1,2-a))/(4*h[a]**2) for a in range(3)).ravel()[f]
    active=np.ones(len(i),bool);history=[];field=np.zeros_like(m)
    for active_iteration in range(max_active_sets):
        chosen=np.flatnonzero(active);ii=i[chosen];ww=w[chosen];cc=c[chosen]
        diag=np.r_[diagonal,np.sum(ww*ww,axis=1)];rhs=np.r_[t.ravel()[f],cc]
        if np.any((diag<=0)&(abs(rhs)>1e-12)):raise ValueError('Joint constraints have incompatible zero support')
        inverse=np.divide(1,diag,out=np.zeros_like(diag),where=diag>0)
        def transpose(lam):
            p=np.zeros_like(t);p.ravel()[f]=lam[:len(f)]
            value=-m*gradient(p,h)
            if len(chosen):
                scatter=np.bincount(ii.ravel(),weights=(lam[len(f):,None]*ww).ravel(),minlength=value.size)
                value+=scatter.reshape(value.shape)
            return value
        def matrix(lam):
            value=transpose(lam)
            return np.r_[divergence(value,h).ravel()[f],np.sum(value.ravel()[ii]*ww,axis=1)]
        lam=np.zeros_like(rhs);r=rhs.copy();z=inverse*r;direction=z.copy();rz=float(r@z)
        initial=max(rz,1e-30);converged=rz==0
        for iteration in range(max_iterations):
            if rz<=initial*1e-20:converged=True;break
            ad=matrix(direction);den=float(direction@ad)
            if den<=0 or not np.isfinite(den):break
            alpha=rz/den;lam+=alpha*direction;r-=alpha*ad;z=inverse*r
            next_rz=float(r@z);direction=z+(next_rz/rz)*direction;rz=next_rz
        field=transpose(lam);eq=divergence(field,h).ravel()[f]-t.ravel()[f]
        actual=np.sum(field.ravel()[i]*w,axis=1);violation=np.maximum(c-actual,0)
        equality_max=float(abs(eq).max(initial=0));boundary_max=float(violation.max(initial=0))
        tensile=chosen[lam[len(f):]<-1e-7]
        history.append(dict(active_set=active_iteration,active_rows=len(chosen),pcg_iterations=iteration+1,
            pcg_converged=converged,maximum_density_equation_error=equality_max,
            maximum_boundary_violation_cm=boundary_max,tensile_rows=len(tensile)))
        if not converged:break
        if len(tensile):active[tensile]=False;continue
        violated=(~active)&(violation>1e-6)
        if violated.any():active[violated]=True;continue
        return field,dict(converged=equality_max<=1e-5 and boundary_max<=1e-6,history=history)
    return field,dict(converged=False,history=history)
