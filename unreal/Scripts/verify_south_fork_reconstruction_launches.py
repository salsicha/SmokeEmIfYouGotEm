"""Read-only native launch preflight for a source-matched South Fork revision.

Checks every saved catalog start against the proposed full-river fields. It
does not enable the preview, save a level, or claim traversal/raft acceptance.
The independent candidate selection here is not the game-mode launch selector.
"""
import json
import math
import os
from pathlib import Path
import sys

import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from prepare_south_fork_joint_preview import Dependencies, require, verify_audits
from package_runtime_bundle import Closure

LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
CONTRACTS = ROOT / ('physics/data/real_world/south_fork_american_chili_bar/'
    'reconstruction_2026_09/full_reach/playable_route/session_contracts.json')


def candidates(stream, x, y):
    """Admissible crop centers retaining the unchanged eight-metre margin."""
    result = set()
    require(stream['live_window_extent_m'] == [224., 224.], 'Unexpected live extent')
    require(math.isfinite(x) and math.isfinite(y), 'Non-finite route point')
    for window in stream['windows']:
        for x0, y0, x1, y1 in window['valid_live_center_bounds_m']:
            require(all(math.isfinite(v) for v in (x0, y0, x1, y1)) and
                    x0 <= x1 and y0 <= y1, 'Invalid coverage rectangle')
            cx, cy = min(max(x, x0), x1), min(max(y, y0), y1)
            if max(abs(cx-x), abs(cy-y)) <= 104.:
                result.add(((cx-x)**2+(cy-y)**2, window['cooked_fields_manifest'], cx, cy))
    return sorted(result)


def sample_values(sample):
    require(sample is not None, 'Native sample unavailable')
    values = [sample.bed_height_meters, sample.depth_meters, sample.surface_height_meters,
              sample.velocity_meters_per_second.x, sample.velocity_meters_per_second.y]
    require(all(math.isfinite(v) for v in values) and values[1] >= 0, 'Invalid native state')
    return dict(wet=bool(sample.wet), bed_m=values[0], depth_m=values[1], surface_m=values[2],
                velocity_mps=values[3:])


