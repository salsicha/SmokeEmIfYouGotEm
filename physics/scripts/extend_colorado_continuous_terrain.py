"""Add source-backed outer tiles without rewriting any existing Landscape tile.

Original construction-grid values always win, including surveyed bed and
explicit shore inference. Additional DEM samples are regional terrain only,
converted with the captured profile geoid. Low/missing padding is rejected,
never raised to manufacture a bank. This is not hydraulic/engine acceptance.
"""
import argparse
import copy
import json
import shutil
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window
from scipy.ndimage import map_coordinates
from build_colorado_catalog_evidence import ROOT,sha,project
from export_colorado_continuous_terrain import (
    LandscapeTriangles,TerrainMosaic,load_sources,encode_height,write_png_u16,
    VERTICES,SPACING,SPAN)


def sample_raster(path,points,nearest=False):
    """Read only the bounded raster window; outside/nodata stays unknown."""
    points=np.asarray(points,dtype=float)
    if points.ndim!=2 or points.shape[1]!=2 or not np.isfinite(points).all():
        raise ValueError('Invalid terrain sample coordinates')
    result=np.full(len(points),np.nan)
    if not len(points):return result
    with rasterio.open(path) as src:
        t=src.transform
        if (src.crs.to_epsg()!=6404 or t.b!=0 or t.d!=0 or t.a<=0 or t.e>=0):
            raise ValueError('Unsupported terrain raster registration')
        b=src.bounds
        take=(points[:,0]>=b.left)&(points[:,0]<=b.right)&(points[:,1]>=b.bottom)&(points[:,1]<=b.top)
        if not take.any():return result
        p=points[take]
        col=np.clip((p[:,0]-t.c)/t.a-.5,0,src.width-1)
        row=np.clip((p[:,1]-t.f)/t.e-.5,0,src.height-1)
        x0,y0=int(np.floor(col.min())),int(np.floor(row.min()))
        x1,y1=min(src.width,int(np.ceil(col.max()))+1),min(src.height,int(np.ceil(row.max()))+1)
        values=src.read(1,window=Window(x0,y0,x1-x0,y1-y0),masked=True).astype(float).filled(np.nan)
        result[take]=map_coordinates(values,[row-y0,col-x0],order=0 if nearest else 1,
                                     mode='nearest',prefilter=False)
    return result


def profile_conversion(points,profiles):
    """Nearest actual profile segment; no DEM-derived fitted height offset."""
    points=np.asarray(points,dtype=float)
    distance=np.full(len(points),np.inf);geoid=np.full(len(points),np.nan);stage=geoid.copy()
    for p in profiles:
        line=p['line'];st=p['station']
        low=line.min(axis=0)-1000.;high=line.max(axis=0)+1000.
        selected=np.flatnonzero((points>=low).all(axis=1)&(points<=high).all(axis=1))
        if not len(selected):continue
        s,_,d=project(points[selected],line,st)
        take=d<distance[selected];selected=selected[take];s=s[take]
        distance[selected]=d[take]
        geoid[selected]=np.interp(s,st,p['geoid'])
        stage[selected]=np.interp(s,st,p['stage'])
    return geoid,stage


class CapturedPadding:
    def __init__(self,rasters,profiles):
        self.rasters=rasters;self.profiles=profiles

    def sample(self,points):
        z=np.full(len(points),np.nan);resolution=z.copy()
        # Ordered immutable sources, independent of chunk/batch traversal.
        # Never select a different source just because it has a higher bank.
        for r in self.rasters:
            x0,y0,x1,y1=r['bounds']
            selected=np.flatnonzero(np.isnan(z)&(points[:,0]>=x0)&(points[:,0]<=x1)&
                                    (points[:,1]>=y0)&(points[:,1]<=y1))
            if not len(selected):continue
            values=sample_raster(r['path'],points[selected])
            native=sample_raster(r['resolution'],points[selected],True)
            if not np.isfinite(values).all() or np.any(values<=0) or not np.isin(native,[1.,10.]).all():
                raise ValueError('Missing/zero terrain or unresolved source resolution')
            z[selected]=values;resolution[selected]=native
        geoid,stage=profile_conversion(points,self.profiles)
        return z+geoid,resolution,stage


def fill_unowned(heights,owners,points,padding):
    """Original samples remain bit-identical; unknown or low DEM is not fill."""
    heights=np.asarray(heights,dtype=float).copy();owners=np.asarray(owners)
    if heights.shape!=owners.shape or points.shape!=heights.shape+(2,):
        raise ValueError('Padding grids differ')
    selected=owners<0
    if not selected.any():return heights,dict(added_vertices=0,resolution_counts={})
    z,resolution,stage=padding.sample(points[selected])
    if not np.isfinite(z).all() or not np.isfinite(stage).all():
        raise ValueError('Missing captured terrain/profile conversion')
    if np.any(z<stage+1.):
        raise ValueError('Low outer DEM requires water/shore evidence; do not raise it')
    if not np.isin(resolution,[1.,10.]).all():raise ValueError('Unknown padding resolution')
    heights[selected]=z
    return heights,dict(added_vertices=int(selected.sum()),
        resolution_counts={str(int(v)):int((resolution==v).sum()) for v in np.unique(resolution)})


