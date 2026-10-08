"""Locate guide-distance estimates on the full route, never catalog-order slots.

These points target geographic review. They are not measured rapid boundaries,
hole geometry, runtime registration, or permission to copy guide maps/assets.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from pyproj import Transformer


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'physics/data/real_world/futaleufu_river_chile'
ROUTE = BASE / 'production_corridor/rio_azul_swinging_bridge_to_pasarela/hydrography/continuous_route_2026_10_v2'
GUIDES = (
    dict(id='gorafting', url='https://gorafting.com/chile/futaleufu-river/',
         anchor=32.5, metres_per_unit=1000., unit='km',
         distances=[35.5, 39.25, 40., 40.3, 40.5], grades=['IV', 'V', 'IV', 'IV', 'IV']),
    dict(id='whitewaterguidebook', url='https://www.whitewaterguidebook.com/chile/futaleufu-river-inferno/',
         anchor=15.5, metres_per_unit=1609.344, unit='mile',
         distances=[17., 19.5, 20.2, 20.4, 20.5], grades=['III', 'V', 'III', 'III/V', 'III']),
)
NAMES = ('Asleep at the Wheel', 'Terminator', 'Son of Terminator', 'Khyber Pass', 'Himalayas')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def project(chart, confluence_station, guide_anchor, guide_station, metres_per_unit):
    points = np.asarray(chart['points'], dtype=float)
    origin = np.asarray(chart['horizontal_origin_m'], dtype=float)
    values = np.asarray([confluence_station, guide_anchor, guide_station, metres_per_unit], dtype=float)
    if (points.ndim != 2 or points.shape[0] < 2 or points.shape[1] != 5
            or not np.isfinite(points).all() or np.any(np.diff(points[:, 0]) <= 0)
            or origin.shape != (2,) or not np.isfinite(origin).all()
            or not np.isfinite(values).all() or metres_per_unit <= 0
            or chart.get('world_y_sign') != -1
            or not chart.get('horizontal_crs', '').startswith('EPSG:32718')):
        raise ValueError('Finite increasing UTM18S full-route chart with reflected engine Y required')
    station = confluence_station + (guide_station-guide_anchor)*metres_per_unit
    if not points[0, 0] < confluence_station < station <= points[-1, 0]:
        raise ValueError('Rapid estimate must lie downstream of the confluence within the full route')
    local = np.array([np.interp(station, points[:, 0], points[:, i]) for i in (1, 2)])
    east, north = origin+local
    lon, lat = Transformer.from_crs(32718, 4326, always_xy=True).transform(east, north)
    return dict(route_station_m=float(station), local_east_north_m=local.tolist(),
                source_projection_lon_lat=[lon, lat],
                unreal_xy_cm=(local*np.array([100., -100.])).tolist())


def build():
    manifest_path, chart_path = ROUTE/'manifest.json', ROUTE/'coordinate_map.json'
    manifest, chart = [json.loads(p.read_text()) for p in (manifest_path, chart_path)]
    if sha(chart_path) != manifest['coordinate_map_sha256']:
        raise ValueError('Full-route chart no longer matches its manifest')
    confluence = manifest['confluence']['route_station_m']
    old_path = BASE/'review/a4_stationing_digitizing_work_window_manifest.json'
    old = json.loads(old_path.read_text())
    rows = []
    for i, name in enumerate(NAMES):
        estimates = []
        for guide in GUIDES:
            estimates.append(dict(source=guide['id'], guide_station=guide['distances'][i],
                                  guide_unit=guide['unit'], source_grade=guide['grades'][i],
                                  **project(chart, confluence, guide['anchor'], guide['distances'][i],
                                            guide['metres_per_unit'])))
        stations = [p['route_station_m'] for p in estimates]
        previous = next(p for p in old['windows'] if p['rapid_name'] == name)
        rows.append(dict(name=name, location_status='source_distance_estimates_for_review',
                         estimates=estimates, source_estimate_span_m=[min(stations), max(stations)],
                         source_disagreement_m=max(stations)-min(stations),
                         rapid_start_m=None, rapid_end_m=None, chosen_runtime_station_m=None,
                         superseded_order_only_station_m=previous['route_order_station_m'],
                         superseded_order_slot_on_tributary=previous['route_order_station_m'] < confluence))
    return dict(schema='raftsim.futaleufu_guide_distance_review.v1', source_checked_on='2026-10-08',
                sources=[dict(id=g['id'], url=g['url'], anchor_name='Rio Azul confluence',
                              anchor_guide_station=g['anchor'], unit=g['unit']) for g in GUIDES],
                inputs_sha256={p.relative_to(ROOT).as_posix(): sha(p)
                               for p in (manifest_path, chart_path, old_path, Path(__file__))},
                confluence_route_station_m=confluence, route_length_m=manifest['projected_route_length_m'],
                method='Add each published distance from the shared confluence to its full-route station. '
                       'No catalog-order interpolation, averaging, inferred takeout equivalence, or stretching of the old crop.',
                limitations='Guide chainages are approximate and differ. The span between estimates is not a '
                            'confidence interval or rapid extent; actual bounds require landform/imagery corroboration. '
                            'Projected coordinates inherit OSM route uncertainty. No grade-to-flow equivalence is asserted.',
                rights='Source facts attributed to linked guides; no guide artwork, photos or paid GPS data copied. '
                       'Route derived from OpenStreetMap contributors under ODbL-1.0.',
                rapids=rows, runtime_modified=False, rapid_boundaries_verified=False,
                engine_accepted=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = build()
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
