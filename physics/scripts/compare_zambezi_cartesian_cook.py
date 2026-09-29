"""Compare a Zambezi Cartesian cook with its evidence grid (numpy only).

Inputs: the evidence folder (build_zambezi_evidence_grid.py), the cook
package folder (prepare_zambezi_cartesian_cook.py) and the cook output
(raftsim_cartesian_cook). Each cooked cell is given the evidence station of
the nearest midline point, so the comparison is along the river whatever the
grid orientation.

Reports (compare.json):
- measured anchors (GLO-30 edited water surface, about +-2 m): cooked median
  surface within 10 m of each anchor station minus the anchor;
- reference surface error per 2 m station bin (partly inferred between
  anchors);
- wet extent: cooked wet (h > 0.05 m) against the evidence river inside the
  reach, as IoU at the cook's cell size;
- discharge: the exact exterior face fluxes the cook logs (inflow faces and
  the outflow face);
- settling: p95 |dh| over wet cells between the last two frames;
- depth, speed and Froude statistics; whitewater share against Froude > 0.8
  per 250 m.
profiles.npz carries station, evidence_station, cook_median and ws_reference
for calibrate_river_bed.py.
"""
import argparse
import json
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path)
    ap.add_argument('packages', type=Path)
    ap.add_argument('cook', type=Path)
    ap.add_argument('out', type=Path)
    args = ap.parse_args()
    out = args.out; out.mkdir(parents=True, exist_ok=True)
    evm = json.loads((args.evidence / 'manifest.json').read_text())
    X0, Y1, NX, NY = evm['grid']['x0'], evm['grid']['y_top'], evm['grid']['nx'], evm['grid']['ny']
    s_in, s_out = evm['statistics']['reach_station_m']
    g = np.load(args.evidence / 'evidence_grid.npz')
    river1, st1, white1 = g['river'], g['station'], g['white_fraction']
    prof = json.loads((args.evidence / 'profile.json').read_text())
    cl = np.array(json.loads((args.evidence / 'centreline.json').read_text())['points_xy_station'])
    pm = json.loads((args.packages / 'manifest.json').read_text())
    D, T = pm['grid']['cell_m'], pm['grid']['tile_cells']
    ax, ay = pm['grid']['lattice_offset_utm_m']
    datum = pm['vertical_datum_m']
    tiles = [tuple(t) for t in pm['tile_indices']]
    frames = sorted(p for p in args.cook.glob('frame_*') if (p / 'complete.json').exists())
    last, prev = frames[-1], frames[-2]
    h = np.load(last / 'h.npy'); u = np.load(last / 'u.npy'); v = np.load(last / 'v.npy'); h0 = np.load(prev / 'h.npy')
    beds = np.concatenate([np.load(args.packages / n / 'bed.npy') for n in pm['packages']])
    # cell centres (UTM) of every tile cell, rows from the south
    cx = np.concatenate([np.broadcast_to(ax + i * D * T + (np.arange(T) + 0.5) * D, (T, T)) for (i, j) in tiles])
    cy = np.concatenate([np.broadcast_to((ay + j * D * T + (np.arange(T) + 0.5) * D)[:, None], (T, T)) for (i, j) in tiles])
    wet = h > 0.05
    # evidence station of the nearest midline point for wet cells
    st = np.full(h.shape, np.nan)
    wi = np.nonzero(wet)
    ex, ey = cx[wi], cy[wi]
    best = np.full(len(ex), np.inf); bi = np.zeros(len(ex), int)
    for j0 in range(0, len(cl), 256):
        j1 = min(len(cl), j0 + 256)
        d2 = (ex[:, None] - cl[None, j0:j1, 0]) ** 2 + (ey[:, None] - cl[None, j0:j1, 1]) ** 2
        jj = np.argmin(d2, 1); dd = d2[np.arange(len(ex)), jj]
        m = dd < best; best[m] = dd[m]; bi[m] = j0 + jj[m]
    st[wi] = cl[bi, 2]
    eta = beds + h + datum
    # 2 m station bins
    bins = np.arange(np.floor(s_in), np.ceil(s_out) + 2.0, 2.0)
    sw = st[wet]; ew = eta[wet]
    idx = np.digitize(sw, bins) - 1
    cook_med = np.full(len(bins), np.nan)
    order = np.argsort(idx)
    split = np.searchsorted(idx[order], np.arange(len(bins) + 1))
    for k in range(len(bins)):
        vals = ew[order][split[k]:split[k + 1]]
        if len(vals) >= 3:
            cook_med[k] = np.median(vals)
    wsr = np.interp(bins, prof['station_center_m'], prof['ws_reference_m'])
    err = cook_med - wsr
    anchors = []
    for a in prof['anchors']:
        s_ = a['station_m']
        if not (s_in <= s_ <= s_out):
            continue
        sel = wet & (np.abs(st - s_) <= 10.0)
        cooked = float(np.median(eta[sel])) if sel.sum() >= 3 else None
        anchors.append(dict(evidence_station_m=s_, elevation_m=a['elevation_m'], cooked_m=cooked,
                            error_m=None if cooked is None else cooked - a['elevation_m']))
    # wet IoU at the cook resolution against the evidence river inside the reach
    c1 = np.floor(cx - X0).astype(int); r1 = np.floor(Y1 - cy).astype(int)
    ok = (c1 >= 0) & (c1 < NX) & (r1 >= 0) & (r1 < NY)
    ev_wet = np.zeros(h.shape, bool); ev_st = np.full(h.shape, np.nan)
    ev_wet[ok] = river1[r1[ok], c1[ok]]; ev_st[ok] = st1[r1[ok], c1[ok]]
    in_reach_ev = ev_wet & np.isfinite(ev_st) & (ev_st >= s_in) & (ev_st <= s_out)
    in_reach_ck = wet & np.isfinite(st) & (st >= s_in) & (st <= s_out)
    inter = (in_reach_ev & in_reach_ck).sum(); union = (in_reach_ev | in_reach_ck).sum()
    # exterior face fluxes from the cook log
    lines = [json.loads(l) for l in (args.cook / 'progress.jsonl').read_text().splitlines() if l.strip()]
    lastl = lines[-1]
    roles = [p_['role'] for p_ in pm['boundary_probes']]
    fl = lastl['exterior_fluxes']
    q_in = float(sum(f for f, r in zip(fl, roles) if r == 'upstream')); q_out = float(sum(-f for f, r in zip(fl, roles) if r == 'downstream'))
    speed = np.hypot(u, v)
    hs = np.maximum(h, 0.05)
    fr = np.where(wet, speed / np.sqrt(9.81 * hs), 0.0)
    dh = np.abs(h - h0)[wet]
    # whitewater vs Froude per 250 m
    wf = np.zeros(h.shape); wf[ok] = white1[r1[ok], c1[ok]]
    ww = []
    for b0 in np.arange(np.floor(s_in / 250) * 250, s_out, 250.0):
        sel = in_reach_ck & (st >= b0) & (st < b0 + 250)
        if sel.sum() < 20:
            continue
        ww.append(dict(station_m=float(b0), evidence_whitewater_share=float((wf[sel] >= 0.25).mean()),
                       cooked_fr_gt_0p8_share=float((fr[sel] > 0.8).mean())))
    valid_err = err[np.isfinite(err)]
    report = dict(frame=last.name, time_seconds=lastl['time_seconds'], discharge_target_m3s=pm['target_discharge_m3s'],
                  measured_anchors=anchors,
                  anchor_error_m_max_abs=float(max(abs(a['error_m']) for a in anchors if a['error_m'] is not None)),
                  reference_surface_error_m=dict(median=float(np.median(valid_err)), median_abs=float(np.median(np.abs(valid_err))),
                                                 p90_abs=float(np.percentile(np.abs(valid_err), 90)), bins_with_water=int(len(valid_err))),
                  wet_iou=float(inter / max(union, 1)), false_wet_cells=int((in_reach_ck & ~in_reach_ev).sum()),
                  missed_wet_cells=int((in_reach_ev & ~in_reach_ck).sum()),
                  discharge_m3s=dict(inflow_faces=q_in, outflow_face=q_out,
                                     method='exact exterior face mass fluxes logged by raftsim_cartesian_cook'),
                  convergence=dict(p95_abs_dh_m=float(np.percentile(dh, 95)), max_abs_dh_m=float(dh.max()), compared=[prev.name, last.name]),
                  conservation_residual_m3=lastl['conservation_residual_m3'],
                  froude=dict(p50=float(np.median(fr[wet])), p95=float(np.percentile(fr[wet], 95)), share_gt_1=float((fr[wet] > 1).mean())),
                  speed_m_per_s=dict(p50=float(np.median(speed[wet])), p95=float(np.percentile(speed[wet], 95)), max=float(speed[wet].max())),
                  depth_m=dict(p50=float(np.median(h[wet])), p95=float(np.percentile(h[wet], 95)), max=float(h.max())),
                  whitewater_vs_froude_by_250m=ww)
    (out / 'compare.json').write_text(json.dumps(report, indent=1) + '\n')
    np.savez(out / 'profiles.npz', station=bins, evidence_station=bins, cook_median=cook_med, ws_reference=wsr)
    print(json.dumps({k: report[k] for k in ('anchor_error_m_max_abs', 'reference_surface_error_m', 'wet_iou', 'discharge_m3s',
                                             'convergence', 'froude', 'depth_m')}, indent=1))


if __name__ == '__main__':
    main()
