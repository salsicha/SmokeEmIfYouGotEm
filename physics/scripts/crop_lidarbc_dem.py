"""Crop and mosaic LidarBC 1 m DEM tiles to a UTM window (numpy + OpenImageIO, run with Blender's python).

LidarBC bare-earth DEM tiles are float32 GeoTIFFs (LZW, one-row strips),
NAD83(CSRS) / UTM zone 10N (EPSG:3157), CGVD2013 heights (EPSG:6647), nodata
-32767, 1 m pixels whose ModelTiepoint is the upper-left pixel corner.
OpenImageIO reads just the scanlines inside the window (in row chunks); the
GeoTIFF tags are parsed with tiff_numpy. --block N averages N x N blocks of
valid 1 m cells (a block with no valid cell is NaN), for far-terrain meshes.
Output: an .npz with the height grid (NaN where no tile has data) and its
georeferencing, plus provenance (tile names, hashes).
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
import OpenImageIO as oiio

from tiff_numpy import _ifd


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()


def georef(path):
    with open(path, 'rb') as fh:
        head = fh.read(8)
        e = {b'II': '<', b'MM': '>'}[head[:2]]
        off = struct.unpack_from(e + 'I', head, 4)[0]
        fh.seek(0)
        data = fh.read(off + 262144)
    t = _ifd(data, e, off)
    keys = t.get(34735, [])
    keys = {keys[i]: keys[i + 3] for i in range(4, len(keys), 4)}
    return dict(x0=float(t[33922][3]), y0=float(t[33922][4]), sx=float(t[33550][0]), sy=float(t[33550][1]),
                width=int(t[256][0]), height=int(t[257][0]), nodata=float(t[42113]) if 42113 in t else None,
                epsg=keys.get(3072), vertical_epsg=keys.get(4096))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tiles', type=Path, nargs='+')
    ap.add_argument('--window', type=float, nargs=4, required=True, metavar=('X0', 'Y0', 'X1', 'Y1'), help='UTM metres, whole metres')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--block', type=int, default=1, help='average N x N blocks of 1 m cells (window must be a multiple of N)')
    ap.add_argument('--chunk-rows', type=int, default=1000)
    args = ap.parse_args()
    X0, Y0, X1, Y1 = [float(round(v)) for v in args.window]
    W, H = int(X1 - X0), int(Y1 - Y0)
    B = args.block
    assert W % B == 0 and H % B == 0, 'window must be a whole number of blocks'
    total = np.zeros((H // B, W // B), np.float64)
    count = np.zeros((H // B, W // B), np.int64)
    used = []
    for tile in args.tiles:
        g = georef(tile)
        assert g['sx'] == 1.0 and g['sy'] == 1.0 and g['epsg'] == 3157, (tile, g)
        c0 = int(max(X0 - g['x0'], 0)); c1 = int(min(X1 - g['x0'], g['width']))
        r0 = int(max(g['y0'] - Y1, 0)); r1 = int(min(g['y0'] - Y0, g['height']))
        if c1 <= c0 or r1 <= r0:
            continue
        # snap the read to whole blocks so each block is filled from one tile
        gr0 = int(Y1 - (g['y0'] - r0)); gc0 = int(g['x0'] + c0 - X0)  # window row/col of tile row r0 / col c0
        gr0b, gc0b = -(-gr0 // B) * B, -(-gc0 // B) * B
        r0 += gr0b - gr0; c0 += gc0b - gc0; gr0, gc0 = gr0b, gc0b
        r1 = r0 + (r1 - r0) // B * B; c1 = c0 + (c1 - c0) // B * B
        if c1 <= c0 or r1 <= r0:
            continue
        inp = oiio.ImageInput.open(str(tile))
        for q0 in range(r0, r1, args.chunk_rows // B * B):
            q1 = min(q0 + args.chunk_rows // B * B, r1)
            rows = np.asarray(inp.read_scanlines(0, 0, q0, q1, 0, 0, 1, oiio.FLOAT), dtype=np.float32).reshape(q1 - q0, -1)[:, c0:c1]
            if g['nodata'] is not None:
                rows = np.where(rows <= g['nodata'] + 1, np.nan, rows)
            blk = rows.reshape((q1 - q0) // B, B, (c1 - c0) // B, B)
            ok = np.isfinite(blk)
            br0 = (gr0 + q0 - r0) // B; bc0 = gc0 // B
            cnt_sub = count[br0:br0 + blk.shape[0], bc0:bc0 + blk.shape[2]]
            tot_sub = total[br0:br0 + blk.shape[0], bc0:bc0 + blk.shape[2]]
            n = ok.sum((1, 3)); t = np.where(ok, blk, 0.0).sum((1, 3))
            take = n > cnt_sub  # the tile covering more of the block owns it (overlaps differ by cm to dm)
            tot_sub[take] = t[take]; cnt_sub[take] = n[take]
        inp.close()
        used.append(dict(file=tile.name, sha256=sha(tile), rows=[r0, r1], cols=[c0, c1], **{k: g[k] for k in ('x0', 'y0', 'epsg', 'vertical_epsg')}))
        print(tile.name, 'rows', r0, r1, 'cols', c0, c1, flush=True)
    grid = np.where(count > 0, total / np.maximum(count, 1), np.nan).astype(np.float32)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out, height_m=grid, x0=X0, y_top=Y1, cell_m=float(B))
    meta = dict(schema='raftsim.lidarbc_dem_crop.v1', window_utm=[X0, Y0, X1, Y1], shape=list(grid.shape), crs='EPSG:3157 NAD83(CSRS) / UTM zone 10N',
                vertical='CGVD2013 (EPSG:6647)', cell_m=float(B),
                pixel=(f'{B} m; row 0 is the north edge (y_top), column 0 the west edge (x0); cell centres at +{B / 2:g}'
                       + ('' if B == 1 else f'; each cell is the mean of the valid 1 m cells in its {B} x {B} block')),
                source='LidarBC open LiDAR 1 m bare-earth DEM (Open Government Licence - British Columbia)', tiles=used,
                valid_share=float(np.isfinite(grid).mean()), height_range_m=[float(np.nanmin(grid)), float(np.nanmax(grid))],
                npz=args.out.name, npz_sha256=sha(args.out))
    args.out.with_suffix('.json').write_text(json.dumps(meta, indent=2) + '\n')
    print(json.dumps({k: meta[k] for k in ('shape', 'valid_share', 'height_range_m')}))


if __name__ == '__main__':
    main()
