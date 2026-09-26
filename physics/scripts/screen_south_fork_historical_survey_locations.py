"""Locate historical survey site endpoints near the playable route, not transects.

Requires numpy/pyproj and the named NOAA grid in --grid-dir. No network fallback,
ballpark datum transform, vertical tie, or geometry modification is allowed.
Zone 10N is a regional hypothesis; proximity is corroboration, not verification
of source CRS, GPS accuracy, benchmark identity or channel-centre placement.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GRID = 'us_noaa_nadcon5_nad27_nad83_1986_conus.tif'
GRID_SHA = 'c7d587e0d0b39b9f46c7de850b9a6a468c17b7139f82a313aa43aa4a64d94fa8'
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/playable_route'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project_to_route(point, xy, stations):
    """Nearest nondegenerate segment with interpolated route station, in metres."""
    point, xy, stations = map(lambda x: np.asarray(x, dtype=float), (point, xy, stations))
    if point.shape != (2,) or xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 2:
        raise ValueError('Expected one 2D point and at least two 2D route points')
    if stations.shape != (len(xy),) or not all(np.isfinite(x).all() for x in (point, xy, stations)):
        raise ValueError('Invalid or non-finite route coordinates/stations')
    if not np.all(np.diff(stations) >= 0):
        raise ValueError('Route stations must not decrease')
    delta = np.diff(xy, axis=0)
    lengths2 = np.sum(delta * delta, axis=1)
    valid = lengths2 > 0
    if not valid.any():
        raise ValueError('Route has no nondegenerate segments')
    fraction = np.zeros(len(delta))
    fraction[valid] = np.clip(np.sum((point - xy[:-1])[valid] * delta[valid], axis=1) / lengths2[valid], 0, 1)
    nearest = xy[:-1] + fraction[:, None] * delta
    distances2 = np.sum((nearest - point) ** 2, axis=1)
    distances2[~valid] = np.inf
    index = int(np.argmin(distances2))
    return dict(station_m=float(stations[index] + fraction[index] * (stations[index+1]-stations[index])),
                distance_to_route_m=float(np.sqrt(distances2[index])),
                segment=index, fraction=float(fraction[index]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grid-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    grid = args.grid_dir.resolve() / GRID
    assert sha(grid) == GRID_SHA, 'Unexpected datum grid: review before use'
    import pyproj
    from pyproj.transformer import TransformerGroup
    from pyproj.aoi import AreaOfInterest
    pyproj.network.set_network_enabled(False)
    pyproj.datadir.append_data_dir(str(grid.parent))
    area = AreaOfInterest(-121.1, 38.6, -120.7, 38.9)
    first = TransformerGroup(26710, 26910, always_xy=True, area_of_interest=area, allow_ballpark=False)
    first_matches = [t for t in first.transformers if 'NAD27 to NAD83 (7)' in t.description]
    assert first.best_available and len(first_matches) == 1, 'Required NADCON5 operation unavailable'
    t1 = first_matches[0]
    # The scene declares generic WGS84, without realization/epoch. Explicitly
    # retain the 4m NAD83-to-WGS84 (1) screen; never silently claim cm registration.
    second = TransformerGroup(26910, 32610, always_xy=True, area_of_interest=area, allow_ballpark=False)
    second_matches = [t for t in second.transformers if 'NAD83 to WGS 84 (1)' in t.description]
    assert len(second_matches) == 1
    t2 = second_matches[0]
    source_path = ROOT / 'docs/reconstruction-review-2026-09-07/south-fork-historical-survey-20260926.json'
    source = json.loads(source_path.read_text())
    assert source['source_coordinate_label'] == 'UTM (NAD 27)'
    map_path = BASE / 'coordinate_map.json'
    assert json.loads(map_path.read_text())['horizontal_crs'] == 'EPSG:32610'
    route_path = BASE / 'route_source_profile.npz'
    with np.load(route_path) as route:
        xy = np.column_stack((route['utm_easting_m'], route['utm_northing_m']))
        stations = route['station_m'].copy()
    results = []
    for site in source['raw_site_endpoints']:
        result = dict(site=site['site'], endpoints={})
        for end in ('upper', 'lower'):
            raw = site[end]
            intermediate = t1.transform(*raw, errcheck=True)
            transformed = t2.transform(*intermediate, errcheck=True)
            inverse = t1.transform(*t2.transform(*transformed, direction='INVERSE', errcheck=True),
                                   direction='INVERSE', errcheck=True)
            closure = float(np.linalg.norm(np.asarray(inverse) - raw))
            assert np.isfinite(closure)
            result['endpoints'][end] = dict(source_xy=raw, scene_crs_xy=list(transformed),
                nad27_to_scene_shift_m=float(np.linalg.norm(np.asarray(transformed)-raw)),
                roundtrip_error_m=closure, roundtrip_1mm_passes=closure < .001,
                projected=project_to_route(transformed, xy, stations),
                untransformed_comparison=project_to_route(raw, xy, stations))
        results.append(result)
    report = dict(schema='raftsim.historical_survey_location_screen.v1',
        source_inventory_sha256=sha(source_path), coordinate_map_sha256=sha(map_path),
        route_sha256=sha(route_path), route_length_m=float(stations[-1]),
        grid=dict(name=GRID, sha256=sha(grid), url='https://cdn.proj.org/' + GRID),
        source_crs_hypothesis='EPSG:26710', target_crs='EPSG:32610',
        source_utm_zone_verified=False, pyproj_version=pyproj.__version__, proj_version=pyproj.proj_version_str,
        transformations=[dict(description=t.description, pipeline=t.definition, stated_accuracy_m=t.accuracy) for t in (t1,t2)],
        second_transform_best_available=second.best_available, network_enabled=False,
        sites=results, endpoint_distance_is_not_registration_error=True,
        individual_transects_registered=False, vertical_tie_established=False,
        geometry_or_cooked_fields_modified=False, suitable_for_geometry_promotion=False)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({r['site']: {k: v['projected'] for k,v in r['endpoints'].items()} for r in results}, indent=2))


if __name__ == '__main__':
    main()
