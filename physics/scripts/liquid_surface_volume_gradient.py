"""Derivative of the actual trilinear surface volume above a fixed riverbed.

Differentiate every active vertical zero crossing, including detached intervals
and the existing explicit linear Z caps. XY integration is adaptive Gauss
quadrature; both volume and local gradient differences control refinement.
No surface offset, density isovalue replacement or terrain change is performed.
Quadrature differences are estimates, not certified error bounds.
"""
import numpy as np
from liquid_interface_volume import negative_lengths,sample_columns


def negative_length_gradient(values,z,bed,lower,upper):
    v=np.asarray(values,float);z=np.asarray(z,float);bed=np.asarray(bed,float)
    length=negative_lengths(v,z,bed,lower,upper)  # Includes shape/finite checks.
    a=v[:-1];b=v[1:];dz=np.diff(z)[:,None];den=a-b
    crossing=z[:-1,None]+np.divide(dz*a,den,out=np.zeros_like(a),where=den!=0)
    active=((a<0)!=(b<0))&(crossing>np.maximum(bed,lower)[None,:])&(crossing<upper)
    # Endpoints at exactly zero are nondifferentiable branch cases. Their
    # one-sided value is retained and the ambiguity is explicitly reported.
    sign=np.where(a<0,1.,-1.);ga=np.zeros_like(a);gb=np.zeros_like(b)
    np.divide(-sign*dz*b,den**2,out=ga,where=active&(den!=0))
    np.divide(sign*dz*a,den**2,out=gb,where=active&(den!=0))
    gradient=np.zeros_like(v);gradient[:-1]+=ga;gradient[1:]+=gb
    return length,gradient,dict(zero_endpoint_rays=int(np.any(v==0,axis=0).sum()),
        zero_crossing_on_bed_rays=int(np.any(((a<0)!=(b<0))&(crossing==bed[None,:]),axis=0).sum()))


