"""Contour-split integration of the unchanged trilinear liquid volume gradient.

Split X at zero crossings of each captured/cap Z level on the two Y edges.
For each X quadrature ray, split Y at ALL exact linear scalar zero crossings.
This resolves changes of vertical crossing interval before numerical integration.
Terrain is still sampled from the exact caller-owned mesh; unresolved terrain
clipping/contour intersections remain subject to the original accuracy gates.
No scalar perturbation, clipping, density mask or terrain change is introduced.
"""
import numpy as np
from liquid_surface_volume_gradient import negative_length_gradient
from liquid_interface_volume import negative_lengths


def intervals_at_roots(left,right):
    """Return parent rows and nonempty intervals cut at linear roots in (0,1).

    Keep distinct arbitrarily close roots. Only exactly repeated endpoints
    make zero-length intervals; no epsilon threshold erases a thin interval.
    """
    a=np.asarray(left,float);b=np.asarray(right,float)
    if a.ndim!=2 or b.shape!=a.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Finite paired ray endpoint scalars required')
    den=a-b;roots=np.full(a.shape,np.inf)
    np.divide(a,den,out=roots,where=den!=0)
    roots[(roots<=0)|(roots>=1)]=np.inf
    cuts=np.sort(np.column_stack((np.zeros(len(a)),np.ones(len(a)),roots)),axis=1)
    low=cuts[:,:-1];high=cuts[:,1:];rows,columns=np.nonzero(np.isfinite(high)&(high>low))
    return rows,low[rows,columns],high[rows,columns]


def _corner_value(corners,x,y):
    return (corners[:,:,0]*(1-x[:,None])*(1-y[:,None])+corners[:,:,1]*x[:,None]*(1-y[:,None])+
            corners[:,:,2]*(1-x[:,None])*y[:,None]+corners[:,:,3]*x[:,None]*y[:,None])


