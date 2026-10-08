"""Build the complete captured Rio Azul-to-Pasarela geographic chart.

This is a route/terrain-construction input, not a hydraulic domain or accepted
playable map. Preserve every captured vertex; dense interpolation is not a
survey. Never give the tributary the mainstem's discharge by implication.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from geo_frames import tm_forward, utm

ROOT = Path(__file__).resolve().parents[2]
RIVER = ROOT/'physics/data/real_world/futaleufu_river_chile'
CORRIDOR = RIVER/'production_corridor/rio_azul_swinging_bridge_to_pasarela'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def vertices(value):
    result = np.asarray(value, dtype=float)
    if result.ndim != 2 or result.shape[1] != 2 or len(result) < 2 or not np.isfinite(result).all():
        raise ValueError('At least two finite 2D vertices required')
    if np.any(np.linalg.norm(np.diff(result, axis=0), axis=1) <= 1e-8):
        raise ValueError('Repeated consecutive route vertex')
    return result


def mainstem_join(route_lonlat, mainstem_lonlat):
    """Require an exact captured common suffix, not a nearest-water jump."""
    route, main = vertices(route_lonlat), vertices(mainstem_lonlat)
    if np.any(abs(route[:, 0]) > 180) or np.any(abs(route[:, 1]) > 90):
        raise ValueError('Invalid geographic route')
    matches = np.all(route[:, None, :] == main[None, :, :], axis=2)
    shared = np.flatnonzero(matches.any(axis=1))
    if not len(shared) or shared[0] == 0:
        raise ValueError('Captured tributary and exact confluence required')
    first = int(shared[0])
    if not np.array_equal(shared, np.arange(first, len(route))):
        raise ValueError('Route departs from captured mainstem after joining')
    if not np.all(matches[first:].sum(axis=1) == 1):
        raise ValueError('Ambiguous repeated mainstem coordinate')
    indices = matches[first:].argmax(axis=1)
    if not np.all(np.diff(indices) == 1):
        raise ValueError('Mainstem reverses or omits captured vertices')
    return first, int(indices[0]), int(indices[-1])


def geographic_chart(xy, origin, spacing=2.):
    xy = vertices(xy)
    origin = np.asarray(origin, dtype=float)
    if origin.shape != (2,) or not np.isfinite(origin).all() or not np.isfinite(spacing) or spacing <= 0:
        raise ValueError('Finite origin and positive spacing required')
    delta = np.diff(xy, axis=0)
    lengths = np.linalg.norm(delta, axis=1)
    source_station = np.r_[0., np.cumsum(lengths)]
    # Include original corners in addition to the nominal lattice: never cut
    # across a bend just because the nearest regular samples straddle it.
    station = np.unique(np.r_[np.arange(0., source_station[-1], spacing), source_station])
    directions = delta / lengths[:, None]
    tangent = np.vstack([directions[0], directions[:-1]+directions[1:], directions[-1]])
    norm = np.linalg.norm(tangent, axis=1)
    if np.any(norm < .1):
        raise ValueError('Reversing route corner has no stable normal')
    tangent /= norm[:, None]
    normal = np.column_stack([-tangent[:, 1], tangent[:, 0]])
    # Native loading checks BOTH +/-256 m terrain-corridor edges with a 16 m
    # maximum step. Subdivide the chart (not the captured geometry) to 12 m,
    # retaining margin. This is sampling control, not proof of nonfolding wet
    # cross-sections; those still require source-water and native inverse tests.
    for _ in range(20):
        position = np.column_stack([np.interp(station, source_station, xy[:, i]) for i in (0, 1)])
        normals = np.column_stack([np.interp(station, source_station, normal[:, i]) for i in (0, 1)])
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        edge = np.maximum.reduce([np.linalg.norm(np.diff(position+sign*256*normals,axis=0),axis=1) for sign in (-1,1)])
        split = edge > 12.
        if not split.any():
            return np.column_stack([station, position-origin, normals]), source_station
        station = np.unique(np.r_[station, (station[:-1][split]+station[1:][split])/2.])
    raise ValueError('Could not bound native terrain-corridor edge sampling')


def build(output):
    output = output.resolve()
    output.relative_to(ROOT)
    if output.exists():
        raise ValueError('Fresh output directory required')
    route_path = CORRIDOR/'hydrography/route_stationing.json'
    corridor_path = CORRIDOR/'manifest.json'
    main_path = RIVER/'futaleufu_sources_2026_09/osm/futaleufu_centreline.json'
    frame_path = RIVER/'terrain/terminator_evidence_2026/terminator_evidence_runtime_coordinate_map.json'
    bound = {p: sha(p) for p in (route_path, corridor_path, main_path, frame_path)}
    route, corridor, main, frame = [json.loads(p.read_text()) for p in bound]
    if route['schema'] != 'raftsim.route_stationing.v1' or main['schema'] != 'raftsim.osm_river_centreline.v1':
        raise ValueError('Unexpected captured route format')
    lonlat = vertices([[p['lon'], p['lat']] for p in route['samples']])
    source = np.asarray(main['centreline_lon_lat_chain'], dtype=float)
    first, start, end = mainstem_join(lonlat, source[:, :2])
    if not np.array_equal(lonlat[[0, -1]], [corridor['route']['start_lon_lat'], corridor['route']['end_lon_lat']]):
        raise ValueError('Changed captured put-in or takeout')
    if frame['horizontal_crs'] != 'EPSG:32718 WGS 84 / UTM zone 18S' or frame['world_y_sign'] != -1:
        raise ValueError('Unexpected production geographic frame')
    xy = np.column_stack(tm_forward(lonlat[:, 0], lonlat[:, 1], utm(18, south=True)))
    points, stations = geographic_chart(xy, frame['horizontal_origin_m'])
    chart = dict(schema='raftsim.curved_river_coordinate_map.v1', river_id='futaleufu',
        section_id='rio_azul_to_pasarela_continuous_construction', world_y_sign=-1,
        horizontal_origin_m=frame['horizontal_origin_m'], horizontal_crs=frame['horizontal_crs'],
        vertical_datum_m=frame['vertical_datum_m'], vertical_reference=frame['vertical_reference'],
        mapping_policy='Captured OSM route with every original vertex retained plus at most 2 m interpolation, adaptively subdivided to a 12 m edge step at +/-256 m. Left normals blend adjacent segment directions without moving the centreline. Sparse source segments remain sparse evidence; this is not proof of nonfolding wet coverage.',
        points=points.tolist())
    report = dict(schema='raftsim.futaleufu_continuous_route.v1',
        sources_sha256={p.relative_to(ROOT).as_posix(): h for p, h in bound.items()},
        source_vertex_count=len(lonlat), chart_vertex_count=len(points),
        projected_route_length_m=float(stations[-1]),
        source_geographic_station_length_m=route['length_m'],
        source_segment_max_m=float(np.diff(stations).max()),
        native_corridor_half_width_m=256.,
        maximum_native_corridor_edge_step_m=float(max(np.linalg.norm(np.diff(points[:,1:3]+sign*256*points[:,3:5],axis=0),axis=1).max() for sign in (-1,1))),
        source_to_projected_stations_m=stations.tolist(),
        confluence=dict(source_route_vertex=first, source_mainstem_vertex=start,
            lon_lat=lonlat[first].tolist(), route_station_m=float(stations[first]),
            source_mainstem_chainage_m=float(source[start, 2])),
        takeout=dict(lon_lat=lonlat[-1].tolist(), source_mainstem_vertex=end,
            source_mainstem_chainage_m=float(source[end, 2])),
        rights='Derived from captured OpenStreetMap contributor data, ODbL-1.0; retain attribution and database obligations. No new imagery, guide artwork or surveyed coordinates asserted.',
        discharge_policy='No discharge assigned. Rio Azul and the upstream Futaleufu must join with separately evidenced or explicitly inferred flows; do not apply 400 m3/s throughout the tributary.',
        remaining=['Terrain and source-water coverage along the entire tributary and mainstem',
            'Confluence hydraulic domain and discharge evidence',
            'Nonfolding wet cross-sections and native inverse-coordinate validation',
            'Rapid registration, full production-hull descents, rescue continuity, normal packaged launch and 20 FPS'],
        runtime_implemented=False, hydraulic_domain_validated=False, engine_accepted=False)
    if not all(sha(p) == h for p, h in bound.items()):
        raise ValueError('Source changed during construction')
    output.mkdir(parents=True)
    with (output/'coordinate_map.json').open('x') as stream:
        json.dump(chart, stream, allow_nan=False)
    report['coordinate_map_sha256'] = sha(output/'coordinate_map.json')
    with (output/'manifest.json').open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    result = build(parser.parse_args().output)
    print(json.dumps({key: result[key] for key in ('projected_route_length_m', 'chart_vertex_count', 'confluence', 'runtime_implemented')}))
