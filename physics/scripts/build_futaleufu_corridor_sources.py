"""Native-grid source window for the entire Rio Azul-to-Pasarela route.

Keeps all three dated optical captures as original DN pixels. The DSM is
resampled from the captured GLO-30 pixel-centre transform, not an assumed
integer-degree corner. This is source preparation, not bathymetry, a water
solution, a vegetation inventory, or a replacement for the installed map.
"""
import argparse
import hashlib
import json
from contextlib import ExitStack
from pathlib import Path

import numpy as np

from futaleufu_imagery import BANDS, grid

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/futaleufu_river_chile'
CORRIDOR = BASE/'production_corridor/rio_azul_swinging_bridge_to_pasarela'
ROUTE = CORRIDOR/'hydrography/continuous_route_2026_10_v2/coordinate_map.json'
OPTICAL = BASE/'futaleufu_sources_2026_09/sentinel2'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def crop_bounds(meta, xy, buffer_m):
    xy = np.asarray(xy, dtype=float)
    if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 2 or not np.isfinite(xy).all():
        raise ValueError('Finite projected route required')
    if not np.isfinite(buffer_m) or not 100 <= buffer_m <= 1000:
        raise ValueError('100-1000 m source context required')
    if meta['cell_m'] != 10 or not np.isfinite([meta['x0'], meta['y0']]).all():
        raise ValueError('Verified native 10 m grid required')
    low, high = xy.min(axis=0)-buffer_m, xy.max(axis=0)+buffer_m
    c0 = int(np.floor((low[0]-meta['x0'])/10))
    c1 = int(np.ceil((high[0]-meta['x0'])/10))
    r0 = int(np.floor((meta['y0']-high[1])/10))
    r1 = int(np.ceil((meta['y0']-low[1])/10))
    if not (0 <= r0 < r1 <= meta['shape'][0] and 0 <= c0 < c1 <= meta['shape'][1]):
        raise ValueError('Full corridor is outside captured optical coverage; never clamp')
    return r0, r1, c0, c1


def optical_crop(archive, meta, bounds):
    r0,r1,c0,c1 = bounds
    bands = {}
    valid = np.ones((r1-r0,c1-c0),dtype=bool)
    for name in BANDS:
        raw = archive[name]
        if raw.dtype != np.dtype('uint16') or list(raw.shape) != meta['shape']:
            raise ValueError('Optical array/grid mismatch')
        bands[name] = raw[r0:r1,c0:c1].copy()
        valid &= bands[name] != 0
    # Missing source values remain zero. Never fill from another date or let
    # their converted reflectance (-0.1) participate in cover classification.
    return dict(**bands, valid=valid)


def aligned_dsm_bounds(bounds, transform):
    a,b,c,d,e,f = list(transform)[:6]
    if b != 0 or d != 0 or a <= 0 or e >= 0:
        raise ValueError('North-up native DSM lattice required')
    west,south,east,north = bounds
    if not np.isfinite([*bounds,a,c,e,f]).all() or west >= east or south >= north:
        raise ValueError('Finite ordered DSM bounds required')
    c0,c1 = np.floor((west-c)/a), np.ceil((east-c)/a)
    r0,r1 = np.floor((north-f)/e), np.ceil((south-f)/e)
    return c+c0*a, f+r1*e, c+c1*a, f+r0*e


