"""Whitewater along a Cartesian cook, bin by bin and per catalogued feature (numpy only).

    audit_cartesian_whitewater.py <atlas_dir> <evidence_dir> --origin E N [--catalogue cat.json] [--bin-m 20]

Rasterises a raftsim.cartesian_state_atlas.v1 (bed, h, u, v tiles; origin_m = the
first cell centre in the runtime frame, rows north, columns east) onto one grid,
places every wet cell in the evidence grid's station/lateral frame and reports,
per station bin: the photographed whitewater share of the wet cells (evidence
foam mask), the share over Froude 0.8, the peak Froude, and the game's breaking
cells (Froude <= 0.94 with a wet cell 4 or 6 m upstream, against the local flow
direction as the Cartesian runtime looks, at Froude >= 1.12 and intensity >= 0.08).
With --catalogue the same numbers per feature footprint (station window 10 m
above to 30 m below, lateral window width + 5 m, catalogue in the evidence frame).
"""
import argparse
import json
from pathlib import Path

import numpy as np


def load_atlas(atlas_dir):
    """An exported atlas folder, or a raw cook folder (last complete frame + its package's tile beds)."""
    atlas_dir = Path(atlas_dir)
    if (atlas_dir / 'input_manifest.json').exists():
        pm = json.loads((atlas_dir / 'input_manifest.json').read_text())
        root = Path((atlas_dir / 'input_manifest_path.txt').read_text().strip()).parent
        frame = sorted(q for q in atlas_dir.glob('frame_*') if (q / 'complete.json').exists())[-1]
        T = int(pm['grid']['tile_cells']); D = float(pm['grid']['cell_m'])
        ax, ay = pm['grid']['lattice_offset_utm_m']; ox, oy = pm['world_origin_utm35s_m']
        arr = {k: np.load(frame / f'{k}.npy') for k in ('h', 'u', 'v')}
        arr['bed'] = np.concatenate([np.load(root / n / 'bed.npy') for n in pm['packages']])
        org = np.array([[ax + i * D * T + 0.5 * D - ox, ay + j * D * T + 0.5 * D - oy] for i, j in pm['tile_indices']])
        m = None
    else:
        m = json.loads((atlas_dir / 'manifest.json').read_text())
        T = int(m['tile_shape'][0]); D = float(m['grid_spacing_m'])
        arr = {k: np.load(atlas_dir / f'{k}.npy') for k in ('bed', 'h', 'u', 'v')}
        org = np.array([t['origin_m'] for t in m['tiles']], float)
    x0, y0 = org[:, 0].min(), org[:, 1].min()
    nx = int(round((org[:, 0].max() - x0) / D)) + T; ny = int(round((org[:, 1].max() - y0) / D)) + T
    g = {k: np.full((ny, nx), np.nan) for k in arr}
    for k, (ox, oy) in enumerate(org):
        c = int(round((ox - x0) / D)); r = int(round((oy - y0) / D))
        for key in arr:
            g[key][r:r + T, c:c + T] = arr[key][k * T:(k + 1) * T]
    return g, x0, y0, D


def breaking_mask(h, u, v, D):
    wet = np.nan_to_num(h) > 0.05
    speed = np.hypot(np.nan_to_num(u), np.nan_to_num(v))
    fr = np.where(wet, speed / np.sqrt(9.81 * np.maximum(np.nan_to_num(h), 0.05)), 0.0)
    ny, nx = h.shape
    rr, cc = np.nonzero(wet & (fr <= 0.94))
    dx = np.nan_to_num(u)[rr, cc] / np.maximum(speed[rr, cc], 1e-6)
    dy = np.nan_to_num(v)[rr, cc] / np.maximum(speed[rr, cc], 1e-6)
    best = np.zeros(len(rr))
    for k in (2, 3):                                   # 4 and 6 m upstream on the 2 m grid
        ur = np.clip(np.round(rr - k * dy).astype(int), 0, ny - 1)
        uc = np.clip(np.round(cc - k * dx).astype(int), 0, nx - 1)
        best = np.maximum(best, np.where(wet[ur, uc], fr[ur, uc], 0.0))
    inten = np.clip((best - 0.85) / 1.5, 0, 1) * np.clip(np.nan_to_num(h)[rr, cc] / 0.6, 0.3, 1.0)
    out = np.zeros_like(wet)
    ok = (best >= 1.12) & (inten >= 0.08)
    out[rr[ok], cc[ok]] = True
    return out, fr, wet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('atlas', type=Path)
    ap.add_argument('evidence', type=Path)
    ap.add_argument('--origin', type=float, nargs=2, required=True, help='runtime frame origin (E, N) in the evidence CRS')
    ap.add_argument('--catalogue', type=Path)
    ap.add_argument('--bin-m', type=float, default=20.0)
    ap.add_argument('--range', type=float, nargs=2, default=None)
    args = ap.parse_args()
    g, x0, y0, D = load_atlas(args.atlas)
    brk, fr, wet = breaking_mask(g['h'], g['u'], g['v'], D)
    ev = np.load(args.evidence / 'evidence_grid.npz')
    em = json.loads((args.evidence / 'manifest.json').read_text())
    ex0, ey_top = float(em['grid']['x0']), float(em['grid']['y_top'])
    ny, nx = wet.shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    E = args.origin[0] + x0 + xx * D; N = args.origin[1] + y0 + yy * D
    er = np.clip(np.floor(ey_top - N).astype(int), 0, ev['station'].shape[0] - 1)
    ec = np.clip(np.floor(E - ex0).astype(int), 0, ev['station'].shape[1] - 1)
    st = ev['station'][er, ec].astype(float); lat = ev['lateral'][er, ec].astype(float); foam = ev['foam'][er, ec]
    lo, hi = args.range or (np.nanmin(st[wet]), np.nanmax(st[wet]))
    for s0 in np.arange(np.floor(lo / args.bin_m) * args.bin_m, hi, args.bin_m):
        m = wet & (st >= s0) & (st < s0 + args.bin_m)
        if m.sum() < 5:
            continue
        pl = np.nanmean(np.where(m & foam, lat, np.nan)) if (m & foam).any() else float('nan')
        print('%5.0f wet %4d photo %.2f (lat %6.1f) Fr>0.8 %.2f peakFr %.2f breaking %3d depth %.1f' % (
            s0, m.sum(), foam[m].mean(), pl, (fr[m] > 0.8).mean(), fr[m].max(), brk[m].sum(), np.median(g['h'][m])))
    if args.catalogue:
        cat = json.loads(args.catalogue.read_text())
        for f in cat['features']:
            s = f['station_m']; L = float(f.get('length_m', 0) or 0); half = 0.5 * float(f.get('width_m', 10)) + 5
            m = wet & (st >= s - 10) & (st <= s + L + 30) & (np.abs(lat - f['lateral_m']) <= half)
            if m.sum() < 3:
                print(f['id'], 'no wet cells'); continue
            print('%-32s st %5.0f wet %4d photo %.2f Fr>0.8 %.2f peakFr %.2f breaking %3d' % (
                f['id'], s, m.sum(), foam[m].mean(), (fr[m] > 0.8).mean(), fr[m].max(), brk[m].sum()))


if __name__ == '__main__':
    main()
