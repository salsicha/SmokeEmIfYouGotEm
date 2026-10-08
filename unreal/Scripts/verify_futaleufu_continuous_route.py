"""Read-only native coordinate checks, not water, boat or map acceptance."""
import hashlib
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    import unreal
    request = json.loads((ROOT/os.environ['RAFTSIM_ROUTE_CHECK_REQUEST']).read_text())
    chart_path = (ROOT/request['chart']).resolve()
    chart_path.relative_to(ROOT)
    manifest_path = chart_path.with_name('manifest.json')
    output = (ROOT/request['output']).resolve()
    output.relative_to(ROOT/'tmp')
    if output.exists():
        raise ValueError('Fresh result required')
    chart = json.loads(chart_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    protected = {chart_path: request['chart_sha256'], manifest_path: request['manifest_sha256']}
    for name, digest in manifest['sources_sha256'].items():
        source = (ROOT/name).resolve()
        source.relative_to(ROOT)
        protected[source] = digest
    if sha(chart_path) != manifest['coordinate_map_sha256'] or not all(sha(p) == h for p,h in protected.items()):
        raise ValueError('Changed source chart')
    adapter = unreal.RaftSimWaterRuntimeAdapter()
    if not adapter.configure_river_coordinate_map(str(chart_path)):
        raise ValueError('Native route load refused')
    # Inspect each captured corner and a 25 m longitudinal lattice. Narrow
    # lateral checks exercise boat-scale registration, not full wet coverage.
    stations = sorted(set(manifest['source_to_projected_stations_m'] +
        list(range(0, int(manifest['projected_route_length_m'])+1, 25))))
    failures = []
    previous_query = None
    maximum = 0.
    count = 0
    for reverse in (False, True):
        for station in reversed(stations) if reverse else stations:
            for lateral in (-2.5, 0., 2.5):
                count += 1
                position = adapter.river_to_world_position(unreal.Vector2D(station,lateral),1000.)
                result = adapter.world_to_river_coordinates(position) if position is not None else None
                if result is None:
                    failures.append(dict(station=station,lateral=lateral,reverse=reverse,error='Native query refused'))
                    continue
                coordinate, tangent, left = result
                error = math.hypot(coordinate.x-station,coordinate.y-lateral)
                if math.isfinite(error): maximum=max(maximum,error)
                else: error=None
                if error is None or error > .05:
                    cold = unreal.RaftSimWaterRuntimeAdapter()
                    if not cold.configure_river_coordinate_map(str(chart_path)):
                        raise ValueError('Cold native control refused chart')
                    cold_result = cold.world_to_river_coordinates(position)
                    cold_error = (math.hypot(cold_result[0].x-station,cold_result[0].y-lateral)
                        if cold_result is not None else None)
                    failures.append(dict(station=station,lateral=lateral,reverse=reverse,error_m=error,
                        returned=[coordinate.x,coordinate.y],previous_query=previous_query,
                        cold_control_error_m=cold_error))
                    del cold
                previous_query = [station,lateral]
    if not all(sha(p) == h for p,h in protected.items()):
        raise ValueError('Inputs changed during native check')
    # A straight dense chart has no bend, terrain or ambiguous inverse. It
    # isolates a segment-count cache window from the real confluence shape.
    dense_path = output.with_name('dense-cache-control.json')
    with dense_path.open('x') as stream:
        json.dump(dict(schema='raftsim.curved_river_coordinate_map.v1',world_y_sign=-1,
            vertical_datum_m=150,points=[[i*.25,i*.25,0,0,1] for i in range(201)]),stream)
    dense = unreal.RaftSimWaterRuntimeAdapter()
    if not dense.configure_river_coordinate_map(str(dense_path)):
        raise ValueError('Dense straight control refused')
    seed = dense.river_to_world_position(unreal.Vector2D(20,0),1000.)
    target = dense.river_to_world_position(unreal.Vector2D(26,0),1000.)
    dense.world_to_river_coordinates(seed)
    warm = dense.world_to_river_coordinates(target)
    dense.configure_river_coordinate_map(str(dense_path))
    cold = dense.world_to_river_coordinates(target)
    control = dict(seed_station_m=20,target_station_m=26,sample_spacing_m=.25,
        query_world_distance_m=6,warm_returned_station_m=warm[0].x,cold_returned_station_m=cold[0].x,
        passed=abs(warm[0].x-26)<.01 and abs(cold[0].x-26)<.01)
    report = dict(schema='raftsim.futaleufu_native_route_check.v1', passed=not failures and control['passed'],
        chart=request['chart'],chart_sha256=sha(chart_path),manifest_sha256=sha(manifest_path),
        query_count=count,stations=len(stations),lateral_samples_m=[-2.5,0,2.5],
        traversal_orders=['forward','reverse'],maximum_station_lateral_error_m=maximum,
        failures=failures,dense_cache_control=control, scope='Native geographic roundtrips only. No terrain, full wet-width, hydraulic, hull-motion, rendering or performance acceptance.',
        saved_maps=False,engine_motion_accepted=False,performance_accepted=False)
    with output.open('x') as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
    unreal.log('Futaleufu native route coordinate check: '+str(report['passed']))
    del adapter,dense
    unreal.SystemLibrary.collect_garbage()


if __name__ == '__main__':
    import unreal
    try: main()
    finally: unreal.SystemLibrary.quit_editor()
