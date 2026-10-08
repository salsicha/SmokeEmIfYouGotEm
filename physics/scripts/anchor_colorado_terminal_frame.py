"""Anchor the numerical chart to the captured terminal cross-section.

Only the numerical chart changes. The last source point and direction are
measured inputs; bed, water classification and terrain are never extended.
Fresh downstream inputs must still pass coverage, folding and native gates.
"""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
from build_colorado_catalog_evidence import ROOT,sha
from build_colorado_catalog_windows import read_profile
from build_colorado_continuous_assembly import native_progress_points


def source_end_caps(rows):
    xy=np.asarray([[r['easting'],r['northing']] for r in rows],dtype=float)
    if len(xy)<3 or not np.isfinite(xy).all():raise ValueError('Invalid captured source')
    delta=np.diff(xy,axis=0);length=np.linalg.norm(delta,axis=1)
    if np.any(length<=0) or np.any(length>40):raise ValueError('Disconnected captured source')
    # Match the source index's cumulative arithmetic, not a differently
    # rounded reduction followed by an endpoint-bracketing tolerance.
    end=float(np.cumsum(length)[-1])
    return dict(stations=[0.,end],positions=xy[[0,-1]].tolist(),
        directions=(delta[[0,-1]]/length[[0,-1],None]).tolist())


def checked_arrays(arrays):
    expected={'station_m','east_north_m','normal_east_north','curvature_per_m','source_global_station_m'}
    if set(arrays)!=expected:raise ValueError('Unexpected chart arrays')
    old={k:np.asarray(v,dtype=float) for k,v in arrays.items()}
    s=old['station_m'];xy=old['east_north_m'];source=old['source_global_station_m']
    if (s.ndim!=1 or len(s)<110 or xy.shape!=(len(s),2) or
        old['normal_east_north'].shape!=xy.shape or old['curvature_per_m'].shape!=s.shape or source.shape!=s.shape or
        not all(np.isfinite(v).all() for v in old.values()) or s[0]!=0 or
        not np.all(np.diff(s)==2.) or np.any(np.diff(source)<=0) or source[0]!=0 or
        not np.allclose(np.linalg.norm(old['normal_east_north'],axis=1),1.,atol=1e-9,rtol=0)):
        raise ValueError('Expected finite, monotonic complete 2 m shared chart')
    return old


