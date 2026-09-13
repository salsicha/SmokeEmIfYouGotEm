"""Build the geographic contract for full-river reconstruction integration.

This does not promote a map or invent hydraulic data. Terrain remains Cartesian;
the river axis supplies progress/station lookup, never a deformation of capture.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
OUT = BASE / 'full_reach/playable_route'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def coordinate_points(xy):
    """Densify without cutting corners or changing source vertices/length.

    Interpolate unit normals angularly, bounding both spatial and angular
    steps for the runtime's existing 256 m corridor / 16 m edge-step guard.
    That guard is NOT proof that a wide station ribbon is injective; render
    and collision must use original Cartesian geometry.
    """
    xy = np.asarray(xy, dtype=np.float64)
    if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 2 or not np.isfinite(xy).all():
        raise ValueError('Expected a finite metric polyline')
    delta = np.diff(xy, axis=0)
    length = np.linalg.norm(delta, axis=1)
    if np.any(length <= 1e-8):
        raise ValueError('Duplicate route vertices')
    tangent = delta / length[:, None]
    vertex_tangent = np.vstack((tangent[0], tangent[:-1] + tangent[1:], tangent[-1]))
    norm = np.linalg.norm(vertex_tangent, axis=1)
    if np.any(norm < 1e-5):
        raise ValueError('Reversing axis needs explicit geographic review')
    vertex_tangent /= norm[:, None]
    angle = np.unwrap(np.arctan2(vertex_tangent[:, 1], vertex_tangent[:, 0]) + np.pi / 2)
    stations = np.r_[0., np.cumsum(length)]
    rows = []
    for i, distance in enumerate(length):
        steps = max(1, int(np.ceil(distance / 2)), int(np.ceil(abs(angle[i+1]-angle[i]) / .02)))
        t = np.arange(steps, dtype=np.float64) / steps
        pos = xy[i] + t[:, None] * delta[i] - xy[0]
        theta = angle[i] + t * (angle[i+1]-angle[i])
        rows.append(np.column_stack((stations[i] + t * distance, pos, np.cos(theta), np.sin(theta))))
    rows.append(np.array([[stations[-1], *(xy[-1]-xy[0]), np.cos(angle[-1]), np.sin(angle[-1])]]))
    return np.vstack(rows)


def nearest_station(points, query_xy):
    """Polyline projection, not the unrelated local rigid hydraulic station."""
    xy = points[:, 1:3]
    delta = np.diff(xy, axis=0)
    t = np.clip(np.sum((query_xy-xy[:-1]) * delta, axis=1) / np.sum(delta*delta, axis=1), 0., 1.)
    projections = xy[:-1] + t[:, None] * delta
    distance = np.linalg.norm(projections-query_xy, axis=1)
    index = int(np.argmin(distance))
    return float(points[index, 0] + t[index]*(points[index+1, 0]-points[index, 0])), float(distance[index])


def engine_translation_cm(rapid_origin, river_origin, rapid_datum, river_datum):
    delta = np.asarray(rapid_origin) - np.asarray(river_origin)
    return np.array([delta[0], -delta[1], rapid_datum-river_datum], dtype=np.float64)*100


def main():
    from rasterio.warp import transform
    import rasterio

    route_path = BASE / 'survey_constrained_route_candidate.geojson'
    feature = next(f for f in json.loads(route_path.read_text())['features'] if f['geometry']['type'] == 'LineString')
    lonlat = np.asarray(feature['geometry']['coordinates'])
    xy = np.column_stack(transform('EPSG:4326', 'EPSG:32610', lonlat[:, 0], lonlat[:, 1]))
    points = coordinate_points(xy)
    assert abs(points[-1, 0] - feature['properties']['length_m']) < .001
    edges = [np.linalg.norm(np.diff(points[:, 1:3] + sign*256*points[:, 3:5], axis=0), axis=1) for sign in (-1, 1)]
    assert max(float(e.max()) for e in edges) < 16

    terrain_manifest = json.loads((BASE / 'full_reach/manifest.json').read_text())
    surface_path = BASE / 'full_reach/captured_surface_navd88_m.tif'
    assert sha(surface_path) == terrain_manifest['canonical_source_surface']['sha256']
    mask_path = BASE / 'full_reach/unknown_submerged_bed_mask.tif'
    assert sha(mask_path) == terrain_manifest['unknown_submerged_bed_mask']['sha256']
    # Recheck actual cells instead of inheriting the earlier alignment's pass flag.
    # Quarter-metre segment samples also test cross-cell diagonal corners.
    mask_queries = []
    for a, b in zip(xy[:-1], xy[1:]):
        t = np.linspace(0, 1, max(2, int(np.ceil(np.linalg.norm(b-a)/.25))+1))
        mask_queries.append(a + t[:, None]*(b-a))
    samples = np.vstack(mask_queries)
    with rasterio.open(mask_path) as ds:
        mask = ds.read(1)
        rows, cols = rasterio.transform.rowcol(ds.transform, samples[:, 0], samples[:, 1])
        rows, cols = np.asarray(rows), np.asarray(cols)
        assert np.all((rows >= 0) & (rows < ds.height) & (cols >= 0) & (cols < ds.width))
        assert np.all(mask[rows, cols] == 1), 'Route leaves captured water'
        diagonal = np.flatnonzero((np.diff(rows) != 0) & (np.diff(cols) != 0))
        assert np.all(mask[rows[diagonal], cols[diagonal+1]] == 1)
        assert np.all(mask[rows[diagonal+1], cols[diagonal]] == 1)

    profile_xy = points[:, 1:3] + xy[0]
    with rasterio.open(surface_path) as ds:
        surface = ds.read(1)
        r, c = rasterio.transform.rowcol(ds.transform, profile_xy[:, 0], profile_xy[:, 1])
        profile_surface = surface[r, c]
        assert np.isfinite(profile_surface).all()
    # These are captured WATER SURFACE elevations, not measured channel bed.
    # Never feed this profile directly into the hydraulic solver as bathymetry.
    profile = dict(station_m=points[:, 0], utm_easting_m=profile_xy[:, 0],
        utm_northing_m=profile_xy[:, 1], source_surface_navd88_m=profile_surface,
        within_survey_water=np.ones(len(points), dtype=bool))

    rapid_path = BASE / 'troublemaker/playable_flow/coordinate_map.json'
    rapid = json.loads(rapid_path.read_text())
    assert rapid['world_y_sign'] == -1
    datum = float(rapid['vertical_datum_m'])
    offset = engine_translation_cm(rapid['origin_utm_m'], xy[0], datum, datum)
    rapid_points = np.asarray(rapid['points'])
    embedded_points = rapid_points.copy()
    embedded_points[:, 1:3] += np.asarray(rapid['origin_utm_m']) - xy[0]
    embedded_hydraulics = dict(rapid)
    embedded_hydraulics.update(points=embedded_points.tolist(), origin_utm_m=xy[0].tolist(),
        source_coordinate_map_sha256=sha(rapid_path),
        source_coordinate_map_path=rapid_path.relative_to(ROOT).as_posix(),
        interpretation='Local rigid hydraulic stations in the full-river Cartesian world; NOT full-river chainage',
        normal_map_integrated=False)
    local = np.interp(0., rapid_points[:, 0], rapid_points[:, 1]), np.interp(0., rapid_points[:, 0], rapid_points[:, 2])
    assert np.linalg.norm(local) < 1e-8
    rapid_station, rapid_distance = nearest_station(points, np.asarray(rapid['origin_utm_m'])-xy[0])

    coordinate_map = dict(schema='raftsim.curved_river_coordinate_map.v1',
        horizontal_crs='EPSG:32610', origin_utm_m=xy[0].tolist(), vertical_datum_m=datum,
        world_y_sign=-1, points=points.tolist(),
        source_axis_path=route_path.relative_to(ROOT).as_posix(), source_axis_sha256=sha(route_path),
        interpretation='Survey-water-constrained geographic axis; not measured thalweg or navigation line',
        terrain_policy='Rigid Cartesian placement only; do not warp captured terrain into this station/lateral ribbon')
    placement = dict(schema='raftsim.south_fork.rapid_placement.v1', rapid='troublemaker',
        parent_scenario_id='south_fork_full_descent', separate_menu_scenario=False,
        source_coordinate_map=rapid_path.relative_to(ROOT).as_posix(), source_coordinate_map_sha256=sha(rapid_path),
        translation_from_existing_rapid_world_cm=offset.tolist(), rotation_degrees=[0., 0., 0.], scale=[1., 1., 1.],
        rapid_origin_river_station_m=rapid_station, rapid_origin_distance_to_axis_m=rapid_distance,
        hydraulic_station_is_local_cartesian_not_river_chainage=True,
        hydraulic_handoff_integrated=False, captured_mesh_deformed=False)
    report = dict(schema='raftsim.south_fork.playable_route_integration.v1',
        source_axis_sha256=sha(route_path), source_water_mask_sha256=sha(mask_path),
        route_length_m=float(points[-1, 0]), source_vertex_count=len(xy), runtime_point_count=len(points),
        maximum_runtime_corridor_edge_step_m=max(float(e.max()) for e in edges),
        mask_probe_count=len(samples), all_probes_and_diagonal_corners_in_captured_water=True,
        previous_terrain_profile_axis_length_m=terrain_manifest['reach_length_m'],
        previous_terrain_profile_reusable_without_restationing=False,
        rapid_origin_river_station_m=rapid_station, rapid_origin_distance_to_axis_m=rapid_distance,
        normal_map_integrated=False, full_reconstruction_accepted=False,
        remaining_integration=['Cartesian terrain/rapid seam and collision replacement',
            'Full-reach bathymetry inference and flow cook using the same geometry',
            'Local rigid rapid hydraulic window to global world handoff',
            'Corrected start, sections, finish and asset placement in normal full river',
            'Engine traversal, motion, reference and performance acceptance'])
    OUT.mkdir(parents=True, exist_ok=True)
    profile_path = OUT/'route_source_profile.npz'
    np.savez_compressed(profile_path, **profile)
    report['route_source_profile'] = dict(path=profile_path.relative_to(ROOT).as_posix(),
        sha256=sha(profile_path), source_surface_sha256=sha(surface_path),
        station_axis_sha256=sha(route_path), sample_count=len(points),
        captured_water_surface_not_bathymetry=True)
    for name, payload in [('coordinate_map.json', coordinate_map), ('troublemaker_placement.json', placement),
                          ('troublemaker_hydraulic_coordinate_map.json', embedded_hydraulics)]:
        path = OUT / name
        path.write_text(json.dumps(payload, indent=2) + '\n')
        report[name] = dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path))
    (OUT/'integration.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
