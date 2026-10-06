"""Bind a reviewed Colorado runtime export to a fresh native playable map.

This records a construction descent, not surveyed rapid bounds or class acceptance.
The editor validates file identities again before constructing the Landscape.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def launch(mapping, bed, depth, wet, grid, station, lateral=0):
    points = np.asarray(mapping['points'], dtype=float)
    col = int(round((station-grid['origin_x_m'])/grid['dx_m']))
    row = int(round((lateral-grid['origin_y_m'])/grid['dy_m']))
    # Require the whole production raft footprint to start in water. These
    # 2 m-grid margins exceed its half length/beam; no dry-cell fallback.
    if row < 2 or col < 3 or row+2 >= depth.shape[0] or col+3 >= depth.shape[1]:
        raise ValueError('Launch too close to source edge')
    area = np.s_[row-2:row+3, col-3:col+4]
    if not wet[area].all() or depth[area].min() < 1.0:
        raise ValueError('Launch footprint is dry or shallower than 1 m')
    s = float(points[col, 0]); p = points[col]
    side = grid['origin_y_m']+row*grid['dy_m']
    xy = p[1:3]+side*p[3:5]
    direction = points[col+1, 1:3]-points[col-1, 1:3]
    sign = mapping['world_y_sign']
    z = float(bed[row, col]+depth[row, col]-mapping['vertical_datum_m'])
    return dict(station_m=s, lateral_m=float(side),
                location_cm=[float(xy[0]*100), float(xy[1]*100*sign), z*100-56/3.4],
                yaw_deg=float(np.degrees(np.arctan2(direction[1]*sign, direction[0]))),
                minimum_footprint_depth_m=float(depth[area].min()))


def build(runtime, map_name, start, finish, lateral=0):
    runtime = runtime.resolve()
    runtime.relative_to(ROOT)
    if not re.fullmatch(r'L_Colorado_[A-Za-z0-9_]+', map_name):
        raise ValueError('Fresh Colorado catalog map name required')
    if (ROOT/'unreal/Content/RaftSim/Maps/Catalog'/f'{map_name}.umap').exists():
        raise ValueError('Refusing to overwrite a map')
    manifest = json.loads((runtime/'manifest.json').read_text())
    if manifest['schema'] != 'raftsim.colorado_catalog_runtime_candidate.v1':
        raise ValueError('Unsupported runtime export')
    if (runtime/'REJECTED.json').exists() or manifest['terrain_solver_bed_error_m']['maximum'] > .1:
        raise ValueError('Rejected terrain/solver export')
    files = {}
    for relative, expected in manifest['files_sha256'].items():
        path = (runtime/relative).resolve()
        path.relative_to(runtime)
        if sha(path) != expected:
            raise ValueError(f'Changed runtime input: {relative}')
        files[path.relative_to(ROOT).as_posix()] = expected
    files[(runtime/'manifest.json').relative_to(ROOT).as_posix()] = sha(runtime/'manifest.json')
    fields = runtime/'cooked_flow_fields'
    flow = json.loads((fields/'manifest.json').read_text())
    band = flow['bands'][0]; grid = flow['grid']
    mapping = json.loads((runtime/'terrain/coordinate_map.json').read_text())
    end = mapping['points'][-1][0]
    if not 10 < start < finish < end-10:
        raise ValueError('Construction descent must stay inside cooked reach')
    arrays = {name: np.load(fields/band['arrays'][name]['file']) for name in ('bed','h','wet_mask')}
    initial = launch(mapping, arrays['bed'], arrays['h'], arrays['wet_mask'], grid, start, lateral)
    rows, cols = np.nonzero(arrays['wet_mask'])
    points = np.asarray(mapping['points'], dtype=float)
    sides = grid['origin_y_m']+rows*grid['dy_m']
    xy = points[cols,1:3]+sides[:,None]*points[cols,3:5]
    probes = np.column_stack((xy[:,0]*100, xy[:,1]*100*mapping['world_y_sign'],
                             (arrays['bed'][rows,cols]-mapping['vertical_datum_m'])*100))
    rel = runtime.relative_to(ROOT).as_posix()
    land = manifest['landscape']
    return dict(schema='raftsim.catalog_map_import.v1', display_name=manifest['name'],
        map_package='/Game/RaftSim/Maps/Catalog/'+map_name, section_id=mapping['section_id'],
        files_sha256=files, heightfield=rel+'/terrain/heightfield_2017.png',
        landscape=land, cooked_fields=rel+'/cooked_flow_fields',
        coordinate_map=rel+'/terrain/coordinate_map.json', streaming=rel+'/moving_water_streaming.json',
        flow_band=band['band_id'], lateral_extent_m=(grid['ny']-1)*grid['dy_m'],
        launch=initial, finish_station_m=finish, rig='ColoradoOarRig',
        wet_bed_collision_probes_cm=probes.tolist(),
        collision_probe_scope='Every cooked wet cell centre; not swept-hull clearance or shoreline animation acceptance.',
        bounds_status='construction descent; whole-rapid bounds not yet accepted',
        acceptance='pending native collision, decision, rendered and packaged tests')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--map-name', required=True)
    p.add_argument('--start', type=float, required=True)
    p.add_argument('--finish', type=float, required=True)
    p.add_argument('--lateral', type=float, default=0)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists(): raise SystemExit('Fresh contract path required')
    result = build(a.runtime, a.map_name, a.start, a.finish, a.lateral)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['launch'], indent=2))
