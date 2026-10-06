"""Score cooked-field whitewater indicators against the 2021 Hance imagery foam (numpy only).

The shipped runtime foam ramps on the local Froude number (onset 0.6, ramp
0.5) and the render-only baseline energy mixes speed and Froude; both are
broad, so the rapid renders as lace instead of the imagery's massed white
crests over dark tongues. This audit asks which cooked-field quantity best
predicts WHERE the photographed whitewater is, on the 2 m curvilinear grid.

For every indicator the threshold is set so the indicator covers the same
area as the imagery foam inside the imagery river (matched area), then:
IoU, precision (= recall at matched area), ROC AUC, and the correlation of
10 m station shares. Advected variants carry an indicator downstream with an
exponential decay (aerated water persists below its source).

Inputs: evidence grid (foam mask), scenario (reference.npz, coordinate grid),
and a raftsim_water_solver run folder (last frame). Writes JSON and a PNG map
(rows = lateral, columns = station; white = imagery foam, orange = indicator,
yellow = both).
"""
import argparse
import json
from pathlib import Path

import numpy as np

from png_numpy import write_png


def read_frame(path, ny, nx):
    a = np.loadtxt(path, delimiter=',', skiprows=1)
    names = 'row,col,x,y,h,eta,u,v,hu,hv,wet,normal_x,normal_y,normal_z,froude'.split(',')
    return {n: a[:, k].reshape(ny, nx) for k, n in enumerate(names)}


def advect(src, u, decay_m, d, passes=1):
    """Carry src downstream along +station (columns) with exponential decay; u>0 only."""
    out = src.copy()
    k = np.exp(-d / decay_m)
    for _ in range(passes):
        acc = np.zeros(src.shape[0])
        res = np.empty_like(src)
        for j in range(src.shape[1]):
            acc = np.maximum(src[:, j], acc * k * (u[:, j] > 0.2))
            res[:, j] = acc
        out = res
    return out


def blur_lateral(a, n=1):
    for _ in range(n):
        p = np.pad(a, ((1, 1), (0, 0)), mode='edge')
        a = 0.25 * p[:-2] + 0.5 * p[1:-1] + 0.25 * p[2:]
    return a


def blur_station(a, n=1):
    for _ in range(n):
        p = np.pad(a, ((0, 0), (1, 1)), mode='edge')
        a = 0.25 * p[:, :-2] + 0.5 * p[:, 1:-1] + 0.25 * p[:, 2:]
    return a


