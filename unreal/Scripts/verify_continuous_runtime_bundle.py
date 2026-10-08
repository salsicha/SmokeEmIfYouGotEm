"""Native staged/source parity for curved runtime bundles; no scene saves.

This is native route, window stepping and handoff verification, not packaged
gameplay/rendering/FPS acceptance. Absolute staged paths prevent repo fallback.
"""
import json
import gc
import math
import os
from pathlib import Path
import sys
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/scripts'))
from package_runtime_bundle import verify_staged, sha


def main():
    bundle = (ROOT/os.environ['RAFTSIM_CONTINUOUS_BUNDLE']).resolve()
    stage = (ROOT/os.environ['RAFTSIM_CONTINUOUS_STAGE']).resolve()
    report = (ROOT/os.environ['RAFTSIM_CONTINUOUS_VERIFY_REPORT']).resolve()
    if stage == ROOT or report.exists() or not report.is_relative_to(ROOT/'tmp'):
        raise ValueError('Separate staged tree and fresh tmp report required')
    audit = verify_staged(bundle, stage)
    manifest = json.loads((bundle/'manifest.json').read_text())
    entries = manifest['entrypoints']
    streaming = json.loads((stage/entries['streaming_manifest']).read_text())
    assert streaming['schema'] == 'raftsim.south_fork.moving_water_streaming.v1'
    routes = []
    for base in (stage, ROOT):
        route = unreal.RaftSimWaterRuntimeAdapter()
        assert route.configure_river_coordinate_map(str(base/entries['route_coordinate_map']))
        routes.append(route)
    chart = json.loads((stage/entries['route_coordinate_map']).read_text())
    first, last = chart['points'][0][0], chart['points'][-1][0]
    max_route_error = 0.
    for index in range(1001):
        station = first+(last-first)*index/1000
        a,b = [r.river_to_world_position(unreal.Vector2D(station,0),0.) for r in routes]
        max_route_error = max(max_route_error, math.dist((a.x,a.y,a.z),(b.x,b.y,b.z)))
    assert max_route_error == 0.
    names = {entries['initial_fields_manifest'], streaming['full_reach_transit_seed']['cooked_fields_manifest']}
    names.update(row['cooked_fields_manifest'] for row in streaming['windows'])
    proofs = []
    for name in sorted(names):
        fields = json.loads((stage/name).read_text()); grid = fields['grid']
        assert (grid['nx']-1)*grid['dx_m'] >= 480 and (grid['ny']-1)*grid['dy_m'] >= 80
        cx = grid['origin_x_m']+(grid['nx']-1)*grid['dx_m']*.5
        cy = grid['origin_y_m']+(grid['ny']-1)*grid['dy_m']*.5
        for band in fields['bands']:
            waters = []
            for base in (stage, ROOT):
                water = unreal.RaftSimWaterRuntimeAdapter()
                config = unreal.RaftSimWaterRuntimeConfig()
                config.require_accepted_report_manifest = False
                config.enable_deterministic_capture = False
                water.configure(config)
                assert water.configure_river_coordinate_map(str(base/entries['hydraulic_coordinate_map']))
                assert water.configure_moving_river_window(str((base/name).parent), band['band_id'],
                    unreal.Vector2D(cx,cy), unreal.Vector2D(240,80), band.get('manning_n',.041))
                waters.append(water)
            queries = wet = 0
            max_error = 0.
            for phase in ('initial', 'stepped', 'handoff'):
                if phase == 'stepped':
                    for _ in range(24):
                        for water in waters:
                            assert water.step_water(1./60.)
                if phase == 'handoff':
                    for water,base in zip(waters,(stage,ROOT)):
                        assert water.configure_moving_river_window(str((base/name).parent),band['band_id'],
                            unreal.Vector2D(cx+40,cy),unreal.Vector2D(240,80),band.get('manning_n',.041))
                for ds in range(-60,61,10):
                    for dl in range(-30,31,10):
                        p = waters[0].river_to_world_position(unreal.Vector2D(cx+ds,cy+dl),0.)
                        a,b = [water.sample_water_at_world_position(p) for water in waters]
                        assert a is not None and b is not None and a.wet == b.wet
                        def values(s):
                            return (s.bed_height_meters,s.depth_meters,s.surface_height_meters,
                                    s.velocity_meters_per_second.x,s.velocity_meters_per_second.y)
                        av,bv = values(a),values(b)
                        assert all(math.isfinite(v) for v in av+bv)
                        max_error = max(max_error,max(abs(x-y) for x,y in zip(av,bv)))
                        wet += int(a.wet); queries += 1
            assert max_error == 0. and wet > 0
            proofs.append(dict(manifest=name,band=band['band_id'],queries=queries,wet_queries=wet,
                maximum_error=max_error,solver_steps_each=24,overlapping_handoffs_each=1))
            # Release harness-owned native solver windows while their module
            # is alive, rather than leaving cleanup to editor finalization.
            for water in waters:
                water.configure(unreal.RaftSimWaterRuntimeConfig())
            waters.clear()
    for route in routes:
        route.configure(unreal.RaftSimWaterRuntimeConfig())
    routes.clear()
    result = dict(audit, native_route_queries=1001, native_route_maximum_error_cm=max_route_error,
        native_field_checks=proofs, absolute_staged_paths_verified=True, editor_process=True,
        saved_assets=False, rendered_gameplay_verified=False, packaged_execution_verified=False,
        bundle_manifest_sha256=sha(bundle/'manifest.json'))
    with report.open('x') as stream:
        json.dump(result,stream,indent=2)
    unreal.log('RAFTSIM_CONTINUOUS_STAGED_RUNTIME_VERIFIED '+str(report))


if __name__ == '__main__':
    try:
        main()
    finally:
        gc.collect()
        unreal.SystemLibrary.collect_garbage()
        unreal.SystemLibrary.quit_editor()
