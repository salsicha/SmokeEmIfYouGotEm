"""Connect corrected captured support, collision and recooked fields to play."""
import hashlib
import json
from pathlib import Path
import shutil
import unreal

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'unreal/SourceArt/RaftSim/TroublemakerSparseRockSupport20260912'
GEOMETRY = ROOT/'tmp/troublemaker-sparse-rock-support-20260912'
FIELDS = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_flow'
BACKUP = ROOT/'tmp/troublemaker-playable-before-sparse-rock-20260912'
LEVEL = '/Game/RaftSim/Maps/L_SouthFork_Troublemaker'
ASSETS = '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker'
NAME = 'SM_TroublemakerCapturedGround'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/troublemaker-sparse-rock-integration-20260912.json'
EXPECTED_LEVEL_SHA = '743a420632a767a78b56779705e394091c94a6f0ad2cdb04a5be3f60ca25f862'
EXPECTED_MESH_SHA = None
MASK_SOURCE = ROOT/'unreal/SourceArt/RaftSim/TroublemakerSparseRockAuthority20260912'
GROUND_LABEL = 'Captured ground and corroborated rock returns - inferred submerged bed'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not REPORT.exists()
    replacing = unreal.EditorAssetLibrary.does_asset_exist(ASSETS+'/'+NAME)
    assert replacing == (EXPECTED_MESH_SHA is not None)
    export = json.loads((SOURCE/'manifest.json').read_text())
    audit = json.loads((GEOMETRY/'sampling-audit.json').read_text())
    delivery = json.loads((FIELDS/'delivery.json').read_text())
    expected = delivery['source_geometry_sha256']
    assert expected == export['source_geometry_sha256'] == audit['source_geometry_sha256'] == sha(GEOMETRY/'registered_mesh_source.npz')
    assert sha(ROOT/export['fbx']) == export['fbx_sha256']
    for name, digest in delivery['files'].items():
        assert sha(FIELDS/name) == digest
    level_file = ROOT/'unreal/Content/RaftSim/Maps/L_SouthFork_Troublemaker.umap'
    assert sha(level_file) == EXPECTED_LEVEL_SHA
    assert not (BACKUP/level_file.name).exists()
    shutil.copy2(level_file, BACKUP/level_file.name)
    mesh_file = ROOT/('unreal/Content/'+ASSETS.removeprefix('/Game/')+'/'+NAME+'.uasset')
    if replacing:
        assert sha(mesh_file) == EXPECTED_MESH_SHA
        assert not (BACKUP/mesh_file.name).exists()
        shutil.copy2(mesh_file, BACKUP/mesh_file.name)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    grounds = [a for a in actors if isinstance(a, unreal.StaticMeshActor) and unreal.Name('RaftSimPhysicalGround') in a.tags]
    assert len(grounds) == 1
    ground = grounds[0]
    assert ground.get_actor_scale3d() == unreal.Vector(1, -1, 1)
    material = ground.static_mesh_component.get_material(0)
    original_mesh = ground.static_mesh_component.static_mesh
    options = unreal.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_mesh = True; options.import_as_skeletal = False
    options.mesh_type_to_import = options.original_import_type = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials = options.import_textures = options.import_animations = False
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.convert_scene_unit = True
    options.static_mesh_import_data.generate_lightmap_u_vs = False
    options.static_mesh_import_data.auto_generate_collision = False
    task = unreal.AssetImportTask()
    task.filename = str(ROOT/export['fbx']); task.destination_path = ASSETS; task.destination_name = NAME
    task.automated = True; task.replace_existing = replacing; task.save = False
    task.factory = unreal.FbxFactory(); task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(ASSETS+'/'+NAME)
    assert isinstance(mesh, unreal.StaticMesh)
    bounds = mesh.get_bounding_box()
    actual = [[bounds.min.x,bounds.min.y,bounds.min.z],[bounds.max.x,bounds.max.y,bounds.max.z]]
    assert max(abs(actual[i][j]-export['expected_unreal_bounds_cm'][i][j]) for i in range(2) for j in range(3)) < 2
    mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    editor.enable_section_collision(mesh, True, 0, 0)
    settings = editor.get_nanite_settings(mesh); settings.enabled = True
    settings.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
    settings.fallback_percent_triangles = 1.; settings.fallback_relative_error = 0.
    editor.set_nanite_settings(mesh, settings)
    mesh.set_material(0, material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert mesh.get_num_triangles(0) == export['triangle_count']
    ground.static_mesh_component.set_static_mesh(mesh)
    ground.static_mesh_component.set_collision_profile_name('BlockAll')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    errors = []
    ignore = [a for a in actors if a != ground]
    probes = audit['exact_changed_triangle_probes_cm']
    # Original source points are still checked, but changed adjacent face
    # interiors must use the new source height, never the superseded surface.
    probes += [[p['position_cm'][0],-p['position_cm'][1],p['position_cm'][2]] for p in export['collision_probes_cm']]
    for x, y, z in probes:
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x,y,z+1000), unreal.Vector(x,y,z-1000),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore, unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        assert values and values[0], (x,y,z)
        error = abs(values[5].z-z)
        assert error <= .1, (x,y,z,error)
        errors.append(error)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    ground.set_actor_label(GROUND_LABEL)
    assert levels.save_current_level()
    # Update only classification data, not material shape/lighting graphs.
    texture_file = ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/T_TroublemakerSurfaceAuthority.uasset'
    shutil.copy2(texture_file, BACKUP/texture_file.name)
    mask_source = MASK_SOURCE
    meta = json.loads((mask_source/'manifest.json').read_text())
    assert meta['source_mesh_sha256'] == expected
    task = unreal.AssetImportTask(); task.filename = str(mask_source/'T_TroublemakerSurfaceAuthority.png')
    task.destination_path = ASSETS; task.destination_name = 'T_TroublemakerSurfaceAuthority'
    task.automated = True; task.replace_existing = True; task.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(ASSETS+'/T_TroublemakerSurfaceAuthority')
    texture.set_editor_property('srgb', False)
    texture.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    mesh_file = ROOT/('unreal/Content/'+ASSETS.removeprefix('/Game/')+'/'+NAME+'.uasset')
    REPORT.write_text(json.dumps(dict(level=LEVEL, level_sha256=sha(level_file), mesh=ASSETS+'/'+NAME,
        mesh_sha256=sha(mesh_file), source_geometry_sha256=expected, previous_mesh=original_mesh.get_path_name(),
        collision_probe_count=len(errors), maximum_collision_error_cm=max(errors), triangle_count=mesh.get_num_triangles(0),
        material_preserved=material.get_path_name(), authority_texture_sha256=sha(texture_file),
        previous_level_sha256=EXPECTED_LEVEL_SHA, previous_mesh_sha256=EXPECTED_MESH_SHA,
        backup_directory=BACKUP.relative_to(ROOT).as_posix(),
        source_geometry_path=(GEOMETRY/'registered_mesh_source.npz').relative_to(ROOT).as_posix(),
        source_mask=meta, normal_playable_integrated=True, runtime_traversal_verified=False, visual_acceptance=False), indent=2)+'\n')
    unreal.log(f'Corrected rock support integrated in normal playable scenario: {REPORT}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
