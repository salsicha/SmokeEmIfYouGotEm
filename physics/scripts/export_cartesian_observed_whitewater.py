"""Observed whitewater for a Cartesian map, as a render-only raster (numpy only).

    export_cartesian_observed_whitewater.py <evidence_dir> <region_dir> --band BAND --origin E N
                                            [--catalogue cat.json] [--cell-m 4]

Appearance evidence, never hydraulics (as export_hance_observed_whitewater.py for
curved maps). For every raster cell over the region's grid, the whitewater
fraction is the larger of:
- the photographed whitewater: the share of the evidence grid's foam mask
  (Sentinel-2 bright neutral water at the low-water dates, 1 m) in the cell;
- the catalogue's expected whitewater (observed rapids that 10 m pixels do not
  resolve, from outfitter, guidebook, video and sub-metre imagery observations):
  broken water across each rapid span by class, a white core behind every hole
  and pour-over (twice its width downstream), crest caps along wave trains, a
  band along laterals and diagonals.
The result is written as RSBF v1 (the layout LoadObservedWhitewaterFieldFromFile
reads) in the Cartesian water frame: rows along x (east), columns along y
(north), so the runtime samples it at the carrier's Cartesian coordinates. A
sidecar JSON records the method, inputs and hashes, and a preview PNG is saved
beside it.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

from png_numpy import write_png

CLASS_BROKEN = {'V': 0.35, 'IV-V': 0.3, 'IV': 0.25, 'III-IV': 0.2, 'III': 0.15, 'II-III': 0.1, 'II': 0.06}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def broken_share(rapid_class):
    key = rapid_class.split(' ')[0]
    return CLASS_BROKEN.get(key, 0.1)


def _ramp(x, width):
    """0 at x <= 0 rising smoothly to 1 at x >= width (a feathered edge, not a cut)."""
    t = np.clip(np.asarray(x, float) / max(width, 1e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def catalogue_whitewater(st, lat, wet, cat):
    """Expected whitewater fraction from an observed-rapid catalogue.

    Every footprint is feathered: a rapid's broken water fades in and out over
    20 m of station (at most a third of its length), and hole, wave, lateral and
    garden footprints fade over their outer quarter width, so the layer shows no
    straight cut lines across the river."""
    f = np.zeros(st.shape)
    for r in cat.get('rapids', []):
        a0 = r['station_m']; a1 = a0 + r['length_m']
        edge = min(20.0, r['length_m'] / 3.0)
        w = broken_share(r.get('rapid_class', 'III')) * _ramp(st - a0, edge) * _ramp(a1 - st, edge)
        f = np.where(wet, np.maximum(f, w), f)
    for q in cat.get('features', []):
        s, l, w = q['station_m'], q['lateral_m'], float(q.get('width_m', 10.0))
        t = q['type']
        v = lat - l
        across = _ramp(0.5 * w - np.abs(v), 0.25 * w)
        if t in ('ledge_hole', 'pour_over'):
            # the white pile of the hole: from the crest to two widths downstream
            u = st - s
            val = 0.85 * np.clip(1.0 - u / (2.0 * w), 0.3, 1.0) * _ramp(u + 1.0, 2.0) * _ramp(2.0 * w - u, 0.5 * w)
            f = np.where(wet, np.maximum(f, val * across), f)
        elif t == 'wave_train':
            lam = float(q.get('wavelength_m', 8.0)); n = int(q.get('waves', 4))
            u = st - s
            caps = np.clip(np.cos(2 * np.pi * u / lam), 0, 1) ** 3
            val = 0.6 * caps * _ramp(u, 0.5 * lam) * _ramp(n * lam - u, lam)
            f = np.where(wet, np.maximum(f, val * across), f)
        elif t in ('lateral', 'diagonal'):
            ang = np.radians(q.get('angle_deg', 30.0))
            u = st - (s + v * np.tan(ang))
            val = 0.6 * _ramp(3.0 - np.abs(u), 2.0)
            f = np.where(wet, np.maximum(f, val * across), f)
        elif t in ('rock_garden', 'whitewater_boulders'):
            u = st - s; length = float(q.get('length_m', 30.0))
            val = 0.3 * _ramp(u, 0.25 * length) * _ramp(length - u, 0.25 * length)
            f = np.where(wet, np.maximum(f, val * across), f)
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('evidence', type=Path)
    ap.add_argument('region', type=Path)
    ap.add_argument('--band', required=True)
    ap.add_argument('--origin', type=float, nargs=2, required=True, help='runtime frame origin (E, N)')
    ap.add_argument('--catalogue', type=Path)
    ap.add_argument('--cell-m', type=float, default=4.0)
    ap.add_argument('--preview', type=Path)
    args = ap.parse_args()
    rm = json.loads((args.region / 'manifest.json').read_text())
    g = rm['grid']
    x0 = g['origin_x_m'] - 0.5 * g['dx_m']; y0 = g['origin_y_m'] - 0.5 * g['dy_m']
    X = g['nx'] * g['dx_m']; Y = g['ny'] * g['dy_m']
    c = args.cell_m
    xs = x0 + (np.arange(int(np.ceil(X / c))) + 0.5) * c
    ys = y0 + (np.arange(int(np.ceil(Y / c))) + 0.5) * c
    assert len(ys) <= 512, 'too many columns for the RSBF reader (512): use a coarser --cell-m'
    ev = np.load(args.evidence / 'evidence_grid.npz')
    em = json.loads((args.evidence / 'manifest.json').read_text())
    ex0, ey_top = float(em['grid']['x0']), float(em['grid']['y_top'])
    H, W = ev['station'].shape
    # sub-sample each raster cell at 1 m (the evidence resolution)
    k = int(round(c))
    sub = (np.arange(k) + 0.5) - 0.5 * k
    XX = (xs[:, None, None, None] + sub[None, None, :, None])
    YY = (ys[None, :, None, None] + sub[None, None, None, :])
    E = args.origin[0] + np.broadcast_to(XX, (len(xs), len(ys), k, k))
    N = args.origin[1] + np.broadcast_to(YY, (len(xs), len(ys), k, k))
    r = np.clip(np.floor(ey_top - N).astype(int), 0, H - 1); cc = np.clip(np.floor(E - ex0).astype(int), 0, W - 1)
    inside = (ey_top - N >= 0) & (ey_top - N < H) & (E - ex0 >= 0) & (E - ex0 < W)
    wet = (ev['river'] | ev['channel'])[r, cc] & inside
    photo = (ev['foam'][r, cc] & wet).mean(axis=(2, 3))
    frac = photo.copy()
    cat_note = None
    if args.catalogue:
        cat = json.loads(args.catalogue.read_text(encoding='utf-8'))
        assert cat.get('station_frame') == 'evidence'
        st = ev['station'][r, cc].astype(float); lat = ev['lateral'][r, cc].astype(float)
        ok = wet & np.isfinite(st) & np.isfinite(lat)
        cw = catalogue_whitewater(np.where(ok, st, np.nan), np.where(ok, lat, np.nan), ok, cat).mean(axis=(2, 3))
        frac = np.maximum(frac, cw)
        cat_note = dict(path=args.catalogue.resolve().relative_to(Path(__file__).resolve().parents[2]).as_posix(), sha256=sha(args.catalogue), rapids=len(cat.get('rapids', [])),
                        features=len(cat.get('features', [])))
    wet_cell = wet.mean(axis=(2, 3)) > 0.25
    ws = np.where(np.isfinite(ev['ws'][r, cc]), ev['ws'][r, cc], 0.0).mean(axis=(2, 3))
    out = args.region / f'observed_whitewater_{args.band}.bin'
    with open(out, 'wb') as fb:
        fb.write(struct.pack('<IIiiff', 0x52534246, 1, len(ys), len(xs), float(ys[0]), float(c)))
        for arr, fmt in ((xs.astype(np.float32), '<f4'), (ws.astype(np.float32), '<f4'),
                         (frac.astype(np.float32), '<f4'), (wet_cell.astype(np.uint8), 'u1')):
            flat = np.ascontiguousarray(arr).astype(fmt).ravel()
            fb.write(struct.pack('<i', flat.size)); fb.write(flat.tobytes())
    side = dict(schema='raftsim.cartesian_observed_whitewater.v1', generator='physics/scripts/export_cartesian_observed_whitewater.py',
                file=out.name, sha256=sha(out), layout='RSBF v1: rows = x (east) cell centres, columns = y (north) from lateral origin '
                'at cell spacing; energy = whitewater fraction 0-1', frame='runtime Cartesian water frame (origin E/N %.1f %.1f)' % tuple(args.origin),
                cell_m=c, rows=len(xs), columns=len(ys),
                photographed=dict(source='evidence foam mask (Sentinel-2 whitewater at the low-water dates)',
                                  evidence_grid_sha256=sha(args.evidence / 'evidence_grid.npz'), cells_with_whitewater=int((photo > 0.05).sum())),
                catalogue=cat_note, cells_with_whitewater=int((frac > 0.05).sum()),
                render_only=True, note='appearance evidence: floors the displayed foam; never reaches forces, contact or gameplay')
    (args.region / f'observed_whitewater_{args.band}.json').write_text(json.dumps(side, indent=1) + '\n')
    if args.preview:
        img = np.zeros((len(ys), len(xs), 3), np.uint8)
        img[..., 2] = np.where(wet_cell.T, 120, 0)
        v = np.clip(frac.T, 0, 1)
        img = (img * (1 - v[..., None]) + 255 * v[..., None]).astype(np.uint8)
        write_png(args.preview, img[::-1])
    print(json.dumps({k: side[k] for k in ('rows', 'columns', 'cells_with_whitewater')}), side['photographed']['cells_with_whitewater'])


if __name__ == '__main__':
    main()