def auc(score, label):
    order = np.argsort(score)
    ranks = np.empty(len(score)); ranks[order] = np.arange(1, len(score) + 1)
    npos = label.sum(); nneg = len(label) - npos
    return float((ranks[label].sum() - npos * (npos + 1) / 2) / max(npos * nneg, 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path)
    ap.add_argument('scenario_root', type=Path)
    ap.add_argument('run', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--station-range', type=float, nargs=2, default=[650.0, 1500.0])
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    sc = json.loads((args.scenario_root / 'scenario/scenario.json').read_text())
    ny, nx, d = sc['grid']['ny'], sc['grid']['nx'], sc['grid']['dx']
    frames = sorted((args.run / 'frames').glob('frame_*.csv'))
    f = read_frame(frames[-1], ny, nx)
    ref = np.load(args.scenario_root / 'reference.npz')
    evg = np.load(args.evidence / 'evidence_grid.npz')
    wx, wy = ref['world_x'], ref['world_y']
    cc = np.clip(np.floor(wx - 211300.0).astype(int), 0, evg['foam'].shape[1] - 1)
    rr = np.clip(np.floor(560300.0 - wy).astype(int), 0, evg['foam'].shape[0] - 1)
    river = ref['river']
    foam = evg['foam'][rr, cc] & river
    station = ref['station']
    h = np.where(f['wet'] > 0.5, f['h'], 0.0)
    wet = h > 0.05
    u, v, eta = f['u'], f['v'], f['eta']
    speed = np.hypot(u, v)
    fr = np.where(wet, speed / np.sqrt(9.81 * np.maximum(h, 0.05)), 0.0)
    energy_head = eta + speed ** 2 / (2 * 9.81)
    ds_u = np.gradient(u, d, axis=1)
    dl_v = np.gradient(v, d, axis=0)
    div = ds_u + dl_v
    gy, gx = np.gradient(eta, d)
    slope = np.hypot(gx, gy)
    dE = -np.gradient(energy_head, d, axis=1)          # head loss per metre along flow
    power = np.clip(dE, 0, None) * np.clip(h * u, 0, None) * 9.81 * 1000.0  # W per m2 (dissipation)
    fr_drop = np.clip(np.roll(fr, 1, axis=1) - fr, 0, None)
    lap = (np.roll(eta, 1, 0) + np.roll(eta, -1, 0) + np.roll(eta, 1, 1) + np.roll(eta, -1, 1) - 4 * eta) / d ** 2
    base_energy = np.clip(0.6 * np.clip((speed - 0.5) / 2.5, 0, 1) + 0.4 * np.clip((fr - 0.5) / 0.5, 0, 1), 0, 1)
    shipped_foam = np.clip((fr - 0.6) / 0.5, 0, 1)
    ind = dict(froude=fr, speed=speed, baseline_energy=base_energy, shipped_live_foam=shipped_foam,
               convergence=np.clip(-div, 0, None), decel=np.clip(-ds_u, 0, None), surface_slope=slope,
               dissipation_power=power, froude_drop=fr_drop, crest_curvature=np.clip(-lap, 0, None),
               speed_x_slope=speed * slope, froude_x_slope=fr * slope)
    for name in ('dissipation_power', 'convergence', 'surface_slope', 'froude_drop', 'speed_x_slope', 'froude_x_slope'):
        for L in (6.0, 12.0, 25.0):
            ind[f'{name}_adv{int(L)}m'] = advect(blur_lateral(ind[name]), u, L, d)
    for name in ('dissipation_power_adv12m', 'surface_slope_adv12m'):
        ind[f'{name}_x_speed'] = ind[name] * np.clip(speed / 2.5, 0, 1)
    region = river & wet & (station >= args.station_range[0])[None] & (station <= args.station_range[1])[None]
    label = foam[region]
    share = label.mean()
    res = {}
    kern = np.ones(5) / 5
    for name, a in ind.items():
        s = a[region]
        thr = np.quantile(s, 1 - share)
        pred = s > thr
        tp = (pred & label).sum()
        iou = tp / max((pred | label).sum(), 1)
        full = np.zeros_like(foam); full[region] = pred
        sh_pred = np.convolve(full.sum(0) / np.maximum(region.sum(0), 1), kern, 'same')
        sh_true = np.convolve((foam & region).sum(0) / np.maximum(region.sum(0), 1), kern, 'same')
        m = region.sum(0) > 5
        corr = float(np.corrcoef(sh_pred[m], sh_true[m])[0, 1]) if m.sum() > 10 else float('nan')
        res[name] = dict(iou=float(iou), precision=float(tp / max(pred.sum(), 1)), auc=auc(s, label),
                         station_share_corr=corr, threshold=float(thr))
    ranked = sorted(res.items(), key=lambda kv: -kv[1]['iou'])
    report = dict(schema='raftsim.colorado.hance_whitewater_indicators.v1', run=str(frames[-1]),
                  station_range_m=args.station_range, region_cells=int(region.sum()), imagery_foam_share=float(share),
                  method='matched-area threshold inside imagery river & cooked wet', indicators=dict(ranked))
    (args.out / 'indicators.json').write_text(json.dumps(report, indent=2) + '\n')
    for name, r in ranked:
        print(f"{name:34s} IoU {r['iou']:.3f}  prec {r['precision']:.3f}  AUC {r['auc']:.3f}  share-corr {r['station_share_corr']:.3f}")
    best = ranked[0][0]
    j0, j1 = np.searchsorted(station, args.station_range)
    for name in (best, 'shipped_live_foam', 'froude'):
        a = ind[name]; s = a[region]; thr = np.quantile(s, 1 - share)
        pred = np.zeros_like(foam); pred[region] = s > thr
        img = np.zeros((ny, nx, 3), np.uint8)
        img[wet] = (30, 60, 90); img[foam] = (245, 245, 245); img[pred] = (230, 110, 40); img[foam & pred] = (250, 210, 60)
        crop = img[::-1, j0:j1]
        write_png(args.out / f'map_{name}.png', np.repeat(np.repeat(crop, 3, 0), 2, 1))


if __name__ == '__main__':
    main()
