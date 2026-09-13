"""Volume-gradient quadrature split at scalar AND exact terrain contacts.

The callback supplies a piecewise-affine bed along each fixed-X ray. This
resolves Y discontinuities analytically; X convergence must still be checked
by the caller. All disconnected liquid intervals and explicit caps remain.
"""
import numpy as np
from liquid_split_volume_gradient import _corner_value
from liquid_bed_contour_intervals import bed_contour_intervals
from liquid_surface_volume_gradient import negative_length_gradient
from liquid_interface_volume import negative_lengths


def _validate_partition(ray,ta,tb,bl,br,n):
    ray=np.asarray(ray);ta=np.asarray(ta,float);tb=np.asarray(tb,float);bl=np.asarray(bl,float);br=np.asarray(br,float)
    if (ray.ndim!=1 or not np.issubdtype(ray.dtype,np.integer) or any(v.shape!=ray.shape for v in (ta,tb,bl,br)) or
            (ray<0).any() or (ray>=n).any() or not all(np.isfinite(v).all() for v in (ta,tb,bl,br)) or
            (ta<0).any() or (tb>1).any() or (tb<=ta).any()):raise ValueError('Invalid exact bed ray partition')
    order=np.lexsort((ta,ray));r=ray[order];a=ta[order];b=tb[order]
    first=np.r_[True,r[1:]!=r[:-1]];last=np.r_[r[1:]!=r[:-1],True]
    if (not len(r) or not np.array_equal(r[first],np.arange(n)) or np.any(a[first]!=0) or np.any(b[last]!=1) or
            np.any(a[1:][~first[1:]]!=b[:-1][~first[1:]])):
        raise ValueError('Incomplete or overlapping bed ray partition')
    return ray,ta,tb,bl,br


def _bed_edge_x_intervals(ext,lower,low,high,h,z,bed_segments):
    """Include bed and scalar contacts on both Y edges in the X partition."""
    n=len(ext);owner=np.tile(np.arange(n),2);yy=np.r_[low[:,1],high[:,1]]
    start=np.column_stack((low[owner,0],yy));end=np.column_stack((high[owner,0],yy))
    ray,ta,tb,bl,br=_validate_partition(*bed_segments(start,end),len(start))
    parent=owner[ray];width=high[parent,0]-low[parent,0]
    x0=low[parent,0]+ta*width;x1=low[parent,0]+tb*width;ty=yy[ray]/h[1]-.5-lower[parent,1]
    a=_corner_value(ext[parent],x0/h[0]-.5-lower[parent,0],ty)
    b=_corner_value(ext[parent],x1/h[0]-.5-lower[parent,0],ty)
    segment,sa,sb=bed_contour_intervals(a,b,z,bl,br)
    ids=np.r_[np.arange(n),np.arange(n),parent[segment],parent[segment]]
    cuts=np.r_[np.zeros(n),np.ones(n),ta[segment]+sa*(tb-ta)[segment],ta[segment]+sb*(tb-ta)[segment]]
    order=np.lexsort((cuts,ids));ids=ids[order];cuts=cuts[order]
    take=(ids[1:]==ids[:-1])&(cuts[1:]>cuts[:-1])
    return ids[:-1][take],cuts[:-1][take],cuts[1:][take]


