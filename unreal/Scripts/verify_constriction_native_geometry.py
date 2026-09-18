"""Import and save only an isolated verified candidate asset, never the map."""
import json
import os
from pathlib import Path
import sys
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'unreal/Scripts'))
from south_fork_terrain_replacement import native_source, sha
from verify_troublemaker_dem_rock_cap_collision import import_candidate_solid


def main():
    proof_path = (ROOT/os.environ['RAFTSIM_CONSTRICTION_NATIVE_PROOF']).resolve()
    output = (ROOT/os.environ['RAFTSIM_CONSTRICTION_NATIVE_REPORT']).resolve()
    if not proof_path.is_relative_to(ROOT/'tmp') or not output.is_relative_to(ROOT/'unreal/Saved/RaftSimValidation') or output.exists():
        raise ValueError('Existing local proof and fresh native report required')
    proof = json.loads(proof_path.read_text())
    assert proof['schema'] == 'raftsim.constriction_native_geometry.v1'
    assert proof['native_collision_tolerance_cm'] == .1
    asset = proof['asset']
    assert asset.startswith('/Game/RaftSim/Environment/GeneratedLocalReview/') and '..' not in asset
    export_dir = ROOT/proof['export_directory']
    assert sha(export_dir/'manifest.json') == proof['export_manifest_sha256']
    source = proof['revision']
    assert sha(ROOT/source['manifest']) == source['manifest_sha256']
    assert sha(ROOT/source['mesh_path']) == source['revised_geometry_sha256']
    map_file = ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    old_file = ROOT/'unreal/Content'/(proof['installed_asset'][6:]+'.uasset')
    protected = {str(p): sha(p) for p in (map_file, old_file)}
    installed = unreal.load_asset(proof['installed_asset'])
    assert native_source(installed, proof['triangle_count'])['collision_source_sha256'] == proof['installed_native_source_sha256']
    mesh, export = import_candidate_solid(export_dir, asset)
    mesh.set_material(0, installed.get_material(0))
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    native = native_source(mesh, proof['triangle_count'])
    assert native['collision_source_sha256'] == proof['expected_native_source_sha256'], 'Imported full directed source differs'
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ignored = actors.get_all_level_actors()
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
    actor.set_actor_location(unreal.Vector(0, 0, 0), False, True)
    actor.set_actor_rotation(unreal.Rotator(0, 0, 0), True)
    actor.set_actor_scale3d(unreal.Vector(1, -1, 1))
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
    actor.static_mesh_component.set_editor_property('disallow_nanite', True)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    counts, maximum, failures = {}, 0., []
    for index, probe in enumerate(proof['probes']):
        p = unreal.Vector(*probe['world_position_cm'])
        hit = unreal.SystemLibrary.line_trace_single(world, p+unreal.Vector(0, 0, 100), p-unreal.Vector(0, 0, 100),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignored, unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        counts[probe['kind']] = counts.get(probe['kind'], 0)+1
        if not values or not values[0]:
            failures.append(dict(index=index, reason='no_blocking_hit'))
            continue
        q = values[5]
        error = ((q.x-p.x)**2+(q.y-p.y)**2+(q.z-p.z)**2)**.5
        maximum = max(maximum, error)
        if error > .1:
            failures.append(dict(index=index, reason='source_position_error', error_cm=error))
    result = dict(schema='raftsim.constriction_native_geometry_audit.v1', proof_path=str(proof_path.relative_to(ROOT)),
                  proof_sha256=sha(proof_path), native_source=native, all_directed_triangles_source_exact=True,
                  probe_counts=counts, maximum_collision_error_cm=maximum, failures=failures,
                  saved_local_mesh=False, saved_levels=False, normal_game_integrated=False,
                  physical_union_and_flow_verified=False, visual_or_performance_accepted=False)
    if not failures:
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        asset_file = ROOT/'unreal/Content'/(asset[6:]+'.uasset')
        result.update(saved_local_mesh=True, asset=asset, mesh_sha256=sha(asset_file))
    for path, digest in protected.items():
        assert sha(path) == digest, 'Installed asset/map changed'
    result['protected_files'] = protected
    output.write_text(json.dumps(result, indent=2)+'\n')
    assert not failures, 'Native collision failures retained in report'
    unreal.log('Isolated source-supported terrain verified and saved: '+str(output))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
