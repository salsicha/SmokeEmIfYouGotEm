"""Captured three-arm topology for the continuous Futaleufu channel builder.

The playable path arrives on Rio Azul; the upstream mainstem is a separate
hydraulic inlet, not a continuation of the tributary's discharge. This artifact
adds that source-captured arm without moving the junction or inventing a flow.
It is construction input, not a solved or engine-installed hydraulic domain.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from build_futaleufu_continuous_route import mainstem_join, vertices
from build_futaleufu_corridor_sources import ROOT, BASE, CORRIDOR, ROUTE, sha
from geo_frames import tm_forward, utm


def upstream_arm(main_xy, junction, minimum_length_m):
    points = vertices(main_xy)
    if (not isinstance(junction, (int, np.integer)) or not 0 < junction < len(points)-1
            or not np.isfinite(minimum_length_m) or minimum_length_m <= 0):
        raise ValueError('Interior junction and positive inlet-arm length required')
    lengths = np.linalg.norm(np.diff(points[:junction+1], axis=0), axis=1)
    backward = np.cumsum(lengths[::-1])
    count = int(np.searchsorted(backward, minimum_length_m))+1
    if count > junction:
        raise ValueError('Captured mainstem does not cover requested upstream arm')
    start = junction-count
    # Retain the preceding captured vertex instead of making a fabricated
    # measurement at an interpolated minimum-length cutoff.
    return start, points[start:junction+1].copy()


def flow_budget(rio_azul_m3_s, upstream_mainstem_m3_s):
    """Explicit caller-supplied branch flows; never infer either from the other."""
    if (isinstance(rio_azul_m3_s, (bool, np.bool_)) or
            isinstance(upstream_mainstem_m3_s, (bool, np.bool_))):
        raise ValueError('Two positive finite branch flows required')
    try:
        values = np.asarray([rio_azul_m3_s, upstream_mainstem_m3_s], dtype=float)
    except (ValueError, TypeError) as exc:
        raise ValueError('Two positive finite branch flows required') from exc
    if values.shape != (2,) or not np.isfinite(values).all() or np.any(values <= 0):
        raise ValueError('Two positive finite branch flows required')
    total = float(values.sum())
    if not np.isfinite(total):
        raise ValueError('Finite downstream flow required')
    return dict(rio_azul_m3_s=float(values[0]), upstream_mainstem_m3_s=float(values[1]),
                downstream_mainstem_m3_s=total)


def build(source_window, output, minimum_inlet_length_m=400.):
    source_window, output = Path(source_window).resolve(), Path(output).resolve()
    output.relative_to(ROOT)
    if output.exists():
        raise ValueError('Fresh confluence network output required')
    files = [CORRIDOR/'hydrography/route_stationing.json',
             BASE/'futaleufu_sources_2026_09/osm/futaleufu_centreline.json',
             ROUTE, ROUTE.parent/'manifest.json', source_window/'manifest.json']
    pins = {p: sha(p) for p in files}
    route, main, chart, info, source = [json.loads(p.read_text()) for p in files]
    if source.get('schema') != 'raftsim.futaleufu_continuous_sources.v1':
        raise ValueError('Verified continuous source window required')
    for relative, digest in source['sources_sha256'].items():
        path = (ROOT/relative).resolve()
        path.relative_to(ROOT)
        if sha(path) != digest:
            raise ValueError('Changed source-window input')
        pins[path] = digest
    if source['sources_sha256'].get(ROUTE.relative_to(ROOT).as_posix()) != sha(ROUTE):
        raise ValueError('Source window must bind the current route chart')
    if (chart['horizontal_crs'] != 'EPSG:32718 WGS 84 / UTM zone 18S' or
            source['grid']['epsg'] != 32718):
        raise ValueError('Shared native UTM18S frame required')
    route_ll = vertices([[p['lon'], p['lat']] for p in route['samples']])
    main_ll = vertices(np.asarray(main['centreline_lon_lat_chain'])[:, :2])
    join, main_join, end = mainstem_join(route_ll, main_ll)
    expected = info['confluence']
    if (join != expected['source_route_vertex'] or main_join != expected['source_mainstem_vertex']
            or not np.array_equal(route_ll[join], expected['lon_lat'])
            or info['coordinate_map_sha256'] != sha(ROUTE)):
        raise ValueError('Captured confluence differs from continuous chart')
    project = lambda ll: np.column_stack(tm_forward(ll[:, 0], ll[:, 1], utm(18, south=True)))
    route_xy, main_xy = project(route_ll), project(main_ll)
    start, inlet = upstream_arm(main_xy, main_join, minimum_inlet_length_m)
    arms = dict(rio_azul=route_xy[:join+1], upstream_mainstem=inlet,
                downstream_mainstem=route_xy[join:])
    if not (np.array_equal(arms['rio_azul'][-1], inlet[-1]) and
            np.array_equal(inlet[-1], arms['downstream_mainstem'][0])):
        raise ValueError('All three arms must share exactly one captured junction')
    t = source['grid']['transform']; height, width = source['grid']['shape']
    if t[0] != 10 or t[4] != -10 or t[1] != 0 or t[3] != 0:
        raise ValueError('Native north-up ten-metre source window required')
    xmin, xmax, ymin, ymax = t[2], t[2]+10*width, t[5]-10*height, t[5]
    branches = {}
    for name, xy in arms.items():
        margin = float(np.min(np.column_stack([xy[:, 0]-xmin, xmax-xy[:, 0],
                                               xy[:, 1]-ymin, ymax-xy[:, 1]])))
        if margin < 150.:
            raise ValueError(f'Source window lacks 150 m bank context for {name}')
        stations = np.r_[0., np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
        branches[name] = dict(direction='toward_junction' if name != 'downstream_mainstem' else 'away_from_junction',
            points_station_easting_northing_m=np.column_stack([stations, xy]).tolist(),
            length_m=float(stations[-1]), source_vertex_count=len(xy), source_window_margin_m=margin)
    if not all(sha(p) == digest for p, digest in pins.items()):
        raise ValueError('Source changed during confluence construction')
    report = dict(schema='raftsim.futaleufu_confluence_network.v1', horizontal_crs=chart['horizontal_crs'],
        sources_sha256={p.relative_to(ROOT).as_posix(): digest for p, digest in pins.items()},
        junction=dict(lon_lat=expected['lon_lat'], easting_northing_m=inlet[-1].tolist(),
                      playable_route_station_m=expected['route_station_m']),
        upstream_mainstem_source_vertex_interval=[start, main_join],
        downstream_mainstem_source_vertex_interval=[main_join, end], branches=branches,
        inlet_arm_minimum_requested_m=minimum_inlet_length_m,
        flow=dict(rio_azul_m3_s=None, upstream_mainstem_m3_s=None, downstream_mainstem_m3_s=None,
                  conservation='Q_downstream = Q_rio_azul + Q_upstream_mainstem',
                  authority='No local discharge measurement supplied. Inferred construction flows must be explicit; basin-outlet statistics and water rights are not local measurements.'),
        rights='OpenStreetMap contributors, ODbL-1.0; retain attribution and database obligations.',
        limitations=['Captured source vertices only; no bank, bed or bathymetric survey claimed.',
            '150 m source-window margin proves rectangular coverage, not valid optical water or cloud-free pixels.',
            'Minimum upstream-arm length is an engineering domain choice, not a documented rapid boundary.',
            'Geometric three-arm join does not yet establish stage continuity, flux conservation in a solver, or boat passage.'],
        hydraulic_domain_validated=False, installed_in_engine=False)
    output.mkdir(parents=True)
    (output/'network.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--minimum-inlet-length-m', type=float, default=400.)
    args = parser.parse_args()
    result = build(args.sources, args.out, args.minimum_inlet_length_m)
    print(json.dumps({name: {k: branch[k] for k in ('length_m', 'source_vertex_count', 'source_window_margin_m')}
                      for name, branch in result['branches'].items()}))
