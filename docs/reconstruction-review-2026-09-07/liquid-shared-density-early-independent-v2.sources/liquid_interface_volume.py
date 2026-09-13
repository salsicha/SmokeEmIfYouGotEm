"""Geometric volume of a tracked scalar above an unchanged height-field bed.

At fixed XY a trilinear scalar is piecewise linear in Z. All its negative
intervals are integrated exactly, including multiple detached sheets/overhangs.
Horizontal integration is adaptive Gauss quadrature against the actual bed
callback. Successive-order differences are estimates, NOT certified bounds.
No voxel-count proxy, density clamp, terrain change or interface repair occurs.
"""
import numpy as np


def negative_lengths(values,z,bed,lower,upper):
    """Negative-scalar lengths above bed for each ray; shared metric Z knots."""
    v=np.asarray(values,float);z=np.asarray(z,float);b=np.asarray(bed,float)
    if (v.ndim!=2 or z.shape!=(v.shape[0],) or b.shape!=(v.shape[1],) or len(z)<2 or
            not all(np.isfinite(a).all() for a in (v,z,b)) or (np.diff(z)<=0).any() or
            not np.isfinite([lower,upper]).all() or lower<z[0] or upper>z[-1] or lower>=upper):
        raise ValueError('Finite ordered Z columns, bed and supported integration interval required')
    a=v[:-1];c=v[1:];za=z[:-1,None];zb=z[1:,None]
    crossing=np.divide(a,a-c,out=np.zeros_like(a),where=a!=c)*(zb-za)+za
    start=np.where(a<0,za,crossing);end=np.where(c<0,zb,crossing)
    start=np.maximum(start,np.maximum(b,lower)[None,:]);end=np.minimum(end,upper)
    lengths=np.where((a<0)|(c<0),np.maximum(end-start,0),0)
    return lengths.sum(0)


def sample_columns(phi,spacing,xy,*,endcaps=False):
    """Bilinear XY samples of every Z level, with optional explicit linear caps.

    Endcaps extrapolate the first/last pair of Z levels to the grid faces.
    They are reported separately, never silently presented as captured samples.
    """
    f=np.asarray(phi,float);h=np.asarray(spacing,float);p=np.asarray(xy,float)
    if (f.ndim!=3 or min(f.shape)<2 or h.shape!=(3,) or p.ndim!=2 or p.shape[1]!=2 or
            not all(np.isfinite(a).all() for a in (f,h,p)) or (h<=0).any()):
        raise ValueError('Finite ZYX scalar grid, XY queries and metric spacing required')
    q=p/h[:2]-.5;lo=np.floor(q).astype(int);t=q-lo;c=np.array(f.shape[:0:-1])
    if (lo<0).any() or (lo+1>=c).any():raise ValueError('Complete horizontal scalar support required')
    values=np.zeros((f.shape[0],len(p)))
    for x in (0,1):
        for y in (0,1):
            w=(t[:,0] if x else 1-t[:,0])*(t[:,1] if y else 1-t[:,1])
            values+=f[:,lo[:,1]+y,lo[:,0]+x]*w
    z=(np.arange(f.shape[0])+.5)*h[2]
    if endcaps:
        values=np.vstack((1.5*values[0]-.5*values[1],values,1.5*values[-1]-.5*values[-2]))
        z=np.r_[0,z,f.shape[0]*h[2]]
    return values,z


