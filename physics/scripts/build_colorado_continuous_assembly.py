"""Register Colorado source reaches in one world, without inventing connections.

The route file uses the native progress-coordinate format. Hydraulic charts keep
their own station axes: concatenating their local s coordinates would distort
the geography. This construction contract cannot be installed as solved water.
"""
import argparse
import copy
import json
import math
from pathlib import Path

import numpy as np

from build_colorado_catalog_windows import (CATALOG, DEFAULT_SOURCE, PROFILE,
                                          ROOT, read_profile, registered_label, sha)
from build_colorado_catalog_evidence import project

DATA = DEFAULT_SOURCE.parent


def native_progress_points(station, xy, normal, origin):
    """Densify without moving the survey polyline or weakening native guards.

    Native charts bound each 256 m corridor-edge step to 16 m. The survey's
    0.01-mile spacing already exceeds that on straight segments. Interpolate
    positions and unit normals, retaining all original vertices and arc length.
    """
    parts = []
    for i in range(len(station)-1):
        if np.dot(normal[i], normal[i+1]) <= -.95:
            raise ValueError('Reversing route normals require source review')
        count = max(1, int(math.ceil((station[i+1]-station[i])/8)))
        while True:
            t = np.linspace(0., 1., count+1)
            positions = xy[i]+t[:, None]*(xy[i+1]-xy[i])
            normals = normal[i]+t[:, None]*(normal[i+1]-normal[i])
            normals /= np.linalg.norm(normals, axis=1)[:, None]
            edge_step = max(np.linalg.norm(np.diff(positions+sign*256*normals, axis=0), axis=1).max()
                            for sign in (-1, 1))
            if edge_step <= 15.5:
                break
            count *= 2
            if count > 4096:
                raise ValueError('Unbounded native route interpolation')
        parts.append(np.column_stack([station[i]+t[:-1]*(station[i+1]-station[i]),
                                      positions[:-1]-origin, normals[:-1]]))
    parts.append(np.array([[station[-1], *(xy[-1]-origin), *normal[-1]]]))
    return np.concatenate(parts).tolist()


def rebase_chart(chart, origin, datum):
    """Rigid translation only; preserve chart station, normals and wet geometry."""
    if (chart.get('schema') != 'raftsim.curved_river_coordinate_map.v1' or
            chart.get('world_y_sign') != -1 or
            chart.get('vertical_reference') != 'NAD83(2011) ellipsoid heights'):
        raise ValueError('Only explicit Colorado east/north, ellipsoid charts are supported')
    old = np.asarray(chart['horizontal_origin_epsg6404_m'], dtype=float)
    origin = np.asarray(origin, dtype=float)
    points = np.asarray(chart['points'], dtype=float)
    if (old.shape != (2,) or origin.shape != (2,) or points.ndim != 2 or
            points.shape[1] != 5 or len(points) < 2 or
            not all(np.isfinite(a).all() for a in (old, origin, points)) or
            not math.isfinite(datum) or not math.isfinite(chart['vertical_datum_m']) or
            np.any(np.diff(points[:, 0]) <= 0) or
            not np.allclose(np.linalg.norm(points[:, 3:5], axis=1), 1., atol=1e-5)):
        raise ValueError('Invalid chart or common frame')
    shift = old - origin
    points[:, 1:3] += shift
    result = copy.deepcopy(chart)
    result.update(horizontal_origin_epsg6404_m=origin.tolist(),
                  vertical_datum_m=float(datum), points=points.tolist())
    translation = [100*shift[0], -100*shift[1],
                   100*(chart['vertical_datum_m']-datum)]
    return result, translation


def uncovered_intervals(start, finish, intervals):
    """Expose connecting reaches, including put-in/runout; never bridge a gap."""
    if not all(math.isfinite(v) for v in (start, finish)) or finish <= start:
        raise ValueError('Invalid route extent')
    checked = []
    for a, b in intervals:
        if not all(math.isfinite(v) for v in (a, b)) or b <= a:
            raise ValueError('Invalid reach extent')
        if b > start and a < finish:
            checked.append((max(start, a), min(finish, b)))
    cursor, gaps = start, []
    for a, b in sorted(checked):
        if a > cursor:
            gaps.append([cursor, a])
        cursor = max(cursor, b)
    if cursor < finish:
        gaps.append([cursor, finish])
    return gaps


