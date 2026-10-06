"""Import the Hance 3DEP terrain backdrop: mesh, colour drape and material.

Inputs: the FBX export folder written by export_colorado_hance_backdrop_fbx.py
(RAFTSIM_HANCE_BACKDROP_EXPORT, repo-relative manifest.json) and the drape
PNG it names. Creates under /Game/RaftSim/Environment/ColoradoRun/Terrain:
  T_RaftSim_ColoradoHance_BackdropDrape   sRGB, clamped, world group
  M_RaftSim_ColoradoHance_Backdrop        opaque default-lit; base colour from
                                          the drape at world-position UVs
                                          (the manifest's drape_uv), no WPO
  SM_RaftSim_ColoradoHance_3DEPBackdrop   Nanite, no collision, no distance field
The map builder (RaftSim.CreateLandscapeImportCandidateMaps colorado_river)
places the mesh; this script saves only these three assets. Re-running
replaces them in place. Report: RAFTSIM_HANCE_BACKDROP_REPORT (fresh repo tmp JSON).
"""
import hashlib
import json
import os
import re
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
DEST = '/Game/RaftSim/Environment/ColoradoRun/Terrain'
TEXTURE = DEST + '/T_RaftSim_ColoradoHance_BackdropDrape'
MATERIAL = DEST + '/M_RaftSim_ColoradoHance_Backdrop'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def import_texture(png):
    task = unreal.AssetImportTask()
    task.filename = str(png)
    task.destination_path, task.destination_name = DEST, TEXTURE.rsplit('/', 1)[1]
    task.automated, task.replace_existing, task.save = True, True, False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(TEXTURE)
    require(isinstance(texture, unreal.Texture2D), 'Backdrop drape import failed')
    texture.set_editor_property('srgb', True)
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_WORLD)
    texture.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
    require(unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False), 'Texture save failed')
    return texture


def build_material(texture, uv):
    # 'U = (world_x + A) / W cm; V = (world_y + B) / H cm'
    a, w, b, h = [float(v) for v in re.findall(r'[-0-9.]+', uv.replace('world_x', '').replace('world_y', ''))[:4]]
    mel = unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(MATERIAL):
        material = unreal.load_asset(MATERIAL)
        mel.delete_all_material_expressions(material)
    else:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            MATERIAL.rsplit('/', 1)[1], DEST, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    for usage in ('used_with_nanite', 'used_with_static_lighting'):
        try:
            material.set_editor_property(usage, True)
        except Exception:
            pass
    world = mel.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -1200, 0)
    mask = mel.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1000, 0)
    mask.set_editor_property('r', True); mask.set_editor_property('g', True)
    mask.set_editor_property('b', False); mask.set_editor_property('a', False)
    offset = mel.create_material_expression(material, unreal.MaterialExpressionConstant2Vector, -1000, 160)
    offset.set_editor_property('r', a); offset.set_editor_property('g', b)
    add = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -800, 0)
    size = mel.create_material_expression(material, unreal.MaterialExpressionConstant2Vector, -800, 160)
    size.set_editor_property('r', w); size.set_editor_property('g', h)
    div = mel.create_material_expression(material, unreal.MaterialExpressionDivide, -600, 0)
    sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -400, 0)
    sample.set_editor_property('texture', texture)
    sample.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 260)
    rough.set_editor_property('r', 0.92)
    spec = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 340)
    spec.set_editor_property('r', 0.35)
    require(mel.connect_material_expressions(world, '', mask, ''), 'connect world')
    require(mel.connect_material_expressions(mask, '', add, 'A'), 'connect mask')
    require(mel.connect_material_expressions(offset, '', add, 'B'), 'connect offset')
    require(mel.connect_material_expressions(add, '', div, 'A'), 'connect add')
    require(mel.connect_material_expressions(size, '', div, 'B'), 'connect size')
    require(mel.connect_material_expressions(div, '', sample, 'UVs'), 'connect uv')
    require(mel.connect_material_property(sample, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR), 'base colour')
    require(mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS), 'roughness')
    require(mel.connect_material_property(spec, '', unreal.MaterialProperty.MP_SPECULAR), 'specular')
    mel.recompile_material(material)
    require(unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False), 'Material save failed')
    return material, dict(u_offset_cm=a, u_span_cm=w, v_offset_cm=b, v_span_cm=h)


def import_mesh(export, material):
    fbx = ROOT / export['fbx']
    require(sha(fbx) == export['fbx_sha256'], 'FBX differs from its export manifest')
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
    task.destination_path, task.destination_name = DEST, export['asset_name']
    task.automated, task.replace_existing, task.save = True, True, False
    task.factory, task.options = unreal.FbxFactory(), options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(DEST + '/' + export['asset_name'])
    require(isinstance(mesh, unreal.StaticMesh), 'Backdrop mesh import failed')
    # The editor subsystem is absent under -run=pythonscript; the static
    # library and the mesh's own property work in both contexts.
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem) or unreal.EditorStaticMeshLibrary
    settings = mesh.get_editor_property('nanite_settings')
    settings.enabled = True
    settings.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
    settings.fallback_percent_triangles = 0.1
    try:
        editor.set_nanite_settings(mesh, settings, apply_changes=True)
    except Exception:
        mesh.set_editor_property('nanite_settings', settings)
    try:
        editor.remove_collisions(mesh)
    except Exception:
        pass
    distance_field = 'unchanged'
    try:
        build = editor.get_lod_build_settings(mesh, 0)
        build.set_editor_property('distance_field_resolution_scale', 0.0)
        editor.set_lod_build_settings(mesh, 0, build)
        distance_field = 'disabled'
    except Exception as error:
        distance_field = 'unchanged: ' + str(error)[:120]

    mesh.set_material(0, material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    box = mesh.get_bounding_box()
    actual = [[box.min.x, box.min.y, box.min.z], [box.max.x, box.max.y, box.max.z]]
    expected = export['expected_mesh_bounds_cm']
    bound_error = max(abs(actual[i][j] - expected[i][j]) for i in range(2) for j in range(3))
    require(bound_error < 1.0, 'Backdrop bounds differ from the export: %s vs %s' % (actual, expected))
    require(unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), 'Mesh save failed')
    return mesh, dict(bound_error_cm=bound_error, fallback_triangles=mesh.get_num_triangles(0), distance_field=distance_field)


def main():
    export_path = ROOT / os.environ['RAFTSIM_HANCE_BACKDROP_EXPORT']
    report_path = ROOT / os.environ['RAFTSIM_HANCE_BACKDROP_REPORT']
    require(report_path.is_relative_to(ROOT / 'tmp') and not report_path.exists(), 'fresh tmp report path required')
    export = json.loads(export_path.read_text())
    drape = ROOT / export['drape']
    require(sha(drape) == export['drape_sha256'], 'Backdrop drape differs from its export manifest')
    texture = import_texture(drape)
    material, uv = build_material(texture, export['drape_uv'])
    mesh, mesh_report = import_mesh(export, material)
    report = dict(export=export_path.relative_to(ROOT).as_posix(), texture=texture.get_path_name(),
                  material=material.get_path_name(), mesh=mesh.get_path_name(), uv=uv,
                  source_triangles=export['triangle_count'], **mesh_report)
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    unreal.log('RAFTSIM_HANCE_BACKDROP_INSTALLED ' + json.dumps(report))


main()
