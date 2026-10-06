"""Trilinear and quadratic affine velocity transfer, following APIC transfers.

The engine grid is collocated, not the paper's MAC grid. Constant particle
mass is assumed here; this does not validate river source/exit mass accounting.
Positions and spacing use the same arbitrary length unit; C has units 1/s.
For quadratic interpolation C=B D^-1, D=diag(h²/4), not a point derivative.
"""
import itertools
import numpy as np


def stencil(points,shape,spacing,quadratic=False):
    points=np.asarray(points,dtype=float);spacing=np.asarray(spacing,dtype=float)
    shape=np.asarray(shape,dtype=int)
    if points.ndim!=2 or points.shape[1]!=3 or spacing.shape!=(3,) or shape.shape!=(3,) or (spacing<=0).any() or not np.isfinite(points).all() or not np.isfinite(spacing).all():
        raise ValueError('Finite XYZ points and positive spacing required')
    q=points/spacing-.5;low=np.floor(q-(.5 if quadratic else 0)).astype(int);t=q-low
    reach=2 if quadratic else 1
    if (low<0).any() or (low+reach>=shape).any():
        raise ValueError('Complete interior support required; no clipped conservation claim')
    for bit in itertools.product(range(reach+1),repeat=3):
        bit=np.array(bit);index=low+bit
        r=bit-t
        axis_weight=np.where(abs(r)<.5,.75-r*r,.5*np.maximum(1.5-abs(r),0)**2) if quadratic else np.where(bit,t,1-t)
        weight=axis_weight.prod(axis=1);gradient=np.empty_like(points)
        for a in range(3):
            # Quadratic APIC moment B D^-1, D=diag(h²/4). This is not
            # the derivative of the interpolated velocity on a nonlinear field.
            gradient[:,a]=weight*4*r[:,a]/spacing[a] if quadratic else (2*bit[a]-1)*np.prod(np.delete(axis_weight,a,axis=1),axis=1)/spacing[a]
        yield index,weight,gradient,(index+.5)*spacing-points


def to_grid(points,velocity,affine,shape,spacing,quadratic=False):
    velocity=np.asarray(velocity,dtype=float);affine=np.asarray(affine,dtype=float)
    if velocity.shape!=np.shape(points) or affine.shape!=(len(points),3,3) or not np.isfinite(velocity).all() or not np.isfinite(affine).all():
        raise ValueError('Finite particle velocities and velocity-gradient matrices required')
    mass=np.zeros(shape);momentum=np.zeros((*shape,3))
    for index,weight,_,offset in stencil(points,shape,spacing,quadratic):
        key=tuple(index.T)
        np.add.at(mass,key,weight)
        np.add.at(momentum,key,weight[:,None]*(velocity+np.einsum('nij,nj->ni',affine,offset)))
    grid=np.divide(momentum,mass[...,None],out=np.zeros_like(momentum),where=mass[...,None]>0)
    return grid,mass


def to_particles(points,grid,spacing,quadratic=False):
    grid=np.asarray(grid,dtype=float)
    if grid.ndim!=4 or grid.shape[-1]!=3 or not np.isfinite(grid).all():
        raise ValueError('Finite XYZ-vector grid required')
    velocity=np.zeros_like(points,dtype=float);affine=np.zeros((len(points),3,3))
    for index,weight,gradient,_ in stencil(points,grid.shape[:3],spacing,quadratic):
        value=grid[tuple(index.T)]
        velocity+=weight[:,None]*value
        affine+=value[:,:,None]*gradient[:,None,:]
    return velocity,affine


def velocity_derivative(points,grid,spacing,quadratic=False):
    """Exact derivative of the interpolation, distinct from quadratic APIC C."""
    grid=np.asarray(grid,dtype=float);points=np.asarray(points,dtype=float)
    spacing=np.asarray(spacing,dtype=float)
    if grid.ndim!=4 or grid.shape[-1]!=3 or not np.isfinite(grid).all():
        raise ValueError('Finite XYZ-vector grid required')
    derivative=np.zeros((len(points),3,3))
    for index,_,tent_derivative,offset in stencil(points,grid.shape[:3],spacing,quadratic):
        value=grid[tuple(index.T)]
        dw=tent_derivative.copy()
        if quadratic:
            r=offset/spacing;a=abs(r)
            w=np.where(a<.5,.75-r*r,.5*np.maximum(1.5-a,0)**2)
            axis_derivative=np.where(a<.5,2*r,np.sign(r)*np.maximum(1.5-a,0))/spacing
            for axis in range(3):
                dw[:,axis]=axis_derivative[:,axis]*np.prod(np.delete(w,axis,axis=1),axis=1)
        derivative+=value[:,:,None]*dw[:,None,:]
    return derivative
