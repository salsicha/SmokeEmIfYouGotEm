"""Discharge-consistent inferred submerged bed for the South Fork 2 m grid.

The captured DEM is hydro-flattened: water pixels carry the captured water
surface, not the bed. The earlier prior lowered every water vertex by a
uniform shore-distance trough (0.35 x distance, capped at 2.2 m). Settled
cooks on that bed hold the river 1-1.6 m below the captured surface and
never form the captured rapid drops, because riffles and rapids are as deep
as pools.

This revision keeps the captured water surface, wetted outline, authored
discharge (45.3 m3/s, 1600 cfs) and the solver's Manning roughness, and
infers depth from them:

* Along 5 m route-station bins, the captured surface slope S (smoothed) and
  the conveyance width of an assumed bank shape f = min(1, d / L) give the
  strip-method normal depth H = (Q n / (S^0.5 sum f^(5/3)))^(3/5).
* Where the captured surface is nearly flat (pools, S < 0.006) the depth is
  not controlled by the surface, so the previous prior's 2.2 m pool depth is
  kept (full weight at S <= 0.002).
* An optional per-bin bias from a settled cook (median cooked surface minus
  captured surface) is added to H, iterating the bed toward a settled
  surface that matches the captured one.
* The Troublemaker registered rapid/seam rectangle is protected; depth
  blends back to the previous prior within 30 m of it.

Dry vertices, the wetted outline and the captured surface are unchanged.
This is explicitly inferred bathymetry, not measured.

Numpy only. Args: output_dir [--bias bias.npz] [--label text]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tiff_numpy import read_geotiff  # noqa: E402

BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
EXT = BASE / 'source_context_extension'
Q = 45.3069545472
N_MANNING = 0.035
BIN_M = 5.0
S_MIN, S_MAX = 0.0005, 0.08
H_MIN, H_MAX = 0.25, 6.0
POOL_DEPTH_M, S_POOL_LO, S_POOL_HI = 2.2, 0.002, 0.006
L_MIN_M, L_FRACTION = 3.0, 0.3
PROTECT_BLEND_M = 30.0
PRIOR_SLOPE, PRIOR_MAX = 0.35, 2.2
STAGE_CORE_M = 3.0      # stage from water at least this far from the mapped shore
BANK_TOL_M = 0.3        # mapped-water cells this far above the stage are bank


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gauss1d(values, sigma_bins):
    r = int(np.ceil(3 * sigma_bins))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_bins) ** 2)
    k /= k.sum()
    return np.convolve(np.pad(values, r, mode='edge'), k, mode='valid')


def edt_cells(inside, max_k):
    """Exact Euclidean distance (cells) from inside cells to the nearest outside cell (capped)."""
    ny = inside.shape[0]
    big = 1e9
    rows = np.arange(ny, dtype=np.float64)[:, None]
    out = ~inside
    above = np.maximum.accumulate(np.where(out, rows, -big), axis=0)
    below = np.minimum.accumulate(np.where(out, rows, big)[::-1], axis=0)[::-1]
    g = np.minimum(np.minimum(rows - above, below - rows), float(max_k + 1))
    g2 = g * g
    best = g2.copy()
    for k in range(1, max_k + 1):
        kk = float(k * k)
        np.minimum(best[:, k:], g2[:, :-k] + kk, out=best[:, k:])
        np.minimum(best[:, :-k], g2[:, k:] + kk, out=best[:, :-k])
    return np.sqrt(best)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--bias', type=Path)
    parser.add_argument('--label', default='discharge-consistent bed')
    args = parser.parse_args()
    out = args.output.resolve()
    assert not out.exists(), 'Fresh output directory required; retain earlier revisions'
    extension = json.loads((EXT / 'manifest.json').read_text())
    composite = json.loads((BASE / 'composite_terrain/manifest.json').read_text())
    for name, expected in extension['artifacts'].items():
        assert sha(EXT / name) == expected, name
    surface, geo_s, _ = read_geotiff(EXT / 'captured_surface_navd88_m.tif')
    prior, geo_b, _ = read_geotiff(EXT / 'coarse_bed_navd88_m.tif')
    mask, geo_m, _ = read_geotiff(EXT / 'unknown_submerged_bed_mask.tif')
    x0, y0 = extension['grid']['first_vertex_utm_m']
    cell = extension['grid']['cell_m']
    for geo in (geo_s, geo_b, geo_m):
        assert geo['cell_m'] == (cell, cell) and geo['corner_utm_m'] == (x0 - cell / 2, y0 + cell / 2)
    assert surface.shape == prior.shape == mask.shape == tuple(extension['grid']['shape'])
    water = mask == 1
    # The previous prior, reproduced exactly, identifies which vertices it owns.
    prior_depth = np.where(water, surface - prior, 0.0).astype(np.float64)
    print('water vertices', int(water.sum()), flush=True)

    rows, cols = np.nonzero(water)
    r0, r1 = max(rows.min() - 2, 0), min(rows.max() + 3, water.shape[0])
    c0, c1 = max(cols.min() - 2, 0), min(cols.max() + 3, water.shape[1])
    sub = water[r0:r1, c0:c1]
    dist_m = np.zeros(water.shape)
    dist_m[r0:r1, c0:c1] = np.maximum(edt_cells(sub, max_k=80) * cell - 0.5 * cell, 0.0)
    old_rule = np.minimum(PRIOR_MAX, PRIOR_SLOPE * dist_m)
    reproduces = np.abs(old_rule[water] - prior_depth[water])
    print('previous prior reproduced: p99 %.4f m, max %.4f m' % (np.percentile(reproduces, 99), reproduces.max()), flush=True)

    route = json.loads((BASE / 'playable_route/coordinate_map.json').read_text())
    pts = np.asarray(route['points'])
    origin = np.asarray(route['origin_utm_m'])
    rx, ry = pts[:, 1] + origin[0], pts[:, 2] + origin[1]
    east = x0 + cols * cell
    north = y0 - rows * cell
    station = np.empty(len(rows))
    tangent_index = np.empty(len(rows), int)
    block = 256
    for br in range(r0, r1, block):
        for bc in range(c0, c1, block):
            sel = np.nonzero((rows >= br) & (rows < br + block) & (cols >= bc) & (cols < bc + block))[0]
            if not len(sel):
                continue
            e, n = east[sel], north[sel]
            margin = 600.0
            cand = np.nonzero((rx > e.min() - margin) & (rx < e.max() + margin) & (ry > n.min() - margin) & (ry < n.max() + margin))[0]
            assert len(cand), 'water far from route'
            best = np.full(len(sel), np.inf); bi = np.zeros(len(sel), int)
            for k0 in range(0, len(cand), 1500):
                cc = cand[k0:k0 + 1500]
                d = (e[:, None] - rx[None, cc]) ** 2 + (n[:, None] - ry[None, cc]) ** 2
                j = d.argmin(1); dv = d[np.arange(len(sel)), j]
                upd = dv < best; best[upd] = dv[upd]; bi[upd] = cc[j[upd]]
            station[sel] = pts[bi, 0]; tangent_index[sel] = bi
    print('stations assigned', flush=True)

    # Water beyond either end of the route (dam tailwater, reservoir arm) gets a
    # station projected along the end tangent, as the cook preparation does.
    tangent = np.column_stack((pts[:, 4], -pts[:, 3]))
    for endpoint in (0, len(pts) - 1):
        m = tangent_index == endpoint
        station[m] += (east[m] - rx[endpoint]) * tangent[endpoint, 0] + (north[m] - ry[endpoint]) * tangent[endpoint, 1]
    beyond = (tangent_index == 0) | (tangent_index == len(pts) - 1)
    lower = np.floor(min(station.min(), 0.0) / BIN_M) * BIN_M
    nb = int(np.ceil((station.max() - lower) / BIN_M)) + 1
    b = np.clip(((station - lower) / BIN_M).astype(int), 0, nb - 1)
    b_all = b
    count = np.bincount(b, minlength=nb)
    zs_raw = np.full(nb, np.nan)
    order = np.argsort(b, kind='stable')
    splits = np.cumsum(count)[:-1]
    core_water = dist_m[rows, cols] >= STAGE_CORE_M
    for k, idx in enumerate(np.split(order, splits)):
        if len(idx) >= 2:
            use = idx[core_water[idx]]
            use = use if len(use) >= 2 else idx
            zs_raw[k] = np.median(surface[rows[use], cols[use]])
    good = np.isfinite(zs_raw)
    zs = np.interp(np.arange(nb), np.nonzero(good)[0], zs_raw[good])
    zs = gauss1d(zs, 1.5)
    slope = gauss1d(-np.gradient(zs, BIN_M), 2.0)
    S = np.clip(slope, S_MIN, S_MAX)
    centers = lower + (np.arange(nb) + 0.5) * BIN_M
    # The mapped water outline includes steep bank inside some constrictions:
    # cells standing clearly above the local stage are bank at their captured
    # height (no inferred depth); shore distance is taken from the rest.
    stage = np.interp(station, centers, zs)
    bank = surface[rows, cols] - stage > BANK_TOL_M
    effective = water.copy()
    effective[rows[bank], cols[bank]] = False
    dist_eff = np.zeros(water.shape)
    dist_eff[r0:r1, c0:c1] = np.maximum(edt_cells(effective[r0:r1, c0:c1], max_k=80) * cell - 0.5 * cell, 0.0)
    d_w = np.where(bank, 0.0, dist_eff[rows, cols])
    print('mapped-water cells treated as bank:', int(bank.sum()), flush=True)
    dmax = np.zeros(nb)
    np.maximum.at(dmax, b, d_w)
    L = np.maximum(L_MIN_M, L_FRACTION * gauss1d(dmax, 2.0))
    f = np.clip(d_w / L[b_all], 0.0, 1.0)
    K = np.bincount(b, weights=f ** (5.0 / 3.0) * cell * cell, minlength=nb) / BIN_M
    K = np.maximum(gauss1d(K, 1.0), 1e-3)
    Hn = (Q * N_MANNING / (np.sqrt(S) * K)) ** 0.6
    Hn = np.clip(gauss1d(np.clip(Hn, H_MIN, H_MAX), 2.0), H_MIN, H_MAX)
    wpool = np.clip((S_POOL_HI - S) / (S_POOL_HI - S_POOL_LO), 0.0, 1.0)
    H = np.maximum(Hn, Hn + (POOL_DEPTH_M - Hn) * wpool)
    bias_info = None
    if args.bias:
        prev = np.load(args.bias)
        bias = np.interp(centers, prev['station'], prev['bias'], left=0.0, right=0.0)
        # Only along the route itself: beyond-end water used the previous prior
        # in the cook that measured this bias.
        bias[(centers < 0) | (centers > pts[-1, 0])] = 0.0
        H = H + bias
        bias_info = dict(path=args.bias.resolve().relative_to(ROOT).as_posix(), sha256=sha(args.bias),
                         median_abs_m=float(np.median(np.abs(bias))), max_abs_m=float(np.abs(bias).max()))
    H = np.clip(H, H_MIN, H_MAX)

    new_depth = np.where(bank, 0.0, H[b_all] * f)
    # Protect the registered Troublemaker rapid/seam rectangle and blend near it.
    ax, ay, bx, by = composite['coarse_exclusion_boundary_utm_m']
    dx = np.maximum(np.maximum(ax - east, east - bx), 0.0)
    dy = np.maximum(np.maximum(ay - north, north - by), 0.0)
    w = np.clip(np.hypot(dx, dy) / PROTECT_BLEND_M, 0.0, 1.0)
    depth = w * new_depth + (1.0 - w) * prior_depth[rows, cols]
    bed = prior.copy()
    bed[rows, cols] = (surface[rows, cols] - depth).astype(np.float32)
    assert np.array_equal(bed[~water], prior[~water], equal_nan=True)
    assert np.isfinite(bed[water]).all() and (bed[water] <= surface[water]).all()

    out.mkdir(parents=True)
    np.savez_compressed(out / 'coarse_bed_navd88_m.npz', coarse_bed_navd88_m=bed)
    np.savez_compressed(out / 'water_vertex_design.npz', rows=rows.astype(np.int32), cols=cols.astype(np.int32), bank=bank, stage_navd88_m=stage,
                        station_m=station, shore_distance_m=d_w, shape_f=f, depth_m=depth, prior_depth_m=prior_depth[rows, cols],
                        protect_weight=w)
    design = dict(bin_m=BIN_M, station_center_m=centers.tolist(), captured_surface_median_navd88_m=zs_raw.tolist(),
                  captured_surface_smoothed_navd88_m=zs.tolist(), slope=S.tolist(), conveyance_width_m=K.tolist(),
                  bank_shape_length_m=L.tolist(), normal_depth_m=Hn.tolist(), pool_weight=wpool.tolist(),
                  centerline_depth_m=H.tolist(), water_vertex_count=count.tolist())
    (out / 'design.json').write_text(json.dumps(design) + '\n')
    change = depth - prior_depth[rows, cols]
    manifest = dict(
        schema='raftsim.south_fork.discharge_consistent_bed.v1', label=args.label,
        grid=dict(first_vertex_utm_m=[x0, y0], cell_m=cell, shape=list(bed.shape), crs='EPSG:32610', vertical_datum='NAVD88'),
        inputs=dict(captured_surface=dict(path=(EXT / 'captured_surface_navd88_m.tif').relative_to(ROOT).as_posix(), sha256=sha(EXT / 'captured_surface_navd88_m.tif')),
                    previous_prior_bed=dict(path=(EXT / 'coarse_bed_navd88_m.tif').relative_to(ROOT).as_posix(), sha256=sha(EXT / 'coarse_bed_navd88_m.tif')),
                    water_mask=dict(path=(EXT / 'unknown_submerged_bed_mask.tif').relative_to(ROOT).as_posix(), sha256=sha(EXT / 'unknown_submerged_bed_mask.tif')),
                    route=dict(path=(BASE / 'playable_route/coordinate_map.json').relative_to(ROOT).as_posix(), sha256=sha(BASE / 'playable_route/coordinate_map.json')),
                    composite_manifest_sha256=sha(BASE / 'composite_terrain/manifest.json')),
        parameters=dict(discharge_m3s=Q, discharge_basis='authored 1600 cfs scenario; flight-time discharge unknown',
                        manning_n=N_MANNING, bin_m=BIN_M, slope_clip=[S_MIN, S_MAX], depth_clip_m=[H_MIN, H_MAX],
                        pool_depth_m=POOL_DEPTH_M, pool_slope_band=[S_POOL_LO, S_POOL_HI], bank_shape_length=dict(minimum_m=L_MIN_M, fraction_of_half_width=L_FRACTION),
                        protected_rectangle_utm_m=composite['coarse_exclusion_boundary_utm_m'], protect_blend_m=PROTECT_BLEND_M, stage_core_distance_m=STAGE_CORE_M, bank_tolerance_above_stage_m=BANK_TOL_M,
                        beyond_route_ends='station projected along the end tangent (as the cook preparation)'),
        bias=bias_info,
        outputs=dict(coarse_bed=dict(path=(out / 'coarse_bed_navd88_m.npz').relative_to(ROOT).as_posix(), sha256=sha(out / 'coarse_bed_navd88_m.npz'), array='coarse_bed_navd88_m', dtype='float32'),
                     design=dict(path=(out / 'design.json').relative_to(ROOT).as_posix(), sha256=sha(out / 'design.json')),
                     water_vertex_design=dict(path=(out / 'water_vertex_design.npz').relative_to(ROOT).as_posix(), sha256=sha(out / 'water_vertex_design.npz'))),
        statistics=dict(water_vertices=int(water.sum()), beyond_route_end_vertices=int(beyond.sum()), mapped_water_bank_vertices=int(bank.sum()), depth_change_m_p5_p50_p95=np.percentile(change, [5, 50, 95]).tolist(),
                        depth_m_p5_p50_p95=np.percentile(depth, [5, 50, 95]).tolist(),
                        vertices_shallower_than_prior=int((change < -1e-6).sum()), vertices_deeper_than_prior=int((change > 1e-6).sum())),
        dry_vertices_bit_identical=True, captured_surface_unchanged=True, water_outline_unchanged=True,
        measured_bathymetry=False, inferred=True, hydraulic_validation_passed=False, normal_map_integrated=False)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest['statistics'], indent=2))


if __name__ == '__main__':
    main()
