"""Export the Zambezi upper-gorge Cartesian cook as runtime data (numpy only).

Inputs: the evidence folder (build_zambezi_evidence_grid.py), the cook
package folder (prepare_zambezi_cartesian_cook.py), the raftsim_cartesian_cook
output and its compare_zambezi_cartesian_cook.py report.

Outputs under physics/data/real_world/zambezi_batoka_gorge:
  scenario_upper_gorge_evidence_2025/
    cartesian_runtime/atlas/ (raftsim.cartesian_state_atlas.v1: the cook
      tiles' bed and the last frame's h, u, v),
    cartesian_runtime/region_upper_gorge/ (raftsim.cooked_flow_fields.v1,
      cartesian_east_north_m: one source grid over every tile, with the
      captured water mask = the Sentinel-2 low-water extent),
    cartesian_runtime/streaming_manifest.json (raftsim.cartesian_water_streaming.v1
      with explicit valid live-centre rectangles that keep every crop off
      unavailable cells: water outside the cook, and the cells beyond its
      inflow and outflow faces),
    cartesian_runtime/coordinate_map.json (raftsim.cartesian_water_coordinate_map.v1),
    cartesian_runtime/progress_coordinate_map.json (raftsim.curved_river_coordinate_map.v1
      along the evidence midline, for run progress only), evidence/.
  terrain/upper_gorge_evidence_2025/
    2017^2 heightfield over the evidence window, 2048^2 Sentinel-2 drape,
    GLO-30 backdrop mesh and drape, local centreline, terrain manifest.

Frame: local metres east/north of the cook's world origin (UTM 35S, the
evidence window's west edge and north-south centre); Unreal X = east * 100,
Y = -north * 100; Z = (EGM2008 height - datum) * 100.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from build_futaleufu_evidence_grid import catmull_rom  # noqa: E402
from build_zambezi_evidence_grid import UTM35S, load_glo30  # noqa: E402
from export_hance_evidence_runtime import bilinear, smooth_fill, write_png_rgb, write_png_u16  # noqa: E402
from geo_frames import tm_inverse  # noqa: E402

DATA = ROOT / 'physics/data/real_world/zambezi_batoka_gorge'
SRC = DATA / 'zambezi_sources_2026_09'
SECTION = 'upper_gorge_evidence_2025'
LANDSCAPE, DRAPE, BACKDROP_DRAPE = 2017, 2048, 2048
BACKDROP_CELL, BACKDROP_EXTENT_M, BACKDROP_MARGIN_M = 20.0, 3000.0, 3.0
BACKDROP_RING_M, BACKDROP_RING_DROP_M = 20.0, 0.5
ALBEDO_MEDIAN, ALBEDO_CAP, WET_BED_DARKENING = 0.10, 0.45, 0.55


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()


def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def array_meta(path, base, dtype):
    a = np.load(path, mmap_mode='r')
    return dict(file=Path(path).resolve().relative_to(Path(base).resolve()).as_posix(), sha256=sha(path), shape=list(a.shape), dtype=dtype)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path)
    ap.add_argument('packages', type=Path)
    ap.add_argument('cook', type=Path)
    ap.add_argument('compare', type=Path)
    ap.add_argument('--band-id', default='low_water_283cms')
    ap.add_argument('--sentinel2', default='S2C_T35KLA_20251003T082652_L2A.npz')
    ap.add_argument('--live-extent-m', type=float, default=224.0)
    ap.add_argument('--advance-m', type=float, default=64.0)
    ap.add_argument('--context-cells', type=int, default=3)
    ap.add_argument('--raft-margin-m', type=float, default=8.0)
    ap.add_argument('--detail-footprint-m', type=float, default=67.0,
                    help="side of the raft's stateful-detail source footprint (RaftSimStatefulDetailComponent LiveSourceSampleSide)")
    ap.add_argument('--centre-step-m', type=float, default=4.0)
    ap.add_argument('--bed-correction-file', type=Path, default=None,
                    help='where the bed correction named by the evidence manifest now lives (checked by its sha256)')
    args = ap.parse_args()
    scen = DATA / f'scenario_{SECTION}'; terr = DATA / f'terrain/{SECTION}'
    assert not scen.exists() and not terr.exists(), 'fresh output folders required'
    ev = args.evidence.resolve(); pk = args.packages.resolve(); ck = args.cook.resolve()
    evm = json.loads((ev / 'manifest.json').read_text())
    X0, Y1, NX, NY = evm['grid']['x0'], evm['grid']['y_top'], evm['grid']['nx'], evm['grid']['ny']
    pm = json.loads((pk / 'manifest.json').read_text())
    assert sha(pk / 'manifest.json') == sha(ck / 'input_manifest.json'), 'cook does not belong to these packages'
    D, T = pm['grid']['cell_m'], pm['grid']['tile_cells']
    ax, ay = pm['grid']['lattice_offset_utm_m']
    datum = pm['vertical_datum_m']; origin = np.array(pm['world_origin_utm35s_m'])
    roughness = json.loads((pk / pm['packages'][0] / 'scenario.json').read_text())['roughness']
    tiles = [tuple(t) for t in pm['tile_indices']]
    frames = sorted(p for p in ck.glob('frame_*') if (p / 'complete.json').exists())
    frame = frames[-1]
    complete = json.loads((frame / 'complete.json').read_text())
    compare = json.loads((args.compare / 'compare.json').read_text())
    assert compare['frame'] == frame.name
    h = np.load(frame / 'h.npy'); u = np.load(frame / 'u.npy'); v = np.load(frame / 'v.npy')
    assert h.min() >= 0 and h.max() <= 10 and np.hypot(u, v).max() <= 20, 'runtime atlas gates'
    bed = np.concatenate([np.load(pk / n / 'bed.npy') for n in pm['packages']]).astype(np.float64)
    ev_g = np.load(ev / 'evidence_grid.npz')

    # ---------------- atlas
    rt = scen / 'cartesian_runtime'; atlas_dir = rt / 'atlas'; atlas_dir.mkdir(parents=True)
    for name, a in (('bed', bed), ('h', h), ('u', u), ('v', v)):
        np.save(atlas_dir / f'{name}.npy', np.ascontiguousarray(a, dtype='<f8'))
    tile_origins = [[float(ax + i * D * T - origin[0] + D / 2), float(ay + j * D * T - origin[1] + D / 2)] for (i, j) in tiles]
    atlas = dict(schema='raftsim.cartesian_state_atlas.v1', tile_shape=[T, T], grid_spacing_m=D, source_elevation_datum_m=datum,
                 dry_tolerance=1.e-6, tiles=[dict(origin_m=o) for o in tile_origins],
                 arrays={n: array_meta(atlas_dir / f'{n}.npy', atlas_dir, '<f8') for n in ('bed', 'h', 'u', 'v')},
                 physical_exterior_faces=pm['boundary_probes'], source_frame=frame.name, source_time_seconds=complete['time_seconds'],
                 input_manifest_sha256=sha(pk / 'manifest.json'), settled_hydraulics=False, normal_map_integrated=False)
    write_json(atlas_dir / 'manifest.json', atlas)
    atlas_hash = sha(atlas_dir / 'manifest.json')

    # ---------------- one source region over every tile
    ii = np.array([t[0] for t in tiles]); jj = np.array([t[1] for t in tiles])
    gi0, gj0 = ii.min(), jj.min()
    RNX, RNY = int((ii.max() - gi0 + 1) * T), int((jj.max() - gj0 + 1) * T)
    r_origin = np.array([ax + gi0 * D * T - origin[0] + D / 2, ay + gj0 * D * T - origin[1] + D / 2])
    rbed = np.full((RNY, RNX), np.nan)
    solved = np.zeros((RNY, RNX), bool)
    for k, (i, j) in enumerate(tiles):
        r0, c0 = (j - gj0) * T, (i - gi0) * T
        rbed[r0:r0 + T, c0:c0 + T] = bed[k * T:(k + 1) * T]
        solved[r0:r0 + T, c0:c0 + T] = True
    # cells outside the tiles: evidence terrain (cell means), relative to datum
    e_c = origin[0] + r_origin[0] + np.arange(RNX) * D; n_c = origin[1] + r_origin[1] + np.arange(RNY) * D
    kk = int(round(D))
    fb = ev_g['bed'].astype(np.float64); fr = ev_g['river']
    cols = np.clip(np.floor(e_c - D / 2 - X0).astype(int), 0, NX - kk); rows = np.clip(np.floor(Y1 - (n_c + D / 2)).astype(int), 0, NY - kk)
    block_bed = np.zeros((RNY, RNX)); block_riv = np.zeros((RNY, RNX))
    for a_ in range(kk):
        for b_ in range(kk):
            block_bed += fb[(rows + a_)[:, None], (cols + b_)[None, :]]
            block_riv += fr[(rows + a_)[:, None], (cols + b_)[None, :]]
    block_bed /= kk * kk; block_riv /= kk * kk
    rbed = np.where(solved, rbed, block_bed - datum)
    captured = (block_riv >= 0.5).astype(np.uint8)
    wet_atlas = np.zeros((RNY, RNX)); speed_atlas = np.zeros((RNY, RNX))
    for k, (i, j) in enumerate(tiles):
        r0, c0 = (j - gj0) * T, (i - gi0) * T
        wet_atlas[r0:r0 + T, c0:c0 + T] = h[k * T:(k + 1) * T]
        speed_atlas[r0:r0 + T, c0:c0 + T] = np.hypot(u[k * T:(k + 1) * T], v[k * T:(k + 1) * T])
    captured = np.maximum(captured, (wet_atlas > 1e-6).astype(np.uint8))   # the cook's water is captured water
    reg = rt / 'region_upper_gorge'; reg.mkdir()
    np.save(reg / 'bed.npy', np.ascontiguousarray(rbed, dtype='<f8')); np.save(reg / 'captured_water_mask.npy', captured)
    region_manifest = dict(
        schema='raftsim.cooked_flow_fields.v1', coordinate_system='cartesian_east_north_m', source_elevation_datum_m=datum,
        grid=dict(nx=RNX, ny=RNY, dx_m=D, dy_m=D, origin_x_m=float(r_origin[0]), origin_y_m=float(r_origin[1])),
        solver=dict(runtime_cartesian_coupled_config=True, solver_mode='finite_volume', flux_scheme='hll', spatial_order=2,
                    fixed_dt_s=pm['dt_seconds'], cfl=.2, dry_tolerance=1.e-6, roughness_manning=roughness, roughness_scale=1.,
                    bed_slope_source_scale=1., feature_strength_scale=0., preserve_initial_mass=False),
        bands=[dict(band_id=args.band_id, discharge_target_m3s=pm['target_discharge_m3s'],
                    arrays=dict(bed=array_meta(reg / 'bed.npy', reg, '<f8'), captured_water_mask=array_meta(reg / 'captured_water_mask.npy', reg, '|u1')),
                    shared_cartesian_state=dict(manifest='../atlas/manifest.json', sha256=atlas_hash))],
        settled_hydraulics=False, normal_map_integrated=False)
    write_json(reg / 'manifest.json', region_manifest)

    # ---------------- valid live centres (every crop cell available and >= 2 cells inside the grid)
    unavailable = (captured == 1) & ~solved
    # cells beyond the physical faces are unavailable too (atlas PhysicalWetExteriorCells)
    for p in pm['boundary_probes']:
        i, j = tiles[p['tile_index']]; r0, c0 = (j - gj0) * T, (i - gi0) * T
        if p['edge'] == 'north' and r0 + T < RNY: unavailable[r0 + T, c0:c0 + T] = True
        if p['edge'] == 'south' and r0 > 0: unavailable[r0 - 1, c0:c0 + T] = True
        if p['edge'] == 'west' and c0 > 0: unavailable[r0:r0 + T, c0 - 1] = True
        if p['edge'] == 'east' and c0 + T < RNX: unavailable[r0:r0 + T, c0 + T] = True
    ps = np.pad(unavailable.astype(np.int64), ((1, 0), (1, 0))).cumsum(0).cumsum(1)

    def box_bad(r0, r1, c0, c1):
        return ps[r1 + 1, c1 + 1] - ps[r0, c1 + 1] - ps[r1 + 1, c0] + ps[r0, c0]
    half = args.live_extent_m / 2 + args.context_cells * D
    step = args.centre_step_m
    xs = np.arange(r_origin[0] + half + 3 * D, r_origin[0] + (RNX - 1) * D - half - 3 * D, step)
    ys = np.arange(r_origin[1] + half + 3 * D, r_origin[1] + (RNY - 1) * D - half - 3 * D, step)
    raft_water = (wet_atlas > 0.3)
    rects = []
    for y in ys:
        run = None
        for x in xs:
            c0 = int(np.floor((x - half - r_origin[0]) / D)) - 1; c1 = int(np.ceil((x + half - r_origin[0]) / D)) + 1
            r0 = int(np.floor((y - half - r_origin[1]) / D)) - 1; r1 = int(np.ceil((y + half - r_origin[1]) / D)) + 1
            ok = c0 >= 2 and r0 >= 2 and c1 <= RNX - 3 and r1 <= RNY - 3 and box_bad(r0, r1, c0, c1) == 0
            # only keep centres whose crop holds solved water (the raft is on the river)
            if ok:
                ci = int(round((x - r_origin[0]) / D)); ri = int(round((y - r_origin[1]) / D)); w_ = int(args.live_extent_m / 2 / D)
                ok = raft_water[max(ri - w_, 0):ri + w_, max(ci - w_, 0):ci + w_].any()
            if ok and run is None:
                run = [x, x]
            elif ok:
                run[1] = x
            if (not ok or x == xs[-1]) and run is not None:
                rects.append([float(run[0]), float(y), float(run[1]), float(y)]); run = None
    # merge vertically identical runs into taller rectangles
    merged = []
    for r in sorted(rects, key=lambda r: (r[0], r[2], r[1])):
        if merged and merged[-1][0] == r[0] and merged[-1][2] == r[2] and abs(r[1] - merged[-1][3] - step) < 1e-6:
            merged[-1][3] = r[3]
        else:
            merged.append(list(r))
    # raft coverage audit: every solved water cell with h > 0.3 m must be coverable by some centre
    covered = np.zeros_like(raft_water)
    reach = args.live_extent_m / 2 - args.raft_margin_m
    for x0_, y0_, x1_, y1_ in merged:
        c0 = int(np.floor((x0_ - reach - r_origin[0]) / D)); c1 = int(np.ceil((x1_ + reach - r_origin[0]) / D))
        r0 = int(np.floor((y0_ - reach - r_origin[1]) / D)); r1 = int(np.ceil((y1_ + reach - r_origin[1]) / D))
        covered[max(r0, 0):r1 + 1, max(c0, 0):c1 + 1] = True
    coverage = float((covered & raft_water).sum() / max(raft_water.sum(), 1))
    bounds = [float(r_origin[0]), float(r_origin[1]), float(r_origin[0] + (RNX - 1) * D), float(r_origin[1] + (RNY - 1) * D)]
    streaming = dict(schema='raftsim.cartesian_water_streaming.v1', grid_spacing_m=D, advance_m=args.advance_m, roughness_manning=roughness,
                     source_context_cells=args.context_cells, minimum_raft_interior_margin_m=args.raft_margin_m,
                     live_window_extent_m=[args.live_extent_m, args.live_extent_m],
                     windows=[dict(window_id='zambezi_upper_gorge', cooked_fields_manifest=rel(reg / 'manifest.json'),
                                   hydraulic_bounds_m=bounds, valid_live_center_bounds_m=merged)],
                     coverage=dict(raft_water_cells_coverable_share=coverage, rectangles=len(merged)),
                     settled_hydraulics=False, normal_map_integrated=False)
    write_json(rt / 'streaming_manifest.json', streaming)

    # ---------------- coordinate maps
    write_json(rt / 'coordinate_map.json', dict(
        schema='raftsim.cartesian_water_coordinate_map.v1', hydraulic_bounds_m=bounds, world_y_sign=-1, vertical_datum_m=datum,
        world_origin_utm_m=origin.tolist(), horizontal_crs='EPSG:32735 WGS 84 / UTM zone 35S',
        progress_coordinate_map=rel(rt / 'progress_coordinate_map.json'),
        notes='Hydraulic x=east, y=north relative to world origin; neither is downstream progress.',
        hydraulic_state_solved=True, normal_map_integrated=False))
    cl = np.array(json.loads((ev / 'centreline.json').read_text())['points_xy_station'])
    s_in, s_out = evm['statistics']['reach_station_m']
    sel = (cl[:, 2] >= s_in - 50) & (cl[:, 2] <= s_out + 50)
    px, py, ps_ = cl[sel, 0] - origin[0], cl[sel, 1] - origin[1], cl[sel, 2]
    # The runtime folds-check the +-256 m corridor: its edges may step at
    # most 16 m between points, i.e. ds * (256 + r) / r <= 16 at radius r.
    # The 2 m midline puts each turn at a vertex (one Batoka hairpin bends
    # at ~6 m radius), so resample at 0.25 m, smooth (sigma 3 m, <= ~1.2 m
    # shift) and keep points at most 1 m apart where the edge step allows.
    seg = np.hypot(np.diff(px), np.diff(py)); arc = np.concatenate([[0], np.cumsum(seg)])
    fine = np.arange(0, arc[-1], 0.25)
    fx, fy = np.interp(fine, arc, px), np.interp(fine, arc, py)
    ker = np.exp(-0.5 * (np.arange(-48, 49) / 12.0) ** 2); ker /= ker.sum()
    fx = np.convolve(np.pad(fx, 48, mode='edge'), ker, 'valid'); fy = np.convolve(np.pad(fy, 48, mode='edge'), ker, 'valid')
    ftx, fty = np.gradient(fx), np.gradient(fy); ftn = np.hypot(ftx, fty); ftx, fty = ftx / ftn, fty / ftn
    flx, fly = -fty, ftx

    def edge_step_between(i, j):
        return max(float(np.hypot(fx[j] - fx[i] + sgn * 256 * (flx[j] - flx[i]), fy[j] - fy[i] + sgn * 256 * (fly[j] - fly[i])))
                   for sgn in (-1, 1))
    keep = [0]
    while keep[-1] < len(fx) - 1:
        i = keep[-1]; j = min(i + 4, len(fx) - 1)
        while j > i + 1 and edge_step_between(i, j) > 12.0:
            j -= 1
        keep.append(j)
    keep = np.array(keep)
    qx, qy, tx, ty = fx[keep], fy[keep], ftx[keep], fty[keep]
    sa = np.concatenate([[0], np.cumsum(np.hypot(np.diff(qx), np.diff(qy)))])   # station = world length
    station0 = float(ps_[0])
    pts = [[float(station0 + s), float(x), float(y), float(-b), float(a)] for s, x, y, a, b in zip(sa, qx, qy, tx, ty)]
    lx, ly = -ty, tx
    edge_step = max(float(np.max(np.hypot(np.diff(qx + sgn * 256 * lx), np.diff(qy + sgn * 256 * ly)))) for sgn in (-1, 1))
    assert edge_step <= 16.0, f'progress map corridor step {edge_step:.1f} m'
    smooth_shift = float(np.max(np.hypot(fx - np.interp(fine, arc, px), fy - np.interp(fine, arc, py))))

    # Launch: the slowest midline point 40-500 m into the reach that a live
    # window can hold, is >= 1 m deep with every cell within 6 m wet, and flows
    # < 2.5 m/s (at 283 m3/s the inferred gorge runs 2-5 m/s, so "calm" is
    # relative); finish 40 m before the outflow cut. "Hold": the runtime
    # clamps the window centre into the nearest valid rectangle, and the
    # raft's stateful detail needs its whole source footprint (a square of
    # --detail-footprint-m around the raft) inside that window, so the raft
    # must lie within extent/2 - max(margin, footprint/2) (L-inf) of a
    # rectangle; 4 m spare. With imprinted observed rapid features the launch
    # is the slowest such point at least 3 m above the first feature, or, when
    # none exists, the first (most upstream) one: the slowest point further
    # down sits inside Rapid 1 (The Wall), past its head. The editor places the
    # raft and run manager at these stations
    # (RaftSimEditorLandscapeGeometry.cpp kZambeziUpperGorge*).
    def region_cell(x, y):
        return int(round((y - r_origin[1]) / D)), int(round((x - r_origin[0]) / D))
    hold_m = args.live_extent_m / 2 - max(args.raft_margin_m, args.detail_footprint_m / 2) - 4.0

    def in_rects(x, y):
        return any(max(x0 - x, x - x1, y0 - y, y - y1, 0.0) <= hold_m for x0, y0, x1, y1 in merged)
    valid = []
    for s, x, y in zip(sa + station0, qx, qy):
        if not s_in + 40.0 <= s <= s_in + 500.0:
            continue
        r, c = region_cell(x, y)
        near = wet_atlas[r - 3:r + 4, c - 3:c + 4]
        if in_rects(x, y) and wet_atlas[r, c] >= 1.0 and speed_atlas[r, c] < 2.5 and (near > 0.3).all():
            valid.append(dict(station_m=float(s), local_xy_m=[float(x), float(y)], depth_m=float(wet_atlas[r, c]),
                              speed_mps=float(speed_atlas[r, c])))
    assert valid, 'no slow, valid launch point in the first 500 m'
    feats = [f['station_m'] for f in evm.get('observed_rapid_features', {}).get('imprint', [])]
    above = [q for q in valid if not feats or q['station_m'] <= min(feats) - 3.0]
    launch = min(above, key=lambda q: q['speed_mps']) if above else min(valid, key=lambda q: q['station_m'])
    launch['rule'] = ('slowest valid point' + (' above the first observed rapid feature' if feats else '')
                      if above else 'first valid point (none above the first observed rapid feature)')
    finish_station = float(np.floor(s_out - 40.0))
    write_json(rt / 'progress_coordinate_map.json', dict(
        schema='raftsim.curved_river_coordinate_map.v1', river_id='zambezi_batoka_gorge', section_id=SECTION,
        horizontal_crs='EPSG:32735 WGS 84 / UTM zone 35S', horizontal_origin_m=origin.tolist(), world_y_sign=-1, vertical_datum_m=datum,
        purpose='run progress (station) along the low-water Sentinel-2 midline; hydraulics use the Cartesian map',
        midline_smoothing=dict(gaussian_sigma_m=3.0, max_shift_m=smooth_shift, max_point_spacing_m=1.0, point_count=len(pts),
                               stations='cumulative world length from the evidence station at the first point'),
        points=pts, corridor_edge_step_max_m=edge_step))

    # ---------------- evidence copies
    (scen / 'evidence').mkdir()
    for srcf, name in ((ev / 'manifest.json', 'evidence_manifest.json'), (ev / 'profile.json', 'evidence_profile.json'),
                       (ev / 'boulders.json', 'inferred_boulders.json'), (ev / 'centreline.json', 'evidence_centreline.json'),
                       (pk / 'manifest.json', 'cook_manifest.json'), (args.compare / 'compare.json', 'cook_compare.json'),
                       (ck / 'progress.jsonl', 'cook_progress.jsonl')):
        shutil.copyfile(srcf, scen / 'evidence' / name)
    for png in ('classes.png', 'terrain_depth.png'):
        shutil.copyfile(ev / png, scen / 'evidence' / ('evidence_' + png))
    corr = evm.get('parameters', {}).get('bed_correction')
    if corr:
        cp = next(c for c in ((args.bed_correction_file.resolve() if args.bed_correction_file else None), Path(corr), ROOT / corr)
                  if c is not None and c.is_absolute() and c.exists())
        assert sha(cp) == evm['parameters']['bed_correction_sha256']
        shutil.copyfile(cp, scen / 'evidence' / 'bed_correction.npz')

    # ---------------- terrain: Landscape heightfield (evidence surface, inferred bed in the channel)
    terr.mkdir(parents=True)
    ebed = ev_g['bed'].astype(np.float64)
    SPAN_X, SPAN_Y = float(NX), float(NY)
    jjs = np.arange(LANDSCAPE) * (SPAN_X / (LANDSCAPE - 1)); iis = np.arange(LANDSCAPE) * (SPAN_Y / (LANDSCAPE - 1))
    FX, FY = np.meshgrid(jjs - 0.5, iis - 0.5)
    height = bilinear(ebed, FX, FY)
    tmin, tmax = float(height.min()), float(height.max()); relief = tmax - tmin
    hf = np.round((height - tmin) / relief * 65535.0).astype(np.uint16)
    hf_path = terr / f'{SECTION}_heightfield_2017.png'; write_png_u16(hf_path, hf)
    # drape: Sentinel-2 true colour of the 283 m3/s date, albedo-scaled
    s2m = json.loads((SRC / 'sentinel2/fetch_manifest.json').read_text())
    item = next(i for i in s2m['items'] if i['npz'] == args.sentinel2)
    s2 = np.load(SRC / 'sentinel2' / args.sentinel2); sw = item['window_utm_m']
    s2_rgb = np.stack([s2[k].astype(np.float64) * 1e-4 - 0.1 for k in ('red', 'green', 'blue')], -1)
    s2_valid = (s2['red'] > 0) & (s2['green'] > 0) & (s2['blue'] > 0)

    def sample_colour(E, N):
        sc_ = (E - sw['xmin']) / 10.0 - 0.5; sr_ = (sw['ymax'] - N) / 10.0 - 0.5
        sat_ = np.stack([bilinear(s2_rgb[..., k], sc_, sr_) for k in range(3)], -1)
        return np.clip(sat_, 0, 1), bilinear(s2_valid.astype(np.float32), sc_, sr_) > 0.99
    E4, N4 = np.meshgrid(X0 + np.arange(0, NX, 4) + 2, Y1 - np.arange(0, NY, 4) - 2)
    s4, sv4 = sample_colour(E4, N4)
    dry4 = sv4 & ~fr[::4, ::4][:s4.shape[0], :s4.shape[1]]
    lum4 = 0.2126 * s4[..., 0] + 0.7152 * s4[..., 1] + 0.0722 * s4[..., 2]
    albedo_scale = ALBEDO_MEDIAN / max(float(np.median(lum4[dry4])), 1e-6)

    def to_albedo(sat_):
        return np.clip(sat_ * albedo_scale, 0, ALBEDO_CAP)
    DE, DN = np.meshgrid(X0 + (np.arange(DRAPE) + 0.5) * (SPAN_X / DRAPE), Y1 - (np.arange(DRAPE) + 0.5) * (SPAN_Y / DRAPE))
    s_d, sv_d = sample_colour(DE, DN)
    assert sv_d.all(), 'the Sentinel-2 window must cover the Landscape'
    alb = to_albedo(s_d)
    wr = np.clip(((np.arange(DRAPE) + 0.5) * (NY / DRAPE)).astype(int), 0, NY - 1)
    wc = np.clip(((np.arange(DRAPE) + 0.5) * (NX / DRAPE)).astype(int), 0, NX - 1)
    water_px = fr[wr][:, wc]
    cont = np.zeros_like(alb)
    for k in range(3):
        cont[..., k] = smooth_fill(alb[..., k], ~water_px, 16, iters=400)[0]
    alb = np.where(water_px[..., None], cont * WET_BED_DARKENING ** 2.2, alb)
    drape_path = terr / f'{SECTION}_drape_{DRAPE}.png'
    write_png_rgb(drape_path, np.round(np.clip(alb, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8))
    # backdrop: GLO-30 around the window
    bx0 = float(np.floor((X0 - BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    bx1 = float(np.ceil((X0 + SPAN_X + BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    by0 = float(np.floor((Y1 - SPAN_Y - BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    by1 = float(np.ceil((Y1 + BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    BW, BH = int((bx1 - bx0) / BACKDROP_CELL), int((by1 - by0) / BACKDROP_CELL)
    BE, BN = np.meshgrid(bx0 + (np.arange(BW) + 0.5) * BACKDROP_CELL, by1 - (np.arange(BH) + 0.5) * BACKDROP_CELL)
    dem_g, lon0, lat0, stp = load_glo30()
    lon, lat = tm_inverse(BE, BN, UTM35S)
    z3 = catmull_rom(dem_g, (lat0 - lat) / stp, (lon - lon0) / stp)
    del dem_g
    under = (BE > X0) & (BE < X0 + SPAN_X) & (BN > Y1 - SPAN_Y) & (BN < Y1)
    inside = ((BE > X0 + BACKDROP_RING_M) & (BE < X0 + SPAN_X - BACKDROP_RING_M)
              & (BN > Y1 - SPAN_Y + BACKDROP_RING_M) & (BN < Y1 - BACKDROP_RING_M))
    land_here = bilinear(ebed, BE - X0 - 0.5, Y1 - BN - 0.5)
    land_lo = np.full(z3.shape, np.inf)
    for i_, j_ in zip(*np.nonzero(inside)):
        c0 = int(max(BE[i_, j_] - X0 - 25, 0)); c1 = int(min(BE[i_, j_] - X0 + 25, NX))
        r0 = int(max(Y1 - BN[i_, j_] - 25, 0)); r1 = int(min(Y1 - BN[i_, j_] + 25, NY))
        land_lo[i_, j_] = ebed[r0:r1, c0:c1].min()
    z3 = np.where(under & ~inside, np.minimum(z3, land_here) - BACKDROP_RING_DROP_M, z3)
    z3 = np.where(inside, np.minimum(z3, land_lo) - BACKDROP_MARGIN_M, z3)
    idx = np.arange(BH * BW).reshape(BH, BW)
    a_, b_, c_, d_ = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]
    quad = ~(inside[:-1, :-1] & inside[:-1, 1:] & inside[1:, :-1] & inside[1:, 1:])
    tri = np.concatenate([np.stack([a_[quad], b_[quad], c_[quad]], 1), np.stack([b_[quad], d_[quad], c_[quad]], 1)])
    e0, n0 = float(BE[0, 0]), float(BN[0, 0])
    xyz_all = np.stack([(BE - e0).ravel(), (BN - n0).ravel(), (z3 - datum).ravel()], 1)
    used = np.zeros(len(xyz_all), bool); used[tri.ravel()] = True
    remap = -np.ones(len(xyz_all), np.int64); remap[used] = np.arange(int(used.sum()))
    xyz_b = xyz_all[used]; tri_b = remap[tri]
    backdrop_path = terr / f'{SECTION}_backdrop_glo30_20m.npz'
    np.savez_compressed(backdrop_path, xyz_local_m=xyz_b, triangles=tri_b)
    BDE, BDN = np.meshgrid(bx0 + (np.arange(BACKDROP_DRAPE) + 0.5) * ((bx1 - bx0) / BACKDROP_DRAPE),
                           by1 - (np.arange(BACKDROP_DRAPE) + 0.5) * ((by1 - by0) / BACKDROP_DRAPE))
    s_b, sv_b = sample_colour(BDE, BDN)
    bdrape_path = terr / f'{SECTION}_backdrop_drape_{BACKDROP_DRAPE}.png'
    write_png_rgb(bdrape_path, np.round(np.clip(to_albedo(s_b), 0, 1) ** (1 / 2.2) * 255).astype(np.uint8))
    # local centreline for the editor (Unreal frame, conditioned surface = cooked median)
    prof = json.loads((ev / 'profile.json').read_text())
    comp_prof = np.load(args.compare / 'profiles.npz')
    surf = np.interp(sa + station0, comp_prof['station'][np.isfinite(comp_prof['cook_median'])],
                     comp_prof['cook_median'][np.isfinite(comp_prof['cook_median'])])
    bedc = surf - np.interp(sa + station0, prof['station_center_m'], np.nan_to_num(prof['normal_depth_m'], nan=1.0))
    clj = dict(schema='raftsim.local_centerline.v1', river_id='zambezi_batoka_gorge', section_id=SECTION,
               local_metric_policy=f'Unreal frame: X = (E - {X0:.0f}) m * 100, Y = ({Y1:.0f} - N) m * 100 from the Landscape north-west corner; '
                                   'E/N EPSG:32735 UTM 35S; heights EGM2008',
               points=[dict(station_m=float(s + station0), unreal_local_cm=[float((x + origin[0] - X0) * 100), float((Y1 - (y + origin[1])) * 100)],
                            conditioned_visual_surface_elevation_m=float(zs), conditioned_visual_bed_elevation_m=float(zb),
                            conditioned_visual_surface_normalized=float((zs - tmin) / relief),
                            conditioned_visual_bed_normalized=float((zb - tmin) / relief))
                       for s, x, y, zs, zb in zip(sa[::2], qx[::2], qy[::2], surf[::2], bedc[::2])])
    cl_path = terr / f'{SECTION}_local_centerline.json'; cl_path.write_text(json.dumps(clj, indent=1) + '\n')
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    tm = dict(schema='raftsim.zambezi.upper_gorge_evidence_terrain.v1', status='evidence_based_reconstruction_glo30_terrain_inferred_bed',
              river_id='zambezi_batoka_gorge', section_id=SECTION, source_commit=git,
              inputs=dict(evidence_grid_sha256=sha(ev / 'evidence_grid.npz'), sources_manifest=rel(SRC / 'manifest.json'),
                          sources_manifest_sha256=sha(SRC / 'manifest.json'),
                          sentinel2=dict(npz=args.sentinel2, sha256=item['npz_sha256'], datetime=item['datetime']), glo30=evm['inputs']['glo30']),
              outputs=dict(heightfield=rel(hf_path), heightfield_sha256=sha(hf_path), drape=rel(drape_path), drape_sha256=sha(drape_path),
                           local_centerline=rel(cl_path), local_centerline_sha256=sha(cl_path),
                           backdrop_mesh=rel(backdrop_path), backdrop_mesh_sha256=sha(backdrop_path),
                           backdrop_drape=rel(bdrape_path), backdrop_drape_sha256=sha(bdrape_path)),
              landscape=dict(size_px=LANDSCAPE, pixel_format='16_bit_grayscale_png', north_up=True, horizontal_span_x_m=SPAN_X, horizontal_span_y_m=SPAN_Y,
                             sample_spacing_x_m=SPAN_X / (LANDSCAPE - 1), sample_spacing_y_m=SPAN_Y / (LANDSCAPE - 1),
                             terrain_min_m=tmin, terrain_max_m=tmax, target_relief_cm=relief * 100.0,
                             world_vertical_offset_cm=(tmin - datum) * 100.0, runtime_vertical_datum_m=datum,
                             world_origin_epsg32735_m=dict(west_edge_e=X0, centre_n=float(origin[1])), world_min_x_cm=0.0),
              drape=dict(size_px=[DRAPE, DRAPE], source='Sentinel-2 L2A true colour at 10 m (' + item['datetime'][:10] + ', 283 m3/s), bilinear',
                         under_water=f'Sentinel-2 low-water extent replaced by the continuation of dry-bank colours x {WET_BED_DARKENING} (invented bed colour)',
                         albedo_median=ALBEDO_MEDIAN, albedo_cap=ALBEDO_CAP, albedo_scale=float(albedo_scale),
                         uv=f'U = world_x / {SPAN_X * 100:.0f} cm; V = (world_y + {SPAN_Y * 50:.0f}) / {SPAN_Y * 100:.0f} cm (north up)'),
              backdrop=dict(mesh=rel(backdrop_path), vertices=int(len(xyz_b)), triangles=int(len(tri_b)), spacing_m=BACKDROP_CELL,
                            source=f'Copernicus GLO-30 (bicubic) on a {BACKDROP_CELL:.0f} m UTM grid, {BACKDROP_EXTENT_M:.0f} m around the Landscape',
                            origin_epsg32735_m=[e0, n0], xyz='local metres east, north, height - datum from origin',
                            actor_translation_cm=[(e0 - origin[0]) * 100.0, -(n0 - origin[1]) * 100.0, 0.0], actor_scale=[1.0, -1.0, 1.0],
                            expected_mesh_bounds_cm=[(xyz_b.min(0) * 100).tolist(), (xyz_b.max(0) * 100).tolist()],
                            drape=dict(file=rel(bdrape_path), size_px=[BACKDROP_DRAPE, BACKDROP_DRAPE], north_up=True,
                                       uv=f'U = (world_x + {(origin[0] - bx0) * 100:.0f}) / {(bx1 - bx0) * 100:.0f} cm; '
                                          f'V = (world_y + {(by1 - origin[1]) * 100:.0f}) / {(by1 - by0) * 100:.0f} cm'),
                            collision=False),
              water=dict(coordinate_map=rel(rt / 'coordinate_map.json'), progress_coordinate_map=rel(rt / 'progress_coordinate_map.json'),
                         streaming_manifest=rel(rt / 'streaming_manifest.json'), atlas_manifest=rel(atlas_dir / 'manifest.json'),
                         region_manifest=rel(reg / 'manifest.json'), live_window_extent_m=args.live_extent_m, grid_spacing_m=D,
                         valid_centre_rectangles=len(merged), raft_water_coverable_share=coverage,
                         launch=launch, finish_station_m=finish_station))
    write_json(terr / f'{SECTION}_terrain_manifest.json', tm)
    print(json.dumps(dict(landscape={k: tm['landscape'][k] for k in ('target_relief_cm', 'world_vertical_offset_cm')},
                          region=[RNX, RNY], rectangles=len(merged), coverage=coverage, progress_edge_step=edge_step,
                          launch=launch, finish_station_m=finish_station,
                          backdrop=tm['backdrop']['actor_translation_cm'], albedo_scale=float(albedo_scale)), indent=1))


if __name__ == '__main__':
    main()
