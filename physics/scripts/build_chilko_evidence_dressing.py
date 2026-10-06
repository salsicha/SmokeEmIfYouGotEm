"""Evidence canopy for the Chilko Lava Canyon Landscape (numpy only).

The BC Vegetation Resources Inventory (VRI, VEG_COMP_LYR_R1_POLY, fetched
into chilko_sources_2026_09/vri) gives, per polygon, the treed/non-treed
class, leading species and their shares, crown closure, projected height and
live stems per hectare. Sentinel-2 at 10 m shows where the dark conifer
clumps sit inside the pale burned grassland. So:

* tree count per polygon (from the inventory): crown closure x area / mean
  crown area, capped at the live stems per hectare; treed polygons only
  (BCLCS level 2 'T'), plus the residual trees of non-treed 'SL' polygons at
  their stated crown closure;
* positions (INFERRED): a jittered --spacing-m lattice, sampled without
  replacement with weights from Sentinel-2 red-band darkness (2024-09-04, dry
  late-summer grass against dark conifers), inside the polygon, away from the
  wetted channel and off cliffs;
* species per tree from the polygon's species shares (inventory); height =
  projected height x N(1, 0.15) clipped 0.6-1.3 (spread INFERRED); crown
  radius 0.13 x height for conifers, 0.18 x height for aspen (allometry
  INFERRED);
* riparian understory (INFERRED structure): shrubs where Sentinel-2 NDVI is
  above --riparian-ndvi-min within --riparian-reach-m of the water (the green
  bank strip the inventory does not resolve).

Output: lava_canyon_evidence_2023_canopy_placement.json (the evidence canopy
layout, schema raftsim.chilko.lava_canyon_evidence_canopy.v1) and a review
PNG, in the Landscape frame of the terrain manifest.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from build_futaleufu_evidence_grid import bilinear
from build_pacuare_evidence_dressing import dilate
from build_pacuare_evidence_grid import edt_inside
from geo_frames import tm_forward, utm
from png_numpy import write_png

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'physics/data/real_world/chilko_river_bc/chilko_sources_2026_09'
SEED = 20260928
UTM10 = utm(10)
CONIFER = ('P', 'F', 'S', 'B', 'L', 'H', 'C', 'Y', 'J', 'T')  # pines, firs, spruces, balsams, larch, hemlock, cedars, cypress, juniper, yew
BROADLEAF = ('A', 'E', 'W', 'D', 'M', 'V', 'Q', 'R', 'G', 'K', 'X', 'Z', 'U')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def fill_polygon(mask, rings, x0, y_top, cell):
    """Even-odd scanline fill of UTM rings (lists of (E, N)) into mask (row 0 = north)."""
    ny, nx = mask.shape
    yc = y_top - (np.arange(ny) + 0.5) * cell
    xs_all = [[] for _ in range(ny)]
    for ring in rings:
        p = np.asarray(ring, np.float64)
        a, b = p[:-1], p[1:]
        lo, hi = np.minimum(a[:, 1], b[:, 1]), np.maximum(a[:, 1], b[:, 1])
        r0 = np.clip(np.floor((y_top - hi) / cell - 0.5).astype(int), 0, ny - 1)
        r1 = np.clip(np.ceil((y_top - lo) / cell - 0.5).astype(int), 0, ny - 1)
        for k in np.nonzero(hi > lo)[0]:
            rows = np.arange(r0[k], r1[k] + 1)
            y = yc[rows]
            hit = (y >= lo[k]) & (y < hi[k])
            t = (y[hit] - a[k, 1]) / (b[k, 1] - a[k, 1])
            x = a[k, 0] + t * (b[k, 0] - a[k, 0])
            for r, xv in zip(rows[hit], x):
                xs_all[r].append(xv)
    for r, xs in enumerate(xs_all):
        if len(xs) < 2:
            continue
        xs = np.sort(np.asarray(xs))
        for xa, xb in zip(xs[0::2], xs[1::2]):
            c0 = max(int(np.ceil((xa - x0) / cell - 0.5)), 0); c1 = min(int(np.floor((xb - x0) / cell - 0.5)), nx - 1)
            if c1 >= c0:  # (spans wholly outside the window give c1 < c0; never a negative slice end)
                mask[r, c0:c1 + 1] ^= True


def species_list(p):
    out = []
    for k in range(1, 7):
        cd, pct = p.get(f'SPECIES_CD_{k}'), p.get(f'SPECIES_PCT_{k}')
        if cd and pct:
            h = p.get(f'PROJ_HEIGHT_{k}') or p.get('PROJ_HEIGHT_1')
            out.append((cd, float(pct), float(h) if h else None))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path, help='build_chilko_evidence_grid.py output folder')
    ap.add_argument('--terrain-manifest', type=Path, required=True)
    ap.add_argument('--out-dir', type=Path, required=True)
    ap.add_argument('--vri', type=Path, default=SRC / 'vri/vri_veg_comp_lyr_r1_poly.json')
    ap.add_argument('--sentinel2', default='S2B_T10UDC_20240904T192337_L2A.npz')
    ap.add_argument('--raster-m', type=float, default=2.0)
    ap.add_argument('--spacing-m', type=float, default=3.0)
    ap.add_argument('--channel-clearance-m', type=int, default=3)
    ap.add_argument('--max-slope-deg', type=float, default=50.0)
    ap.add_argument('--dark-red', type=float, nargs=2, default=(0.075, 0.035), help='red reflectance mapped to weight 0.05 and 1')
    ap.add_argument('--riparian-reach-m', type=float, default=25.0)
    ap.add_argument('--riparian-ndvi-min', type=float, default=0.45)
    ap.add_argument('--riparian-spacing-m', type=float, default=4.0)
    args = ap.parse_args()
    out = args.out_dir.resolve() / 'lava_canyon_evidence_2023_canopy_placement.json'
    assert not out.exists(), 'fresh output required'
    rng = np.random.default_rng(SEED)

    manifest = json.loads((args.evidence / 'manifest.json').read_text(encoding='utf-8'))
    g = manifest['grid']
    X0, Y1, NX, NY = g['x0'], g['y_top'], g['nx'], g['ny']
    ev = np.load(args.evidence / 'evidence_grid.npz')
    river, dem = ev['river'], ev['dem'].astype(np.float64)
    land = json.loads(args.terrain_manifest.read_text(encoding='utf-8'))['landscape']
    west_e = land['world_origin_epsg3157_m']['west_edge_e']; centre_n = land['world_origin_epsg3157_m']['centre_n']
    datum = land['runtime_vertical_datum_m']
    assert (west_e, land['horizontal_span_x_m'], land['horizontal_span_y_m']) == (X0, NX, NY)

    # ---------------- inventory polygons on a --raster-m grid
    cell = args.raster_m
    RY, RX = int(np.ceil(NY / cell)), int(np.ceil(NX / cell))
    vri = json.loads(args.vri.read_text(encoding='utf-8'))
    poly_id = -np.ones((RY, RX), np.int32)
    polys = []
    for f in vri['features']:
        geom = f['geometry']
        parts = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        m = np.zeros((RY, RX), bool)
        for part in parts:
            rings = []
            for ring in part:
                ll = np.asarray(ring, np.float64)
                e, n = tm_forward(ll[:, 0], ll[:, 1], UTM10)
                rings.append(np.column_stack([e, n]))
            fill_polygon(m, rings, X0, Y1, cell)
        if not m.any():
            continue
        poly_id[m & (poly_id < 0)] = len(polys)
        polys.append(f['properties'])

    # ---------------- where trees may stand
    gy, gx = np.gradient(dem)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    blocked1 = dilate(river, args.channel_clearance_m) | (slope > args.max_slope_deg)
    dist_w = edt_inside(~river)

    # Sentinel-2 darkness weight and NDVI at 10 m
    fm = json.loads((SRC / 'sentinel2/fetch_manifest.json').read_text())
    item = next(i for i in fm['items'] if i['npz'] == args.sentinel2)
    w = item['window_utm_m']; z = np.load(SRC / 'sentinel2' / args.sentinel2)
    R, N_ = [z[k].astype(np.float64) * 1e-4 - 0.1 for k in ('red', 'nir')]
    ndvi10 = (N_ - R) / np.maximum(N_ + R, 1e-3)
    r_hi, r_lo = args.dark_red
    weight10 = 0.05 + 0.95 * np.clip((r_hi - R) / (r_hi - r_lo), 0.0, 1.0) ** 1.5

    def s2_at(a, px, py):
        return bilinear(a, (w['ymax'] - py) / 10.0 - 0.5, (px - w['xmin']) / 10.0 - 0.5)

    # candidate lattice (column x, row y in 1 m window cells)
    s = args.spacing_m
    gxv, gyv = np.meshgrid(np.arange(s / 2, NX, s), np.arange(s / 2, NY, s))
    cand = np.column_stack([gxv.ravel(), gyv.ravel()]) + rng.uniform(-0.35, 0.35, (gxv.size, 2)) * s
    cand = cand[(cand[:, 0] >= 0) & (cand[:, 0] < NX) & (cand[:, 1] >= 0) & (cand[:, 1] < NY)]
    ci, cj = cand[:, 1].astype(int), cand[:, 0].astype(int)
    cand = cand[~blocked1[ci, cj]]
    ci, cj = cand[:, 1].astype(int), cand[:, 0].astype(int)
    cpoly = poly_id[np.minimum((ci / cell).astype(int), RY - 1), np.minimum((cj / cell).astype(int), RX - 1)]
    cweight = s2_at(weight10, X0 + cand[:, 0], Y1 - cand[:, 1])

    rows, per_poly = [], []
    for pid, p in enumerate(polys):
        l2, l4 = p.get('BCLCS_LEVEL_2'), p.get('BCLCS_LEVEL_4')
        cc = p.get('CROWN_CLOSURE') or 0
        sp = species_list(p)
        area_ha = float((poly_id == pid).sum()) * cell * cell / 1e4
        use = (l2 == 'T' or l4 in ('SL', 'ST')) and cc > 0 and sp and all(h is not None for _, _, h in sp)
        rec = dict(feature=pid, bclcs_2=l2, bclcs_4=l4, crown_closure_pct=cc, species=[[c, q, h] for c, q, h in sp],
                   stems_per_ha=p.get('VRI_LIVE_STEMS_PER_HA'), disturbance=p.get('LINE_7B_DISTURBANCE_HISTORY'),
                   area_in_window_ha=area_ha, trees=0)
        per_poly.append(rec)
        if not use:
            continue
        idx = np.nonzero(cpoly == pid)[0]
        if not len(idx):
            continue
        shares = np.array([q for _, q, _ in sp]); shares = shares / shares.sum()
        broad = np.array([c[0] in BROADLEAF and c[0] not in CONIFER for c, _, _ in sp])
        heights = np.array([h for _, _, h in sp])
        mean_r = float((shares * np.where(broad, 0.18, 0.13) * heights).sum())
        n_cc = cc / 100.0 * area_ha * 1e4 / (np.pi * max(mean_r, 1.0) ** 2)
        n_stems = (p.get('VRI_LIVE_STEMS_PER_HA') or 1e9) * area_ha
        n = int(min(round(n_cc), n_stems, len(idx)))
        if n <= 0:
            continue
        keys = np.log(rng.uniform(1e-12, 1.0, len(idx))) / cweight[idx]
        pick = idx[np.argpartition(-keys, n - 1)[:n]] if n < len(idx) else idx
        k_sp = rng.choice(len(sp), size=len(pick), p=shares)
        h = heights[k_sp] * np.clip(rng.normal(1.0, 0.15, len(pick)), 0.6, 1.3)
        r = np.clip(np.where(broad[k_sp], 0.18, 0.13) * h, 1.0, 4.5)
        form = np.where(broad[k_sp], 0, 1)
        for q, kk, hh, rr, ff in zip(pick, k_sp, h, r, form):
            rows.append((cand[q, 0], cand[q, 1], rr, hh, ff, pid))
        rec['trees'] = int(len(pick))
    arr = np.array(rows, np.float64)
    pts = arr[:, :2]; radius = arr[:, 2]; height = arr[:, 3]; form = arr[:, 4].astype(int)
    yaw = rng.uniform(0, 360, len(pts))
    r_i, c_i = pts[:, 1].astype(int), pts[:, 0].astype(int)
    x_cm = pts[:, 0] * 100.0; y_cm = -((Y1 - pts[:, 1]) - centre_n) * 100.0
    z_cm = (dem[r_i, c_i] - datum) * 100.0
    instances = [[round(float(x_cm[k]), 1), round(float(y_cm[k]), 1), round(float(z_cm[k]), 1), round(float(radius[k]), 2),
                  round(float(height[k]), 1), int(form[k]), 1, round(float(yaw[k]), 1)] for k in range(len(pts))]

    # ---------------- riparian understory (INFERRED structure, Sentinel-2 green strip)
    us = args.riparian_spacing_m
    ux, uy = np.meshgrid(np.arange(us / 2, NX, us), np.arange(us / 2, NY, us))
    up = np.column_stack([ux.ravel(), uy.ravel()]) + rng.uniform(-0.4, 0.4, (ux.size, 2)) * us
    up = up[(up[:, 0] >= 0) & (up[:, 0] < NX) & (up[:, 1] >= 0) & (up[:, 1] < NY)]
    ui, uj = up[:, 1].astype(int), up[:, 0].astype(int)
    near = (dist_w[ui, uj] <= args.riparian_reach_m) & ~blocked1[ui, uj]
    up = up[near]
    green = s2_at(ndvi10, X0 + up[:, 0], Y1 - up[:, 1]) > args.riparian_ndvi_min
    up = up[green]
    u_h = rng.uniform(1.5, 4.0, len(up)); u_w = rng.uniform(2.0, 4.5, len(up)); u_yaw = rng.uniform(0, 360, len(up))
    understory = [[round(float(x * 100.0), 1), round(float(-((Y1 - y) - centre_n) * 100.0), 1), round(float(u_h[k]), 2),
                   round(float(u_w[k]), 2), round(float(u_yaw[k]), 1)] for k, (x, y) in enumerate(up)]

    placement = dict(
        schema='raftsim.chilko.lava_canyon_evidence_canopy.v1',
        level='/Game/RaftSim/Maps/L_LavaCanyon', river_id='chilko', section_id='lava_canyon_evidence_2023',
        frame=dict(x_cm='east of the Landscape west edge (EPSG:3157 E - %.1f) x 100' % west_e,
                   y_cm='south of the Landscape centre row (-(N - %.1f)) x 100' % centre_n,
                   z_cm='LiDAR terrain - %.1f m datum (information only; the editor grounds on the Landscape)' % datum),
        instance_fields=['x_cm', 'y_cm', 'terrain_z_cm', 'crown_radius_m', 'height_m', 'form', 'kind', 'yaw_deg'],
        kinds={'1': 'count, species and heights from the VRI polygon; position sampled by Sentinel-2 darkness (position INFERRED)'},
        forms={'0': 'broadleaf (trembling aspen in the inventory)', '1': 'conifer (lodgepole pine, interior Douglas-fir, Engelmann spruce)'},
        inputs=dict(evidence_manifest=rel(args.evidence / 'manifest.json'), evidence_grid_sha256=sha(args.evidence / 'evidence_grid.npz'),
                    vri=rel(args.vri), vri_sha256=sha(args.vri), sentinel2=args.sentinel2, sentinel2_sha256=item['npz_sha256'],
                    terrain_manifest=rel(args.terrain_manifest), terrain_manifest_sha256=sha(args.terrain_manifest)),
        parameters=dict(raster_m=cell, spacing_m=s, channel_clearance_m=args.channel_clearance_m, max_slope_deg=args.max_slope_deg,
                        dark_red=list(args.dark_red), darkness_weight='0.05 + 0.95 * clip((red_hi - red) / (red_hi - red_lo))^1.5',
                        tree_count='crown closure x area / (pi x mean crown radius^2), capped at live stems/ha x area',
                        crown_radius='0.13 x height (conifer), 0.18 x height (broadleaf), 1-4.5 m',
                        height='VRI projected height x N(1, 0.15) clipped 0.6-1.3',
                        riparian=dict(reach_m=args.riparian_reach_m, ndvi_min=args.riparian_ndvi_min, spacing_m=us), seed=SEED),
        statistics=dict(polygons_in_window=len(polys), instance_count=int(len(pts)), understory_count=int(len(up)),
                        conifer_share=float((form == 1).mean()),
                        crown_radius_m_p10_p50_p90=[float(v) for v in np.percentile(radius, [10, 50, 90])],
                        height_m_p10_p50_p90=[float(v) for v in np.percentile(height, [10, 50, 90])],
                        trees_per_ha_window=float(len(pts) / (NX * NY / 1e4))),
        polygons=per_poly,
        positions_from_imagery=False, cover_from_inventory=True, tree_inventory_surveyed=False,
        species_and_heights_from_inventory=True, individual_heights_and_crowns_inferred=True,
        collision='visual only (no collision)', terrain_or_hydraulic_geometry_modified=False, instances=instances,
        understory_fields=['x_cm', 'y_cm', 'height_m', 'width_m', 'yaw_deg'],
        understory_mesh='the reach shrub mesh (riparian willow/alder structure INFERRED)', understory=understory,
        attribution='VRI: Contains information licensed under the Open Government Licence - British Columbia; '
                    'Sentinel-2: Contains modified Copernicus Sentinel data')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(placement, separators=(',', ':')) + '\n')
    rgb = np.load(args.evidence / 'sentinel2_rgb.npz')['rgb'].copy()
    edge = np.zeros((RY, RX), bool)
    edge[:-1] |= poly_id[:-1] != poly_id[1:]; edge[:, :-1] |= poly_id[:, :-1] != poly_id[:, 1:]
    er, ec = np.nonzero(edge)
    rgb[np.minimum((er * cell).astype(int), NY - 1), np.minimum((ec * cell).astype(int), NX - 1)] = (255, 255, 0)
    for (x, y), ff in zip(pts.astype(int), form):
        rgb[max(y - 1, 0):y + 2, max(x - 1, 0):x + 2] = (255, 60, 60) if ff == 0 else (60, 90, 255)
    for x, y in up.astype(int):
        rgb[y, x] = (0, 255, 0)
    write_png(out.with_suffix('.png'), rgb[::2, ::2])
    print(json.dumps(placement['statistics'], indent=1))


if __name__ == '__main__':
    main()
