"""Fetch WMTS tiles covering a buffered river corridor and stitch them (numpy only).

For GeoWebCache-backed services that only answer tile-aligned requests (for
example SNIT Costa Rica `Ortofoto2017`). Uses the standard EPSG:3857
("GoogleMapsCompatible") matrix, whose tile (col, row) at zoom z covers Web
Mercator x in [-20037508.34 + col * t, ...] with t = 40075016.69 / 2^z.

The corridor is every tile within --buffer-m of the centreline between two
chainages (from extract_osm_river_centreline.py). Writes the original PNG
tiles, a stitched RGBA mosaic (.npz, with its Web Mercator bounds) and a
manifest with the request template and a SHA-256 per tile.
"""
import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

import numpy as np

from png_numpy import read_png, write_png

HALF = 20037508.342789244


def lonlat_to_merc(lon, lat):
    return np.radians(lon) * 6378137.0, 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--centreline', required=True)
    ap.add_argument('--chain-m', type=float, nargs=2, required=True)
    ap.add_argument('--buffer-m', type=float, default=400.0, help='ground metres either side of the centreline')
    ap.add_argument('--zoom', type=int, required=True)
    ap.add_argument('--url', required=True, help='GetTile template with {z} {row} {col}')
    ap.add_argument('--out', required=True)
    ap.add_argument('--pause-s', type=float, default=0.1)
    args = ap.parse_args()
    cl = np.array(json.loads(Path(args.centreline).read_text(encoding='utf-8'))['centreline_lon_lat_chain'])
    s0, s1 = args.chain_m
    keep = (cl[:, 2] >= s0) & (cl[:, 2] <= s1)
    # Densify to 10 m so the buffer test is continuous.
    sub = cl[max(np.argmax(keep) - 1, 0):len(keep) - np.argmax(keep[::-1]) + 1]
    ss = np.arange(s0, s1 + 10, 10.0)
    lon = np.interp(ss, sub[:, 2], sub[:, 0]); lat = np.interp(ss, sub[:, 2], sub[:, 1])
    mx, my = lonlat_to_merc(lon, lat)
    scale = 1 / np.cos(np.radians(lat.mean()))  # ground m -> Web Mercator m
    buf = args.buffer_m * scale
    t = 2 * HALF / 2 ** args.zoom
    tiles = set()
    for x, y in zip(mx, my):
        for col in range(int((x - buf + HALF) // t), int((x + buf + HALF) // t) + 1):
            for row in range(int((HALF - (y + buf)) // t), int((HALF - (y - buf)) // t) + 1):
                cx = -HALF + (col + 0.5) * t; cy = HALF - (row + 0.5) * t
                # nearest distance from the tile rectangle to the point, within the buffer
                dx = max(abs(cx - x) - t / 2, 0); dy = max(abs(cy - y) - t / 2, 0)
                if np.hypot(dx, dy) <= buf:
                    tiles.add((col, row))
    tiles = sorted(tiles)
    out = Path(args.out); tdir = out / f'tiles_z{args.zoom}'; tdir.mkdir(parents=True, exist_ok=True)
    print(f'{len(tiles)} tiles at z{args.zoom} ({t / scale:.1f} m ground per tile, {t / 256 / scale:.3f} m/px)', flush=True)
    records = []
    for k, (col, row) in enumerate(tiles):
        path = tdir / f'{args.zoom}_{col}_{row}.png'
        if not path.exists():
            url = args.url.format(z=args.zoom, row=row, col=col)
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(urllib.request.Request(
                            url, headers={'User-Agent': 'RaftSim-evidence-research/1.0'}), timeout=120) as r:
                        body, ctype = r.read(), r.headers.get('Content-Type')
                    assert ctype and ctype.startswith('image/png'), f'{ctype}: {body[:200]!r}'
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    time.sleep(3 * (attempt + 1))
            path.write_bytes(body)
            time.sleep(args.pause_s)
        records.append(dict(col=col, row=row, file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        if k % 25 == 0:
            print(f'  {k + 1}/{len(tiles)}', flush=True)
    cols = [c for c, _ in tiles]; rows = [r for _, r in tiles]
    c0, r0 = min(cols), min(rows)
    mosaic = np.zeros(((max(rows) - r0 + 1) * 256, (max(cols) - c0 + 1) * 256, 4), np.uint8)
    for rec in records:
        img = read_png(tdir / rec['file'])
        if img.ndim == 2:
            img = np.repeat(img[..., None], 3, axis=2)
        if img.shape[2] == 3:
            img = np.concatenate([img, np.full(img.shape[:2] + (1,), 255, np.uint8)], axis=2)
        rr, cc = (rec['row'] - r0) * 256, (rec['col'] - c0) * 256
        mosaic[rr:rr + 256, cc:cc + 256] = img
        rec['opaque_fraction'] = float((img[..., 3] > 0).mean())
    bounds = dict(xmin=-HALF + c0 * t, xmax=-HALF + (max(cols) + 1) * t, ymax=HALF - r0 * t, ymin=HALF - (max(rows) + 1) * t)
    np.savez_compressed(out / f'mosaic_z{args.zoom}.npz', rgba=mosaic,
                        bounds_epsg3857=np.array([bounds['xmin'], bounds['ymin'], bounds['xmax'], bounds['ymax']]))
    write_png(out / f'mosaic_z{args.zoom}_preview.png', mosaic[::4, ::4, :3])
    manifest = dict(schema='raftsim.wmts_corridor_fetch.v1', url_template=args.url, zoom=args.zoom,
                    tile_matrix_set='EPSG:3857 (GoogleMapsCompatible, 256 px)', centreline=Path(args.centreline).name,
                    chain_m=[s0, s1], buffer_m=args.buffer_m, tile_ground_m=t / scale, pixel_ground_m=t / 256 / scale,
                    mosaic=f'mosaic_z{args.zoom}.npz', mosaic_shape=list(mosaic.shape), mosaic_bounds_epsg3857=bounds,
                    mosaic_sha256=hashlib.sha256((out / f'mosaic_z{args.zoom}.npz').read_bytes()).hexdigest(),
                    tiles=records, retrieved_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    (out / 'fetch_manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    opaque = np.mean([r['opaque_fraction'] for r in records])
    print(f'mosaic {mosaic.shape}, mean opaque fraction {opaque:.3f}')


if __name__ == '__main__':
    main()
