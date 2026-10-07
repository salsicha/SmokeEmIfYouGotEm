"""Compare a curvilinear river cook with its evidence (numpy only).

For scenarios from build_curvilinear_river_scenario.py. Uses the last saved
frame unless --frame is given. Reports:
- reference anchors (evidence profile.json `anchors`): cooked median surface
  against each reference elevation, retaining whether the reference is inferred;
- reference surface (the evidence ws_reference, partly inferred): cooked
  median over wet channel cells per 10 m bin;
- wet extent: cooked wet (h > 0.05 m) against the evidence wetted mask (IoU);
- discharge through every station section: the solver's exact face mass
  flux (solver_face_discharge.py; the cell-centre h*u sum is kept as a
  diagnostic, it overstates transport on steep wet/dry reaches); convergence
  between the last two frames; Froude / speed distributions; cooked Fr > 0.8 share against the
  evidence whitewater share per 250 m.
Writes compare.json, profiles.npz (cook_median, ws_reference per station) and
maps (depth/speed, wet agreement, profile chart).
"""
import argparse
import json
from pathlib import Path

import numpy as np

from png_numpy import write_png
from solver_face_discharge import face_discharge

ROOT = Path(__file__).resolve().parents[2]


def anchor_evidence_kind(profile):
    kind = profile.get('anchor_evidence_kind')
    inferred = str(profile.get('ws_reference_method', '')).startswith('inferred_')
    if kind == 'measured' and inferred:
        raise ValueError('Inferred surface method contradicts measured-anchor claim')
    if kind in ('measured', 'inferred_dem_surface_reference'):
        return kind
    if inferred:
        return 'inferred_dem_surface_reference'
    return 'unclassified_reference_not_verified_measurement'


