"""Import the exact join and check collision in the full-river coordinate frame.

Only the new mesh asset is saved. The temporary test-tank actors/map are never
saved; the normal South Fork map is not promoted before hydraulic integration.
"""
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'unreal/SourceArt/RaftSim/SouthForkCompositeTerrain20260912'
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
ASSET = '/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/SM_SouthForkTroublemakerJoin'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    export = json.loads((SOURCE/'manifest.json').read_text())
    assert sha(ROOT/export['fbx']) == export['fbx_sha256']
    assert not unreal.EditorAssetLibrary.does_asset_exist(ASSET), 'Do not overwrite an existing geometry revision'
    probes = json.loads((BASE/'composite_terrain/engine_seam_probes.json').read_text())
    assert probes['source_geometry_sha256'] == export['source_geometry_sha256']
    placement = json.loads((BASE/'playable_route/troublemaker_placement.json').read_text())
    options = unreal.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_mesh = True
    options.import_as_skeletal = False
    options.mesh_type_to_import = options.original_import_type = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials = options.import_textures = options.import_animations = False
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.convert_scene_unit = True
    options.static_mesh_import_data.generate_lightmap_u_vs = False
    options.static_mesh_import_data.auto_generate_collision = False
    task = unreal.AssetImportTask()
    task.filename = str(ROOT/export['fbx'])
    task.destination_path, task.destination_name = ASSET.rsplit('/', 1)
    task.automated = True
    task.replace_existing = False
    task.save = False
    task.factory, task.options = unreal.FbxFactory(), options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(ASSET)
    assert isinstance(mesh, unreal.StaticMesh)
    bounds = mesh.get_bounding_box()
    actual = [[bounds.min.x, bounds.min.y, bounds.min.z], [bounds.max.x, bounds.max.y, bounds.max.z]]
    assert max(abs(actual[i][j]-export['expected_unreal_bounds_cm'][i][j]) for i in range(2) for j in range(3)) < .1
    mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    editor.enable_section_collision(mesh, True, 0, 0)
    settings = editor.get_nanite_settings(mesh)
    settings.enabled = True
    settings.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
    settings.fallback_percent_triangles = 1.
    settings.fallback_relative_error = 0.
    editor.set_nanite_settings(mesh, settings)
    material = unreal.load_asset('/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/MI_TroublemakerGround')
    assert material
    mesh.set_material(0, material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert mesh.get_num_triangles(0) == export['triangle_count']
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    tank_file = ROOT/'unreal/Content/RaftSim/Maps/L_RaftSimTestTank.umap'
    before = sha(tank_file)
    assert levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ignore = list(actors.get_all_level_actors())
    translation = unreal.Vector(*placement['translation_from_existing_rapid_world_cm'])
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, translation)
    actor.set_actor_scale3d(unreal.Vector(1, -1, 1))
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
    errors = []
    for point in probes['local_rapid_engine_cm']:
        query = unreal.Vector(*point)+translation
        hit = unreal.SystemLibrary.line_trace_single(world,
            query+unreal.Vector(0, 0, 1000), query-unreal.Vector(0, 0, 1000),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore, unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        assert values and values[0], f'Missing seam collision at {point}'
        error = abs(values[5].z-query.z)
        assert error < .1, f'Collision height error {error} cm'
        errors.append(error)
    assert actors.destroy_actor(actor)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    assert sha(tank_file) == before
    output = ROOT/'unreal/Saved/RaftSimValidation/south-fork-composite-seam-20260912.json'
    output.write_text(json.dumps(dict(asset=ASSET, source_geometry_sha256=export['source_geometry_sha256'],
        collision_probe_count=len(errors), maximum_collision_error_cm=max(errors),
        triangle_count=mesh.get_num_triangles(0), test_map_unchanged=True,
        normal_map_integrated=False, source_material_world_frame_review_pending=True), indent=2)+'\n')
    unreal.log(f'Composite seam asset/collision verified: {output}')


try:
    main()
finally:
    unreal.SystemLibrary.quit_editor()
