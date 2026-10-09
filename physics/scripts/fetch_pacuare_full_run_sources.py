"""Capture SNIT, OSM and Sentinel-2 sources for the full Lower Pacuare run.

Extends the 2026-09 Upper Huacas capture (huacas_sources_2026_09) to the whole
San Martin / Tres Equis to Siquirres run, with the same services, layers and
corridor rule. Downloads approved by the user on 2026-10-08; see
review/snit_use_decision_2026_10_08.json for the SNIT terms, which still bar
commercial use.

Sources:
- OpenStreetMap (Overpass): Rio Pacuare relation 12000489, rapid, put-in and
  river-area features. ODbL.
- SNIT IGN 1:5,000 WFS: curvas_5000, hidrografia_5000, forestal2017_5k.
- SNIT Ortofoto 2017 WMTS: z18 tiles within 400 m of the OSM centreline.
- Sentinel-2 L2A (AWS Open Data): the three Huacas scenes, over the full run.

Corridor: OSM centreline chainage 69,100-96,600 m (GoRafting km -0.5 to
26.7 through the repo fit km = 0.000991 * chain - 68.978), 400 m either side.
Every file is hashed in manifest.json. Downloaded content is only parsed as
data (JSON, PNG, GeoTIFF windows); nothing downloaded is executed.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import time
import urllib.parse
import urllib.request

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RIVER = ROOT / 'physics/data/real_world/pacuare_river_costa_rica'
CENTRELINE = RIVER / 'huacas_sources_2026_09/osm/pacuare_centreline.json'
HUACAS = RIVER / 'huacas_sources_2026_09'
CHAIN_M = (69100.0, 96600.0)
BUFFER_M = 400.0
WFS = 'https://geos.snitcr.go.cr/be/IGN_5/wfs'
LAYERS = ('curvas_5000', 'hidrografia_5000', 'forestal2017_5k')
WMTS = ('https://geos1.snitcr.go.cr/Ortofoto2017/wmts?service=WMTS&version=1.0.0&request=GetTile'
        '&layer=ortofoto_5k:ortofoto2017_5000_altaresolucion&style=&tilematrixset=EPSG:3857'
        '&tilematrix=EPSG:3857:{z}&tilerow={row}&tilecol={col}&format=image/png')
ZOOM = 18
OVERPASS = 'https://overpass-api.de/api/interpreter'
STAC = 'https://earth-search.aws.element84.com/v1'
USER_AGENT = 'SmokeEmIfYouGotEm-river-research/1.0 (one-time corridor capture)'
EARTH = 6378137.0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def get(url, data=None, attempts=4, timeout=120):
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, data=data, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(5 * (attempt + 1))


def corridor_line():
    data = json.loads(CENTRELINE.read_text(encoding='utf-8'))
    pts = np.asarray(data['centreline_lon_lat_chain'], float)
    keep = (pts[:, 2] >= CHAIN_M[0] - 50) & (pts[:, 2] <= CHAIN_M[1] + 50)
    return pts[keep]


def mercator(lon, lat):
    return EARTH * np.radians(lon), EARTH * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))


def segment_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    length2 = np.maximum(dx * dx + dy * dy, 1e-12)
    t = np.clip(((px[:, None] - ax) * dx + (py[:, None] - ay) * dy) / length2, 0, 1)
    return np.hypot(px[:, None] - (ax + t * dx), py[:, None] - (ay + t * dy)).min(axis=1)


def tiles(line):
    """z18 tiles whose footprint can reach within BUFFER_M of the centreline."""
    x, y = mercator(line[:, 0], line[:, 1])
    scale = 1 / math.cos(math.radians(float(line[:, 1].mean())))  # Mercator metres per ground metre
    size = 2 * math.pi * EARTH / 2 ** ZOOM
    reach = (BUFFER_M * scale) + size * math.sqrt(0.5)
    col = lambda v: int(math.floor((v + math.pi * EARTH) / size))
    row = lambda v: int(math.floor((math.pi * EARTH - v) / size))
    cols = range(col(x.min() - reach), col(x.max() + reach) + 1)
    rows = range(row(y.max() + reach), row(y.min() - reach) + 1)
    cc, rr = np.meshgrid(np.array(cols), np.array(rows))
    cx = (cc.ravel() + 0.5) * size - math.pi * EARTH
    cy = math.pi * EARTH - (rr.ravel() + 0.5) * size
    d = np.full(cx.shape, np.inf)
    for i in range(0, len(x) - 1, 200):
        j = slice(i, min(i + 201, len(x)))
        d = np.minimum(d, segment_distance(cx, cy, x[j][:-1], y[j][:-1], x[j][1:], y[j][1:]))
    inside = d <= reach
    return sorted(zip(cc.ravel()[inside].tolist(), rr.ravel()[inside].tolist())), size / scale


def fetch_tiles(line, out, resume=False):
    from PIL import Image
    folder = out / 'ortofoto2017/tiles_z18'
    folder.mkdir(parents=True, exist_ok=resume)
    wanted, ground = tiles(line)

    def decode(body):
        with Image.open(io.BytesIO(body)) as image:
            return np.asarray(image.convert('RGBA'))[..., 3]

    def one(cr):
        c, r = cr
        path = folder / f'{ZOOM}_{c}_{r}.png'
        body, alpha = (path.read_bytes() if path.is_file() else None), None
        if body is not None:
            try:
                alpha = decode(body)
            except Exception:
                body = None
        # The service sometimes answers a tile with a plain-text error under
        # load; retry slowly, and record tiles it never serves.
        for attempt in range(5):
            if alpha is not None:
                break
            body = get(WMTS.format(z=ZOOM, row=r, col=c))
            try:
                alpha = decode(body)
            except Exception:
                time.sleep(3 * (attempt + 1))
        if alpha is None:
            path.unlink(missing_ok=True)
            return dict(col=c, row=r, file=None, unavailable=True, response=body[:80].decode('latin-1'))
        path.write_bytes(body)
        time.sleep(0.1)
        return dict(col=c, row=r, file=path.name, sha256=hashlib.sha256(body).hexdigest(),
                    bytes=len(body), opaque_fraction=float((alpha > 0).mean()))

    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        rows = list(pool.map(one, wanted))
    manifest = dict(schema='raftsim.wmts_corridor_fetch.v1', url_template=WMTS, zoom=ZOOM,
                    tile_matrix_set='EPSG:3857 (GoogleMapsCompatible, 256 px)',
                    centreline=str(CENTRELINE.relative_to(ROOT).as_posix()), chain_m=list(CHAIN_M),
                    buffer_m=BUFFER_M, tile_ground_m=ground, pixel_ground_m=ground / 256, tiles=rows)
    (out / 'ortofoto2017/fetch_manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    served = [r for r in rows if r['file']]
    return dict(tiles=len(served), unavailable=len(rows) - len(served), bytes=sum(r['bytes'] for r in served),
                fully_opaque=sum(r['opaque_fraction'] == 1.0 for r in served))


def fetch_wfs(line, out):
    folder = out / 'ign5_vectors'
    folder.mkdir(parents=True)
    lat_pad, lon_pad = BUFFER_M / 111320.0, BUFFER_M / (111320.0 * math.cos(math.radians(10.0)))
    boxes = []
    for start in np.arange(CHAIN_M[0], CHAIN_M[1], 2000.0):
        part = line[(line[:, 2] >= start - 20) & (line[:, 2] <= start + 2020)]
        if len(part):
            boxes.append([float(part[:, 1].min() - lat_pad), float(part[:, 0].min() - lon_pad),
                          float(part[:, 1].max() + lat_pad), float(part[:, 0].max() + lon_pad)])
    summary = {}
    for layer in LAYERS:
        features, requests = {}, []
        for box in boxes:
            start = 0
            while True:
                query = dict(service='WFS', version='2.0.0', request='GetFeature', typeNames='IGN_5:' + layer,
                             bbox=','.join('%.6f' % v for v in box) + ',urn:ogc:def:crs:EPSG::4326',
                             srsName='urn:ogc:def:crs:EPSG::5367', outputFormat='application/json',
                             count='5000', startIndex=str(start))
                url = WFS + '?' + urllib.parse.urlencode(query)
                page = json.loads(get(url))
                requests.append(url)
                batch = page.get('features', [])
                for f in batch:
                    features[f.get('id') or json.dumps(f['geometry'], sort_keys=True)] = f
                if len(batch) < 5000:
                    break
                start += 5000
            time.sleep(0.5)
        collection = dict(type='FeatureCollection', name=layer,
                          crs=dict(type='name', properties=dict(name='urn:ogc:def:crs:EPSG::5367')),
                          features=[features[k] for k in sorted(features)])
        path = folder / (layer + '.geojson')
        path.write_text(json.dumps(collection) + '\n')
        summary[layer] = dict(features=len(features), requests=len(requests), bytes=path.stat().st_size)
    (folder / 'request_boxes_lat_lon.json').write_text(json.dumps(boxes, indent=1) + '\n')
    return summary


def fetch_osm(line, out):
    folder = out / 'osm'
    folder.mkdir(parents=True)
    pad = 0.01
    south, west = line[:, 1].min() - pad, line[:, 0].min() - pad
    north, east = line[:, 1].max() + pad, line[:, 0].max() + pad
    box = '%.4f,%.4f,%.4f,%.4f' % (south, west, north, east)
    source = (HUACAS / 'osm/pacuare_query.overpassql').read_text(encoding='utf-8')
    query = source.replace('9.95,-83.60,10.10,-83.44', box)
    if query == source:
        raise ValueError('Unexpected Overpass template')
    (folder / 'pacuare_full_run_query.overpassql').write_text(query, encoding='utf-8')
    body = get(OVERPASS, data=urllib.parse.urlencode(dict(data=query)).encode())
    (folder / 'pacuare_full_run_overpass.json').write_bytes(body)
    data = json.loads(body)
    return dict(elements=len(data.get('elements', [])), osm_base=data.get('osm3s', {}).get('timestamp_osm_base'),
                bbox_lat_lon=box, bytes=len(body))


def fetch_sentinel(line, out):
    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds
    folder = out / 'sentinel2'
    folder.mkdir(parents=True, exist_ok=True)
    pad = 0.01
    bbox = [float(line[:, 0].min() - pad), float(line[:, 1].min() - pad),
            float(line[:, 0].max() + pad), float(line[:, 1].max() + pad)]
    old = json.loads((HUACAS / 'sentinel2/fetch_manifest.json').read_text())
    items = []
    for previous in old['items']:
        link = previous['stac_item_self']
        link = link[0] if isinstance(link, list) else link
        item = json.loads(get(link))
        assets = item['assets']
        hrefs = dict(blue=assets['blue']['href'], green=assets['green']['href'], red=assets['red']['href'],
                     nir=assets['nir']['href'], scl=assets['scl']['href'])
        arrays, window_utm = {}, None
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
            for band, href in hrefs.items():
                with rasterio.open(href) as source:
                    bounds = transform_bounds('EPSG:4326', source.crs, *bbox)
                    window = from_bounds(*bounds, transform=source.transform).round_offsets().round_lengths()
                    arrays[band] = source.read(1, window=window)
                    if band == 'blue':
                        t = source.window_transform(window)
                        window_utm = dict(xmin=t.c, ymax=t.f, xmax=t.c + t.a * window.width, ymin=t.f + t.e * window.height)
                        epsg = source.crs.to_epsg()
        path = folder / (item['id'] + '.npz')
        np.savez_compressed(path, **arrays)
        items.append(dict(id=item['id'], datetime=item['properties']['datetime'], epsg=epsg,
                          window_utm_m=window_utm, npz=path.name, npz_sha256=sha(path), bands=hrefs,
                          stac_item_self=link))
    manifest = dict(old, bbox_lonlat=bbox, items=items)
    (folder / 'fetch_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return dict(items=len(items), bbox_lonlat=bbox, bytes=sum((folder / i['npz']).stat().st_size for i in items))


def main(out, parts, resume=False):
    """With resume, only the named parts run, into the existing folder; the
    orthophoto part keeps valid tiles already saved. Earlier results in the
    manifest are kept."""
    out = Path(out).resolve()
    out.relative_to(RIVER)
    previous = {}
    if resume:
        if (out / 'manifest.json').is_file():
            previous = json.loads((out / 'manifest.json').read_text())
    elif out.exists():
        raise ValueError('Fresh capture folder required')
    out.mkdir(parents=True, exist_ok=resume)
    line = corridor_line()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    results = dict(previous.get('results', {}))
    for name, function in (('osm', fetch_osm), ('ign5_vectors', fetch_wfs), ('ortofoto2017', fetch_tiles),
                           ('sentinel2', fetch_sentinel)):
        if name in parts:
            results[name] = function(line, out, resume) if name == 'ortofoto2017' else function(line, out)
            print(name, json.dumps(results[name]), flush=True)
    files = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
    manifest = dict(schema='raftsim.pacuare.full_run_sources.v1', retrieved_started_utc=started,
                    retrieved_finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    retrieval_permission='user approved the full-run SNIT, OSM and Sentinel-2 download on 2026-10-08',
                    reach='Rio Pacuare, San Martin / Tres Equis put-ins to the Siquirres take-out',
                    corridor=dict(centreline=CENTRELINE.relative_to(ROOT).as_posix(), chain_m=list(CHAIN_M),
                                  buffer_m=BUFFER_M, gorafting_km_fit='km = 0.000991030194 * chain_m - 68.9781768448'),
                    rights=dict(snit='SNIT published terms do not authorize commercial use; see '
                                     'review/snit_rights_review_2026_10_07.json and review/snit_use_decision_2026_10_08.json',
                                osm='ODbL 1.0, (c) OpenStreetMap contributors',
                                sentinel2='Copernicus Sentinel data terms; attribution required'),
                    results=results, files=files)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=RIVER / 'full_run_sources_2026_10')
    parser.add_argument('--parts', default='osm,ign5_vectors,ortofoto2017,sentinel2')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    main(args.out, set(args.parts.split(',')), args.resume)
