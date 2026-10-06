"""Compact interpolation compatible with a collocated centered divergence.

Average adjacent collocated components onto faces, then use cubic normal /
quadratic transverse B-splines. Equivalently the normal kernel is
K(r) = (B3(r-.5)+B3(r+.5))/2. Its derivative is
K'(r) = (B2(r+1)-B2(r-1))/2, so continuous divergence equals
quadratic interpolation of the grid's centered divergence on complete support.

This is an advection reference, not an APIC momentum-transfer replacement,
boundary condition, or a claim of exact finite-time volume preservation.
"""
from itertools import product
import numpy as np


def b2(r):
    a=abs(r)
    return np.where(a<.5,.75-r*r,.5*np.maximum(1.5-a,0)**2)


def db2(r):
    a=abs(r)
    return np.where(a<.5,-2*r,-np.sign(r)*np.maximum(1.5-a,0))


def b3(r):
    a=abs(r)
    return np.where(a<1,2/3-a*a+.5*a*a*a,np.maximum(2-a,0)**3/6)


def sample(points,grid,spacing,derivatives=False):
    points=np.asarray(points,float);grid=np.asarray(grid,float);h=np.asarray(spacing,float)
    if points.ndim!=2 or points.shape[1]!=3 or grid.ndim!=4 or grid.shape[-1]!=3 or h.shape!=(3,) or (h<=0).any() or not all(np.isfinite(a).all() for a in (points,grid,h)):
        raise ValueError('Finite points, vector grid and positive spacing required')
    q=points/h-.5;low=np.floor(q-.5).astype(int)-1
    if (low<0).any() or (low+4>=grid.shape[:3]).any():
        raise ValueError('Complete five-point support required')
    value=np.zeros_like(points);jac=np.zeros((len(points),3,3)) if derivatives else None
    for bit in product(range(5),repeat=3):
        # Union of the three 5x3x3 component supports is 81, not 125.
        if sum(b in (0,4) for b in bit)>1:continue
        index=low+bit;r=index-q;w=b2(r);normal=.5*(b3(r-.5)+b3(r+.5))
        v=grid[tuple(index.T)]
        for c in range(3):
            weights=w.copy();weights[:,c]=normal[:,c]
            value[:,c]+=v[:,c]*weights.prod(axis=1)
            if derivatives:
                for a in range(3):
                    dw=-(.5*(b2(r[:,a]+1)-b2(r[:,a]-1)) if a==c else db2(r[:,a]))/h[a]
                    jac[:,c,a]+=v[:,c]*dw*np.prod(np.delete(weights,a,axis=1),axis=1)
    return (value,jac) if derivatives else value


def midpoint(points,grid,spacing,dt):
    if not np.isfinite(dt) or dt<=0:raise ValueError('Positive finite time step required')
    points=np.asarray(points,float)
    first=sample(points,grid,spacing)
    return points+dt*sample(points+.5*dt*first,grid,spacing)


def sample_compact(points, grid, spacing, derivatives=False):
    """C0 transport: averaged quadratic normal / tent transverse kernels.

    K(r)=(B2(r-.5)+B2(r+.5))/2, K'=(B1(r+1)-B1(r-1))/2.
    Thus divergence commutes with *tent* interpolation of centered grid D.
    The union of 4x2x2 component supports requires 32 vector loads (vs 81
    for the smoother cubic/quadratic variant above). This changes position
    transport only, not particle momentum, P2G mass or boundary conditions.
    """
    points=np.asarray(points,float);grid=np.asarray(grid,float);h=np.asarray(spacing,float)
    if points.ndim!=2 or points.shape[1]!=3 or grid.ndim!=4 or grid.shape[-1]!=3 or h.shape!=(3,) or (h<=0).any() or not all(np.isfinite(a).all() for a in (points,grid,h)):
        raise ValueError('Finite points, vector grid and positive spacing required')
    q=points/h-.5;low=np.floor(q).astype(int)-1
    if (low<0).any() or (low+3>=grid.shape[:3]).any():
        raise ValueError('Complete four-point support required')
    value=np.zeros_like(points);jac=np.zeros((len(points),3,3)) if derivatives else None
    for bit in product(range(4),repeat=3):
        if sum(b in (0,3) for b in bit)>1:continue
        index=low+bit;r=index-q;w=np.maximum(1-abs(r),0)
        normal=.5*(b2(r-.5)+b2(r+.5));v=grid[tuple(index.T)]
        for c in range(3):
            weights=w.copy();weights[:,c]=normal[:,c]
            value[:,c]+=v[:,c]*weights.prod(axis=1)
            if derivatives:
                for a in range(3):
                    derivative=(.5*(np.maximum(1-abs(r[:,a]+1),0)-np.maximum(1-abs(r[:,a]-1),0))
                                if a==c else np.where(abs(r[:,a])<1,-np.sign(r[:,a]),0))
                    jac[:,c,a]-=v[:,c]*derivative/h[a]*np.prod(np.delete(weights,a,axis=1),axis=1)
    return (value,jac) if derivatives else value
