"""Re-export the Zambezi upper-gorge Landscape from a wall-reconstructed evidence grid (numpy only).

    export_zambezi_gorge_wall_terrain.py <walls_evidence_dir>

<walls_evidence_dir> is reconstruct_zambezi_gorge_walls.py output (an evidence
grid whose dry ground carries the reconstructed basalt walls, class 6, and a
wall_zone raster). This replaces, in terrain/upper_gorge_evidence_2025/:

* the 2017^2 Landscape heightfield, sampled exactly as
  export_zambezi_evidence_runtime.py does (bilinear of the grid's terrain),
  clamped to the committed terrain range so the Landscape relief and vertical
  offset (and the editor catalogue constants that mirror them) are unchanged;
* the drape: the committed Sentinel-2 drape recoloured where the walls were
  reconstructed, since 10 m top-down colour cannot show a near-vertical face:
  cliffs dark basalt (observed "black to dark-grey basalt", weathered rust
  streaks), talus grey-brown rubble mixed with the image colour (it carries
  woodland), beaches pale sand. Inferred colour, labelled;
* the GLO-30 backdrop, re-lowered under the new Landscape edge as the exporter
  does (it never shows through the Landscape).

The water, atlas, coordinate maps, centreline and launch are unchanged: the
walls change dry ground only. The terrain manifest's outputs, input evidence
hash and a gorge_walls record are updated.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from build_futaleufu_evidence_grid import catmull_rom  # noqa: E402
from build_zambezi_evidence_grid import UTM35S, load_glo30  # noqa: E402
from export_hance_evidence_runtime import bilinear, write_png_rgb, write_png_u16  # noqa: E402
from export_zambezi_evidence_runtime import (BACKDROP_CELL, BACKDROP_EXTENT_M, BACKDROP_MARGIN_M,  # noqa: E402
                                             BACKDROP_RING_DROP_M, BACKDROP_RING_M, DRAPE, LANDSCAPE, SECTION)
from geo_frames import tm_inverse  # noqa: E402
from png_numpy import read_png  # noqa: E402

DATA = ROOT / 'physics/data/real_world/zambezi_batoka_gorge'
TERR = DATA / f'terrain/{SECTION}'
SEED = 20261002


def replace_via(path, writer, data):
    """Write beside the target and rename: truncating a tracked file in place fails on
    Windows while another process (an editor, an indexer) has it mapped."""
    tmp = Path(str(path) + '.tmp' + Path(path).suffix)
    writer(tmp, data)
    os.replace(tmp, path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()


def noise2(shape, scale, seed):
    rng = np.random.default_rng(seed)
    H, W = shape
    lat = rng.uniform(-1, 1, (int(H / scale) + 3, int(W / scale) + 3))
    r, c = np.mgrid[0:H, 0:W] / scale
    i, j = np.floor(r).astype(int), np.floor(c).astype(int)
    fr, fc = (1 - np.cos(np.pi * (r - i))) / 2, (1 - np.cos(np.pi * (c - j))) / 2
    return ((lat[i, j] * (1 - fc) + lat[i, j + 1] * fc) * (1 - fr) + (lat[i + 1, j] * (1 - fc) + lat[i + 1, j + 1] * fc) * fr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('walls', type=Path)
    args = ap.parse_args()
    wm = json.loads((args.walls / 'manifest.json').read_text(encoding='utf-8'))
    assert 'gorge_walls' in wm, 'not a reconstruct_zambezi_gorge_walls.py output'
    tm_path = TERR / f'{SECTION}_terrain_manifest.json'
    tm = json.loads(tm_path.read_text())
    ev = np.load(args.walls / 'evidence_grid.npz')
    X0, Y1, NX, NY = wm['grid']['x0'], wm['grid']['y_top'], wm['grid']['nx'], wm['grid']['ny']
    land = tm['landscape']
    assert (land['horizontal_span_x_m'], land['horizontal_span_y_m']) == (float(NX), float(NY))
    tmin, tmax = land['terrain_min_m'], land['terrain_max_m']; relief = tmax - tmin
    datum = land['runtime_vertical_datum_m']

    # ---------------- heightfield (same sampling as the exporter), committed range
    ebed = ev['bed'].astype(np.float64)
    jjs = np.arange(LANDSCAPE) * (NX / (LANDSCAPE - 1)); iis = np.arange(LANDSCAPE) * (NY / (LANDSCAPE - 1))
    FX, FY = np.meshgrid(jjs - 0.5, iis - 0.5)
    height = bilinear(ebed, FX, FY)
    clamped = int(((height < tmin) | (height > tmax)).sum())
    height = np.clip(height, tmin, tmax)
    hf = np.round((height - tmin) / relief * 65535.0).astype(np.uint16)
    hf_path = TERR / f'{SECTION}_heightfield_2017.png'
    replace_via(hf_path, write_png_u16, hf)

    # ---------------- drape recolour on the reconstructed walls
    drape_path = TERR / f'{SECTION}_drape_{DRAPE}.png'
    img = read_png(drape_path).astype(np.float64) / 255.0
    alb = img[..., :3] ** 2.2
    wr = np.clip(((np.arange(DRAPE) + 0.5) * (NY / DRAPE)).astype(int), 0, NY - 1)
    wc = np.clip(((np.arange(DRAPE) + 0.5) * (NX / DRAPE)).astype(int), 0, NX - 1)
    zone = ev['wall_zone'][wr][:, wc]
    # slope of the new terrain at the drape pixels (m/m): faces vs ledges
    gy, gx = np.gradient(ebed)
    slope = np.hypot(gx, gy)[wr][:, wc]
    # A near-vertical face samples a ~1 m strip of a top-down drape over its
    # whole height, so any pixel-scale noise is stretched into blocks down
    # the face: cliffs get one dark basalt tone varying only over tens of
    # metres along the wall, and the geometry's ledges carry the banding.
    n_lo = noise2((DRAPE, DRAPE), 40.0, SEED); n_hi = noise2((DRAPE, DRAPE), 2.5, SEED + 1)
    streak = np.clip(noise2((DRAPE, DRAPE), 60.0, SEED + 2), 0, 1) ** 2   # weathered rust staining
    basalt = np.stack([0.050, 0.048, 0.046]) * (1.0 + 0.15 * n_lo[..., None])
    rust = np.stack([0.085, 0.060, 0.044])
    cliff_col = basalt * (1 - 0.25 * streak[..., None]) + rust * 0.25 * streak[..., None]
    rubble = np.stack([0.080, 0.074, 0.066]) * (1.0 + 0.20 * n_hi[..., None])
    sand = np.stack([0.30, 0.27, 0.22]) * (1.0 + 0.08 * n_hi[..., None])
    out = alb.copy()
    out = np.where((zone == 3)[..., None], cliff_col, out)
    out = np.where((zone == 2)[..., None], 0.75 * rubble + 0.25 * alb, out)
    out = np.where((zone == 4)[..., None], 0.55 * alb + 0.45 * basalt, out)
    # The face of a near-vertical wall stretches each drape pixel of its ~10 m
    # footprint over tens of metres of height, so any step between the cliff,
    # talus and rim colours shows as blocks down the face (second survey):
    # blur the colour across the whole wall zone so it varies only smoothly.
    walls = (zone >= 2)
    k = 5
    pad = np.pad(out, ((k, k), (k, k), (0, 0)), mode='edge')
    c = np.pad(pad.cumsum(0).cumsum(1), ((1, 0), (1, 0), (0, 0)))
    n = 2 * k + 1
    blurred = (c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]) / (n * n)
    out = np.where(walls[..., None], blurred, out)
    out = np.where((zone == 1)[..., None], sand, out)
    replace_via(drape_path, write_png_rgb, np.round(np.clip(out, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8))

    # ---------------- backdrop: GLO-30 lowered under the new Landscape edge (as the exporter)
    origin_n = land['world_origin_epsg32735_m']['centre_n']
    bx0 = float(np.floor((X0 - BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    bx1 = float(np.ceil((X0 + NX + BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    by0 = float(np.floor((Y1 - NY - BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    by1 = float(np.ceil((Y1 + BACKDROP_EXTENT_M) / BACKDROP_CELL) * BACKDROP_CELL)
    BW, BH = int((bx1 - bx0) / BACKDROP_CELL), int((by1 - by0) / BACKDROP_CELL)
    BE, BN = np.meshgrid(bx0 + (np.arange(BW) + 0.5) * BACKDROP_CELL, by1 - (np.arange(BH) + 0.5) * BACKDROP_CELL)
    dem_g, lon0, lat0, stp = load_glo30()
    lon, lat = tm_inverse(BE, BN, UTM35S)
    z3 = catmull_rom(dem_g, (lat0 - lat) / stp, (lon - lon0) / stp)
    del dem_g
    under = (BE > X0) & (BE < X0 + NX) & (BN > Y1 - NY) & (BN < Y1)
    inside = ((BE > X0 + BACKDROP_RING_M) & (BE < X0 + NX - BACKDROP_RING_M)
              & (BN > Y1 - NY + BACKDROP_RING_M) & (BN < Y1 - BACKDROP_RING_M))
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
    backdrop_path = TERR / f'{SECTION}_backdrop_glo30_20m.npz'
    assert tm['backdrop']['origin_epsg32735_m'] == [e0, n0] and tm['backdrop']['vertices'] == len(xyz_b)
    replace_via(backdrop_path, lambda f, d: np.savez_compressed(f, **d), dict(xyz_local_m=xyz_b, triangles=tri_b))

    # ---------------- manifest
    tm['status'] = 'evidence_based_reconstruction_glo30_terrain_inferred_bed_observation_reconstructed_walls'
    tm['inputs']['evidence_grid_sha256'] = sha(args.walls / 'evidence_grid.npz')
    tm['outputs'].update(heightfield_sha256=sha(hf_path), drape_sha256=sha(drape_path), backdrop_mesh_sha256=sha(backdrop_path))
    tm['backdrop']['expected_mesh_bounds_cm'] = [(xyz_b.min(0) * 100).tolist(), (xyz_b.max(0) * 100).tolist()]
    tm['drape']['walls'] = ('reconstructed walls recoloured (inferred colour): cliffs one dark basalt tone varying over tens of '
                            'metres with rust staining (no pixel-scale noise, which a vertical face stretches into blocks), talus 75 % '
                            'dark rubble over the image colour, the rim blend 45 % basalt, all blurred over 11 px across the wall '
                            'zone (a vertical face stretches pixel steps into blocks), beaches pale sand')
    gw = wm['gorge_walls']
    tm['gorge_walls'] = dict(generator=gw['generator'], exporter='physics/scripts/export_zambezi_gorge_wall_terrain.py',
                             method=gw['method'], observations=gw['observations'], parameters=gw['parameters'],
                             beaches=gw['beaches'], statistics=gw['statistics'], heightfield_samples_clamped_to_committed_range=clamped,
                             hydraulics_changed=False)
    replace_via(tm_path, lambda f, d: Path(f).write_text(d), json.dumps(tm, indent=2) + '\n')
    print(json.dumps(dict(clamped=clamped, zone_px={str(z): int((zone == z).sum()) for z in (1, 2, 3, 4)},
                          backdrop_vertices=len(xyz_b)), indent=1))


if __name__ == '__main__':
    main()