def read_frame(path, ny, nx):
    a = np.loadtxt(path, delimiter=',', skiprows=1)
    assert a.shape[0] == ny * nx
    names = 'row,col,x,y,h,eta,u,v,hu,hv,wet,normal_x,normal_y,normal_z,froude'.split(',')
    return {n: a[:, k].reshape(ny, nx) for k, n in enumerate(names)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path)
    ap.add_argument('scenario_root', type=Path)
    ap.add_argument('run', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--frame', type=int, default=-1)
    ap.add_argument('--solver-binary', type=Path, default=ROOT / 'tmp/hance-solver-build/raftsim_water_solver.exe')
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sc = json.loads((args.scenario_root / 'scenario/scenario.json').read_text())
    ny, nx, d = sc['grid']['ny'], sc['grid']['nx'], sc['grid']['dx']
    Q = sc['metadata']['provenance']['target_discharge_m3s']
    ref = np.load(args.scenario_root / 'reference.npz')
    frames = sorted((args.run / 'frames').glob('frame_*.csv'))
    f = read_frame(frames[args.frame], ny, nx); f0 = read_frame(frames[args.frame - 1], ny, nx)
    h, eta, u, v = f['h'], f['eta'], f['u'], f['v']
    wet = h > 0.05
    river = ref['river'].astype(bool); channel = ref['channel'].astype(bool)
    station, evs, wsr = ref['station'], ref['evidence_station'], ref['ws_reference']
    speed = np.hypot(u, v)
    fr = np.where(wet, speed / np.sqrt(9.81 * np.maximum(h, 0.05)), 0.0)
    cook_med = np.array([np.median(eta[wet[:, j] & channel[:, j], j]) if (wet[:, j] & channel[:, j]).sum() >= 3 else np.nan for j in range(nx)])
    err = cook_med - wsr
    bins = []
    for s0 in np.arange(0, station[-1], 10.0):
        m = (station >= s0) & (station < s0 + 10) & np.isfinite(err)
        if m.any():
            bins.append([float(s0), float(np.median(err[m]))])
    prof = json.loads((args.evidence / 'profile.json').read_text())
    anchor_kind = anchor_evidence_kind(prof)
    anchors = []
    for a in prof.get('anchors', []):
        if evs[0] <= a['station_m'] <= evs[-1]:
            j = int(np.argmin(np.abs(evs - a['station_m'])))
            win = slice(max(j - 2, 0), j + 3)
            anchors.append(dict(evidence_station_m=a['station_m'], scenario_station_m=float(station[j]), elevation_m=a['elevation_m'],
                                cooked_m=float(np.nanmedian(cook_med[win])), error_m=float(np.nanmedian(cook_med[win]) - a['elevation_m'])))
    iou = float((river & wet).sum() / max((river | wet).sum(), 1))
    q_centre = (np.where(wet, h * u, 0.0)).sum(0) * d
    q_face = face_discharge(args.solver_binary, args.scenario_root / 'scenario', f)
    dh = np.abs(h - f0['h'])[wet]
    # whitewater: evidence share per 250 m against cooked Fr > 0.8 share
    ev_share = np.interp(evs, np.array(prof['station_center_m']), np.array(prof.get('whitewater_share', [0] * len(prof['station_center_m'])))[:len(prof['station_center_m'])] if len(prof.get('whitewater_share', [])) == len(prof['station_center_m']) else np.zeros(len(prof['station_center_m'])))
    fast = (fr > 0.8) & wet
    per250 = []
    for j0 in range(0, nx, 125):
        m = slice(j0, j0 + 125)
        per250.append(dict(station_m=float(station[j0]), evidence_whitewater_share=float(np.mean(ev_share[m])),
                           cooked_fr_gt_0p8_share=float(fast[:, m].sum() / max(wet[:, m].sum(), 1))))
    ok = np.isfinite(err)
    report = dict(
        frame=frames[args.frame].name, discharge_target_m3s=Q,
        reference_anchors=anchors,
        anchor_evidence_kind=anchor_kind,
        measured_anchors=anchors if anchor_kind == 'measured' else [],
        anchor_error_m_max_abs=float(max((abs(a['error_m']) for a in anchors), default=float('nan'))),
        reference_surface_error_m=dict(median=float(np.median(err[ok])), median_abs=float(np.median(np.abs(err[ok]))),
                                       p90_abs=float(np.percentile(np.abs(err[ok]), 90)), by_bin=bins),
        wet_iou=iou, false_wet_cells=int((wet & ~channel).sum()), missed_wet_cells=int((river & ~wet).sum()),
        discharge_m3s=dict(median=float(np.median(q_face[5:-5])), p5=float(np.percentile(q_face[5:-5], 5)), p95=float(np.percentile(q_face[5:-5], 95)),
                           inlet_face=float(q_face[0]), outlet_face=float(q_face[-1]),
                           method='exact numerical face mass flux of the frame (solver --inspect-face-fluxes)'),
        discharge_cell_centre_hu_sum_m3s=dict(median=float(np.median(q_centre[5:-5])), p5=float(np.percentile(q_centre[5:-5], 5)),
                                              p95=float(np.percentile(q_centre[5:-5], 95)),
                                              note='diagnostic only: overstates transport on steep, shallow wet/dry reaches'),
        convergence=dict(p95_abs_dh_m=float(np.percentile(dh, 95)), max_abs_dh_m=float(dh.max()), compared=[frames[args.frame - 1].name, frames[args.frame].name]),
        froude=dict(p50=float(np.median(fr[wet])), p95=float(np.percentile(fr[wet], 95)), share_gt_1=float((fr[wet] > 1).mean())),
        speed_m_per_s=dict(p50=float(np.median(speed[wet])), p95=float(np.percentile(speed[wet], 95)), max=float(speed[wet].max())),
        depth_m=dict(p50=float(np.median(h[wet])), p95=float(np.percentile(h[wet], 95))),
        whitewater_vs_froude_by_250m=per250)
    (args.output / 'compare.json').write_text(json.dumps(report, indent=2) + '\n')
    np.savez(args.output / 'profiles.npz', station=station, evidence_station=evs, cook_median=cook_med, ws_reference=wsr, q_face=q_face, q_cell_centre=q_centre)
    # maps (rows = lateral, flipped so river-left is up)
    t = np.clip(h / 3.0, 0, 1)
    img = np.stack([30 * np.ones_like(t), 60 + 100 * t, 120 + 130 * t], -1).astype(np.uint8)
    img[~wet] = (120, 110, 90)
    sp = np.clip(speed / 4.0, 0, 1)
    img2 = np.stack([255 * sp, 80 * np.ones_like(sp), 255 * (1 - sp)], -1).astype(np.uint8); img2[~wet] = (120, 110, 90)
    agree = np.zeros((ny, nx, 3), np.uint8); agree[river & wet] = (40, 90, 200); agree[river & ~wet] = (240, 60, 40); agree[wet & ~river] = (250, 200, 40)
    write_png(args.output / 'depth_speed_agreement.png', np.repeat(np.repeat(np.vstack([img[::-1], img2[::-1], agree[::-1]]), 2, 0), 1, 1))
    W, H = 1100, 360
    chart = np.full((H, W, 3), 255, np.uint8)
    zlo, zhi = np.nanmin(wsr) - 3, np.nanmax(wsr) + 3
    def xy(s, z):
        return int(s / station[-1] * (W - 1)), int(np.clip((zhi - z) / (zhi - zlo) * (H - 1), 0, H - 1))
    for j in range(nx):
        x, y = xy(station[j], wsr[j]); chart[max(y - 1, 0):y + 2, x] = (20, 60, 200)
        if np.isfinite(cook_med[j]):
            x, y = xy(station[j], cook_med[j]); chart[y, x] = (230, 60, 30)
    for a in anchors:
        x, y = xy(a['scenario_station_m'], a['elevation_m']); chart[max(y - 4, 0):y + 5, max(x - 4, 0):x + 5] = (0, 150, 0)
    write_png(args.output / 'profile.png', chart)
    print(json.dumps({k: report[k] for k in ('anchor_evidence_kind', 'reference_anchors', 'reference_surface_error_m', 'wet_iou', 'discharge_m3s', 'convergence', 'froude')}, indent=1)[:3000])


if __name__ == '__main__':
    main()
