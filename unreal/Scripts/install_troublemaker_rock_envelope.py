"""Install the interpreted Troublemaker rock envelope in the normal FullReach map.

Imports the FBX written by ``export_troublemaker_rock_envelope.py`` with the
same settings as the installed captured-rock solid (imported authored normals,
complex-as-simple collision from the render triangles, CPU access, Nanite with
a full fallback) and the same material, then points the existing rock actor at
the new mesh. Only the new mesh package and that actor's external package are
saved. The previous mesh asset is kept, so the change is a one-actor revert.

Run inside the editor:
  UnrealEditor-Cmd <project> -ExecCmds="py install_troublemaker_rock_envelope.py, QUIT_EDITOR"
with RAFTSIM_ROCK_ENVELOPE_EXPORT=<export dir> and RAFTSIM_ROCK_ENVELOPE_RECEIPT=<new json>.
"""
import hashlib
import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
ROCK_ACTOR = 'StaticMeshActor_UAID_04421A89ABE5930203_1558143815'
OLD_MESH = ('/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SourceMatched20260917/'
            'SM_CapturedRockInferredFlanks')
DEST = '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/RockEnvelope20260926/SM_CapturedRockEnvelope'
MATERIAL = '/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/MI_SouthForkCompositeGround'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def asset_file(path):
    return ROOT / 'unreal/Content' / (path.removeprefix('/Game/').split('.')[0] + '.uasset')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def import_envelope(export_dir):
    export = json.loads((export_dir / 'manifest.json').read_text())
    require(sha(ROOT / export['fbx']) == export['fbx_sha256'], 'FBX differs from its export manifest')
    require(not unreal.EditorAssetLibrary.does_asset_exist(DEST), 'Never overwrite an existing envelope asset')
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
    options.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    task = unreal.AssetImportTask()
    task.filename = str(ROOT / export['fbx'])
    task.destination_path = DEST.rsplit('/', 1)[0]
    task.destination_name = DEST.rsplit('/', 1)[1]
    task.automated = True
    task.replace_existing = False
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(DEST)
    require(isinstance(mesh, unreal.StaticMesh), 'Envelope import failed')
    mesh.set_editor_property('allow_cpu_access', True)
    bounds = mesh.get_bounding_box()
    actual = [[bounds.min.x, bounds.min.y, bounds.min.z], [bounds.max.x, bounds.max.y, bounds.max.z]]
    bounds_error = max(abs(actual[i][j] - export['expected_unreal_bounds_cm'][i][j])
                       for i in range(2) for j in range(3))
    require(bounds_error < 0.1, f'Imported bounds differ: {actual} vs {export["expected_unreal_bounds_cm"]}')
    mesh.get_editor_property('body_setup').set_editor_property(
        'collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    editor.enable_section_collision(mesh, True, 0, 0)
    settings = editor.get_nanite_settings(mesh)
    settings.enabled = True
    settings.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
    settings.fallback_percent_triangles = 1.0
    settings.fallback_relative_error = 0.0
    editor.set_nanite_settings(mesh, settings)
    mesh.set_material(0, unreal.load_asset(MATERIAL))
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    require(mesh.get_num_triangles(0) == export['triangle_count'], 'Triangle count changed on import')
    require(not editor.get_lod_build_settings(mesh, 0).recompute_normals, 'Authored normals were discarded')
    require(unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), 'Envelope save failed')
    return mesh, export, actual


def main():
    export_dir = (ROOT / os.environ['RAFTSIM_ROCK_ENVELOPE_EXPORT']).resolve()
    receipt = (ROOT / os.environ['RAFTSIM_ROCK_ENVELOPE_RECEIPT']).resolve()
    require(receipt.is_relative_to(ROOT / 'tmp') and not receipt.exists(), 'Fresh tmp receipt required')
    material_before = sha(asset_file(MATERIAL))
    old_mesh_before = sha(asset_file(OLD_MESH))
    mesh, export, bounds = import_envelope(export_dir)

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    require(levels.load_level(LEVEL), 'Normal scene load failed')
    descs = [d for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs() if str(d.name) == ROCK_ACTOR]
    require(len(descs) == 1, 'Rock actor descriptor missing')
    unreal.WorldPartitionBlueprintLibrary.load_actors([descs[0].guid])
    actors = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
              if a.get_name() == ROCK_ACTOR]
    require(len(actors) == 1, 'Rock actor not loaded')
    actor = actors[0]
    component = actor.static_mesh_component
    require(component.static_mesh.get_path_name().split('.')[0] == OLD_MESH, 'Rock actor already changed')
    transform = actor.get_actor_transform()
    require([transform.scale3d.x, transform.scale3d.y, transform.scale3d.z] == [1.0, -1.0, 1.0],
            'Rock actor transform changed')
    package_name = str(actor.get_package().get_name())
    package_file = ROOT / 'unreal/Content' / (package_name.removeprefix('/Game/') + '.uasset')
    actor_before = sha(package_file)
    actor.modify()
    component.modify()
    require(component.set_static_mesh(mesh), 'Mesh swap failed')
    require(component.get_material(0).get_path_name().split('.')[0] == MATERIAL, 'Material changed')
    require(unreal.EditorLoadingAndSavingUtils.save_packages([actor.get_package()], False), 'Actor save failed')
    report = dict(
        schema='raftsim.troublemaker_rock_envelope_install.v1',
        level=LEVEL, rock_actor=ROCK_ACTOR, actor_package=package_name,
        actor_package_sha256_before=actor_before, actor_package_sha256_after=sha(package_file),
        previous_mesh=OLD_MESH, previous_mesh_sha256=old_mesh_before,
        previous_mesh_unchanged=sha(asset_file(OLD_MESH)) == old_mesh_before,
        new_mesh=DEST, new_mesh_sha256=sha(asset_file(DEST)), imported_bounds_cm=bounds,
        export_manifest=export_dir.relative_to(ROOT).as_posix(), fbx_sha256=export['fbx_sha256'],
        envelope_sha256=export['envelope_sha256'], triangle_count=export['triangle_count'],
        material=MATERIAL, material_unchanged=sha(asset_file(MATERIAL)) == material_before,
        collision='complex-as-simple from the same render triangles',
        hydraulic_fields_changed=False, faces_measured=False, visual_accepted=False)
    receipt.write_text(json.dumps(report, indent=2) + '\n')
    unreal.log('RAFTSIM_ROCK_ENVELOPE_INSTALLED ' + json.dumps(report))


if __name__ == '__main__':
    main()
