"""Fetch Sentinel-2 L2A windows from the AWS Earth Search open archive (numpy only).

Reads only the tiles of each cloud-optimised GeoTIFF that cover a lon/lat
window, by HTTP range requests; no account and no full-granule download.
Collection `sentinel-2-c1-l2a` (Element 84 Earth Search v1): surface
reflectance = DN * 0.0001 - 0.1, nodata 0; SCL is the ESA scene
classification (20 m).

Two modes:
  screen  read the SCL window of every candidate item in a STAC search result
          and rank them by cloud, cloud shadow and cirrus inside the window
          (the item's own eo:cloud_cover is for the whole 110 km granule);
  fetch   read the named bands of the chosen items and write one .npz per
          item (uint16 DN arrays, UTM transform, EPSG, STAC properties) plus
          a true-colour quicklook PNG.

Copernicus Sentinel data [year], processed by ESA; open and free with
attribution (Copernicus Sentinel Data Terms and Conditions).
"""
import argparse
import hashlib
import json
import struct
import time
import urllib.request
import zlib
from pathlib import Path

import numpy as np

from png_numpy import write_png

_TYPES = {1: 'B', 2: 's', 3: 'H', 4: 'I', 5: 'II', 11: 'f', 12: 'd', 16: 'Q'}
_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 11: 4, 12: 8, 16: 8}
SCL_NAMES = {0: 'no_data', 1: 'saturated', 2: 'dark_or_topographic_shadow', 3: 'cloud_shadow', 4: 'vegetation',
             5: 'not_vegetated', 6: 'water', 7: 'unclassified', 8: 'cloud_medium', 9: 'cloud_high',
             10: 'thin_cirrus', 11: 'snow'}


def lonlat_to_utm(lon_deg, lat_deg, zone, south):
    """Forward WGS84 transverse Mercator (Snyder series); window extents only."""
    lon, lat = np.radians(lon_deg), np.radians(lat_deg)
    a, f, k0 = 6378137.0, 1 / 298.257223563, 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    lon0 = np.radians(-183.0 + 6.0 * zone)
    n = a / np.sqrt(1 - e2 * np.sin(lat) ** 2)
    t = np.tan(lat) ** 2
    c = ep2 * np.cos(lat) ** 2
    aa = np.cos(lat) * (lon - lon0)
    m = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * lat
             - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * np.sin(2 * lat)
             + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * np.sin(4 * lat)
             - (35 * e2 ** 3 / 3072) * np.sin(6 * lat))
    e = k0 * n * (aa + (1 - t + c) * aa ** 3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * ep2) * aa ** 5 / 120) + 500000.0
    nn = k0 * (m + n * np.tan(lat) * (aa * aa / 2 + (5 - t + 9 * c + 4 * c * c) * aa ** 4 / 24
                                      + (61 - 58 * t + t * t + 600 * c - 330 * ep2) * aa ** 6 / 720))
    return e, nn + (10000000.0 if south else 0.0)


def _range(url, start, size, retries=4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'Range': f'bytes={start}-{start + size - 1}',
                                                       'User-Agent': 'RaftSim-evidence-research/1.0'})
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
            assert len(body) == size, f'short read {len(body)} != {size}'
            return body
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2.0 * (attempt + 1))


