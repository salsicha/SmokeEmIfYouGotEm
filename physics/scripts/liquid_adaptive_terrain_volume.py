"""Adaptive X subdivision over exact scalar/terrain-split Y quadrature.

Each child receives its proportional share of the ORIGINAL column's volume
and gradient tolerances. Accepted differences add, never cancel. Exhausted
leaves remain explicit failures; none are relabeled as resolved.
"""
import numpy as np
from liquid_terrain_volume_gradient import evaluate_bed_columns


def adaptive_bed_columns(corners,lower,centers,half,spacing,bed_segments,*,orders=(8,16),
                         column_tolerance=1e-4,gradient_tolerance=1e-4,max_depth=14,progress=None):
    c=np.asarray(corners,float);lower=np.asarray(lower);centers=np.asarray(centers,float);half=np.asarray(half,float)
    h=np.asarray(spacing,float)
    if (c.ndim!=3 or c.shape[1]<2 or c.shape[2]!=4 or lower.shape!=(len(c),2) or
            not np.issubdtype(lower.dtype,np.integer) or centers.shape!=lower.shape or half.shape!=lower.shape or
            h.shape!=(3,) or (half<=0).any() or (h<=0).any() or
            not all(np.isfinite(v).all() for v in (c,centers,half,h)) or
            len(orders)!=2 or any(not isinstance(o,int) or o<1 or o>128 for o in orders) or orders[0]>=orders[1] or
            not isinstance(max_depth,int) or not 0<=max_depth<=24 or
            not np.isfinite([column_tolerance,gradient_tolerance]).all() or min(column_tolerance,gradient_tolerance)<=0):
        raise ValueError('Finite columns, positive tolerances and bounded subdivision controls required')
    n,nz,_=c.shape;volume=np.zeros((n,3));gradient=np.zeros((n,nz,4));vd=np.zeros(n);gd=np.zeros(n)
    final_depth=np.zeros(n,int);unresolved=np.zeros(n,bool);leaves=np.zeros(n,int)
    active=np.arange(n);cc=centers.copy();hh=half.copy();history=[]
    totals=dict(queries=0,x_intervals=0,y_intervals=0,zero_endpoint_rays=0,zero_crossing_on_bed_rays=0)
    for depth in range(max_depth+1):
        next_ids=[];next_centers=[];next_half=[];rejected=0
        for first in range(0,len(active),64):
            ids=active[first:first+64];pos=cc[first:first+64];ext=hh[first:first+64]
            low,lg,lr=evaluate_bed_columns(c[ids],lower[ids],pos,ext,h,bed_segments,orders[0])
            high,hg,hr=evaluate_bed_columns(c[ids],lower[ids],pos,ext,h,bed_segments,orders[1])
            for key in totals:totals[key]+=lr[key]+hr[key]
            dv=np.max(abs(high-low),axis=1);dg=np.max(abs(hg-lg),axis=(1,2));share=ext[:,0]/half[ids,0]
            fail=(dv>column_tolerance*share)|(dg>gradient_tolerance*share);rejected+=int(fail.sum())
            retain=~fail if depth<max_depth else np.ones(len(ids),bool)
            chosen=ids[retain]
            np.add.at(volume,chosen,high[retain]);np.add.at(gradient,chosen,hg[retain])
            np.add.at(vd,chosen,dv[retain]);np.add.at(gd,chosen,dg[retain]);np.add.at(leaves,chosen,1)
            np.maximum.at(final_depth,chosen,depth)
            if depth==max_depth:unresolved[ids[fail]]=True
            elif fail.any():
                child_half=ext[fail].copy();child_half[:,0]/=2
                for sign in (-1,1):
                    child=pos[fail].copy();child[:,0]+=sign*child_half[:,0]
                    next_ids.append(ids[fail]);next_centers.append(child);next_half.append(child_half)
        record=dict(depth=depth,evaluated_subcolumns=len(active),failed_subcolumns=rejected,queries_so_far=totals['queries'])
        history.append(record)
        if progress:progress(dict(event='adaptive_bed_depth',**record))
        if not next_ids:break
        active=np.concatenate(next_ids);cc=np.concatenate(next_centers);hh=np.concatenate(next_half)
    diagnostics=dict(volume_difference=vd,gradient_difference=gd,final_depth=final_depth,
                     unresolved_columns=np.flatnonzero(unresolved),leaf_count=leaves)
    proof=dict(columns=n,unresolved_columns=int(unresolved.sum()),history=history,volume=float(volume[:,0].sum()),
        volume_difference_sum=float(vd.sum()),gradient_difference_sum=float(gd.sum()),
        column_tolerance=column_tolerance,gradient_tolerance=gradient_tolerance,orders=list(orders),max_depth=max_depth,
        estimated_not_certified=True,terrain_or_interface_modified=False,**totals)
    return volume,gradient,diagnostics,proof


