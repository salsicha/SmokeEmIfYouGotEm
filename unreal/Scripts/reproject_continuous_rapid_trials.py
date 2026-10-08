"""Prepare trials through the production coordinate adapter, not station offsets.

Run with RAFTSIM_TRIAL_REPROJECTION pointing at a fresh JSON request. This is
coordinate validation only: no map mutation, boat simulation or FPS acceptance.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(name):
    path = (ROOT / name).resolve()
    path.relative_to(ROOT)
    return path


def interpolate(route, station):
    for (a, x), (b, y) in zip(route, route[1:]):
        if a <= station <= b:
            return x + (y - x) * (station - a) / (b - a)
    raise ValueError('Event outside authored route')


def main():
    request_path = local(os.environ['RAFTSIM_TRIAL_REPROJECTION'])
    request = json.loads(request_path.read_text(encoding='utf-8-sig'))
    output = local(request['output'])
    output.relative_to(ROOT / 'tmp')
    assert not output.exists(), 'Fresh evidence directory required'
    paths = [request_path] + [local(request[k]) for k in ('plan', 'source_chart', 'target_chart')]
    protected = {p: digest(p) for p in paths}
    source_json, target_json = [json.loads(p.read_text()) for p in paths[2:]]
    for key in ('schema', 'world_y_sign', 'horizontal_origin_epsg6404_m', 'vertical_datum_m'):
        assert key in source_json and source_json[key] == target_json[key], 'Different geographic frames'
    assert source_json['schema'] == 'raftsim.curved_river_coordinate_map.v1'
    source, target = unreal.RaftSimWaterRuntimeAdapter(), unreal.RaftSimWaterRuntimeAdapter()
    assert source.configure_river_coordinate_map(str(paths[2]))
    assert target.configure_river_coordinate_map(str(paths[3]))
    original = json.loads(paths[1].read_text(encoding='utf-8-sig'))
    assert len(original) == 1
    plan = copy.deepcopy(original[0])
    plan.update({k: request[k] for k in ('river', 'map', 'scenario')})
    plan['source'] = request['runtime_manifest']
    plan['calibration_scope'] = ('Native source-world-target reprojection of retained approaches; '
        'event gates follow the preferred line, not surveyed rapid boundaries. '
        'No claim of identical hydraulics, whole-river acceptance or measured class.')
    plan['trials'] = []
    records, excluded, errors = [], [], []

    def convert(station, lateral):
        assert source_json['points'][0][0] <= station <= source_json['points'][-1][0]
        world = source.river_to_world_position(unreal.Vector2D(station, lateral), 1000.)
        assert world is not None
        native = target.world_to_river_coordinates(world)
        assert native is not None
        coordinate = native[0]
        assert all(math.isfinite(v) for v in (coordinate.x, coordinate.y))
        assert request['coverage_m'][0] <= coordinate.x <= request['coverage_m'][1]
        back = target.river_to_world_position(coordinate, 1000.)
        assert back is not None
        error = math.hypot(back.x-world.x, back.y-world.y) / 100.
        assert error < .01, 'Native round trip exceeds one centimetre'
        errors.append(error)
        return [coordinate.x, coordinate.y], world, native[1]

    stations = {'start_m', 'finish_m', 'control_m', 'steering_start_m', 'steering_end_m',
                'mistake_trigger_m', 'rescue_drill_station_m'}
    for original_trial in original[0]['trials']:
        if any(key.startswith('heading_') for key in original_trial):
            excluded.append(dict(id=original_trial['id'], reason='Station-varying heading hold needs explicit new calibration'))
            continue
        trial = copy.deepcopy(original_trial)
        assert trial.get('strict_route') is True, 'No adaptive route fallback'
        route = trial['route_laterals']
        assert len(route) >= 2 and route[0][0] == trial['start_m'] and route[-1][0] == trial['finish_m']
        assert all(math.isfinite(v) for pair in route for v in pair)
        assert all(a[0] < b[0] for a, b in zip(route, route[1:]))
        # Explicit field allowlist prevents silently leaving a new event in the old frame.
        for key in trial:
            if key.endswith('_m') and key not in stations | {'lane_m', 'lookahead_m'}:
                raise ValueError('Unreviewed distance/event field: ' + key)
        assert 'steering_blackouts' not in trial, 'Blackout intervals need explicit conversion'
        new_route = []
        for index, ((a, x), (b, y)) in enumerate(zip(route, route[1:])):
            count = math.ceil((b-a)/2.)
            for n in range(count + 1):
                if index and n == 0:
                    continue
                s = a + (b-a)*n/count
                new_route.append(convert(s, x+(y-x)*n/count)[0])
        assert all(a[0] < b[0] for a, b in zip(new_route, new_route[1:])), 'Projected route folds'
        # The harness interpolates target station/lateral pairs. Verify its
        # mid-segment line still follows the original physical approach.
        route_error = 0.
        for (a, x), (b, y) in zip(new_route, new_route[1:]):
            middle = target.river_to_world_position(unreal.Vector2D((a+b)/2., (x+y)/2.), 1000.)
            old = source.world_to_river_coordinates(middle)
            assert old is not None
            old_coord = old[0]
            if trial['start_m'] <= old_coord.x <= trial['finish_m']:
                expected = source.river_to_world_position(unreal.Vector2D(old_coord.x, interpolate(route, old_coord.x)), 1000.)
                route_error = max(route_error, math.hypot(middle.x-expected.x, middle.y-expected.y)/100.)
        assert route_error < .02, 'Interpolated route differs by more than two centimetres'
        for key in stations & trial.keys():
            s = trial[key]
            trial[key] = convert(s, interpolate(route, s))[0][0]
        for gate in trial['gates']:
            s = gate['station_m']
            gate['station_m'] = convert(s, interpolate(route, s))[0][0]
        _, world, tangent = convert(route[0][0], route[0][1])
        source_tangent = source.world_to_river_coordinates(world)[1]
        heading_delta = math.degrees(math.atan2(source_tangent.y, source_tangent.x) - math.atan2(tangent.y, tangent.x))
        trial['initial_heading_deg'] = (trial.get('initial_heading_deg', 0.)+heading_delta+180.)%360.-180.
        trial['route_laterals'] = new_route
        trial['lane_m'] = new_route[0][1]
        records.append(dict(id=trial['id'], start_m=trial['start_m'], finish_m=trial['finish_m'],
                            source_start=route[0], target_start=new_route[0],
                            maximum_interpolated_line_error_m=route_error, heading_frame_delta_deg=heading_delta))
        plan['trials'].append(trial)
    assert plan['trials'], 'No eligible trials'
    assert all(digest(path) == expected for path, expected in protected.items()), 'Inputs changed'
    output.mkdir(parents=True)
    (output/'plan.json').write_text(json.dumps([plan], indent=2, allow_nan=False)+'\n')
    report = dict(schema='raftsim.native_trial_reprojection.v1', passed=True,
        inputs={str(p.relative_to(ROOT)): h for p, h in protected.items()},
        native_roundtrip_max_error_m=max(errors), native_queries=len(errors), trials=records,
        excluded=excluded, map_mutated=False, boat_trials_run=False, performance_accepted=False)
    (output/'receipt.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    unreal.log('Native trial reprojection: ' + str(output/'receipt.json'))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
