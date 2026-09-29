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


def repo_path(p):
    """Repo-relative path for provenance records (absolute only outside the repo)."""
    root = Path(__file__).resolve().parents[2]
    p = Path(p).resolve()
    return p.relative_to(root).as_posix() if p.is_relative_to(root) else p.as_posix()


def project_on_centreline(shape, centreline, x0, y_top, band_m=90.0):
    """Station and signed lateral (river left +) of every cell within band_m of the centreline:
    nearest point on the polyline with each segment's foot clamped to its ends (as the builders)."""
    pts = np.array(centreline, float)
    order = np.argsort(pts[:, 2]); pts = pts[order]
    H, W = shape
    st = np.full(shape, np.nan); lat = np.full(shape, np.nan); best = np.full(shape, np.inf)
    for i in range(len(pts) - 1):
        (ax, ay, sa), (bx, by, sb) = pts[i], pts[i + 1]
        seg = np.hypot(bx - ax, by - ay)
        if seg < 1e-6:
            continue
        tx, ty = (bx - ax) / seg, (by - ay) / seg
        c0 = max(int(np.floor(min(ax, bx) - x0 - band_m)), 0); c1 = min(int(np.ceil(max(ax, bx) - x0 + band_m)) + 1, W)
        r0 = max(int(np.floor(y_top - max(ay, by) - band_m)), 0); r1 = min(int(np.ceil(y_top - min(ay, by) + band_m)) + 1, H)
        if c1 <= c0 or r1 <= r0:
            continue
        yy, xx = np.mgrid[r0:r1, c0:c1]
        ex = x0 + xx + 0.5; ey = y_top - yy - 0.5
        a = np.clip((ex - ax) * tx + (ey - ay) * ty, 0.0, seg)
        px = ax + a * tx; py = ay + a * ty
        d = np.hypot(ex - px, ey - py)
        side = (ex - ax) * (-ty) + (ey - ay) * tx
        sub = best[r0:r1, c0:c1]
        closer = (d < sub) & (d <= band_m)
        sub[closer] = d[closer]
        st[r0:r1, c0:c1][closer] = (sa + a * (sb - sa) / seg)[closer]
        lat[r0:r1, c0:c1][closer] = np.where(side >= 0, d, -d)[closer]
    return st, lat


def scenario_features_to_evidence(features, scenario_root, st_grid, lat_grid, x0, y_top):
    """Catalogues written in the in-game (scenario) frame: station and lateral of the
    solver grid. Place each feature by world position, then read the evidence grid's
    own station/lateral there (the two frames' centrelines differ by metres)."""
    ref = np.load(Path(scenario_root) / 'reference.npz')
    s_ax = np.asarray(ref['station'], float); l_ax = np.asarray(ref['lateral'], float)
    wx, wy = ref['world_x'].astype(float), ref['world_y'].astype(float)
    if abs(float(np.nanmean(wx)) - x0) > 5.0e4:
        o = json.loads((Path(scenario_root) / 'build_report.json').read_text())['origin']
        wx = wx + o[0]; wy = wy + o[1]
    out = []
    for f in features:
        g = dict(f)
        c = float(np.interp(f['station_m'], s_ax, np.arange(len(s_ax))))
        r = float(np.interp(f['lateral_m'], l_ax, np.arange(len(l_ax))))
        c0, r0 = int(np.clip(np.floor(c), 0, len(s_ax) - 2)), int(np.clip(np.floor(r), 0, len(l_ax) - 2))
        fc, fr = c - c0, r - r0
        def bil(a):
            return ((1 - fr) * ((1 - fc) * a[r0, c0] + fc * a[r0, c0 + 1]) + fr * ((1 - fc) * a[r0 + 1, c0] + fc * a[r0 + 1, c0 + 1]))
        x, y = bil(wx), bil(wy)
        rr, cc = int(np.floor(y_top - y)), int(np.floor(x - x0))
        g['scenario_station_m'], g['scenario_lateral_m'] = f['station_m'], f['lateral_m']
        g['station_m'] = float(st_grid[rr, cc]); g['lateral_m'] = float(lat_grid[rr, cc])
        assert np.isfinite(g['station_m']) and np.isfinite(g['lateral_m']), 'feature off the evidence corridor: ' + f['id']
        out.append(g)
    return out


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
    run = Path(run)
    if (run / 'manifest.json').exists() and json.loads((run / 'manifest.json').read_text()).get('schema') == \
            'raftsim.cooked_flow_fields.v1':
        cm = json.loads((run / 'manifest.json').read_text()); (band,) = cm['bands']
        h = np.load(run / band['arrays']['h']['file']).astype(float); b = np.load(run / band['arrays']['bed']['file']).astype(float)
        f = dict(h=h, eta=b + h)
    else:
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


