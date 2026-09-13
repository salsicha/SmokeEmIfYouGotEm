"""Import and collision-check all source-exact full-river terrain tiles.

Saves only new terrain assets, with per-tile resumable evidence. No map is saved.
"""
import hashlib
import json
from pathlib import Path
import shutil
import unreal

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'unreal/SourceArt/RaftSim/SouthForkCompositeTerrain20260912/Tiles/manifest.json'
ASSETS = '/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/Tiles'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-composite-tiles-20260912.json'
PAUSE_REQUEST = ROOT/'unreal/Saved/RaftSimValidation/south-fork-composite-tiles.pause'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(source_path=SOURCE, asset_directory=ASSETS, report_path=REPORT,
         pause_request=PAUSE_REQUEST,
         material_path='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/MI_TroublemakerGround'):
    SOURCE, ASSETS, REPORT, PAUSE_REQUEST = source_path, asset_directory, report_path, pause_request
    source = json.loads(SOURCE.read_text())
    if REPORT.exists():
        report = json.loads(REPORT.read_text())
        assert report['source_export_manifest_sha256'] == sha(SOURCE)
    else:
        report = dict(source_export_manifest_sha256=sha(SOURCE), tiles=[], completed=False,
            normal_map_integrated=False, source_material_world_frame_review_pending=True)
    previous = {row['asset']: row for row in report['tiles']}
    report.pop('pause_reason', None)
    report['material'] = material_path
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    assert editor, 'Requires full editor, not -run=pythonscript commandlet'
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    tank_file = ROOT/'unreal/Content/RaftSim/Maps/L_RaftSimTestTank.umap'
    before = sha(tank_file)
    assert levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ignore = list(actors.get_all_level_actors())
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
    actor.set_actor_scale3d(unreal.Vector(1, -1, 1))
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
    material = unreal.load_asset(material_path)
    assert material
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
    for index, tile in enumerate(source['tiles']):
        asset = ASSETS+'/'+tile['asset_name']
        asset_file = ROOT/'unreal/Content'/(asset.removeprefix('/Game/')+'.uasset')
        if asset in previous:
            assert sha(asset_file) == previous[asset]['asset_sha256']
            assert previous[asset]['fbx_sha256'] == tile['fbx_sha256']
            continue
        if PAUSE_REQUEST.exists() or shutil.disk_usage(ROOT).free < 4*1024**3:
            report['pause_reason'] = ('Explicit checkpoint pause requested' if PAUSE_REQUEST.exists()
                else 'Fewer than 4 GiB free; paused safely before the next asset')
            REPORT.write_text(json.dumps(report, indent=2)+'\n')
            raise RuntimeError(report['pause_reason'])
        assert not unreal.EditorAssetLibrary.does_asset_exist(asset), 'Unverified existing tile; do not overwrite'
        assert sha(ROOT/tile['fbx']) == tile['fbx_sha256']
        task = unreal.AssetImportTask()
        task.filename = str(ROOT/tile['fbx'])
        task.destination_path, task.destination_name = ASSETS, tile['asset_name']
        task.automated = True
        task.replace_existing = False
        task.save = False
        task.factory, task.options = unreal.FbxFactory(), options
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        mesh = unreal.load_asset(asset)
        assert isinstance(mesh, unreal.StaticMesh)
        bounds = mesh.get_bounding_box()
        actual = [[bounds.min.x, bounds.min.y, bounds.min.z], [bounds.max.x, bounds.max.y, bounds.max.z]]
        assert max(abs(actual[i][j]-tile['expected_unreal_bounds_cm'][i][j]) for i in range(2) for j in range(3)) < .1
        mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        editor.enable_section_collision(mesh, True, 0, 0)
        settings = editor.get_nanite_settings(mesh)
        settings.enabled = True
        settings.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
        settings.fallback_percent_triangles = 1.
        settings.fallback_relative_error = 0.
        editor.set_nanite_settings(mesh, settings)
        mesh.set_material(0, material)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert mesh.get_num_triangles(0) == tile['triangle_count']
        translation = unreal.Vector(*tile['actor_translation_cm'])
        actor.set_actor_location(translation, False, False)
        actor.static_mesh_component.set_static_mesh(mesh)
        errors = []
        for point in tile['local_engine_collision_probes_cm']:
            query = unreal.Vector(*point)+translation
            hit = unreal.SystemLibrary.line_trace_single(world, query+unreal.Vector(0, 0, 1000),
                query-unreal.Vector(0, 0, 1000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                False, ignore, unreal.DrawDebugTrace.NONE, False)
            values = hit.to_tuple() if hit else None
            assert values and values[0], f'Missing tile collision {asset} {point}'
            error = abs(values[5].z-query.z)
            assert error < .1, f'Tile collision error {asset} {error} cm'
            errors.append(error)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        row = dict(asset=asset, asset_sha256=sha(asset_file), fbx_sha256=tile['fbx_sha256'],
            triangle_count=mesh.get_num_triangles(0), collision_probe_count=len(errors),
            maximum_collision_error_cm=max(errors), actor_translation_cm=tile['actor_translation_cm'])
        report['tiles'].append(row)
        REPORT.write_text(json.dumps(report, indent=2)+'\n')
        if index % 25 == 0:
            unreal.log(f'Full-river source tiles verified {index+1}/{len(source["tiles"])}')
    assert actors.destroy_actor(actor)
    assert sha(tank_file) == before
    assert len(report['tiles']) == len(source['tiles'])
    report.update(completed=True, test_map_unchanged=True,
        total_triangle_count=sum(row['triangle_count'] for row in report['tiles']),
        collision_probe_count=sum(row['collision_probe_count'] for row in report['tiles']),
        maximum_collision_error_cm=max(row['maximum_collision_error_cm'] for row in report['tiles']))
    REPORT.write_text(json.dumps(report, indent=2)+'\n')
    unreal.log(f'Full-river source tile import complete: {REPORT}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