def evaluate_bed_columns(corners,lower,centers,half,spacing,bed_segments,order):
    c=np.asarray(corners,float);h=np.asarray(spacing,float);n,nz,_=c.shape
    nodes,weights=np.polynomial.legendre.leggauss(order)
    ext=np.concatenate((1.5*c[:,:1]-.5*c[:,1:2],c,1.5*c[:,-1:]-.5*c[:,-2:-1]),axis=1)
    z=np.r_[0,(np.arange(nz)+.5)*h[2],nz*h[2]]
    low=centers-half;high=centers+half
    ids,xa,xb=_bed_edge_x_intervals(ext,lower,low,high,h,z,bed_segments)
    xp=low[ids,0,None]+(xa[:,None]+(xb-xa)[:,None]*(nodes+1)/2)*2*half[ids,0,None]
    xw=(xb-xa)[:,None]*half[ids,0,None]*weights
    parent=np.repeat(ids,order);xp=xp.ravel();xw=xw.ravel()
    volume=np.zeros((n,3));gradient=np.zeros((n,nz,4));queries=0;intervals=0;zero=0;ties=0
    for first in range(0,len(xp),1024):
        pp=parent[first:first+1024];xx=xp[first:first+1024];wx=xw[first:first+1024]
        start=np.column_stack((xx,low[pp,1]));end=np.column_stack((xx,high[pp,1]))
        ray,ta,tb,bl,br=_validate_partition(*bed_segments(start,end),len(start))
        tx=xx[ray]/h[0]-.5-lower[pp[ray],0]
        y0=low[pp[ray],1]+ta*2*half[pp[ray],1];y1=low[pp[ray],1]+tb*2*half[pp[ray],1]
        yl=_corner_value(ext[pp[ray]],tx,y0/h[1]-.5-lower[pp[ray],1])
        yr=_corner_value(ext[pp[ray]],tx,y1/h[1]-.5-lower[pp[ray],1])
        segment,sa,sb=bed_contour_intervals(yl,yr,z,bl,br);intervals+=len(segment)
        size=max(1,32768//order)
        for begin in range(0,len(segment),size):
            seg=segment[begin:begin+size];aa=sa[begin:begin+size];bb=sb[begin:begin+size]
            rr=ray[seg];ids=pp[rr];fraction=aa[:,None]+(bb-aa)[:,None]*(nodes+1)/2
            yy=y0[seg,None]+fraction*(y1-y0)[seg,None]
            txq=xx[rr,None]/h[0]-.5-lower[ids,0,None];tyq=yy/h[1]-.5-lower[ids,1,None]
            bed=bl[seg,None]+fraction*(br-bl)[seg,None];queries+=bed.size
            values=np.zeros((nz,len(ids),order));xy_weights=[]
            for k,(cx,cy) in enumerate(((0,0),(1,0),(0,1),(1,1))):
                w=(txq if cx else 1-txq)*(tyq if cy else 1-tyq);xy_weights.append(w)
                values+=c[ids,:,k].T[:,:,None]*w
            values=values.reshape(nz,-1)
            scalar=np.vstack((1.5*values[0]-.5*values[1],values,1.5*values[-1]-.5*values[-2]))
            length,derivative,diagnostic=negative_length_gradient(scalar,z,bed.ravel(),0,z[-1])
            zero+=diagnostic['zero_endpoint_rays'];ties+=diagnostic['zero_crossing_on_bed_rays']
            area=wx[rr,None]*(bb-aa)[:,None]*(y1-y0)[seg,None]*weights/2
            np.add.at(volume[:,0],ids,np.sum(length.reshape(len(ids),order)*area,axis=1))
            for k,(lower_z,upper_z) in enumerate(((0,.5*h[2]),(z[-1]-.5*h[2],z[-1])),1):
                part=negative_lengths(scalar,z,bed.ravel(),lower_z,upper_z).reshape(len(ids),order)
                np.add.at(volume[:,k],ids,np.sum(part*area,axis=1))
            raw=derivative[1:-1].copy();raw[0]+=1.5*derivative[0];raw[1]-=.5*derivative[0]
            raw[-1]+=1.5*derivative[-1];raw[-2]-=.5*derivative[-1]
            raw=raw.reshape(nz,len(ids),order).transpose(1,0,2)
            for k,w in enumerate(xy_weights):np.add.at(gradient[:,:,k],ids,np.sum(raw*(area*w)[:,None,:],axis=2))
    return volume,gradient,dict(queries=queries,x_intervals=len(parent)//order,y_intervals=intervals,
        zero_endpoint_rays=zero,zero_crossing_on_bed_rays=ties)
