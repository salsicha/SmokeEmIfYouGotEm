"""Native read-only comparison of the staged South Fork runtime dependency tree.

This validates actual native route/initial-field loading from absolute staged
paths. It is NOT packaged executable, evolved-water, visual or FPS acceptance.
"""
import json
import math
import os
from pathlib import Path
import sys
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/scripts'))
from package_runtime_bundle import verify_staged, sha
from verify_active_south_fork_stage import selected_bundle


def main():
    bundle = selected_bundle(ROOT)
    staged = Path(os.environ['RAFTSIM_RUNTIME_BUNDLE_ROOT']).resolve()
    if staged == ROOT:
        raise ValueError('An actual staged tree, not the source root, is required')
    report = Path(os.environ['RAFTSIM_RUNTIME_BUNDLE_REPORT']).resolve()
    if report.exists() or not report.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh local verification report required')
    audit = verify_staged(bundle, staged)
    manifest = json.loads((bundle/'manifest.json').read_text())
    entries = manifest['entrypoints']
    routes = []
    # Staged paths load first in a fresh engine process. The native shared-atlas
    # cache also keys by absolute path, not just identical content hashes.
    for data_root in (staged, ROOT):
        route = unreal.RaftSimWaterRuntimeAdapter()
        assert route.configure_river_coordinate_map(str(data_root/entries['route_coordinate_map']))
        routes.append(route)
    route_data = json.loads((staged/entries['route_coordinate_map']).read_text())
    finish = route_data['points'][-1][0]
    assert finish > 30000, 'Full South Fork route required, not a rapid-only fixture'
    route_error = 0.
    for index in range(2001):
        station = finish*index/2000
        left, right = [route.river_to_world_position(unreal.Vector2D(station,0),227.) for route in routes]
        assert isinstance(left,unreal.Vector) and isinstance(right,unreal.Vector)
        route_error = max(route_error, math.dist([left.x,left.y,left.z],[right.x,right.y,right.z]))
    assert route_error == 0.
    start = routes[0].river_to_world_position(unreal.Vector2D(120.,0),220.)
    stream = json.loads((staged/entries['streaming_manifest']).read_text())
    window, = [row for row in stream['windows'] if row['cooked_fields_manifest'] == entries['initial_fields_manifest']]
    px,py = start.x/100.,-start.y/100.
    candidates=[]
    for x0,y0,x1,y1 in window['valid_live_center_bounds_m']:
        cx,cy = min(max(px,x0),x1),min(max(py,y0),y1)
        candidates.append(((cx-px)**2+(cy-py)**2,cx,cy))
    _,cx,cy = min(candidates)
    waters=[]
    for data_root in (staged,ROOT):
        water=unreal.RaftSimWaterRuntimeAdapter()
        config=unreal.RaftSimWaterRuntimeConfig()
        config.require_accepted_report_manifest=False
        config.enable_deterministic_capture=False
        water.configure(config)
        assert water.configure_river_coordinate_map(str(data_root/entries['hydraulic_coordinate_map']))
        fields=(data_root/entries['initial_fields_manifest']).parent
        assert water.configure_moving_river_window(str(fields),'median_runnable',
            unreal.Vector2D(cx,cy),unreal.Vector2D(224,224),.035)
        waters.append(water)
    maximum_error=0.;wet=0;count=0
    for dy in range(-100,101,4):
        for dx in range(-100,101,4):
            point=unreal.Vector((cx+dx)*100,-(cy+dy)*100,0)
            a,b=[water.sample_water_at_world_position(point) for water in waters]
            assert a is not None and b is not None
            def values(sample):
                return [sample.bed_height_meters,sample.depth_meters,sample.surface_height_meters,
                        sample.velocity_meters_per_second.x,sample.velocity_meters_per_second.y]
            va,vb=values(a),values(b)
            assert all(math.isfinite(value) for value in va+vb)
            assert a.wet == b.wet
            maximum_error=max(maximum_error,max(abs(x-y) for x,y in zip(va,vb)))
            wet+=int(a.wet);count+=1
    assert maximum_error == 0. and wet > 0
    result=dict(audit, native_route_queries=2001,native_route_maximum_error_cm=route_error,
        native_water_queries=count,native_water_wet_queries=wet,native_field_maximum_error=maximum_error,
        native_water_center_m=[cx,cy],absolute_staged_paths_verified=True,
        editor_process=True,solver_steps_run=0,saved_assets=False,
        native_route_and_initial_fields_verified=True,
        source_stream_sha256=sha(ROOT/entries['streaming_manifest']),
        selected_bundle=bundle.relative_to(ROOT).as_posix())
    report.write_text(json.dumps(result,indent=2)+'\n')
    unreal.log('Native staged runtime bundle verified: '+str(report))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
