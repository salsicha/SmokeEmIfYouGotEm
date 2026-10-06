"""Reconstruct the Batoka basalt gorge walls of the Zambezi upper-gorge evidence grid (numpy only).

    reconstruct_zambezi_gorge_walls.py <evidence_dir> <out_dir> [--observations obs.json]

Why: Copernicus GLO-30 (30 m radar, edited water) cannot resolve the gorge's
walls. Over the reach it is flat at water level for 40-60 m beside the
Sentinel-2 water, then rises smoothly 85-115 m to the rim over another
60-100 m. build_zambezi_evidence_grid.py raised a 6 m wall at the wet edge to
stop the cook flooding that flat, which leaves a flat 60 m shelf at +6 m along
both banks and smooth radar slopes above it: no cliffs, banding or talus.

Observations (upper_gorge_observations_2026_09_29.json, banks_terrain_vegetation):
near-vertical black to dark-grey basalt walls about 100-120 m high with
horizontal lava-flow banding, a bare scoured band of basalt and boulders at the
waterline, talus aprons carrying woodland, and a few small pale beaches.

What GLO-30 still measures well is the rim height (the gorge depth D above the
water) and where the smeared wall crosses mid-height (d_mid, the distance from
the water edge). A blur of a step keeps the step's position at its mid-height,
so the cliff is placed there. For every dry cell within --reach-m of the water,
with the distance d to the nearest Sentinel-2 water cell and that cell's water
surface and station:

  * d <= the existing wall width (6 m): unchanged (the cook's bank);
  * talus apron from +6 m at --talus-deg up to T = --talus-share x D, then a
    gentle --shoulder-deg rise to the cliff foot;
  * the cliff: lava-flow units of --bench-m (varied) height, each a
    --face-deg face and a --ledge-m ledge, from the talus top to the rim, placed
    so its mid-height lies at d_mid (smoothed along station, with a bounded
    deterministic wander for buttresses and embayments);
  * above the rim the terrain blends back to GLO-30 over --rim-blend-m;
  * beaches: where the observations place a beach (station, side), the first
    --beach-width-m slope gently from +0.6 m instead (pale sand in the drape).

D and d_mid come from GLO-30 per 25 m of station and side (river left = lateral
> 0, Zambia), smoothed over 150 m. Only dry ground (class 0) changes; the water,
the inferred bed, measured inputs and the cook's bank band are untouched. Every
changed cell is labelled class 6: "gorge wall reconstructed from observations
over the GLO-30 rim and mid-height (shape inferred)".

Writes <out_dir>/evidence_grid.npz (the evidence grid with bed/dem/dem2021 and
class_code updated, plus 'wall_zone': 0 none, 1 scoured band/beach, 2 talus,
3 cliff, 4 rim blend) and <out_dir>/manifest.json (the input manifest plus a
'gorge_walls' record with parameters, statistics and per-bin D and d_mid).
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

from build_pacuare_evidence_grid import box_mean

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261001


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def nearest_wet(wet):
    """Exact-ish Euclidean distance and the index of the nearest wet cell, by
    propagating source coordinates over 8-neighbour sweeps until stable."""
    H, W = wet.shape
    R, C = np.mgrid[0:H, 0:W]
    sr = np.where(wet, R, -1).astype(np.int32); sc = np.where(wet, C, -1).astype(np.int32)
    d = np.where(wet, 0.0, np.inf)
    for _ in range(600):
        changed = False
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            rs = slice(max(dr, 0), H + min(dr, 0)); rd = slice(max(-dr, 0), H + min(-dr, 0))
            cs = slice(max(dc, 0), W + min(dc, 0)); cd = slice(max(-dc, 0), W + min(-dc, 0))
            cr = np.full((H, W), -1, np.int32); ccn = np.full((H, W), -1, np.int32)
            cr[rd, cd] = sr[rs, cs]; ccn[rd, cd] = sc[rs, cs]
            ok = cr >= 0
            nd = np.where(ok, np.hypot(R - cr, C - ccn), np.inf)
            b = nd < d - 1e-9
            if b.any():
                changed = True
                d = np.where(b, nd, d); sr = np.where(b, cr, sr); sc = np.where(b, ccn, sc)
        if not changed:
            break
    return d, sr, sc


def max_filter(a, r):
    """Square maximum filter of radius r cells (separable shifts)."""
    out = a.copy()
    for axis in (0, 1):
        src = out.copy()
        n = src.shape[axis]
        for k in range(1, r + 1):
            lo = [slice(None)] * 2; hi = [slice(None)] * 2
            lo[axis] = slice(0, n - k); hi[axis] = slice(k, n)
            out[tuple(lo)] = np.maximum(out[tuple(lo)], src[tuple(hi)])
            out[tuple(hi)] = np.maximum(out[tuple(hi)], src[tuple(lo)])
    return out


def smooth1d(v, ok, window):
    """Mean over a moving window of the valid entries; gaps filled by interpolation."""
    v = np.where(ok, v, 0.0); w = ok.astype(float)
    k = np.ones(window) / window
    num = np.convolve(v, k, mode='same'); den = np.convolve(w, k, mode='same')
    out = np.where(den > 1e-6, num / np.maximum(den, 1e-6), np.nan)
    idx = np.arange(len(out)); good = np.isfinite(out)
    return np.interp(idx, idx[good], out[good]) if good.any() else out


def value_noise(x, scale, seed):
    """Smooth deterministic 1-D noise in [-1, 1] (cosine-interpolated lattice)."""
    rng = np.random.default_rng(seed)
    n = int(np.nanmax(x) / scale) + 3
    lat = rng.uniform(-1.0, 1.0, n)
    t = np.clip(x / scale, 0, n - 2)
    i = np.floor(t).astype(int); f = t - i
    f = (1 - np.cos(np.pi * f)) / 2
    return lat[i] * (1 - f) + lat[i + 1] * f


def value_noise2(r, c, scale, seed):
    """Smooth deterministic 2-D noise in [-1, 1] on the grid."""
    rng = np.random.default_rng(seed)
    nr = int(r.max() / scale) + 3; nc = int(c.max() / scale) + 3
    lat = rng.uniform(-1.0, 1.0, (nr, nc))
    tr = r / scale; tc = c / scale
    i = np.floor(tr).astype(int); j = np.floor(tc).astype(int)
    fr = (1 - np.cos(np.pi * (tr - i))) / 2; fc = (1 - np.cos(np.pi * (tc - j))) / 2
    return ((lat[i, j] * (1 - fc) + lat[i, j + 1] * fc) * (1 - fr) +
            (lat[i + 1, j] * (1 - fc) + lat[i + 1, j + 1] * fc) * fr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--observations', type=Path,
                    default=ROOT / 'physics/data/real_world/zambezi_batoka_gorge/observed_rapids/upper_gorge_observations_2026_09_29.json')
    ap.add_argument('--reach-m', type=float, default=240.0)
    ap.add_argument('--band-m', type=float, default=6.0, help='the cook bank width that stays unchanged')
    ap.add_argument('--talus-deg', type=float, default=36.0)
    ap.add_argument('--talus-share', type=float, default=0.35, help='talus top as a share of the gorge depth')
    ap.add_argument('--shoulder-deg', type=float, default=14.0, help='rise from the talus top to the cliff foot')
    ap.add_argument('--face-deg', type=float, default=84.0)
    ap.add_argument('--bench-m', type=float, default=13.0, help='mean lava-flow unit height')
    ap.add_argument('--ledge-m', type=float, default=1.8)
    ap.add_argument('--wander-m', type=float, default=7.0, help='bounded cliff-line wander (buttresses, embayments)')
    ap.add_argument('--rim-blend-m', type=float, default=25.0)
    ap.add_argument('--bin-m', type=float, default=25.0)
    ap.add_argument('--smooth-m', type=float, default=150.0)
    ap.add_argument('--beach-width-m', type=float, default=16.0)
    ap.add_argument('--beach-length-m', type=float, default=45.0)
    ap.add_argument('--param-smooth-m', type=float, default=21.0, help='box over which the profile parameters are smoothed')
    ap.add_argument('--plateau-radius-m', type=int, default=40, help='the cliff tops out at the GLO-30 maximum within this radius')
    ap.add_argument('--distance-cache', type=Path, help='optional .npz cache of the distance transform')
    args = ap.parse_args()
    out = args.out.resolve()
    assert not out.exists(), 'fresh output folder required'
    ev = dict(np.load(args.evidence / 'evidence_grid.npz'))
    manifest = json.loads((args.evidence / 'manifest.json').read_text(encoding='utf-8'))
    wet = ev['river'] | ev['channel']
    G = ev['glo30'].astype(np.float64); bed = ev['bed'].astype(np.float64)
    ws = ev['ws'].astype(np.float64); st = ev['station'].astype(np.float64); lat = ev['lateral'].astype(np.float64)
    H, W = wet.shape
    if args.distance_cache and args.distance_cache.exists():
        cache = np.load(args.distance_cache)
        assert cache['river_sha256'].item() == hashlib.sha256(ev['river'].tobytes()).hexdigest()
        d, sr, sc = cache['d'], cache['sr'], cache['sc']
    else:
        d, sr, sc = nearest_wet(ev['river'])      # distance to the Sentinel-2 water (the wall reference)
        if args.distance_cache:
            np.savez(args.distance_cache, d=d, sr=sr, sc=sc,
                     river_sha256=np.array(hashlib.sha256(ev['river'].tobytes()).hexdigest()))
    srr = np.clip(sr, 0, H - 1); scc = np.clip(sc, 0, W - 1)
    ws_n = ws[srr, scc]; st_n = st[srr, scc]
    side = np.where(np.isfinite(lat), np.sign(lat), 0.0)   # +1 river left (Zambia), -1 river right
    ok_cell = (~wet) & np.isfinite(ws_n) & np.isfinite(st_n) & (side != 0) & (ev['class_code'] == 0)

    # ---------------- per (station bin, side): gorge depth D and the wall's mid-height distance d_mid
    rel = G - ws_n
    nb = int(np.nanmax(st_n[ok_cell]) // args.bin_m) + 1
    D = np.full((2, nb), np.nan); dmid = np.full((2, nb), np.nan)
    b_idx = np.clip((st_n // args.bin_m).astype(int), 0, nb - 1)
    dist_steps = np.arange(0.0, args.reach_m + 1.0, 2.0)
    for s_i, sgn in enumerate((1.0, -1.0)):
        m_side = ok_cell & (side == sgn) & (d <= args.reach_m + 10)
        for b in range(nb):
            m = m_side & (b_idx == b)
            if m.sum() < 400:
                continue
            dd = d[m]; rr = rel[m]
            far = (dd >= 60) & (dd <= args.reach_m)
            if far.sum() < 50:
                continue
            Db = float(np.percentile(rr[far], 90))
            prof = np.array([np.median(rr[np.abs(dd - x) < 2.0]) if (np.abs(dd - x) < 2.0).sum() >= 8 else np.nan
                             for x in dist_steps])
            good = np.isfinite(prof)
            if good.sum() < 10:
                continue
            prof = np.maximum.accumulate(np.interp(dist_steps, dist_steps[good], prof[good]))
            cross = np.nonzero(prof >= 0.5 * Db)[0]
            if not len(cross):
                continue
            D[s_i, b] = Db; dmid[s_i, b] = dist_steps[cross[0]]
    win = max(int(round(args.smooth_m / args.bin_m)), 1)
    Ds = np.vstack([np.clip(smooth1d(D[i], np.isfinite(D[i]), win), 40.0, 125.0) for i in range(2)])
    dms = np.vstack([np.clip(smooth1d(dmid[i], np.isfinite(dmid[i]), win), 18.0, 160.0) for i in range(2)])

    # ---------------- profile per cell (interpolated along station between bins)
    s_f = np.clip(st_n / args.bin_m - 0.5, 0, nb - 1)
    s0 = np.floor(s_f).astype(int); s1 = np.minimum(s0 + 1, nb - 1); fa = s_f - s0
    si = np.where(side > 0, 0, 1)
    Dc = Ds[si, s0] * (1 - fa) + Ds[si, s1] * fa
    dmc = dms[si, s0] * (1 - fa) + dms[si, s1] * fa
    # bounded wander of the cliff line along the wall (station and side) and a
    # 2-D component so neighbouring gullies and buttresses differ
    R_, C_ = np.mgrid[0:H, 0:W]
    wander = (args.wander_m * (0.7 * value_noise(np.nan_to_num(st_n) + 5000.0 * (side > 0), 70.0, SEED)
                               + 0.3 * value_noise2(R_.astype(float), C_.astype(float), 23.0, SEED + 1)))
    dmc = np.maximum(dmc + wander, args.band_m + 8.0)
    bench = args.bench_m * (1.0 + 0.3 * value_noise(np.nan_to_num(st_n) + 900.0 * side, 260.0, SEED + 2))
    # The nearest water cell (and with it the station, side and water surface)
    # switches abruptly along Voronoi edges between water cells, at hairpins
    # and across peninsulas; smooth every profile parameter over the dry
    # ground so those switches leave no straight seams in the walls.
    r_s = int(round(args.param_smooth_m / 2.0))
    wgt = ok_cell.astype(np.float64)

    def wsmooth(a):
        num = box_mean(np.where(ok_cell, np.nan_to_num(a), 0.0), r_s); den = box_mean(wgt, r_s)
        return np.where(den > 1e-6, num / np.maximum(den, 1e-6), a)
    ws_p = wsmooth(ws_n); Dc = wsmooth(Dc); dmc = wsmooth(dmc); bench = wsmooth(bench)
    # The cliff tops out at the local plateau: the bin depth D is a 90th
    # percentile over 60-240 m, so where GLO-30 is lower just beyond the rim
    # (side gorges, the peninsulas) a cliff to D would stand as a lip above it.
    Dc = np.maximum(np.minimum(Dc, wsmooth(max_filter(G, args.plateau_radius_m)) - ws_p), 20.0)
    T = np.clip(args.talus_share * Dc, 14.0, 55.0)
    tt = np.tan(np.radians(args.talus_deg)); tf = np.tan(np.radians(args.face_deg))
    face_w = bench / tf; period = face_w + args.ledge_m
    mean_slope = bench / period
    d_base = dmc - (0.5 * Dc - T) / mean_slope
    # talus at --talus-deg to its top T, then a gentle --shoulder-deg rise to
    # the cliff foot (a flat shelf along the wall read as a terrace)
    d_talus_top = args.band_m + (T - args.band_m) / tt
    talus = np.where(d < d_talus_top, args.band_m + tt * (d - args.band_m),
                     T + np.tan(np.radians(args.shoulder_deg)) * (d - d_talus_top))
    u = np.maximum(d - d_base, 0.0) / period
    k = np.floor(u); f = (u - k) * period
    cliff = T + bench * (k + np.minimum(f / face_w, 1.0))
    cliff = np.where(d >= d_base, cliff, -np.inf)
    prof = np.minimum(np.maximum(talus, cliff), Dc)
    zone = np.where(cliff > talus, 3, 2)
    # talus roughness: blocky rubble, +-0.5 m, fading out near the bank band
    rough = 0.5 * value_noise2(R_.astype(float), C_.astype(float), 3.0, SEED + 3) * np.clip((d - args.band_m) / 6.0, 0, 1)
    prof = np.where(zone == 2, prof + rough, prof)
    # rim: blend back to GLO-30 above the rim (where the cliff reaches D), and
    # in any case before the edge of the reconstructed band
    d_rim = d_base + np.ceil((Dc - T) / bench) * period
    blend = np.clip((d - d_rim) / args.rim_blend_m, 0.0, 1.0)
    taper = np.clip((d - (args.reach_m - 45.0)) / 40.0, 0.0, 1.0)
    new = ws_p + prof
    new = np.where(d > d_rim, (1 - blend) * (ws_p + Dc) + blend * G, new)
    new = (1 - taper) * new + taper * G
    zone = np.where((d > d_rim) | (taper > 0), 4, zone)

    # ---------------- beaches from the observations
    # upper_gorge_observations_2026_09_29 (banks_terrain_vegetation): "pale
    # patches at about 790 L, 2000 L, 2850 R and 3170 R"
    beaches = []
    beach_list = [(790.0, 1.0), (2000.0, 1.0), (2850.0, -1.0), (3170.0, -1.0)]
    beach = np.zeros((H, W), bool)
    for s_b, sgn in beach_list:
        m = ok_cell & (side == sgn) & (np.abs(st_n - s_b) <= args.beach_length_m / 2) & (d <= args.beach_width_m)
        beach |= m
        beaches.append(dict(station_m=s_b, side='left' if sgn > 0 else 'right', cells=int(m.sum())))
    beach_z = ws_n + 0.6 + (args.band_m - 0.6) * (d / args.beach_width_m) ** 2
    apply = ok_cell & (d > args.band_m) & (d <= args.reach_m)
    zone = np.where(apply, zone, 0)
    target = np.where(apply, new, bed)
    target = np.where(beach & ok_cell, np.minimum(np.where(apply, target, bed), beach_z), target)
    zone = np.where(beach & ok_cell, 1, zone)
    changed = (np.abs(target - bed) > 1e-3) & ok_cell
    # never below the water: every changed dry cell stays >= 0.6 m above its nearest water surface
    target = np.where(changed, np.maximum(target, ws_n + 0.6), bed)
    stats = dict(changed_cells=int(changed.sum()),
                 zone_cells={str(z): int(((zone == z) & changed).sum()) for z in (1, 2, 3, 4)},
                 raised_cells=int((changed & (target > bed)).sum()), lowered_cells=int((changed & (target < bed)).sum()),
                 dz_p1_p50_p99=[float(v) for v in np.percentile((target - bed)[changed], [1, 50, 99])] if changed.any() else None,
                 min_height_above_water_m=float(np.min((target - ws_n)[changed])) if changed.any() else None,
                 terrain_min_max_m=[float(target.min()), float(target.max())],
                 input_terrain_min_max_m=[float(bed.min()), float(bed.max())])
    for key in ('bed', 'dem', 'dem2021'):
        if key in ev:
            ev[key] = np.where(changed, target, ev[key].astype(np.float64)).astype(ev[key].dtype)
    ev['class_code'] = np.where(changed, 6, ev['class_code']).astype(ev['class_code'].dtype)
    ev['wall_zone'] = np.where(changed, zone, 0).astype(np.uint8)
    out.mkdir(parents=True)
    np.savez_compressed(out / 'evidence_grid.npz', **ev)
    for name in ('centreline.json', 'profile.json', 'boulders.json', 'sentinel2_rgb.npz'):
        if (args.evidence / name).exists():
            shutil.copyfile(args.evidence / name, out / name)
    manifest['class_codes']['6'] = ('gorge wall reconstructed from observations (near-vertical banded basalt over talus aprons, '
                                    'scoured waterline band, small beaches) placed on the GLO-30 rim height and the GLO-30 '
                                    'wall mid-height: shape INFERRED')
    manifest['gorge_walls'] = dict(
        generator='physics/scripts/reconstruct_zambezi_gorge_walls.py',
        source_evidence=dict(path=str(args.evidence.resolve()), evidence_grid_sha256=sha(args.evidence / 'evidence_grid.npz')),
        observations=dict(path=args.observations.resolve().relative_to(ROOT).as_posix(), sha256=sha(args.observations),
                          used='near-vertical dark basalt walls ~100-120 m with lava-flow banding; scoured basalt/boulder '
                               'waterline band; talus aprons with woodland; beaches ~790 L, 2000 L, 2850 R, 3170 R'),
        method='per 25 m station bin and side: D = p90 of GLO-30 above the water at 60-240 m from it; d_mid = first distance '
               'where the cumulative-max median GLO-30 profile reaches D/2 (a blurred step keeps its mid-height position); '
               'both smoothed over 150 m. Cliff mid-height at d_mid (+ bounded wander), talus below, GLO-30 above the rim.',
        parameters={k: v for k, v in vars(args).items() if k not in ('evidence', 'out', 'observations', 'distance_cache')},
        beaches=beaches, statistics=stats,
        bins=dict(bin_m=args.bin_m, left=dict(depth_m=[round(float(v), 2) for v in Ds[0]], mid_height_distance_m=[round(float(v), 2) for v in dms[0]]),
                  right=dict(depth_m=[round(float(v), 2) for v in Ds[1]], mid_height_distance_m=[round(float(v), 2) for v in dms[1]])),
        hydraulics_changed=False,
        note='dry ground only: the Sentinel-2 water, the inferred bed and the cook bank band (first 6 m) are unchanged, so the '
             'committed cook and runtime atlas stay valid; the Landscape and canopy are rebuilt from this grid')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(stats, indent=1))


if __name__ == '__main__':
    main()
