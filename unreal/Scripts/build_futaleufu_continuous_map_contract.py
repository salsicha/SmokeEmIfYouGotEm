"""Write the Futaleufu continuous-map runtime contract from an exported runtime.

Input is a runtime candidate written by export_futaleufu_cartesian_runtime.py
(its export_audit.json names the native audit it came from). The contract
binds:
- the Cartesian water (coordinate_map.json, streaming_manifest.json and the
  window covering the launch);
- the captured progress route (station 0 on the Rio Azul, the confluence at
  about 5,370 m, the Pasarela at the end);
- the three-arm hydraulic contract (Rio Azul and upstream-mainstem inflows);
- a launch on the deepest native water within 25 m of the route at the start
  station, facing downstream.
RaftSim.AddContinuousRuntime verifies every hashed file before using it.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / ('physics/data/real_world/futaleufu_river_chile/production_corridor/'
                'rio_azul_swinging_bridge_to_pasarela/hydrography/continuous_route_2026_10_v2/coordinate_map.json')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def route_point(points, station):
    stations = points[:, 0]
    if not stations[0] <= station <= stations[-1]:
        raise ValueError('Station outside the captured route')
    i = int(np.searchsorted(stations, station))
    i = min(max(i, 1), len(points) - 1)
    a, b = points[i - 1], points[i]
    f = (station - a[0]) / max(b[0] - a[0], 1e-9)
    xy = a[1:3] + f * (b[1:3] - a[1:3])
    tangent = a[3:5] + f * (b[3:5] - a[3:5])
    return xy, tangent / np.linalg.norm(tangent)


def deepest_wet_cell(atlas_dir, atlas, xy, radius):
    size = atlas['tile_shape'][0]
    h = np.load(atlas_dir / atlas['arrays']['h']['file'], mmap_mode='r')
    best = None
    for i, tile in enumerate(atlas['tiles']):
        ox, oy = tile['origin_m']
        if not (ox - radius <= xy[0] <= ox + size + radius and oy - radius <= xy[1] <= oy + size + radius):
            continue
        depth = np.asarray(h[i * size:(i + 1) * size])
        rows, cols = np.indices(depth.shape)
        cx, cy = ox + cols, oy + rows
        near = np.hypot(cx - xy[0], cy - xy[1]) <= radius
        if not near.any():
            continue
        k = np.argmax(np.where(near, depth, -1.0))
        r, c = np.unravel_index(k, depth.shape)
        if best is None or depth[r, c] > best[0]:
            best = (float(depth[r, c]), float(cx[r, c]), float(cy[r, c]))
    return best


def build(runtime, start, finish, map_package, minimum_depth):
    runtime = Path(runtime).resolve()
    receipt = json.loads((runtime / 'export_audit.json').read_text())
    if receipt.get('schema') != 'raftsim.futaleufu_cartesian_runtime_candidate.v1':
        raise ValueError('Futaleufu Cartesian runtime candidate required')
    if receipt['covered_probes'] != receipt['original_route_and_bank_probes']:
        raise ValueError('Runtime does not cover every route and bank probe')
    audit_hash = receipt['source_audit_sha256']
    audits = [p for p in (ROOT / 'tmp').glob('*audit*.json') if sha(p) == audit_hash]
    audits += [p for p in (ROOT / 'physics/data/real_world/futaleufu_river_chile/review').glob('*.json') if sha(p) == audit_hash]
    if not audits:
        raise ValueError('The export names a source audit that is not present')
    audit = audits[0]
    audit_json = json.loads(audit.read_text())
    native_manifest = json.loads((ROOT / audit_json['native_run'] / 'native' / 'input_manifest.json').read_text())
    inlets = {name: row['target_m3s'] for name, row in native_manifest['inlet_budget'].items()}
    if set(inlets) != {'rio_azul', 'upstream_mainstem'}:
        raise ValueError('Three-arm inlet budget required')
    streaming = json.loads((runtime / 'streaming_manifest.json').read_text())
    atlas_dir = runtime / 'atlas'
    atlas = json.loads((atlas_dir / 'manifest.json').read_text())
    route = json.loads(ROUTE.read_text())
    points = np.asarray(route['points'], float)
    if not start < finish <= points[-1, 0]:
        raise ValueError('Finish must follow the start inside the route')
    xy, tangent = route_point(points, start)
    best = deepest_wet_cell(atlas_dir, atlas, xy, 25.0)
    if best is None or best[0] < minimum_depth:
        raise ValueError('No native water deep enough near the start station')
    depth, x, y = best
    window = None
    for row in streaming['windows']:
        for box in row['valid_live_center_bounds_m']:
            if box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                window = row
                break
        if window:
            break
    if window is None:
        raise ValueError('No streaming window may centre on the launch')
    fields_dir = Path(window['cooked_fields_manifest']).parent.as_posix()
    files = {rel(p): sha(p) for p in (runtime / 'coordinate_map.json', runtime / 'streaming_manifest.json',
                                      runtime / 'export_audit.json', atlas_dir / 'manifest.json', ROUTE, audit)}
    files[window['cooked_fields_manifest']] = sha(ROOT / window['cooked_fields_manifest'])
    yaw = math.degrees(math.atan2(route['world_y_sign'] * tangent[1], tangent[0]))
    return dict(
        schema='raftsim.continuous_map_import.v1', river_id='futaleufu_river_chile', map_package=map_package,
        display_name='Futaleufu continuous descent', section_id='futaleufu_continuous',
        files_sha256=files, coordinate_map=rel(runtime / 'coordinate_map.json'),
        progress_coordinate_map=rel(ROUTE), streaming=rel(runtime / 'streaming_manifest.json'),
        cooked_fields=fields_dir, flow_band='median_runnable',
        lateral_extent_m=float(streaming['live_window_extent_m'][1]),
        launch=dict(station_m=float(start), hydraulic_xy_m=[x, y], yaw_deg=yaw,
                    minimum_footprint_depth_m=float(minimum_depth), launch_depth_m=depth),
        finish_station_m=float(finish), rig='PaddleCrew',
        hydraulic_contract=dict(schema='raftsim.futaleufu_three_arm_runtime.v1', inlet_discharge_m3s=inlets,
                                source_audit=rel(audit),
                                basis='Settled from a coarse pre-cook warm start; inflows are inferred construction values'),
        acceptance='Pending native rendered descent, rescue streaming and packaged performance checks')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--start', type=float, required=True)
    parser.add_argument('--finish', type=float, required=True)
    parser.add_argument('--map', default='/Game/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousContextV1')
    parser.add_argument('--minimum-depth', type=float, default=1.0)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Fresh contract required')
    contract = build(args.runtime, args.start, args.finish, args.map, args.minimum_depth)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(contract, indent=2) + '\n')
    print(json.dumps(contract['launch'], indent=2))
