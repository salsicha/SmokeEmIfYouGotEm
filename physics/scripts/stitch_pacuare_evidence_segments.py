"""Stitch overlapping Pacuare evidence segments into one full-run evidence folder.

build_pacuare_evidence_grid.py works on a north-up 1 m window around a reach
of a few kilometres. The full Lower Pacuare run is built as overlapping
segments of OSM chainage; this joins them into the same folder layout
(evidence_grid.npz, centreline.json, profile.json, manifest.json), so
build_curvilinear_river_scenario.py applies unchanged.

Ownership: each segment owns the OSM chainage from the middle of its overlap
with the previous segment to the middle of its overlap with the next.
- River cells (cells with a midline station) are taken from the segment that
  owns their chainage.
- Other cells (ground away from the river) are taken from the first segment
  that covers them; neighbouring segments interpolate the same contours.
- Midline: each segment's bank-derived midline over its owned chainage,
  joined in order, lightly smoothed and resampled at 1 m; station is the
  joined midline's arc length.
- Water-surface reference: each segment's anchored profile over its owned
  chainage, made non-increasing downstream across the joins.

Nothing is re-derived from the sources; every input file is hashed.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ARRAYS_F32 = ('bed', 'dem2021', 'dem', 'bathy2014', 'station', 'lateral', 'ws')
ARRAYS_BOOL = ('river', 'channel', 'foam', 'rocks', 'bars')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gauss_smooth(v, sigma):
    if sigma <= 0:
        return v
    r = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    return np.convolve(np.pad(v, r, mode='edge'), k, mode='valid')


def arc_resample(x, y, step):
    s = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))]
    t = np.arange(0, s[-1], step)
    return np.interp(t, s, x), np.interp(t, s, y), np.interp(t, s, np.arange(len(s)))


def load(folder):
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_text())
    centre = json.loads((folder / 'centreline.json').read_text())
    profile = json.loads((folder / 'profile.json').read_text())
    pts = np.asarray(centre['points_xy_station'], float)
    chain = np.asarray(centre['osm_chain_m'], float)
    order = np.argsort(pts[:, 2])
    return dict(folder=folder, manifest=manifest, profile=profile, xy=pts[order, :2], station=pts[order, 2],
                chain=chain[order], range=manifest['parameters']['chain_m'])


def stitch(segments, out, run_chain):
    out = Path(out).resolve()
    if out.exists():
        raise ValueError('Fresh stitched evidence folder required')
    segs = sorted((load(s) for s in segments), key=lambda s: s['range'][0])
    for a, b in zip(segs, segs[1:]):
        if not b['range'][0] < a['range'][1]:
            raise ValueError('Segments must overlap')
    bounds = [segs[0]['range'][0]] + [0.5 * (b['range'][0] + a['range'][1]) for a, b in zip(segs, segs[1:])] + [segs[-1]['range'][1]]
    # The source bank lines can stop before the last window does: end the
    # stitched river where the last midline ends, never beyond its evidence.
    bounds[-1] = min(bounds[-1], float(segs[-1]['chain'].max()))
    for s, lo, hi in zip(segs, bounds, bounds[1:]):
        s['own'] = (lo, hi)
        if not (s['chain'].min() <= lo and s['chain'].max() >= hi):
            raise ValueError('Segment midline does not cover its owned chainage: %s' % s['folder'])

    # ---- joined midline (CRTM05), with OSM chainage per point
    parts_xy, parts_chain = [], []
    for s in segs:
        keep = (s['chain'] >= s['own'][0]) & (s['chain'] < s['own'][1])
        parts_xy.append(s['xy'][keep]); parts_chain.append(s['chain'][keep])
    xy = np.vstack(parts_xy); chain = np.concatenate(parts_chain)
    gaps = np.hypot(*np.diff(xy, axis=0).T)
    joins = [float(g) for g in gaps[np.r_[np.cumsum([len(p) for p in parts_xy])[:-1] - 1]]]
    x, y = gauss_smooth(xy[:, 0], 4.0), gauss_smooth(xy[:, 1], 4.0)
    x, y, index = arc_resample(x, y, 1.0)
    chain = np.maximum.accumulate(np.interp(index, np.arange(len(chain)), chain))
    station = np.arange(len(x), dtype=float)

    # ---- water-surface profile over owned chainage, mapped to joined station
    prof_st, prof = [], {}
    # Only per-station arrays every segment provides at full length (some
    # segments write whitewater_share one sample short).
    per_station = [k for k, v in segs[0]['profile'].items() if isinstance(v, list) and
                   all(isinstance(s['profile'].get(k), list) and
                       len(s['profile'][k]) == len(s['profile']['station_center_m']) for s in segs)]
    for s in segs:
        p = s['profile']
        seg_chain = np.interp(p['station_center_m'], s['station'], s['chain'])
        keep = (seg_chain >= s['own'][0]) & (seg_chain < s['own'][1])
        prof_st.append(np.interp(seg_chain[keep], chain, station))
        for key in per_station:
            prof.setdefault(key, []).append(np.asarray(p[key], float)[keep])
    st = np.concatenate(prof_st)
    order = np.argsort(st)
    profile = {k: np.concatenate(v)[order] for k, v in prof.items()}
    profile['station_center_m'] = st[order]
    ws = profile['ws_reference_m']
    step_drops = [float(d) for d in np.diff(ws)[np.diff(ws) > 0]]
    profile['ws_reference_m'] = np.minimum.accumulate(ws)

    # ---- north-up window covering every segment
    grids = [s['manifest']['grid'] for s in segs]
    x0 = min(g['x0'] for g in grids); x1 = max(g['x0'] + g['nx'] for g in grids)
    ytop = max(g['y_top'] for g in grids); ybot = min(g['y_top'] - g['ny'] for g in grids)
    nx, ny = int(round(x1 - x0)), int(round(ytop - ybot))
    print('window %d x %d m (%d Mcells)' % (nx, ny, nx * ny // 1_000_000), flush=True)
    grid = {k: np.full((ny, nx), np.nan, np.float32) for k in ARRAYS_F32}
    grid.update({k: np.zeros((ny, nx), bool) for k in ARRAYS_BOOL})
    grid['class_code'] = np.zeros((ny, nx), np.uint8)
    filled = np.zeros((ny, nx), bool)
    sources = []
    for s in segs:
        g = s['manifest']['grid']
        r0, c0 = int(round(ytop - g['y_top'])), int(round(g['x0'] - x0))
        view = np.s_[r0:r0 + g['ny'], c0:c0 + g['nx']]
        path = s['folder'] / 'evidence_grid.npz'
        sources.append(dict(folder=str(s['folder']), owned_chain_m=list(s['own']), evidence_grid_sha256=sha(path),
                            manifest_sha256=sha(s['folder'] / 'manifest.json')))
        with np.load(path) as a:
            seg_station = a['station'].astype(float)
            seg_chain = np.full(seg_station.shape, np.nan)
            ok = np.isfinite(seg_station)
            seg_chain[ok] = np.interp(seg_station[ok], s['station'], s['chain'])
            owned = ok & (seg_chain >= s['own'][0]) & (seg_chain < s['own'][1])
            ground = ~ok & ~filled[view]
            take = owned | ground
            for key in ARRAYS_F32 + ARRAYS_BOOL + ('class_code',):
                if key == 'station':
                    continue
                if key in a.files:
                    target = grid[key][view]
                    target[take] = a[key][take]
            # Joined-midline station for river cells.
            target = grid['station'][view]
            target[owned] = np.interp(seg_chain[owned], chain, station).astype(np.float32)
            filled[view] |= take
        print('pasted', s['folder'].name, 'owned', s['own'], flush=True)
    missing = int((~filled).sum())
    out.mkdir(parents=True)
    np.savez_compressed(out / 'evidence_grid.npz', **grid)
    run_station = [float(np.interp(c, chain, station)) for c in run_chain]
    base = segs[0]['manifest']
    (out / 'centreline.json').write_text(json.dumps(dict(
        schema='raftsim.pacuare.huacas_midline.v1', crs=base.get('crs', 'EPSG:5367 CR05 / CRTM05'),
        method='Joined segment midlines (each over its owned OSM chainage), Gaussian sigma 4 m at the joins, 1 m arc length',
        reach_station_m=run_station, points_xy_station=np.c_[x, y, station].round(3).tolist(),
        osm_chain_m=chain.round(2).tolist())) + '\n')
    (out / 'profile.json').write_text(json.dumps(
        {k: (v.round(4).tolist() if isinstance(v, np.ndarray) else v) for k, v in profile.items()}
        | dict(ws_reference_method='segment anchored profiles over owned chainage, non-increasing downstream')) + '\n')
    manifest = dict(schema='raftsim.pacuare.full_run_evidence_grid.v1', crs=base.get('crs'), vertical=base.get('vertical'),
                    grid=dict(x0=x0, y_top=ytop, nx=nx, ny=ny, cell_m=1.0), parameters=dict(base['parameters'], chain_m=list(run_chain)),
                    class_codes=base.get('class_codes'),
                    statistics=dict(reach_station_m=run_station, reach_osm_chain_m=list(run_chain),
                                    midline_join_gaps_m=joins, profile_rises_removed_m=step_drops,
                                    window_cells_without_segment=missing, midline_length_m=float(station[-1])),
                    segments=sources, inferred=True, accepted=False)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(json.dumps(manifest['statistics'], indent=1))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('segments', nargs='+', type=Path, help='segment evidence folders')
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--run-chain-m', type=float, nargs=2, required=True,
                        help='OSM chainage of the playable run (put-in, take-out)')
    args = parser.parse_args()
    stitch(args.segments, args.out, args.run_chain_m)
