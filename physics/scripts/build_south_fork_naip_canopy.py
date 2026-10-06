"""Full-corridor South Fork tree placement from NAIP canopy evidence.

Outside the Troublemaker rapid (LiDAR/NAIP canopy, 1,268 trees) and the Chili
Bar put-in (captured canopy), the normal FullReach map has no vegetation, so
33 km of oak/pine woodland renders as bare hills. This builder places trees
where the repository's NAIP drape (`build_south_fork_naip_drape.py`, 1.22 m,
registered to the terrain within ~5 m) shows tree canopy:

* canopy pixel: valid drape (not submerged bed), sRGB luma < 0.33 and G >= R
  (dark green crowns; dry grass, roads, roofs and bare ground excluded);
* a jittered 6.5 m candidate lattice keeps a tree where at least half of a
  3 m-radius disc is canopy, on terrain no steeper than 40 degrees, at least
  2 m from the submerged bed, and not within 6 m of an existing captured tree
  or inside the registered Troublemaker domain.

What is evidence and what is inferred:
* positions and canopy extent: NAIP 2022 imagery (canopy-top colour), coarse;
* root elevation: the terrain's own captured surface grid (verified again by
  line traces against the rendered collision in Unreal);
* species, heights, crown forms and individual trunk positions: INFERRED
  (riparian white alder within 25 m of the water, interior live oak elsewhere
  with ~15% pine), not a surveyed tree inventory.

Run inside Blender (`--background --python`) for image I/O.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FULL = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
DEM = FULL / 'source_context_extension/captured_surface_navd88_m.tif'
CONTEXT = FULL / 'source_context_extension/manifest.json'
COMPOSITE = FULL / 'composite_terrain/manifest.json'
EXISTING = [FULL / 'playable_route/captured_canopy_placement_v1.json',
            ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/chili_bar/canopy_20260918/placement.json']
WORLD_ORIGIN_UTM = (689237.0, 4293073.0)
DATUM_M = 220.0

SPACING_M = 6.5
DISC_R_M = 3.0
CANOPY_MIN_FRACTION = 0.5
LUMA_MAX = 0.33
MAX_SLOPE_DEG = 40.0
WATER_CLEARANCE_M = 2.0
RIPARIAN_M = 25.0
EXISTING_CLEARANCE_M = 6.0
SEED = 20260926

# form index -> (mesh package, nominal mesh height m, height range m)
FORMS = [
    ('/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_SpreadingMature', (8.0, 12.0)),
    ('/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_AsymmetricCompetition', (7.0, 11.0)),
    ('/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/SM_RaftSim_SouthForkInteriorLiveOakCrownFamilyV3_CompactRiverEdge', (6.0, 9.5)),
    ('/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/SM_RaftSim_SouthForkWhiteAlder_ConnectedCrownV2', (9.0, 15.0)),
    ('/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/SM_RaftSim_SouthForkPonderosaMature_ConnectedCrownV1', (13.0, 21.0)),
    ('/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/SM_RaftSim_SouthForkPonderosaIntermediate_ConnectedCrownV1', (10.0, 16.0)),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, non_color=True):
    img = bpy.data.images.load(str(path))
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    arr = np.empty(w * h * img.channels, dtype=np.float32)
    img.pixels.foreach_get(arr)
    arr = arr.reshape(h, w, img.channels)[::-1]
    bpy.data.images.remove(img)
    return arr


def box_mean(mask, radius_px):
    """Mean of a boolean/float image over a square window (integral image)."""
    k = int(radius_px)
    c = np.pad(mask.astype(np.float64), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    h, w = mask.shape
    y0 = np.clip(np.arange(h) - k, 0, h); y1 = np.clip(np.arange(h) + k + 1, 0, h)
    x0 = np.clip(np.arange(w) - k, 0, w); x1 = np.clip(np.arange(w) + k + 1, 0, w)
    s = c[y1][:, x1] - c[y0][:, x1] - c[y1][:, x0] + c[y0][:, x0]
    area = (y1 - y0)[:, None] * (x1 - x0)[None, :]
    return (s / area).astype(np.float32)


def dilate_distance(seed, steps, step_m):
    """Approximate distance (m) to the nearest seed pixel by 8-neighbour dilation."""
    dist = np.full(seed.shape, np.inf, dtype=np.float32)
    front = seed.copy()
    dist[front] = 0.0
    for i in range(1, steps + 1):
        grown = front.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                grown |= np.roll(np.roll(front, dy, 0), dx, 1)
        new = grown & ~front
        dist[new] = i * step_m
        front = grown
    return dist


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    drape_dir = Path(args[0]).resolve()
    out_dir = Path(args[1]).resolve()
    out_dir.mkdir(parents=True, exist_ok=False)
    receipt = json.loads((drape_dir / 'receipt.json').read_text())
    px = receipt['pixel_m']
    e0, n_top = receipt['top_left_utm_m']
    used = receipt['used_rows']

    drape = load(drape_dir / 'T_SouthForkFullReachNAIP.png')[:used]
    rgb, alpha = drape[..., :3], drape[..., 3]
    luma = rgb.mean(axis=2)
    valid = alpha > 0.5
    canopy = valid & (luma < LUMA_MAX) & (rgb[..., 1] - rgb[..., 0] > -0.005)
    fraction = box_mean(canopy, round(DISC_R_M / px))
    del drape, rgb, luma

    # Submerged bed (drape alpha 0 inside the corridor) -> water distance on a 2x grid.
    ctx = json.loads(CONTEXT.read_text())
    ge0, gn_top = ctx['grid']['first_vertex_utm_m']
    gcell = ctx['grid']['cell_m']
    dem = load(DEM)[..., 0]
    comp = json.loads(COMPOSITE.read_text())
    # The DEM extends beyond the old composite footprint. Sampling that old
    # mask with clipped indices admitted canopy over the added river channel.
    water_mask_path = DEM.parent / 'unknown_submerged_bed_mask.tif'
    mask_raw = load(water_mask_path)[..., 0] * 255.0
    assert mask_raw.shape == dem.shape, 'Water mask must share the context DEM grid'
    submerged = np.abs(mask_raw - 1.0) < 0.5
    me0, mn_top = ctx['grid']['first_vertex_utm_m']
    water_dist = dilate_distance(submerged, int(RIPARIAN_M / gcell) + 2, gcell)
    water_dist[mask_raw > 254.5] = -1.0  # Unknown coverage cannot admit a tree.

    # Existing captured canopy roots (world cm) -> UTM for exclusion.
    existing = []
    for path in EXISTING:
        data = json.loads(path.read_text())
        for row in data['instances']:
            x, y, _ = row['world_root_cm']
            existing.append((x / 100.0 + WORLD_ORIGIN_UTM[0], WORLD_ORIGIN_UTM[1] - y / 100.0))
    existing = np.array(existing)
    tm = comp['inner_boundary_utm_m']

    rng = np.random.default_rng(SEED)
    e_max = e0 + px * drape_dir.stat().st_size * 0 + px * 16384
    n_min = n_top - px * used
    ge = np.arange(e0 + SPACING_M / 2, e0 + px * 16384, SPACING_M)
    gn = np.arange(n_min + SPACING_M / 2, n_top, SPACING_M)
    E, N = np.meshgrid(ge, gn)
    E = E + rng.uniform(-0.4, 0.4, E.shape) * SPACING_M
    N = N + rng.uniform(-0.4, 0.4, N.shape) * SPACING_M
    E, N = E.ravel(), N.ravel()
    # canopy fraction at candidates
    ci = np.clip(((n_top - N) / px).astype(np.int64), 0, used - 1)
    cj = np.clip(((E - e0) / px).astype(np.int64), 0, 16383)
    keep = fraction[ci, cj] >= CANOPY_MIN_FRACTION
    E, N, frac = E[keep], N[keep], fraction[ci[keep], cj[keep]]
    # terrain elevation and slope from the captured surface grid (bilinear)
    fi = (gn_top - N) / gcell
    fj = (E - ge0) / gcell
    i0 = np.floor(fi).astype(np.int64); j0 = np.floor(fj).astype(np.int64)
    ok = (i0 >= 1) & (i0 < dem.shape[0] - 2) & (j0 >= 1) & (j0 < dem.shape[1] - 2)
    E, N, frac, fi, fj, i0, j0 = (v[ok] for v in (E, N, frac, fi, fj, i0, j0))
    ti, tj = fi - i0, fj - j0
    z = (dem[i0, j0] * (1 - ti) * (1 - tj) + dem[i0, j0 + 1] * (1 - ti) * tj
         + dem[i0 + 1, j0] * ti * (1 - tj) + dem[i0 + 1, j0 + 1] * ti * tj)
    dzdx = (dem[i0, j0 + 1] - dem[i0, j0 - 1]) / (2 * gcell)
    dzdy = (dem[i0 + 1, j0] - dem[i0 - 1, j0]) / (2 * gcell)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    ok = np.isfinite(z) & np.isfinite(slope) & (slope <= MAX_SLOPE_DEG)
    E, N, frac, z = E[ok], N[ok], frac[ok], z[ok]
    # water clearance / riparian band
    wi = np.round((mn_top - N) / gcell).astype(np.int64)
    wj = np.round((E - me0) / gcell).astype(np.int64)
    assert ((wi >= 0) & (wi < water_dist.shape[0]) & (wj >= 0) & (wj < water_dist.shape[1])).all()
    wd = water_dist[wi, wj]
    ok = wd >= WATER_CLEARANCE_M
    E, N, frac, z, wd = E[ok], N[ok], frac[ok], z[ok], wd[ok]
    # registered rapid domain and existing captured trees
    ok = ~((E >= tm[0]) & (E <= tm[2]) & (N >= tm[1]) & (N <= tm[3]))
    E, N, frac, z, wd = E[ok], N[ok], frac[ok], z[ok], wd[ok]
    if len(existing):
        cell = EXISTING_CLEARANCE_M
        buckets = {}
        for k, (x, y) in enumerate(existing):
            buckets.setdefault((int(x // cell), int(y // cell)), []).append(k)
        near = np.zeros(len(E), bool)
        for k in range(len(E)):
            bx, by = int(E[k] // cell), int(N[k] // cell)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for idx in buckets.get((bx + dx, by + dy), ()):
                        if (existing[idx, 0] - E[k]) ** 2 + (existing[idx, 1] - N[k]) ** 2 < cell * cell:
                            near[k] = True
        E, N, frac, z, wd = E[~near], N[~near], frac[~near], z[~near], wd[~near]

    # inferred species/form and size
    n = len(E)
    u = rng.uniform(0, 1, n)
    riparian = wd <= RIPARIAN_M
    form = np.where(u < 0.40, 0, np.where(u < 0.70, 1, 2))
    pine = ~riparian & (rng.uniform(0, 1, n) < 0.15)
    form = np.where(pine, np.where(rng.uniform(0, 1, n) < 0.6, 4, 5), form)
    form = np.where(riparian & (rng.uniform(0, 1, n) < 0.6), 3, form)
    lo = np.array([FORMS[f][1][0] for f in range(len(FORMS))])[form]
    hi = np.array([FORMS[f][1][1] for f in range(len(FORMS))])[form]
    # denser canopy patches read as taller, more closed stands
    height = lo + (hi - lo) * np.clip(0.35 + 0.65 * (frac - CANOPY_MIN_FRACTION) / (1 - CANOPY_MIN_FRACTION)
                                      + rng.uniform(-0.25, 0.25, n), 0, 1)
    yaw = rng.uniform(0, 360, n)
    x_cm = (E - WORLD_ORIGIN_UTM[0]) * 100.0
    y_cm = -(N - WORLD_ORIGIN_UTM[1]) * 100.0
    z_cm = (z - DATUM_M) * 100.0
    instances = [dict(id=int(k), form_index=int(form[k]), world_root_cm=[round(float(x_cm[k]), 1), round(float(y_cm[k]), 1),
                      round(float(z_cm[k]), 1)], height_m=round(float(height[k]), 2), yaw_degrees=round(float(yaw[k]), 1))
                 for k in range(n)]
    placement = dict(
        schema='raftsim.south_fork.naip_canopy_placement.v1',
        level='/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach', scenario_id='south_fork_full_descent',
        world_y_sign=-1, vertical_datum_m=DATUM_M, world_origin_utm_m=list(WORLD_ORIGIN_UTM),
        drape_receipt=str((drape_dir / 'receipt.json').relative_to(ROOT).as_posix()), drape_sha256=receipt['sha256'],
        sources={str(p.relative_to(ROOT).as_posix()): sha(p) for p in [DEM, water_mask_path, *EXISTING]},
        parameters=dict(spacing_m=SPACING_M, disc_radius_m=DISC_R_M, canopy_min_fraction=CANOPY_MIN_FRACTION,
                        luma_max=LUMA_MAX, max_slope_deg=MAX_SLOPE_DEG, water_clearance_m=WATER_CLEARANCE_M,
                        riparian_band_m=RIPARIAN_M, existing_clearance_m=EXISTING_CLEARANCE_M, seed=SEED),
        assets=[dict(package=p, height_range_m=list(r)) for p, r in FORMS],
        instance_count=n, form_counts={str(f): int((form == f).sum()) for f in range(len(FORMS))},
        canopy_positions_from_imagery=True, tree_inventory_surveyed=False,
        species_heights_and_forms_inferred=True, root_elevation_from_captured_surface=True,
        collision='Visual non-colliding canopy', terrain_or_hydraulic_geometry_modified=False,
        instances=instances)
    path = out_dir / 'placement.json'
    path.write_text(json.dumps(placement, separators=(',', ':')) + '\n')
    summary = {k: placement[k] for k in ('instance_count', 'form_counts', 'parameters')}
    summary['sha256'] = sha(path)
    (out_dir / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('CANOPY_SUMMARY ' + json.dumps(summary))


main()
