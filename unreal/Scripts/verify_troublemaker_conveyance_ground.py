"""Verify candidate triangles on the existing normal-scene ground actor.

Only the verified new mesh may be saved. The actor swap is transient. Ground-
only traces explicitly ignore rocks; this is NOT complete union/play acceptance.
"""
import json
import math
import os
from pathlib import Path
import sys

import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/scripts'))
sys.path.insert(0, str(ROOT/'unreal/Scripts'))
from package_runtime_bundle import sha
from prepare_south_fork_joint_preview import asset_file, require
from south_fork_terrain_replacement import compare_native_meshes, native_source
from verify_troublemaker_dem_rock_cap_collision import import_candidate_solid

LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'


def main():
    source = (ROOT/os.environ['RAFTSIM_BED_NATIVE_PREFLIGHT']).resolve()
    output = (ROOT/os.environ['RAFTSIM_BED_NATIVE_REPORT']).resolve()
    require(source.is_relative_to(ROOT/'tmp') and output.is_relative_to(ROOT/'tmp') and
            not output.exists(), 'Explicit fresh project tmp inputs/report required')
    preflight = json.loads(source.read_text())
    require(preflight['schema'] == 'raftsim.troublemaker_bed_native_preflight.v1', 'Wrong preflight')
    dependencies = preflight['dependencies']

    def check_dependencies():
        for name, digest in dependencies.items():
            path = (ROOT/name).resolve()
            require(path.is_relative_to(ROOT) and sha(path) == digest, 'Source changed: '+name)

    check_dependencies()
    asset = preflight['candidate_asset']
    require(asset.startswith('/Game/RaftSim/Environment/GeneratedLocalReview/') and
            not asset_file(asset).exists() and not unreal.EditorAssetLibrary.does_asset_exist(asset),
            'Fresh regenerable candidate asset required')
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    require(levels.load_level(LEVEL), 'Normal scene failed to load')
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    protected = {str(asset_file(str(d.actor_package))):sha(asset_file(str(d.actor_package))) for d in descs}
    map_path = ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    protected[str(map_path)] = sha(map_path)
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs if d.native_class.get_name() == 'StaticMeshActor'])
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    matches = [a for a in actors if isinstance(a, unreal.StaticMeshActor) and
        a.static_mesh_component.static_mesh and
        a.static_mesh_component.static_mesh.get_path_name().split('.')[0] == preflight['baseline_asset']]
    require(len(matches) == 1, 'Exactly one installed baseline ground actor required')
    actor = matches[0]
    component = actor.static_mesh_component
    original = component.static_mesh
    require('RaftSimPhysicalGround' in map(str,actor.tags) and
            str(component.get_collision_profile_name()) == 'BlockAll', 'Ground collision contract changed')
    require(actor.get_actor_scale3d() == unreal.Vector(1.,-1.,1.), 'Registered reflection changed')
    rotation = actor.get_actor_rotation()
    require(max(abs(rotation.pitch),abs(rotation.yaw),abs(rotation.roll)) < 1e-5, 'Registered rotation changed')
    pos = actor.get_actor_location()
    material = component.get_material(0)
    original_disallow_nanite = component.get_editor_property('disallow_nanite')
    before = native_source(original, preflight['triangle_count'])
    require(before['collision_source_sha256'] == preflight['baseline_native_source']['collision_source_sha256'] and
            sha(asset_file(preflight['baseline_asset'])) == preflight['baseline_package_sha256'], 'Baseline native source changed')
    candidate, export = import_candidate_solid(ROOT/preflight['export_directory'], asset)
    require(export['source_geometry_sha256'] == preflight['candidate_mesh_sha256'], 'Export source changed')
    candidate.set_material(0, material)
    after = native_source(candidate, preflight['triangle_count'])
    exact = compare_native_meshes(original, candidate, preflight)
    require(component.set_static_mesh(candidate), 'Transient actor replacement failed')
    component.set_editor_property('disallow_nanite', True)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ignored = [a for a in actors if a != actor]
    failures = []
    max_error = 0.
    probes = preflight['ground_triangle_centroids_cm']
    require(len(probes) == preflight['changed_triangle_probe_count'], 'Incomplete changed-face probes')
    for i, (x,y,z) in enumerate(probes):
        p = pos+unreal.Vector(x,-y,z)
        hit = unreal.SystemLibrary.line_trace_single(world, p+unreal.Vector(0,0,1000),
            p-unreal.Vector(0,0,1000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False,
            ignored, unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        if not values or not values[0]:
            failures.append(dict(index=i,reason='no_blocking_hit'))
            continue
        point = values[5]
        error = math.sqrt((point.x-p.x)**2+(point.y-p.y)**2+(point.z-p.z)**2)
        owner = next((v for v in values if isinstance(v,unreal.Actor)),None)
        max_error = max(max_error,error)
        if error > .1 or owner != actor:
            failures.append(dict(index=i,reason='position_or_owner',error_cm=error))
    require(component.set_static_mesh(original), 'Failed to restore transient actor binding')
    component.set_editor_property('disallow_nanite', original_disallow_nanite)
    check_dependencies()
    for path,digest in protected.items():
        require(sha(Path(path)) == digest, 'Saved normal scene changed: '+path)
    saved = False
    if not failures:
        require(unreal.EditorAssetLibrary.save_loaded_asset(candidate, only_if_is_dirty=False), 'Candidate save failed')
        require(native_source(candidate, preflight['triangle_count'])['collision_source_sha256'] ==
                after['collision_source_sha256'], 'Save changed native geometry')
        saved = True
    report = dict(schema='raftsim.troublemaker_conveyance_ground_native.v1',
        preflight=source.relative_to(ROOT).as_posix(),preflight_sha256=sha(source),
        source_mesh_sha256=preflight['candidate_mesh_sha256'],mesh_asset=asset,
        original_actor=actor.get_name(),original_asset=preflight['baseline_asset'],
        original_native_source=before,revised_native_source=after,exact_native_replacement=exact,
        changed_triangle_trace_count=len(probes),maximum_collision_error_cm=max_error,position_tolerance_cm=.1,
        failures=failures,passed=not failures,saved_candidate_mesh=saved,
        candidate_package_sha256=sha(asset_file(asset)) if saved else None,
        protected_scene_package_count=len(protected),saved_levels=False,
        normal_scene_unchanged=True,ground_only_rocks_excluded=True,
        rock_union_verified=False,hydraulic_runtime_verified=False,playable_integrated=False)
    output.write_text(json.dumps(report,indent=2)+'\n')
    require(not failures, 'Ground trace failures; preserve report')
    unreal.log('Exact candidate ground verified; normal scene unchanged: '+str(output))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