def validate_additive_manifest(base,extension,base_sha):
    if extension.get('additive_terrain_extension',{}).get('base_manifest_sha256')!=base_sha:
        raise ValueError('Extension does not bind original terrain')
    for key in ('schema','route_coordinate_map','route_sha256','horizontal_origin_epsg6404_m',
                'vertical_datum_m','landscape','source_inputs'):
        if extension.get(key)!=base.get(key):raise ValueError('Extension changed the original terrain frame or sources')
    before={tuple(c['chunk']):c for c in base['chunks']}
    after={tuple(c['chunk']):c for c in extension['chunks']}
    if len(after)!=len(extension['chunks']) or any(after.get(i)!=c for i,c in before.items()):
        raise ValueError('Extension replaced or removed an original tile')
    if len(after)<=len(before):raise ValueError('No additional terrain tiles')


def select_extension_chunks(review,launch,complete,allow_partial=False):
    requested=review['missing_chunk_indices']
    if any(len(c)!=2 or any(type(v) is not int for v in c) for c in requested):
        raise ValueError('Invalid requested tile indices')
    if len({tuple(c) for c in requested})!=len(requested):raise ValueError('Duplicate requested tiles')
    if complete['captures_complete'] and not complete['errors'] and len(complete['completed_windows'])==complete['expected_windows']:
        return requested,[]
    if not allow_partial:raise ValueError('Incomplete outer terrain captures')
    available={tuple(c) for c in launch['existing_full_extent_tiles']}
    for row in complete['completed_windows']:available.update(tuple(c) for c in row['needed_chunks'])
    return ([c for c in requested if tuple(c) in available],
            [dict(chunk=c,error='Capture pending; no terrain invented') for c in requested if tuple(c) not in available])


