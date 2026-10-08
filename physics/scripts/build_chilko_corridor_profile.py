"""Build one source-referenced Chilko longitudinal profile over the full route.

FWA defines mapped planform, not surveyed flight-day banks. DEM channel pixels
support an INFERRED surface reference, never measured bathymetry. No rapid
names or boundaries are assigned, and no hydraulic field is promoted here.
The single global reference avoids independently inferred tile-end stages.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString

from build_pacuare_evidence_grid import pava_nonincreasing
from chilko_planform import load_planform, route_planform_policy
from correct_chilko_route import compatible_capture_route
from chilko_corridor_chart import directions_at_source_points
from chilko_corridor_terrain import CorridorTerrain
from mosaic_lidarbc_crops import sha
from plan_lidarbc_corridor_capture import route_xy


def mapped_span(lateral, mapped):
    zero=np.flatnonzero(lateral==0)
    if len(zero)!=1 or not mapped[zero[0]]:
        raise ValueError('Source route leaves mapped river; review geography before inferring channel')
    left=right=int(zero[0])
    while left>0 and mapped[left-1]:left-=1
    while right+1<len(mapped) and mapped[right+1]:right+=1
    if left==0 or right==len(mapped)-1:
        raise ValueError('Mapped channel exceeds sampled width; no clamped bank permitted')
    return left,right


def local_reference_support(projected_station, section_station, half_width=2.):
    """Use evidence at this source station, not low samples from another bend.

    Non-mapped samples may have missing projections and cannot contribute.
    This filter changes reference support only, never the mapped bank span.
    """
    projected_station=np.asarray(projected_station,dtype=float)
    if (projected_station.ndim!=1 or not np.isfinite([section_station,half_width]).all()
            or not 0<half_width<=10.):
        raise ValueError('One-dimensional projections and bounded station window required')
    return np.isfinite(projected_station)&(abs(projected_station-section_station)<=half_width+1e-8)


def channel_section(lateral, mapped, height, kind, reference_support=None):
    lateral=np.asarray(lateral,dtype=float);mapped=np.asarray(mapped,dtype=bool)
    height,kind=np.asarray(height),np.asarray(kind)
    if (lateral.ndim!=1 or len(lateral)<3 or any(a.shape!=lateral.shape for a in (mapped,height,kind)) or
            not np.isfinite(lateral).all() or lateral[1]-lateral[0] not in (1.,2.) or
            not np.allclose(np.diff(lateral),lateral[1]-lateral[0],atol=1e-12,rtol=0) or
            not np.isin(kind,[0,1,2,3]).all() or not np.array_equal(np.isfinite(height),kind>0)):
        raise ValueError('Aligned one/two-metre lateral samples with explicit terrain provenance required')
    spacing=lateral[1]-lateral[0]
    left,right=mapped_span(lateral,mapped)
    # Retain only the component containing the source route, not nearby braids
    # or the far side of an island. Exclude at least 3 m next to mapped banks.
    erosion=int(np.ceil(3./spacing))
    interior=np.arange(left+erosion,right-erosion+1)
    if not np.isfinite(height[left:right+1]).all():
        raise ValueError('Channel interior has missing terrain support')
    if len(interior)<3:
        raise ValueError('Insufficient supported channel interior')
    if reference_support is not None:
        reference_support=np.asarray(reference_support)
        if reference_support.shape!=lateral.shape or reference_support.dtype.kind!='b':
            raise ValueError('Boolean source-local reference support required')
        interior=interior[reference_support[interior]]
        if len(interior)<3:
            raise ValueError('Insufficient source-local reference support')
    low=float(np.percentile(height[interior],20))
    support=interior[height[interior]<=low+.25]
    reference=float(np.median(height[support]))
    return dict(right_bank_m=float(lateral[left]-spacing/2),left_bank_m=float(lateral[right]+spacing/2),
        width_m=float((right-left+1)*spacing),reference_m=reference,support_count=len(support),
        native_support_count=int((kind[support]==1).sum()),
        surface_sample_range_m=[float(height[support].min()),float(height[support].max())],
        surface_source_kind=int(kind[support].max()))


def reference_weights(sections):
    """Resolution-based inference weights, not a statistical accuracy estimate.

    Resampling one 30 m fallback pixel to 900 one-metre pixels must not grant
    900 native observations' influence on the common longitudinal reference.
    Conditioned fallback remains coarse; it does not become a LiDAR sample.
    """
    weights=[]
    for row in sections:
        if row is None or not np.isfinite(row['reference_m']):continue
        total=row['support_count'];native=row['native_support_count']
        if not np.isfinite([total,native]).all() or not 0<=native<=total or total<=0:
            raise ValueError('Finite native/coarse reference support counts required')
        weights.append(native+(total-native)/900.)
    return np.asarray(weights,dtype=float)


def surface_reference(sections):
    """Record unsupported sections as missing, never interpolate through them."""
    supported=np.array([r is not None and np.isfinite(r['reference_m']) for r in sections])
    raw=np.array([r['reference_m'] if r else np.nan for r in sections])
    result=np.full(raw.shape,np.nan)
    if supported.any():
        weights=reference_weights(sections)
        result[supported]=pava_nonincreasing(raw[supported],weights)
    return raw,result,supported


def bridge_short_reference_gaps(station, reference):
    """Explicitly infer only interior gaps bounded by <=20 m and <=0.25 m drop.

    This does not repair missing terrain, move banks, widen the river, modify
    raw evidence, or turn these interpolated stages into measurements.
    """
    station,reference=np.asarray(station,dtype=float),np.asarray(reference,dtype=float)
    if (station.ndim!=1 or station.shape!=reference.shape or not np.isfinite(station).all() or
            np.any(np.diff(station)<=0) or np.isinf(reference).any()):
        raise ValueError('Ordered reference stations required')
    result=reference.copy();records=[]
    edges=np.flatnonzero(np.diff(np.r_[False,~np.isfinite(reference),False]))
    for start,end in zip(edges[::2],edges[1::2]):
        if start==0 or end==len(station):continue
        span=station[end]-station[start-1];drop=reference[start-1]-reference[end]
        if span>20.+1e-8 or not 0<=drop<=.25:continue
        result[start:end]=np.interp(station[start:end],station[[start-1,end]],reference[[start-1,end]])
        records.append(dict(upstream_station_m=float(station[start-1]),downstream_station_m=float(station[end]),
            span_m=float(span),drop_m=float(drop),inferred_sections=int(end-start),
            method='linear stage interpolation only; original missing reference samples retained'))
    return result,records


def build(terrain_path,route,planform,out,step=4.,diagnostic_gaps=False,bridge_short_gaps=False,chart_directions=False,reference_window_m=2.):
    if out.exists():raise ValueError('Fresh corridor profile required')
    if not np.isfinite(step) or not 1<=step<=10:raise ValueError('Bounded positive route spacing required')
    if not np.isfinite(reference_window_m) or not 0<reference_window_m<=10:
        raise ValueError('Bounded source-local reference window required')
    terrain=CorridorTerrain(terrain_path);receipt=sha(terrain.folder/'manifest.json')
    if not terrain.conditioned or not compatible_capture_route(route,terrain.manifest['route_sha256']):
        raise ValueError('Verified conditioned terrain on the same FWA route required')
    polygon=load_planform(planform,route)
    shapely.prepare(polygon)
    xy=route_xy(route);chain=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
    station=np.r_[np.arange(0,chain[-1],step),chain[-1]]
    points=np.c_[np.interp(station,chain,xy[:,0]),np.interp(station,chain,xy[:,1])]
    tangent=np.gradient(points,station,axis=0);norm=np.linalg.norm(tangent,axis=1)
    if (norm<1e-6).any():raise ValueError('Degenerate source route direction')
    normal=np.c_[-tangent[:,1],tangent[:,0]]/norm[:,None]
    source_line=LineString(xy)
    if chart_directions:normal=directions_at_source_points(source_line,points)
    lateral=np.arange(-320,321,1.);sections=[];rejected=[]
    for start in range(0,len(points),256):
        p=points[start:start+256,None,:]+lateral[None,:,None]*normal[start:start+256,None,:]
        inside=shapely.contains_xy(polygon,p[...,0],p[...,1])
        h,k=terrain.sample(p)
        projected=np.full(inside.shape,np.nan)
        projected[inside]=shapely.line_locate_point(source_line,shapely.points(p[inside]))
        for i in range(len(p)):
            support=local_reference_support(projected[i],station[start+i],reference_window_m)
            try:sections.append(channel_section(lateral,inside[i],h[i],k[i],support))
            except ValueError as e:
                if not diagnostic_gaps and not bridge_short_gaps:raise ValueError(f'FWA station {station[start+i]:.3f} m: {e}') from e
                if str(e) not in ('Insufficient supported channel interior',
                        'Insufficient source-local reference support',
                        'Source route leaves mapped river; review geography before inferring channel',
                        'Mapped channel exceeds sampled width; no clamped bank permitted'):
                    raise
                if str(e) in ('Insufficient supported channel interior','Insufficient source-local reference support'):
                    left,right=mapped_span(lateral,inside[i])
                    sections.append(dict(right_bank_m=float(lateral[left]-.5),left_bank_m=float(lateral[right]+.5),
                        width_m=float(right-left+1),reference_m=np.nan,support_count=0,native_support_count=0,
                        surface_sample_range_m=[np.nan,np.nan],surface_source_kind=0))
                else:sections.append(None)
                rejected.append(dict(index=start+i,station_m=float(station[start+i]),reason=str(e)))
        print(f'profile sections {len(sections)}/{len(station)}',flush=True)
    raw,reference,supported=surface_reference(sections)
    if not supported.any() or not np.isfinite(reference[supported]).all() or (np.diff(reference[supported])>1e-8).any():
        raise ValueError('Invalid inferred global surface')
    if bridge_short_gaps and any(r['reason']!='Insufficient supported channel interior' for r in rejected):
        failures=[r for r in rejected if r['reason']!='Insufficient supported channel interior']
        raise ValueError('Only narrow mapped branches may use bounded stage inference: '+json.dumps(failures))
    reference,gap_records=bridge_short_reference_gaps(station,reference) if bridge_short_gaps else (reference,[])
    valid_sections=[r for r in sections if r]
    have_section=np.array([r is not None for r in sections])
    arrays={}
    for key in valid_sections[0]:
        if key=='reference_m':continue
        values=np.full((len(sections),)+np.shape(valid_sections[0][key]),np.nan)
        values[have_section]=np.asarray([r[key] for r in valid_sections])
        arrays[key]=values
    out.mkdir(parents=True)
    np.savez_compressed(out/'profile.npz',station_m=station,xy_m=points,normal_xy=normal,
        raw_reference_m=raw,reference_m=reference,supported=supported,
        interpolated_reference=~supported&np.isfinite(reference),**arrays)
    result=dict(schema='raftsim.chilko_corridor_profile.v1',river_id='chilko_river_bc',
        horizontal_crs='EPSG:3157',vertical_reference='CGVD2013 (EPSG:6647)',
        station_frame='EPSG:3157 arc length along exact FWA source vertices; not smoothed runtime station',
        route_length_m=float(chain[-1]),sample_count=len(station),station_spacing_m=step,lateral_spacing_m=1.,
        source_terrain=dict(manifest=str(terrain.folder/'manifest.json'),sha256=receipt),
        route=dict(path=str(route.resolve()),sha256=sha(route)),
        planform=dict(path=str(planform.resolve()),sha256=sha(planform),metadata_sha256=sha(planform.with_suffix('.json'))),
        planform_policy=route_planform_policy(route),
        cross_section_direction_policy=('Shared full-route 320 m Gaussian numerical chart, 64 m endpoint extension; directions projected onto exact geographic anchors, not measured flow' if chart_directions else 'Raw exact-route finite-difference tangent'),
        profile_sha256=sha(out/'profile.npz'),
        inference='Source-station-local channel-interior DEM samples within 0.25 m of local interior p20, median then global resolution-weighted nonincreasing regression; no water-level survey',
        reference_support_policy=dict(kind='exact_source_route_projection_window_v1',
            station_half_width_m=float(reference_window_m),minimum_local_interior_samples=3,
            bank_margin_m=3.,remote_reference_fallback=False,
            qualification='Reference support is restricted to its actual geographic source station; bank spans and source terrain are unchanged. Missing local support remains an explicit refusal.'),
        regression_weight_policy=dict(native_1m_support_weight=1.,coarse_30m_support_weight=1./900.,
            conditioned_fallback_remains_coarse=True,
            qualification='Resolution-based inference weight, not measured sensor accuracy or independent statistical samples'),
        terrain_source_kind=terrain.manifest['source_kind'],
        regression_abs_adjustment_p95_m=float(np.percentile(abs(reference[supported]-raw[supported]),95)),
        regression_abs_adjustment_max_m=float(abs(reference[supported]-raw[supported]).max()),
        native_only_reference_sections=sum(r['surface_source_kind']==1 for r in valid_sections),
        sampled_width_range_m=[min(r['width_m'] for r in valid_sections),max(r['width_m'] for r in valid_sections)],
        continuous_reference_complete=bool(np.isfinite(reference).all()),rejected_source_sections=rejected,
        inferred_reference_gaps=gap_records,
        diagnostic_only=diagnostic_gaps,unsupported_reference_policy='Raw NaN retained; only explicitly listed narrow-branch stage gaps may be inferred; no generated riverbed',
        named_rapid_bounds=False,measured_surface=False,measured_bed=False,hydraulic_bed_ready=False,engine_validated=False)
    if sha(terrain.folder/'manifest.json')!=receipt:raise ValueError('Terrain changed during profiling')
    (out/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('terrain','route','planform','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--diagnostic-gaps',action='store_true',help='Record ALL unsupported sections as NaN; never a complete construction profile')
    p.add_argument('--bridge-short-reference-gaps',action='store_true',help='Explicit inferred stage across narrow branches only: source anchors at most 20 m apart and 0.25 m drop')
    p.add_argument('--chart-directions',action='store_true',help='Orient exact route anchors across the existing shared full-domain numerical chart')
    p.add_argument('--reference-window-m',type=float,default=2.,help='Maximum geographic source-station offset for DEM reference samples; no remote-bend fallback')
    a=p.parse_args();r=build(a.terrain,a.route,a.planform,a.out,diagnostic_gaps=a.diagnostic_gaps,bridge_short_gaps=a.bridge_short_reference_gaps,chart_directions=a.chart_directions,reference_window_m=a.reference_window_m)
    print(json.dumps({k:v for k,v in r.items() if k!='rejected_source_sections'},indent=2))
    print('unsupported_source_sections',len(r['rejected_source_sections']))
