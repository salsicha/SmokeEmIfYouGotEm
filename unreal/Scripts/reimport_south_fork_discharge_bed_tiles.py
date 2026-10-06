"""Re-import rebuilt South Fork terrain tiles in place (discharge-consistent bed).

Input: the Blender export manifest written by export_south_fork_composite_tiles.py
for the changed-tile manifest of prepare_south_fork_discharge_bed_tiles.py.
Each existing static mesh keeps its package path, so the 443 placed ground
actors keep their references and material overrides. Import options, CPU
access, complex-as-simple collision, section collision and Nanite settings
match import_south_fork_composite_tiles.py; the mesh's existing material slot
is restored. Collision is traced on a temporary actor in the test-tank level
(the map is not modified) and must hit every probe within 0.1 cm.

Environment: RAFTSIM_TILE_EXPORT (repo-relative export manifest),
RAFTSIM_TILE_ASSETS (asset folder), RAFTSIM_TILE_REPORT (fresh tmp JSON).
"""
import hashlib
import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    source_path = ROOT / os.environ['RAFTSIM_TILE_EXPORT']
    assets = os.environ.get('RAFTSIM_TILE_ASSETS', '/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/Tiles')
    report_path = ROOT / os.environ['RAFTSIM_TILE_REPORT']
    assert report_path.is_relative_to(ROOT / 'tmp') and not report_path.exists()
    source = json.loads(source_path.read_text())
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ignore = list(actors.get_all_level_actors())
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
    actor.set_actor_scale3d(unreal.Vector(1, -1, 1))
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
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
    rows = []
    for index, tile in enumerate(source['tiles']):
        asset = assets + '/' + tile['asset_name']
        asset_file = ROOT / 'unreal/Content' / (asset.removeprefix('/Game/') + '.uasset')
        assert unreal.EditorAssetLibrary.does_asset_exist(asset), f'Missing existing tile {asset}'
        before = sha(asset_file)
        old = unreal.load_asset(asset)
        material = old.get_material(0)
        assert old.get_num_triangles(0) == tile['triangle_count'], 'Topology must be unchanged'
        assert sha(ROOT / tile['fbx']) == tile['fbx_sha256']
        task = unreal.AssetImportTask()
        task.filename = str(ROOT / tile['fbx'])
        task.destination_path, task.destination_name = assets, tile['asset_name']
        task.automated = True
        task.replace_existing = True
        task.replace_existing_settings = False
        task.save = False
        task.factory, task.options = unreal.FbxFactory(), options
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        mesh = unreal.load_asset(asset)
        assert isinstance(mesh, unreal.StaticMesh)
        mesh.set_editor_property('allow_cpu_access', True)
        mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        editor.enable_section_collision(mesh, True, 0, 0)
        settings = editor.get_nanite_settings(mesh)
        settings.enabled = True
        settings.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
        settings.fallback_percent_triangles = 1.
        settings.fallback_relative_error = 0.
        editor.set_nanite_settings(mesh, settings)
        if material:
            mesh.set_material(0, material)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert mesh.get_num_triangles(0) == tile['triangle_count']
        bounds = mesh.get_bounding_box()
        actual = [[bounds.min.x, bounds.min.y, bounds.min.z], [bounds.max.x, bounds.max.y, bounds.max.z]]
        bound_error = max(abs(actual[i][j] - tile['expected_unreal_bounds_cm'][i][j]) for i in range(2) for j in range(3))
        assert bound_error < .1, f'{asset} bounds differ by {bound_error} cm'
        translation = unreal.Vector(*tile['actor_translation_cm'])
        actor.set_actor_location(translation, False, False)
        actor.static_mesh_component.set_static_mesh(mesh)
        errors = []
        for point in tile['local_engine_collision_probes_cm']:
            query = unreal.Vector(*point) + translation
            hit = unreal.SystemLibrary.line_trace_single(world, query + unreal.Vector(0, 0, 1000), query - unreal.Vector(0, 0, 1000),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore, unreal.DrawDebugTrace.NONE, False)
            values = hit.to_tuple() if hit else None
            assert values and values[0], f'Missing tile collision {asset} {point}'
            error = abs(values[5].z - query.z)
            assert error < .1, f'Tile collision error {asset} {error} cm'
            errors.append(error)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        rows.append(dict(asset=asset, asset_sha256_before=before, asset_sha256_after=sha(asset_file), fbx_sha256=tile['fbx_sha256'],
                         triangle_count=mesh.get_num_triangles(0), bounds_error_cm=bound_error,
                         collision_probe_count=len(errors), maximum_collision_error_cm=max(errors)))
        if index % 20 == 0:
            unreal.log(f'Re-imported discharge-bed tile {index + 1}/{len(source["tiles"])}')
    actors.destroy_actor(actor)
    report = dict(schema='raftsim.south_fork.discharge_bed_tile_reimport.v1', export_manifest=source_path.relative_to(ROOT).as_posix(),
                  export_manifest_sha256=sha(source_path), tiles=rows, tile_count=len(rows),
                  maximum_collision_error_cm=max(r['maximum_collision_error_cm'] for r in rows) if rows else None,
                  map_modified=False, completed=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    unreal.log('RAFTSIM_DISCHARGE_BED_TILES_REIMPORTED ' + json.dumps(dict(tiles=len(rows), max_error_cm=report['maximum_collision_error_cm'])))


if __name__ == '__main__':
    main()
