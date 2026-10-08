"""Local numerical-chart repair; never move geographic terrain or water sources.

Produces a fresh shared chart, not a valid hydraulic cook. All affected inputs
must be rebuilt and pass the existing coverage/folding/shoreline gates. Old
cooks may only be reused where the full coordinate arrays are exactly equal.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator

from build_colorado_catalog_evidence import ROOT, sha
from build_colorado_catalog_windows import read_profile
from build_colorado_continuous_assembly import native_progress_points
from build_hance_curvilinear_scenario import gauss_smooth


def resample(dense, source_station, step=2.):
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(dense,axis=0),axis=1))]
    if not np.isfinite(arc).all() or np.any(np.diff(arc)<1e-6):
        raise ValueError('Degenerate numerical chart')
    station=np.arange(0,arc[-1],step)
    xy=np.column_stack([np.interp(station,arc,dense[:,i]) for i in range(2)])
    tangent=np.column_stack([np.gradient(xy[:,i],step) for i in range(2)])
    lengths=np.linalg.norm(tangent,axis=1)
    if np.any(lengths<1e-8):raise ValueError('Degenerate numerical tangent')
    tangent/=lengths[:,None]
    curvature=tangent[:,0]*np.gradient(tangent[:,1],step)-tangent[:,1]*np.gradient(tangent[:,0],step)
    return dict(station_m=station,east_north_m=xy,
                normal_east_north=np.column_stack([-tangent[:,1],tangent[:,0]]),
                curvature_per_m=curvature,source_global_station_m=np.interp(station,arc,source_station))


def refined_arrays(rows, refinements):
    xy=np.array([[r['easting'],r['northing']] for r in rows],dtype=float)
    if len(xy)<3 or not np.isfinite(xy).all():raise ValueError('Invalid source profile')
    ds=np.linalg.norm(np.diff(xy,axis=0),axis=1)
    if np.any(ds<=0) or np.any(ds>40):raise ValueError('Disconnected source profile')
    source=np.r_[0.,np.cumsum(ds)]
    if source[-1]<8.:raise ValueError('Insufficient source length for 2 m chart')
    dense_s=np.arange(0,source[-1],2.)
    dense=PchipInterpolator(source,xy,axis=0)(dense_s)
    base=np.column_stack([gauss_smooth(dense[:,i],30.) for i in range(2)])
    candidate=base.copy();supports=[]
    if not isinstance(refinements,list) or not refinements:raise ValueError('Explicit refinements required')
    for patch in refinements:
        try:
            lo,hi=patch['source_plateau_interval_m'];taper=patch['taper_m'];sigma=patch['smoothing_m']
            values=np.array([lo,hi,taper,sigma],dtype=float)
        except (KeyError,TypeError,ValueError) as error:raise ValueError('Invalid refinement specification') from error
        lo,hi,taper,sigma=values
        if (not np.isfinite(values).all() or taper<60 or sigma<=60 or sigma>300 or
                hi<=lo or lo-taper<=0 or hi+taper>=dense_s[-1]):
            raise ValueError('Refinement must be bounded inside the captured route')
        support=(lo-taper,hi+taper)
        if any(max(support[0],a)<min(support[1],b) for a,b in supports):
            raise ValueError('Overlapping chart refinements require joint review')
        supports.append(support)
        weight=np.ones(len(dense_s));left=dense_s<lo;right=dense_s>hi
        weight[left]=.5-.5*np.cos(np.pi*np.clip((dense_s[left]-support[0])/taper,0,1))
        weight[right]=.5+.5*np.cos(np.pi*np.clip((dense_s[right]-hi)/taper,0,1))
        alternative=np.column_stack([gauss_smooth(dense[:,i],sigma/2.) for i in range(2)])
        candidate+=weight[:,None]*(alternative-base)
    before=resample(base,dense_s);after=resample(candidate,dense_s)
    # Gradients reach two grid cells ahead. A conservative 10 m buffer prevents
    # declaring a changed tangent/curvature equal at the first taper boundary.
    count=int(np.count_nonzero(before['source_global_station_m']<min(a for a,b in supports)-10.))
    if count<3 or any(not np.array_equal(before[k][:count],after[k][:count]) for k in before):
        raise ValueError('Chart refinement changed its upstream prefix')
    receipt=dict(refinements=copy.deepcopy(refinements),upstream_identical_point_count=count,
        upstream_identical_through_station_m=float(before['station_m'][count-1]),
        maximum_numerical_axis_displacement_m=float(np.linalg.norm(candidate-base,axis=1).max()),
        captured_geometry_modified=False,bed_modified=False,classified_water_modified=False)
    return before,after,receipt


def build(original, specification, out):
    original=Path(original).resolve();specification=Path(specification).resolve();out=Path(out).resolve()
    if out.exists():raise ValueError('Fresh refined chart output required')
    old_manifest=original/'manifest.json';manifest_sha=sha(old_manifest)
    manifest=json.loads(old_manifest.read_text());spec_sha=sha(specification)
    if (manifest.get('schema')!='raftsim.colorado_shared_hydraulic_frame.v1' or
            manifest.get('grid_step_m')!=2 or manifest.get('numerical_chart_refinement')):
        raise ValueError('Expected original 2 m, 60 m-smoothed shared chart')
    protected={old_manifest:manifest_sha,specification:spec_sha}
    for name in ('frame.npz','coordinate_map.json'):
        p=original/name;h=sha(p)
        if h!=manifest['files_sha256'][name]:raise ValueError('Changed original chart')
        protected[p]=h
    source=ROOT/manifest['source_profile'];protected[source]=sha(source)
    if protected[source]!=manifest['source_profile_sha256']:raise ValueError('Changed source profile')
    before,after,receipt=refined_arrays(read_profile(source),json.loads(specification.read_text()))
    with np.load(original/'frame.npz',allow_pickle=False) as saved:
        if set(saved.files)!=set(before) or any(not np.array_equal(saved[k],before[k]) for k in before):
            raise ValueError('Reconstructed baseline is not the registered original chart')
    mapping=json.loads((original/'coordinate_map.json').read_text())
    mapping['points']=native_progress_points(after['station_m'],after['east_north_m'],
        after['normal_east_north'],np.array(mapping['horizontal_origin_epsg6404_m']))
    mapping['mapping_policy']='One globally registered 2 m numerical chart with explicit local smoothing refinements; geographic source features are unchanged'
    if any(sha(p)!=h for p,h in protected.items()):raise ValueError('Input changed during chart refinement')
    out.mkdir(parents=True)
    np.savez_compressed(out/'frame.npz',**after)
    (out/'coordinate_map.json').write_text(json.dumps(mapping,separators=(',',':'),allow_nan=False)+'\n')
    result=copy.deepcopy(manifest)
    result.update(hydraulic_station_range_m=[float(after['station_m'][0]),float(after['station_m'][-1])],
        source_station_range_m=[float(after['source_global_station_m'][0]),float(after['source_global_station_m'][-1])],
        files_sha256={name:sha(out/name) for name in ('frame.npz','coordinate_map.json')},
        numerical_chart_refinement=dict(**receipt,baseline_manifest=original.relative_to(ROOT).as_posix()+'/manifest.json',
            baseline_manifest_sha256=manifest_sha,specification=specification.relative_to(ROOT).as_posix(),
            specification_sha256=spec_sha,source_files_unchanged=True),runtime_ready=False)
    result['limitations']+=['Rebuild all affected hydraulic inputs; station values downstream of refinements change.',
        'No terrain coverage, wet-strip, discharge, native coordinate inverse or engine acceptance is implied by chart generation.']
    if any(sha(p)!=h for p,h in protected.items()):raise ValueError('Input changed before chart receipt')
    (out/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('original','specification','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.original,a.specification,a.out),indent=2))
