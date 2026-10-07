"""Capture the official Chilko river polygon as planform evidence, not a stage survey."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import numpy as np

from capture_lidarbc_window import validate_window
from fetch_colorado_catalog_sources import read, validate_json

LAYER = 'https://delivery.maps.gov.bc.ca/arcgis/rest/services/mpcm/bcgwpub/MapServer/36'
CATALOGUE = 'https://open.canada.ca/data/en/dataset/f7dac054-efbf-402f-ab62-6fc4b32a619e'


def validate_polygon(payload, key):
    if payload.get('type') != 'FeatureCollection' or payload.get('exceededTransferLimit'):
        raise ValueError('Incomplete/non-GeoJSON river-polygon response')
    features = payload.get('features', [])
    if len(features) != 1:
        raise ValueError('Expected one reviewed river polygon, not a nearest-name match')
    feature = features[0]
    properties = feature['properties']
    if (properties.get('WATERBODY_KEY') != key or properties.get('WATERBODY_TYPE') != 'R' or
            properties.get('WATERSHED_GROUP_CODE') != 'CHIR'):
        raise ValueError('Unexpected waterbody identity')
    geometry = feature['geometry']
    if geometry['type'] not in ('Polygon', 'MultiPolygon'):
        raise ValueError('River area must have polygon geometry')
    polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
    count = 0
    for polygon in polygons:
        if not polygon:
            raise ValueError('Empty river polygon')
        for ring in polygon:
            points = np.asarray(ring, dtype=float)
            if (points.ndim != 2 or points.shape[1] != 2 or len(points) < 4 or
                    not np.isfinite(points).all() or not np.array_equal(points[0], points[-1]) or
                    np.any((points[:, 0] < -140) | (points[:, 0] > -114)) or
                    np.any((points[:, 1] < 48) | (points[:, 1] > 61))):
                raise ValueError('Invalid/unexpected WGS84 polygon ring')
            count += len(points)
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--window', nargs=4, type=float, required=True)
    parser.add_argument('--waterbody-key', type=int, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    bounds = validate_window(args.window)
    out = args.out
    receipt = out.with_suffix('.json')
    if out.suffix != '.geojson' or out.exists() or receipt.exists():
        raise ValueError('Fresh GeoJSON and provenance paths required')
    query = dict(f='geojson', where=f'WATERBODY_KEY={args.waterbody_key}',
                 geometry=','.join(map(str, bounds)), geometryType='esriGeometryEnvelope',
                 inSR=3157, outSR=4326, spatialRel='esriSpatialRelIntersects',
                 outFields='*', returnGeometry='true')
    url = LAYER + '/query?' + urlencode(query)
    raw = read(url)
    payload = validate_json(raw)
    vertices = validate_polygon(payload, args.waterbody_key)
    metadata = dict(schema='raftsim.chilko_fwa_polygon_capture.v1',
                    acquired_utc=datetime.now(timezone.utc).isoformat(),
                    source_url=url, catalogue_url=CATALOGUE, horizontal_crs='EPSG:4326',
                    selection_window_crs='EPSG:3157', selection_window_m=list(bounds),
                    waterbody_key=args.waterbody_key, vertex_count=vertices,
                    sha256=hashlib.sha256(raw).hexdigest(),
                    attribution='Contains information licensed under the Open Government Licence - British Columbia',
                    licence_url='https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc',
                    qualification='Official mapped river planform, not a flight-day shoreline, rapid boundary, bathymetry or hydraulic stage survey. Full intersecting polygon is preserved, not clipped or simplified.',
                    rapid_boundaries_verified=False, playable_acceptance=False)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    receipt.write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