def bilinear_dsm(values, transform, longitude, latitude):
    a,b,c,d,e,f = list(transform)[:6]
    values = np.asarray(values)
    if values.ndim != 2 or min(values.shape) < 2 or b != 0 or d != 0 or a <= 0 or e >= 0:
        raise ValueError('North-up two-dimensional DSM required')
    # GDAL transforms describe pixel edges even for AREA_OR_POINT=Point.
    # Subtract half a pixel exactly once to address the recorded sample centres.
    column = (np.asarray(longitude)-c)/a-.5
    row = (np.asarray(latitude)-f)/e-.5
    if (not np.isfinite(column).all() or not np.isfinite(row).all() or
        np.any(column < 0) or np.any(row < 0) or
        np.any(column > values.shape[1]-1) or np.any(row > values.shape[0]-1)):
        raise ValueError('Requested DSM point outside captured centre support')
    i = np.minimum(np.floor(column).astype(int),values.shape[1]-2)
    j = np.minimum(np.floor(row).astype(int),values.shape[0]-2)
    u,v = column-i,row-j
    corners = [values[j,i],values[j,i+1],values[j+1,i],values[j+1,i+1]]
    if not all(np.isfinite(corner).all() for corner in corners):
        raise ValueError('Unknown DSM interpolation neighbour')
    return (corners[0]*(1-u)*(1-v)+corners[1]*u*(1-v)+corners[2]*(1-u)*v+corners[3]*u*v).astype(np.float32)


