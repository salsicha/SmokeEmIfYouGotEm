"""Compose bounded Colorado construction grids from registered source windows.

Outputs are construction inputs, NOT accepted terrain or cooked hydraulics.
Keep the survey pool bed unchanged wherever consistent with the water profile.
Never use DEM pixels over classified water as bed or infer a vertical offset
from those pixels. Missing rapid bed, shore stabilization and velocity remain
explicit modelling, with separate masks and quantitative conflict receipts.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from scipy.ndimage import distance_transform_edt, gaussian_filter1d

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'physics/data/real_world/colorado_river_grand_canyon_rowing'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_checked(directory, row, key='sha256'):
    path=directory/row['file']
    if path.parent.resolve()!=directory.resolve() or sha(path)!=row[key]:
        raise ValueError('Source path or checksum mismatch')
    return path


def project(points, line, stations, chunk=8192):
    """Exact nearest line-segment projection, not nearest point stair steps."""
    points=np.asarray(points,dtype=float); line=np.asarray(line,dtype=float)
    stations=np.asarray(stations,dtype=float)
    if (line.ndim!=2 or line.shape[1]!=2 or stations.shape!=(len(line),) or
        len(line)<2 or not np.isfinite(line).all() or not np.isfinite(stations).all() or
        not np.isfinite(points).all() or np.any(np.diff(stations)<=0)):
        raise ValueError('Invalid registered centerline')
    seg=np.diff(line,axis=0); lengths=np.linalg.norm(seg,axis=1)
    if np.any(lengths<1e-6): raise ValueError('Duplicate centerline points')
    station=np.empty(len(points)); lateral=np.empty(len(points)); distance=np.empty(len(points))
    for start in range(0,len(points),chunk):
        q=points[start:start+chunk,None,:]-line[None,:-1,:]
        t=np.clip(np.einsum('ijk,jk->ij',q,seg)/lengths**2,0,1)
        residual=q-t[...,None]*seg
        d2=np.einsum('ijk,ijk->ij',residual,residual)
        j=d2.argmin(axis=1); ix=np.arange(len(j)); r=residual[ix,j]
        sl=slice(start,start+len(j))
        station[sl]=stations[j]+t[ix,j]*np.diff(stations)[j]
        lateral[sl]=(-seg[j,1]*r[:,0]+seg[j,0]*r[:,1])/lengths[j]
        distance[sl]=np.sqrt(d2[ix,j])
    return station,lateral,distance


def infer_depth(wet, distance_to_edge, station, profile_station, surface, q, cell=1., station_origin_m=0.):
    """Manning strip depth hypothesis, not a survey or a solved flow field."""
    if not np.isfinite(q) or q<=0: raise ValueError('Positive discharge required')
    if not np.isfinite(station_origin_m): raise ValueError('Finite source station origin required')
    step=5.
    # Adjacent full-river tiles must use the same physical five-metre bins.
    # Restarting bins at each crop changes cross-section area and inferred bed
    # within their overlap even when shoreline and profile samples are equal.
    base=np.floor(station_origin_m/step)*step
    global_profile=profile_station+station_origin_m
    bins=np.arange(base,global_profile[-1]+step,step)
    ws=np.interp(bins,global_profile,surface)
    slope=np.maximum(-np.gradient(gaussian_filter1d(ws,2,mode='nearest'),step),0.0001)
    ids=np.clip(((station+station_origin_m-base)/step).astype(int),0,len(bins)-1)
    # Endpoint-clamped projections include upstream/downstream water outside
    # this finite profile. They are not cross-section samples: counting them
    # makes inferred depth depend on the rectangular crop's padding.
    interior=wet&(station>profile_station[0])&(station<profile_station[-1])
    # Area/bin length estimates water width, retaining separate island holes.
    width=np.bincount(ids[interior],minlength=len(bins))*cell*cell/step
    shape=np.minimum(1.,distance_to_edge/np.maximum(3.,.15*width[ids]))
    conveyance=np.bincount(ids[interior],weights=shape[interior]**(5/3),minlength=len(bins))*cell*cell/step
    roughness=np.where(slope>=.004,.045,.035)
    depth=(q*roughness/np.maximum(np.sqrt(slope)*conveyance,1e-8))**.6
    # Edge construction bins can be truncated; interpolate only from usable bins.
    valid=(conveyance>1.)&(width>5.)&(bins>=global_profile[0])&(bins+step<=global_profile[-1])
    if not valid.any(): raise ValueError('No usable wet cross-sections')
    depth=np.interp(bins,bins[valid],depth[valid])
    return np.where(wet,shape*depth[ids],0.)


def compose(profile, water, bed, terrain_ellipsoid, q=226.534772736, shore_clearance_m=.15):
    if not np.isfinite(shore_clearance_m) or not .15 <= shore_clearance_m <= 2.:
        raise ValueError('Inferred dry-shore clearance must be between 0.15 and 2 m')
    wet=water['classified_water_mask'].astype(bool)
    original=bed['elevation_ellipsoid_m'].astype(float)
    measured=bed['measured_pool_bed_mask'].astype(bool)&np.isfinite(original)
    if wet.shape!=original.shape or wet.shape!=terrain_ellipsoid.shape:
        raise ValueError('Source grids differ')
    for key in ('corner_east_north_m','cell_m'):
        if not np.array_equal(water[key],bed[key]): raise ValueError('Source grid registration differs')
    if not np.array_equal(water['cell_m'],[1.,1.]): raise ValueError('Expected one metre source grid')
    if not np.isfinite(terrain_ellipsoid).all(): raise ValueError('Missing regional terrain coverage')
    samples=profile['samples']
    line=np.array([[p['easting'],p['northing']] for p in samples])
    st=np.array([p['local_arc_station_m'] for p in samples])
    surface=np.array([p['ws_nonincreasing'] for p in samples])
    rows,cols=np.indices(wet.shape); x0,y1=water['corner_east_north_m']
    xy=np.column_stack([(x0+cols+.5).ravel(),(y1-rows-.5).ravel()])
    s,n,d=project(xy,line,st)
    s=s.reshape(wet.shape); n=n.reshape(wet.shape); d=d.reshape(wet.shape)
    ws=np.interp(s,st,surface)
    edge=distance_transform_edt(wet)
    station_origin=profile.get('source_halo_interval_m',[0.])[0]
    model=ws-infer_depth(wet,edge,s,st,surface,q,station_origin_m=station_origin)
    # Survey/profile conflict is retained separately; do not pretend a dry sonar
    # sample or an above-surface value is validated riverbed.
    conflict=wet&measured&(original>=ws-.02)
    supported=wet&measured&~conflict
    if supported.any():
        dist,indices=distance_transform_edt(~supported,return_indices=True)
        residual=np.where(supported,original-model,0.)
        correction=residual[tuple(indices)]*np.exp(-dist/25.)
        model=np.minimum(ws-.02,model+correction)
        model=np.where(supported,original,model)
    missing=wet&~supported
    # A terrain DEM need not resolve every classified dry island/shore cell. Keep
    # untouched terrain and a separate inferred correction, not a false survey.
    shore_model=(~wet)&(terrain_ellipsoid<ws+shore_clearance_m)&(distance_transform_edt(~wet)<=10.)
    composite=np.where(wet,model,terrain_ellipsoid)
    composite=np.where(shore_model,np.maximum(composite,ws+shore_clearance_m),composite)
    codes=np.zeros(wet.shape,np.uint8)
    codes[supported]=1; codes[missing]=2; codes[shore_model]=3
    result=dict(bed_ellipsoid_m=composite.astype('float32'),
        regional_terrain_ellipsoid_m=terrain_ellipsoid.astype('float32'),
        original_survey_bed_ellipsoid_m=original.astype('float32'),
        reference_surface_ellipsoid_m=ws.astype('float32'),
        station_m=s.astype('float32'),lateral_m=n.astype('float32'),
        classified_water_mask=wet,measured_pool_bed_mask=supported,
        source_bed_profile_conflict_mask=conflict,inferred_rapid_bed_mask=missing,
        inferred_shore_stabilization_mask=shore_model,class_code=codes,
        corner_east_north_m=water['corner_east_north_m'],cell_m=water['cell_m'])
    receipt=dict(classified_water_cells=int(wet.sum()),supported_survey_bed_cells=int(supported.sum()),
        inferred_wet_bed_cells=int(missing.sum()),source_bed_profile_conflicts=int(conflict.sum()),
        inferred_shore_cells=int(shore_model.sum()),
        unclassified_low_terrain_cells=int(((~wet)&(composite<ws)).sum()),
        measured_bed_max_change_m=float(np.max(np.abs(composite[supported]-original[supported]))) if supported.any() else None,
        inferred_depth_range_m=[float((ws-model)[wet].min()),float((ws-model)[wet].max())])
    return result,receipt


def build(profile_path, water_dir, bed_dir, terrain_dir, out, shore_clearance_m=.15):
    if out.exists(): raise ValueError('Fresh construction output required')
    profile=json.loads(profile_path.read_text(encoding='utf-8')); name=profile['name']
    wm=json.loads((water_dir/'manifest.json').read_text()); bm=json.loads((bed_dir/'manifest.json').read_text())
    tm=json.loads((terrain_dir/'manifest.json').read_text())
    if (profile['horizontal_crs']!='EPSG:6404' or not tm['vertical_reference'].startswith('NAVD88') or
        wm['horizontal_crs']!='EPSG:6404' or bm['horizontal_crs']!='EPSG:6404'):
        raise ValueError('Unreviewed coordinate or vertical reference')
    wr=next(r for r in wm['windows'] if r['name']==name)
    br=next(r for r in bm['windows'] if r['name']==name)
    tr=next(r for r in tm['windows'] if r['name']==name)
    if tr['cell_m']<10 and not tr.get('valid_pixel_coverage_verified'):
        raise ValueError('Fine terrain export lacks verified valid-pixel coverage')
    wp=read_checked(water_dir,dict(wr,sha256=wr['files_sha256'][wr['file']]))
    bp=read_checked(bed_dir,br); tp=read_checked(terrain_dir,tr)
    water=dict(np.load(wp)); bed=dict(np.load(bp))
    target=np.full(water['classified_water_mask'].shape,np.nan,dtype='float32')
    x0,y1=water['corner_east_north_m']
    with rasterio.open(tp) as source:
        if source.crs.to_epsg()!=6404: raise ValueError('Terrain CRS mismatch')
        reproject(rasterio.band(source,1),target,src_transform=source.transform,src_crs=source.crs,
            dst_transform=from_origin(x0,y1,1,1),dst_crs=source.crs,dst_nodata=np.nan,resampling=Resampling.bilinear)
    if not np.isfinite(target).all() or (target<=0).any():
        raise ValueError('Missing or zero-filled Colorado terrain; no silent dry-bank fill')
    samples=profile['samples']; st=np.array([p['local_arc_station_m'] for p in samples])
    line=np.array([[p['easting'],p['northing']] for p in samples])
    # The local surveyed geoid supplies a declared, smoothly interpolated
    # vertical conversion, never a fitted height offset from DEM water values.
    rows,cols=np.indices(target.shape)
    station,_,_=project(np.column_stack([(x0+cols+.5).ravel(),(y1-rows-.5).ravel()]),line,st)
    geoid=np.interp(station,st,[p['geoid18_value'] for p in samples]).reshape(target.shape)
    terrain=target+geoid
    arrays,receipt=compose(profile,water,bed,terrain,shore_clearance_m=shore_clearance_m)
    arrays['source_regional_terrain_navd88_m']=target
    arrays['interpolated_survey_geoid18_m']=geoid.astype('float32')
    terrain_sources=[tp]
    resolution=np.full(target.shape,tr['cell_m'],dtype='float32')
    if tr.get('source_resolution_mask'):
        rp=read_checked(terrain_dir,tr['source_resolution_mask']);terrain_sources.append(rp)
        with rasterio.open(rp) as source:
            if source.crs.to_epsg()!=6404:raise ValueError('Resolution-mask CRS mismatch')
            resolution[:]=np.nan
            reproject(rasterio.band(source,1),resolution,src_transform=source.transform,src_crs=source.crs,
                dst_transform=from_origin(x0,y1,1,1),dst_crs=source.crs,dst_nodata=np.nan,resampling=Resampling.nearest)
        if not np.isin(resolution,[1.,10.]).all():raise ValueError('Missing or unsupported native resolution mask')
    arrays['regional_terrain_source_resolution_m']=resolution
    out.mkdir(parents=True)
    np.savez_compressed(out/'evidence_grid.npz',**arrays)
    manifest=dict(schema='raftsim.colorado_catalog_construction_grid.v1',name=name,
        horizontal_crs='EPSG:6404',vertical_datum='NAD83(2011) ellipsoid',
        source_files_sha256={str(p.relative_to(ROOT)):sha(p) for p in [profile_path,wp,bp,*terrain_sources]},
        class_codes={'0':f"regional dry terrain, resampled from {tr['cell_m']} m export; not independently verified boulder geometry",
                     '1':'2021 survey pool bed, no change except float32 serialization',
                     '2':'inferred unsurveyed/conflicting bed, Manning depth with decaying pool residual',
                     '3':'inferred shoreline/island stabilization where coarse terrain is below classified water'},
        conversion='ellipsoid = NAVD88 + profile geoid18; interpolated along nearest centerline segment',
        parameters=dict(target_discharge_cfs=8000,target_discharge_m3s=226.534772736,
                        regional_terrain_export_cell_m=tr['cell_m'],
                        regional_terrain_source_resolution_counts={str(float(v)):int((resolution==v).sum()) for v in np.unique(resolution)},
                        profile_discharge_cfs_approx=8400,pool_residual_decay_m=25.,shore_model_radius_m=10.,
                        inferred_dry_shore_clearance_m=shore_clearance_m,
                        depth_bin_policy='Global five-metre bins; exclude endpoint-clamped projections and incomplete profile-edge bins',
                        depth_bin_global_station_origin_m=profile.get('source_halo_interval_m',[0.])[0]),
        limitations=['Source DEM water values excluded from bed inference.',
                    'Model bank corrections and missing bathymetry require engine review; no measured rock shapes inferred.',
                    'Classified-water holes can include imagery errors, not necessarily solid boulders.',
                    'Dry-shore clearance is a bounded geometry hypothesis, not a surveyed bank height; requires a fresh cook and unchanged water-footprint/stage gates.',
                    '8000 cfs target differs from approximate 8400 cfs profile; reference level is not exact flow-matched stage.',
                    'No solved hydraulic field, playable map, route difficulty or class acceptance yet.'],
        statistics=receipt,evidence_grid_sha256=sha(out/'evidence_grid.npz'),
        playable_map_created=False,accepted=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,required=True)
    p.add_argument('--water',type=Path,default=DATA/'catalog_water_windows_2026_10_v2')
    p.add_argument('--bed',type=Path,default=DATA/'catalog_pool_bed_windows_2026_10_v1')
    p.add_argument('--terrain',type=Path,default=DATA/'catalog_terrain_3dep_capture_v1')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--shore-clearance-m',type=float,default=.15)
    a=p.parse_args();build(a.profile.resolve(),a.water.resolve(),a.bed.resolve(),a.terrain.resolve(),a.out.resolve(),a.shore_clearance_m)
