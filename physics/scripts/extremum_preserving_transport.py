"""Research EP donor transport; not a pressure geometry or gameplay switch.

Slope: Sekora/Colella arXiv:0903.4200v2, equations 35--51, C_VL=1.25.
Only that slope operator is used, not the paper's full MUSCL/PPM algorithm.
An independent |dh| <= 2h reconstruction constraint ensures nonnegative
depth endpoints, without changing any cell average. Hydrostatic cuts retain
the two reconstructed bed sides. Original MC pressure geometry is unchanged.
The paper does not supply positivity for this coupled river model.
"""
from fractions import Fraction
import numpy as np
from hydrostatic_energy_transport import HydrostaticEnergyTransport
from total_depth_bank_replay import mc


def ep_slope(value,axis,other=None):
    back=value-np.roll(value,1,axis)
    front=np.roll(value,-1,axis)-value
    if other is not None:
        back+=other-np.roll(other,1,axis)
        front+=np.roll(other,-1,axis)-other
    far_back=np.roll(back,1,axis);far_front=np.roll(front,-1,axis)
    center=.5*(back+front);curvature=front-back
    sign=np.sign(curvature)
    bound=np.minimum(abs(curvature),np.minimum(
        np.maximum(sign*(back-far_back),0),np.maximum(sign*(far_front-front),0)))
    # Compare signs, not products: tiny-depth differences must not underflow
    # away the extremum predicate.
    opposite=lambda a,b: ((a<0)&(b>0))|((a>0)&(b<0))
    extremum=opposite(back,front)|opposite(far_back,far_front)
    edge=np.where(sign*np.sign(center)<0,abs(back),abs(front))
    limit=np.where(extremum,np.minimum(1.875*bound,2*edge),2*np.minimum(abs(back),abs(front)))
    return np.sign(center)*np.minimum(abs(center),limit)


def exact_slope(values):
    mm,m,c,p,pp=values
    back=c-m;front=p-c;far_back=m-mm;far_front=pp-p
    center=(back+front)/2;curve=front-back
    sign=lambda x: 1 if x>0 else -1 if x<0 else 0
    if min(back*front,far_back*far_front)<0:
        s=sign(curve)
        bound=min(abs(curve),max(s*(back-far_back),0),max(s*(far_front-front),0))
        edge=abs(back) if s*center<0 else abs(front)
        limit=min(Fraction(15,8)*bound,2*edge)
    else:limit=2*min(abs(back),abs(front))
    return sign(center)*min(abs(center),limit)


class ExtremumPreservingTransport(HydrostaticEnergyTransport):
    slope=staticmethod(ep_slope)
    exact_limiter=staticmethod(exact_slope)

    @classmethod
    def face_heights(cls,h,b,axis):
        # The EP stencil is five cells. Do not inspect across an exactly dry
        # intermediate cell to restore a slope on the far side of a dry gap.
        wet=(h>0)&(np.roll(h,1,axis)>0)&(np.roll(h,-1,axis)>0)
        wide=wet&(np.roll(h,2,axis)>0)&(np.roll(h,-2,axis)>0)
        # Preserve the original connected three-cell reconstruction when EP's
        # wider support is interrupted. Do not enlarge the first-order band.
        dh=np.where(wide,cls.slope(h,axis),mc(h,axis,True))*wet
        de=np.where(wide,cls.slope(h,axis,other=b),mc(h,axis,True,other=b))*wet
        dh=np.sign(dh)*2*np.minimum(.5*abs(dh),h)
        ha=h+.5*dh;hb=np.roll(h-.5*dh,-1,axis)
        bed_slope=de-dh
        jump=(np.roll(b,-1,axis)-b)-.5*(bed_slope+np.roll(bed_slope,-1,axis))
        before_a=ha-np.maximum(jump,0);before_b=hb-np.maximum(-jump,0)
        fa=np.maximum(before_a,0);fb=np.maximum(before_b,0)
        # Exact same EP polynomial on represented inputs at cancellation-prone
        # cuts. This is precision selection, not a wet/dry threshold or repair.
        scale=abs(h)+abs(np.roll(h,-1,axis))+abs(jump)+abs(bed_slope)+abs(np.roll(bed_slope,-1,axis))
        bound=64*np.finfo(float).eps*scale
        risk=(abs(before_a)<=bound)|(abs(before_b)<=bound)
        cache={}
        def polynomial(point):
            if point not in cache:
                points=[]
                for shift in (-2,-1,0,1,2):
                    q=list(point);q[axis]=(q[axis]+shift)%h.shape[axis];points.append(tuple(q))
                hs=[Fraction(float(h[q])) for q in points]
                bs=[Fraction(float(b[q])) for q in points]
                d=e=Fraction(0)
                if all(v>0 for v in hs[1:4]):
                    def slope(values):
                        if all(v>0 for v in hs):return cls.exact_limiter(values)
                        back=values[2]-values[1];front=values[3]-values[2]
                        if back>0 and front>0:return min(2*back,(back+front)/2,2*front)
                        if back<0 and front<0:return max(2*back,(back+front)/2,2*front)
                        return Fraction(0)
                    d=slope(hs);d=max(-2*hs[2],min(2*hs[2],d))
                    e=slope([a+z for a,z in zip(hs,bs)])
                cache[point]=(hs[2],bs[2],d,e)
            return cache[point]
        for point in map(tuple,np.argwhere(risk)):
            other=list(point);other[axis]=(other[axis]+1)%h.shape[axis];other=tuple(other)
            a,za,da,ea=polynomial(point);c,zc,dc,ec=polynomial(other)
            dz=zc-za-(ea-da+ec-dc)/2
            fa[point]=float(max(0,a+da/2-max(0,dz)))
            fb[point]=float(max(0,c-dc/2-max(0,-dz)))
        return fa,fb
