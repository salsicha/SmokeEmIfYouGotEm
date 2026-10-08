"""Register guide points to retained OSM controls, never to catalog-order spacing.

This produces geographic SEARCH locations, not accepted rapid boundaries or
game assets. It refuses extrapolation past the first/last mapped controls.
The original approximate OSM chain frame and original node coordinates remain
explicit; no guide km is mistaken for a station in the current Huacas map.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'physics/data/real_world/pacuare_river_costa_rica'
EVIDENCE = DATA / 'observed_rapids/catalog_order_evidence_2026_10_07.json'
ROUTE = DATA / 'huacas_sources_2026_09/osm/pacuare_centreline.json'
CATALOG = ROOT / 'physics/data/real_world/named_rapid_source_catalog.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_route(data):
    points = np.asarray(data['centreline_lon_lat_chain'], dtype=float)
    if (data.get('schema') != 'raftsim.osm_river_centreline.v1' or
            data.get('relation') != 12000489 or data.get('join_max_endpoint_gap_deg') != 0 or
            points.ndim != 2 or points.shape[1] != 3 or len(points) < 2 or
            not np.isfinite(points).all() or np.any(np.diff(points[:, 2]) <= 0) or
            np.any(abs(points[:, 0]) > 180) or np.any(abs(points[:, 1]) >= 90)):
        raise ValueError('Continuous finite downstream Pacuare source route required')
    return points


def controls(data, evidence):
    route = validate_route(data)
    nodes = {n['id']: n for n in data['nodes']}
    if len(nodes) != len(data['nodes']):
        raise ValueError('Duplicate source node identities')
    result = []
    for node_id, km in evidence['osm_control_guide_km']:
        node = nodes[node_id]
        values = [km, node['chain_m'], node['lon'], node['lat'], node['offset_from_centreline_m']]
        if (not np.isfinite(values).all() or km < 0 or
                not route[0, 2] <= node['chain_m'] <= route[-1, 2] or
                not 0 <= node['offset_from_centreline_m'] <= 50):
            raise ValueError('Control outside source route or excessive mapped offset')
        result.append(dict(osm_node_id=node_id, guide_km=km, source_chain_m=node['chain_m'],
            original_lon_lat=[node['lon'], node['lat']],
            original_offset_m=node['offset_from_centreline_m']))
    values = np.array([[r['guide_km'], r['source_chain_m']] for r in result])
    if (len(result) < 2 or len(set(r['osm_node_id'] for r in result)) != len(result) or
            np.any(np.diff(values, axis=0) <= 0)):
        raise ValueError('Distinct increasing mapped controls required')
    return result


def register(km, anchors, route):
    if not np.isfinite(km) or km < 0:
        raise ValueError('Finite nonnegative guide distance required')
    guide = np.array([a['guide_km'] for a in anchors])
    chain = np.array([a['source_chain_m'] for a in anchors])
    if not guide[0] <= km <= guide[-1]:
        return dict(status='outside_control_span_no_extrapolation', guide_km=km,
                    source_chain_m=None, lon_lat=None)
    station = float(np.interp(km, guide, chain))
    point = [float(np.interp(station, route[:, 2], route[:, j])) for j in (0, 1)]
    exact = np.flatnonzero(guide == km)
    if len(exact):
        control = anchors[int(exact[0])]
        return dict(status='published_osm_control_point_not_rapid_bounds', guide_km=km,
            source_chain_m=station, lon_lat=control['original_lon_lat'],
            route_projection_lon_lat=point, osm_node_id=control['osm_node_id'])
    lower = int(np.searchsorted(guide, km)-1)
    return dict(status='piecewise_registered_search_point_not_rapid_bounds', guide_km=km,
        source_chain_m=station, lon_lat=point,
        bracketing_osm_node_ids=[anchors[i]['osm_node_id'] for i in (lower, lower+1)])


def build():
    paths = {'catalog': CATALOG, 'guide_index': EVIDENCE, 'osm_route': ROUTE,
             'osm_capture': ROUTE.parent/'pacuare_overpass.json'}
    hashes = {key: sha(path) for key, path in paths.items()}
    data = json.loads(ROUTE.read_text(encoding='utf-8'))
    evidence = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    raw = json.loads(paths['osm_capture'].read_text(encoding='utf-8'))
    raw_nodes = {n['id']: n for n in raw['elements'] if n['type'] == 'node'}
    route = validate_route(data); anchors = controls(data, evidence)
    for a in anchors:
        n = raw_nodes[a['osm_node_id']]
        if a['original_lon_lat'] != [n['lon'], n['lat']]:
            raise ValueError('Derived point differs from original captured node')
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    river = next(r for r in catalog['rivers'] if r['river_id'] == 'pacuare_river_costa_rica')
    guide = dict(evidence['guide_rapid_km'])
    if [r['name'] for r in river['rapids'] if r['name'] != 'Bobo Falls'] != list(guide):
        raise ValueError('Catalog sequence differs from source index')
    records = []
    for rapid in river['rapids']:
        name = rapid['name']
        if name in guide:
            location = register(guide[name], anchors, route)
        elif name == 'Bobo Falls':
            location = dict(status='name_identity_and_boundaries_unresolved',
                source_chain_m=None, lon_lat=None,
                source_order_bracket=evidence['bobo'])
        else:
            raise ValueError('Rapid missing source evidence')
        records.append(dict(name=name, order=rapid['order'], catalog_class=rapid['class'],
            location=location, rapid_boundary_coordinates=None, runtime_placement_authorized=False))
    if any(sha(paths[k]) != value for k, value in hashes.items()):
        raise ValueError('Geographic evidence changed during registration')
    offsets = [a['source_chain_m']-1000*a['guide_km'] for a in anchors]
    return dict(schema='raftsim.pacuare.catalog_location_registration.v1',
        scope='Source-registered search points, not rapid bounds, a surveyed route or game acceptance',
        sources={k: dict(path=str(p.resolve()), sha256=hashes[k]) for k,p in paths.items()},
        source_chain_frame=data['chainage'], guide_frame=evidence['guide_origin'],
        controls=anchors, single_offset_spread_m=max(offsets)-min(offsets),
        offset_spread_is_accuracy_bound=False, method='Piecewise linear guide-to-OSM chain registration; no extrapolation',
        rapid_locations=records, production_promoted=False,
        attribution=data['licence'], guide_rights=evidence['rights'],
        licence_scope='Only OSM geometry and link-only guide facts used; no IGN/SNIT data used')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():parser.error('Fresh registration path required')
    result=build()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2,allow_nan=False,ensure_ascii=False)
    for row in result['rapid_locations']:
        print(row['name'],row['location']['status'],row['location']['source_chain_m'])