def anchor_terminal(arrays,rows,blend_m=200.):
    old=checked_arrays(arrays)
    s=old['station_m'];xy=old['east_north_m'];source=old['source_global_station_m']
    caps=source_end_caps(rows);endpoint=np.array(caps['positions'][-1]);direction=np.array(caps['directions'][-1])
    remaining=caps['stations'][-1]-source[-1]
    if not 0<remaining<=4.:raise ValueError('Only the unresolved final sampling interval may be anchored')
    if not np.isfinite(blend_m) or not 100<=blend_m<=600 or blend_m%2 or blend_m>=s[-1]-10:
        raise ValueError('Bounded 2 m-aligned terminal blend required')
    station=np.r_[s,s[-1]+2.];start=station[-1]-blend_m
    first=int(np.searchsorted(station,start));prefix=first-2
    velocity=np.column_stack([np.gradient(xy[:,i],2.) for i in range(2)])
    # This is a numerical-axis tangent continuation for one grid interval,
    # not extrapolated source terrain. The correction ends exactly at the
    # captured point and aligns its normal with the captured end plane.
    base=np.vstack([xy,xy[-1]+2.*velocity[-1]])
    base_velocity=np.vstack([velocity,velocity[-1]])
    delta=endpoint-base[-1];dv=direction-base_velocity[-1]
    if np.linalg.norm(delta)>10:raise ValueError('Terminal correction exceeds the local sampling defect')
    u=np.clip((station-start)/blend_m,0.,1.)
    correction=(-2*u**3+3*u**2)[:,None]*delta+(u**3-u**2)[:,None]*blend_m*dv
    derivative=((-6*u**2+6*u)/blend_m)[:,None]*delta+(3*u**2-2*u)[:,None]*dv
    points=base+correction;points[-1]=endpoint
    tangent=base_velocity+derivative;tangent[-1]=direction
    speed=np.linalg.norm(tangent,axis=1)
    segment_speed=np.linalg.norm(np.diff(points,axis=0),axis=1)/2.
    if (np.any(speed[first:]<.95) or np.any(speed[first:]>1.05) or
            np.any(segment_speed[first:]<.95) or np.any(segment_speed[first:]>1.05)):
        raise ValueError('Terminal chart scale distortion exceeds 5 percent')
    tangent/=speed[:,None]
    normal=np.vstack([old['normal_east_north'],[-direction[1],direction[0]]])
    normal[first:]=np.column_stack([-tangent[first:,1],tangent[first:,0]])
    normal[-1]=[-direction[1],direction[0]]
    t=np.column_stack([normal[:,1],-normal[:,0]])
    curvature=np.r_[old['curvature_per_m'],0.]
    computed=t[:,0]*np.gradient(t[:,1],2.)-t[:,1]*np.gradient(t[:,0],2.)
    curvature[prefix:]=computed[prefix:]
    result=dict(station_m=station,east_north_m=points,normal_east_north=normal,
        curvature_per_m=curvature,source_global_station_m=np.r_[source,caps['stations'][-1]])
    if any(not np.array_equal(result[k][:prefix],old[k][:prefix]) for k in old):
        raise ValueError('Endpoint repair changed the upstream chart')
    return result,dict(blend_m=blend_m,blend_start_station_m=start,
        unchanged_prefix_points=prefix,source_end_caps=caps,missing_source_interval_m=remaining,
        terminal_segment_scale_range=[float(segment_speed[first:].min()),float(segment_speed[first:].max())],
        terminal_tangent_scale_range=[float(speed[first:].min()),float(speed[first:].max())],
        maximum_numerical_correction_m=float(np.linalg.norm(correction,axis=1).max()),
        captured_geometry_modified=False,terrain_extrapolated=False,endpoint_curvature_recomputed=True)


def anchor_initial(arrays,rows,blend_m=200.):
    old=checked_arrays(arrays);s=old['station_m'];xy=old['east_north_m']
    if not np.isfinite(blend_m) or not 100<=blend_m<=600 or blend_m%2 or blend_m>=s[-1]-10:
        raise ValueError('Bounded 2 m-aligned initial blend required')
    caps=source_end_caps(rows);endpoint=np.array(caps['positions'][0]);direction=np.array(caps['directions'][0])
    velocity=np.column_stack([np.gradient(xy[:,i],2.) for i in range(2)])
    delta=endpoint-xy[0];dv=direction-velocity[0]
    if np.linalg.norm(delta)>10:raise ValueError('Initial correction exceeds the local sampling defect')
    u=np.clip(s/blend_m,0.,1.)
    correction=(2*u**3-3*u**2+1)[:,None]*delta+(u**3-2*u**2+u)[:,None]*blend_m*dv
    derivative=((6*u**2-6*u)/blend_m)[:,None]*delta+(3*u**2-4*u+1)[:,None]*dv
    points=xy+correction;points[0]=endpoint
    tangent=velocity+derivative;tangent[0]=direction
    last=int(blend_m/2)+1;suffix=last+2
    speed=np.linalg.norm(tangent,axis=1)
    segment_speed=np.linalg.norm(np.diff(points,axis=0),axis=1)/2.
    if (np.any(speed[:last]<.95) or np.any(speed[:last]>1.05) or
            np.any(segment_speed[:last]<.95) or np.any(segment_speed[:last]>1.05)):
        raise ValueError('Initial chart scale distortion exceeds 5 percent')
    tangent/=speed[:,None];normal=old['normal_east_north'].copy()
    normal[:last]=np.column_stack([-tangent[:last,1],tangent[:last,0]])
    normal[0]=[-direction[1],direction[0]]
    t=np.column_stack([normal[:,1],-normal[:,0]])
    curvature=old['curvature_per_m'].copy()
    computed=t[:,0]*np.gradient(t[:,1],2.)-t[:,1]*np.gradient(t[:,0],2.)
    curvature[:suffix]=computed[:suffix]
    result={k:v.copy() for k,v in old.items()}
    result.update(east_north_m=points,normal_east_north=normal,curvature_per_m=curvature)
    if any(not np.array_equal(result[k][suffix:],old[k][suffix:]) for k in old):
        raise ValueError('Initial repair changed the downstream chart')
    return result,dict(blend_m=blend_m,unchanged_suffix_from_point=suffix,source_end_caps=caps,
        initial_segment_scale_range=[float(segment_speed[:last].min()),float(segment_speed[:last].max())],
        initial_tangent_scale_range=[float(speed[:last].min()),float(speed[:last].max())],
        maximum_numerical_correction_m=float(np.linalg.norm(correction,axis=1).max()),
        captured_geometry_modified=False,terrain_extrapolated=False,endpoint_curvature_recomputed=True)