def evaluate_columns(corners,lower,centers,half,spacing,sample_bed,order):
    """Evaluate a bounded group of original XY columns; all weights stay local."""
    c=np.asarray(corners,float);h=np.asarray(spacing,float);n,nz,_=c.shape
    nodes,weights=np.polynomial.legendre.leggauss(order)
    extended=np.concatenate((1.5*c[:,:1]-.5*c[:,1:2],c,1.5*c[:,-1:]-.5*c[:,-2:-1]),axis=1)
    z=np.r_[0,(np.arange(nz)+.5)*h[2],nz*h[2]]
    low_xy=centers-half;high_xy=centers+half
    t0=low_xy/h[:2]-.5-lower;t1=high_xy/h[:2]-.5-lower
    left=np.concatenate((_corner_value(extended,t0[:,0],t0[:,1]),_corner_value(extended,t0[:,0],t1[:,1])),axis=1)
    right=np.concatenate((_corner_value(extended,t1[:,0],t0[:,1]),_corner_value(extended,t1[:,0],t1[:,1])),axis=1)
    parent,xa,xb=intervals_at_roots(left,right)
    xp=low_xy[parent,0,None]+(xa[:,None]+(xb-xa)[:,None]*(nodes+1)/2)*2*half[parent,0,None]
    xw=(xb-xa)[:,None]*half[parent,0,None]*weights
    parent=np.repeat(parent,order);xp=xp.ravel();xw=xw.ravel()
    volume=np.zeros((n,3));gradient=np.zeros((n,nz,4));queries=0;y_intervals=0;zero=0;bed_ties=0
    # Bound all intermediate ray/scalar arrays, including columns with many
    # disconnected liquid intervals. No giant order^2 whole-river allocation.
    for first in range(0,len(xp),1024):
        pp=parent[first:first+1024];xx=xp[first:first+1024];wx=xw[first:first+1024]
        tx=xx/h[0]-.5-lower[pp,0]
        yl=_corner_value(extended[pp],tx,t0[pp,1]);yr=_corner_value(extended[pp],tx,t1[pp,1])
        ray,ya,yb=intervals_at_roots(yl,yr);y_intervals+=len(ray)
        for begin in range(0,len(ray),max(1,32768//order)):
            rr=ray[begin:begin+max(1,32768//order)];a=ya[begin:begin+len(rr)];b=yb[begin:begin+len(rr)]
            ids=pp[rr];yy=low_xy[ids,1,None]+(a[:,None]+(b-a)[:,None]*(nodes+1)/2)*2*half[ids,1,None]
            qx=np.broadcast_to(xx[rr,None],yy.shape);xy=np.column_stack((qx.ravel(),yy.ravel()))
            bed=np.asarray(sample_bed(xy),float)
            if bed.shape!=(len(xy),) or not np.isfinite(bed).all():raise ValueError('Exact bed failed a split integration query')
            queries+=len(xy);txq=qx/h[0]-.5-lower[ids,0,None];tyq=yy/h[1]-.5-lower[ids,1,None]
            values=np.zeros((nz,len(ids),order))
            xy_weights=[]
            for k,(cx,cy) in enumerate(((0,0),(1,0),(0,1),(1,1))):
                w=(txq if cx else 1-txq)*(tyq if cy else 1-tyq);xy_weights.append(w)
                values+=c[ids,:,k].T[:,:,None]*w
            raw_values=values.reshape(nz,-1)
            scalar=np.vstack((1.5*raw_values[0]-.5*raw_values[1],raw_values,1.5*raw_values[-1]-.5*raw_values[-2]))
            lengths,derivative,diagnostic=negative_length_gradient(scalar,z,bed,0,z[-1])
            zero+=diagnostic['zero_endpoint_rays'];bed_ties+=diagnostic['zero_crossing_on_bed_rays']
            area=wx[rr,None]*(b-a)[:,None]*half[ids,1,None]*weights
            np.add.at(volume[:,0],ids,np.sum(lengths.reshape(len(ids),order)*area,axis=1))
            for k,(lo,hi) in enumerate(((0,.5*h[2]),(z[-1]-.5*h[2],z[-1])),1):
                length=negative_lengths(scalar,z,bed,lo,hi).reshape(len(ids),order)
                np.add.at(volume[:,k],ids,np.sum(length*area,axis=1))
            raw=derivative[1:-1].copy();raw[0]+=1.5*derivative[0];raw[1]-=.5*derivative[0]
            raw[-1]+=1.5*derivative[-1];raw[-2]-=.5*derivative[-1]
            raw=raw.reshape(nz,len(ids),order).transpose(1,0,2)
            for k,w in enumerate(xy_weights):
                np.add.at(gradient[:,:,k],ids,np.sum(raw*(area*w)[:,None,:],axis=2))
    return volume,gradient,dict(queries=queries,x_intervals=len(parent)//order,y_intervals=y_intervals,
        zero_endpoint_rays=zero,zero_crossing_on_bed_rays=bed_ties)


def integrate_gradient_split(phi,spacing,minimum_xy,maximum_xy,sample_bed,*,orders=(2,4,8,16,32,64,128),
                             column_tolerance=1e-4,gradient_tolerance=1e-4,diagnostics=None,progress=None):
    f=np.asarray(phi,float);h=np.asarray(spacing,float);lo=np.asarray(minimum_xy,float);hi=np.asarray(maximum_xy,float)
    if (f.ndim!=3 or min(f.shape)<2 or h.shape!=(3,) or lo.shape!=(2,) or hi.shape!=(2,) or
            not all(np.isfinite(a).all() for a in (f,h,lo,hi)) or (h<=0).any() or (hi<=lo).any() or
            (lo<.5*h[:2]).any() or (hi>=(np.array(f.shape[:0:-1])-.5)*h[:2]).any() or
            len(orders)<2 or any(not isinstance(o,int) or o<1 or o>128 for o in orders) or
            any(a>=b for a,b in zip(orders,orders[1:])) or not np.isfinite([column_tolerance,gradient_tolerance]).all() or
            min(column_tolerance,gradient_tolerance)<=0):raise ValueError('Supported grid and positive increasing quadrature controls required')
    knots=[]
    for axis in range(2):
        grid=(np.arange(f.shape[2-axis])+.5)*h[axis]
        knots.append(np.r_[lo[axis],grid[(grid>lo[axis])&(grid<hi[axis])],hi[axis]])
    x0,y0=np.meshgrid(knots[0][:-1],knots[1][:-1]);x1,y1=np.meshgrid(knots[0][1:],knots[1][1:])
    centers=np.column_stack(((x0+x1).ravel()/2,(y0+y1).ravel()/2));half=np.column_stack(((x1-x0).ravel()/2,(y1-y0).ravel()/2))
    lower=np.floor(centers/h[:2]-.5).astype(int);n=len(centers);nz=len(f)
    corners=np.stack([f[:,lower[:,1]+cy,lower[:,0]+cx].T for cx,cy in ((0,0),(1,0),(0,1),(1,1))],axis=-1)
    volume=np.zeros((n,3));local_gradient=np.zeros((n,nz,4));vdiff=np.full(n,np.inf);gdiff=np.full(n,np.inf)
    active=np.arange(n);history=[];totals=dict(queries=0,x_intervals=0,y_intervals=0,zero_endpoint_rays=0,zero_crossing_on_bed_rays=0)
    final_orders=np.zeros(n,int)
    for iteration,order in enumerate(orders):
        candidate=np.zeros((len(active),3));gradient=np.zeros((len(active),nz,4))
        for first in range(0,len(active),128):
            ids=active[first:first+128]
            v,g,r=evaluate_columns(corners[ids],lower[ids],centers[ids],half[ids],h,sample_bed,order)
            candidate[first:first+len(ids)]=v;gradient[first:first+len(ids)]=g
            for key in totals:totals[key]+=r[key]
        if iteration:
            vdiff[active]=np.max(abs(candidate-volume[active]),axis=1)
            gdiff[active]=np.max(abs(gradient-local_gradient[active]),axis=(1,2))
        volume[active]=candidate;local_gradient[active]=gradient;final_orders[active]=order
        remain=(vdiff[active]>column_tolerance)|(gdiff[active]>gradient_tolerance)
        record=dict(order=order,evaluated_columns=len(active),unresolved_columns=int(remain.sum()),volume=float(volume[:,0].sum()),queries_so_far=totals['queries'])
        history.append(record)
        if progress:progress(dict(event='split_quadrature_order',**record))
        active=active[remain]
        if not len(active):break
    result=np.zeros_like(f);zz=np.arange(nz)[None,:]
    for k,(cx,cy) in enumerate(((0,0),(1,0),(0,1),(1,1))):np.add.at(result,(zz,lower[:,1,None]+cy,lower[:,0,None]+cx),local_gradient[:,:,k])
    if diagnostics is not None:diagnostics.update(centers_xy=centers,half_extent_xy=half,lower_xy=lower,volume_by_column=volume,
        volume_difference=vdiff,gradient_difference=gdiff,final_order=final_orders,unresolved_columns=active)
    return result,dict(volume=float(volume[:,0].sum()),lower_extrapolated_cap_volume=float(volume[:,1].sum()),
        upper_extrapolated_cap_volume=float(volume[:,2].sum()),columns=n,unresolved_columns=len(active),history=history,
        volume_difference_sum=float(vdiff.sum()),gradient_difference_sum=float(gdiff.sum()),column_tolerance=column_tolerance,
        gradient_tolerance=gradient_tolerance,zero_endpoint_rays_across_orders=totals['zero_endpoint_rays'],
        zero_crossing_on_bed_rays_across_orders=totals['zero_crossing_on_bed_rays'],quadrature_queries=totals['queries'],
        contour_splits=True,quadrature_estimated_not_certified=True,interface_or_terrain_modified=False)
