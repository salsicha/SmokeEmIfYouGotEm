"""Evidence canopy for the Zambezi upper-gorge Landscape (numpy only).

Sentinel-2 at 10 m resolves forest cover but not crowns, so this is the
Pacuare canopy method without its crown detection:

* woodland cover (measured, 10 m): NDVI > --ndvi-min on the 2025-05-28
  image (end of the rains; in the October low-water images the savanna is
  leafless), cleaned by a 30 m majority; minus a clearance around the
  wetted channel and slopes above --max-slope-deg. The gorge-floor riverine
  woodland, the spray-fed rainforest by the falls and the woodland on the
  rims all read green in May;
* positions: a jittered --spacing-m lattice inside the cover (INFERRED);
* crown radius 0.7 x the neighbour spacing (2.5-6 m), heights 2.2 x radius
  + up to 3 m (6-18 m), all the broadleaf form: INFERRED (no species
  inventory);
* understory: one sub-canopy shrub beside each tree within
  --understory-reach-m of the water (INFERRED structure).
* nothing stands in the cooked water: cells wet in the runtime atlas
  (h > 2 cm) join the channel clearance, because the cook's water is wider
  than the Sentinel-2 low-water extent on the gentle inferred banks.

Output: upper_gorge_evidence_2025_canopy_placement.json (Pacuare canopy layout,
schema raftsim.zambezi.upper_gorge_evidence_canopy.v1) and a review PNG,
in the Landscape frame of the terrain manifest.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from build_pacuare_evidence_dressing import dilate, nearest_distance
from build_pacuare_evidence_grid import box_mean, edt_inside
from png_numpy import write_png

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'physics/data/real_world/zambezi_batoka_gorge/zambezi_sources_2026_09'
SEED = 20260927


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def cook_wet_mask(atlas_manifest, nx, ny, y_top, centre_n, wet_m=0.02):
    """Cells of the 1 m evidence window that are wet in the runtime atlas.

    Atlas tile origins are the first cell centres in local metres (east of
    the west edge, north of centre_n), 2 m cells, rows northward."""
    atlas = json.loads(Path(atlas_manifest).read_text(encoding='utf-8'))
    t = atlas['tile_shape'][0]; d = atlas['grid_spacing_m']
    h = np.load(Path(atlas_manifest).parent / atlas['arrays']['h']['file'])
    wet = np.zeros((ny, nx), bool)
    x = np.arange(nx) + 0.5
    for k, tile in enumerate(atlas['tiles']):
        ox, oy = tile['origin_m']
        c0 = max(int(np.floor(ox - d / 2)), 0); c1 = min(int(np.ceil(ox + (t - 0.5) * d)), nx)
        n_lo, n_hi = oy - d / 2, oy + (t - 0.5) * d
        r0 = max(int(np.floor(y_top - centre_n - n_hi)), 0); r1 = min(int(np.ceil(y_top - centre_n - n_lo)), ny)
        if c0 >= c1 or r0 >= r1:
            continue
        cols = np.clip(np.floor((x[c0:c1] - (ox - d / 2)) / d).astype(int), 0, t - 1)
        north = (y_top - (np.arange(r0, r1) + 0.5)) - centre_n
        rows = np.clip(np.floor((north - (oy - d / 2)) / d).astype(int), 0, t - 1)
        wet[r0:r1, c0:c1] |= h[k * t:(k + 1) * t][rows][:, cols] > wet_m
    return wet


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path, help='build_zambezi_evidence_grid.py output folder')
    ap.add_argument('--terrain-manifest', type=Path, required=True)
    ap.add_argument('--out-dir', type=Path, required=True)
    ap.add_argument('--sentinel2', default='S2A_T35KLA_20250528T083438_L2A.npz')
    ap.add_argument('--ndvi-min', type=float, default=0.5)
    ap.add_argument('--green-max', type=float, default=1.0, help='no brightness test: there is no pasture in the gorge')
    ap.add_argument('--channel-clearance-m', type=int, default=4)
    ap.add_argument('--spacing-m', type=float, default=10.0)
    ap.add_argument('--max-slope-deg', type=float, default=62.0)
    ap.add_argument('--runtime-atlas', type=Path,
                    default=ROOT / 'physics/data/real_world/zambezi_batoka_gorge/scenario_upper_gorge_evidence_2025/'
                                   'cartesian_runtime/atlas/manifest.json',
                    help='runtime atlas whose wet cells are kept clear of vegetation')
    ap.add_argument('--understory-reach-m', type=float, default=120.0)
    args = ap.parse_args()
    out = args.out_dir.resolve() / 'upper_gorge_evidence_2025_canopy_placement.json'
    assert not out.exists(), 'fresh output required'

    manifest = json.loads((args.evidence / 'manifest.json').read_text(encoding='utf-8'))
    g = manifest['grid']
    X0, Y1, NX, NY = g['x0'], g['y_top'], g['nx'], g['ny']
    ev = np.load(args.evidence / 'evidence_grid.npz')
    river, dem = ev['river'], ev['dem'].astype(np.float64)
    land = json.loads(args.terrain_manifest.read_text(encoding='utf-8'))['landscape']
    west_e = land['world_origin_epsg32735_m']['west_edge_e']; centre_n = land['world_origin_epsg32735_m']['centre_n']
    datum = land['runtime_vertical_datum_m']
    assert (west_e, land['horizontal_span_x_m'], land['horizontal_span_y_m']) == (X0, NX, NY)

    # forest cover from Sentinel-2 (10 m) on the 1 m window
    fm = json.loads((SRC / 'sentinel2/fetch_manifest.json').read_text())
    item = next(i for i in fm['items'] if i['npz'] == args.sentinel2)
    w = item['window_utm_m']; z = np.load(SRC / 'sentinel2' / args.sentinel2)
    Gr, R, N = [z[k].astype(np.float32) * 1e-4 - 0.1 for k in ('green', 'red', 'nir')]
    ndvi = (N - R) / np.maximum(N + R, 1e-3)
    forest10 = (ndvi > args.ndvi_min) & (Gr < args.green_max)
    cc = np.clip(((X0 + np.arange(NX) + 0.5 - w['xmin']) / 10.0).astype(int), 0, forest10.shape[1] - 1)
    rr = np.clip(((w['ymax'] - (Y1 - np.arange(NY) - 0.5)) / 10.0).astype(int), 0, forest10.shape[0] - 1)
    forest = forest10[rr][:, cc]
    forest = box_mean(forest.astype(np.float32), 15) > 0.5
    gy, gx = np.gradient(dem)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    # The cook's water is wider than the Sentinel-2 low-water extent where the
    # inferred banks are gentle (surface ~0.5 m high), so trees on "dry" image
    # pixels stood in the river; keep them out of the cooked water too.
    cook_wet = cook_wet_mask(args.runtime_atlas, NX, NY, Y1, centre_n)
    allowed = (forest & ~dilate(river | cook_wet, args.channel_clearance_m) &
               (slope <= args.max_slope_deg))
    # Reconstructed gorge walls (reconstruct_zambezi_gorge_walls.py): the
    # observed walls are bare basalt, so the cliff zone and its ledges carry
    # no trees; the talus aprons below keep their woodland.
    cliff_cells = 0
    if 'wall_zone' in ev.files:
        cliff = dilate(ev['wall_zone'] == 3, 1)
        cliff_cells = int((allowed & cliff).sum())
        allowed &= ~cliff

    rng = np.random.default_rng(SEED)
    s = args.spacing_m
    gxv, gyv = np.meshgrid(np.arange(s / 2, NX, s), np.arange(s / 2, NY, s))
    pts = np.column_stack([gxv.ravel(), gyv.ravel()]) + rng.uniform(-0.35, 0.35, (gxv.size, 2)) * s
    pts = pts[(pts[:, 0] >= 0) & (pts[:, 0] < NX) & (pts[:, 1] >= 0) & (pts[:, 1] < NY)]
    pts = pts[allowed[pts[:, 1].astype(int), pts[:, 0].astype(int)]]
    radius = np.clip(0.7 * nearest_distance(pts), 2.5, 6.0)
    height = np.clip(2.2 * radius + rng.uniform(0.0, 3.0, len(pts)), 6.0, 18.0)
    form = np.zeros(len(pts), int); yaw = rng.uniform(0, 360, len(pts))
    r_i, c_i = pts[:, 1].astype(int), pts[:, 0].astype(int)
    x_cm = pts[:, 0] * 100.0; y_cm = -((Y1 - pts[:, 1]) - centre_n) * 100.0
    z_cm = (dem[r_i, c_i] - datum) * 100.0
    instances = [[round(float(x_cm[k]), 1), round(float(y_cm[k]), 1), round(float(z_cm[k]), 1), round(float(radius[k]), 2),
                  round(float(height[k]), 1), int(form[k]), 1, round(float(yaw[k]), 1)] for k in range(len(pts))]
    # understory near the water (INFERRED)
    dist_w = edt_inside(~river)
    near = dist_w[r_i, c_i] <= args.understory_reach_m
    ang = rng.uniform(0.0, 2.0 * np.pi, len(pts)); dist = radius * rng.uniform(0.4, 0.9, len(pts))
    upts = (pts + np.column_stack([np.cos(ang), np.sin(ang)]) * dist[:, None])[near]
    ok = (upts[:, 0] >= 0) & (upts[:, 0] < NX) & (upts[:, 1] >= 0) & (upts[:, 1] < NY)
    upts = upts[ok]
    upts = upts[allowed[upts[:, 1].astype(int), upts[:, 0].astype(int)]]
    u_h = rng.uniform(3.0, 6.0, len(upts)); u_w = rng.uniform(4.0, 7.0, len(upts)); u_yaw = rng.uniform(0, 360, len(upts))
    understory = [[round(float(x * 100.0), 1), round(float(-((Y1 - y) - centre_n) * 100.0), 1), round(float(u_h[k]), 2),
                   round(float(u_w[k]), 2), round(float(u_yaw[k]), 1)] for k, (x, y) in enumerate(upts)]

    placement = dict(
        schema='raftsim.zambezi.upper_gorge_evidence_canopy.v1',
        level='/Game/RaftSim/Maps/L_ZambeziUpperGorge', river_id='zambezi_batoka_gorge', section_id='upper_gorge_evidence_2025',
        frame=dict(x_cm='east of the Landscape west edge (EPSG:32735 E - %.1f) x 100' % west_e,
                   y_cm='south of the Landscape centre row (-(N - %.1f)) x 100' % centre_n,
                   z_cm='evidence terrain - %.1f m datum (information only; the editor grounds on the Landscape)' % datum),
        instance_fields=['x_cm', 'y_cm', 'terrain_z_cm', 'crown_radius_m', 'height_m', 'form', 'kind', 'yaw_deg'],
        kinds={'1': 'lattice inside Sentinel-2 forest cover; 10 m imagery resolves no crowns (position INFERRED)'},
        forms={'0': 'the broadleaf canopy form (dry woodland and riverine trees; species INFERRED)'},
        inputs=dict(evidence_manifest=rel(args.evidence / 'manifest.json'), evidence_grid_sha256=sha(args.evidence / 'evidence_grid.npz'),
                    sentinel2=args.sentinel2, sentinel2_sha256=item['npz_sha256'],
                    terrain_manifest=rel(args.terrain_manifest), terrain_manifest_sha256=sha(args.terrain_manifest),
                    runtime_atlas=rel(args.runtime_atlas), runtime_atlas_sha256=sha(args.runtime_atlas)),
        parameters=dict(ndvi_min=args.ndvi_min, green_max=args.green_max, majority_window_m=31, channel_clearance_m=args.channel_clearance_m,
                        spacing_m=args.spacing_m, max_slope_deg=args.max_slope_deg, understory_reach_m=args.understory_reach_m,
                        crown_radius='0.7 x nearest-neighbour distance, 2.5-6 m', height='2.2 x crown radius + U(0, 3) m, 6-18 m', seed=SEED),
        statistics=dict(forest_share=float(forest.mean()), allowed_share=float(allowed.mean()), instance_count=int(len(pts)),
                        cliff_cells_excluded=cliff_cells,
                        cook_wet_share=float(cook_wet.mean()), cook_wet_outside_sentinel2_share=float((cook_wet & ~river).mean()),
                        understory_count=int(len(upts)),
                        crown_radius_m_p10_p50_p90=[float(v) for v in np.percentile(radius, [10, 50, 90])],
                        height_m_p10_p50_p90=[float(v) for v in np.percentile(height, [10, 50, 90])]),
        positions_from_imagery=False, cover_from_imagery=True, tree_inventory_surveyed=False, species_heights_and_forms_inferred=True,
        collision='visual only (no collision)', terrain_or_hydraulic_geometry_modified=False, instances=instances,
        understory_fields=['x_cm', 'y_cm', 'height_m', 'width_m', 'yaw_deg'],
        understory_mesh='the reach shrub mesh (sub-canopy structure INFERRED)', understory=understory)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(placement, separators=(',', ':')) + '\n')
    rgb = np.load(args.evidence / 'sentinel2_rgb.npz')['rgb'].copy()
    rgb[forest & dilate(~forest, 1)] = (255, 255, 0)
    for x, y in pts.astype(int)[::1]:
        rgb[max(y - 1, 0):y + 2, max(x - 1, 0):x + 2] = (60, 90, 255)
    write_png(out.with_suffix('.png'), rgb[::2, ::2])
    print(json.dumps(placement['statistics'], indent=1))


if __name__ == '__main__':
    main()
