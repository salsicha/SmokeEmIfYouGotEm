"""Plan a diagnostic line against the full-map atlas and registered rapid mesh.

Does not change scoring coordinates, water, terrain, or the playable scenario.
Sampled clearance is a conservative planning screen, not traversal acceptance
or surveyed navigation advice. Actual yawed tube contact still needs gameplay.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tmp/south-fork-geospatial-deps'))
import numpy as np
from scipy.ndimage import minimum_filter, shift
from south_fork_geometry_source import load_registered_mesh
from plan_south_fork_guided_review import plan


def sha(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def sample_atlas(manifest, arrays, east, north):
    """Bilinear nodal sampling across tile seams; absent corners fail closed."""
    ny, nx = manifest['tile_shape']
    spacing = manifest['grid_spacing_m']
    origins = np.array([tile['origin_m'] for tile in manifest['tiles']])
    base = origins.min(axis=0)
    offsets = (origins-base)/spacing
    if not np.allclose(offsets, np.rint(offsets), rtol=0, atol=1e-7):
        raise ValueError('Atlas is not one aligned lattice')
    offsets = np.rint(offsets).astype(int)
    if np.any(offsets % [nx, ny]):
        raise ValueError('Atlas tiles are not aligned')
    lookup = {tuple(offset//[nx, ny]): i for i, offset in enumerate(offsets)}
    xy = np.stack(np.broadcast_arrays(east, north), axis=-1)
    grid = (xy-base)/spacing
    floor = np.floor(grid).astype(int)
    fraction = grid-floor
    out = {key: np.zeros(xy.shape[:-1]) for key in arrays}
    valid = np.ones(xy.shape[:-1], dtype=bool)
    for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1)):
        corner = floor+[dx, dy]
        tilexy = corner//[nx, ny]
        indices = np.array([lookup.get(tuple(p), -1) for p in tilexy.reshape(-1, 2)]).reshape(valid.shape)
        weight = (fraction[..., 0] if dx else 1-fraction[..., 0])*(fraction[..., 1] if dy else 1-fraction[..., 1])
        valid &= (indices >= 0) | (weight == 0.)
        row = np.maximum(indices, 0)*ny+corner[..., 1] % ny
        col = corner[..., 0] % nx
        for key, data in arrays.items():
            out[key] += weight*data[row, col]
    return out, valid


def oriented_clearance(depth, cell, yaw_radians):
    """Sample the rectangle at three headings; runtime checks remain required."""
    clearance = depth.copy()
    along = np.linspace(-2.35, 2.35, 11)
    across = np.linspace(-1.2, 1.2, 7)
    for yaw in yaw_radians + np.deg2rad(np.array([-15., 0., 15.])):
        for x in along:
            for y in across:
                east = x*np.cos(yaw)-y*np.sin(yaw)
                north = x*np.sin(yaw)+y*np.cos(yaw)
                clearance = np.minimum(clearance, shift(depth, (-north/cell, -east/cell),
                    order=1, mode='constant', cval=0., prefilter=False))
    return clearance


def require_endpoint_rejoin(clearance, north, end_column, end_north, tolerance=5.):
    result = clearance.copy()
    result[np.abs(north-end_north) > tolerance, end_column] = 0.
    return result


def distance_to_axis(east, north, axis):
    queries = np.stack(np.broadcast_arrays(east, north), axis=-1)
    result = np.full(queries.shape[:-1], np.inf)
    for start, end in zip(axis[:-1], axis[1:]):
        delta = end-start
        length2 = np.dot(delta, delta)
        if length2 == 0.:
            continue
        t = np.clip(np.sum((queries-start)*delta, axis=-1)/length2, 0., 1.)
        result = np.minimum(result, np.linalg.norm(queries-start-t[..., None]*delta, axis=-1))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--start-report', type=Path, required=True)
    parser.add_argument('--envelope', choices=('any_yaw', 'downstream'), default='any_yaw')
    parser.add_argument('--start-station', type=float,
        help='Explicit earlier centreline planning seed, not an observed raft position or game teleport')
    parser.add_argument('--candidate-seed-radius', type=float, default=0.,
        help='Explore a nearby safe planning seed only; never claim traversal from the observed start')
    parser.add_argument('--constrain-scoring-axis', action='store_true',
        help='Diagnose whether the same footprint fits within 5m of the provisional scoring centreline')
    parser.add_argument('--downstream-turn-margin', action='store_true',
        help='Keep ground-track directions within 65 degrees of downstream')
    parser.add_argument('--maximum-cross-current', type=float, default=2.2,
        help='Planning margin only, must be no greater than the unchanged 2.2m/s paddle capability')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve previous evidence; choose a fresh output')
    atlas_path = ROOT/'tmp/south-fork-runtime-atlas-600s-v1-20260912/atlas/manifest.json'
    geometry_path = ROOT/'tmp/troublemaker-inferred-rock-flanks-20260912/registered_mesh_source.npz'
    expected_geometry = '8bdf1a586e7bd2536eaf25a982763efd9e5a558e7172fd7897b8ae0ecc8fe06b'
    if sha(geometry_path) != expected_geometry:
        raise ValueError('Registered full-map geometry revision changed')
    atlas = json.loads(atlas_path.read_text())
    arrays = {}
    for key, entry in atlas['arrays'].items():
        path = (atlas_path.parent/entry['file']).resolve()
        if not path.is_relative_to(ROOT) or sha(path) != entry['sha256']:
            raise ValueError(f'Atlas source changed: {key}')
        arrays[key] = np.load(path, mmap_mode='r', allow_pickle=False)
        if list(arrays[key].shape) != entry['shape'] or not np.isfinite(arrays[key]).all():
            raise ValueError(f'Invalid atlas data: {key}')
    if atlas['source_elevation_datum_m'] != 220.:
        raise ValueError('Geometry and water datum differ')
    route_path = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/playable_route/coordinate_map.json'
    route = json.loads(route_path.read_text())
    points = np.array(route['points'])
    if route['world_y_sign'] != -1:
        raise ValueError('Unexpected world north convention')
    observation = json.loads(args.start_report.read_text())
    if observation['scenario_id'] != 'south_fork_full_descent':
        raise ValueError('Start must come from actual full South Fork gameplay')
    first = observation['samples'][0]
    start_xy = np.array([first['world_x_cm'], -first['world_y_cm']])/100.
    if args.start_station is not None:
        if not np.isfinite(args.start_station) or not 8280. <= args.start_station <= observation['start_station_m']:
            raise ValueError('Earlier planning seed must be inside the captured approach')
        start_xy = np.array([np.interp(args.start_station, points[:, 0], points[:, i]) for i in (1, 2)])
    end_station = observation['start_station_m']+125.
    end_xy = np.array([np.interp(end_station, points[:, 0], points[:, i]) for i in (1, 2)])
    # Enough width to diagnose alternatives, never clip source data into water.
    cell = .5
    east = np.arange(np.floor(end_xy[0])-10., np.ceil(start_xy[0])+10.+cell, cell)
    north = np.arange(min(start_xy[1], end_xy[1])-35., max(start_xy[1], end_xy[1])+35.+cell, cell)
    xx, yy = np.meshgrid(east, north)
    water, valid = sample_atlas(atlas, arrays, xx, yy)
    _, sampler = load_registered_mesh(geometry_path)
    translation = np.array([683805.1336302214, 4296673.447587562])-route['origin_utm_m']
    terrain = sampler.sample(xx-translation[0], yy-translation[1])
    depth = np.where(valid & (water['h'] > atlas['dry_tolerance']), water['bed']+water['h']-terrain, 0.)
    depth = np.maximum(depth, 0.)
    # Circular envelope contains the 4.7 x 2.4 m raft-plus-margin at any yaw.
    # Half-cell diagonal expansion covers gaps between sampled offsets.
    radius = np.hypot(2.35, 1.2)+cell/np.sqrt(2.)
    count = int(np.ceil(radius/cell))
    dy, dx = np.mgrid[-count:count+1, -count:count+1]*cell
    footprint = dx*dx+dy*dy <= radius*radius
    yaw = np.arctan2(end_xy[1]-start_xy[1], end_xy[0]-start_xy[0])
    clearance = (minimum_filter(depth, footprint=footprint, mode='constant', cval=0.)
        if args.envelope == 'any_yaw' else oriented_clearance(depth, cell, yaw))
    local_axis = points[(points[:, 0]>=8270.) & (points[:, 0]<=8500.), 1:3]
    axis_distance = distance_to_axis(xx, yy, local_axis)
    if args.constrain_scoring_axis:
        clearance = np.where(axis_distance<=5., clearance, 0.)
    index = np.rint((start_xy-[east[0], north[0]])/cell).astype(int)
    requested_index = index.copy()
    if not 0. <= args.candidate_seed_radius <= 5.:
        raise ValueError('Candidate seed radius must remain inside the existing 5m route tolerance')
    safe_y, safe_x = np.where(clearance >= .55)
    safe_distance = np.hypot(east[safe_x]-start_xy[0], north[safe_y]-start_xy[1])
    nearest = int(np.argmin(safe_distance)) if len(safe_distance) else None
    if args.candidate_seed_radius and nearest is not None and safe_distance[nearest] <= args.candidate_seed_radius:
        index = np.array([safe_x[nearest], safe_y[nearest]])
    end_column = round((end_xy[0]-east[0])/cell)
    # The reusable graph search ends at any row in a column. A river segment
    # must instead rejoin the intended full-river endpoint, not a parallel pool.
    search_clearance = require_endpoint_rejoin(clearance, north, end_column, end_xy[1])
    result = dict(schema='raftsim.normal_river_planned_line.v1', scenario_id='south_fork_full_descent',
        source_atlas=str(atlas_path.relative_to(ROOT)), source_atlas_sha256=sha(atlas_path),
        source_geometry_sha256=expected_geometry, route_source_sha256=sha(route_path),
        source_start_report=str(args.start_report), source_start_report_sha256=sha(args.start_report),
        atlas_time_s=atlas['source_time_seconds'], hydraulic_settled=atlas['settled_hydraulics'],
        required_depth_m=.55, grid_spacing_m=cell, planning_envelope_radius_m=radius,
        planning_envelope=args.envelope, downstream_heading_east_north_deg=float(np.rad2deg(yaw)),
        starting_world_east_north_m=start_xy.tolist(), target_chainage_m=end_station,
        start_position_source='observed_gameplay' if args.start_station is None else 'explicit_earlier_scoring_centerline_seed',
        explicit_start_station_m=args.start_station,
        start_sampled_depth_m=float(depth[requested_index[1], requested_index[0]]),
        start_footprint_depth_m=float(clearance[requested_index[1], requested_index[0]]),
        nearest_safe_seed_distance_m=float(safe_distance[nearest]) if nearest is not None else None,
        planning_seed_world_east_north_m=[float(east[index[0]]), float(north[index[1]])],
        planning_seed_shifted=bool(np.any(index != requested_index)),
        approach_from_observed_start_validated=False,
        endpoint_maximum_offset_m=5.,
        constrain_scoring_axis_to_5m=args.constrain_scoring_axis,
        downstream_turn_margin=args.downstream_turn_margin,
        maximum_planned_cross_current_mps=args.maximum_cross_current,
        safe_grid_points=int((clearance>=.55).sum()),
        full_map_runtime_validated=False, real_river_navigation_line=False, underwater_depth_measured=False,
        scope='Actual registered triangles and current full-map 600s atlas; sampled envelope (see planning_envelope). Downstream mode samples a 4.7x2.4m rectangle at mean downstream heading and +/-15 degrees only. No water/terrain/scoring changes; not continuous collision proof or runtime acceptance.')
    try:
        allowed_steps = None
        if args.downstream_turn_margin:
            downstream = np.array([np.cos(yaw), np.sin(yaw)])
            allowed_steps = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                if (dx or dy) and np.dot([dx, dy], downstream)/np.hypot(dx, dy)>=np.cos(np.deg2rad(65.))]
        path, _ = plan(depth, (index[1], index[0]), end_column, cell,
            clearance=search_clearance, velocity=(water['u'], water['v']),
            allowed_steps=allowed_steps, maximum_cross_current=args.maximum_cross_current)
        result.update(planned=True, world_east_north_m=[[float(east[x]), float(north[y])] for y, x in path],
            minimum_sampled_footprint_depth_m=float(min(clearance[y, x] for y, x in path)))
        # A fixed orientation planning screen is insufficient for actual turns.
        # Independently sample ORIGINAL triangles at the flow-compensated raft
        # heading implied by every outgoing route edge, without grid shifting.
        centers = np.array(result['world_east_north_m'])
        result['maximum_planned_scoring_axis_distance_m'] = float(distance_to_axis(centers[:, 0], centers[:, 1], local_axis).max())
        direction = np.diff(centers, axis=0)
        direction = np.vstack((direction, direction[-1]))
        direction /= np.linalg.norm(direction, axis=1)[:, None]
        flow, covered = sample_atlas(atlas, arrays, centers[:, 0], centers[:, 1])
        velocity = np.column_stack((flow['u'], flow['v']))
        across_flow = velocity-direction*np.sum(velocity*direction, axis=1)[:, None]
        remaining = 2.2**2-np.sum(across_flow**2, axis=1)
        effort = direction*np.sqrt(np.maximum(remaining, 0.))[:, None]-across_flow
        angle = np.arctan2(effort[:, 1], effort[:, 0])
        along, across = np.meshgrid(np.linspace(-2.35, 2.35, 21), np.linspace(-1.2, 1.2, 11))
        a, b = along.ravel(), across.ravel()
        ex = centers[:, 0, None]+np.cos(angle[:, None])*a-np.sin(angle[:, None])*b
        no = centers[:, 1, None]+np.sin(angle[:, None])*a+np.cos(angle[:, None])*b
        footprint_water, footprint_valid = sample_atlas(atlas, arrays, ex, no)
        footprint_ground = sampler.sample(ex-translation[0], no-translation[1])
        actual_depth = np.where(footprint_valid & (footprint_water['h'] > atlas['dry_tolerance']),
            footprint_water['bed']+footprint_water['h']-footprint_ground, 0.)
        route_depth = actual_depth.min(axis=1)
        result.update(flow_heading_footprint_sample_count=int(actual_depth.size),
            minimum_flow_heading_footprint_depth_m=float(route_depth.min()),
            unsafe_flow_heading_points=int((route_depth<.55).sum()),
            flow_heading_screen_passed=bool(covered.all() and np.all(remaining>0.) and np.all(route_depth>=.55)),
            flow_heading_screen_scope='231 original-triangle samples per route point, desired flow-compensated outgoing heading only; does not prove intermediate turns or motion.')
    except ValueError as error:
        result.update(planned=False, reason=str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'world_east_north_m'}, indent=2))


if __name__ == '__main__':
    main()
