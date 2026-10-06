"""Observed rock on the banks of a curved evidence reach (numpy only).

    build_observed_rock_placement.py {futaleufu_terminator|chilko_lava_canyon}

The evidence terrains are 30 m radar (Futaleufu, GLO-30 with its canopy) or a
10 m drape over 1 m LiDAR (Chilko). Neither shows the rock the observations
describe at the water:

* Futaleufu Terminator (terminator_observations_2026_09_29.json):
  "a tall cliff marks the 90-deg left bend at the top (station ~0), and a
  large bedrock outcrop sits on river left at the right bend (~650)";
  "granite formations rising straight from the riverbanks"; a channel
  "strewn with very large granite boulders".
* Chilko Lava Canyon (lava_canyon_observations_2026_09_29.json): "dark basalt
  boulder talus (1-3 m boulders) at the waterline" at Bidwell; "steep grey
  talus/scree slopes and rockslide fans reach the river on river right at
  ~2640-2790 m and at the White Mile head (~3570-3650 m)"; "banks are mostly
  boulder talus and cobble lines".

Each zone below (station span, bank, count, size, distance beyond the cooked
wet edge) restates one of those observations. Rocks are placed along the bank
from the reach's curved coordinate map and the cooked wet mask, never inside
the cooked water, and written in the Landscape frame of the terrain manifest
as observed_rock_placement.json (schema raftsim.observed_rock_placement.v1),
which the editor fits the six reviewed rock meshes to (AddObservedRockShells).
Canopy trees standing inside a large rock's footprint are removed from the
reach's canopy placement, so trunks do not pierce the rock.

Positions and sizes are approximate (described, not measured). Visual only:
no collision, terrain, bed or water changes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'physics/data/real_world'
SEED = 20261003

REACHES = {
    'futaleufu_terminator': dict(
        terrain=DATA / 'futaleufu_river_chile/terrain/terminator_evidence_2026',
        prefix='terminator_evidence',
        cooked=DATA / 'futaleufu_river_chile/scenario_terminator_evidence_2026/cooked_flow_fields',
        observations=DATA / 'futaleufu_river_chile/observed_rapids/terminator_observations_2026_09_29.json',
        zones=[
            dict(id='top_bend_cliff', span=[0, 170], side='right', count=14, length=[9, 15], height=[9, 16],
                 offset=[1.0, 5.0], line=True,
                 observation='a tall cliff marks the 90-deg left bend at the top (station ~0), on its outside (river right)'),
            dict(id='right_bend_left_outcrop', span=[580, 760], side='left', count=16, length=[12, 20], height=[8, 15],
                 offset=[1.0, 8.0], line=False,
                 observation='a large bedrock outcrop sits on river left at the right bend (~650)'),
            dict(id='terminator_left_granite', span=[980, 1460], side='left', count=22, length=[4, 9], height=[3, 7],
                 offset=[0.5, 5.0], line=True,
                 observation='granite formations rising straight from the riverbanks; the left bank below the mid-rapid '
                             'scout is steep'),
            dict(id='terminator_right_boulders', span=[900, 1700], side='right', count=18, length=[2.5, 5], height=[1.5, 3.5],
                 offset=[0.3, 4.0], line=False,
                 observation='channel strewn with very large granite boulders (black in the channel, white and sculpted at '
                             'Camp Terminador)'),
            dict(id='khyber_himalayas_bank_boulders', span=[1550, 2000], side='both', count=14, length=[2, 5], height=[1.5, 3],
                 offset=[0.3, 4.0], line=False,
                 observation='very large granite boulders along the Khyber Pass and Himalayas banks'),
        ]),
    'chilko_lava_canyon': dict(
        terrain=DATA / 'chilko_river_bc/terrain/lava_canyon_evidence_2023',
        prefix='lava_canyon_evidence_2023',
        cooked=DATA / 'chilko_river_bc/scenario_lava_canyon_evidence_2023/cooked_flow_fields',
        observations=DATA / 'chilko_river_bc/observed_rapids/lava_canyon_observations_2026_09_29.json',
        zones=[
            dict(id='bidwell_waterline_talus', span=[690, 1000], side='both', count=300, length=[1.2, 3.2], height=[0.8, 2.2],
                 offset=[0.0, 6.0], line=False,
                 observation='Bidwell: dark basalt boulder talus (1-3 m boulders) at the waterline below buff/grey bluffs'),
            dict(id='landslide_apron_above_bidwell', span=[650, 760], side='left', count=60, length=[0.6, 1.4], height=[0.4, 1.0],
                 offset=[0.0, 10.0], line=False,
                 observation='a large grey-tan eroding bare slope (landslide area) on river left just above the rapid, with a '
                             'gravel/cobble apron to the water'),
            dict(id='reach_boulder_banks', span=[0, 3978], side='both', count=900, length=[0.8, 2.2], height=[0.5, 1.6],
                 offset=[0.0, 4.0], line=False,
                 observation='banks are mostly boulder talus and cobble lines'),
            dict(id='talus_fan_2700_right', span=[2640, 2790], side='right', count=140, length=[1.0, 3.0], height=[0.7, 2.0],
                 offset=[0.0, 14.0], line=False,
                 observation='steep grey talus/scree slopes and rockslide fans reach the river on river right at ~2640-2790 m'),
            dict(id='white_mile_head_fan_right', span=[3570, 3650], side='right', count=110, length=[1.0, 3.0], height=[0.7, 2.0],
                 offset=[0.0, 14.0], line=False,
                 observation='a rockslide fan reaches the river on river right at the White Mile head (~3570-3650 m; pale grey '
                             'scar ~60 x 40 m)'),
        ]),
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(path, value, indent=None):
    tmp = Path(str(path) + '.tmp')
    tmp.write_text(json.dumps(value, indent=indent, separators=None if indent else (',', ':')) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('reach', choices=sorted(REACHES))
    args = ap.parse_args()
    R = REACHES[args.reach]
    terrain, prefix = R['terrain'], R['prefix']
    tm_path = terrain / f'{prefix}_terrain_manifest.json'
    land = json.loads(tm_path.read_text())['landscape']
    origin = next(v for k, v in land.items() if k.startswith('world_origin_'))
    west_e, centre_n = origin['west_edge_e'], origin['centre_n']
    cm_path = terrain / f'{prefix}_runtime_coordinate_map.json'
    cmap = json.loads(cm_path.read_text())
    assert list(cmap['horizontal_origin_m']) == [west_e, centre_n], 'coordinate map and Landscape share their origin'
    P = np.array(cmap['points'], float)
    st, px, py = P[:, 0], P[:, 1], P[:, 2]
    tx = np.gradient(px); ty = np.gradient(py); n = np.hypot(tx, ty); tx /= n; ty /= n
    lx, ly = -ty, tx                                  # left normal (lateral positive to river left)
    manifest = json.loads((R['cooked'] / 'manifest.json').read_text())
    g = manifest['grid']; band = manifest['bands'][0]['band_id']
    wet = np.load(R['cooked'] / band / 'wet_mask.npy') > 0
    lats = g['origin_y_m'] + np.arange(g['ny']) * g['dy_m']

    def wet_edges(s):
        col = int(np.clip(round((s - g['origin_x_m']) / g['dx_m']), 0, g['nx'] - 1))
        w = lats[wet[:, col]]
        return (float(w.max()), float(w.min())) if w.size else (0.0, 0.0)

    rng = np.random.default_rng(SEED)
    rows, zones_out = [], []
    for z in R['zones']:
        a0, a1 = z['span']; sides = ['left', 'right'] if z['side'] == 'both' else [z['side']]
        count = z['count']
        stations = (np.linspace(a0, a1, count) + rng.uniform(-0.4, 0.4, count) * (a1 - a0) / max(count, 1)
                    if z['line'] else rng.uniform(a0, a1, count))
        placed = 0
        for k, s in enumerate(np.clip(stations, st[0], st[-1])):
            side = sides[k % len(sides)]
            left_edge, right_edge = wet_edges(s)
            length = rng.uniform(*z['length']); height = rng.uniform(*z['height'])
            width = length * rng.uniform(0.55, 0.85)
            off = rng.uniform(*z['offset']) + 0.35 * width      # the rock's inner face sits at the offset
            lat = left_edge + off if side == 'left' else right_edge - off
            i = int(np.clip(np.searchsorted(st, s), 0, len(st) - 1))
            x = px[i] + lat * lx[i]; y = py[i] + lat * ly[i]
            along = np.degrees(np.arctan2(-ty[i], tx[i]))   # yaw in the Landscape frame (Y south)
            yaw = along + (rng.uniform(-20, 20) if z['line'] else rng.uniform(0, 360))
            rows.append([round(x * 100.0, 1), round(-y * 100.0, 1), round(0.3 * height * 100.0, 1), round(length, 2),
                         round(width, 2), round(height, 2), round(float(yaw), 1), int(rng.integers(0, 6)),
                         round(float(rng.uniform(-8, 8)), 1), round(float(rng.uniform(-8, 8)), 1)])
            placed += 1
        zones_out.append({k: v for k, v in z.items() if k != 'line'} | dict(placed=placed))
    out = terrain / f'{prefix}_observed_rock_placement.json'
    placement = dict(
        schema='raftsim.observed_rock_placement.v1', reach=args.reach,
        generator='physics/scripts/build_observed_rock_placement.py',
        frame=dict(x_cm='east of the Landscape west edge (E - %.1f) x 100' % west_e,
                   y_cm='south of the Landscape centre row (-(N - %.1f)) x 100' % centre_n),
        instance_fields=['x_cm', 'y_cm', 'sink_cm', 'length_m', 'width_m', 'height_m', 'yaw_deg', 'variant', 'pitch_deg', 'roll_deg'],
        inputs=dict(observations=R['observations'].relative_to(ROOT).as_posix(), observations_sha256=sha(R['observations']),
                    coordinate_map=cm_path.relative_to(ROOT).as_posix(), coordinate_map_sha256=sha(cm_path),
                    cooked_manifest=(R['cooked'] / 'manifest.json').relative_to(ROOT).as_posix(),
                    cooked_manifest_sha256=sha(R['cooked'] / 'manifest.json')),
        zones=zones_out, seed=SEED,
        placement_note='rocks sit beyond the cooked wet edge at the zone\'s offset (inner face), 30 % of their height sunk; '
                       'yaw along the bank for cliff and granite lines, random for talus',
        positions_and_sizes='approximate, from descriptions (not measured)', collision='visual only (no collision)',
        terrain_or_hydraulic_geometry_modified=False, instances=rows)
    write_json(out, placement, indent=None)
    # canopy trees inside a large rock's footprint
    canopy_path = terrain / f'{prefix}_canopy_placement.json'
    canopy = json.loads(canopy_path.read_text(encoding='utf-8'))
    big = np.array([[r[0], r[1], 50.0 * r[3]] for r in rows if r[3] >= 4.0])
    removed = 0
    if len(big):
        keep = []
        for inst in canopy['instances']:
            d = np.hypot(big[:, 0] - inst[0], big[:, 1] - inst[1])
            if np.any(d < big[:, 2] + 100.0):
                removed += 1
            else:
                keep.append(inst)
        canopy['instances'] = keep
        canopy['statistics']['instance_count'] = len(keep)
        canopy['statistics']['removed_inside_observed_rock'] = canopy['statistics'].get('removed_inside_observed_rock', 0) + removed
        write_json(canopy_path, canopy, indent=None)
    print(json.dumps(dict(out=out.relative_to(ROOT).as_posix(), rocks=len(rows), canopy_removed=removed,
                          zones=[(z['id'], z['placed']) for z in zones_out]), indent=1))


if __name__ == '__main__':
    main()
