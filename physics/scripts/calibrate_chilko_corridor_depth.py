"""Bounded inferred-bed capacity experiment from settled geographic stage errors.

Does not move banks, change references, raise terrain or manufacture a solved
field. Positive stage errors deepen only the existing inferred channel. A fresh
canonical export, native cook and unchanged independent gates are mandatory.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import gaussian_filter1d

from chilko_corridor_bed import CorridorBed
from mosaic_lidarbc_crops import sha
from review_chilko_continuous_cook import read_inputs, validate_native, validate_frame
from review_colorado_catalog_cook import load_frame


def depth_step(station, parent, points, error, section_shape, bounds):
    station,parent,points,error,section_shape,bounds=map(np.asarray,
        (station,parent,points,error,section_shape,bounds))
    if (station.ndim!=1 or len(station)<2 or parent.shape!=station.shape
            or points.ndim!=1 or error.shape!=points.shape or section_shape.shape!=points.shape
            or bounds.shape!=(2,) or not all(np.isfinite(a).all() for a in
                (station,parent,points,error,section_shape,bounds))
            or np.any(np.diff(station)<=0) or np.any(parent<=0) or np.any(parent>10)
            or bounds[0]<station[0] or bounds[1]>station[-1] or np.diff(bounds)[0]<400
            or np.any(points<bounds[0]) or np.any(points>bounds[1])
            or np.any(section_shape<0) or np.any(section_shape>1)):
        raise ValueError('Finite aligned geographic calibration samples required')
    # Fixed conservative policy: 20 m bins, 30 m smoothing, 150 m boundary
    # tapers. Marginal bank cells do not amplify the inverse shape correction.
    bin_m=20.; maximum_step=.75; relax=.7
    count=int(np.ceil((bounds[1]-bounds[0])/bin_m))
    centres=bounds[0]+(np.arange(count)+.5)*bin_m
    raw=np.full(count,np.nan);counts=np.zeros(count,dtype=int)
    bins=np.minimum(((points-bounds[0])/bin_m).astype(int),count-1)
    for i in range(count):
        selected=(bins==i)&(section_shape>=.2)
        counts[i]=selected.sum()
        if counts[i]>=3:
            raw[i]=np.clip(relax*np.median(error[selected])/np.median(section_shape[selected]),0,maximum_step)
    valid=np.isfinite(raw)
    if valid.sum()<5:raise ValueError('Insufficient independent geographic stage coverage')
    weight=gaussian_filter1d(valid.astype(float),30/bin_m,mode='constant',cval=0.)
    smooth=gaussian_filter1d(np.nan_to_num(raw),30/bin_m,mode='constant',cval=0.)/np.maximum(weight,1e-12)
    # Never bridge unsampled bins: a missing reference is not zero error.
    smooth[~valid]=0.
    delta=np.interp(station,centres,smooth,left=0.,right=0.)
    taper=np.minimum(np.clip((station-bounds[0])/150.,0,1),np.clip((bounds[1]-station)/150.,0,1))
    delta*=np.sin(taper*np.pi/2)**2
    delta=np.minimum(delta,10-parent)
    return delta,dict(bin_centres_m=centres.tolist(),sample_counts=counts.tolist(),
        raw_step_m=[float(x) if np.isfinite(x) else None for x in raw],
        bin_m=bin_m,smoothing_sigma_m=30.,boundary_taper_m=150.,relaxation=relax,
        maximum_allowed_step_m=maximum_step,maximum_actual_step_m=float(delta.max()),
        changed_source_nodes=int((delta>0).sum()),bounds_m=bounds.tolist())


def build(inputs,cook,review,out):
    inputs,cook,review,out=[Path(p).resolve() for p in (inputs,cook,review,out)]
    if out.exists():raise ValueError('Fresh calibration directory required')
    receipt=json.loads(review.read_text());review_hash=sha(review)
    report,scenario,mapping,triangles,bed,ref,hashes=read_inputs(inputs)
    if receipt['input_files_sha256']!=hashes:
        raise ValueError('Review does not bind these native inputs')
    native=json.loads((cook/'manifest.json').read_text())
    validation=json.loads((cook/'validation.json').read_text())
    validate_native(native,validation,scenario)
    if receipt['native_manifest']!=native or receipt['native_validation']!=validation:
        raise ValueError('Review does not bind this native cook')
    for gate in ('discharge_abs_p95_below_5percent','settling_depth_p95_below_3cm',
                 'inlet_to_outlet_wet_path','all_surface_sections_sampled','solved_wet_chart_nonfolding'):
        if receipt['construction_screen'].get(gate) is not True:
            raise ValueError('Settled connected finite native source required')
    frame_name=receipt['comparison_frames'][-1]
    if Path(frame_name).name!=frame_name:raise ValueError('Invalid reviewed frame path')
    frame_path=cook/'frames'/frame_name;frame_hash=sha(frame_path)
    if receipt['frame_sha256'][frame_name]!=frame_hash:raise ValueError('Changed reviewed state')
    frame=load_frame(frame_path,bed.shape);validate_frame(frame,bed,scenario['grid'])
    source=triangles.manifest['evidence_source'];profile=Path(source['profile_manifest']).parent
    parent_path=Path(source['available_channel_depth']['manifest'])
    parent_manifest=json.loads(parent_path.read_text())
    if parent_manifest.get('native_calibration'):
        raise ValueError('This bounded experiment allows one step, not unbounded repeated calibration')
    model=CorridorBed(Path(json.loads((profile/'manifest.json').read_text())['source_terrain']['manifest']).parent,
                      profile,source['discharge_m3s'],source['manning_n'],parent_path.parent)
    xy=np.stack((ref['world_x'],ref['world_y']),axis=-1)
    selected=ref['channel']&(frame['h']>.05)
    points=shapely.points(xy[selected]);station=shapely.line_locate_point(model.line,points)
    width=np.interp(station,model.station,model.width)
    shape=np.sqrt(np.clip(2*shapely.distance(points,model.polygon.boundary)/width,0,1))
    bounds=np.asarray(report['requested_source_interval_m'])
    inside=(station>=bounds[0])&(station<=bounds[1])
    error=(frame['eta']-ref['ws_reference_grid'])[selected]
    delta,stats=depth_step(model.station,model.depth,station[inside],error[inside],shape[inside],bounds)
    if not (delta>0).any():raise ValueError('No positive stage error supports this capacity experiment')
    with np.load(parent_path.parent/'depth.npz',allow_pickle=False) as old:
        arrays=dict(station_m=model.station,depth_amplitude_m=model.depth+delta,
            previous_depth_amplitude_m=old['previous_depth_amplitude_m'],
            calibration_parent_depth_amplitude_m=model.depth,calibration_step_m=delta)
    if sha(review)!=review_hash or sha(frame_path)!=frame_hash or any(sha(inputs/k)!=v for k,v in hashes.items()):
        raise ValueError('Native calibration source changed during preparation')
    if sha(parent_path)!=source['available_channel_depth']['manifest_sha256']:
        raise ValueError('Depth source changed during preparation')
    out.mkdir(parents=True);np.savez_compressed(out/'depth.npz',**arrays)
    keys=('schema','source_profile_manifest','source_profile_sha256','source_terrain_sha256',
          'source_route_sha256','source_planform_sha256','ownership_policy','discharge_m3s','manning_n',
          'maximum_allowed_amplitude_m','hydraulic_solution','engine_validated')
    result={k:parent_manifest[k] for k in keys}
    result.update(depth_sha256=sha(out/'depth.npz'),maximum_amplitude_m=float(arrays['depth_amplitude_m'].max()),
        scope='One bounded positive-stage depth-amplitude experiment, not measured bathymetry or a solved hydraulic field',
        capacity_policy='Original Manning capacity statistics do not describe this changed candidate; fresh native review required',
        native_calibration=dict(parent_manifest=str(parent_path),parent_manifest_sha256=sha(parent_path),
            parent_depth_sha256=sha(parent_path.parent/'depth.npz'),review=str(review),review_sha256=review_hash,
            frame=str(frame_path),frame_sha256=frame_hash,input_files_sha256=hashes,
            geographic_projection='Each wet source-owned cell projected to corrected source route; never numerical row station',
            policy='Positive errors only; no shallowing, bank edits, new channel ownership, or reference-mask changes',
            statistics=stats,requires_fresh_canonical_export_and_native_review=True))
    (out/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in stats.items() if not isinstance(v,list)},indent=2));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('inputs','cook','review','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();build(a.inputs,a.cook,a.review,a.out)