def integrate_gradient(phi,spacing,minimum_xy,maximum_xy,sample_bed,*,orders=(2,4,8,16),
                       column_tolerance=1e-4,gradient_tolerance=1e-4):
    f=np.asarray(phi,float);h=np.asarray(spacing,float);lo=np.asarray(minimum_xy,float);hi=np.asarray(maximum_xy,float)
    if (f.ndim!=3 or min(f.shape)<2 or h.shape!=(3,) or lo.shape!=(2,) or hi.shape!=(2,) or
            not all(np.isfinite(a).all() for a in (f,h,lo,hi)) or (h<=0).any() or (hi<=lo).any() or
            (lo<.5*h[:2]).any() or (hi>=(np.array(f.shape[:0:-1])-.5)*h[:2]).any() or
            len(orders)<2 or any(not isinstance(o,int) or o<1 or o>128 for o in orders) or
            any(a>=b for a,b in zip(orders,orders[1:])) or not np.isfinite([column_tolerance,gradient_tolerance]).all() or
            min(column_tolerance,gradient_tolerance)<=0):
        raise ValueError('Supported physical grid, increasing quadrature orders and positive tolerances required')
    knots=[]
    for axis in range(2):
        centers=(np.arange(f.shape[2-axis])+.5)*h[axis]
        knots.append(np.r_[lo[axis],centers[(centers>lo[axis])&(centers<hi[axis])],hi[axis]])
    x0,y0=np.meshgrid(knots[0][:-1],knots[1][:-1]);x1,y1=np.meshgrid(knots[0][1:],knots[1][1:])
    centers=np.column_stack(((x0+x1).ravel()/2,(y0+y1).ravel()/2));half=np.column_stack(((x1-x0).ravel()/2,(y1-y0).ravel()/2))
    lower=np.floor(centers/h[:2]-.5).astype(int);count=len(centers);nz=len(f)
    volumes=np.zeros((count,3));local_gradient=np.zeros((count,nz,4));active=np.arange(count)
    differences=np.full(count,np.inf);gradient_differences=np.full(count,np.inf);history=[];ambiguous=0;bed_ties=0
    for iteration,order in enumerate(orders):
        nodes,weights=np.polynomial.legendre.leggauss(order);x,y=np.meshgrid(nodes,nodes)
        offsets=np.column_stack((x.ravel(),y.ravel()));ww=np.outer(weights,weights).ravel();nq=len(ww)
        candidate=np.zeros((len(active),3));g=np.zeros((len(active),nz,4));batch=max(1,32768//nq)
        for first in range(0,len(active),batch):
            chosen=active[first:first+batch];query=centers[chosen,None,:]+half[chosen,None,:]*offsets
            xy=query.reshape(-1,2);bed=np.asarray(sample_bed(xy),float)
            scalar,z=sample_columns(f,h,xy,endcaps=True)
            lengths,derivative,diagnostic=negative_length_gradient(scalar,z,bed,0,z[-1])
            ambiguous+=diagnostic['zero_endpoint_rays'];bed_ties+=diagnostic['zero_crossing_on_bed_rays']
            area_weights=half[chosen].prod(axis=1)[:,None]*ww
            candidate[first:first+len(chosen),0]=np.sum(lengths.reshape(len(chosen),nq)*area_weights,axis=1)
            for k,(a,b) in enumerate(((0,.5*h[2]),(z[-1]-.5*h[2],z[-1])),1):
                candidate[first:first+len(chosen),k]=np.sum(negative_lengths(scalar,z,bed,a,b).reshape(len(chosen),nq)*area_weights,axis=1)
            # Transpose the exact explicit endcap extrapolation into captured Z.
            raw=derivative[1:-1].copy();raw[0]+=1.5*derivative[0];raw[1]-=.5*derivative[0]
            raw[-1]+=1.5*derivative[-1];raw[-2]-=.5*derivative[-1]
            raw=raw.T.reshape(len(chosen),nq,nz)
            t=query/h[:2]-.5-lower[chosen,None,:]
            for corner,(cx,cy) in enumerate(((0,0),(1,0),(0,1),(1,1))):
                wxy=(t[:,:,0] if cx else 1-t[:,:,0])*(t[:,:,1] if cy else 1-t[:,:,1])
                g[first:first+len(chosen),:,corner]=np.sum(raw*(wxy*area_weights)[:,:,None],axis=1)
        if iteration:
            differences[active]=np.max(abs(candidate-volumes[active]),axis=1)
            gradient_differences[active]=np.max(abs(g-local_gradient[active]),axis=(1,2))
        volumes[active]=candidate;local_gradient[active]=g
        remain=(differences[active]>column_tolerance)|(gradient_differences[active]>gradient_tolerance)
        history.append(dict(order=order,evaluated_columns=len(active),unresolved_columns=int(remain.sum()),volume=float(volumes[:,0].sum())))
        active=active[remain]
        if not len(active):break
    gradient=np.zeros_like(f)
    zz=np.arange(nz)[None,:]
    for corner,(cx,cy) in enumerate(((0,0),(1,0),(0,1),(1,1))):
        np.add.at(gradient,(zz,lower[:,1,None]+cy,lower[:,0,None]+cx),local_gradient[:,:,corner])
    return gradient,dict(volume=float(volumes[:,0].sum()),lower_extrapolated_cap_volume=float(volumes[:,1].sum()),
        upper_extrapolated_cap_volume=float(volumes[:,2].sum()),columns=count,unresolved_columns=len(active),history=history,
        volume_difference_sum=float(differences.sum()),gradient_difference_sum=float(gradient_differences.sum()),
        column_tolerance=column_tolerance,gradient_tolerance=gradient_tolerance,
        zero_endpoint_rays_across_orders=ambiguous,zero_crossing_on_bed_rays_across_orders=bed_ties,
        quadrature_estimated_not_certified=True,interface_or_terrain_modified=False)
