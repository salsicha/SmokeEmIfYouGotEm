"""Sparse-factorized CPU reference for the contact Schur complement.

For validation only; scipy is an optional workspace-local preprocessing
dependency, not an Unreal runtime dependency. Eliminates all pressure unknowns
before solving the small unilateral wall problem, avoiding an ill-conditioned
equality solve that falsely forces every detected contact to remain active.
"""
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
from liquid_compatible_projection import constrain_velocity


def geometric_position_mobility(boundary):
    """Fix solid nodes, but constrain nearby water through exact contact rows.

    The old stair-step velocity rule also froze fluid-node components adjacent
    to solids. That is an extra, axis-aligned constraint, not the bed's normal.
    This position-only alternative replaces it with the explicit B constraints.
    It does not change the native momentum projection or solid-node support.
    """
    b=np.asarray(boundary,float)
    if b.ndim!=4 or b.shape[-1]!=4 or not np.isfinite(b).all():raise ValueError('Finite XYZ/type boundary required')
    types=np.rint(b[...,3]).astype(int)
    if not np.isin(types,[0,1,2,3]).all():raise ValueError('Known boundary types required')
    return np.repeat((types!=1)[...,None],3,axis=-1).astype(float)


def solve(target,boundary,spacing,indices,weights,lower,max_sweeps=30000,mobility=None):
    t=np.asarray(target,float);b=np.asarray(boundary,float);h=np.asarray(spacing,float)
    if (t.ndim!=3 or h.shape!=(3,) or not np.isfinite(h).all() or (h<=0).any() or
        not np.isfinite(t).all() or max_sweeps<1):raise ValueError('Finite target, positive spacing and sweeps required')
    _,m,fluid=constrain_velocity(np.zeros((*t.shape,3)),b)
    if np.any(t[~fluid]!=0):raise ValueError('Density target must be zero outside fluid')
    if mobility is not None:
        m=np.asarray(mobility,float)
        if m.shape!=(*t.shape,3) or not np.isin(m,[0,1]).all():raise ValueError('Matching binary position mobility required')
        if np.any(m[np.rint(b[...,3])==1]!=0):raise ValueError('Solid displacement nodes must remain fixed')
    f=np.flatnonzero(fluid)
    z,y,x=np.unravel_index(f,t.shape);cells=np.array(t.shape[::-1]);coords=np.column_stack((x,y,z))
    if ((coords<2)|(coords>=cells-2)).any():raise ValueError('Pressure constraints need complete centered two-cell support')
    rows=[];cols=[];values=[];strides=[1,cells[0],cells[0]*cells[1]];mobile=m.reshape(-1,3)
    for c,stride in enumerate(strides):
        for sign in (-1,1):
            node=f+sign*stride;weight=sign*mobile[node,c]/(2*h[c]);use=weight!=0
            rows.extend(np.flatnonzero(use));cols.extend(node[use]*3+c);values.extend(weight[use])
    D=sparse.csr_matrix((values,(rows,cols)),shape=(len(f),m.size))
    A=(D@D.T).tocsc()
    # The actual free-surface domains supply pressure reference cells. A singular
    # closed component is rejected here, not regularized with invented leakage.
    factor=splu(A)
    ii=np.asarray(indices,int);ww=np.asarray(weights,float);c=np.asarray(lower,float)
    if (ii.ndim!=2 or ww.shape!=ii.shape or c.shape!=(len(ii),) or (ii<0).any() or (ii>=m.size).any() or
        not np.isfinite(ww).all() or not np.isfinite(c).all()):raise ValueError('Matching finite contact rows required')
    B=sparse.csr_matrix((ww.ravel(),(np.repeat(np.arange(len(ii)),ii.shape[1]),ii.ravel())),shape=(len(ii),m.size))
    B.eliminate_zeros();K=(D@B.T).tocsc();rhs=t.ravel()[f]
    p0=factor.solve(rhs);delta0=np.asarray(D.T@p0).ravel();r=c-np.asarray(B@delta0).ravel()
    S=(B@B.T).toarray()
    for first in range(0,len(ii),16):
        last=min(first+16,len(ii));columns=K[:,first:last].toarray()
        S[:,first:last]-=K.T@factor.solve(columns)
    asymmetry=float(abs(S-S.T).max(initial=0));S=(S+S.T)/2
    diagonal=np.diag(S);lam=np.zeros(len(ii));residual=r.copy();kkt=0
    incompatible=np.flatnonzero((diagonal<=0)&(r>1e-8))
    if len(incompatible):
        row=int(incompatible[0])
        raise ValueError(f'Wall constraint incompatible with divergence and fixed geometry: row={row}, diagonal={diagonal[row]}, required={r[row]} cm')
    for sweep in range(max_sweeps):
        for row in range(len(ii)):
            if diagonal[row]<=0:continue
            updated=max(0,lam[row]+residual[row]/diagonal[row]);change=updated-lam[row]
            if change:lam[row]=updated;residual-=S[:,row]*change
        kkt=float(np.max(np.where(lam>0,abs(residual),np.maximum(residual,0)),initial=0))
        if kkt<=1e-7:break
    p=factor.solve(rhs-K@lam);field=np.asarray(D.T@p+B.T@lam).reshape(m.shape)
    density_error=np.asarray(D@field.ravel()).ravel()-rhs
    violation=np.maximum(c-np.asarray(B@field.ravel()).ravel(),0)
    report=dict(converged=float(abs(density_error).max(initial=0))<=1e-5 and float(violation.max(initial=0))<=1e-6 and kkt<=1e-7,
        pressure_unknowns=len(f),contact_rows=len(ii),active_contact_rows=int((lam>0).sum()),dual_sweeps=sweep+1,
        dual_kkt_error_cm=kkt,schur_symmetry_error=asymmetry,maximum_density_equation_error=float(abs(density_error).max(initial=0)),
        maximum_boundary_violation_cm=float(violation.max(initial=0)),native_integrated=False)
    return field,report
