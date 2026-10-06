"""Closed, layered rainforest on the Pacuare Huacas Landscape (numpy only).

    densify_pacuare_rainforest.py

The evidence canopy (build_pacuare_evidence_dressing.py, then
add_pacuare_huacas_falls.py) placed the IGN-forest trees with crowns of 0.7 x
their neighbour spacing (3.5-5.8 m) and 14-21 m tall, one 3-6 m shrub each, on
the hazy orthophoto drape. In game the walls read as separate lollipop trees
on pale ground, where the observations describe dense rainforest spilling down
the gorge walls to the water (huacas_observations_2026_09_29.json) and the IGN
cover and orthophoto show a closed canopy. Costa Rica's Caribbean-slope wet
forest stands 25-35 m with emergents above, a sub-canopy beneath and a dense
shrub layer. This pass rebuilds the structure (INFERRED) on the same measured
positions and cover:

* canopy: crown radius 1.0 x the neighbour spacing (4.5-10 m), so neighbouring
  crowns overlap into a closed canopy; heights 3.4 x radius + U(0, 6) m, 18-38 m;
* sub-canopy (kind 2): one 9-16 m tree (crown 2.8-4.5 m) in the gap beside
  each canopy tree, at least 3 m from any trunk;
* understory: two 4-8 m shrubs (5-9 m wide) per canopy tree;
* forest floor: drape pixels under the crowns darkened to shaded forest floor
  (x 0.6, toward dark green), so gaps read as shade, not pale ground.

Nothing is placed in or within 4 m of the cooked water, and the Huacas Falls
fall line keeps a 9 m clearance (its painted cascade is not darkened). The
canopy's original crown and infill rows are kept by position (kinds 0 and 1);
re-running regenerates the sub-canopy, understory and drape from them, so the
pass is repeatable. The terrain manifest's drape hash and the canopy's
terrain-manifest hash are updated.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from build_pacuare_evidence_dressing import nearest_distance  # noqa: E402
from build_pacuare_evidence_grid import box_mean  # noqa: E402
from export_hance_evidence_runtime import write_png_rgb  # noqa: E402
from png_numpy import read_png  # noqa: E402

P = ROOT / 'physics/data/real_world/pacuare_river_costa_rica'
T = P / 'terrain/huacas_evidence_2017'
COOKED = P / 'scenario_huacas_evidence_2017/cooked_flow_fields'
SEED = 20261005
FALL_CLEARANCE_M = 9.0
WATER_CLEARANCE_CELLS = 2      # 2 m cooked cells


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def replace_via(path, write):
    tmp = Path(str(path) + '.tmp')
    write(tmp)
    os.replace(tmp, path)


def main():
    canopy_path = T / 'huacas_evidence_canopy_placement.json'
    tm_path = T / 'huacas_evidence_terrain_manifest.json'
    canopy = json.loads(canopy_path.read_text(encoding='utf-8'))
    tm = json.loads(tm_path.read_text(encoding='utf-8'))
    fall = json.loads((T / 'huacas_evidence_observed_waterfall.json').read_text(encoding='utf-8'))
    rng = np.random.default_rng(SEED)

    # the measured crown and infill positions (kinds 0 and 1)
    rows = [r for r in canopy['instances'] if int(r[6]) in (0, 1)]
    pts = np.array([r[:2] for r in rows], float) / 100.0          # Landscape metres (x east, y south)
    nn = nearest_distance(pts)

    # exclusion: the cooked water (+4 m) and the Huacas Falls fall line
    cmap = json.loads((T / 'huacas_evidence_runtime_coordinate_map.json').read_text(encoding='utf-8'))
    C = np.array(cmap['points'], float)
    st, cx, cy = C[:, 0], C[:, 1], C[:, 2]                      # local east / north metres
    tx, ty = np.gradient(cx), np.gradient(cy); n = np.hypot(tx, ty); tx /= n; ty /= n
    manifest = json.loads((COOKED / 'manifest.json').read_text(encoding='utf-8'))
    g = manifest['grid']; band = manifest['bands'][0]['band_id']
    wet = np.load(COOKED / band / 'wet_mask.npy') > 0               # (ny lateral, nx station)
    grown = wet.copy()
    for _ in range(WATER_CLEARANCE_CELLS):
        grown[1:] |= grown[:-1].copy(); grown[:-1] |= grown[1:].copy()
        grown[:, 1:] |= grown[:, :-1].copy(); grown[:, :-1] |= grown[:, 1:].copy()
    base = np.array(fall['base_cm'], float) / 100.0; lip = np.array(fall['lip_cm'], float) / 100.0

    def nearest_centreline(east, north, chunk=2000):
        return np.concatenate([np.argmin((east[i:i + chunk, None] - cx[None, :]) ** 2 +
                                         (north[i:i + chunk, None] - cy[None, :]) ** 2, axis=1)
                               for i in range(0, len(east), chunk)])

    def allowed(xy):
        east, north = xy[:, 0], -xy[:, 1]
        k = nearest_centreline(east, north)
        lat = (east - cx[k]) * -ty[k] + (north - cy[k]) * tx[k]
        col = np.clip(np.round((st[k] - g['origin_x_m']) / g['dx_m']).astype(int), 0, g['nx'] - 1)
        row = np.round((lat - g['origin_y_m']) / g['dy_m']).astype(int)
        inside = (row >= 0) & (row < g['ny'])
        in_water = np.zeros(len(xy), bool)
        in_water[inside] = grown[row[inside], col[inside]]
        v = lip - base; u = np.clip(((xy - base) @ v) / max(v @ v, 1e-9), 0, 1)
        near_fall = np.hypot(*(xy - (base + u[:, None] * v)).T) < FALL_CLEARANCE_M
        return ~in_water & ~near_fall

    # canopy: overlapping crowns, taller stand
    radius = np.clip(1.0 * nn, 4.5, 10.0)
    # crowns beside the fall line must not close over the cascade
    v = lip - base; u = np.clip(((pts - base) @ v) / max(v @ v, 1e-9), 0, 1)
    fall_dist = np.hypot(*(pts - (base + u[:, None] * v)).T)
    radius = np.minimum(radius, np.maximum(fall_dist - 1.5, 3.0))
    height =np.clip(3.4 * radius + rng.uniform(0.0, 6.0, len(rows)), 18.0, 38.0)
    for r, rad, h in zip(rows, radius, height):
        r[3] = round(float(rad), 2); r[4] = round(float(h), 1)

    # sub-canopy in the gaps
    ang = rng.uniform(0, 2 * np.pi, len(pts))
    cand = pts + np.column_stack([np.cos(ang), np.sin(ang)]) * (nn * rng.uniform(0.5, 0.8, len(pts)))[:, None]
    span_x = tm['landscape']['horizontal_span_x_m']; span_y = tm['landscape']['horizontal_span_y_m']
    ok = (cand[:, 0] >= 0) & (cand[:, 0] <= span_x) & (np.abs(cand[:, 1]) <= span_y / 2) & allowed(cand)
    cand = cand[ok]
    # at least 3 m from any trunk (canopy or accepted sub-canopy), on a 3 m hash grid
    occupied = {}
    for p in pts:
        occupied.setdefault((int(p[0] // 3), int(p[1] // 3)), []).append(p)
    sub = []
    for p in cand:
        cxk, cyk = int(p[0] // 3), int(p[1] // 3)
        near = [q for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in occupied.get((cxk + dx, cyk + dy), ())]
        if all(np.hypot(*(p - q)) >= 3.0 for q in near):
            sub.append(p); occupied.setdefault((cxk, cyk), []).append(p)
    sub = np.array(sub)
    s_rad = rng.uniform(2.8, 4.5, len(sub)); s_h = rng.uniform(9.0, 16.0, len(sub))
    s_form = rng.integers(0, 2, len(sub)); s_yaw = rng.uniform(0, 360, len(sub))
    sub_rows = [[round(float(x * 100), 1), round(float(y * 100), 1), 0.0, round(float(s_rad[k]), 2), round(float(s_h[k]), 1),
                 int(s_form[k]), 2, round(float(s_yaw[k]), 1)] for k, (x, y) in enumerate(sub)]

    # understory: two shrubs per canopy tree
    reps = np.repeat(np.arange(len(pts)), 2)
    ua = rng.uniform(0, 2 * np.pi, len(reps)); ud = radius[reps] * rng.uniform(0.3, 1.0, len(reps))
    upts = pts[reps] + np.column_stack([np.cos(ua), np.sin(ua)]) * ud[:, None]
    uok = (upts[:, 0] >= 0) & (upts[:, 0] <= span_x) & (np.abs(upts[:, 1]) <= span_y / 2) & allowed(upts)
    upts = upts[uok]
    u_h = rng.uniform(4.0, 8.0, len(upts)); u_w = rng.uniform(5.0, 9.0, len(upts)); u_yaw = rng.uniform(0, 360, len(upts))
    understory = [[round(float(x * 100), 1), round(float(y * 100), 1), round(float(u_h[k]), 2), round(float(u_w[k]), 2),
                   round(float(u_yaw[k]), 1)] for k, (x, y) in enumerate(upts)]

    # forest-floor shade in the drape under the crowns (not on the painted
    # falls); applied once (the manifest records it), re-runs keep the drape
    drape_path = ROOT / tm['outputs']['drape']
    if 'forest_floor_shade' in tm:
        write_canopy(canopy, rows, sub_rows, understory, radius, height, tm_path, canopy_path)
        return
    drape = read_png(drape_path)[..., :3].astype(np.float32)
    H, W = drape.shape[:2]
    cover = np.zeros((H, W), bool)
    all_xy = np.vstack([pts, sub]); all_r = np.concatenate([radius, s_rad])
    px_m, py_m = span_x / W, span_y / H
    for (x, y), rad in zip(all_xy, all_r):
        c0, r0 = x / px_m, (y + span_y / 2) / py_m
        rc, rr = 0.8 * rad / px_m, 0.8 * rad / py_m
        a0, a1 = int(max(c0 - rc, 0)), int(min(c0 + rc + 1, W)); b0, b1 = int(max(r0 - rr, 0)), int(min(r0 + rr + 1, H))
        if a0 >= a1 or b0 >= b1:
            continue
        yy, xx = np.mgrid[b0:b1, a0:a1]
        cover[b0:b1, a0:a1] |= ((xx - c0) / rc) ** 2 + ((yy - r0) / rr) ** 2 <= 1.0
    gy, gx = np.mgrid[0:H, 0:W]
    pix = np.column_stack([(gx.ravel() + 0.5) * px_m, (gy.ravel() + 0.5) * py_m - span_y / 2])
    v = lip - base; u = np.clip(((pix - base) @ v) / max(v @ v, 1e-9), 0, 1)
    fall_px = (np.hypot(*(pix - (base + u[:, None] * v)).T) < FALL_CLEARANCE_M + 3.0).reshape(H, W)
    # Feathered weight that closes the small gaps between crown ellipses
    # (a hard mask leaves a pale lattice between crowns).
    weight = np.clip(1.6 * box_mean(cover.astype(np.float32), 4), 0.0, 1.0)
    weight[fall_px] = 0.0
    weight = box_mean(weight, 2)[..., None]
    shade = weight[..., 0] > 0.5
    floor = np.array([34.0, 46.0, 28.0], np.float32)             # shaded wet-forest floor (sRGB)
    drape = np.clip(drape * (1.0 - 0.67 * weight) + floor * 0.45 * weight, 0, 255)
    replace_via(drape_path, lambda t: write_png_rgb(t, drape.astype(np.uint8)))

    tm['outputs']['drape_sha256'] = sha(drape_path)
    tm['forest_floor_shade'] = dict(generator='physics/scripts/densify_pacuare_rainforest.py',
                                    shaded_share=round(float(shade.mean()), 4),
                                    method='drape x (1 - 0.67 w) + shaded forest floor (34, 46, 28) x 0.45 w, w the '
                                           'crown cover (0.8 x crown radius) feathered over 9 px; the painted falls '
                                           'are kept')
    replace_via(tm_path, lambda t: t.write_text(json.dumps(tm, indent=2) + '\n'))
    write_canopy(canopy, rows, sub_rows, understory, radius, height, tm_path, canopy_path)
    print(json.dumps(dict(shaded_share=tm['forest_floor_shade']['shaded_share'])))


def write_canopy(canopy, rows, sub_rows, understory, radius, height, tm_path, canopy_path):
    canopy['instances'] = rows + sub_rows
    canopy['understory'] = understory
    canopy['kinds']['2'] = 'sub-canopy tree in the gap beside a canopy tree (position and size INFERRED)'
    canopy['parameters']['crown_radius'] = '1.0 x nearest-neighbour distance, 4.5-10 m (closed, overlapping canopy)'
    canopy['parameters']['height'] = '3.4 x crown radius + U(0, 6) m, 18-38 m'
    canopy['rainforest_structure'] = dict(
        generator='physics/scripts/densify_pacuare_rainforest.py', seed=SEED,
        observation='dense rainforest spilling down the gorge walls to the water; closed canopy in the IGN cover and '
                    'orthophoto; Caribbean-slope wet forest 25-35 m with emergents, sub-canopy and shrub layer',
        sub_canopy='one 9-16 m tree (crown 2.8-4.5 m) beside each canopy tree, >= 3 m from any trunk',
        understory='two 4-8 m shrubs (5-9 m wide) per canopy tree',
        clearance=dict(cooked_water_m=2.0 * WATER_CLEARANCE_CELLS, huacas_falls_m=FALL_CLEARANCE_M),
        inferred=True)
    stats = canopy['statistics']
    stats.update(instance_count=len(canopy['instances']), understory_count=len(understory),
                 canopy_tree_count=len(rows), sub_canopy_count=len(sub_rows),
                 crown_radius_m_p10_p50_p90=[float(x) for x in np.percentile(radius, [10, 50, 90])],
                 height_m_p10_p50_p90=[float(x) for x in np.percentile(height, [10, 50, 90])])
    canopy['inputs']['terrain_manifest_sha256'] = sha(tm_path)
    replace_via(canopy_path, lambda t: t.write_text(json.dumps(canopy, separators=(',', ':')) + '\n', encoding='utf-8'))
    print(json.dumps(dict(canopy_trees=len(rows), sub_canopy=len(sub_rows), understory=len(understory),
                          radius_p50=stats['crown_radius_m_p10_p50_p90'][1], height_p50=stats['height_m_p10_p50_p90'][1])))


if __name__ == '__main__':
    main()
