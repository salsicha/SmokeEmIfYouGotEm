"""Infer depth amplitude from available source-owned channel, not total width.

This is a Manning construction hypothesis, NOT measured bathymetry or a native
flow solution. Local emergent features are excluded; no banks are widened.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely

from chilko_corridor_bed import CorridorBed
from mosaic_lidarbc_crops import sha
from build_chilko_corridor_scenario import validate_branch_coverage
from chilko_corridor_chart import hydraulic_frame


def fit_depth_amplitude(terrain, stage, owned, shape, minimum, slope, discharge,
                        roughness, spacing=1., maximum=10.):
    terrain,stage,owned,shape=[np.asarray(a) for a in (terrain,stage,owned,shape)]
    minimum,slope=np.asarray(minimum),np.asarray(slope)
    if (terrain.ndim!=2 or any(a.shape!=terrain.shape for a in (stage,owned,shape)) or
            owned.dtype.kind!='b' or minimum.shape!=(len(terrain),) or slope.shape!=minimum.shape or
            not np.isfinite(terrain).all() or
            not all(np.isfinite(a[owned]).all() for a in (stage,shape)) or
            not np.isfinite(minimum).all() or not np.isfinite(slope).all() or
            np.any(minimum<=0) or np.any(minimum>maximum) or np.any(slope<=0) or
            np.any(shape[owned]<0) or np.any(shape[owned]>1) or
            not np.isfinite([discharge,roughness,spacing,maximum]).all() or
            not 0<discharge<=500 or not .02<=roughness<=.1 or spacing<=0 or maximum<=0):
        raise ValueError('Finite bounded source-owned section parameters required')
    if not owned.any(axis=1).all():raise ValueError('No source-owned channel at a section')
    baseline=np.where(owned,np.maximum(stage-terrain,0.),0.)
    section_shape=np.where(owned,shape,0.)
    def capacity(amplitude):
        h=np.where(owned,np.maximum(baseline,np.maximum(amplitude[:,None]*section_shape,.05)),0.)
        return (h**(5/3)).sum(axis=1)*spacing*np.sqrt(slope)/roughness
    lo=minimum.astype(float).copy();hi=np.full(len(lo),maximum)
    initial=capacity(lo)
    if np.any(capacity(hi)<discharge):
        raise ValueError('Required inferred depth exceeds bounded amplitude; inspect source sections')
    active=initial<discharge
    for _ in range(40):
        mid=(lo+hi)/2;too_shallow=capacity(mid)<discharge
        lo=np.where(active&too_shallow,mid,lo);hi=np.where(active&~too_shallow,mid,hi)
    result=np.where(active,hi,minimum)
    return result,initial,capacity(result)


def constrain_source_amplitude(station, amplitude, projected_station, required):
    """Conservative nodal envelope: interpolation must satisfy every cell bound.

    Updating both bracketing source nodes preserves physical cell ownership and
    avoids giving a numerical row's coefficient to an unrelated downstream bend.
    """
    station,amplitude,projected_station,required=map(np.asarray,(station,amplitude,projected_station,required))
    if (station.ndim!=1 or len(station)<2 or amplitude.shape!=station.shape or
            amplitude.dtype.kind!='f' or not amplitude.flags.writeable or
            projected_station.shape!=required.shape or not all(np.isfinite(a).all() for a in
                (station,amplitude,projected_station,required)) or np.any(np.diff(station)<=0) or
            np.any(projected_station<station[0]) or np.any(projected_station>station[-1]) or
            np.any(amplitude<=0) or np.any(amplitude>10) or np.any(required<=0) or np.any(required>10)):
        raise ValueError('Finite in-route amplitude constraints required')
    lower=np.searchsorted(station,projected_station,side='right')-1
    upper=np.minimum(lower+1,len(station)-1)
    np.maximum.at(amplitude,lower,required)
    between=projected_station>station[lower]
    np.maximum.at(amplitude,upper[between],required[between])
    return amplitude


def build(terrain,profile,out,discharge=45.,roughness=.045):
    out=Path(out).resolve()
    if out.exists():raise ValueError('Fresh inferred-depth profile required')
    model=CorridorBed(terrain,profile,discharge,roughness)
    # Exact-route normals can intersect ANOTHER bend hundreds of metres away.
    # Fit on the globally non-overlapping full-domain chart, then constrain the
    # original geographic profile at each cell's own source projection. No
    # geography is moved and no remote bend is counted as local conveyance.
    frame,chart_policy=hydraulic_frame(model.line,model.receipt.get('planform_policy'))
    coverage=validate_branch_coverage(frame,256.,model.polygon,model.line)
    selected=(frame['source_station']>=20)&(frame['source_station']<=model.line.length-20)
    frame={k:v[selected] for k,v in frame.items()}
    lateral=np.arange(-256.,257.,1.)
    row_stage=np.interp(frame['source_station'],model.station,model.surface)
    slope=np.maximum(-np.gradient(row_stage,frame['station']),.001)
    depth=model.depth.copy();before=[];after=[];width=[]
    for start in range(0,len(frame['station']),128):
        sl=slice(start,start+128)
        xy=frame['xy'][sl,None,:]+frame['normal'][sl,None,:]*lateral[None,:,None]
        r=model.sample(xy);mapped=r['mapped_water']
        if mapped[:,0].any() or mapped[:,-1].any():
            raise ValueError('Mapped branches exceed depth quadrature; do not silently truncate capacity')
        owned=mapped&(r['source_height_m']<=r['ownership_reference_m']+.25)
        f=np.zeros(mapped.shape)
        projected=np.full(mapped.shape,np.nan)
        if mapped.any():
            points=shapely.points(xy[mapped]);s=shapely.line_locate_point(model.line,points)
            projected[mapped]=s
            distance=shapely.distance(points,model.polygon.boundary)
            w=np.interp(s,model.station,model.width)
            f[mapped]=np.sqrt(np.clip(2*distance/w,0.,1.))
        # Existing inferred depth is the baseline, so an adequate section needs
        # no higher envelope; never flatten or raise pre-existing deeper cells.
        fitted,old,new=fit_depth_amplitude(r['height_m'],r['reference_m'],owned,f,
            np.full(len(xy),.05),slope[sl],discharge,roughness)
        required=np.broadcast_to(fitted[:,None],owned.shape)
        constrain_source_amplitude(model.station,depth,projected[owned],required[owned])
        before.extend(old);after.extend(new);width.extend(owned.sum(axis=1).astype(float))
        if start%1024==0:print(f'available-channel chart sections {start}/{len(frame["station"])}',flush=True)
    if (sha(Path(profile)/'manifest.json')!=model.receipt['profile_manifest_sha256'] or
            sha(Path(profile)/'profile.npz')!=model.receipt['profile_sha256'] or
            sha(model.terrain.folder/'manifest.json')!=model.receipt['terrain_manifest_sha256']):
        raise ValueError('Source profile or terrain changed during depth inference')
    out.mkdir(parents=True)
    np.savez_compressed(out/'depth.npz',station_m=model.station,depth_amplitude_m=depth,
        previous_depth_amplitude_m=model.depth,available_width_m=np.asarray(width),
        capacity_chart_station_m=frame['station'],capacity_chart_source_station_m=frame['source_station'],
        previous_capacity_m3s=before,inferred_capacity_m3s=after)
    receipt=dict(schema='raftsim.chilko_available_channel_depth.v1',
        source_profile_manifest=str(Path(profile).resolve()/'manifest.json'),
        source_profile_sha256=model.receipt['profile_manifest_sha256'],
        source_terrain_sha256=model.receipt['terrain_manifest_sha256'],
        source_route_sha256=model.receipt['route_sha256'],source_planform_sha256=model.receipt['planform_sha256'],
        ownership_policy=model.receipt['ownership_policy'],discharge_m3s=discharge,manning_n=roughness,
        depth_sha256=sha(out/'depth.npz'),section_spacing_m=4.,lateral_spacing_m=1.,lateral_half_extent_m=256.,
        capacity_section_spacing_m=2.,capacity_chart_coverage=coverage,
        numerical_chart_policy=chart_policy,
        capacity_policy='Non-overlapping numerical cross sections; conservative per-cell source-node amplitude constraints. Estimated Manning capacity, not measured branch discharge or native flux.',
        maximum_allowed_amplitude_m=10.,maximum_amplitude_m=float(depth.max()),
        changed_section_count=int((depth>model.depth+1e-6).sum()),
        previous_capacity_percentiles_m3s=np.nanpercentile(before,[0,5,50,95,100]).tolist(),
        inferred_capacity_percentiles_m3s=np.nanpercentile(after,[0,5,50,95,100]).tolist(),
        capacity_values_are_lower_bounds_before_geographic_envelope=True,
        endpoint_policy='Original source nodes constrained only by interior chart cells; no geometry extrapolation beyond route endpoints',
        scope='Available-channel Manning depth inference, preserving local emergent features; not measured bathymetry or solved flow',
        hydraulic_solution=False,engine_validated=False)
    (out/'manifest.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps(receipt,indent=2));return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('terrain','profile','out'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--discharge',type=float,default=45.,help='Construction discharge in m3/s; not measured local flow')
    parser.add_argument('--roughness',type=float,default=.045,help='Inferred Manning n, not the native friction coefficient')
    a=parser.parse_args();build(a.terrain,a.profile,a.out,a.discharge,a.roughness)
