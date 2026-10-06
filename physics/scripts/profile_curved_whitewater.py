"""Photographed vs cooked whitewater along a committed curved-map export (numpy only).

    profile_curved_whitewater.py <scenario_export_dir> [--bin-m 40] [--catalogue cat.json]

Reads cooked_flow_fields/manifest.json (h, u, v, wet_mask of its band) and the
band's observed_whitewater layer (RSBF, photographed whitewater fraction on the
cooked grid) and prints per station bin: the photographed whitewater share of
wet cells and its mean lateral (river left +), the share over Froude 0.8, the
peak Froude, the game's breaking cells (ARaftSimWaterSurfaceActor rule:
Froude <= 0.94 with a wet cell 4 or 6 m upstream at Froude >= 1.12 and
intensity >= 0.08) and the median depth. With --catalogue (scenario frame) the
catalogued features falling in each bin are listed beside it.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from augment_observed_whitewater import read_rsbf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('export', type=Path)
    ap.add_argument('--bin-m', type=float, default=40.0)
    ap.add_argument('--catalogue', type=Path)
    args = ap.parse_args()
    cooked = args.export / 'cooked_flow_fields'
    m = json.loads((cooked / 'manifest.json').read_text()); (b,) = m['bands']; g = m['grid']
    A = {k: np.load(cooked / b['arrays'][k]['file']) for k in ('h', 'u', 'v', 'wet_mask')}
    h = A['h'].astype(float); wet = A['wet_mask'].astype(bool) & (h > 0.05)
    fr = np.where(wet, np.hypot(A['u'], A['v']) / np.sqrt(9.81 * np.maximum(h, 0.05)), 0.0)
    ny, nx = h.shape; d = g['dx_m']; lat = g['origin_y_m'] + d * np.arange(ny)
    st = g['origin_x_m'] + d * np.arange(nx)
    brk = np.zeros_like(wet)
    for k in (2, 3):
        up = np.zeros_like(fr); up[:, k:] = np.where(wet[:, :-k], fr[:, :-k], 0.0)
        cand = wet & (fr <= 0.94) & (up >= 1.12) & (np.clip((up - 0.85) / 1.5, 0, 1) * np.clip(h / 0.6, 0.3, 1) >= 0.08)
        brk |= cand
    photo = None
    if 'observed_whitewater' in b:
        f = read_rsbf(cooked / b['observed_whitewater']['file'])
        photo = f['energy'].T                    # (lateral, station)
    cat = json.loads(args.catalogue.read_text(encoding='utf-8')) if args.catalogue else None
    for s0 in np.arange(0, st[-1], args.bin_m):
        cols = (st >= s0) & (st < s0 + args.bin_m)
        w = wet[:, cols]
        if w.sum() < 5:
            continue
        L = np.broadcast_to(lat[:, None], w.shape)
        ph = photo[:, cols] if photo is not None else np.zeros(w.shape)
        pl = float((ph * L)[w].sum() / max(ph[w].sum(), 1e-9)) if ph[w].sum() > 0.5 else float('nan')
        names = ''
        if cat:
            names = ' '.join(q['id'] for q in cat.get('features', []) if s0 <= q['station_m'] < s0 + args.bin_m)
        print('%5.0f photo %.2f (lat %6.1f) Fr>0.8 %.2f peakFr %.2f breaking %3d depth %.1f %s' % (
            s0, ph[w].mean(), pl, (fr[:, cols][w] > 0.8).mean(), fr[:, cols][w].max(), brk[:, cols].sum(),
            np.median(h[:, cols][w]), names))


if __name__ == '__main__':
    main()
