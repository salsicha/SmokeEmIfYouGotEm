"""Transient native import/trace verification. Saves no assets or levels."""
import hashlib
import json
import math
import os
from pathlib import Path
import unreal

ROOT=Path(__file__).resolve().parents[2]
EXPORT=ROOT/'tmp/troublemaker-dem-rock-cap-v4-20260915/fbx'
PROBES=ROOT/'tmp/troublemaker-dem-rock-cap-v4-20260915/native-probes-v3.json'
REPORT=ROOT/'unreal/Saved/RaftSimValidation/dem-rock-cap-collision-v3-20260915.json'
ASSET='/Game/RaftSim/Environment/GeneratedLocalReview/DemRockCap20260915/SM_OriginalReturnRockSolid'


def import_candidate_solid(export_directory=None,asset_path=None):
    """Import the source-exact candidate without saving or replacing assets."""
    export_directory=EXPORT if export_directory is None else Path(export_directory)
    asset_path=ASSET if asset_path is None else asset_path
    export=json.loads((export_directory/'manifest.json').read_text())
    assert hashlib.sha256((ROOT/export['fbx']).read_bytes()).hexdigest()==export['fbx_sha256']
    assert not unreal.EditorAssetLibrary.does_asset_exist(asset_path)
    options=unreal.FbxImportUI()
    options.automated_import_should_detect_type=False
    options.import_mesh=True;options.import_as_skeletal=False
    options.mesh_type_to_import=options.original_import_type=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials=options.import_textures=options.import_animations=False
    options.static_mesh_import_data.combine_meshes=True
    options.static_mesh_import_data.convert_scene_unit=True
    options.static_mesh_import_data.generate_lightmap_u_vs=False
    options.static_mesh_import_data.auto_generate_collision=False
    if export.get('shading',{}).get('import_normals_required'):
        options.static_mesh_import_data.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    task=unreal.AssetImportTask();task.filename=str(ROOT/export['fbx'])
    task.destination_path=asset_path.rsplit('/',1)[0];task.destination_name=asset_path.rsplit('/',1)[1]
    task.automated=True;task.replace_existing=False;task.save=False
    task.factory=unreal.FbxFactory();task.options=options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh=unreal.load_asset(asset_path);assert isinstance(mesh,unreal.StaticMesh)
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
    if export.get('shading',{}).get('import_normals_required'):
        assert not editor.get_lod_build_settings(mesh,0).recompute_normals
    return mesh,export


def candidate_configuration(path,root=ROOT):
    """Explicit local-review targets only; partial or destructive overrides fail."""
    root=Path(root).resolve()
    config=json.loads(Path(path).read_text())
    resolved={key:(root/config[key]).resolve() for key in ('export_directory','probes','report')}
    if not resolved['export_directory'].is_relative_to(root/'tmp') or not resolved['probes'].is_relative_to(root/'tmp'):
        raise ValueError('Generated candidate inputs must stay within project tmp')
    if not resolved['report'].is_relative_to(root/'unreal/Saved/RaftSimValidation') or resolved['report'].exists():
        raise ValueError('Fresh local validation report required')
    if not (resolved['export_directory']/'manifest.json').is_file() or not resolved['probes'].is_file():
        raise ValueError('Existing export manifest and source probes required')
    asset=config['asset']
    if not asset.startswith('/Game/RaftSim/Environment/GeneratedLocalReview/') or any(
            not part or not part.replace('_','').isalnum() for part in asset[1:].split('/')):
        raise ValueError('Only a regenerable local-review asset path is allowed')
    return resolved|dict(asset=asset)


def main():
    config_path=os.environ.get('RAFTSIM_ROCK_COLLISION_CONFIG')
    config=candidate_configuration(config_path) if config_path else dict(export_directory=EXPORT,probes=PROBES,report=REPORT,asset=ASSET)
    report_path,probes_path=config['report'],config['probes']
    assert not report_path.exists()
    probes=json.loads(probes_path.read_text())
    mesh,export=import_candidate_solid(config['export_directory'],config['asset'])
    assert export['source_cap_sha256']==probes['source_cap_sha256']
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
    errors=[];kinds={};failures=[];kind_errors={}
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
        if error>.1:failures.append(dict(probe=probe,reason='source_position_error',error_cm=error,
            actual_hit_position_cm=[values[5].x,values[5].y,values[5].z]))
        errors.append(error);kinds[probe['kind']]=kinds.get(probe['kind'],0)+1
        kind_errors[probe['kind']]=max(kind_errors.get(probe['kind'],0.),error)
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(dict(source_cap_sha256=export['source_cap_sha256'],fbx_sha256=export['fbx_sha256'],
        source_probe_sha256=hashlib.sha256(probes_path.read_bytes()).hexdigest(),triangle_count=mesh.get_num_triangles(0),
        requested_probe_count=len(probes['probes']),probe_count=len(errors),probe_kind_counts=kinds,
        probe_kind_maximum_error_cm=kind_errors,
        probe_kind_failure_counts={kind:sum(f['probe']['kind']==kind for f in failures) for kind in {p['kind'] for p in probes['probes']}},
        maximum_collision_error_cm=max(errors) if errors else None,failures=failures,
        collision_verified=not failures,actor_location_cm=[location.x,location.y,location.z],
        complex_collision_same_triangles=True,full_nanite_fallback=True,saved_assets=False,saved_levels=False,
        parent_terrain_modified=False,actual_full_river_union_verified=False,
        hydraulic_recooked=False,playable_integrated=False,visual_acceptance=False),indent=2)+'\n')
    assert not failures, str(len(failures))+' collision probes failed; see '+str(report_path)
    unreal.log('Transient source-rock collision verified: '+str(report_path))


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