def integrate(phi,spacing,minimum_xy,maximum_xy,sample_bed,*,orders=(2,4,8,16),column_tolerance=1e-4):
    f=np.asarray(phi,float);h=np.asarray(spacing,float)
    lo=np.asarray(minimum_xy,float);hi=np.asarray(maximum_xy,float)
    if (f.ndim!=3 or min(f.shape)<2 or h.shape!=(3,) or lo.shape!=(2,) or hi.shape!=(2,) or
            not all(np.isfinite(a).all() for a in (f,h,lo,hi)) or (h<=0).any() or (hi<=lo).any() or
            (lo<.5*h[:2]).any() or (hi>=(np.array(f.shape[:0:-1])-.5)*h[:2]).any() or
            len(orders)<2 or any(not isinstance(o,int) or o<1 or o>128 for o in orders) or
            any(a>=b for a,b in zip(orders,orders[1:])) or not np.isfinite(column_tolerance) or column_tolerance<=0):
        raise ValueError('Supported physical XY box, positive grid and increasing quadrature orders required')
    knots=[]
    for axis in range(2):
        centers=(np.arange(f.shape[2-axis])+.5)*h[axis]
        knots.append(np.r_[lo[axis],centers[(centers>lo[axis])&(centers<hi[axis])],hi[axis]])
    x0,y0=np.meshgrid(knots[0][:-1],knots[1][:-1]);x1,y1=np.meshgrid(knots[0][1:],knots[1][1:])
    centers=np.column_stack(((x0+x1).ravel()/2,(y0+y1).ravel()/2))
    half=np.column_stack(((x1-x0).ravel()/2,(y1-y0).ravel()/2))
    n=len(centers);volumes=np.zeros((n,3));differences=np.full((n,3),np.inf)
    active=np.arange(n);history=[];zero_rays=0
    for iteration,order in enumerate(orders):
        nodes,weights=np.polynomial.legendre.leggauss(order)
        x,y=np.meshgrid(nodes,nodes);offsets=np.column_stack((x.ravel(),y.ravel()));ww=np.outer(weights,weights).ravel()
        candidate=np.zeros((len(active),3));ambiguous=0
        batch=max(1,32768//(order*order))
        for first in range(0,len(active),batch):
            chosen=active[first:first+batch];query=centers[chosen,None,:]+half[chosen,None,:]*offsets[None,:,:]
            p=query.reshape(-1,2);bed=np.asarray(sample_bed(p),float)
            if bed.shape!=(len(p),) or not np.isfinite(bed).all():raise ValueError('Complete finite exact-bed samples required')
            scalar,z=sample_columns(f,h,p,endcaps=True)
            ambiguous+=int(np.any((scalar[:-1]==0)&(scalar[1:]==0),axis=0).sum())
            intervals=((0,z[-1]),(0,.5*h[2]),(z[-1]-.5*h[2],z[-1]))
            for k,(lower,upper) in enumerate(intervals):
                length=negative_lengths(scalar,z,bed,lower,upper).reshape(len(chosen),-1)
                candidate[first:first+len(chosen),k]=(length@ww)*half[chosen].prod(1)
        old=volumes[active].copy();volumes[active]=candidate
        if iteration:
            differences[active]=abs(candidate-old)
            remain=np.any(differences[active]>column_tolerance,axis=1)
        else:remain=np.ones(len(active),bool)
        history.append(dict(order=order,evaluated_columns=len(active),unresolved_columns=int(remain.sum()),
            integrated_volume=float(volumes[:,0].sum()),ambiguous_zero_segment_rays=ambiguous))
        zero_rays+=ambiguous;active=active[remain]
        if not len(active):break
    return dict(volume=float(volumes[:,0].sum()),lower_extrapolated_cap_volume=float(volumes[:,1].sum()),
        upper_extrapolated_cap_volume=float(volumes[:,2].sum()),resolved_z_volume=float((volumes[:,0]-volumes[:,1]-volumes[:,2]).sum()),
        columns=n,unresolved_columns=len(active),successive_order_absolute_difference_sum=differences.sum(0).tolist(),
        maximum_column_difference=float(differences.max()),column_tolerance=column_tolerance,history=history,
        ambiguous_zero_segment_rays_across_orders=zero_rays,quadrature_estimated_not_certified=True,
        endcap_model='explicit linear extension of first/last two samples to Z faces; volumes reported separately',
        scalar_is_signed_distance=False,interface_or_terrain_modified=False)
