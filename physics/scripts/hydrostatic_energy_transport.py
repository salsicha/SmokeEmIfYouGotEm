"""Research donor-face mass transport and its matching energy adjoint.

Use original unscaled MC h/eta hydrostatic cuts, and a depth-weighted face
velocity. Upwind retained height supplies nonnegative donor mass. Frozen at
the current state this defines a linear velocity-to-mass-rate map T; T.T is
assembled from the SAME faces. T.T*a / h is evaluated with algebraically
cancelled owner depth, including finite coefficients at an exactly dry owner.

The mass-only forward-Euler draining bound does not qualify pressure at dry
cells, energy in time, entropy/shocks, open boundaries or gameplay. This is a
new transport, not the original FV/Rusanov solver and not a native mode.
"""
import numpy as np
from total_depth_bank_replay import mc,hydrostatic_faces
from depth_weighted_scalar_gradient import ratio


def retained_over_total(retained,h,neighbor):
    scale=np.maximum(h,neighbor)
    r=np.divide(retained,scale,out=np.zeros_like(h),where=scale>0)
    denominator=np.divide(h,scale,out=np.zeros_like(h),where=scale>0)
    denominator+=np.divide(neighbor,scale,out=np.zeros_like(h),where=scale>0)
    value=np.divide(r,denominator,out=np.zeros_like(h),where=denominator>0)
    if not np.isfinite(value).all() or np.any((retained>0)&(value==0)):
        raise ValueError('Positive retained-face coefficient exceeds storage range')
    return value


class HydrostaticEnergyTransport:
    @staticmethod
    def face_heights(h,b,axis):
        wet=(h>0)&(np.roll(h,1,axis)>0)&(np.roll(h,-1,axis)>0)
        dh=mc(h,axis,True)*wet;de=mc(h,axis,True,other=b)*wet
        _,_,_,_,fa,fb=hydrostatic_faces(h,b,dh,de,axis,True,reconstruction=True)
        select=[slice(None),slice(None)];select[axis]=slice(1,None)
        return fa[tuple(select)],fb[tuple(select)]

    def __init__(self,depth,bed,velocity,dx,*,periodic):
        h=np.asarray(depth,dtype=float);b=np.asarray(bed,dtype=float);u=np.asarray(velocity,dtype=float)
        if (periodic is not True or h.ndim!=2 or not h.size or b.shape!=h.shape
                or u.shape!=(*h.shape,2) or not np.isfinite(h).all() or np.any(h<0)
                or not np.isfinite(b).all() or not np.isfinite(u).all() or not np.isfinite(dx) or dx<=0):
            raise ValueError('Registered finite nonnegative periodic mass control required')
        self.h=h.copy();self.h.flags.writeable=False;self.dx=float(dx);self.faces=[]
        outgoing=np.zeros_like(h)
        for component,axis in enumerate((1,0)):
            neighbor=np.roll(h,-1,axis)
            fa,fb=self.face_heights(h,b,axis)
            own=ratio(h,neighbor);other=ratio(neighbor,h)
            face_velocity=own*u[...,component]+other*np.roll(u[...,component],-1,axis)
            retained=np.where(face_velocity>=0,fa,fb)
            if h.shape[axis]==1:retained=np.zeros_like(retained)
            if np.any(retained<0) or not np.isfinite(retained).all():raise ValueError('Invalid original cut height')
            flux=retained*face_velocity
            normalized=retained_over_total(retained,h,neighbor)
            if not np.isfinite(flux).all():raise ValueError('Mass face flux exceeds storage range')
            outgoing+=(np.maximum(flux,0)+np.roll(np.maximum(-flux,0),1,axis))/self.dx
            face=dict(own=own,other=other,retained=retained,flux=flux,normalized=normalized)
            for array in face.values():array.flags.writeable=False
            self.faces.append(face)
        if np.any((h==0)&(outgoing>0)):raise ValueError('Exactly dry owner loses mass')
        active=outgoing>0
        self.draining_bound=float(np.min(h[active]/outgoing[active])) if np.any(active) else float('inf')
        self.mass_rate=self.apply(u);self.mass_rate.flags.writeable=False

    def apply(self,velocity):
        u=np.asarray(velocity,dtype=float)
        if u.shape!=(*self.h.shape,2) or not np.isfinite(u).all():raise ValueError('Invalid velocity action')
        result=np.zeros_like(self.h)
        for component,(axis,face) in enumerate(zip((1,0),self.faces)):
            flux=face['retained']*(face['own']*u[...,component]+face['other']*np.roll(u[...,component],-1,axis))
            result-=(flux-np.roll(flux,1,axis))/self.dx
        if not np.isfinite(result).all():raise ValueError('Mass rate exceeds storage range')
        return result

    def adjoint(self,scalar,*,normalized=False):
        a=np.asarray(scalar,dtype=float)
        if a.shape!=self.h.shape or not np.isfinite(a).all():raise ValueError('Invalid energy scalar')
        result=[]
        for axis,face in zip((1,0),self.faces):
            jump=(np.roll(a,-1,axis)-a)/self.dx
            if normalized:
                piece=face['normalized']*jump
                value=piece+np.roll(piece,1,axis)
            else:
                piece=face['retained']*jump
                value=face['own']*piece+np.roll(face['other']*piece,1,axis)
            result.append(value)
        result=np.stack(result,axis=-1)
        if not np.isfinite(result).all():raise ValueError('Energy adjoint exceeds storage range')
        return result

    def forward_euler_mass(self,dt):
        if not np.isfinite(dt) or dt<=0 or dt>self.draining_bound:
            raise ValueError('Step exceeds original donor draining bound')
        result=self.h+dt*self.mass_rate
        if np.any(result<0) or not np.isfinite(result).all():
            raise ValueError('Mass step loses positivity; no repair')
        return result