def build(out, buffer_m=600.):
    import rasterio
    from rasterio.merge import merge
    from rasterio.transform import from_origin, array_bounds
    from rasterio.warp import transform_bounds
    from pyproj import Transformer

    out = Path(out).resolve()
    if out.exists():
        raise ValueError('Fresh source window required')
    route = json.loads(ROUTE.read_text())
    if route['horizontal_origin_m'] != [739986., 5195961.5] or route['world_y_sign'] != -1:
        raise ValueError('Unreviewed route frame')
    xy = np.asarray(route['points'], dtype=float)[:,1:3]+route['horizontal_origin_m']
    fetch = OPTICAL/'fetch_manifest.json'
    capture = json.loads(fetch.read_text())
    items = capture['items']
    if len(items) != 3:
        raise ValueError('Review changed dated capture set')
    reference = grid(items[0])
    r0,r1,c0,c1 = crop_bounds(reference, xy, buffer_m)
    shape = (r1-r0, c1-c0)
    transform = from_origin(reference['x0']+10*c0, reference['y0']-10*r0, 10, 10)
    protected = {ROUTE:sha(ROUTE), fetch:sha(fetch), CORRIDOR/'manifest.json':sha(CORRIDOR/'manifest.json')}
    optical = []
    for item in items:
        meta = grid(item)
        if any(meta[k] != reference[k] for k in ('x0','y0','cell_m','shape')):
            raise ValueError('Dated mosaics do not share a native grid')
        path = (OPTICAL/item['npz']).resolve()
        path.relative_to(OPTICAL)
        if sha(path) != item['npz_sha256']:
            raise ValueError('Captured optical source changed')
        protected[path] = item['npz_sha256']
        with np.load(path, allow_pickle=False) as archive:
            bands = optical_crop(archive,meta,(r0,r1,c0,c1))
            optical.append((item, bands))
    valid_dates = np.sum([bands['valid'] for _,bands in optical],axis=0).astype(np.uint8)
    if (valid_dates == 0).any():
        raise ValueError('No dated optical coverage at some corridor pixels; review required')
    source_records = json.loads((CORRIDOR/'manifest.json').read_text())['source_records']
    dem_records = [s for s in source_records if s['role'] == 'terrain']
    if len(dem_records) != 2:
        raise ValueError('Review changed DSM source set')
    source_metadata = []
    target_bounds = array_bounds(*shape, transform)
    west,south,east,north = transform_bounds('EPSG:32718','EPSG:4326',*target_bounds,densify_pts=21)
    with ExitStack() as stack:
        datasets = []
        for record in dem_records:
            path = (ROOT/record['path']).resolve(); path.relative_to(ROOT)
            if sha(path) != record['sha256']:
                raise ValueError('Captured DSM changed')
            protected[path] = record['sha256']
            source = stack.enter_context(rasterio.open(path))
            if source.crs.to_epsg() != 4326 or source.tags().get('AREA_OR_POINT') != 'Point':
                raise ValueError('Expected captured pixel-centred geographic DSM')
            datasets.append(source)
            source_metadata.append(dict(**record, native_transform=list(source.transform),
                                        shape=[source.height, source.width], tags=source.tags()))
        # Two native pixels of support: do not interpolate against a cropped edge.
        # A free geographic crop origin would shift native samples during
        # merge (and can leave a rounding-gap column). Snap to the captured
        # point-aware lattice BEFORE the one intentional bilinear reprojection.
        native_bounds = aligned_dsm_bounds((west-.001,south-.001,east+.001,north+.001),datasets[0].transform)
        mosaic, source_transform = merge(datasets, bounds=native_bounds,
                                         nodata=np.nan, dtype='float32')
        if not np.isfinite(mosaic).all():
            raise ValueError('DSM source gap inside buffered sampling support')
        east_grid,north_grid = np.meshgrid(transform.c+(np.arange(shape[1])+.5)*10,
                                          transform.f-(np.arange(shape[0])+.5)*10)
        longitude,latitude = Transformer.from_crs(32718,4326,always_xy=True).transform(east_grid,north_grid)
        dsm = bilinear_dsm(mosaic[0],source_transform,longitude,latitude)
    if not np.isfinite(dsm).all():
        raise ValueError('DSM does not cover full native optical window')
    for path,digest in protected.items():
        if sha(path) != digest:
            raise ValueError('Source changed during assembly')
    out.mkdir(parents=True)
    artifacts = []
    for item,bands in optical:
        name = item['datetime'][:10]+'_optical_dn.npz'
        np.savez_compressed(out/name, **bands)
        artifacts.append(dict(file=name,sha256=sha(out/name),datetime=item['datetime'],
                              source=item['npz'],source_sha256=item['npz_sha256'],
                              native_pixels_unchanged=True,missing_pixels=int((~bands['valid']).sum()),
                              validity_array='valid',cloud_screened=False))
    np.savez_compressed(out/'source_dsm.npz', dsm_m=dsm, valid_optical_dates=valid_dates)
    result = dict(schema='raftsim.futaleufu_continuous_sources.v1',
        sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in protected.items()},
        route_length_m=route['points'][-1][0],buffer_m=buffer_m,
        grid=dict(epsg=32718,shape=list(shape),transform=list(transform),cell_m=10,
                  native_optical_crop_rc=[r0,r1,c0,c1],bounds_m=list(target_bounds)),
        optical=artifacts,optical_radiometry='DN * 0.0001 - 0.1 ONLY where valid=True; original nodata=0 retained',
        optical_attribution=capture['attribution'],optical_license=capture['licence'],
        dsm=dict(file='source_dsm.npz',sha256=sha(out/'source_dsm.npz'),sources=source_metadata,
                 method='exact pyproj transform for each target centre, explicit four-source-pixel bilinear interpolation; no approximate raster warp',
                 merged_native_transform=list(source_transform),merged_native_bounds=list(native_bounds),
                 source_nominal_resolution_m=30,output_spacing_is_not_new_detail=True,
                 minimum_m=float(dsm.min()),maximum_m=float(dsm.max()),vertical_reference='EGM2008',
                 represents='DSM: vegetation/buildings and edited water included; not bare ground or bed',
                 license_url='https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf',
                 distribution_requires_article_6_notices=True),
        cells_without_any_optical_date=int((valid_dates==0).sum()),
        minimum_valid_optical_dates=int(valid_dates.min()), dsm_no_data_cells=0,
        terrain_conditioned=False,bathymetry_measured=False,
        discharge_assigned=False,installed_in_engine=False,full_river_complete=False)
    (out/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--buffer-m',type=float,default=600.)
    args = parser.parse_args()
    result = build(args.out,args.buffer_m)
    print(json.dumps(dict(route_m=result['route_length_m'],grid=result['grid'],
                         optical_dates=[x['datetime'] for x in result['optical']],
                         dsm_range_m=[result['dsm']['minimum_m'],result['dsm']['maximum_m']])))