def build(source, windows, inputs, out):
    if out.exists():
        raise ValueError('Fresh output required; preserve earlier construction evidence')
    index = json.loads((windows/'index.json').read_text())
    profile_path = source/PROFILE
    # The window capture authenticated these same extracted profile bytes.
    # Absolute Windows capture paths are only identities, never read targets.
    identities = {str(k).replace('\\', '/').rsplit('/', 1)[-1]: v
                  for k, v in index['inputs_sha256'].items()}
    for path in (profile_path, CATALOG, source/'rapid_points_000.json'):
        if identities.get(path.name) != sha(path):
            raise ValueError('Source changed since registration: '+path.name)
    if index['source_rights'] != 'CC0 1.0 Universal':
        raise ValueError('Source rights require review')
    profile = read_profile(profile_path)
    xy = np.array([[r['easting'], r['northing']] for r in profile])
    mile = np.array([r['rm'] for r in profile])
    steps = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    if np.any(steps < .1) or np.any(steps > 40):
        raise ValueError('Duplicate or disconnected profile geometry')
    station = np.r_[0., np.cumsum(steps)]
    origin = np.floor(xy[0]/100)*100
    datum = float(math.floor(min(r['ws_nonincreasing'] for r in profile)/10)*10)
    tangent = np.gradient(xy, axis=0)
    lengths = np.linalg.norm(tangent, axis=1)
    if np.any(lengths < .1):
        raise ValueError('Degenerate progress tangent')
    tangent /= lengths[:, None]
    normal = np.column_stack([-tangent[:, 1], tangent[:, 0]])
    route = dict(schema='raftsim.curved_river_coordinate_map.v1',
        river_id='colorado_river', section_id='colorado_continuous_source_route',
        world_y_sign=-1, vertical_datum_m=datum,
        horizontal_origin_epsg6404_m=origin.tolist(),
        vertical_reference='NAD83(2011) ellipsoid heights',
        mapping_policy='Captured profile polyline, adaptively densified without moving survey vertices; downstream progress only, not a hydraulic grid or safe line.',
        points=native_progress_points(station, xy, normal, origin))
    points = json.loads((source/'rapid_points_000.json').read_text())
    river = next(r for r in json.loads(CATALOG.read_text())['rivers']
                 if r['river_id'] == 'colorado_river_grand_canyon_rowing')
    registrations = []
    for rapid in river['rapids']:
        matches = [f for f in points['features']
                   if f['attributes']['rapid'] == registered_label(rapid['name'])]
        if len(matches) != 1:
            raise ValueError('Ambiguous rapid identity: '+rapid['name'])
        point = matches[0]
        rm = float(point['attributes']['rm_label'])
        if not mile[0] <= rm <= mile[-1]:
            raise ValueError('Rapid outside captured route')
        geographic = np.array([point['geometry']['x'], point['geometry']['y']])
        nearest = np.min(np.linalg.norm(xy-geographic, axis=1))
        if nearest > 40:
            raise ValueError('Rapid point is not registered to the route')
        registrations.append(dict(name=rapid['name'], catalog_class=rapid['class'],
            catalog_mile=rapid['river_mile'], usgs_mile=rm,
            global_station_m=float(np.interp(rm, mile, station)),
            epsg6404_point_m=geographic.tolist(),
            world_xy_cm=((geographic-origin)*[100, -100]).tolist(),
            point_to_profile_sample_m=float(nearest),
            entry_exit_bounds_verified=False))
    reaches, charts, covered = [], {}, []
    for path in inputs:
        path = path.resolve()
        path.relative_to(ROOT)
        report = json.loads((path/'build_report.json').read_text())
        for name, digest in report['files_sha256'].items():
            dependency = (path/name).resolve()
            dependency.relative_to(path)
            if sha(dependency) != digest:
                raise ValueError('Changed reach dependency: '+name)
        definition_path = ROOT/report['source_profile']
        if report['name'] not in [r['name'] for r in registrations]:
            raise ValueError('Reach is absent from the river catalog')
        if report['name'] in [r['name'] for r in reaches]:
            raise ValueError('Duplicate reach; select one version explicitly')
        definition = json.loads(definition_path.read_text())
        # Validate the source window against the captured profile, rather than
        # trust a hand-edited source_station_range_m receipt.
        sample_lookup = {r['rm']: r for r in profile}
        for row in definition['samples']:
            if any(row[k] != sample_lookup.get(row['rm'], {}).get(k)
                   for k in ('easting', 'northing', 'ws_final', 'ws_nonincreasing')):
                raise ValueError('Reach profile no longer matches the full river')
        source_s = np.array([r['local_arc_station_m'] for r in definition['samples']])
        local_mile = np.array([r['rm'] for r in definition['samples']])
        reference = np.load(path/'reference.npz', allow_pickle=False)
        chart = json.loads((path/'coordinate_map.json').read_text())
        chart_source = reference['source_station']
        if (len(chart_source) != len(chart['points']) or
                not np.isfinite(chart_source).all() or np.any(np.diff(chart_source) <= 0) or
                chart_source[0] < source_s[0] or chart_source[-1] > source_s[-1]):
            raise ValueError('Reach chart has incomplete source registration')
        global_s = np.interp(np.interp(chart_source, source_s, local_mile), mile, station)
        rebased, translation = rebase_chart(chart, origin, datum)
        charts[path.name] = rebased
        interval = [float(global_s[0]), float(global_s[-1])]
        covered.append(interval)
        reaches.append(dict(name=report['name'], source_input=path.relative_to(ROOT).as_posix(),
            input_manifest_sha256=sha(path/'build_report.json'),
            chart_sha256=sha(path/'coordinate_map.json'),
            rebased_chart='charts/'+path.name+'.json',
            actor_translation_cm=translation, source_route_interval_m=interval,
            station_registration=[[p[0], float(s)] for p, s in zip(chart['points'], global_s)],
            registration_scope='Geographic extent only; not water, terrain, boat clearance or seam acceptance.'))
    # Retain the actual Hance chart, not the unused catalog-window replacement.
    # Its imagery-derived numerical axis differs from the USGS profile, so
    # register downstream progress by bounded spatial projection only. The
    # world positions, terrain, water and authored local feature stations stay
    # unchanged under the common-frame translation.
    hance_manifest = DATA/'terrain/hance_evidence_2021/hance_evidence_terrain_manifest.json'
    hance_meta = json.loads(hance_manifest.read_text())
    hance_path = ROOT/hance_meta['outputs']['runtime_coordinate_map']
    if sha(hance_path) != hance_meta['outputs']['runtime_coordinate_map_sha256']:
        raise ValueError('Existing Hance chart changed after terrain export')
    hance = json.loads(hance_path.read_text())
    hp = np.asarray(hance['points'], dtype=float)
    physical = hp[:, 1:3]+hance['horizontal_origin_epsg6404_m']
    hance_station = next(r['global_station_m'] for r in registrations if r['name'] == 'Hance')
    nearby = abs(station-hance_station) <= 5000
    hs, _, distance = project(physical, xy[nearby], station[nearby], chunk=64)
    if np.any(np.diff(hs) <= 0) or distance.max() > 250:
        raise ValueError('Hance cannot be monotonically registered to the same river reach')
    rebased, translation = rebase_chart(hance, origin, datum)
    charts['existing_hance'] = rebased
    interval = [float(hs[0]), float(hs[-1])]
    covered.append(interval)
    reaches.append(dict(name='Hance', source_chart=hance_path.relative_to(ROOT).as_posix(),
        terrain_manifest=hance_manifest.relative_to(ROOT).as_posix(),
        input_manifest_sha256=sha(hance_manifest), chart_sha256=sha(hance_path),
        rebased_chart='charts/existing_hance.json', actor_translation_cm=translation,
        source_route_interval_m=interval,
        station_registration=np.column_stack([hp[:, 0], hs]).tolist(),
        maximum_progress_axis_offset_m=float(distance.max()),
        registration_scope='Existing Hance geography retained. Progress-axis projection is not a bed, water, seam or difficulty approval.'))
    for reach in reaches:
        if 'source_chart' not in reach:
            reach['source_chart'] = reach['source_input']+'/coordinate_map.json'
    gaps = uncovered_intervals(float(station[0]), float(station[-1]), covered)
    result = dict(schema='raftsim.colorado_continuous_construction.v1',
        integration_policy='One uninterrupted geographic river; no level travel, raft resets, or gap skipping.',
        horizontal_crs='EPSG:6404', horizontal_origin_epsg6404_m=origin.tolist(),
        vertical_reference='NAD83(2011) ellipsoid heights', vertical_datum_m=datum,
        source_profile_sha256=sha(profile_path), source_points_sha256=sha(source/'rapid_points_000.json'),
        source_doi=index['source_doi'], source_rights=index['source_rights'],
        route_coordinate_map='route_coordinate_map.json',
        survey_mile_range=[float(mile[0]), float(mile[-1])],
        route_length_m=float(station[-1]),
        extent_scope='Complete captured profile envelope. Exact playable Pearce Ferry takeout must be registered separately.',
        rapid_registrations=registrations, source_reaches=reaches,
        missing_source_route_intervals_m=gaps,
        missing_source_route_length_m=sum(b-a for a, b in gaps),
        runtime_ready=False,
        blockers=['Connecting terrain and water are not supplied by rapid-only crops.',
                  'Local hydraulic charts require source-aware handoff, not concatenated station axes.',
                  'Rapid and connecting reaches need matched render/collision/bed and wet seam checks.',
                  'Whole-route native descents, rescue continuity and packaged performance remain required.'])
    out.mkdir(parents=True)
    (out/'charts').mkdir()
    for name, value in [('manifest.json', result), ('route_coordinate_map.json', route),
                        *[('charts/'+key+'.json', value) for key, value in charts.items()]]:
        (out/name).write_text(json.dumps(value, indent=1, allow_nan=False)+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    p.add_argument('--windows', type=Path, default=DATA/'catalog_construction_windows_2026_10_v1')
    p.add_argument('--input', type=Path, action='append', required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    result = build(args.source, args.windows, args.input, args.out)
    print(json.dumps({k: result[k] for k in ('route_length_m', 'missing_source_route_length_m', 'runtime_ready')}, indent=2))