def run(base_folder,review_path,capture_job,out,allow_partial=False):
    if out.exists():raise ValueError('Fresh additive terrain output required')
    base=LandscapeTriangles(base_folder);m=base.manifest
    review=json.loads(review_path.read_text());launch=json.loads((capture_job/'launch.json').read_text())
    capture_receipt=capture_job/'completion.json'
    if allow_partial and not capture_receipt.exists():capture_receipt=capture_job/'failure.json'
    complete=json.loads(capture_receipt.read_text())
    requested,pending=select_extension_chunks(review,launch,complete,allow_partial)
    identities={ROOT/n:h for n,h in launch['files_sha256'].items()}
    if (identities.get(base_folder/'manifest.json')!=base.manifest_sha256 or
            identities.get(review_path)!=sha(review_path)):
        raise ValueError('Capture job did not bind this terrain gap review')
    protected={base_folder/'manifest.json':base.manifest_sha256,review_path:sha(review_path),
        capture_job/'launch.json':sha(capture_job/'launch.json'),capture_receipt:sha(capture_receipt)}
    def bind(path,digest):
        if path in protected and protected[path]!=digest:raise ValueError('Conflicting source identity')
        if path not in protected and sha(path)!=digest:raise ValueError('Changed captured source')
        protected[path]=digest
    for name,h in launch['files_sha256'].items():bind(ROOT/name,h)
    evidence=[];profiles=[];conversion=[];rasters=[];seen=set()
    def raster_source(manifest_path,name):
        manifest=json.loads(manifest_path.read_text());bind(manifest_path,sha(manifest_path))
        if (manifest['source_service']!='https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer'
                or manifest['vertical_reference']!='NAVD88 orthometric metres (CONUS 3DEP)'):
            raise ValueError('Unreviewed DEM source/datum')
        row=next(r for r in manifest['windows'] if r['file']==name)
        path=manifest_path.parent/name
        if path in seen:return
        seen.add(path);bind(path,row['sha256'])
        rp=manifest_path.parent/row['source_resolution_mask']['file'];bind(rp,row['source_resolution_mask']['sha256'])
        with rasterio.open(path) as src:
            if src.crs.to_epsg()!=6404 or list(src.bounds)!=row['bounds_epsg6404']:
                raise ValueError('Captured bounds/CRS mismatch')
        rasters.append(dict(path=path,resolution=rp,bounds=row['bounds_epsg6404']))
    for source in m['source_inputs']:
        folder=ROOT/source['evidence'];profile=ROOT/source['profile']
        bind(folder/'manifest.json',source['evidence_manifest_sha256']);bind(profile,source['profile_sha256'])
        em=json.loads((folder/'manifest.json').read_text());p=json.loads(profile.read_text())
        bind(folder/'evidence_grid.npz',em['evidence_grid_sha256'])
        evidence.append(folder);profiles.append(profile)
        samples=p['samples']
        conversion.append(dict(line=np.array([[s['easting'],s['northing']] for s in samples]),
            station=np.array([s['local_arc_station_m'] for s in samples]),
            geoid=np.array([s['geoid18_value'] for s in samples]),
            stage=np.array([s['ws_nonincreasing'] for s in samples])))
        for name,h in em['source_files_sha256'].items():
            if name.endswith('.tif') and 'source_resolution' not in name:
                path=ROOT/name;bind(path,h);raster_source(path.parent/'manifest.json',path.name)
    for row in complete['completed_windows']:
        path=ROOT/row['manifest'];bind(path,row['manifest_sha256'])
        cm=json.loads(path.read_text())
        if len(cm['windows'])!=1:raise ValueError('Expected bounded capture window')
        raster_source(path,cm['windows'][0]['file'])
    mosaic=TerrainMosaic(load_sources(evidence,profiles,bounded=True));padding=CapturedPadding(rasters,conversion)
    if shutil.disk_usage(ROOT).free<40*1024**3:raise ValueError('Preserve 40 GiB reserve')
    out.mkdir(parents=True);result=copy.deepcopy(m);added=[];rejected=pending.copy()
    for chunk in m['chunks']:shutil.copyfile(base_folder/chunk['heightfield'],out/chunk['heightfield'])
    for i,j in requested:
        if shutil.disk_usage(ROOT).free<40*1024**3:raise ValueError('Preserve 40 GiB reserve')
        if (i,j) in base.by_index:raise ValueError('Requested extension already exists')
        x0,y0=base.origin+np.array([i,j])*SPAN
        east,north=np.meshgrid(x0+np.arange(VERTICES)*SPACING,y0+SPAN-np.arange(VERTICES)*SPACING)
        points=np.stack([east,north],axis=-1);heights,owners=mosaic.sample(east,north)
        try:heights,stats=fill_unowned(heights,owners,points,padding)
        except ValueError as error:
            rejected.append(dict(chunk=[i,j],error=str(error)));continue
        name=f'height_{i}_{j}.png';write_png_u16(out/name,encode_height(heights))
        result['chunks'].append(dict(chunk=[i,j],heightfield=name,sha256=sha(out/name),
            origin_epsg6404_m=[float(x0),float(y0+SPAN)],
            world_northwest_xy_cm=[float((x0-base.origin[0])*100),float((base.origin[1]-y0-SPAN)*100)],
            source_owner_indices=np.unique(owners[owners>=0]).tolist(),regional_padding=stats))
        added.append([i,j]);print('EXTENDED',len(added),'of',len(review['missing_chunk_indices']),flush=True)
    result['incomplete_source_chunks']=[r for r in m['incomplete_source_chunks'] if r['chunk'] not in added]
    result['additive_terrain_extension']=dict(base_manifest_sha256=base.manifest_sha256,
        base_manifest=str((base_folder/'manifest.json').relative_to(ROOT)),added_chunks=added,
        rejected_chunks=rejected,files_sha256={str(p.relative_to(ROOT)):h for p,h in protected.items()},
        original_tiles_unchanged=True,original_source_samples_unchanged=True,
        partial_capture_scope=bool(pending),
        policy='Only unowned regional terrain: NAVD88 + nearest captured profile GEOID18; reject below profile stage + 1 m, never raise it')
    validate_additive_manifest(m,result,base.manifest_sha256)
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    # Exact common encoded edges, hashes and old tile registration, not a
    # hand-waved visual blend. Preserve rejected outputs for diagnosis.
    extended=LandscapeTriangles(out);extended.verify_unchanged();base.verify_unchanged()
    if any(sha(p)!=h for p,h in protected.items()):raise ValueError('Sources changed during extension')
    receipt=dict(added_chunks=len(added),rejected_chunks=rejected,original_chunks=len(m['chunks']),
        requested_chunks=len(review['missing_chunk_indices']),shared_edges_validated=True,
        original_tiles_byte_identical=True,engine_accepted=False,
        manifest_sha256=sha(out/'manifest.json'))
    (out/('completion.json' if not rejected else 'rejected.json')).write_text(json.dumps(receipt,indent=2))
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','review','captures','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--allow-partial-captures',action='store_true',help='Export only completed source-backed tiles; preserve a rejection receipt for every pending tile')
    a=p.parse_args();r=run(a.base.resolve(),a.review.resolve(),a.captures.resolve(),a.out.resolve(),a.allow_partial_captures)
    print(json.dumps(r,indent=2))
    if r['rejected_chunks']:raise SystemExit(1)
