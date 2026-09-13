"""Reusable CPU pressure/contact reference for a fixed geometric field.

Cache the pressure factorization and unchanged contact Schur columns across
geometry iterations. Changing a contact row invalidates the column cache;
changing boundary/mobility requires a new system. Exactly identical rows share
the strongest bound; the final field is checked against every original row.
This is a validation reference, not a real-time implementation.
"""
import time
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
from liquid_compatible_projection import constrain_velocity
from liquid_contact_dual import solve_contact_dual
from liquid_contact_psor import solve_contact_psor
from liquid_contact_active_set import polish_contact_dual


def unique_contact_rows(matrix,lower):
    """Exact algebraic reduction only: same coefficients, strongest bound.

    No approximate normals, spatial bins or rank tolerances. Thus no different
    physical plane can disappear just because it is close to another plane.
    """
    b=matrix.tocsr(copy=True);b.sum_duplicates();b.eliminate_zeros();b.sort_indices()
    c=np.asarray(lower,float)
    if c.shape!=(b.shape[0],) or not np.isfinite(c).all():raise ValueError('Matching finite contact bounds required')
    groups={};winners=[]
    for row in range(b.shape[0]):
        lo,hi=b.indptr[row:row+2]
        key=(b.indices[lo:hi].tobytes(),b.data[lo:hi].tobytes())
        group=groups.get(key)
        if group is None:groups[key]=len(winners);winners.append(row)
        elif c[row]>c[winners[group]]:winners[group]=row
    return np.asarray(winners,dtype=int)


