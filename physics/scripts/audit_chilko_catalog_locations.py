"""Compare published Chilko point identities to existing construction geometry.

Point stationing is for source review, not rapid boundaries or navigation advice.
No runtime assets or existing captured files are changed.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from pyproj import Geod, Transformer

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'physics/data/real_world/chilko_river_bc'


def unique_object(pairs):
    """Refuse evidence silently lost through duplicate JSON keys at any depth."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate geographic evidence key: {key}')
        result[key] = value
    return result


def project(point, xy, station):
    xy, station, point = map(np.asarray, (xy, station, point))
    if (xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 2 or
            station.shape != (len(xy),) or point.shape != (2,) or
            not all(np.isfinite(a).all() for a in (xy, station, point)) or
            np.any(np.diff(station) <= 0)):
        raise ValueError('Invalid route or point')
    delta = np.diff(xy, axis=0)
    length2 = np.sum(delta * delta, axis=1)
    if np.any(length2 <= 0):
        raise ValueError('Duplicate route vertices')
    fraction = np.clip(np.sum((point - xy[:-1]) * delta, axis=1) / length2, 0, 1)
    distance = np.linalg.norm(xy[:-1] + fraction[:, None] * delta - point, axis=1)
    i = int(distance.argmin())
    return dict(route_station_m=float(station[i] + fraction[i] * (station[i+1] - station[i])),
                point_to_route_m=float(distance[i]))


def runtime_centreline(chart):
    if (chart.get('schema') != 'raftsim.curved_river_coordinate_map.v1' or
            chart.get('horizontal_crs') != 'EPSG:3157 NAD83(CSRS) / UTM zone 10N' or
            chart.get('world_y_sign') != -1):
        raise ValueError('Unexpected runtime coordinate frame')
    points = np.asarray(chart['points'], dtype=float)
    origin = np.asarray(chart['horizontal_origin_m'], dtype=float)
    if (points.ndim != 2 or points.shape[1] != 5 or len(points) < 2 or
            origin.shape != (2,) or not np.isfinite(points).all() or
            not np.isfinite(origin).all() or np.any(np.diff(points[:, 0]) <= 0)):
        raise ValueError('Invalid runtime centreline')
    # Columns are station, east, north, normal-east, normal-north. The Unreal
    # Y reflection does not apply to these geographic east/north coordinates.
    return np.column_stack((points[:, 1:3] + origin, points[:, 0]))


def validate_identity_checks(evidence):
    """Unresolved names cannot authorize aliases or distinct placed sections."""
    checks = evidence.get('identity_checks', [])
    for check in checks:
        if (len(check.get('names', [])) != 2 or
                not check.get('sources') or
                any(source not in evidence['sources'] for source in check['sources'])):
            raise ValueError('Identity comparison lacks named sources')
        if check.get('relationship') == 'unresolved' and (
                check.get('automatic_alias_allowed') is not False or
                check.get('distinct_geographic_sections_confirmed') is not False):
            raise ValueError('Unresolved identity cannot authorize geographic placement')
    return checks


def corrected_anchor_stationing(route, parent_hash, anchors, entries):
    """Reproject fixed source points; never subtract a blanket route-length delta.

    Unverified rapid identities and interval boundaries stay unverified. This
    receipt is for a candidate route, not authorization to change game labels.
    """
    from correct_chilko_route import lineage, projected, route_points, sha
    route=Path(route)
    receipt,_=lineage(route)
    if receipt['parent_route']['sha256']!=parent_hash:
        raise ValueError('Corrected stationing has a different original route')
    xy=projected(route_points(json.loads(route.read_text())))
    station=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
    result={}
    for anchor in anchors:
        row=project(projected([anchor['lon_lat']])[0],xy,station)
        result[anchor['id']]=dict(id=anchor['id'],lon_lat=anchor['lon_lat'],**row,
            previous_terrain_route_station_m=anchor['terrain_route_station_m'],
            station_change_m=row['route_station_m']-anchor['terrain_route_station_m'])
    brackets=[]
    for entry in entries:
        if 'upstream_anchor' not in entry:continue
        values=[result[entry[key]]['route_station_m'] for key in ('upstream_anchor','downstream_anchor')]
        if values[0]>=values[1]:raise ValueError('Corrected source marker sequence reverses')
        brackets.append(dict(name=entry['name'], sources=entry['sources'],
            location_status=entry['location_status'],
            upstream_anchor=entry['upstream_anchor'],downstream_anchor=entry['downstream_anchor'],
            marker_station_bracket_m_not_rapid_bounds=values,
            rapid_boundary_coordinates=None, runtime_placement_authorized=False))
    return dict(route=dict(path=str(route.resolve()),sha256=sha(route)),
        route_length_m=float(station[-1]),station_frame='EPSG:3157 corrected geographic route; not numerical chart or lake-outlet kilometres',
        anchors=list(result.values()),sequence_brackets=brackets,
        named_rapid_boundaries_established=False,runtime_assets_changed=False,
        qualification='Same published geographic points on the corrected candidate; point precision and unresolved naming are unchanged')


