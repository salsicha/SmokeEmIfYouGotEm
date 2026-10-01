"""Huacas Falls on the Pacuare Huacas reach, reconstructed from observations (numpy only).

    add_pacuare_huacas_falls.py [--station-m 820] [--height-m 40]

Observations (huacas_observations_2026_09_29.json): "Huacas Falls (R): a
30-46 m fall (100-150 ft) lands on river right between the Huacas rapids, and
rafts paddle under it. IGN shows a steep right wall there" (stations
700-800, river right rises about 80 m within 100 m). The terrain (IGN 1:5,000
contours) carries the wall but no fall, and the 2014-2017 orthophoto, taken
from above through the canopy, shows none either.

The fall is placed at --station-m on river right. Its base is the cooked wet
edge; its line climbs straight up the wall along the outward normal until the
terrain is --height-m above the water (the lip). The cascade is painted into
the drape along that line as white aerated water over dark wet rock: about
5 m wide at the lip, spreading to 8 m at the base, streaked along the fall
line, feathered at its edges. A record of the lip and base in the Landscape
frame (huacas_evidence_observed_waterfall.json) lets the editor put spray
mist at the plunge. Inferred appearance; the terrain, bed and water are not
changed. The terrain manifest's drape hash and a waterfall record are updated.
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
from export_hance_evidence_runtime import write_png_rgb  # noqa: E402
from png_numpy import read_png  # noqa: E402

P = ROOT / 'physics/data/real_world/pacuare_river_costa_rica'
T = P / 'terrain/huacas_evidence_2017'
PREFIX = 'huacas_evidence'
OBS = P / 'observed_rapids/huacas_observations_2026_09_29.json'
SEED = 20261004


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--station-m', type=float, default=820.0)
    ap.add_argument('--height-m', type=float, default=40.0)
    args = ap.parse_args()
    tm_path = T / f'{PREFIX}_terrain_manifest.json'
    tm = json.loads(tm_path.read_text())
    land = tm['landscape']
    from PIL import Image
    hf = np.array(Image.open(T / f'{PREFIX}_heightfield_2017.png')).astype(np.float64)
    z = land['terrain_min_m'] + hf / 65535.0 * (land['terrain_max_m'] - land['terrain_min_m'])
    SX, SY = land['horizontal_span_x_m'], land['horizontal_span_y_m']
    N = hf.shape[0]

    def height(xm, ym):          # Landscape metres: x east of the west edge, y south of the north edge
        c = np.clip(xm / SX * (N - 1), 0, N - 1.001); r = np.clip(ym / SY * (N - 1), 0, N - 1.001)
        i, j = int(r), int(c); a, b = r - i, c - j
        return (1 - a) * (1 - b) * z[i, j] + (1 - a) * b * z[i, j + 1] + a * (1 - b) * z[i + 1, j] + a * b * z[i + 1, j + 1]

    cmap = json.loads((T / f'{PREFIX}_runtime_coordinate_map.json').read_text())
    pts = np.array(cmap['points'], float)
    k = int(np.argmin(np.abs(pts[:, 0] - args.station_m)))
    tx, ty = pts[min(k + 3, len(pts) - 1), 1:3] - pts[max(k - 3, 0), 1:3]
    tn = np.hypot(tx, ty); tx, ty = tx / tn, ty / tn
    lx, ly = -ty, tx
    ck = P / 'scenario_huacas_evidence_2017/cooked_flow_fields'
    man = json.loads((ck / 'manifest.json').read_text()); g = man['grid']; band = man['bands'][0]['band_id']
    wet = np.load(ck / band / 'wet_mask.npy') > 0
    bed = np.load(ck / band / 'bed.npy'); hh = np.load(ck / band / 'h.npy')
    col = int(round(args.station_m / g['dx_m']))
    lats = g['origin_y_m'] + np.arange(g['ny']) * g['dy_m']
    right_edge = float(lats[wet[:, col]].min())
    ws = float((bed[:, col] + hh[:, col])[wet[:, col]].mean())
    # base: the wet edge on river right; local E/N offsets from the Landscape origin
    bx, by = pts[k, 1] + right_edge * lx, pts[k, 2] + right_edge * ly
    to_land = lambda e, n: (e, land['horizontal_span_y_m'] / 2.0 - n)      # (east, north) -> Landscape metres
    line = [to_land(bx, by)]
    # The fall line runs straight up the wall along the outward (river-right)
    # normal: the IGN wall rises steadily that way, while the flat, noisy wet
    # edge gives no reliable steepest-ascent direction.
    step = 0.5
    ox, oy = to_land(bx - lx, by - ly); ox -= line[0][0]; oy -= line[0][1]
    on = np.hypot(ox, oy); ox, oy = ox / on, oy / on
    for _ in range(400):
        x, y = line[-1]
        if height(x, y) - ws >= args.height_m:
            break
        line.append((x + step * ox, y + step * oy))
    line = np.array(line)
    lip_h = height(*line[-1]) - ws
    run = float(np.sum(np.hypot(*np.diff(line, axis=0).T)))
    # paint the drape
    drape_path = T / f'{PREFIX}_drape_2048.png'
    img = read_png(drape_path)[..., :3].astype(np.float64) / 255.0
    D = img.shape[0]
    px = (np.arange(D) + 0.5) * SX / D; py = (np.arange(D) + 0.5) * SY / D
    c0 = int(max(line[:, 0].min() - 15, 0) / SX * D); c1 = int(min(line[:, 0].max() + 15, SX) / SX * D) + 1
    r0 = int(max(line[:, 1].min() - 15, 0) / SY * D); r1 = int(min(line[:, 1].max() + 15, SY) / SY * D) + 1
    XX, YY = np.meshgrid(px[c0:c1], py[r0:r1])
    # distance to the fall line and the along-fall parameter (0 base .. 1 lip)
    seg_a = line[:-1]; seg_b = line[1:]
    cum = np.concatenate([[0.0], np.cumsum(np.hypot(*(seg_b - seg_a).T))])
    best_d = np.full(XX.shape, np.inf); best_t = np.zeros(XX.shape)
    for (ax_, ay_), (bx_, by_), s0, s1 in zip(seg_a, seg_b, cum[:-1], cum[1:]):
        vx, vy = bx_ - ax_, by_ - ay_; L2 = vx * vx + vy * vy
        u = np.clip(((XX - ax_) * vx + (YY - ay_) * vy) / max(L2, 1e-9), 0, 1)
        d = np.hypot(XX - (ax_ + u * vx), YY - (ay_ + u * vy))
        better = d < best_d
        best_d = np.where(better, d, best_d); best_t = np.where(better, (s0 + u * (s1 - s0)) / max(cum[-1], 1e-6), best_t)
    half = 3.0 + 2.0 * (1.0 - best_t)                    # 6 m at the lip, 10 m at the base
    edge = np.clip(1.0 - (best_d - 0.6 * half) / (0.4 * half), 0, 1)
    edge = edge * edge * (3 - 2 * edge)
    rng = np.random.default_rng(SEED)
    # streaks along the fall line: noise across the line, smooth along it
    across = (XX - XX.mean()) * (-(line[-1, 1] - line[0, 1])) + (YY - YY.mean()) * (line[-1, 0] - line[0, 0])
    across /= max(np.hypot(line[-1, 0] - line[0, 0], line[-1, 1] - line[0, 1]), 1e-6)
    phases = rng.uniform(0, 2 * np.pi, 3)
    streak = 0.5 + 0.5 * (0.5 * np.sin(across * 2.1 + phases[0]) + 0.3 * np.sin(across * 4.7 + phases[1])
                          + 0.2 * np.sin(across * 9.3 + phases[2]))
    white = np.array([0.86, 0.89, 0.90]); wet_rock = np.array([0.10, 0.12, 0.11])
    water = wet_rock[None, None] * (1 - streak[..., None]) + white[None, None] * streak[..., None]
    streak = streak ** 0.6                               # mostly white, darker gaps between the strands
    water = wet_rock[None, None] * (1 - streak[..., None]) + white[None, None] * streak[..., None]
    a = (edge * 0.95)[..., None]
    lin = img[r0:r1, c0:c1] ** 2.2
    lin = lin * (1 - a) + (water ** 2.2) * a
    # a wet, darker halo of spray-fed rock and moss around the fall
    halo = np.clip(1.0 - (best_d - half) / 6.0, 0, 1) * (1 - edge)
    lin = lin * (1 - 0.35 * halo[..., None])
    img[r0:r1, c0:c1] = lin ** (1 / 2.2)
    tmp = Path(str(drape_path) + '.tmp.png')
    write_png_rgb(tmp, np.round(np.clip(img, 0, 1) * 255).astype(np.uint8))
    os.replace(tmp, drape_path)
    to_cm = lambda xm, ym: [round(xm * 100.0, 1), round((ym - SY / 2.0) * 100.0, 1)]
    record = dict(
        schema='raftsim.observed_waterfall.v1', name='Huacas Falls', reach='pacuare huacas_evidence_2017',
        generator='physics/scripts/add_pacuare_huacas_falls.py',
        observation='a 30-46 m fall (100-150 ft) lands on river right between the Huacas rapids, and rafts paddle under it; '
                    'IGN shows a steep right wall there',
        observations=OBS.relative_to(ROOT).as_posix(), observations_sha256=sha(OBS),
        station_m=args.station_m, side='right', water_surface_m=round(ws, 2),
        base_cm=to_cm(*line[0]), lip_cm=to_cm(*line[-1]), lip_height_above_water_m=round(float(lip_h), 1),
        horizontal_run_m=round(run, 1),
        frame='Landscape frame: x_cm east of the west edge, y_cm south of the centre row',
        appearance='white aerated water streaked along the fall line over dark wet rock in the drape, 6-10 m wide; spray '
                   'mist at the plunge (editor); canopy and understory removed from the fall line', inferred=True, terrain_or_hydraulic_geometry_modified=False)
    (T / f'{PREFIX}_observed_waterfall.json').write_text(json.dumps(record, indent=1) + '\n', encoding='utf-8')
    # trees and shrubs standing on the fall line would hide it
    canopy_path = T / f'{PREFIX}_canopy_placement.json'
    canopy = json.loads(canopy_path.read_text(encoding='utf-8'))

    def clear(xy_cm):
        q = np.array([xy_cm[0] / 100.0, xy_cm[1] / 100.0 + SY / 2.0])
        sa = seg_a; sb = seg_b; v = sb - sa; L2 = np.maximum((v ** 2).sum(1), 1e-9)
        u = np.clip(((q - sa) * v).sum(1) / L2, 0, 1)
        return np.hypot(*(q - (sa + u[:, None] * v)).T).min() > 7.0
    before = (len(canopy['instances']), len(canopy['understory']))
    canopy['instances'] = [i for i in canopy['instances'] if clear(i)]
    canopy['understory'] = [u for u in canopy['understory'] if clear(u)]
    removed = (before[0] - len(canopy['instances']), before[1] - len(canopy['understory']))
    canopy['statistics']['instance_count'] = len(canopy['instances'])
    canopy['statistics']['understory_count'] = len(canopy['understory'])
    canopy['statistics']['removed_on_huacas_falls'] = list(removed)
    tmp = Path(str(canopy_path) + '.tmp')
    tmp.write_text(json.dumps(canopy, separators=(',', ':')) + '\n', encoding='utf-8'); os.replace(tmp, canopy_path)
    record['canopy_removed_trees_shrubs'] = list(removed)
    (T / f'{PREFIX}_observed_waterfall.json').write_text(json.dumps(record, indent=1) + '\n', encoding='utf-8')
    tm['outputs']['drape_sha256'] = sha(drape_path)
    tm['observed_waterfall'] = dict(record=f'{PREFIX}_observed_waterfall.json', name='Huacas Falls',
                                    drape='cascade painted along the fall line (inferred appearance)')
    tmp = Path(str(tm_path) + '.tmp'); tmp.write_text(json.dumps(tm, indent=2) + '\n'); os.replace(tmp, tm_path)
    # the canopy records the terrain manifest it was placed against
    canopy['inputs']['terrain_manifest_sha256'] = sha(tm_path)
    tmp = Path(str(canopy_path) + '.tmp')
    tmp.write_text(json.dumps(canopy, separators=(',', ':')) + '\n', encoding='utf-8'); os.replace(tmp, canopy_path)
    print(json.dumps({k: record[k] for k in ('base_cm', 'lip_cm', 'lip_height_above_water_m', 'horizontal_run_m',
                                             'water_surface_m')}))


if __name__ == '__main__':
    main()