def build(original,out,blend_m=200.,endpoint='end'):
    original=Path(original).resolve();out=Path(out).resolve()
    if out.exists():raise ValueError('Fresh endpoint chart required')
    manifest_path=original/'manifest.json';manifest=json.loads(manifest_path.read_text())
    if endpoint not in ('start','end'):raise ValueError('Expected start or end anchor')
    receipt_key='source_endpoint_anchor' if endpoint=='end' else 'source_start_anchor'
    if manifest.get('schema')!='raftsim.colorado_shared_hydraulic_frame.v1' or manifest.get(receipt_key):
        raise ValueError('Expected a shared chart without a prior anchor at this end')
    if endpoint=='start' and not manifest.get('source_endpoint_anchor'):
        raise ValueError('Anchor the exact terminal source endpoint before the initial cross-section')
    protected={manifest_path:sha(manifest_path)}
    for name in ('frame.npz','coordinate_map.json'):
        p=original/name;h=sha(p)
        if h!=manifest['files_sha256'][name]:raise ValueError('Changed original chart')
        protected[p]=h
    source=ROOT/manifest['source_profile'];protected[source]=sha(source)
    if protected[source]!=manifest['source_profile_sha256']:raise ValueError('Changed captured source')
    anchor=anchor_terminal if endpoint=='end' else anchor_initial
    with np.load(original/'frame.npz',allow_pickle=False) as saved:arrays,receipt=anchor(dict(saved),read_profile(source),blend_m)
    mapping=json.loads((original/'coordinate_map.json').read_text())
    mapping['points']=native_progress_points(arrays['station_m'],arrays['east_north_m'],arrays['normal_east_north'],np.array(mapping['horizontal_origin_epsg6404_m']))
    mapping['mapping_policy']+='; bounded '+endpoint+' chart correction to the exact captured endpoint and cross-section'
    if any(sha(p)!=h for p,h in protected.items()):raise ValueError('Inputs changed during endpoint repair')
    out.mkdir(parents=True);np.savez_compressed(out/'frame.npz',**arrays)
    (out/'coordinate_map.json').write_text(json.dumps(mapping,separators=(',',':'),allow_nan=False)+'\n')
    result=copy.deepcopy(manifest)
    result.update(hydraulic_station_range_m=[0.,float(arrays['station_m'][-1])],
        source_station_range_m=[0.,float(arrays['source_global_station_m'][-1])],
        files_sha256={n:sha(out/n) for n in ('frame.npz','coordinate_map.json')},runtime_ready=False)
    result[receipt_key]=dict(**receipt,parent_manifest=manifest_path.relative_to(ROOT).as_posix(),parent_manifest_sha256=protected[manifest_path])
    if endpoint=='start' and 'numerical_chart_refinement' in result:
        result['numerical_chart_refinement']['identity_receipt_scope']='Intermediate bend-refinement stage only; source_start_anchor changes the initial prefix of the final combined chart'
    limitation='Endpoint anchoring does not certify bed coverage, physical-space wet metrics, source footprint, solver convergence or runtime acceptance.'
    if limitation not in result['limitations']:result['limitations'].append(limitation)
    if any(sha(p)!=h for p,h in protected.items()):raise ValueError('Inputs changed before endpoint receipt')
    (out/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--blend-m',type=float,default=200.)
    p.add_argument('--endpoint',choices=('start','end'),default='end')
    a=p.parse_args();print(json.dumps(build(a.original,a.out,a.blend_m,a.endpoint),indent=2))
