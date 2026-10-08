"""Project source-identified Pearce Ferry takeout, not an arbitrary river mile.

Produces a source-location receipt only. Numerical chart stationing, wet-bank
approach, ramp geometry/collision and native completion still require testing.
Never truncate captured terrain or alter a playable map from this receipt.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from pyproj import Transformer

from build_colorado_catalog_evidence import project

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / ('physics/data/real_world/colorado_river_grand_canyon_rowing/'
                   'review/pearce_ferry_location_evidence_2026_10_07.json')


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def checked_node(root, expected):
    matches = root.findall("./node[@id='" + expected['node_id'] + "']")
    if len(matches) != 1:
        raise ValueError('Missing or duplicate source node')
    node = matches[0]
    for key in ('version', 'timestamp'):
        if node.get(key) != expected[key]:
            raise ValueError('Source node revision changed')
    tags = {tag.get('k'): tag.get('v') for tag in node.findall('tag')}
    key, value = expected['required_tag']
    if tags.get('name') != expected['name'] or tags.get(key) != value:
        raise ValueError('Source node identity changed')
    lonlat = [float(node.attrib['lon']), float(node.attrib['lat'])]
    if (not np.isfinite(lonlat).all() or lonlat != expected['lon_lat'] or
            not -180 <= lonlat[0] <= 180 or not -90 <= lonlat[1] <= 90):
        raise ValueError('Source coordinate changed or invalid')
    return lonlat


def register(chart, evidence, osm):
    """All inputs are bytes so receipt hashes bind exactly what was inspected."""
    info = json.loads(evidence)
    if (info.get('schema') != 'raftsim.colorado_takeout_evidence.v1' or
            info.get('runtime_ready') is not False or
            info.get('ramp_dimensions_surveyed') is not False):
        raise ValueError('Unsupported takeout evidence scope')
    if sha(chart) != info['source_chart_sha256']:
        raise ValueError('Source route identity changed')
    capture = info['osm_capture']
    if (sha(osm) != capture['sha256'] or capture['coordinate_crs'] != 'EPSG:4326' or
            capture['license'] != 'ODbL-1.0' or not capture['attribution']):
        raise ValueError('OSM source identity or attribution changed')
    mapping = json.loads(chart)
    if (mapping.get('schema') != 'raftsim.curved_river_coordinate_map.v1' or
            mapping.get('river_id') != 'colorado_river' or
            mapping.get('section_id') != 'colorado_continuous_source_route' or
            mapping.get('world_y_sign') != -1):
        raise ValueError('Expected geographic source route, not runtime chart')
    points = np.asarray(mapping['points'], dtype=float)
    origin = np.asarray(mapping['horizontal_origin_epsg6404_m'], dtype=float)
    if (points.ndim != 2 or points.shape[1] != 5 or len(points) < 2 or
            origin.shape != (2,) or not np.isfinite(origin).all() or
            not np.isfinite(points).all() or points[0, 0] != 0):
        raise ValueError('Invalid source route frame')
    # World Y reflection is only for native centimetres, never geographic north.
    line = points[:, 1:3] + origin
    stations = points[:, 0]
    if not np.allclose(np.linalg.norm(np.diff(line, axis=0), axis=1),
                       np.diff(stations), rtol=1e-6, atol=.001):
        raise ValueError('Source stationing disagrees with metric route geometry')
    root = ET.fromstring(osm)
    if root.tag != 'osm':
        raise ValueError('Expected OSM XML source')
    transform = Transformer.from_crs(4326, 6404, always_xy=True)
    rows = {}
    for key in ('takeout', 'downstream_rapid'):
        expected = info[key]
        lonlat = checked_node(root, expected)
        xy = transform.transform(*lonlat)
        s, lateral, distance = project([xy], line, stations, chunk=1)
        if not 0 < s[0] < stations[-1] or distance[0] > 100:
            raise ValueError('Mapped feature outside source corridor or clamped to endpoint')
        rows[key] = dict(name=expected['name'], source_node_id=expected['node_id'],
            source_version=expected['version'], source_timestamp=expected['timestamp'],
            lon_lat=lonlat, projected_epsg6404_m=list(xy),
            source_route_station_m=float(s[0]), source_left_lateral_m=float(lateral[0]),
            point_to_source_route_m=float(distance[0]))
    takeout = rows['takeout']['source_route_station_m']
    rapid = rows['downstream_rapid']['source_route_station_m']
    if rapid <= takeout or rows['takeout']['source_left_lateral_m'] <= 0:
        raise ValueError('Takeout must be on river left upstream of the rapid')
    rejected = []
    for point in info['rejected_takeout_points']:
        s, lateral, distance = project([transform.transform(*point['lon_lat'])],
                                      line, stations, chunk=1)
        rejected.append(dict(point, source_route_station_m=float(s[0]),
                             point_to_source_route_m=float(distance[0])))
    return dict(schema='raftsim.colorado_takeout_registration.v1',
        inputs_sha256=dict(source_chart=sha(chart), evidence=sha(evidence), osm=sha(osm)),
        coordinate_transform=dict(source='EPSG:4326', target='EPSG:6404',
            description=transform.description, declared_accuracy_m=transform.accuracy,
            qualification='Transform accuracy does not establish source point survey accuracy'),
        source_station_frame='Captured geographic polyline metric arc length; not numerical hydraulic chart station or guide mile',
        **rows, rejected_takeout_points=rejected,
        takeout_to_rapid_source_distance_m=rapid-takeout,
        retained_source_extent_m=[float(stations[0]), float(stations[-1])],
        source_extent_beyond_takeout_m=float(stations[-1]-takeout),
        attribution=capture['attribution'], license=capture['license'],
        license_url=capture['license_url'],
        runtime_finish_station_m=None, runtime_ready=False, runtime_assets_changed=False,
        qualification='Mapped takeout point registered; not surveyed ramp bounds, navigable approach or accepted native finish')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chart', type=Path, required=True)
    parser.add_argument('--osm', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = register(args.chart.read_bytes(), args.evidence.read_bytes(), args.osm.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2, allow_nan=False))