def integrate_gradient_terrain(phi,spacing,minimum_xy,maximum_xy,bed_segments,*,
                               column_tolerance=1e-4,gradient_tolerance=1e-4,diagnostics=None,progress=None):
    """Full physical XY footprint, retaining all original-column error budgets."""
    f=np.asarray(phi,float);h=np.asarray(spacing,float);lo=np.asarray(minimum_xy,float);hi=np.asarray(maximum_xy,float)
    if (f.ndim!=3 or min(f.shape)<2 or h.shape!=(3,) or lo.shape!=(2,) or hi.shape!=(2,) or
            not all(np.isfinite(v).all() for v in (f,h,lo,hi)) or (h<=0).any() or (hi<=lo).any() or
            (lo<.5*h[:2]).any() or (hi>=(np.array(f.shape[:0:-1])-.5)*h[:2]).any()):
        raise ValueError('Finite supported physical scalar grid required')
    knots=[]
    for axis in range(2):
        grid=(np.arange(f.shape[2-axis])+.5)*h[axis]
        knots.append(np.r_[lo[axis],grid[(grid>lo[axis])&(grid<hi[axis])],hi[axis]])
    x0,y0=np.meshgrid(knots[0][:-1],knots[1][:-1]);x1,y1=np.meshgrid(knots[0][1:],knots[1][1:])
    centers=np.column_stack(((x0+x1).ravel()/2,(y0+y1).ravel()/2));half=np.column_stack(((x1-x0).ravel()/2,(y1-y0).ravel()/2))
    lower=np.floor(centers/h[:2]-.5).astype(int);n=len(centers);nz=len(f)
    corners=np.stack([f[:,lower[:,1]+cy,lower[:,0]+cx].T for cx,cy in ((0,0),(1,0),(0,1),(1,1))],axis=-1)
    v=np.zeros((n,3));g=np.zeros((n,nz,4));vd=np.zeros(n);gd=np.zeros(n);depth=np.zeros(n,int);leaves=np.zeros(n,int)
    unresolved=np.zeros(n,bool);records=[];queries=zero=ties=0
    # Most quiescent columns resolve at low order. Only unresolved columns pay
    # for higher-order/adaptive integration. No failed result is discarded.
    for first in range(0,n,128):
        ids=np.arange(first,min(first+128,n));args=(corners[ids],lower[ids],centers[ids],half[ids],h,bed_segments)
        controls=dict(column_tolerance=column_tolerance,gradient_tolerance=gradient_tolerance)
        bv,bg,d,r=adaptive_bed_columns(*args,orders=(2,4),max_depth=0,**controls)
        queries+=r['queries'];zero+=r['zero_endpoint_rays'];ties+=r['zero_crossing_on_bed_rays']
        fail=d['unresolved_columns'];pending=np.zeros(len(ids),bool)
        if len(fail):
            av,ag,ad,ar=adaptive_bed_columns(corners[ids[fail]],lower[ids[fail]],centers[ids[fail]],half[ids[fail]],h,bed_segments,**controls)
            bv[fail]=av;bg[fail]=ag;queries+=ar['queries'];zero+=ar['zero_endpoint_rays'];ties+=ar['zero_crossing_on_bed_rays']
            for key in ('volume_difference','gradient_difference','final_depth','leaf_count'):d[key][fail]=ad[key]
            pending[fail[ad['unresolved_columns']]]=True
        v[ids]=bv;g[ids]=bg;vd[ids]=d['volume_difference'];gd[ids]=d['gradient_difference']
        depth[ids]=d['final_depth'];leaves[ids]=d['leaf_count'];unresolved[ids]=pending
        record=dict(processed_columns=int(ids[-1]+1),columns=n,unresolved_columns=int(unresolved.sum()),queries_so_far=queries)
        records.append(record)
        if progress and (first==0 or (first//128)%16==15 or ids[-1]+1==n):progress(dict(event='terrain_quadrature_batch',**record))
    result=np.zeros_like(f);zz=np.arange(nz)[None,:]
    for k,(cx,cy) in enumerate(((0,0),(1,0),(0,1),(1,1))):np.add.at(result,(zz,lower[:,1,None]+cy,lower[:,0,None]+cx),g[:,:,k])
    if diagnostics is not None:diagnostics.update(centers_xy=centers,half_extent_xy=half,lower_xy=lower,volume_by_column=v,
        volume_difference=vd,gradient_difference=gd,final_depth=depth,leaf_count=leaves,unresolved_columns=np.flatnonzero(unresolved))
    return result,dict(volume=float(v[:,0].sum()),lower_extrapolated_cap_volume=float(v[:,1].sum()),
        upper_extrapolated_cap_volume=float(v[:,2].sum()),columns=n,unresolved_columns=int(unresolved.sum()),history=records,
        volume_difference_sum=float(vd.sum()),gradient_difference_sum=float(gd.sum()),column_tolerance=column_tolerance,
        gradient_tolerance=gradient_tolerance,zero_endpoint_rays_across_orders=zero,zero_crossing_on_bed_rays_across_orders=ties,
        quadrature_queries=queries,terrain_contact_splits=True,adaptive_x_subdivision=True,
        quadrature_estimated_not_certified=True,interface_or_terrain_modified=False)
