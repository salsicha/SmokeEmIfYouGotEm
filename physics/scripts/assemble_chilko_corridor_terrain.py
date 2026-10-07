"""Assemble bounded full-corridor terrain with explicit native/coarse provenance.

Native LidarBC pixels take precedence without alteration. Verified MRDEM-30
fills only missing terrain; resampling never upgrades its source resolution.
This is not bathymetry, rapid registration, a hydraulic bed, or game acceptance.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from scipy.spatial import cKDTree

from capture_lidarbc_plan import checked_crop, checked_plan
from mosaic_lidarbc_crops import CRS, VERTICAL, mosaic_crops, sha
from plan_lidarbc_corridor_capture import route_xy

ROOT = Path(__file__).resolve().parents[2]


def fill_missing(native, owner, coarse, coarse_class):
    native, coarse = np.asarray(native), np.asarray(coarse)
    if (native.ndim != 2 or native.dtype != np.float32 or coarse.dtype != np.float32 or
            any(np.shape(a) != native.shape for a in (owner, coarse, coarse_class)) or
            np.isinf(native).any() or np.isinf(coarse).any() or
            not np.array_equal(np.asarray(owner)>0, np.isfinite(native))):
        raise ValueError('Native ownership and aligned finite-or-missing grids required')
    if not np.isin(coarse_class,[0,1]).all():
        raise ValueError('Unreviewed MRDEM source class; inspect its product provenance')
    height = native.copy()
    kind = np.where(np.isfinite(native),1,0).astype(np.uint8)
    take = ~np.isfinite(native)&np.isfinite(coarse)&(coarse_class==1)
    height[take] = coarse[take]; kind[take] = 2
    return height,kind


def route_tree(xy, step=1.):
    xy = np.asarray(xy,dtype=float)
    if (xy.ndim!=2 or xy.shape[1]!=2 or len(xy)<2 or not np.isfinite(xy).all() or
            not np.isfinite(step) or not 0<step<=10):
        raise ValueError('Finite route and bounded sampling interval required')
    pieces=[]
    for a,b in zip(xy[:-1],xy[1:]):
        length=float(np.linalg.norm(b-a))
        if length<=0:raise ValueError('Duplicate route vertices')
        count=int(np.ceil(length/step))
        if count>1_000_000:raise ValueError('Implausible route segment')
        pieces.append(a+np.arange(count)[:,None]/count*(b-a))
    return cKDTree(np.concatenate([*pieces,xy[-1:]],axis=0))


def missing_near_route(height,bounds,tree,buffer_m,route_step=1.):
    """Conservative missing-pixel count: includes full pixel and sampling radii."""
    rows,cols=np.nonzero(~np.isfinite(height))
    count=0
    for start in range(0,len(rows),65536):
        sl=slice(start,start+65536)
        xy=np.column_stack((bounds[0]+cols[sl]+.5,bounds[3]-rows[sl]-.5))
        # Nearest route sample lies at most half a sample interval from any
        # segment point. A pixel can intersect the buffer up to sqrt(.5) away
        # from its centre. Over-inclusion is safe; under-inclusion is not.
        count+=int((tree.query(xy,workers=1)[0]<=buffer_m+route_step/2+np.sqrt(.5)).sum())
    return count


def checked_fallback(path):
    m=json.loads(path.read_text())
    if (m.get('schema')!='raftsim.chilko.mrdem30_corridor_clip.v1' or
            m.get('license')!='Open Government Licence - Canada' or
            m.get('vertical_datum')!='CGVD2013 orthometric heights (EPSG:6647)' or
            m.get('horizontal_clip_crs')!='EPSG:4326 WGS 84' or
            m['metadata']['effective_resolution_m']!=30. or
            m['per_pixel_source_classes']!=[dict(value=1,meaning='adjusted_copernicus_glo_30',pixel_count=1462383)]):
        raise ValueError('Unreviewed fallback product, datum, source classes or resolution')
    paths={key:(ROOT/value['path']).resolve() for key,value in m['outputs'].items()}
    for key,p in paths.items():
        p.relative_to(ROOT)
        if sha(p)!=m['outputs'][key]['sha256']:raise ValueError('Changed fallback raster')
    with rasterio.open(paths['dtm']) as a,rasterio.open(paths['per_pixel_source']) as b:
        if (a.crs.to_epsg()!=4326 or b.crs!=a.crs or a.shape!=b.shape or a.transform!=b.transform or
                list(a.shape)!=m['metadata']['target_shape'] or
                not np.allclose(list(a.bounds),m['metadata']['target_bounds_wgs84'],atol=1e-10,rtol=0) or
                a.count!=1 or b.count!=1 or a.dtypes!=('float32',) or b.dtypes!=('uint8',)):
            raise ValueError('Fallback raster geometry differs from its receipt')
        if not np.isin(b.read(1),[0,1]).all():raise ValueError('Changed fallback source classification')
    return m,paths


def assemble(plan_path,captures,fallback_path,out):
    if out.exists():raise ValueError('Fresh assembly directory required')
    plan=checked_plan(plan_path)
    identity=dict(plan_sha256=sha(plan_path),route_sha256=plan['route_sha256'])
    if json.loads((captures/'plan_identity.json').read_text())!=identity:
        raise ValueError('Capture collection belongs to another plan')
    groups={tuple(c['cell']):[] for c in plan['cells']}
    empty=[]
    # Require all requests terminal. Never consume partially written captures.
    for i,request in enumerate(plan['capture_requests']):
        path=captures/f'request_{i:04d}.npz'
        if path.exists() and path.with_suffix('.json').exists():
            checked_crop(path,request); groups[tuple(request['cell'])].append(path)
        elif path.with_suffix('.missing.json').exists():
            receipt=json.loads(path.with_suffix('.missing.json').read_text())
            if (path.exists() or receipt.get('request')!=request or
                    receipt.get('reason')!='native_window_has_no_valid_pixels' or
                    receipt.get('catalogue_sha256')!=sha(path.with_suffix('.catalog.json'))):
                raise ValueError('Unverified empty native window')
            empty.append(i)
        else:raise ValueError(f'Capture {i} is not complete; wait for the existing acquisition')
    fallback,paths=checked_fallback(fallback_path)
    tree=route_tree(route_xy(Path(plan['route'])))
    out.mkdir(parents=True);(out/'native').mkdir();(out/'tiles').mkdir()
    records=[]
    with rasterio.open(paths['dtm']) as dem,rasterio.open(paths['per_pixel_source']) as source:
        for cell in plan['cells']:
            x0,y0,x1,y1=cell['bounds']; shape=(y1-y0,x1-x0)
            stem='cell_'+'_'.join(map(str,cell['cell']))
            inputs=groups[tuple(cell['cell'])]
            native_receipt=None
            if inputs:
                native_path=out/'native'/f'{stem}.npz'
                native_receipt=mosaic_crops(inputs,cell['bounds'],native_path)
                with np.load(native_path) as z: native,owner=z['height_m'],z['source_index']
            else:
                native=np.full(shape,np.nan,np.float32);owner=np.zeros(shape,np.uint16)
            coarse=np.full(shape,np.nan,np.float32);coarse_class=np.zeros(shape,np.uint8)
            for src,dest,resampling,nodata in ((dem,coarse,Resampling.bilinear,np.nan),
                                               (source,coarse_class,Resampling.nearest,0)):
                reproject(rasterio.band(src,1),dest,src_transform=src.transform,src_crs=src.crs,
                          src_nodata=src.nodata,dst_transform=from_origin(x0,y1,1,1),dst_crs='EPSG:3157',
                          dst_nodata=nodata,resampling=resampling,num_threads=1)
            height,kind=fill_missing(native,owner,coarse,coarse_class)
            near_missing=missing_near_route(height,cell['bounds'],tree,plan['buffer_m'])
            target=out/'tiles'/f'{stem}.npz'
            np.savez_compressed(target,height_m=height,source_kind=kind,native_crop_owner=owner,
                                mrdem_source_code=coarse_class,x0=float(x0),y_top=float(y1),cell_m=1.)
            record=dict(cell=cell['cell'],bounds=cell['bounds'],file=target.relative_to(out).as_posix(),
                sha256=sha(target),native_mosaic_sha256=None if not inputs else native_receipt['npz_sha256'],
                native_pixels=int((kind==1).sum()),coarse_pixels=int((kind==2).sum()),
                missing_pixels=int((kind==0).sum()),missing_required_corridor_pixels=near_missing)
            records.append(record)
            print(json.dumps(record),flush=True)
    result=dict(schema='raftsim.chilko_corridor_terrain.v1',river_id='chilko_river_bc',
        horizontal_crs='EPSG:3157',vertical_reference=VERTICAL,cell_m=1.,mixed_resolution_terrain=True,
        source_kind={'0':'missing','1':'native LidarBC 1 m terrain','2':'MRDEM-30 adjusted Copernicus terrain, bilinear resampled; NOT 1 m source'},
        ownership='first finite native source; coarse fallback fills only missing terrain; no datum offset or smoothing',
        inputs=dict(plan=str(plan_path.resolve()),plan_sha256=sha(plan_path),
                    capture_collection=str(captures.resolve()),fallback_manifest=str(fallback_path.resolve()),
                    fallback_sha256=sha(fallback_path),fallback_outputs=fallback['outputs']),
        attribution=['Contains information licensed under the Open Government Licence - British Columbia',
                     'Contains information licensed under the Open Government Licence - Canada'],
        source_notice='MRDEM derived in part from Copernicus WorldDEM-30; retain the original NRCan product attribution and rights notice.',
        route_sha256=plan['route_sha256'],required_buffer_m=plan['buffer_m'],
        missing_required_corridor_pixels=sum(r['missing_required_corridor_pixels'] for r in records),
        required_corridor_terrain_covered=all(r['missing_required_corridor_pixels']==0 for r in records),
        empty_native_requests=empty,tiles=records,
        submerged_bed_measured=False,hydraulic_bed_ready=False,rapid_boundaries_verified=False,playable_acceptance=False)
    (out/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','captures','fallback','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=assemble(a.plan,a.captures,a.fallback,a.out)
    print(json.dumps(dict(tiles=len(r['tiles']),required_corridor_terrain_covered=r['required_corridor_terrain_covered'],
                         missing_required_corridor_pixels=r['missing_required_corridor_pixels'])))
