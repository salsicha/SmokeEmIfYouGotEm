"""Capture a bounded native 1 m LidarBC DEM window, not bathymetry.

Uses public catalogue DEM URLs only and preserves gaps as NaN. Range-read crop
hashes identify the actual capture; they are not hashes of unread full tiles.
No existing source/crop is overwritten. Compatible with the evidence builder's
lidar crop layout. Compound EPSG:6653 means horizontal 3157 + vertical 6647.
"""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse

import numpy as np
import rasterio
from pyproj import CRS
from rasterio.windows import Window

from fetch_colorado_catalog_sources import read, validate_json

INDEX = 'https://services6.arcgis.com/ubm4tcTYICKBpist/arcgis/rest/services/LiDAR_BC_S3_Public/FeatureServer/6'
LICENCE = 'https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc'


def validate_window(bounds, max_pixels=8_000_000):
    if type(max_pixels) is not int or max_pixels <= 0:
        raise ValueError('Positive integer pixel budget required')
    if len(bounds) != 4 or not all(math.isfinite(v) and v == int(v) for v in bounds):
        raise ValueError('Whole-metre finite window required')
    x0, y0, x1, y1 = bounds
    if x1 <= x0 or y1 <= y0 or (x1-x0)*(y1-y0) > max_pixels:
        raise ValueError(f'Empty/reversed window or more than {max_pixels} pixels')
    return tuple(map(int, bounds))


def validate_catalogue(row, filename):
    url = row.get('s3Url', '')
    u = urlparse(url)
    if (row.get('filename') != filename or Path(filename).name != filename or
            '\\' in filename or not filename.endswith('.tif') or
            row.get('spacing') != '1 metre' or row.get('projection') != 'utm10' or
            u.scheme != 'https' or u.netloc != 'nrs.objectstore.gov.bc.ca' or
            not u.path.startswith('/gdwuts/') or '/dem/' not in u.path or
            Path(u.path).name != filename or u.query or u.fragment):
        raise ValueError('Unreviewed tile, resolution, projection or public DEM URL')
    return url


def validate_raster(src):
    crs = CRS(src.crs)
    components = crs.sub_crs_list
    if (len(components) != 2 or components[0].to_epsg() != 3157 or
            components[1].to_epsg() != 6647 or src.res != (1., 1.) or
            src.count != 1 or src.dtypes != ('float32',) or
            src.transform.b != 0 or src.transform.d != 0 or
            src.transform.a != 1 or src.transform.e != -1):
        raise ValueError('Expected native EPSG:3157/6647 north-up one-metre float DEM')


def capture(filename, bounds, out):
    bounds = validate_window(bounds)
    if out.suffix != '.npz':
        raise ValueError('NPZ output required')
    catalog_path = out.with_suffix('.catalog.json')
    if any(p.exists() for p in (out, out.with_suffix('.json'), catalog_path)):
        raise ValueError('Fresh crop and receipt names required')
    if not filename.replace('_', '').replace('.', '').isalnum():
        raise ValueError('Unsafe catalogue filename')
    url = INDEX + '/query?' + urlencode(dict(f='json', where=f"filename='{filename}'",
                                            outFields='*', returnGeometry='false'))
    raw = read(url)
    catalogue = validate_json(raw)
    rows = catalogue.get('features', [])
    if len(rows) != 1:
        raise ValueError('Expected exactly one public DEM catalogue record')
    attributes = rows[0]['attributes']
    tile_url = validate_catalogue(attributes, filename)
    x0, y0, x1, y1 = bounds
    shape = (y1-y0, x1-x0)
    height = np.full(shape, np.nan, dtype='float32')
    out.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_bytes(raw)
    # Keep each read bounded, with normal TLS verification and finite timeouts.
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', GDAL_HTTP_TIMEOUT='30',
                      GDAL_HTTP_CONNECTTIMEOUT='15', CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif'):
        with rasterio.open('/vsicurl/' + tile_url) as src:
            validate_raster(src)
            b = src.bounds
            if not (b.left <= x0 < x1 <= b.right and b.bottom <= y0 < y1 <= b.top):
                raise ValueError('Window outside native tile; do not edge-clamp')
            c, r = x0-b.left, b.top-y1
            if c != int(c) or r != int(r):
                raise ValueError('Native pixel grid not aligned with requested crop')
            for start in range(0, shape[0], 128):
                count = min(128, shape[0]-start)
                block = src.read(1, window=Window(c, r+start, shape[1], count), masked=True)
                height[start:start+count] = block.filled(np.nan)
                print(f'Captured native rows {start+count}/{shape[0]}', flush=True)
            raster = dict(crs=src.crs.to_string(), bounds=list(b), nodata=src.nodata,
                          transform=list(src.transform), shape=[src.height, src.width])
    finite = np.isfinite(height)
    if not finite.any():
        raise ValueError('Native tile has no valid pixels in the requested window')
    np.savez_compressed(out, height_m=height, x0=float(x0), y_top=float(y1), cell_m=1.)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    metadata = dict(schema='raftsim.lidarbc_dem_crop.v1',
                    acquired_utc=datetime.now(timezone.utc).isoformat(),
                    window_utm=list(bounds), shape=list(shape), cell_m=1.,
                    crs='EPSG:3157 NAD83(CSRS) / UTM zone 10N',
                    vertical='CGVD2013 (EPSG:6647)',
                    source='LidarBC open LiDAR 1 m bare-earth DEM',
                    licence_url=LICENCE,
                    attribution='Contains information licensed under the Open Government Licence - British Columbia',
                    tiles=[dict(file=filename, url=tile_url, raster=raster,
                                source_catalogue_attributes=attributes,
                                full_tile_hash_verified=False, hash_scope='captured_crop_only')],
                    catalogue_url=url, catalogue_file=catalog_path.name,
                    catalogue_sha256=hashlib.sha256(raw).hexdigest(),
                    npz=out.name, npz_sha256=digest,
                    valid_share=float(finite.mean()), missing_pixels=int((~finite).sum()),
                    height_range_m=[float(height[finite].min()), float(height[finite].max())],
                    measured_underwater_bed=False, rapid_boundaries_verified=False,
                    playable_acceptance=False)
    out.with_suffix('.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: metadata[k] for k in ('shape', 'valid_share', 'missing_pixels', 'npz_sha256')}), flush=True)
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tile', required=True)
    parser.add_argument('--window', type=float, nargs=4, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    capture(args.tile, args.window, args.out)
