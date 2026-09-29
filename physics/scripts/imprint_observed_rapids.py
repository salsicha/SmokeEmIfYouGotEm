"""Imprint a reach's observed rapid features on its evidence grid (numpy only).

    imprint_observed_rapids.py <evidence_dir> <catalogue.json> --out <new_evidence_dir>

Reads <evidence_dir>/evidence_grid.npz (bed, class_code, station, and lateral and
ws where the builder saved them) and manifest.json, applies
observed_rapid_features.imprint, and writes a complete new evidence folder
(every other file copied unchanged) whose grid carries the reconstructed bed
and class 5 cells, and whose manifest records the catalogue, its hash and the
per-feature imprint report. Downstream steps (scenario build, cook, compare,
export) run on the new folder exactly as on the old one.

Where the grid lacks lateral or ws (the Hance builder), lateral comes from the
nearest point of centreline.json and ws from the per-station reference surface
of profile.json.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

from observed_rapid_features import Frame, imprint, load_catalogue


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def lateral_from_centreline(station, centreline, x0, y_top):
    """Signed distance (river left +) to the nearest centreline point, per cell with a station."""
    pts = np.array(centreline, float)             # (x, y, station) world metres
    H, W = station.shape
    lat = np.full((H, W), np.nan, np.float32)
    rr, cc = np.nonzero(np.isfinite(station))
    ex = x0 + cc + 0.5; ey = y_top - rr - 0.5
    tx = np.gradient(pts[:, 0]); ty = np.gradient(pts[:, 1]); tn = np.hypot(tx, ty); tx /= tn; ty /= tn
    order = np.argsort(pts[:, 2])
    for k in range(0, len(rr), 20000):
        sl = slice(k, k + 20000)
        j = np.clip(np.searchsorted(pts[order, 2], station[rr[sl], cc[sl]]), 0, len(pts) - 1)
        i = order[j]
        dx = ex[sl] - pts[i, 0]; dy = ey[sl] - pts[i, 1]
        lat[rr[sl], cc[sl]] = dx * (-ty[i]) + dy * tx[i]
    return lat


def cooked_surface(shape, x0, y_top, scenario_root, run):
    """The last frame's water surface of a curvilinear cook, rasterised onto the 1 m evidence grid."""
    from audit_observed_rapids import last_frame
    from export_hance_evidence_runtime import read_frame
    sc = json.loads((Path(scenario_root) / 'scenario/scenario.json').read_text())
    ny, nx = sc['grid']['ny'], sc['grid']['nx']
    ref = np.load(Path(scenario_root) / 'reference.npz')
    wx, wy = ref['world_x'].astype(float), ref['world_y'].astype(float)
    if abs(float(np.nanmean(wx)) - x0) > 5.0e4:          # local solver frame: add the build origin
        o = json.loads((Path(scenario_root) / 'build_report.json').read_text())['origin']
        wx = wx + o[0]; wy = wy + o[1]
    f = read_frame(last_frame(run), ny, nx)
    wet = f['h'] > 0.05
    H, W = shape
    acc = np.zeros(shape); cnt = np.zeros(shape)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            r = np.floor(y_top - wy[wet]).astype(int) + dr; c = np.floor(wx[wet] - x0).astype(int) + dc
            ok = (r >= 0) & (r < H) & (c >= 0) & (c < W)
            np.add.at(acc, (r[ok], c[ok]), f['eta'][wet][ok]); np.add.at(cnt, (r[ok], c[ok]), 1.0)
    return np.where(cnt > 0, acc / np.maximum(cnt, 1.0), np.nan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('evidence', type=Path)
    ap.add_argument('catalogue', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--channel-classes', type=int, nargs='+', default=[2, 4])
    ap.add_argument('--surface-from', type=Path, nargs=2, metavar=('SCENARIO_ROOT', 'RUN'),
                    help='set crests against this cook\'s water surface instead of the evidence reference surface')
    args = ap.parse_args()
    assert not args.out.exists(), 'fresh output folder required'
    ev = args.evidence
    man = json.loads((ev / 'manifest.json').read_text())
    z = dict(np.load(ev / 'evidence_grid.npz'))
    cat = load_catalogue(args.catalogue)
    grid = man.get('grid', {})
    x0 = float(grid.get('x0', 0.0)); y_top = float(grid.get('y_top', 0.0))
    st = z['station'].astype(np.float64)
    if 'lateral' in z:
        lat = z['lateral'].astype(np.float64)
    else:
        cl = json.loads((ev / 'centreline.json').read_text())
        pts = cl.get('points_xy_station') or cl.get('points')
        lat = lateral_from_centreline(st, pts, x0, y_top).astype(np.float64)
        z['lateral'] = lat.astype(np.float32)
    if 'ws' in z:
        ws = z['ws'].astype(np.float64)
    else:
        prof = json.loads((ev / 'profile.json').read_text())
        s_ref = np.array(prof['station_center_m'], float); w_ref = np.array(prof['ws_reference_m'], float)
        ok = np.isfinite(w_ref)
        ws = np.where(np.isfinite(st), np.interp(st, s_ref[ok], w_ref[ok]), np.nan)
    surface_note = 'evidence reference surface'
    if args.surface_from:
        cooked = cooked_surface(st.shape, x0, y_top, *args.surface_from)
        ws = np.where(np.isfinite(cooked) & np.isfinite(ws), cooked, ws)
        surface_note = 'cooked surface of ' + ' / '.join(p.as_posix() for p in args.surface_from)
    discharge = float(man.get('parameters', {}).get('discharge_m3s') or cat['discharge_m3s'])
    frame = Frame(z['bed'].astype(np.float64), z['class_code'].copy(), ws, st, lat, discharge,
                  channel_classes=tuple(args.channel_classes), foam=z.get('foam'))
    bed, cls, report = imprint(frame, cat['features'])
    args.out.mkdir(parents=True)
    for p in ev.iterdir():
        if p.name not in ('evidence_grid.npz', 'manifest.json') and p.is_file():
            shutil.copyfile(p, args.out / p.name)
    z['bed'] = bed.astype(np.float32); z['class_code'] = cls
    np.savez_compressed(args.out / 'evidence_grid.npz', **z)
    man.setdefault('class_codes', {})['5'] = ('bed shape reconstructed from observations (whitewater imagery, outfitter and '
                                              'guidebook descriptions, video): position and size approximate, shape inferred')
    man['observed_rapid_features'] = dict(catalogue=args.catalogue.resolve().as_posix(), catalogue_sha256=sha(args.catalogue),
                                          source_evidence=ev.resolve().as_posix(), crest_surface=surface_note,
                                          features=len(report), imprint=report)
    (args.out / 'manifest.json').write_text(json.dumps(man, indent=1) + '\n')
    for r in report:
        print(json.dumps(r))


if __name__ == '__main__':
    main()
