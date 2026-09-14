"""Independent dense kinetic metric and its exact discrete directional rate.

For one pole lambda=1/3 this is the reconstructed SGN completed-square energy.
For the actual rational poles, S=cI+sum(w A^-1) and S^-1 is the kinetic metric
required by the frozen linear response. Extending that metric to nonlinear
states does NOT prove it is an invariant of the existing rational forcing.
Small fully-wet controls only: no dry normalization, boundary flux, native mode,
energy projection, added damping, or replacement of the two-pole solver.
"""
import numpy as np
from audit_difference_scalar_identities import face_matrices
from finite_depth_pressure_reference import LENGTHS, WEIGHTS


def tangent_matrices(tangent):
    """Explicit signed face accumulation, independent of vector rate actions."""
    g=tangent.geometry; n=g.h.size
    d=np.zeros((n,2*n)); e=np.zeros_like(d)
    indices=np.arange(n).reshape(g.h.shape)
    for component,(axis,edge,rate) in enumerate(zip((1,0),g.edges,tangent.edges)):
        for point in np.ndindex(g.h.shape):
            neighbor=list(point);neighbor[axis]=(neighbor[axis]+1)%g.h.shape[axis];neighbor=tuple(neighbor)
            i,j=int(indices[point]),int(indices[neighbor]); vi,vj=2*i+component,2*j+component
            aa,ab,own,other=(edge[key][point] for key in ('aa','ab','own','other'))
            at,bt,ot,tt,kt=(rate[key][point] for key in ('aa','ab','own','other','shared_b'))
            d[i,vi]+=(at*own+aa*ot)/g.dx;d[i,vj]+=(at*other+aa*tt)/g.dx
            d[j,vi]-=(bt*own+ab*ot)/g.dx;d[j,vj]-=(bt*other+ab*tt)/g.dx
            e[i,vi]-=kt/g.dx;e[i,vj]+=kt/g.dx
            e[j,vj]-=kt/g.dx;e[j,vi]+=kt/g.dx
    return d,e


def metric(geometry, tangent=None, *, rational=False):
    g=geometry;h=g.h.ravel()
    if not g.periodic or np.any(h<=0):
        raise ValueError('Energy control requires fully positive periodic geometry')
    d,e,*_=face_matrices(g)
    root=np.sqrt(h); inverse=np.repeat(1/root,2)
    w=root[:,None]*(h[:,None]*d-1.5*e)*inverse[None,:]
    v=root[:,None]*e*inverse[None,:]
    base=w.T@w+.75*v.T@v
    base_t=None
    if tangent is not None:
        if tangent.geometry is not g or tangent.one_sided:
            raise ValueError('Energy tangent must match stationary positive geometry')
        ht=tangent.mass_rate.ravel(); ell=ht/(2*h); column_ell=np.repeat(ell,2)
        dt,et=tangent_matrices(tangent)
        wt=ell[:,None]*w+root[:,None]*(ht[:,None]*d+h[:,None]*dt-1.5*et)*inverse[None,:]-w*column_ell
        vt=ell[:,None]*v+root[:,None]*et*inverse[None,:]-v*column_ell
        base_t=wt.T@w+w.T@wt+.75*(vt.T@v+v.T@vt)
    if not rational:
        return np.eye(2*h.size)+base/3,None if base_t is None else base_t/3
    # Sum of direct non-dispersive response and both actual pressure poles.
    # The stored weights sum to 14/15 up to their represented roundoff.
    s=(1-float(np.sum(WEIGHTS)))*np.eye(2*h.size)
    st=np.zeros_like(s)
    for length,weight in zip(LENGTHS,WEIGHTS):
        inverse_pole=np.linalg.solve(np.eye(2*h.size)+length*base,np.eye(2*h.size))
        s+=weight*inverse_pole
        if base_t is not None:st-=weight*length*(inverse_pole@base_t@inverse_pole)
    k=np.linalg.solve(s,np.eye(2*h.size))
    return k,None if base_t is None else -k@st@k


def energy(geometry, velocity, *, rational=False):
    u=np.asarray(velocity,dtype=float)
    if u.shape!=(*geometry.h.shape,2) or not np.isfinite(u).all():raise ValueError('Invalid energy velocity')
    k,_=metric(geometry,rational=rational)
    x=(np.sqrt(geometry.h)[...,None]*u).ravel()
    kinetic=.5*float(x@k@x)
    potential=float(np.sum(9.81*geometry.h*(.5*geometry.h+geometry.bed)))
    return (kinetic+potential)*geometry.dx**2


def energy_rate(geometry,tangent,velocity,momentum_rate,*,rational=False):
    h=geometry.h;ht=tangent.mass_rate;u=np.asarray(velocity,dtype=float);mt=np.asarray(momentum_rate,dtype=float)
    if u.shape!=(*h.shape,2) or mt.shape!=u.shape or not np.isfinite(u).all() or not np.isfinite(mt).all():
        raise ValueError('Invalid energy state/rate')
    k,kt=metric(geometry,tangent,rational=rational)
    root=np.sqrt(h)[...,None];x=(root*u).ravel()
    xt=((mt-.5*u*ht[...,None])/root).ravel()
    acceleration=float(xt@k@x);changing_metric=.5*float(x@kt@x)
    potential=float(np.sum(9.81*(h+geometry.bed)*ht))
    area=geometry.dx**2
    return dict(total=(acceleration+changing_metric+potential)*area,
        kinetic_state_rate=acceleration*area,kinetic_geometry_rate=changing_metric*area,
        potential_rate=potential*area,
        interpretation=('frozen-linear-response metric extended nonlinearly; invariant not established'
                        if rational else 'reconstructed classical SGN energy'))
