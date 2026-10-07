"""Read-only native test of continuous-route and reach-frame registration.

No map mutation, synthetic hull, simulated descent, water or FPS acceptance.
Run with RAFTSIM_COLORADO_ASSEMBLY and RAFTSIM_COLORADO_REGISTRATION_REPORT.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import time

import unreal

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xyz(value):
    assert value is not None
    values = [value.x, value.y, value.z]
    assert all(math.isfinite(v) for v in values)
    return values


def main():
    directory = (ROOT/os.environ['RAFTSIM_COLORADO_ASSEMBLY']).resolve()
    report_path = (ROOT/os.environ['RAFTSIM_COLORADO_REGISTRATION_REPORT']).resolve()
    directory.relative_to(ROOT)
    report_path.relative_to(ROOT/'tmp')
    assert not report_path.exists(), 'Fresh report required'
    manifest_path = directory/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['schema'] == 'raftsim.colorado_continuous_construction.v1'
    route_path = directory/manifest['route_coordinate_map']
    route = json.loads(route_path.read_text())
    protected = {p: digest(p) for p in (manifest_path, route_path)}
    water = unreal.RaftSimWaterRuntimeAdapter()
    assert water.configure_river_coordinate_map(str(route_path))
    points = route['points']
    stations = {points[0][0], points[-1][0]}
    stations.update(p[0] for p in points[::100])
    stations.update(r['global_station_m'] for r in manifest['rapid_registrations'])
    errors, count = [], 0
    start = time.perf_counter()
    # The progress axis is not a navigable-line claim. Test only a raft-width
    # offset, plus exact endpoints, rather than asserting a 512 m safe channel.
    for station in sorted(stations):
        for side in (-3., 0., 3.):
            position = water.river_to_world_position(unreal.Vector2D(station, side), 1000.)
            xyz(position)
            result = water.world_to_river_coordinates(position)
            assert result is not None
            coordinate, tangent, normal = result
            xyz(tangent)
            xyz(normal)
            error = math.hypot(coordinate.x-station, coordinate.y-side)
            assert math.isfinite(error)
            errors.append(error)
            count += 1
    route_seconds = time.perf_counter()-start
    results = []
    for reach in manifest['source_reaches']:
        source = ROOT/reach['source_chart']
        rebased = directory/reach['rebased_chart']
        assert digest(source) == reach['chart_sha256']
        protected[source], protected[rebased] = digest(source), digest(rebased)
        original, relocated = unreal.RaftSimWaterRuntimeAdapter(), unreal.RaftSimWaterRuntimeAdapter()
        assert original.configure_river_coordinate_map(str(source))
        assert relocated.configure_river_coordinate_map(str(rebased))
        mapping = json.loads(source.read_text())
        delta = reach['actor_translation_cm']
        sample_points = mapping['points'][::20]+[mapping['points'][-1]]
        maximum, probes = 0., 0
        for point in sample_points:
            for side in (-20., 0., 20.):
                coordinates = unreal.Vector2D(point[0], side)
                a = xyz(original.river_to_world_position(coordinates, 1000.))
                b = xyz(relocated.river_to_world_position(coordinates, 1000.))
                maximum = max(maximum, math.sqrt(sum((a[i]+delta[i]-b[i])**2 for i in range(3))))
                probes += 1
        results.append(dict(name=reach['name'], probes=probes,
                            maximum_relocation_error_cm=maximum, passed=maximum < .01))
    assert all(digest(path) == expected for path, expected in protected.items())
    result = dict(schema='raftsim.colorado_continuous_native_registration.v1',
        passed=max(errors) < .1 and all(r['passed'] for r in results),
        manifest_sha256=protected[manifest_path], route_sha256=protected[route_path],
        route_point_count=len(points), route_probes=count,
        route_roundtrip_max_error_m=max(errors), native_coordinate_query_wall_seconds=route_seconds,
        reach_tests=results, saved_assets=False, connected_water_validated=False,
        full_hull_traversal_validated=False, rendered_or_packaged_fps=None)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2)+'\n')
    unreal.log('Continuous registration report: '+str(report_path))
    assert result['passed'], 'Native coordinate registration failed; do not assemble maps'


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
