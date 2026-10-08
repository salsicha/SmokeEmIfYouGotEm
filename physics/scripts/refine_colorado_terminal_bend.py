"""Repair a terminal numerical-chart fold without changing captured geography.

The source endpoint and cross-section stay exact. Only the final bounded chart
window is smoothed/reparameterized; all affected inputs must be rebuilt. This
does not establish terrain coverage, a valid wet domain or accepted hydraulics.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np

from anchor_colorado_terminal_frame import checked_arrays,source_end_caps
from build_colorado_catalog_evidence import ROOT,sha
from build_colorado_catalog_windows import read_profile
from build_colorado_continuous_assembly import native_progress_points
from build_hance_curvilinear_scenario import gauss_smooth


def refine(arrays,window_m,smoothing_m):
    old=checked_arrays(arrays);s=old['station_m']
    parameters=np.asarray([window_m,smoothing_m],dtype=float)
    if (not np.isfinite(parameters).all() or not 600<=window_m<=3000 or window_m%2 or
            window_m>=s[-1]-10 or not 60<smoothing_m<=300 or smoothing_m>window_m/4):
        raise ValueError('Bounded 2 m-aligned terminal window and smoothing required')
    start=int(np.searchsorted(s,s[-1]-window_m));xy=old['east_north_m'][start:]
    t=s[start:]-s[start];length=t[-1]
    smooth=np.column_stack([gauss_smooth(xy[:,k],smoothing_m/2) for k in range(2)])
    u=np.clip(t/(window_m/2),0,1)
    weight=10*u**3-15*u**4+6*u**5
    points=xy+(smooth-xy)*weight[:,None]
    velocity=np.column_stack([np.gradient(points[:,k],2.) for k in range(2)])
    direction=np.array([old['normal_east_north'][-1,1],-old['normal_east_north'][-1,0]])
    # Endpoint position and tangent correction, zero value/derivative at the
    # upstream seam. This is a numerical axis, not interpolated source terrain.
    delta=xy[-1]-points[-1];dv=direction-velocity[-1];u=t/length
    points+=(-2*u**3+3*u**2)[:,None]*delta+(u**3-u**2)[:,None]*length*dv
    points[0]=xy[0];points[-1]=xy[-1]
    displacement=float(np.linalg.norm(points-xy,axis=1).max())
    if displacement>100:raise ValueError('Terminal numerical-axis displacement exceeds 100 m review limit')
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    if not np.isfinite(arc).all() or np.any(np.diff(arc)<=1e-8):
        raise ValueError('Degenerate terminal numerical axis')
    # Reparameterize only this window, preserving every upstream station and
    # source association. Spread the <1 m lattice remainder over this window.
    n=int(round(arc[-1]/2));sample=np.linspace(0,arc[-1],n+1)
    curve=np.column_stack([np.interp(sample,arc,points[:,k]) for k in range(2)])
    curve[0]=xy[0];curve[-1]=xy[-1]
    whole=np.vstack([old['east_north_m'][:start],curve]);station=np.arange(len(whole))*2.
    derivative=np.column_stack([np.gradient(whole[:,k],2.) for k in range(2)])
    speed=np.linalg.norm(derivative,axis=1)
    segment=np.linalg.norm(np.diff(whole[start:],axis=0),axis=1)/2
    if (not np.isfinite(speed).all() or np.any(speed<=1e-8) or
            np.any(speed[start:]<.95) or np.any(speed[start:]>1.05) or
            np.any(segment<.95) or np.any(segment>1.05)):
        raise ValueError('Terminal chart scale distortion exceeds 5 percent')
    tangent=derivative/speed[:,None]
    if float(tangent[-1]@direction)<.999:
        raise ValueError('Terminal resampling no longer follows the captured end direction')
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    normal[:start-2]=old['normal_east_north'][:start-2]
    normal[-1]=old['normal_east_north'][-1]
    tangent=np.column_stack([normal[:,1],-normal[:,0]])
    curvature=tangent[:,0]*np.gradient(tangent[:,1],2.)-tangent[:,1]*np.gradient(tangent[:,0],2.)
    curvature[:start-3]=old['curvature_per_m'][:start-3]
    source=np.r_[old['source_global_station_m'][:start],np.interp(sample,arc,old['source_global_station_m'][start:])]
    result=checked_arrays(dict(station_m=station,east_north_m=whole,normal_east_north=normal,
        curvature_per_m=curvature,source_global_station_m=source))
    if (any(not np.array_equal(result[k][:start-3],old[k][:start-3]) for k in old) or
            source[-1]!=old['source_global_station_m'][-1]):
        raise ValueError('Terminal repair changed the upstream prefix or captured endpoint station')
    receipt=dict(window_m=float(window_m),smoothing_m=float(smoothing_m),
        unchanged_prefix_points=start-3,changed_from_hydraulic_station_m=float(s[start-3]),
        maximum_numerical_axis_displacement_m=displacement,
        segment_scale_range=[float(segment.min()),float(segment.max())],
        endpoint_position_and_normal_preserved=True,captured_geometry_modified=False,
        terrain_modified=False,source_water_classification_modified=False)
    return result,receipt


def build(original,out,window_m=1200.,smoothing_m=90.):
    original=Path(original).resolve();out=Path(out).resolve()
    if out.exists():raise ValueError('Fresh terminal-bend chart required')
    path=original/'manifest.json';manifest=json.loads(path.read_text())
    if (manifest.get('schema')!='raftsim.colorado_shared_hydraulic_frame.v1' or
            'source_endpoint_anchor' not in manifest or 'terminal_bend_refinement' in manifest):
        raise ValueError('Expected endpoint-anchored chart without a terminal-bend refinement')
    protected={path:sha(path)}
    for name in ('frame.npz','coordinate_map.json'):
        p=original/name;digest=sha(p)
        if digest!=manifest['files_sha256'][name]:raise ValueError('Changed parent chart')
        protected[p]=digest
    source=ROOT/manifest['source_profile'];protected[source]=sha(source)
    if protected[source]!=manifest['source_profile_sha256']:raise ValueError('Changed captured source profile')
    caps=source_end_caps(read_profile(source))
    with np.load(original/'frame.npz',allow_pickle=False) as saved:old=checked_arrays(dict(saved))
    direction=np.asarray(caps['directions'][-1])
    if (manifest['source_endpoint_anchor']['source_end_caps']!=caps or
            old['source_global_station_m'][-1]!=caps['stations'][-1] or
            not np.array_equal(old['east_north_m'][-1],caps['positions'][-1]) or
            not np.array_equal(old['normal_east_north'][-1],[-direction[1],direction[0]])):
        raise ValueError('Parent chart does not match the captured terminal cross-section')
    arrays,receipt=refine(old,window_m,smoothing_m)
    mapping=json.loads((original/'coordinate_map.json').read_text())
    mapping['points']=native_progress_points(arrays['station_m'],arrays['east_north_m'],arrays['normal_east_north'],np.array(mapping['horizontal_origin_epsg6404_m']))
    mapping['mapping_policy']+='; bounded terminal numerical-bend refinement with exact captured endpoint and normal'
    if any(sha(p)!=h for p,h in protected.items()):raise ValueError('Inputs changed during terminal repair')
    out.mkdir(parents=True);np.savez_compressed(out/'frame.npz',**arrays)
    (out/'coordinate_map.json').write_text(json.dumps(mapping,separators=(',',':'),allow_nan=False)+'\n')
    result=copy.deepcopy(manifest)
    result.update(hydraulic_station_range_m=[0.,float(arrays['station_m'][-1])],
        source_station_range_m=[0.,float(arrays['source_global_station_m'][-1])],
        files_sha256={n:sha(out/n) for n in ('frame.npz','coordinate_map.json')},runtime_ready=False)
    result['terminal_bend_refinement']=dict(**receipt,parent_manifest=path.relative_to(ROOT).as_posix(),
        parent_manifest_sha256=protected[path],source_files_unchanged=True)
    result['source_endpoint_anchor']['identity_receipt_scope']='Original endpoint anchoring stage; terminal_bend_refinement changes the final chart while preserving that exact captured endpoint and normal'
    result['limitations']+=['Rebuild affected tail inputs and validate full-width water coverage and folds; terminal chart generation is not hydraulic or playable acceptance.']
    if any(sha(p)!=h for p,h in protected.items()):raise ValueError('Inputs changed before terminal receipt')
    (out/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--window-m',type=float,default=1200.);p.add_argument('--smoothing-m',type=float,default=90.)
    a=p.parse_args();print(json.dumps(build(a.original,a.out,a.window_m,a.smoothing_m),indent=2))