class RemoteCOG:
    """First (full-resolution) image of a classic little/big-endian tiled TIFF."""

    def __init__(self, url, header_bytes=1 << 16):
        self.url = url
        self.head = _range(url, 0, header_bytes)
        self.endian = {b'II': '<', b'MM': '>'}[self.head[:2]]
        assert struct.unpack_from(self.endian + 'H', self.head, 2)[0] == 42, 'BigTIFF not supported'
        self.tags = self._ifd(struct.unpack_from(self.endian + 'I', self.head, 4)[0])
        t = self.tags
        self.width, self.height = t[256][0], t[257][0]
        self.tw, self.th = t[322][0], t[323][0]
        self.offsets, self.counts = t[324], t[325]
        self.compression = t.get(259, [1])[0]
        self.predictor = t.get(317, [1])[0]
        assert t.get(277, [1])[0] == 1, 'single-band COGs only'
        bits, fmt = t[258][0], t.get(339, [1])[0]
        self.dtype = np.dtype(self.endian + {(1, 8): 'u1', (1, 16): 'u2', (2, 16): 'i2', (3, 32): 'f4'}[(fmt, bits)])
        scale, tie = t[33550], t[33922]
        self.x0, self.y0 = tie[3] - tie[0] * scale[0], tie[4] + tie[1] * scale[1]
        self.cell = scale[0]
        assert abs(scale[0] - scale[1]) < 1e-9

    def _bytes(self, offset, size):
        if offset + size <= len(self.head):
            return self.head[offset:offset + size]
        return _range(self.url, offset, size)

    def _ifd(self, offset):
        e = self.endian
        count = struct.unpack_from(e + 'H', self._bytes(offset, 2))[0]
        entries = self._bytes(offset + 2, 12 * count)
        tags = {}
        for k in range(count):
            tag, typ, n, value = struct.unpack_from(e + 'HHI4s', entries, 12 * k)
            if typ not in _SIZES:
                continue
            size = _SIZES[typ] * n
            raw = value[:size] if size <= 4 else self._bytes(struct.unpack_from(e + 'I', value)[0], size)
            if typ == 2:
                tags[tag] = raw.rstrip(b'\0').decode('ascii', 'replace')
            elif typ == 5:
                tags[tag] = [a / b for a, b in zip(*[iter(struct.unpack(e + 'I' * (2 * n), raw))] * 2)]
            else:
                tags[tag] = list(struct.unpack(e + _TYPES[typ] * n, raw))
        return tags

    def _tile(self, tr, tc):
        k = tr * ((self.width + self.tw - 1) // self.tw) + tc
        cnt = self.counts[k]
        if cnt == 0:
            return np.zeros((self.th, self.tw), self.dtype.newbyteorder('='))
        raw = _range(self.url, self.offsets[k], cnt)
        if self.compression in (8, 32946):
            raw = zlib.decompress(raw)
        else:
            assert self.compression == 1, f'compression {self.compression} unsupported'
        block = np.frombuffer(raw, self.dtype).reshape(self.th, self.tw)
        if self.predictor == 2:
            block = np.cumsum(block, axis=1, dtype=block.dtype)
        return block.astype(self.dtype.newbyteorder('='))

    def read_window(self, xmin, ymin, xmax, ymax, allow_partial=False):
        """Pixels whose area lies in [xmin, xmax] x [ymin, ymax] (UTM m); returns (array, x0, y0).

        Raises if the window reaches past the granule, since a clamped read would
        silently drop part of the reach; with allow_partial the missing part
        is returned as nodata (0) for mosaicking with the neighbouring granule."""
        c0 = int(np.floor((xmin - self.x0) / self.cell))
        c1 = int(np.ceil((xmax - self.x0) / self.cell))
        r0 = int(np.floor((self.y0 - ymax) / self.cell))
        r1 = int(np.ceil((self.y0 - ymin) / self.cell))
        if not allow_partial and (c0 < 0 or r0 < 0 or c1 > self.width or r1 > self.height):
            raise ValueError(f'window rows {r0}:{r1} cols {c0}:{c1} exceeds granule {self.height} x {self.width}')
        out = np.zeros((r1 - r0, c1 - c0), self.dtype.newbyteorder('='))
        for tr in range(max(r0, 0) // self.th, (min(r1, self.height) - 1) // self.th + 1):
            for tc in range(max(c0, 0) // self.tw, (min(c1, self.width) - 1) // self.tw + 1):
                block = self._tile(tr, tc)
                br0, bc0 = tr * self.th, tc * self.tw
                a0, a1 = max(r0, br0), min(r1, br0 + self.th, self.height)
                b0, b1 = max(c0, bc0), min(c1, bc0 + self.tw, self.width)
                out[a0 - r0:a1 - r0, b0 - c0:b1 - c0] = block[a0 - br0:a1 - br0, b0 - bc0:b1 - bc0]
        return out, self.x0 + c0 * self.cell, self.y0 - r0 * self.cell


def item_epsg(item):
    p = item['properties']
    code = p.get('proj:epsg') or p.get('proj:code')
    return int(str(code).split(':')[-1])


def utm_window(item, bbox):
    epsg = item_epsg(item)
    zone, south = epsg % 100, epsg // 100 == 327
    lon = np.array([bbox[0], bbox[2], bbox[0], bbox[2]]); lat = np.array([bbox[1], bbox[1], bbox[3], bbox[3]])
    e, n = lonlat_to_utm(lon, lat, zone, south)
    return epsg, (float(e.min()), float(n.min()), float(e.max()), float(n.max()))


def screen(args):
    items = json.loads(Path(args.stac).read_text())['features']
    if args.tile:
        items = [f for f in items if f['properties'].get('s2:mgrs_tile', f['id'].split('_')[1][1:]) == args.tile
                 or f"_T{args.tile}_" in f['id']]
    rows = []
    for item in items:
        epsg, win = utm_window(item, args.bbox)
        cog = RemoteCOG(item['assets']['scl']['href'])
        scl, _, _ = cog.read_window(*win)
        total = scl.size
        frac = {SCL_NAMES[k]: float((scl == k).sum()) / total for k in SCL_NAMES}
        bad = frac['cloud_medium'] + frac['cloud_high'] + frac['thin_cirrus'] + frac['cloud_shadow'] + frac['no_data']
        rows.append(dict(id=item['id'], datetime=item['properties']['datetime'], epsg=epsg,
                         granule_cloud_cover=item['properties'].get('eo:cloud_cover'), window_obstructed=bad,
                         window_scl_fractions=frac))
        print(f"{item['id']}  obstructed {bad:6.3f}  cloud {frac['cloud_medium'] + frac['cloud_high']:.3f}"
              f"  cirrus {frac['thin_cirrus']:.3f}  shadow {frac['cloud_shadow']:.3f}  water {frac['water']:.3f}", flush=True)
    rows.sort(key=lambda r: r['window_obstructed'])
    Path(args.out).write_text(json.dumps(dict(schema='raftsim.sentinel2_window_screen.v1', stac_search=args.stac,
                                              bbox_lonlat=args.bbox, items=rows), indent=2) + '\n')


def fetch(args):
    feats = {f['id']: f for f in json.loads(Path(args.stac).read_text())['features']}
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for item_id in args.ids:
        # 'A+B' mosaics same-datatake granules of one UTM zone (same 10 m grid):
        # pixels that are nodata in A are taken from B.
        parts = [feats[k] for k in item_id.split('+')]
        item = parts[0]
        epsg, win = utm_window(item, args.bbox)
        assert all(item_epsg(p) == epsg for p in parts), 'mosaic parts must share a UTM zone'
        arrays, meta = {}, {}
        for band in args.bands:
            a = None
            for part in parts:
                asset = part['assets'][band]
                cog = RemoteCOG(asset['href'])
                b, bx0, by0 = cog.read_window(*win, allow_partial=len(parts) > 1)
                if a is None:
                    a, x0, y0, hrefs = b, bx0, by0, [asset['href']]
                else:
                    assert (bx0, by0, b.shape) == (x0, y0, a.shape), 'mosaic parts are not on one grid'
                    hole = a == 0
                    a[hole] = b[hole]
                    hrefs.append(asset['href'])
            arrays[band] = a
            meta[band] = dict(href=hrefs if len(hrefs) > 1 else hrefs[0], cell_m=cog.cell, x0=x0, y0=y0,
                              shape=list(a.shape), nodata_fraction=float((a == 0).mean()),
                              raster_bands=asset.get('raster:bands'))
            print(item_id, band, a.shape, 'nodata', meta[band]['nodata_fraction'], flush=True)
        scl_stats = None
        if 'scl' in arrays:
            scl = arrays['scl']
            scl_stats = {SCL_NAMES[k]: float((scl == k).mean()) for k in SCL_NAMES}
        name = parts[0]['id'] + ('_mosaic' if len(parts) > 1 else '')
        path = out_dir / f'{name}.npz'
        np.savez_compressed(path, **arrays)
        rgb = None
        if all(b in arrays for b in ('red', 'green', 'blue')):
            refl = np.stack([arrays[b].astype(np.float32) * 1e-4 - 0.1 for b in ('red', 'green', 'blue')], axis=2)
            rgb = (np.clip(refl / args.quicklook_white, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)
            write_png(out_dir / f'{name}_truecolour.png', rgb)
        records.append(dict(id=item_id, datetime=item['properties']['datetime'], epsg=epsg,
                            window_utm_m=dict(zip(('xmin', 'ymin', 'xmax', 'ymax'), win)), npz=path.name,
                            npz_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bands=meta,
                            window_scl_fractions=scl_stats,
                            stac_item_self=[next((l['href'] for l in p['links'] if l['rel'] == 'self'), None) for p in parts],
                            properties={k: item['properties'].get(k) for k in (
                                'eo:cloud_cover', 's2:processing_baseline', 's2:product_uri', 'sun:elevation',
                                'sun:azimuth', 'view:sun_elevation', 'view:sun_azimuth', 's2:mgrs_tile', 'platform')}))
    Path(out_dir / 'fetch_manifest.json').write_text(json.dumps(dict(
        schema='raftsim.sentinel2_window_fetch.v1', collection='sentinel-2-c1-l2a',
        stac_api='https://earth-search.aws.element84.com/v1', bbox_lonlat=args.bbox,
        reflectance='DN * 0.0001 - 0.1 (nodata 0)', quicklook=f'true colour, white {args.quicklook_white}, gamma 2.2',
        licence='Copernicus Sentinel data, open and free with attribution (Copernicus Sentinel Data Terms and Conditions)',
        attribution='Contains modified Copernicus Sentinel data [year], processed by ESA',
        items=records), indent=2) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='mode', required=True)
    s = sub.add_parser('screen'); f = sub.add_parser('fetch')
    for p in (s, f):
        p.add_argument('--stac', required=True, help='STAC search result JSON (FeatureCollection)')
        p.add_argument('--bbox', type=float, nargs=4, required=True, metavar=('LON0', 'LAT0', 'LON1', 'LAT1'))
        p.add_argument('--out', required=True)
    s.add_argument('--tile', help='only items of this MGRS tile, e.g. 17PKM')
    f.add_argument('--ids', nargs='+', required=True)
    f.add_argument('--bands', nargs='+', default=['blue', 'green', 'red', 'nir', 'scl'])
    f.add_argument('--quicklook-white', type=float, default=0.25)
    args = ap.parse_args()
    (screen if args.mode == 'screen' else fetch)(args)


if __name__ == '__main__':
    main()
