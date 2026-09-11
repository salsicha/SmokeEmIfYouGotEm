"""Import the exact crux collision solid and test every top triangle in engine."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
CENTERED='-RaftSimLiquidControlCentered' in unreal.SystemLibrary.get_command_line()
WINDOW_NAME='SouthForkLiquidControlCentered20260909' if CENTERED else 'SouthForkLiquidWindow20260908'
SOURCE=ROOT/'unreal/SourceArt/RaftSim'/WINDOW_NAME
DEST='/Game/RaftSim/Environment/'+WINDOW_NAME
NAME='SM_SouthForkLiquidCollisionSolid'
REPORT=ROOT/'docs/reconstruction-review-2026-09-07'/('liquid-control-centered-engine-import.json' if CENTERED else 'liquid-terrain-engine-import.json')


def main():
    assert not REPORT.exists() and not unreal.EditorAssetLibrary.does_asset_exist(DEST+'/'+NAME)
    manifest=json.loads((SOURCE/'manifest.json').read_text())
    export=json.loads((SOURCE/'fbx_export.json').read_text())
    probes=json.loads((SOURCE/'collision_probes.json').read_text())
    assert probes['solid_sha256']==export['solid_sha256']==manifest['solid_sha256']
    fbx=SOURCE/'SM_SouthForkLiquidCollisionSolid.fbx'
    assert hashlib.sha256(fbx.read_bytes()).hexdigest()==export['fbx_sha256']
    options=unreal.FbxImportUI()
    options.automated_import_should_detect_type=False
    options.import_mesh=True;options.import_as_skeletal=False
    options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.original_import_type=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials=False;options.import_textures=False;options.import_animations=False
    options.static_mesh_import_data.combine_meshes=True
    options.static_mesh_import_data.convert_scene_unit=True
    options.static_mesh_import_data.generate_lightmap_u_vs=False
    options.static_mesh_import_data.auto_generate_collision=False
    task=unreal.AssetImportTask()
    task.filename=str(fbx);task.destination_path=DEST;task.destination_name=NAME
    task.automated=True;task.replace_existing=False;task.save=False
    task.factory=unreal.FbxFactory();task.options=options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh=unreal.load_asset(DEST+'/'+NAME)
    assert isinstance(mesh,unreal.StaticMesh)
    mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    subsystem=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    subsystem.enable_section_collision(mesh,True,0,0)
    build=subsystem.get_lod_build_settings(mesh,0)
    build.set_editor_property('distance_field_resolution_scale',2.)
    build.set_editor_property('generate_distance_field_as_if_two_sided',False)
    subsystem.set_lod_build_settings(mesh,0,build)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert mesh.get_num_triangles(0)==export['triangles']
    bounds=mesh.get_bounding_box()
    actual=[[bounds.min.x,bounds.min.y,bounds.min.z],[bounds.max.x,bounds.max.y,bounds.max.z]]
    assert max(abs(actual[i][j]-export['expected_local_bounds_cm'][i][j]) for i in range(2) for j in range(3))<.1
    world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ground=actors.spawn_actor_from_class(unreal.StaticMeshActor,
        unreal.Vector(*manifest['local_origin_engine_cm']),
        unreal.Rotator(pitch=0,yaw=manifest['local_to_engine_yaw_degrees'],roll=0))
    ground.static_mesh_component.set_static_mesh(mesh)
    ground.static_mesh_component.set_collision_profile_name('BlockAll')
    transform=ground.get_actor_transform()
    maximum_error=0.
    for local in probes['top_triangle_centroids_local_cm']:
        point=unreal.MathLibrary.transform_location(transform,unreal.Vector(*local))
        hit=unreal.SystemLibrary.line_trace_single(world,point+unreal.Vector(0,0,1000),
            point-unreal.Vector(0,0,1000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False,[],unreal.DrawDebugTrace.NONE,False)
        values=hit.to_tuple() if hit else None
        assert values and values[0], f'Missing top collision at {local}'
        error=abs(values[5].z-point.z)
        assert error<.1, f'Changed top collision at {local}: {error}cm'
        maximum_error=max(maximum_error,error)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False)
    REPORT.write_text(json.dumps({'asset':mesh.get_path_name(),
        'solid_sha256':manifest['solid_sha256'],'fbx_sha256':export['fbx_sha256'],
        'top_triangle_probes':len(probes['top_triangle_centroids_local_cm']),
        'maximum_engine_collision_height_error_cm':maximum_error,
        'distance_field_resolution_scale':2.,'distance_field_data_verified':False,
        'local_origin_engine_cm':manifest['local_origin_engine_cm'],
        'yaw_degrees':manifest['local_to_engine_yaw_degrees'],
        'level_saved':False,'hydraulic_boundary_handoff_ready':manifest['boundary_handoff_ready'],
        'fluid_coupled':False,'production_promoted':False},indent=2)+'\n')
    unreal.log('Imported exact captured-candidate crux solid; all top collision probes passed')


try:
    main()
finally:
    unreal.SystemLibrary.quit_editor()