def cartesian_cooked_surface(shape, x0, y_top, cook_dir, origin):
    """A Cartesian cook's last frame surface (bed + h where wet), rasterised onto the 1 m evidence grid."""
    from audit_cartesian_whitewater import load_atlas
    g, ax0, ay0, D = load_atlas(cook_dir)
    wet = np.nan_to_num(g['h']) > 0.05
    eta = np.where(wet, g['bed'] + g['h'], np.nan) + (json.loads((Path(cook_dir) / 'input_manifest.json').read_text())
                                                      .get('vertical_datum_m', 0.0))
    ny, nx = wet.shape
    H, W = shape
    out = np.full(shape, np.nan)
    yy, xx = np.mgrid[0:H, 0:W]
    E = x0 + xx + 0.5; N = y_top - yy - 0.5
    c = np.floor((E - origin[0] - ax0) / D + 0.5).astype(int); r = np.floor((N - origin[1] - ay0) / D + 0.5).astype(int)
    ok = (r >= 0) & (r < ny) & (c >= 0) & (c < nx)
    out[ok] = eta[r[ok], c[ok]]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('evidence', type=Path)
    ap.add_argument('catalogue', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--channel-classes', type=int, nargs='+', default=[2, 4])
    ap.add_argument('--surface-from', type=Path, nargs=2, metavar=('SCENARIO_ROOT', 'RUN'),
                    help='set crests against this cook\'s water surface instead of the evidence reference surface')
    ap.add_argument('--cartesian-surface-from', type=Path, metavar='COOK_DIR',
                    help='as --surface-from, for a Cartesian cook (raftsim_cartesian_cook output folder); needs --origin')
    ap.add_argument('--origin', type=float, nargs=2, help='Cartesian runtime frame origin (E, N)')
    ap.add_argument('--scenario-root', type=Path,
                    help='solver scenario whose (station, lateral) frame a catalogue with station_frame "scenario" uses')
    ap.add_argument('--edit-cooked-wet-banks', action='store_true',
                    help='let features extend over cells the cook wets outside the channel classes (inferred bank zones only; '
                         'never for measured bank terrain)')
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
    # Builders store station/lateral only inside the imaged channel; a cook can
    # wet a wider corridor. Extend both over a band around the centreline.
    cl = json.loads((ev / 'centreline.json').read_text()) if (ev / 'centreline.json').exists() else None
    pts = (cl.get('points_xy_station') or cl.get('points')) if cl else None
    if pts is not None and len(pts) and len(pts[0]) >= 3:
        st_full, lat_full = project_on_centreline(st.shape, pts, x0, y_top)
        st = np.where(np.isfinite(st), st, st_full)
        lat = np.where(np.isfinite(lat), lat, lat_full)
    surface_note = 'evidence reference surface'
    wet_extent = None
    if args.surface_from:
        cooked = cooked_surface(st.shape, x0, y_top, *args.surface_from)
        wet_extent = np.isfinite(cooked) & (cooked > z['bed'] + 0.05)
        ws = np.where(np.isfinite(cooked), cooked, ws)
        surface_note = 'cooked surface of ' + ' / '.join(repo_path(p) for p in args.surface_from)
    elif args.cartesian_surface_from:
        cooked = cartesian_cooked_surface(st.shape, x0, y_top, args.cartesian_surface_from, args.origin)
        wet_extent = np.isfinite(cooked) & (cooked > z['bed'] + 0.05)
        ws = np.where(np.isfinite(cooked), cooked, ws)
        surface_note = 'cooked surface of ' + repo_path(args.cartesian_surface_from)
    features = cat['features']
    if cat.get('station_frame') == 'scenario':
        assert args.surface_from or args.scenario_root, 'a scenario-frame catalogue needs --scenario-root (or --surface-from)'
        features = scenario_features_to_evidence(features, args.scenario_root or args.surface_from[0], st, lat, x0, y_top)
    # size features for the catalogue's flow (the cook's): an evidence grid can be
    # built at another one (Chilko: the 45 m3/s LiDAR flight flow, cooked at 93)
    discharge = float(cat.get('discharge_m3s') or man.get('parameters', {}).get('discharge_m3s'))
    frame = Frame(z['bed'].astype(np.float64), z['class_code'].copy(), ws, st, lat, discharge,
                  channel_classes=tuple(args.channel_classes), foam=z.get('foam'), wet_extent=wet_extent,
                  edit_wet_extent=args.edit_cooked_wet_banks)
    bed, cls, report = imprint(frame, features)
    args.out.mkdir(parents=True)
    for p in ev.iterdir():
        if p.name not in ('evidence_grid.npz', 'manifest.json') and p.is_file():
            shutil.copyfile(p, args.out / p.name)
    z['bed'] = bed.astype(np.float32); z['class_code'] = cls
    np.savez_compressed(args.out / 'evidence_grid.npz', **z)
    man.setdefault('class_codes', {})['5'] = ('bed shape reconstructed from observations (whitewater imagery, outfitter and '
                                              'guidebook descriptions, video): position and size approximate, shape inferred')
    man['observed_rapid_features'] = dict(catalogue=repo_path(args.catalogue), catalogue_sha256=sha(args.catalogue),
                                          source_evidence=repo_path(ev), crest_surface=surface_note,
                                          sizing_discharge_m3s=discharge, features=len(report), imprint=report)
    (args.out / 'manifest.json').write_text(json.dumps(man, indent=1) + '\n')
    for r in report:
        print(json.dumps(r))


if __name__ == '__main__':
    main()