def main():
    descriptor_path = (ROOT / os.environ['RAFTSIM_RECONSTRUCTION_DESCRIPTOR']).resolve()
    report = (ROOT / os.environ['RAFTSIM_RECONSTRUCTION_LAUNCH_REPORT']).resolve()
    require(descriptor_path.is_relative_to(ROOT), 'Descriptor outside repository')
    require(report.is_relative_to(ROOT / 'tmp') and not report.exists(), 'Fresh local report required')
    deps = Dependencies(ROOT)
    descriptor = deps.read(descriptor_path)
    require(descriptor['schema'] == 'raftsim.south_fork_joint_preview.v2' and
            descriptor['target_level'] == LEVEL, 'Source-matched full river required')
    for name, digest in descriptor['dependencies'].items():
        deps.add(ROOT / name, digest)
    def read(key):
        path = ROOT / descriptor[key]
        require(descriptor[key] in descriptor['dependencies'], 'Unbound evidence: ' + key)
        return deps.read(path)
    atlas, stream = read('atlas_manifest'), read('streaming_manifest')
    verify_audits(atlas, read('snapshot_audit'), read('bank_audit'), read('coverage_audit'),
                  deps.hashes[descriptor['atlas_manifest']], deps.hashes[descriptor['streaming_manifest']])
    collision = read('collision_audit')
    require(collision['failures'] == [] and collision['sampled_full_map_union_verified'] is True and
            collision['native_runtime']['field_queries_verified'] is True and
            collision['native_runtime']['atlas_sha256'] == deps.hashes[descriptor['atlas_manifest']],
            'Native terrain/water evidence failed')
    contracts = deps.read(CONTRACTS)
    require(contracts['level'] == LEVEL and contracts['rapid_has_no_menu_entry'] is True and
            len(contracts['sessions']) == 5, 'Full South Fork launch contracts required')
    deps.add(ROOT / contracts['coordinate_map'], contracts['coordinate_map_sha256'])
    entries = dict(streaming_manifest=descriptor['streaming_manifest'],
        initial_fields_manifest=descriptor['initial_fields_manifest'],
        hydraulic_coordinate_map=descriptor['coordinate_map'], route_coordinate_map=contracts['coordinate_map'])
    closure = Closure(ROOT)
    closure.collect(entries)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    require(levels.load_level(LEVEL), 'Normal map load failed')
    map_file = ROOT / 'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    protected = {deps.add(map_file): deps.hashes[map_file.relative_to(ROOT).as_posix()]}
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    for desc in descriptors:
        package = str(desc.actor_package)
        path = ROOT / 'unreal/Content' / (package[6:] + '.uasset')
        name = deps.add(path)
        protected[name] = deps.hashes[name]
    profile = ROOT / 'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav'
    if profile.exists():
        name = deps.add(profile)
        protected[name] = deps.hashes[name]
    catalog = {str(row.scenario_id): row for row in unreal.RaftSimProgressionLibrary.get_scenario_catalog()}
    require('troublemaker_challenge' not in catalog, 'Rapid incorrectly exposed as a scenario')
    route = unreal.RaftSimWaterRuntimeAdapter()
    require(route.configure_river_coordinate_map(contracts['coordinate_map']), 'Native route rejected')
    results = []
    for session in contracts['sessions']:
        item = catalog[session['id']]
        require(str(item.level_name) == LEVEL and abs(item.start_station_m-session['start_m']) < .002 and
                abs(item.finish_station_m-session['finish_m']) < .002, 'Catalog contract mismatch')
        point = route.river_to_world_position(unreal.Vector2D(session['start_m'], 0.), 220.)
        require(isinstance(point, unreal.Vector), 'Native route conversion failed')
        choices = candidates(stream, point.x/100., -point.y/100.)
        require(bool(choices), 'No covered launch crop for ' + session['id'])
        _, fields, cx, cy = choices[0]
        water = unreal.RaftSimWaterRuntimeAdapter()
        config = unreal.RaftSimWaterRuntimeConfig()
        config.require_accepted_report_manifest = False
        config.enable_deterministic_capture = False
        water.configure(config)
        require(water.configure_river_coordinate_map(descriptor['coordinate_map']), 'Native hydraulic coordinates rejected')
        require(water.configure_moving_river_window(str((ROOT / fields).parent), 'median_runnable',
            unreal.Vector2D(cx, cy), unreal.Vector2D(224, 224), stream['roughness_manning']), 'Native crop rejected')
        initial = sample_values(water.sample_water_at_world_position(point))
        failures = [] if initial['wet'] else ['authored_start_dry']
        # A short native evolution catches immediate invalid state; it is not
        # game-mode selection, full-raft support or whole-river acceptance.
        steps = 0
        for index in range(120):
            if not water.step_water(1./120.):
                failures.append('native_step_rejected')
                break
            steps += 1
        final = sample_values(water.sample_water_at_world_position(point))
        if not final['wet']:
            failures.append('authored_start_dry_after_one_second')
        results.append(dict(scenario_id=session['id'], start_m=session['start_m'],
            finish_m=session['finish_m'], world_start_cm=[point.x, point.y, point.z],
            initial_fields_manifest=fields, window_center_m=[cx, cy],
            initial=initial, final=final, solver_steps=steps, failures=failures))
        unreal.log('Source-matched launch preflight: ' + json.dumps(results[-1]))
    # Rehash directly, not through the dependency cache, to detect any write.
    from package_runtime_bundle import sha
    for name, digest in protected.items():
        require(sha(ROOT / name) == digest, 'Read-only preflight changed ' + name)
    result = dict(schema='raftsim.south_fork_reconstruction_launch_preflight.v1',
        passed=all(not row['failures'] for row in results), level=LEVEL,
        descriptor=descriptor_path.relative_to(ROOT).as_posix(), descriptor_sha256=sha(descriptor_path),
        source_time_seconds=atlas['source_time_seconds'], contracts_sha256=sha(CONTRACTS),
        launches=results, protected_files=protected, runtime_dependency_files=len(closure.files),
        saved_assets=False, game_mode_selector_verified=False, raft_contact_verified=False,
        settled_hydraulics=False, visual_accepted=False, performance_accepted=False)
    report.write_text(json.dumps(result, indent=2)+'\n')
    unreal.log('Reconstruction launch preflight report: ' + str(report))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
