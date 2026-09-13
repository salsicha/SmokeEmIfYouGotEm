"""Piecewise-affine bed along XY rays through the unchanged registered mesh.

Triangle edges are explicit integration boundaries, not a resampled terrain.
No short interval is discarded. Duplicate edge crossings merely make empty
intervals; shared-edge rays are partitioned once rather than counted twice.
"""
import numpy as np


def bed_ray_intervals(sampler,start,end,*,maximum_nominal_span=8):
    a=np.asarray(start,float);b=np.asarray(end,float)
    if (a.ndim!=2 or a.shape[1]!=2 or b.shape!=a.shape or
            not np.isfinite(a).all() or not np.isfinite(b).all() or
            not isinstance(maximum_nominal_span,int) or maximum_nominal_span<1):
        raise ValueError('Finite paired ENU XY rays and bounded search required')
    if not len(a):return (np.empty(0,dtype=int),)+(np.empty(0),)*4
    xy=np.concatenate((a,b))
    if (np.any(xy[:,0]<sampler.east[0]+sampler.dx/2) or np.any(xy[:,0]>sampler.east[-1]-sampler.dx/2) or
            np.any(xy[:,1]<sampler.north[-1]+sampler.dy/2) or np.any(xy[:,1]>sampler.north[0]-sampler.dy/2)):
        raise ValueError('Ray leaves the guaranteed registered-mesh interior')
    c0=np.floor((a[:,0]-sampler.east[0])/sampler.dx).astype(int)
    c1=np.floor((b[:,0]-sampler.east[0])/sampler.dx).astype(int)
    r0=np.floor((sampler.north[0]-a[:,1])/sampler.dy).astype(int)
    r1=np.floor((sampler.north[0]-b[:,1])/sampler.dy).astype(int)
    if np.any(abs(c1-c0)>maximum_nominal_span) or np.any(abs(r1-r0)>maximum_nominal_span):
        raise ValueError('Ray exceeds the bounded triangle search span')
    cmin=np.minimum(c0,c1)-1;rmin=np.minimum(r0,r1)-1
    nc=abs(c1-c0)+3;nr=abs(r1-r0)+3;travel=b-a
    cuts=[np.zeros(len(a)),np.ones(len(a))]
    for dr in range(int(nr.max())):
        for dc in range(int(nc.max())):
            rows=rmin+dr;cols=cmin+dc
            ids=np.flatnonzero((dr<nr)&(dc<nc)&(rows>=0)&(rows<sampler.rows-1)&(cols>=0)&(cols<sampler.cols-1))
            for side in (0,1):
                faces=rows[ids]*(sampler.cols-1)+cols[ids]+side*sampler.quads
                p,q,s=(sampler.xyz[sampler.faces[faces,j],:2] for j in range(3))
                u=q-p;v=s-p;offset=a[ids]-p;d=travel[ids]
                det=u[:,0]*v[:,1]-u[:,1]*v[:,0]
                x=(offset[:,0]*v[:,1]-offset[:,1]*v[:,0])/det
                y=(u[:,0]*offset[:,1]-u[:,1]*offset[:,0])/det
                dx=(d[:,0]*v[:,1]-d[:,1]*v[:,0])/det
                dy=(u[:,0]*d[:,1]-u[:,1]*d[:,0])/det
                lo=np.zeros(len(ids));hi=np.ones(len(ids));valid=np.ones(len(ids),bool)
                for value,slope in ((x,dx),(y,dy),(1-x-y,-dx-dy)):
                    moving=slope!=0;cross=np.divide(-value,slope,out=np.zeros_like(value),where=moving)
                    lo=np.where(slope>0,np.maximum(lo,cross),lo)
                    hi=np.where(slope<0,np.minimum(hi,cross),hi)
                    valid&=moving|(value>=0)
                valid&=lo<hi
                for fraction in (lo,hi):
                    cut=np.full(len(a),np.inf);cut[ids[valid]]=fraction[valid];cuts.append(cut)
    cuts=np.sort(np.stack(cuts,axis=1),axis=1)
    low=cuts[:,:-1];high=cuts[:,1:];parents,columns=np.nonzero(np.isfinite(high)&(high>low))
    low=low[parents,columns];high=high[parents,columns]
    # Select one exact face at each subinterval midpoint. The mesh is a
    # continuous height graph; both faces agree on a ray lying on their edge.
    mid=(low+high)/2;points=a[parents]+mid[:,None]*travel[parents]
    height,normal=sampler.sample(points[:,0],points[:,1],with_normals=True)
    slope=-np.sum(normal[:,:2]*travel[parents],axis=1)/normal[:,2]
    return parents,low,high,height+(low-mid)*slope,height+(high-mid)*slope
