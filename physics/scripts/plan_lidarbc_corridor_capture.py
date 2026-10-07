"""Inventory native DEM sources for an entire continuous river corridor.

The conservative grid covers every route segment plus a square buffer. Raster
headers constrain capture requests, but neither catalogue polygons nor headers
prove valid pixels: missing-data coverage is verified by the capture/mosaic
tools later. No elevation, bathymetry, rapid boundary or game map is invented.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
import rasterio
from pyproj import Transformer

from capture_lidarbc_window import INDEX, LICENCE, validate_catalogue, validate_raster, validate_window
from fetch_colorado_catalog_sources import read, validate_json


def corridor_cells(xy, buffer_m=1000, size=2048):
    xy = np.asarray(xy, dtype=float)
    if (xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 2 or
            not np.isfinite(xy).all() or not math.isfinite(buffer_m) or buffer_m <= 0 or
            type(size) is not int or size <= 0 or size*size > 8_000_000):
        raise ValueError('Finite route, positive buffer and bounded integer grid required')
    cells = set()
    for a, b in zip(xy[:-1], xy[1:]):
        lo = np.floor((np.minimum(a, b)-buffer_m)/size).astype(int)
        hi = np.floor((np.maximum(a, b)+buffer_m)/size).astype(int)
        if np.prod(hi-lo+1) > 4096:
            raise ValueError('Implausible long route segment; review source geometry')
        for x in range(lo[0], hi[0]+1):
            for y in range(lo[1], hi[1]+1):
                cells.add((x, y))
        if len(cells) > 4096:
            raise ValueError('Corridor exceeds bounded inventory size')
    return [dict(cell=[x,y], bounds=[x*size,y*size,(x+1)*size,(y+1)*size])
            for x,y in sorted(cells)]


def capture_window(cell_bounds, raster_bounds):
    # Native tiles can have irregular extents. Never clamp outside a raster or
    # assign ownership to a header-only region with unverified valid pixels.
    if len(raster_bounds) != 4 or not all(math.isfinite(v) and v == int(v) for v in raster_bounds):
        raise ValueError('Native whole-metre raster bounds required')
    x0,y0,x1,y1 = raster_bounds
    if x1 <= x0 or y1 <= y0:
        raise ValueError('Reversed raster bounds')
    c0,c1,c2,c3 = validate_window(cell_bounds)
    bounds = [max(c0,x0),max(c1,y0),min(c2,x1),min(c3,y1)]
    return list(validate_window(bounds)) if bounds[0] < bounds[2] and bounds[1] < bounds[3] else None


def route_xy(path):
    source = json.loads(path.read_text())
    if source.get('crs'):
        raise ValueError('Legacy GeoJSON CRS requires explicit review')
    if source.get('type') == 'FeatureCollection':
        if len(source['features']) != 1:
            raise ValueError('One already-connected source route required')
        geometry = source['features'][0]['geometry']
    else:
        geometry = source['geometry'] if source.get('type') == 'Feature' else source
    if geometry.get('type') != 'LineString':
        raise ValueError('Connected LineString required; do not stitch disconnected features')
    ll = np.asarray(geometry['coordinates'], dtype=float)
    if (ll.ndim != 2 or ll.shape[1] < 2 or len(ll)<2 or not np.isfinite(ll).all() or
            (ll[:,0] < -126).any() or (ll[:,0] > -120).any() or
            (ll[:,1] < 48).any() or (ll[:,1] > 61).any()):
        raise ValueError('Expected reviewed UTM 10 British Columbia geographic route')
    return np.column_stack(Transformer.from_crs(4326,3157,always_xy=True).transform(ll[:,0],ll[:,1]))


def route_header_gaps(xy, bounds):
    """Exact line/rectangle interval coverage, not just endpoint membership.

    A cell intersecting a header can still contain an uncovered river segment.
    Even a zero-gap result says nothing about missing pixels inside the header.
    Returned stations are EPSG:3157 polyline lengths, not stored spherical km.
    """
    xy = np.asarray(xy, dtype=float)
    rectangles = np.asarray(bounds, dtype=float).reshape(-1, 4)
    if (xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 2 or
            not np.isfinite(xy).all() or not np.isfinite(rectangles).all() or
            np.any(rectangles[:, 2:] <= rectangles[:, :2])):
        raise ValueError('Finite route and ordered header rectangles required')
    gaps, station = [], 0.
    for a, b in zip(xy[:-1], xy[1:]):
        delta = b-a; length = float(np.linalg.norm(delta))
        if length <= 0:
            raise ValueError('Duplicate route vertices')
        covered = []
        for box in rectangles:
            lo, hi = 0., 1.
            for axis in (0, 1):
                if delta[axis] == 0:
                    if not box[axis] <= a[axis] <= box[axis+2]:
                        hi = -1.; break
                else:
                    t0, t1 = sorted(((box[axis]-a[axis])/delta[axis],
                                     (box[axis+2]-a[axis])/delta[axis]))
                    lo, hi = max(lo, t0), min(hi, t1)
            if hi > lo:
                covered.append((lo, hi))
        cursor = 0.
        for lo, hi in sorted(covered)+[(1., 1.)]:
            if lo > cursor+1e-12:
                left, right = station+cursor*length, station+lo*length
                if gaps and abs(gaps[-1][1]-left) < 1e-6:
                    gaps[-1][1] = right
                else:
                    gaps.append([left, right])
            cursor = max(cursor, hi)
        station += length
    return gaps


def inventory(route, out, buffer_m=1000, size=2048):
    if out.exists():
        raise ValueError('Fresh inventory directory required')
    xy = route_xy(route)
    cells = corridor_cells(xy,buffer_m,size)
    lo,hi = xy.min(axis=0)-buffer_m,xy.max(axis=0)+buffer_m
    query = dict(f='json',where="spacing='1 metre' AND projection='utm10'",
        geometry=','.join(map(str,[*lo,*hi])),geometryType='esriGeometryEnvelope',inSR=3157,
        spatialRel='esriSpatialRelIntersects',outFields='*',returnGeometry='false',orderByFields='OBJECTID')
    url = INDEX+'/query?'+urlencode(query)
    raw = read(url); catalog = validate_json(raw)
    rows = catalog.get('features',[])
    if not rows or len(rows)>64:
        raise ValueError('Missing or unexpectedly broad DEM catalogue response')
    out.mkdir(parents=True)
    (out/'catalogue.json').write_bytes(raw)
    accepted,rejected = [],[]
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',GDAL_HTTP_TIMEOUT='30',
                      GDAL_HTTP_CONNECTTIMEOUT='15',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif'):
        for row in rows:
            a = row['attributes']; filename = a.get('filename','')
            try:
                source_url = validate_catalogue(a,filename)
                with rasterio.open('/vsicurl/'+source_url) as src:
                    validate_raster(src)
                    bounds = list(src.bounds)
                    # Validate grid origin as well as CRS, transform and resolution.
                    capture_window(bounds if (bounds[2]-bounds[0])*(bounds[3]-bounds[1])<=8_000_000
                                   else [bounds[0],bounds[1],bounds[0]+1,bounds[1]+1],bounds)
                    accepted.append(dict(filename=filename,url=source_url,catalogue_attributes=a,
                        raster_bounds=bounds,crs=src.crs.to_string(),shape=[src.height,src.width],
                        valid_pixel_coverage_verified=False,full_tile_hash_verified=False))
                print('HEADER '+filename,flush=True)
            except (ValueError,rasterio.errors.RasterioError) as error:
                rejected.append(dict(filename=filename,error=str(error)))
                print('UNAVAILABLE '+filename+': '+str(error),flush=True)
    requests = []
    for cell in cells:
        names=[]
        for tile in accepted:
            bounds=capture_window(cell['bounds'],tile['raster_bounds'])
            if bounds:
                requests.append(dict(cell=cell['cell'],tile=tile['filename'],window_utm=bounds))
                names.append(tile['filename'])
        cell['candidate_tiles']=names
    result=dict(schema='raftsim.lidarbc_continuous_capture_plan.v1',
        route=str(route.resolve()),route_sha256=hashlib.sha256(route.read_bytes()).hexdigest(),
        route_length_m=float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()),
        route_endpoints_utm=xy[[0,-1]].tolist(),horizontal_crs='EPSG:3157',vertical='CGVD2013 (EPSG:6647)',
        buffer_m=buffer_m,grid_size_m=size,
        cell_selection='Conservative segment AABBs plus square buffer; may include extra terrain, never clips river bends',
        catalogue_url=url,catalogue_sha256=hashlib.sha256(raw).hexdigest(),licence_url=LICENCE,
        attribution='Contains information licensed under the Open Government Licence - British Columbia',
        accepted_headers=accepted,rejected_headers=rejected,cells=cells,capture_requests=requests,
        cells_without_candidate_headers=[c['cell'] for c in cells if not c['candidate_tiles']],
        route_header_gap_intervals_m=route_header_gaps(xy,[t['raster_bounds'] for t in accepted]),
        valid_pixel_coverage_verified=False,measured_underwater_bed=False,rapid_boundaries_verified=False,
        full_river_playable=False)
    (out/'plan.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--route',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--buffer-m',type=float,default=1000);p.add_argument('--size',type=int,default=2048)
    a=p.parse_args();r=inventory(a.route,a.out,a.buffer_m,a.size)
    print(json.dumps(dict(route_length_m=r['route_length_m'],cells=len(r['cells']),
        tiles=len(r['accepted_headers']),rejected_headers=len(r['rejected_headers']),
        requests=len(r['capture_requests']),cells_without_candidate_headers=r['cells_without_candidate_headers'])))
