"""Evidence dressing for the Pacuare Huacas-Pinball Landscape (numpy only).

Canopy and emergent-rock placements for L_UpperHuacas, from the evidence grid
(build_pacuare_evidence_grid.py), the IGN tree cover and the orthophoto.

Canopy.

The river-band dressing leaves the gorge walls as a draped Landscape with a
few scattered trees, while the orthophoto and the IGN tree-cover layer show
closed rainforest down to the banks. This builder places canopy trees over
the whole Landscape window:

* forest extent: IGN forestal2017_5k "arborea" polygons (measured cover),
  minus a clearance around the IGN active channel;
* crowns: sunlit crown tops in the 2014-2017 IGN orthophoto (local maxima of
  the 1.5 m-smoothed luminance, relative to its 15 m mean, over a 9 m
  window), thinned greedily by prominence to a minimum spacing (positions
  measured, coarse: ~1 m imagery);
* infill: forest cells farther than the infill distance from any crown
  (shaded slopes, where the photo resolves no crowns) receive trees on a
  jittered lattice (INFERRED positions inside measured forest cover);
* crown radius: 0.7 x the distance to the nearest neighbour, so neighbouring
  crowns touch as in the closed canopy the photo shows (INFERRED from
  spacing); tree heights (3.2 x crown radius + up to 4 m, 14-30 m), species
  and forms are INFERRED (the project's two opaque rainforest canopy
  meshes). Outside the orthophoto footprint only infill is placed;
* understory: one sub-canopy shrub beside each tree (0.4-0.9 crown radii
  away, 3-6 m tall, 4-7 m wide), so the trunk zone of the walls reads as
  layered rainforest rather than bare stems (INFERRED structure).

Emergent rocks. The Landscape carries the photographed rocks as bumps of the
evidence bed (their collision and the solver's obstacles), which at 0.7-0.8 m
sampling render as faceted prisms. Each single-boulder component (2-12 m2;
clusters and boulder gardens stay terrain, one mesh would turn them into a
slab) gets a rights-reviewed rock mesh shell on its equal-area footprint
ellipse (centroid, principal-axis ratio and area of the photographed pixels,
measured) from 0.4 m below the reference surface to 0.1 m above the bump
top (heights INFERRED as for the bumps). Visual only.

Outputs in --out-dir (world centimetres of the L_UpperHuacas Landscape frame:
x east from the window's west edge, y south from its centre row, z = (height
- datum) x 100): huacas_evidence_canopy_placement.json (+ review PNG; tree
roots are grounded on the Landscape in the editor) and
huacas_evidence_rock_placement.json.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from build_pacuare_evidence_grid import box_mean, components
from geo_frames import CRTM05, lonlat_to_merc, tm_inverse
from png_numpy import write_png

ROOT = Path(__file__).resolve().parents[2]
SEED = 20260927


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def rasterize_polygons(features, x0, y_top, nx, ny):
    """Even-odd scanline fill per polygon (rings together, so holes stay open); cell centres."""
    mask = np.zeros((ny, nx), bool)
    yc = y_top - np.arange(ny) - 0.5
    xc = x0 + np.arange(nx) + 0.5
    for f in features:
        geom = f['geometry']
        polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
        for rings in polys:
            edges = []
            for ring in rings:
                p = np.asarray(ring, float)[:, :2]
                edges.append(np.column_stack([p[:-1], p[1:]]))
            e = np.vstack(edges)
            if e[:, [0, 2]].max() < x0 or e[:, [0, 2]].min() > x0 + nx or e[:, [1, 3]].max() < y_top - ny or e[:, [1, 3]].min() > y_top:
                continue
            ex0, ey0, ex1, ey1 = e.T
            r0 = max(int(np.floor(y_top - max(ey0.max(), ey1.max()))), 0)
            r1 = min(int(np.ceil(y_top - min(ey0.min(), ey1.min()))) + 1, ny)
            for r in range(r0, r1):
                y = yc[r]
                hit = (ey0 <= y) != (ey1 <= y)
                if not hit.any():
                    continue
                xs = np.sort(ex0[hit] + (y - ey0[hit]) * (ex1[hit] - ex0[hit]) / (ey1[hit] - ey0[hit]))
                inside = (np.searchsorted(xs, xc) % 2) == 1
                mask[r] |= inside
    return mask


def gauss_blur(a, sigma):
    """Separable Gaussian blur (edge-padded), sigma in cells."""
    r = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    p = np.pad(a, r, mode='edge')
    t = sum(k[i] * p[i:i + a.shape[0], r:r + a.shape[1]] for i in range(2 * r + 1))
    p = np.pad(t, ((0, 0), (r, r)), mode='edge')
    return sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))


def sliding_max(a, r):
    out = a.copy()
    p = np.pad(a, r, mode='constant', constant_values=-np.inf)
    H, W = a.shape
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            np.maximum(out, p[dy:dy + H, dx:dx + W], out=out)
    return out


def dilate(mask, steps):
    m = mask.copy()
    for _ in range(steps):
        o = m.copy(); o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        m = o
    return m


def thin(points, score, min_dist):
    """Greedy: keep the highest-score point, drop neighbours within min_dist."""
    order = np.argsort(-score)
    cell = min_dist
    buckets = {}
    keep = []
    for k in order:
        x, y = points[k]
        bx, by = int(x // cell), int(y // cell)
        ok = True
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in buckets.get((bx + dx, by + dy), ()):
                    if (points[j, 0] - x) ** 2 + (points[j, 1] - y) ** 2 < min_dist * min_dist:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            keep.append(k)
            buckets.setdefault((bx, by), []).append(k)
    return np.array(keep, int)


def nearest_distance(points):
    """Distance from each point to its nearest other point (bucketed)."""
    cell = 12.0
    buckets = {}
    for k, (x, y) in enumerate(points):
        buckets.setdefault((int(x // cell), int(y // cell)), []).append(k)
    d = np.full(len(points), cell * 1.5)
    for k, (x, y) in enumerate(points):
        bx, by = int(x // cell), int(y // cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in buckets.get((bx + dx, by + dy), ()):
                    if j != k:
                        d[k] = min(d[k], np.hypot(points[j, 0] - x, points[j, 1] - y))
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path, help='build_pacuare_evidence_grid.py output folder')
    ap.add_argument('--forest', type=Path, required=True, help='IGN forestal2017_5k GeoJSON (EPSG:5367)')
    ap.add_argument('--ortho', type=Path, required=True, help='WMTS mosaic npz (fetch_wmts_corridor.py)')
    ap.add_argument('--terrain-manifest', type=Path, required=True)
    ap.add_argument('--out-dir', type=Path, required=True, help='terrain folder receiving the placement JSONs')
    ap.add_argument('--channel-clearance-m', type=int, default=4)
    ap.add_argument('--crown-window-m', type=int, default=4, help='half-width of the local-maximum window')
    ap.add_argument('--min-spacing-m', type=float, default=6.0)
    ap.add_argument('--infill-distance-m', type=int, default=7)
    ap.add_argument('--infill-spacing-m', type=float, default=8.0)
    ap.add_argument('--max-slope-deg', type=float, default=62.0)
    ap.add_argument('--rock-area-m2', type=float, nargs=2, default=(2.0, 12.0), help='rock components given a mesh shell')
    args = ap.parse_args()
    out = args.out_dir.resolve() / 'huacas_evidence_canopy_placement.json'
    rock_out = args.out_dir.resolve() / 'huacas_evidence_rock_placement.json'
    assert not out.exists() and not rock_out.exists(), 'fresh outputs required'

    manifest = json.loads((args.evidence / 'manifest.json').read_text(encoding='utf-8'))
    g = manifest['grid']
    X0, Y1, NX, NY = g['x0'], g['y_top'], g['nx'], g['ny']
    assert g['cell_m'] == 1.0
    ev = np.load(args.evidence / 'evidence_grid.npz')
    channel, dem = ev['channel'], ev['dem'].astype(np.float64)
    terrain = json.loads(args.terrain_manifest.read_text(encoding='utf-8'))
    land = terrain['landscape']
    west_e = land['world_origin_epsg5367_m']['west_edge_e']; centre_n = land['world_origin_epsg5367_m']['centre_n']
    datum = land['runtime_vertical_datum_m']
    assert (west_e, land['horizontal_span_x_m'], land['horizontal_span_y_m']) == (X0, NX, NY)

    # forest cover (IGN) and the orthophoto on the 1 m window
    forest_features = json.loads(args.forest.read_text(encoding='utf-8'))['features']
    forest = rasterize_polygons(forest_features, X0, Y1, NX, NY)
    CE, CN = np.meshgrid(X0 + np.arange(NX) + 0.5, Y1 - np.arange(NY) - 0.5)
    om = np.load(args.ortho)
    rgba, b = om['rgba'], om['bounds_epsg3857']
    lon, lat = tm_inverse(CE, CN, CRTM05)
    mx, my = lonlat_to_merc(lon, lat)
    pc = np.clip(((mx - b[0]) / (b[2] - b[0]) * rgba.shape[1]).astype(int), 0, rgba.shape[1] - 1)
    pr = np.clip(((b[3] - my) / (b[3] - b[1]) * rgba.shape[0]).astype(int), 0, rgba.shape[0] - 1)
    rgb = rgba[pr, pc, :3].astype(np.float32); valid = rgba[pr, pc, 3] > 0
    del lon, lat, mx, my, pc, pr, CE, CN
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.3 * R + 0.59 * G + 0.11 * B
    # Bare/built ground (roads, clearings, landslips): the hazy photo is
    # desaturated everywhere (forest median saturation 0.12), so the test is
    # red-dominant and bright over most of a 5 m patch (gravel bars: G-R
    # median -16; forest: +11).
    bare = box_mean(((G < R - 2) & (lum > 100)).astype(np.float32), 2) > 0.5
    gy, gx = np.gradient(dem)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    near_channel = dilate(channel, args.channel_clearance_m)
    allowed = forest & ~near_channel & ~(valid & dilate(bare, 1)) & (slope <= args.max_slope_deg) & np.isfinite(dem)

    # crowns: sunlit tops relative to the local mean
    ls = gauss_blur(lum, 1.5)
    relative = ls / np.maximum(box_mean(lum, 7), 1.0)
    peak = (ls >= sliding_max(ls, args.crown_window_m)) & (relative >= 1.0) & allowed & ~dilate(~valid, 8)
    rr, cc = np.nonzero(peak)
    pts = np.column_stack([cc + 0.5, rr + 0.5])
    keep = thin(pts, relative[rr, cc], args.min_spacing_m)
    crowns = pts[keep]
    print(f'forest cells {forest.sum()}, allowed {allowed.sum()}, crown peaks {len(pts)}, crowns {len(crowns)}', flush=True)

    # infill where no crown lies within the infill distance
    covered = np.zeros((NY, NX), bool)
    covered[crowns[:, 1].astype(int), crowns[:, 0].astype(int)] = True
    covered = dilate(covered, args.infill_distance_m)
    rng = np.random.default_rng(SEED)
    s = args.infill_spacing_m
    gxv, gyv = np.meshgrid(np.arange(s / 2, NX, s), np.arange(s / 2, NY, s))
    cand = np.column_stack([gxv.ravel(), gyv.ravel()]) + rng.uniform(-0.35, 0.35, (gxv.size, 2)) * s
    cand = cand[(cand[:, 0] >= 0) & (cand[:, 0] < NX) & (cand[:, 1] >= 0) & (cand[:, 1] < NY)]
    ci, cj = cand[:, 1].astype(int), cand[:, 0].astype(int)
    cand = cand[allowed[ci, cj] & ~covered[ci, cj]]
    points = np.vstack([crowns, cand])
    kind = np.concatenate([np.zeros(len(crowns), int), np.ones(len(cand), int)])
    # widen so neighbouring crowns touch; INFERRED crown size and height
    radius = np.clip(0.7 * nearest_distance(points), 3.5, 8.0)
    height = np.clip(3.2 * radius + rng.uniform(0.0, 4.0, len(points)), 14.0, 30.0)
    form = rng.integers(0, 2, len(points))
    yaw = rng.uniform(0, 360, len(points))
    r_i, c_i = points[:, 1].astype(int), points[:, 0].astype(int)
    E = X0 + points[:, 0]; N = Y1 - points[:, 1]
    x_cm = (E - west_e) * 100.0
    y_cm = -(N - centre_n) * 100.0
    z_cm = (dem[r_i, c_i] - datum) * 100.0
    instances = [[round(float(x_cm[k]), 1), round(float(y_cm[k]), 1), round(float(z_cm[k]), 1),
                  round(float(radius[k]), 2), round(float(height[k]), 1), int(form[k]), int(kind[k]), round(float(yaw[k]), 1)]
                 for k in range(len(points))]
    # understory beside each tree (INFERRED)
    ang = rng.uniform(0.0, 2.0 * np.pi, len(points)); dist = radius * rng.uniform(0.4, 0.9, len(points))
    upts = points + np.column_stack([np.cos(ang), np.sin(ang)]) * dist[:, None]
    inside = (upts[:, 0] >= 0) & (upts[:, 0] < NX) & (upts[:, 1] >= 0) & (upts[:, 1] < NY)
    upts = upts[inside]
    upts = upts[allowed[upts[:, 1].astype(int), upts[:, 0].astype(int)]]
    u_h = rng.uniform(3.0, 6.0, len(upts)); u_w = rng.uniform(4.0, 7.0, len(upts)); u_yaw = rng.uniform(0, 360, len(upts))
    understory = [[round(float((X0 + x - west_e) * 100.0), 1), round(float(-(Y1 - y - centre_n) * 100.0), 1),
                   round(float(u_h[k]), 2), round(float(u_w[k]), 2), round(float(u_yaw[k]), 1)] for k, (x, y) in enumerate(upts)]

    placement = dict(
        schema='raftsim.pacuare.huacas_evidence_canopy.v1',
        level='/Game/RaftSim/Maps/L_UpperHuacas', river_id='pacuare', section_id='huacas_evidence_2017',
        frame=dict(x_cm='east of the Landscape west edge (EPSG:5367 E - %.1f) x 100' % west_e,
                   y_cm='south of the Landscape centre row (-(N - %.1f)) x 100' % centre_n,
                   z_cm='interpolated contour terrain - %.1f m datum (information only; the editor grounds on the Landscape)' % datum),
        instance_fields=['x_cm', 'y_cm', 'terrain_z_cm', 'crown_radius_m', 'height_m', 'form', 'kind', 'yaw_deg'],
        kinds={'0': 'orthophoto crown top (position measured, ~1 m imagery)',
               '1': 'infill inside IGN forest cover where the photo resolves no crown (position INFERRED)'},
        forms={'0': 'SM_RaftSim_Pacuare_CanopyTree_A_OpaqueV2 (species INFERRED)',
               '1': 'SM_RaftSim_Pacuare_CanopyTree_B_OpaqueV2 (species INFERRED)'},
        inputs=dict(evidence_manifest=rel(args.evidence / 'manifest.json'), evidence_grid_sha256=sha(args.evidence / 'evidence_grid.npz'),
                    forest=rel(args.forest), forest_sha256=sha(args.forest), forest_layer='IGN forestal2017_5k (categoria arborea)',
                    ortho=rel(args.ortho), ortho_sha256=sha(args.ortho),
                    terrain_manifest=rel(args.terrain_manifest), terrain_manifest_sha256=sha(args.terrain_manifest)),
        parameters=dict(channel_clearance_m=args.channel_clearance_m, crown_window_m=args.crown_window_m,
                        min_spacing_m=args.min_spacing_m, infill_distance_m=args.infill_distance_m,
                        infill_spacing_m=args.infill_spacing_m, max_slope_deg=args.max_slope_deg,
                        crown_radius='0.7 x nearest-neighbour distance, 3.5-8 m', height='3.2 x crown radius + U(0, 4) m, 14-30 m', seed=SEED),
        statistics=dict(forest_share=float(forest.mean()), allowed_share=float(allowed.mean()),
                        crown_count=int(len(crowns)), infill_count=int(len(cand)), instance_count=int(len(points)),
                        crown_radius_m_p10_p50_p90=[float(v) for v in np.percentile(radius, [10, 50, 90])],
                        height_m_p10_p50_p90=[float(v) for v in np.percentile(height, [10, 50, 90])],
                        density_per_ha=float(len(points) / max(allowed.sum() / 1e4, 1e-9)),
                        understory_count=int(len(upts))),
        positions_from_imagery=True, tree_inventory_surveyed=False, species_heights_and_forms_inferred=True,
        collision='visual only (no collision)', terrain_or_hydraulic_geometry_modified=False,
        instances=instances,
        understory_fields=['x_cm', 'y_cm', 'height_m', 'width_m', 'yaw_deg'],
        understory_mesh='SM_RaftSim_Pacuare_RiparianShrub_A_OpaqueV2 (sub-canopy structure INFERRED)',
        understory=understory)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(placement, separators=(',', ':')) + '\n')

    # emergent rock shells: footprint ellipse of each compact photographed rock
    cls, bed, ws = ev['class_code'], ev['bed'].astype(np.float64), ev['ws'].astype(np.float64)
    rock_comps, _ = components(cls == 3)
    rows = []
    for pix in rock_comps:
        if not args.rock_area_m2[0] <= len(pix) <= args.rock_area_m2[1]:
            continue
        r_, c_ = pix[:, 0], pix[:, 1]
        de, dn = c_ - c_.mean(), -(r_ - r_.mean())
        # + the variance of a unit cell, so one- and two-cell rocks keep a size
        cov = (np.cov(np.vstack([de, dn])) if len(pix) > 2 else np.zeros((2, 2))) + np.eye(2) / 12.0
        evals, evecs = np.linalg.eigh(cov)
        # equal-area ellipse with the principal-axis ratio: pi (L/2)(W/2) = area
        aspect = np.sqrt(evals[1] / evals[0])
        length = 2.0 * np.sqrt(len(pix) / np.pi * aspect); width = 2.0 * np.sqrt(len(pix) / np.pi / aspect)
        yaw = np.degrees(np.arctan2(-evecs[1, 1], evecs[0, 1]))  # Unreal +Y is south
        r0, r1, c0, c1 = max(r_.min() - 3, 0), min(r_.max() + 4, NY), max(c_.min() - 3, 0), min(c_.max() + 4, NX)
        local = np.zeros((r1 - r0, c1 - c0), bool); local[r_ - r0, c_ - c0] = True
        wsn = ws[r0:r1, c0:c1][dilate(local, 3) & ~local]
        surface = float(np.median(wsn[np.isfinite(wsn)])) if np.isfinite(wsn).any() else float(bed[r_, c_].min() - 0.45)
        top = float(bed[r_, c_].max())
        base = surface - 0.4
        E_, N_ = X0 + c_.mean() + 0.5, Y1 - r_.mean() - 0.5
        rows.append([round((E_ - west_e) * 100.0, 1), round(-(N_ - centre_n) * 100.0, 1), round((base - datum) * 100.0, 1),
                     round(float(length), 2), round(float(width), 2), round(top + 0.1 - base, 2), round(float(yaw), 1),
                     int(rng.integers(0, 6))])
    rocks = dict(
        schema='raftsim.pacuare.huacas_evidence_rocks.v1',
        level='/Game/RaftSim/Maps/L_UpperHuacas', river_id='pacuare', section_id='huacas_evidence_2017',
        frame=dict(placement['frame'], z_cm='base elevation - %.1f m datum' % datum),
        instance_fields=['x_cm', 'y_cm', 'base_z_cm', 'length_m', 'width_m', 'height_m', 'yaw_deg', 'variant'],
        source='evidence class 3 components (emergent rock: orthophoto location, size-scaled height) of '
               + rel(args.evidence / 'evidence_grid.npz'),
        evidence_grid_sha256=placement['inputs']['evidence_grid_sha256'],
        method='equal-area footprint ellipse (centroid, principal-axis ratio, pixel area) measured; base 0.4 m below the reference surface (median of '
               'the evidence surface within 3 m), top 0.1 m above the terrain bump (heights INFERRED); variant = one of the six '
               'rights-reviewed rock meshes',
        area_range_m2=list(args.rock_area_m2), component_count=len(rock_comps), instance_count=len(rows),
        collision='visual only (the Landscape bump is the collision and the solver obstacle)',
        terrain_or_hydraulic_geometry_modified=False, instances=rows)
    rock_out.write_text(json.dumps(rocks, separators=(',', ':')) + '\n')

    # review: orthophoto with forest outline, crowns (red) and infill (blue)
    img = np.clip(rgb, 0, 255).astype(np.uint8)
    img[forest & dilate(~forest, 1)] = (255, 255, 0)
    img[near_channel & ~channel] = (0, 200, 255)
    for (x, y), k in zip(points.astype(int), kind):
        img[max(y - 1, 0):y + 2, max(x - 1, 0):x + 2] = (255, 40, 40) if k == 0 else (60, 90, 255)
    write_png(out.with_suffix('.png'), img)
    print(json.dumps(placement['statistics'], indent=1))
    print(f'rock shells {len(rows)} of {len(rock_comps)} components')


if __name__ == '__main__':
    main()
