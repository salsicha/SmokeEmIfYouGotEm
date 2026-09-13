"""Separable three-dimensional contact QPs for particle correction directions.

Enumerate active sets of at most three independent normals in R3. Unlike
cyclic projection, nearly parallel contacts do not need thousands of sweeps.
Every candidate is checked against every original inequality, with no diagonal
regularization, removed physical plane, position clamp or mass change.
"""
from itertools import combinations
import numpy as np


def project_contacts(base,indices,weights,lower,tolerance=1e-7):
    b=np.asarray(base,float);ii=np.asarray(indices);w=np.asarray(weights,float);c=np.asarray(lower,float)
    if (b.ndim!=2 or b.shape[1]!=3 or ii.shape!=w.shape or ii.ndim!=2 or ii.shape[1]!=3 or
            c.shape!=(len(ii),) or not all(np.isfinite(a).all() for a in (b,ii,w,c)) or
            not np.issubdtype(ii.dtype,np.integer) or (ii<0).any() or (ii>=b.size).any() or
            not np.array_equal(ii,ii[:,0,None]+np.arange(3)) or (ii[:,0]%3).any() or
            not np.isfinite(tolerance) or tolerance<=0):raise ValueError('Finite per-particle XYZ constraints required')
    out=b.copy();ids=ii[:,0]//3;max_stationarity=0.;max_complementarity=0.;max_rows=0
    owners,order,counts=np.unique(ids,return_inverse=True,return_counts=True)
    # Fast path: independent single-plane projections in one vector batch.
    single=counts[order]==1;rows=np.flatnonzero(single);norm=np.sum(w[rows]**2,axis=1)
    need=c[rows]-np.sum(b[ids[rows]]*w[rows],axis=1)
    if np.any((norm==0)&(need>tolerance)):raise ValueError('Infeasible zero-normal contact')
    lam=np.divide(np.maximum(need,0),norm,out=np.zeros_like(need),where=norm>0)
    out[ids[rows]]+=lam[:,None]*w[rows]
    for owner in owners[counts>1]:
        chosen=np.flatnonzero(ids==owner);a=w[chosen];rhs=c[chosen];x0=b[owner];max_rows=max(max_rows,len(chosen))
        if np.all(a@x0>=rhs-tolerance):continue
        best=None;cost=np.inf;dual=None;active=None
        for size in range(1,min(3,len(chosen))+1):
            for group in combinations(range(len(chosen)),size):
                selected=np.asarray(group);aa=a[selected]
                candidate_dual,_,rank,_=np.linalg.lstsq(aa@aa.T,rhs[selected]-aa@x0,rcond=None)
                if rank<size or np.any(candidate_dual<0):continue
                candidate=x0+aa.T@candidate_dual
                if np.any(a@candidate<rhs-tolerance):continue
                candidate_cost=float(np.sum((candidate-x0)**2))
                if candidate_cost<cost:best=candidate;cost=candidate_cost;dual=candidate_dual;active=selected
        if best is None:raise ValueError('No fully feasible three-dimensional contact active set')
        out[owner]=best
        max_stationarity=max(max_stationarity,float(abs(best-x0-a[active].T@dual).max(initial=0)))
        max_complementarity=max(max_complementarity,float(abs((a[active]@best-rhs[active])*dual).max(initial=0)))
    violation=float(np.maximum(c-np.sum(out[ids]*w,axis=1),0).max(initial=0))
    if violation>tolerance:raise ValueError('Projected contacts fail original full inequality set')
    return out,dict(constraints=len(ii),constrained_particles=len(owners),maximum_rows_per_particle=max(1 if len(ii) else 0,max_rows),
        maximum_constraint_violation_cm=violation,maximum_stationarity_error=max_stationarity,
        maximum_complementarity_error=max_complementarity)
