"""Exact clearance plane for a straight path crossing a raised mesh edge.

The plane through the original particle and the two edge vertices (raised by
the required vertical clearance) bounds safe path directions. Its inequality
has zero RHS and is independent of where along the path the edge is crossed.
This avoids repeatedly freezing an outdated contact-time fraction at a ridge.
"""
import numpy as np


def edge_visibility_planes(start,movement,edge_a,edge_b,clearance):
    p,d,a,b=(np.asarray(v,float) for v in (start,movement,edge_a,edge_b))
    skin=np.asarray(clearance,float)
    if (p.ndim!=2 or p.shape[1]!=3 or any(v.shape!=p.shape for v in (d,a,b)) or
        skin.shape!=(len(p),) or not all(np.isfinite(v).all() for v in (p,d,a,b,skin)) or (skin<0).any()):
        raise ValueError('Finite matching XYZ paths, edges and nonnegative clearance required')
    edge=b-a;offset=a-p
    cross=lambda x,y:x[:,0]*y[:,1]-x[:,1]*y[:,0]
    denominator=cross(d,edge);moving=denominator!=0
    time=np.divide(cross(offset,edge),denominator,out=np.full(len(p),np.nan),where=moving)
    along=np.divide(cross(offset,d),denominator,out=np.full(len(p),np.nan),where=moving)
    lifted_a=a.copy();lifted_b=b.copy();lifted_a[:,2]+=skin;lifted_b[:,2]+=skin
    normal=np.cross(lifted_b-p,lifted_a-p)
    normal=np.where((normal[:,2]<0)[:,None],-normal,normal)
    length=np.linalg.norm(normal,axis=1)
    valid=moving&(time>0)&(time<1)&(along>=-1e-9)&(along<=1+1e-9)&(normal[:,2]>0)&(length>0)
    normal=np.divide(normal,length[:,None],out=np.zeros_like(normal),where=(length>0)[:,None])
    return normal,valid,time,along