class ContactSystem:
    def __init__(self,boundary,spacing,mobility=None,*,relaxation=1.,active_set=False):
        started=time.perf_counter();b=np.asarray(boundary,float);h=np.asarray(spacing,float)
        if not np.isfinite(relaxation) or not 0<relaxation<2:raise ValueError('Relaxation must be in (0,2)')
        self.relaxation=float(relaxation)
        self.active_set=active_set
        if b.ndim!=4 or b.shape[-1]!=4 or h.shape!=(3,) or not np.isfinite(h).all() or (h<=0).any():
            raise ValueError('Matching boundary and finite positive spacing required')
        self.shape=b.shape[:-1]
        _,m,self.fluid=constrain_velocity(np.zeros((*self.shape,3)),b)
        if mobility is not None:
            m=np.asarray(mobility,float).copy()
            if m.shape!=(*self.shape,3) or not np.isin(m,[0,1]).all():raise ValueError('Matching binary mobility required')
            if np.any(m[np.rint(b[...,3])==1]!=0):raise ValueError('Solid displacement nodes must remain fixed')
        self.mobility=m;f=np.flatnonzero(self.fluid);self.fluid_indices=f
        if not len(f):raise ValueError('A pressure-fluid domain is required')
        z,y,x=np.unravel_index(f,self.shape);cells=np.array(self.shape[::-1]);coords=np.column_stack((x,y,z))
        if ((coords<2)|(coords>=cells-2)).any():raise ValueError('Complete two-cell pressure support required')
        rows=[];cols=[];values=[];mobile=m.reshape(-1,3)
        for c,stride in enumerate([1,cells[0],cells[0]*cells[1]]):
            for sign in (-1,1):
                node=f+sign*stride;weight=sign*mobile[node,c]/(2*h[c]);use=weight!=0
                rows.extend(np.flatnonzero(use));cols.extend(node[use]*3+c);values.extend(weight[use])
        self.D=sparse.csr_matrix((values,(rows,cols)),shape=(len(f),m.size))
        # Do not add diagonal regularization to hide a singular physical system.
        self.factor=splu((self.D@self.D.T).tocsc())
        self.factor_seconds=time.perf_counter()-started
        self._indices=None;self._weights=None;self._schur=None;self._dual=None

    def solve(self,target,indices,weights,lower,*,max_sweeps=30000):
        started=time.perf_counter();t=np.asarray(target,float)
        raw_indices=np.asarray(indices);ii=np.asarray(indices,int);ww=np.asarray(weights,float);c=np.asarray(lower,float)
        if t.shape!=self.shape or not np.isfinite(t).all() or np.any(t[~self.fluid]!=0):raise ValueError('Finite fluid-only target required')
        if (ii.ndim!=2 or not np.array_equal(raw_indices,ii) or ww.shape!=ii.shape or c.shape!=(len(ii),) or
            (ii<0).any() or (ii>=self.mobility.size).any() or not np.isfinite(ww).all() or not np.isfinite(c).all()):
            raise ValueError('Matching finite contact rows with integral indices required')
        if np.any(ww[self.mobility.ravel()[ii]==0]!=0):raise ValueError('Contact rows must not move fixed nodes')
        B=sparse.csr_matrix((ww.ravel(),(np.repeat(np.arange(len(ii)),ii.shape[1]),ii.ravel())),shape=(len(ii),self.mobility.size))
        B.eliminate_zeros();full_B=B;full_c=c
        winners=unique_contact_rows(B,c);B=B[winners];c=c[winners];ii=ii[winners];ww=ww[winners]
        K=(self.D@B.T).tocsc();rhs=t.ravel()[self.fluid_indices]
        p0=self.factor.solve(rhs);delta0=np.asarray(self.D.T@p0).ravel();r=c-np.asarray(B@delta0).ravel()
        reused=0
        if self._indices is not None and len(ii)>=len(self._indices):
            n=len(self._indices)
            if np.array_equal(ii[:n],self._indices) and np.array_equal(ww[:n],self._weights):reused=n
        S=(B@B.T).toarray()
        if reused:S[:reused,:reused]=self._schur
        for first in range(reused,len(ii),16):
            last=min(first+16,len(ii));columns=K[:,first:last].toarray()
            S[:,first:last]-=K.T@self.factor.solve(columns)
        if reused:S[reused:,:reused]=S[:reused,reused:].T
        asymmetry=float(abs(S-S.T).max(initial=0));S=(S+S.T)/2
        preparation_seconds=time.perf_counter()-started;dual_started=time.perf_counter()
        initial=np.zeros(len(ii))
        if reused:initial[:reused]=self._dual
        seed_sweeps=min(max_sweeps,1024) if self.active_set else max_sweeps
        if self.relaxation==1.:lam,dual=solve_contact_dual(S,r,max_sweeps=seed_sweeps,initial=initial)
        else:lam,dual=solve_contact_psor(S,r,max_sweeps=seed_sweeps,initial=initial,relaxation=self.relaxation)
        if self.active_set and not dual['converged']:
            seed=dual;lam,polished=polish_contact_dual(S,r,lam)
            dual=dict(polished,coordinate_seed=seed,dual_sweeps=seed['dual_sweeps'],
                dual_kkt_error_cm=polished['recomputed_dual_kkt_error_cm'])
        # Publish a consistent cache only after the dual call returns; a rejected
        # incompatible system must not leave new columns with old multipliers.
        self._indices=ii.copy();self._weights=ww.copy();self._schur=S.copy()
        self._dual=lam.copy()
        dual_seconds=time.perf_counter()-dual_started
        p=self.factor.solve(rhs-K@lam)
        field=np.asarray(self.D.T@p+B.T@lam).reshape(self.mobility.shape)
        error=np.asarray(self.D@field.ravel()).ravel()-rhs
        gap=full_c-np.asarray(full_B@field.ravel()).ravel();violation=np.maximum(gap,0)
        full_lam=np.zeros(len(full_c));full_lam[winners]=lam
        full_kkt=float(np.max(np.where(full_lam>0,abs(gap),np.maximum(gap,0)),initial=0))
        report=dict(dual,converged=dual['converged'] and full_kkt<=1e-7 and float(abs(error).max(initial=0))<=1e-5 and float(violation.max(initial=0))<=1e-6,
            relaxation=self.relaxation,
            active_set_refinement=self.active_set,
            pressure_unknowns=len(self.fluid_indices),contact_rows=len(full_c),unique_contact_rows=len(ii),
            exact_duplicate_rows=len(full_c)-len(ii),active_contact_rows=int((lam>0).sum()),full_contact_kkt_error_cm=full_kkt,
            warm_contact_rows=reused,
            reused_schur_columns=reused,new_schur_columns=len(ii)-reused,
            pressure_factorization_seconds=self.factor_seconds,contact_preparation_seconds=preparation_seconds,
            dual_seconds=dual_seconds,total_solve_seconds=time.perf_counter()-started,
            schur_symmetry_error=asymmetry,maximum_density_equation_error=float(abs(error).max(initial=0)),
            maximum_boundary_violation_cm=float(violation.max(initial=0)),native_integrated=False)
        return field,report
