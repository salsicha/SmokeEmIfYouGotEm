"""Transient native import/trace verification. Saves no assets or levels."""
import hashlib
import json
import math
from pathlib import Path
import unreal

ROOT=Path(__file__).resolve().parents[2]
EXPORT=ROOT/'tmp/troublemaker-dem-rock-cap-v4-20260915/fbx'
PROBES=ROOT/'tmp/troublemaker-dem-rock-cap-v4-20260915/native-probes-v3.json'
REPORT=ROOT/'unreal/Saved/RaftSimValidation/dem-rock-cap-collision-v3-20260915.json'
ASSET='/Game/RaftSim/Environment/GeneratedLocalReview/DemRockCap20260915/SM_OriginalReturnRockSolid'


def main():
    assert not REPORT.exists()
    export=json.loads((EXPORT/'manifest.json').read_text());probes=json.loads(PROBES.read_text())
    assert export['source_cap_sha256']==probes['source_cap_sha256']
    assert hashlib.sha256((ROOT/export['fbx']).read_bytes()).hexdigest()==export['fbx_sha256']
    assert not unreal.EditorAssetLibrary.does_asset_exist(ASSET)
    options=unreal.FbxImportUI()
    options.automated_import_should_detect_type=False
    options.import_mesh=True;options.import_as_skeletal=False
    options.mesh_type_to_import=options.original_import_type=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials=options.import_textures=options.import_animations=False
    options.static_mesh_import_data.combine_meshes=True
    options.static_mesh_import_data.convert_scene_unit=True
    options.static_mesh_import_data.generate_lightmap_u_vs=False
    options.static_mesh_import_data.auto_generate_collision=False
    task=unreal.AssetImportTask();task.filename=str(ROOT/export['fbx'])
    task.destination_path=ASSET.rsplit('/',1)[0];task.destination_name=ASSET.rsplit('/',1)[1]
    task.automated=True;task.replace_existing=False;task.save=False
    task.factory=unreal.FbxFactory();task.options=options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh=unreal.load_asset(ASSET);assert isinstance(mesh,unreal.StaticMesh)
    bounds=mesh.get_bounding_box()
    actual=[[bounds.min.x,bounds.min.y,bounds.min.z],[bounds.max.x,bounds.max.y,bounds.max.z]]
    assert max(abs(actual[i][j]-export['expected_unreal_bounds_cm'][i][j]) for i in range(2) for j in range(3))<.1
    mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    editor.enable_section_collision(mesh,True,0,0)
    settings=editor.get_nanite_settings(mesh);settings.enabled=True
    settings.fallback_target=unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
    settings.fallback_percent_triangles=1.;settings.fallback_relative_error=0.
    editor.set_nanite_settings(mesh,settings)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert mesh.get_num_triangles(0)==export['triangle_count']
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ignore=actors.get_all_level_actors()
    ground=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0))
    # Editor spawning may choose a viewport placement. Traces require the
    # declared source frame, not the editor's last placement or rotation.
    ground.set_actor_location(unreal.Vector(0,0,0),False,True)
    ground.set_actor_rotation(unreal.Rotator(0,0,0),True)
    ground.set_actor_scale3d(unreal.Vector(1,-1,1))
    ground.static_mesh_component.set_static_mesh(mesh)
    ground.static_mesh_component.set_collision_profile_name('BlockAll')
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    location=ground.get_actor_location();rotation=ground.get_actor_rotation()
    assert location==unreal.Vector(0,0,0) and rotation==unreal.Rotator(0,0,0)
    errors=[];kinds={};failures=[]
    for probe in probes['probes']:
        p=unreal.Vector(*probe['world_position_cm']);n=unreal.Vector(*probe['outward_normal'])
        distance=probe['ray_half_length_cm']
        hit=unreal.SystemLibrary.line_trace_single(world,p+n*distance,p-n*distance,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignore,unreal.DrawDebugTrace.NONE,False)
        values=hit.to_tuple() if hit else None
        if not values or not values[0]:
            failures.append(dict(probe=probe,reason='no_blocking_hit'))
            continue
        error=math.sqrt((values[5].x-p.x)**2+(values[5].y-p.y)**2+(values[5].z-p.z)**2)
        if error>.1:failures.append(dict(probe=probe,reason='source_position_error',error_cm=error))
        errors.append(error);kinds[probe['kind']]=kinds.get(probe['kind'],0)+1
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(dict(source_cap_sha256=export['source_cap_sha256'],fbx_sha256=export['fbx_sha256'],
        source_probe_sha256=hashlib.sha256(PROBES.read_bytes()).hexdigest(),triangle_count=mesh.get_num_triangles(0),
        requested_probe_count=len(probes['probes']),probe_count=len(errors),probe_kind_counts=kinds,
        maximum_collision_error_cm=max(errors) if errors else None,failures=failures,
        collision_verified=not failures,actor_location_cm=[location.x,location.y,location.z],
        complex_collision_same_triangles=True,full_nanite_fallback=True,saved_assets=False,saved_levels=False,
        parent_terrain_modified=False,actual_full_river_union_verified=False,
        hydraulic_recooked=False,playable_integrated=False,visual_acceptance=False),indent=2)+'\n')
    assert not failures, str(len(failures))+' collision probes failed; see '+str(REPORT)
    unreal.log('Transient source-rock collision verified: '+str(REPORT))


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
