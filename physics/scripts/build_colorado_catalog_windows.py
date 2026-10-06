"""Georeferenced construction inputs for every catalogued Colorado rapid.

No terrain or playable-map acceptance is implied. The 2021 table supplies a
longitudinal water profile and bed *statistics*, never full-width bathymetry.
Missing values remain null; acquisition/interpolation flags remain attached.
"""
import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / 'physics/data/real_world/named_rapid_source_catalog.json'
DEFAULT_SOURCE = ROOT / 'physics/data/real_world/colorado_river_grand_canyon_rowing/sources_all_rapids_2026_10'
PROFILE = Path('profile_extracted/1_profile/watersurface_riverbed_profile_2021.csv')
METADATA = Path('profile_extracted/1_profile/watersurface_riverbed_profile_2021_metadata.xml')
MILE_M = 1609.344
TEXT_FIELDS = {'geomorphic_reach', 'ws_final_source', 'ws_nonincreasing_source'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_profile(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        rows = [{k: v if k in TEXT_FIELDS else None if v in ('NA', '') else float(v)
                 for k, v in row.items()} for row in csv.DictReader(f)]
    if len(rows) < 2:
        raise ValueError('Incomplete longitudinal profile')
    for i, row in enumerate(rows):
        if any(row.get(k) is None or not math.isfinite(row[k])
               for k in ('rm', 'easting', 'northing', 'ws_final', 'ws_nonincreasing')):
            raise ValueError('Missing/nonfinite profile coordinates or water height')
        if any(isinstance(v, float) and not math.isfinite(v) for v in row.values()):
            raise ValueError('Nonfinite profile value')
        if i and not 0 < row['rm'] - rows[i-1]['rm'] <= .011:
            raise ValueError('Unordered, duplicate or missing profile samples')
    return rows


def registered_label(name):
    # Georgie was formerly 24 Mile; 24.5 Mile is a DIFFERENT rapid.
    return '24-Mile Rapid' if name == 'Georgie' else name + ' Rapid'


def window(rapid, feature, profile, half_window_m=800.):
    if not math.isfinite(half_window_m) or half_window_m < 100:
        raise ValueError('Construction window must be finite and at least 100 m either side')
    attr = feature['attributes']
    if attr['rapid'] != registered_label(rapid['name']):
        raise ValueError('Rapid registration mismatch')
    # Keep the published catalog mile AND the distinct USGS line mile.
    mile = float(attr['rm_label'])
    samples = [dict(r) for r in profile if abs(r['rm']-mile)*MILE_M <= half_window_m]
    if len(samples) < 3 or samples[0]['rm'] >= mile or samples[-1]['rm'] <= mile:
        raise ValueError('Window does not bracket the USGS rapid point')
    if ((mile-samples[0]['rm'])*MILE_M < half_window_m-17 or
            (samples[-1]['rm']-mile)*MILE_M < half_window_m-17):
        raise ValueError('Source ends before the requested construction window')
    origin = [samples[0]['easting'], samples[0]['northing']]
    arc = 0.
    for i, row in enumerate(samples):
        if i:
            arc += math.hypot(row['easting']-samples[i-1]['easting'], row['northing']-samples[i-1]['northing'])
        row['local_east_m'] = row['easting']-origin[0]
        row['local_north_m'] = row['northing']-origin[1]
        row['local_arc_station_m'] = arc
        row['source_river_mile_station_m'] = (row['rm']-samples[0]['rm'])*MILE_M
        row['water_evidence_kind'] = ('interpolated' if row['ws_final_source'].startswith('interpolate')
                                      else 'dsm_derived' if row['ws_final_source'] == 'DSM' else 'surveyed_gnss')
        if row['ws_final_source'] not in ('applanix', 'r10', 'DSM', 'interpolate - select', 'interpolate - no data'):
            raise ValueError('Unknown water evidence source; do not silently call it measured')
    def local_station(rm):
        for a, b in zip(samples, samples[1:]):
            if a['rm'] <= rm <= b['rm']:
                return a['local_arc_station_m']+(b['local_arc_station_m']-a['local_arc_station_m'])*(rm-a['rm'])/(b['rm']-a['rm'])
        raise ValueError('Point is outside construction window')
    point = feature['geometry']
    point_distance = min(math.hypot(point['x']-r['easting'], point['y']-r['northing']) for r in samples)
    if point_distance > 40:
        raise ValueError('Rapid point and profile disagree spatially by more than 40 m')
    missing = [r for r in samples if r['min_bed_height'] is None]
    return dict(schema='raftsim.colorado_rapid_construction_window.v1',
        name=rapid['name'], catalog_class=rapid['class'], catalog_river_mile=rapid['river_mile'],
        usgs_label=attr['rapid'], usgs_river_mile=mile,
        catalog_to_usgs_mile_delta=mile-rapid['river_mile'],
        point_to_nearest_profile_sample_m=point_distance,
        rapid_point_local_station_m=local_station(mile),
        construction_bounds_only=True, rapid_entry_exit_bounds_verified=False,
        horizontal_crs='EPSG:6404', origin_east_north_m=origin,
        local_axes='east/north metres; downstream arc station is separately derived; Unreal north requires Y sign conversion',
        vertical_datum='NAD83(2011) ellipsoid; only ws_final_navd88 is NAVD88',
        profile_survey_dates='2021-05-29 through 2021-06-05', profile_survey_flow_cfs_approx=8400,
        runtime_target_flow_cfs=8000, flow_match='different; surface cannot be asserted measured at runtime discharge',
        length_m=arc, sample_count=len(samples),
        water_source_counts=dict(Counter(r['ws_final_source'] for r in samples)),
        missing_bed_statistic_samples=len(missing),
        bed_statistic_sample_coverage=(len(samples)-len(missing))/len(samples),
        full_channel_bathymetry_coverage=None,
        bounds_epsg6404=[min(r['easting'] for r in samples), min(r['northing'] for r in samples),
                         max(r['easting'] for r in samples), max(r['northing'] for r in samples)],
        limitations=['Window bounds are construction margins, not surveyed rapid start/end.',
                    'min_bed_height is a 1st-percentile statistic per river-mile slice, not a cross-section.',
                    'max_bed_depth is a 99th-percentile statistic; do not extrude either across channel width.',
                    'ws_nonincreasing is a separately labelled modelling profile, not raw measured water.',
                    'No bank width, submerged rock shape, safe line or difficulty match is established.'],
        samples=samples)


def build(source, out):
    if out.exists():
        raise ValueError('Fresh construction output required')
    manifest = json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    for name in ('rapid_points_000.json', 'watersurface_riverbed_profile_tables.7z'):
        receipt = next(r for r in manifest['files'] if r['file'] == name)
        if sha(source/name) != receipt['sha256']:
            raise ValueError('Captured source checksum mismatch: '+name)
    points = json.loads((source/'rapid_points_000.json').read_text(encoding='utf-8'))
    if points['spatialReference'].get('latestWkid', points['spatialReference']['wkid']) != 6404:
        raise ValueError('Unexpected rapid point CRS')
    profile = read_profile(source/PROFILE)
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    rapids = next(r['rapids'] for r in catalog['rivers'] if r['river_id'] == 'colorado_river_grand_canyon_rowing')
    products = []
    for rapid in rapids:
        candidates = [f for f in points['features'] if f['attributes']['rapid'] == registered_label(rapid['name'])]
        if len(candidates) != 1:
            raise ValueError('Missing or ambiguous source rapid: '+rapid['name'])
        products.append(window(rapid, candidates[0], profile))
    out.mkdir(parents=True)
    for product in products:
        name = re.sub(r'[^a-z0-9]+', '_', product['name'].lower()).strip('_')
        (out/(name+'.json')).write_text(json.dumps(product, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    index = dict(schema='raftsim.colorado_rapid_construction_index.v1',
        inputs_sha256={str(p): sha(p) for p in (CATALOG, source/PROFILE, source/METADATA, source/'rapid_points_000.json')},
        source_doi=manifest['profile_release_doi'], source_rights=manifest['profile_rights'],
        source_rights_url=manifest['profile_rights_source'],
        alias_authority='https://www.nps.gov/articles/000/revolutionizing-the-river-down-the-colorado-river-through-grand-canyon.htm',
        playable_map_count=0, source_window_count=len(products),
        windows=[{k:v for k,v in p.items() if k != 'samples'} for p in products])
    (out/'index.json').write_text(json.dumps(index, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return index


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    index = build(args.source, args.out)
    print(f"{index['source_window_count']} georeferenced construction windows; no playable-map acceptance")
