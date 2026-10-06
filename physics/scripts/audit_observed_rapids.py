"""Does a cook reproduce each catalogued rapid feature? (curvilinear cooks, numpy only)

    audit_observed_rapids.py <scenario_root> <run> <catalogue.json> --evidence <evidence_dir>
                             [--baseline-run <run>] [--out report.json]

For each feature of an observed-rapid catalogue, looks at the cooked frame in the
feature's footprint and reports:
- breaking cells: the game's own breaking-site rule (ARaftSimWaterSurfaceActor):
  the cell is wet with Froude <= 0.94, a wet cell 4 or 6 m upstream has
  Froude >= 1.12, and intensity clamp((Fr_up - 0.85) / 1.5) x clamp(h / 0.6,
  0.3, 1) >= 0.08;
- peak Froude and the share of wet cells over Froude 0.8;
- surface relief: the spread (p95 - p5) of the water surface after removing
  the linear trend along station, a proxy for wave and hole height;
- where the evidence grid has a whitewater (foam) mask, the photographed
  whitewater share of the footprint beside the cooked Froude > 0.8 share.
The footprint is in the catalogue's frame (evidence-grid station and lateral):
from 10 m above the feature to 30 m below its end, its width plus 5 m. Solver
cells are placed in that frame through their world coordinates (reference.npz)
sampled on the evidence grid. With --baseline-run the same numbers for another
cook on the same grid are reported beside them.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from export_hance_evidence_runtime import read_frame


def last_frame(run):
    run = Path(run)
    frames = sorted((run / 'frames').glob('frame_*.csv'))
    if not frames:
        frames = sorted(run.rglob('frames/frame_*.csv'))
    return frames[-1]


def solver_cells_in_evidence_frame(scenario_root, evidence):
    ref = np.load(Path(scenario_root) / 'reference.npz')
    ev = np.load(Path(evidence) / 'evidence_grid.npz')
    man = json.loads((Path(evidence) / 'manifest.json').read_text())
    x0, y_top = float(man['grid']['x0']), float(man['grid']['y_top'])
    wx, wy = ref['world_x'].astype(float), ref['world_y'].astype(float)
    if abs(float(np.nanmean(wx)) - x0) > 5.0e4:
        o = json.loads((Path(scenario_root) / 'build_report.json').read_text())['origin']
        wx = wx + o[0]; wy = wy + o[1]
    H, W = ev['station'].shape
    r = np.clip(np.floor(y_top - wy).astype(int), 0, H - 1); c = np.clip(np.floor(wx - x0).astype(int), 0, W - 1)
    st = ev['station'][r, c].astype(float)
    if 'lateral' in ev.files:
        lat = ev['lateral'][r, c].astype(float)
    else:
        from imprint_observed_rapids import lateral_from_centreline
        cl = json.loads((Path(evidence) / 'centreline.json').read_text())
        full = lateral_from_centreline(ev['station'].astype(float), cl.get('points_xy_station') or cl.get('points'), x0, y_top)
        lat = full[r, c].astype(float)
    foam = ev['foam'][r, c] if 'foam' in ev.files else None
    return st, lat, foam


def metrics(f, mask, foam=None):
    h, u, v, eta = f['h'], f['u'], f['v'], f['eta']
    wet = h > 0.05
    fr = np.where(wet, np.hypot(u, v) / np.sqrt(9.81 * np.maximum(h, 0.05)), 0.0)
    breaking = 0; max_int = 0.0
    for r, c in zip(*np.nonzero(mask & wet & (fr <= 0.94))):
        up = [fr[r, c - k] for k in (2, 3) if c - k >= 0 and wet[r, c - k]]
        if not up or max(up) < 1.12:
            continue
        inten = np.clip((max(up) - 0.85) / 1.5, 0, 1) * np.clip(h[r, c] / 0.6, 0.3, 1.0)
        if inten >= 0.08:
            breaking += 1; max_int = max(max_int, float(inten))
    w = mask & wet
    if w.sum() < 4:
        return dict(wet_cells=int(w.sum()))
    cols = np.broadcast_to(np.arange(h.shape[1])[None, :], h.shape)
    A = np.stack([cols[w].astype(float), np.ones(int(w.sum()))], 1)
    coef, *_ = np.linalg.lstsq(A, eta[w], rcond=None)
    res = eta[w] - A @ coef
    out = dict(wet_cells=int(w.sum()), breaking_cells=breaking, max_breaking_intensity=round(max_int, 3),
               peak_froude=round(float(fr[w].max()), 2), froude_gt_0p8_share=round(float((fr[w] > 0.8).mean()), 3),
               surface_relief_m=round(float(np.percentile(res, 95) - np.percentile(res, 5)), 2))
    if foam is not None:
        out['photographed_white_share'] = round(float(foam[w].mean()), 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scenario_root', type=Path)
    ap.add_argument('run', type=Path)
    ap.add_argument('catalogue', type=Path)
    ap.add_argument('--evidence', type=Path, required=True)
    ap.add_argument('--baseline-run', type=Path)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    sc = json.loads((args.scenario_root / 'scenario/scenario.json').read_text())
    ny, nx = sc['grid']['ny'], sc['grid']['nx']
    st, lat, foam = solver_cells_in_evidence_frame(args.scenario_root, args.evidence)
    cat0 = json.loads(args.catalogue.read_text())
    if cat0.get('station_frame') == 'scenario':
        # footprints in the solver's own (station, lateral) frame
        ref = np.load(args.scenario_root / 'reference.npz')
        st = np.broadcast_to(np.asarray(ref['station'], float)[None, :], (ny, nx)).copy()
        lat = np.broadcast_to(np.asarray(ref['lateral'], float)[:, None], (ny, nx)).copy()
    frames = [read_frame(last_frame(args.run), ny, nx)]
    if args.baseline_run:
        frames.append(read_frame(last_frame(args.baseline_run), ny, nx))
    cat = json.loads(args.catalogue.read_text())
    out = []
    for feat in cat['features']:
        s0 = feat['station_m']; length = float(feat.get('length_m', 0.0) or 0.0)
        half = 0.5 * float(feat.get('width_m', 10.0)) + 5.0
        mask = (st >= s0 - 10.0) & (st <= s0 + length + 30.0) & (np.abs(lat - feat['lateral_m']) <= half)
        rec = dict(id=feat['id'], type=feat['type'], station_m=s0, footprint_cells=int(mask.sum()))
        rec['cook'] = metrics(frames[0], mask, foam)
        if len(frames) > 1:
            rec['baseline'] = metrics(frames[1], mask, foam)
        out.append(rec)
        print(json.dumps(rec))
    if args.out:
        args.out.write_text(json.dumps(dict(catalogue=str(args.catalogue), run=str(args.run), features=out), indent=1) + '\n')


if __name__ == '__main__':
    main()