def audit(corrected_route=None):
    paths = {
        'evidence': DATA / 'observed_rapids/catalog_location_evidence_2026_10_06.json',
        'route': DATA / 'production_corridor/chilko_river_lodge_to_taseko_junction/hydrography/route_stationing.json',
        'route_geometry': DATA / 'production_corridor/chilko_river_lodge_to_taseko_junction/hydrography/route_centerline.geojson',
        'route_alignment': DATA / 'production_corridor/chilko_river_lodge_to_taseko_junction/hydrography/route_alignment_evidence_2026_10_07.json',
        'current_coordinate_map': DATA / 'terrain/lava_canyon_evidence_2023/lava_canyon_evidence_2023_runtime_coordinate_map.json',
        'terrain_manifest': DATA / 'terrain/lava_canyon_evidence_2023/lava_canyon_evidence_2023_terrain_manifest.json',
        'current_rapids': DATA / 'observed_rapids/lava_canyon_observed_rapids.json',
    }
    raw = {key: path.read_bytes() for key, path in paths.items()}
    data = {key: json.loads(blob, object_pairs_hook=unique_object) for key, blob in raw.items()}
    identity_checks = validate_identity_checks(data['evidence'])
    samples = data['route']['samples']
    transform = Transformer.from_crs(4326, 3157, always_xy=True)
    xy = np.array(transform.transform([p['lon'] for p in samples],
                                      [p['lat'] for p in samples])).T
    station = np.array([p['station_m'] for p in samples])
    lonlat = np.array([[p['lon'], p['lat']] for p in samples])
    geometries = data['route_geometry']['features']
    if (len(geometries) != 1 or geometries[0]['geometry']['type'] != 'LineString' or
            not np.array_equal(lonlat, np.asarray(geometries[0]['geometry']['coordinates'])[:, :2])):
        raise ValueError('Stored stationing and terrain route do not use the same vertices')
    _, _, distances = Geod(a=6371000, b=6371000).inv(
        lonlat[:-1, 0], lonlat[:-1, 1], lonlat[1:, 0], lonlat[1:, 1])
    if not np.allclose(station, np.r_[0., np.cumsum(distances)], atol=.001, rtol=0):
        raise ValueError('Stored stationing no longer matches the declared spherical frame')
    terrain_station = np.r_[0., np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
    alignment = data['route_alignment']
    if (alignment['route_sha256'] != hashlib.sha256(raw['route_geometry']).hexdigest() or
            alignment.get('observation_crs') != 'EPSG:32610' or
            alignment.get('named_rapid_placement_authorized') is not False or
            alignment.get('automatic_route_replacement_authorized') is not False):
        raise ValueError('Route alignment evidence changed identity or authorized unsupported placement')
    image_to_terrain = Transformer.from_crs(32610, 3157, always_xy=True)
    image_checks = []
    for observation in alignment['observations']:
        if 'indicative_channel_point_m' not in observation:
            continue
        image_checks.append(dict(id=observation['id'], **project(
            image_to_terrain.transform(*observation['indicative_channel_point_m']), xy, terrain_station),
            qualification='Indicative 10 m imagery spot check, not surveyed banks or a replacement route vertex'))
    anchors = {p['id']: dict(p, **project(transform.transform(*p['lon_lat']), xy, station))
               for p in data['evidence']['anchors']}
    for anchor in anchors.values():
        anchor['terrain_route_station_m'] = project(
            transform.transform(*anchor['lon_lat']), xy, terrain_station)['route_station_m']
    outputs = data['terrain_manifest']['outputs']
    if (outputs['runtime_coordinate_map'] != paths['current_coordinate_map'].relative_to(ROOT).as_posix() or
            outputs['runtime_coordinate_map_sha256'] != hashlib.sha256(raw['current_coordinate_map']).hexdigest()):
        raise ValueError('Runtime coordinate map does not match terrain manifest')
    current = runtime_centreline(data['current_coordinate_map'])
    comparisons = []
    for rapid_id, anchor_id in [('bidwell', 'bcww_bidwell'), ('white_mile', 'bcww_white_mile')]:
        rapid = next(p for p in data['current_rapids']['rapids'] if p['id'] == rapid_id)
        local_s = rapid['station_m']
        if not current[0, 2] <= local_s <= current[-1, 2]:
            raise ValueError(f'{rapid_id} starts outside existing centreline')
        point = [np.interp(local_s, current[:, 2], current[:, col]) for col in (0, 1)]
        registered = project(point, xy, station)
        comparisons.append(dict(rapid_id=rapid_id, existing_start_station_m=local_s,
            existing_start_route_station_m=registered['route_station_m'],
            source_marker_route_station_m=anchors[anchor_id]['route_station_m'],
            displacement_from_source_marker_m=registered['route_station_m'] - anchors[anchor_id]['route_station_m'],
            qualification='Existing inferred rapid start versus published representative point; not matched surveyed boundaries'))
    entries = []
    for entry in data['evidence']['entries']:
        row = dict(entry)
        if 'upstream_anchor' in entry:
            bracket = [anchors[entry[key]]['route_station_m']
                       for key in ('upstream_anchor', 'downstream_anchor')]
            if bracket[0] >= bracket[1]:
                raise ValueError('Reversed source sequence')
            row['source_marker_bracket_m_not_rapid_bounds'] = bracket
            row['terrain_marker_bracket_m_not_rapid_bounds'] = [
                anchors[entry[key]]['terrain_route_station_m']
                for key in ('upstream_anchor', 'downstream_anchor')]
        entries.append(row)
    result=dict(schema='raftsim.chilko_catalog_location_audit.v2', runtime_ready=False,
        source_inputs={key: dict(path=str(paths[key].relative_to(ROOT)),
            sha256=hashlib.sha256(blob).hexdigest()) for key, blob in raw.items()},
        route_origin='Existing FWA lodge-to-Taseko construction route; not lake-outlet river kilometres',
        route_station_frame='Stored spherical-distance stationing, radius 6371000 m; not terrain-grid chainage',
        terrain_route_station_frame='EPSG:3157 segment arc length on the same FWA vertices; not smoothed runtime chainage',
        route_lengths_m=dict(stored=float(station[-1]), terrain_projected=float(terrain_station[-1])),
        route_alignment_status=alignment['status'],
        route_alignment_scope=alignment['scope'],
        route_alignment_spot_checks=image_checks,
        current_station_frame='Actual Gaussian-smoothed runtime coordinate map, not unsmoothed evidence centreline stationing',
        anchors=list(anchors.values()), entries=entries, identity_checks=identity_checks,
        qualitative_location_constraints=data['evidence'].get('qualitative_location_constraints', []),
        rejected_location_leads=data['evidence'].get('rejected_location_leads', []),
        current_map_comparisons=comparisons,
        current_centreline_route_extent_m=[project(current[i, :2], xy, station)['route_station_m'] for i in (0, -1)],
        geographic_acceptance='blocked_by_existing_label_conflict_and_unresolved_boundaries',
        modified_runtime_assets=False)
    if corrected_route is not None:
        result['corrected_candidate_stationing']=corrected_anchor_stationing(corrected_route,
            hashlib.sha256(raw['route_geometry']).hexdigest(),list(anchors.values()),entries)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--corrected-route',type=Path,help='Also project unchanged published points onto a lineage-verified corrected candidate')
    args = parser.parse_args()
    result = audit(args.corrected_route)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2, allow_nan=False))
