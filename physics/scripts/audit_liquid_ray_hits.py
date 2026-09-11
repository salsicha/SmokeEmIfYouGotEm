"""Compare inherited distance marching to dense first-crossing samples of a captured field.

This isolates the liquid field: no terrain occlusion, temporal AA or real GPU
texture-filter rounding. The dense scan is evidence, not an exact cubic solver.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from liquid_current_surface_foam import sample as trilinear


def camera_rays(width=144,height=96):
    origin=np.array([-17.,-23.,12.])
    forward=np.array([0.,0.,2.5])-origin;forward/=np.linalg.norm(forward)
    right=np.cross([0.,0.,1.],forward);right/=np.linalg.norm(right)
    up=np.cross(forward,right)
    y,x=np.indices((height,width));scale=np.tan(np.deg2rad(24))
    directions=forward+((2*(x+.5)/width-1)*scale)[...,None]*right+((1-2*(y+.5)/height)*scale*height/width)[...,None]*up
    directions=directions.reshape(-1,3);directions/=np.linalg.norm(directions,axis=-1)[:,None]
    return origin,directions


def box_intervals(origin,directions,minimum,extent):
    with np.errstate(divide='ignore',invalid='ignore'):
        a=(minimum-origin)/directions;b=(minimum+extent-origin)/directions
    entry=np.maximum(np.minimum(a,b).max(axis=-1),0)
    exit=np.maximum(a,b).min(axis=-1)
    return entry,exit


def compare(field,origin,directions,minimum,extent,scan_step=.01):
    field=np.asarray(field,dtype=float)
    if field.ndim!=3 or not np.isfinite(field).all() or not np.isfinite(scan_step) or scan_step<=0:
        raise ValueError('Finite scalar field and positive scan spacing required')
    size=np.array(field.shape[::-1]);spacing=extent/size
    entry,exit=box_intervals(origin,directions,minimum,extent)
    valid=exit>=entry
    def sample(t,ids):
        p=origin+directions[ids]*t[:,None]
        return trilinear(field[...,None],(p-minimum)/extent)[:,0]
    n=len(directions);old=np.full(n,np.nan);reference=np.full(n,np.nan)
    t=entry.copy();active=valid.copy();tolerance=spacing[0]*.005
    for _ in range(300):
        ids=np.flatnonzero(active)
        if not len(ids):break
        phi=sample(t[ids],ids)
        hit=(abs(phi)<tolerance)&(t[ids]>=entry[ids])&(t[ids]<=exit[ids])
        old[ids[hit]]=t[ids[hit]];active[ids[hit]]=False
        t[ids[~hit]]+=phi[~hit]
    # Fixed positive increments cannot skip a sign bracket more than the scan
    # spacing wide; bisect each observed first bracket to isolate tracing error.
    t=entry.copy();active=valid.copy();previous=np.zeros(n)
    ids=np.flatnonzero(active);previous[ids]=sample(t[ids],ids)
    for _ in range(int(np.ceil(np.max(np.where(valid,exit-entry,0))/scan_step))+1):
        ids=np.flatnonzero(active)
        if not len(ids):break
        nxt=np.minimum(t[ids]+scan_step,exit[ids]);phi=sample(nxt,ids)
        hit=(phi<=0)&(previous[ids]>0)
        found=ids[hit];lo=t[found].copy();hi=nxt[hit].copy()
        for _ in range(14):
            mid=(lo+hi)/2;inside=sample(mid,found)<=0
            hi=np.where(inside,mid,hi);lo=np.where(inside,lo,mid)
        reference[found]=(lo+hi)/2
        active[found]=False;active[ids[nxt>=exit[ids]]]=False
        t[ids]=nxt;previous[ids]=phi
    common=np.isfinite(old)&np.isfinite(reference)
    delta=old[common]-reference[common]
    result=dict(rays=n,intersect_volume=int(valid.sum()),dense_first_hits=int(np.isfinite(reference).sum()),
        inherited_hits=int(np.isfinite(old).sum()),inherited_missed_hits=int((np.isfinite(reference)&~np.isfinite(old)).sum()),
        inherited_later_surface_over_2cm=int((delta>.02).sum()),
        common_hit_error_cm_quantiles=np.quantile(abs(delta)*100,[.5,.95,.99,1]).tolist() if len(delta) else [],
        scan_step_m=scan_step,exact_intersections=False,terrain_occlusion_modeled=False,
        gpu_filter_rounding_modeled=False,physical_or_visual_acceptance=False)
    return result,old,reference


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path)
    p.add_argument('--step',type=float,default=.01);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    raw=(args.capture/'live_density/surface.rgba16f').read_bytes()
    field=np.frombuffer(raw,dtype='<f2').reshape(48,136,136,4)[...,0].astype(float)/100
    origin,directions=camera_rays()
    result,old,reference=compare(field,origin,directions,np.array([-11.15625,-11.15625,0.]),np.array([22.3125,22.3125,8.]),args.step)
    result['source_surface_sha256']=hashlib.sha256(raw).hexdigest()
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
