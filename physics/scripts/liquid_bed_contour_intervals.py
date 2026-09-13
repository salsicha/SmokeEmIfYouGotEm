"""Split an affine bed ray at exact scalar/bed contact transitions.

Within a fixed vertical slab, trilinear phi restricted to one XY ray and
its affine triangle bed is quadratic. Its real roots locate contact changes.
This only partitions integration intervals; it never changes phi or bed.
"""
import numpy as np


def quadratic_roots(a,b,c):
    a,b,c=np.broadcast_arrays(np.asarray(a,float),np.asarray(b,float),np.asarray(c,float))
    if not all(np.isfinite(v).all() for v in (a,b,c)):raise ValueError('Finite polynomial coefficients required')
    roots=np.full((*a.shape,2),np.inf)
    linear=(a==0)&(b!=0)
    np.divide(-c,b,out=roots[...,0],where=linear)
    discriminant=b*b-4*a*c
    active=(a!=0)&(discriminant>=0)
    radical=np.sqrt(np.maximum(discriminant,0))
    q=-.5*(b+np.copysign(radical,b))
    np.divide(q,a,out=roots[...,0],where=active)
    np.divide(c,q,out=roots[...,1],where=active&(q!=0))
    roots[...,1]=np.where(active&(q==0),0.,roots[...,1])
    return roots


def bed_contour_intervals(left,right,z,bed_left,bed_right):
    a=np.asarray(left,float);b=np.asarray(right,float);z=np.asarray(z,float)
    bl=np.asarray(bed_left,float);br=np.asarray(bed_right,float)
    if (a.ndim!=2 or b.shape!=a.shape or a.shape[1]<2 or z.shape!=(a.shape[1],) or
            bl.shape!=(len(a),) or br.shape!=bl.shape or (np.diff(z)<=0).any() or
            not all(np.isfinite(v).all() for v in (a,b,z,bl,br))):
        raise ValueError('Finite paired scalar/bed rays and increasing Z levels required')
    dv=b-a;db=br-bl
    scalar_roots=np.full(a.shape,np.inf)
    np.divide(-a,dv,out=scalar_roots,where=dv!=0)
    bed_roots=np.full(a.shape,np.inf)
    np.divide(z[None,:]-bl[:,None],db[:,None],out=bed_roots,where=db[:,None]!=0)
    dz=np.diff(z)[None,:];delta=a[:,1:]-a[:,:-1];delta_slope=dv[:,1:]-dv[:,:-1]
    offset=bl[:,None]-z[None,:-1]
    qa=db[:,None]*delta_slope/dz
    qb=dv[:,:-1]+(offset*delta_slope+db[:,None]*delta)/dz
    qc=a[:,:-1]+offset*delta/dz
    contacts=quadratic_roots(qa,qb,qc)
    valid=np.isfinite(contacts)&(contacts>0)&(contacts<1)
    # Avoid inf*0 while inspecting roots of inactive polynomial branches.
    height=bl[:,None,None]+np.where(valid,contacts,0)*db[:,None,None]
    valid&=(height>=z[None,:-1,None])&(height<=z[None,1:,None])
    contacts=np.where(valid,contacts,np.inf).reshape(len(a),-1)
    cuts=np.column_stack((np.zeros(len(a)),np.ones(len(a)),scalar_roots,bed_roots,contacts))
    cuts[(cuts<0)|(cuts>1)]=np.inf;cuts.sort(axis=1)
    low=cuts[:,:-1];high=cuts[:,1:];parent,column=np.nonzero(np.isfinite(high)&(high>low))
    return parent,low[parent,column],high[parent,column]
