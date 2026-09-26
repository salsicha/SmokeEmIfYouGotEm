"""Import the South Fork terrain backdrop and place it, always loaded, in FullReach.

The normal map streams its 441 detailed terrain tiles within 2 km of the view
and has no far-field terrain, so beyond that the world ended in sky and distant
ridges and trees read as floating shards. The backdrop
(physics/scripts/build_south_fork_terrain_backdrop.py; exported by
export_south_fork_composite_tiles.py) lies at least 1.5 m below every detailed
tile surface, so it is hidden wherever a tile is loaded.

Mesh: same FBX import options as the tiles, Nanite on, no collision, no mesh
distance field, the coarse tiles' ground material. Actor: one StaticMeshActor
at the tile-convention translation and (1, -1, 1) scale, not spatially loaded,
no collision, no shadow casting, no navigation. Existing tiles, collision,
water and cooks are untouched. Refuses to run twice.

Environment: RAFTSIM_BACKDROP_EXPORT (repo-relative export manifest),
RAFTSIM_BACKDROP_REPORT (fresh repo tmp JSON).
"""
import hashlib
import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
ASSETS = '/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/Backdrop'
MATERIAL_SOURCE_TILE = '/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/Tiles/SM_SouthFork_coarse_0000_4096'
LABEL = 'SouthFork terrain backdrop - 8 m min-eroded, inferred presentation, no collision'
TAG = 'RaftSimTerrainBackdrop'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    export_path = ROOT / os.environ['RAFTSIM_BACKDROP_EXPORT']
    report_path = ROOT / os.environ['RAFTSIM_BACKDROP_REPORT']
    assert report_path.is_relative_to(ROOT / 'tmp') and not report_path.exists()
    export = json.loads(export_path.read_text())
    assert len(export['tiles']) == 1
    tile = export['tiles'][0]
    fbx = ROOT / tile['fbx']
    assert sha(fbx) == tile['fbx_sha256']
    asset = ASSETS + '/' + tile['asset_name']
    assert not unreal.EditorAssetLibrary.does_asset_exist(asset), 'Backdrop already imported; inspect before retrying'

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    assert not any(str(d.label) == LABEL for d in descs), 'Backdrop actor already placed'

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
    task.filename = str(fbx)
    task.destination_path, task.destination_name = ASSETS, tile['asset_name']
    task.automated = True
    task.replace_existing = False
    task.save = False
    task.factory, task.options = unreal.FbxFactory(), options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(asset)
    assert isinstance(mesh, unreal.StaticMesh)
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    settings = editor.get_nanite_settings(mesh)
    settings.enabled = True
    settings.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
    settings.fallback_percent_triangles = 0.1
    editor.set_nanite_settings(mesh, settings)
    distance_field = 'unchanged'
    try:
        build = editor.get_lod_build_settings(mesh, 0)
        build.set_editor_property('distance_field_resolution_scale', 0.0)
        editor.set_lod_build_settings(mesh, 0, build)
        distance_field = 'disabled'
    except Exception as error:  # Setting names differ between engine versions.
        distance_field = 'unchanged: ' + str(error)[:120]
    material = unreal.load_asset(MATERIAL_SOURCE_TILE).get_material(0)
    assert material
    mesh.set_material(0, material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    # LOD0 here is the Nanite fallback (10 % of the source triangles); the
    # imported geometry is checked by its bounds against the export record.
    fallback_triangles = mesh.get_num_triangles(0)
    assert 0 < fallback_triangles <= tile['triangle_count'], (fallback_triangles, tile['triangle_count'])
    box = mesh.get_bounding_box()
    actual = [[box.min.x, box.min.y, box.min.z], [box.max.x, box.max.y, box.max.z]]
    bound_error = max(abs(actual[i][j] - tile['expected_unreal_bounds_cm'][i][j]) for i in range(2) for j in range(3))
    assert bound_error < 1.0, ('Backdrop bounds differ from the export', actual, tile['expected_unreal_bounds_cm'])
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    t = tile['actor_translation_cm']
    actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(t[0], t[1], t[2]))
    actor.set_actor_scale3d(unreal.Vector(*tile['actor_scale']))
    actor.set_actor_label(LABEL)
    actor.tags = [TAG, 'InferredPresentation']
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name('NoCollision')
    component.set_editor_property('can_ever_affect_navigation', False)
    component.set_editor_property('cast_shadow', False)
    component.set_editor_property('affect_distance_field_lighting', False)
    actor.set_editor_property('is_spatially_loaded', False)
    bounds_origin, bounds_extent = actor.get_actor_bounds(False)
    assert levels.save_current_level()
    package = actor.get_package().get_name() if actor.get_package() else ''
    report = dict(asset=asset, fbx=tile['fbx'], fbx_sha256=tile['fbx_sha256'], source_triangles=tile['triangle_count'],
                  nanite_fallback_triangles=fallback_triangles, bound_error_cm=bound_error,
                  material=material.get_path_name(), nanite_fallback_percent_triangles=0.1,
                  distance_field=distance_field, actor_label=LABEL, actor_package=package,
                  actor_translation_cm=t, actor_scale=tile['actor_scale'], always_loaded=True, collision=False,
                  cast_shadow=False, bounds_origin_cm=[bounds_origin.x, bounds_origin.y, bounds_origin.z],
                  bounds_extent_cm=[bounds_extent.x, bounds_extent.y, bounds_extent.z],
                  source_manifest=str(export_path.relative_to(ROOT).as_posix()))
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    unreal.log('RAFTSIM_TERRAIN_BACKDROP_INSTALLED ' + json.dumps(dict(triangles=report['source_triangles'], package=package)))


if __name__ == '__main__':
    main()
