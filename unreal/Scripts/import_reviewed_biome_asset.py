"""Import the rights-reviewed Poly Haven fir candidate into an isolated UE folder.

Run this through UnrealEditor-Cmd with -ExecutePythonScript. The source bundle is
kept outside the repository and selected with RAFTSIM_REVIEWED_BIOME_SOURCE_ROOT.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import traceback

import unreal


ASSET_ID = "polyhaven_fir_tree_01_1k"
DESTINATION = "/Game/RaftSim/Environment/ExternalReview/PolyHaven/FirTree01_1K"
SOURCE_FILES = {
    "fir_tree_01_1k.fbx": "281d26c46e97df3fa803f8ef0fc17c6bccf8b6f6868c093a62e032f259a16438",
    "textures/fir_tree_01_bark_diff_1k.png": "508ca0a40d118beec98e8375b4611e8a16123eec94b5d2b4870617cf4d24e6fa",
    "textures/fir_tree_01_bark_disp_1k.png": "ab08f400d208487b7bfd5d9cd4386456ed8e5fbcfdd045eca1705e3ed4b3dab8",
    "textures/fir_tree_01_bark_nor_gl_1k.png": "b889e7080d6efb0592f83e64cc5a5afa5fb7787b4b7d1ae13a65602689e793e8",
    "textures/fir_tree_01_bark_rough_1k.png": "b198105d3022db6c459ae9c307ecdb7b644832ee20bcbfd89c3741cecc77881f",
    "textures/fir_tree_01_twig_alpha_1k.png": "3f399629337e7ac3af27a01b08ffb9c0d60224a9dd374a1427761a5c2eea9d6e",
    "textures/fir_tree_01_twig_diff_1k.png": "76f6d0c0044d76bac08fbbd3d2ac1c9b66bb046de7d0b1a22aa9b319308f3833",
    "textures/fir_tree_01_twig_nor_gl_1k.png": "cbb6b8179a9f7f6e84fd15d1f422bc342841d20845b2bad437612f03fb0067de",
    "textures/fir_tree_01_twig_rough_1k.png": "a4f0a4c8bc93946dea229def779ffe5d32c555c717e4bf7b0e4b4d86bc21987a",
}
TEXTURE_NAMES = {
    "textures/fir_tree_01_bark_diff_1k.png": "T_FirTree01_Bark_BaseColor_1K",
    "textures/fir_tree_01_bark_disp_1k.png": "T_FirTree01_Bark_Displacement_1K",
    "textures/fir_tree_01_bark_nor_gl_1k.png": "T_FirTree01_Bark_NormalGL_1K",
    "textures/fir_tree_01_bark_rough_1k.png": "T_FirTree01_Bark_Roughness_1K",
    "textures/fir_tree_01_twig_alpha_1k.png": "T_FirTree01_Twig_Opacity_1K",
    "textures/fir_tree_01_twig_diff_1k.png": "T_FirTree01_Twig_BaseColor_1K",
    "textures/fir_tree_01_twig_nor_gl_1k.png": "T_FirTree01_Twig_NormalGL_1K",
    "textures/fir_tree_01_twig_rough_1k.png": "T_FirTree01_Twig_Roughness_1K",
}
SOURCE_TRIANGLE_COUNTS = {
    "_a_LOD0": 4176819,
    "_b_LOD0": 2300624,
    "_c_LOD0": 505494,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source(root: Path) -> list[dict[str, object]]:
    verified = []
    for relative_path, expected_sha256 in SOURCE_FILES.items():
        path = root / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Missing reviewed source file: {path}")
        actual_sha256 = sha256(path)
        if actual_sha256 != expected_sha256:
            raise RuntimeError(
                f"Hash mismatch for {relative_path}: expected {expected_sha256}, got {actual_sha256}"
            )
        verified.append(
            {
                "relative_path": relative_path,
                "sha256": actual_sha256,
                "bytes": path.stat().st_size,
            }
        )
    return verified


def import_tasks(tasks: list[unreal.AssetImportTask]) -> list[str]:
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    imported_paths = []
    for task in tasks:
        imported_paths.extend(str(path) for path in task.imported_object_paths)
    return imported_paths


def import_meshes(source_root: Path) -> list[unreal.StaticMesh]:
    force_reimport = os.environ.get("RAFTSIM_REVIEWED_BIOME_REIMPORT", "0") == "1"
    existing_paths = unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=False)
    existing_meshes = [
        unreal.load_asset(path)
        for path in existing_paths
        if isinstance(unreal.load_asset(path), unreal.StaticMesh)
    ]
    if existing_meshes and not force_reimport:
        return existing_meshes

    options = unreal.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_mesh = True
    options.import_as_skeletal = False
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.original_import_type = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials = False
    options.import_textures = False
    options.import_animations = False
    options.static_mesh_import_data.combine_meshes = False
    options.static_mesh_import_data.generate_lightmap_u_vs = True
    options.static_mesh_import_data.remove_degenerates = True
    options.static_mesh_import_data.transform_vertex_to_absolute = False
    options.static_mesh_import_data.bake_pivot_in_vertex = True

    task = unreal.AssetImportTask()
    task.filename = str(source_root / "fir_tree_01_1k.fbx")
    task.destination_path = DESTINATION
    task.destination_name = "SM_FirTree01"
    task.replace_existing = force_reimport
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    imported_paths = import_tasks([task])
    meshes = [unreal.load_asset(path) for path in imported_paths]
    meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    if len(meshes) != 3:
        raise RuntimeError(f"Expected three fir meshes, imported {len(meshes)}: {imported_paths}")
    return meshes


def import_textures(source_root: Path) -> dict[str, unreal.Texture2D]:
    textures = {}
    tasks = []
    task_keys = []
    for relative_path, asset_name in TEXTURE_NAMES.items():
        asset_path = f"{DESTINATION}/{asset_name}"
        texture = unreal.load_asset(asset_path)
        if isinstance(texture, unreal.Texture2D):
            textures[relative_path] = texture
            continue
        task = unreal.AssetImportTask()
        task.filename = str(source_root / relative_path)
        task.destination_path = DESTINATION
        task.destination_name = asset_name
        task.replace_existing = False
        task.automated = True
        task.save = False
        tasks.append(task)
        task_keys.append(relative_path)

    if tasks:
        import_tasks(tasks)
        for relative_path, task in zip(task_keys, tasks):
            imported_paths = list(task.imported_object_paths)
            if len(imported_paths) != 1:
                raise RuntimeError(f"Texture import for {relative_path} produced {imported_paths}")
            texture = unreal.load_asset(imported_paths[0])
            if not isinstance(texture, unreal.Texture2D):
                raise RuntimeError(f"Imported object is not Texture2D: {imported_paths[0]}")
            textures[relative_path] = texture

    for relative_path, texture in textures.items():
        texture.set_editor_property("srgb", relative_path.endswith("_diff_1k.png"))
        if "_nor_gl_" in relative_path:
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            texture.set_editor_property("flip_green_channel", True)
        elif "_rough_" in relative_path or "_alpha_" in relative_path or "_disp_" in relative_path:
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        texture.modify()
    return textures


def texture_sample(
    material: unreal.Material,
    texture: unreal.Texture2D,
    x: int,
    y: int,
    sampler_type: unreal.MaterialSamplerType,
) -> unreal.MaterialExpressionTextureSample:
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, x, y
    )
    expression.texture = texture
    expression.sampler_type = sampler_type
    return expression


def configure_existing_sampler_types(material: unreal.Material) -> None:
    material.modify()
    for expression in unreal.MaterialEditingLibrary.get_material_expressions(material):
        if not isinstance(expression, unreal.MaterialExpressionTextureSample):
            continue
        texture = expression.texture
        if not texture:
            continue
        texture_name = texture.get_name().lower()
        expression.modify()
        if "normalgl" in texture_name or "norgl" in texture_name or "normal" in texture_name:
            expression.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
        elif (
            "roughness" in texture_name
            or "rough" in texture_name
            or "opacity" in texture_name
            or "alpha" in texture_name
            or "displacement" in texture_name
        ):
            expression.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
        else:
            expression.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_COLOR


def load_or_create_material(
    name: str,
    textures: dict[str, unreal.Texture2D],
    foliage: bool,
) -> unreal.Material:
    asset_path = f"{DESTINATION}/{name}"
    existing = unreal.load_asset(asset_path)
    if isinstance(existing, unreal.Material):
        configure_existing_sampler_types(existing)
        existing.modify()
        unreal.MaterialEditingLibrary.recompile_material(existing)
        return existing

    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, DESTINATION, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create material {asset_path}")

    prefix = "textures/fir_tree_01_twig" if foliage else "textures/fir_tree_01_bark"
    base_color = texture_sample(
        material,
        textures[f"{prefix}_diff_1k.png"],
        -640,
        -140,
        unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    )
    normal = texture_sample(
        material,
        textures[f"{prefix}_nor_gl_1k.png"],
        -640,
        40,
        unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    )
    roughness = texture_sample(
        material,
        textures[f"{prefix}_rough_1k.png"],
        -640,
        220,
        unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        base_color, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        normal, "RGB", unreal.MaterialProperty.MP_NORMAL
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness, "R", unreal.MaterialProperty.MP_ROUGHNESS
    )

    if foliage:
        opacity = texture_sample(
            material,
            textures["textures/fir_tree_01_twig_alpha_1k.png"],
            -640,
            400,
            unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            opacity, "R", unreal.MaterialProperty.MP_OPACITY_MASK
        )
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        material.set_editor_property("two_sided", True)
        material.set_editor_property(
            "shading_model", unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE
        )
        material.set_editor_property("opacity_mask_clip_value", 0.34)

    material.modify()
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    return material


def configure_meshes(
    meshes: list[unreal.StaticMesh],
    bark_material: unreal.Material,
    twig_material: unreal.Material,
) -> list[dict[str, object]]:
    records = []
    static_mesh_editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not static_mesh_editor:
        raise RuntimeError("StaticMeshEditorSubsystem is unavailable")
    for mesh in sorted(meshes, key=lambda item: item.get_name()):
        initial_bounds = mesh.get_bounding_box()
        initial_height_cm = initial_bounds.max.z - initial_bounds.min.z
        build_settings = static_mesh_editor.get_lod_build_settings(mesh, 0)
        build_scale_applied = False
        if initial_height_cm < 100.0 and build_settings.build_scale3d.z < 99.0:
            build_settings.build_scale3d = unreal.Vector(100.0, 100.0, 100.0)
            static_mesh_editor.set_lod_build_settings(mesh, 0, build_settings)
            build_scale_applied = True

        nanite_settings = mesh.get_editor_property("nanite_settings")
        nanite_settings.enabled = True
        mesh.set_editor_property("nanite_settings", nanite_settings)

        slot_records = []
        for slot_index, static_material in enumerate(mesh.static_materials):
            slot_name = str(static_material.material_slot_name)
            material = twig_material if "twig" in slot_name.lower() else bark_material
            mesh.set_material(slot_index, material)
            slot_records.append(
                {
                    "index": slot_index,
                    "slot_name": slot_name,
                    "material": material.get_path_name(),
                }
            )
        mesh.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        bounds = mesh.get_bounding_box()
        persisted_build_settings = static_mesh_editor.get_lod_build_settings(mesh, 0)
        raw_height = bounds.max.z - bounds.min.z
        bounds_scale = persisted_build_settings.build_scale3d.z if raw_height < 100.0 else 1.0
        center_x = (bounds.min.x + bounds.max.x) * 0.5 * bounds_scale
        center_y = (bounds.min.y + bounds.max.y) * 0.5 * bounds_scale
        extent_x = (bounds.max.x - bounds.min.x) * 0.5 * bounds_scale
        extent_y = (bounds.max.y - bounds.min.y) * 0.5 * bounds_scale
        height_cm = raw_height * bounds_scale
        pivot_offset_xy_cm = (center_x * center_x + center_y * center_y) ** 0.5
        pivot_tolerance_cm = max(25.0, max(extent_x, extent_y) * 0.2)
        source_triangle_count = next(
            count for suffix, count in SOURCE_TRIANGLE_COUNTS.items() if suffix in mesh.get_name()
        )
        records.append(
            {
                "asset_path": mesh.get_path_name(),
                "source_triangle_count_lod0": source_triangle_count,
                "nanite_fallback_triangle_count_lod0": mesh.get_num_triangles(0),
                "bounds_cm": {
                    "min": [
                        bounds.min.x * bounds_scale,
                        bounds.min.y * bounds_scale,
                        bounds.min.z * bounds_scale,
                    ],
                    "max": [
                        bounds.max.x * bounds_scale,
                        bounds.max.y * bounds_scale,
                        bounds.max.z * bounds_scale,
                    ],
                },
                "raw_bounds_to_effective_scale": bounds_scale,
                "instance_pivot": {
                    "xy_offset_cm": pivot_offset_xy_cm,
                    "tolerance_cm": pivot_tolerance_cm,
                    "centered_for_instancing": pivot_offset_xy_cm <= pivot_tolerance_cm,
                },
                "physical_scale": {
                    "height_cm": height_cm,
                    "plausible_tree_height": 1000.0 <= height_cm <= 2500.0,
                    "lod0_build_scale_applied": build_scale_applied,
                    "lod0_build_scale": [
                        persisted_build_settings.build_scale3d.x,
                        persisted_build_settings.build_scale3d.y,
                        persisted_build_settings.build_scale3d.z,
                    ],
                },
                "nanite_enabled": mesh.get_editor_property("nanite_settings").enabled,
                "material_slots": slot_records,
            }
        )
    return records


def write_report(report: dict[str, object]) -> None:
    report_path_text = os.environ.get("RAFTSIM_REVIEWED_BIOME_REPORT_PATH", "").strip()
    if not report_path_text:
        report_path = Path(unreal.Paths.project_saved_dir()) / "RaftSim" / "reviewed_biome_import.json"
    else:
        report_path = Path(report_path_text).expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed biome import report: {report_path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_biome_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        source_root_text = os.environ.get("RAFTSIM_REVIEWED_BIOME_SOURCE_ROOT", "").strip()
        if not source_root_text:
            raise RuntimeError("RAFTSIM_REVIEWED_BIOME_SOURCE_ROOT is required")
        source_root = Path(source_root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        meshes = import_meshes(source_root)
        textures = import_textures(source_root)
        bark_material = load_or_create_material("M_FirTree01_Bark", textures, foliage=False)
        twig_material = load_or_create_material("M_FirTree01_Needles", textures, foliage=True)
        for asset in [*textures.values(), bark_material, twig_material]:
            unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        report["meshes"] = configure_meshes(meshes, bark_material, twig_material)
        if not all(record["instance_pivot"]["centered_for_instancing"] for record in report["meshes"]):
            raise RuntimeError("One or more imported fir meshes retained an off-center shared FBX pivot")
        if not all(record["physical_scale"]["plausible_tree_height"] for record in report["meshes"]):
            raise RuntimeError("One or more imported fir meshes failed the 10-25 m physical-height gate")
        report["textures"] = sorted(texture.get_path_name() for texture in textures.values())
        report["materials"] = [bark_material.get_path_name(), twig_material.get_path_name()]
        report["status"] = "isolated_review_candidate_imported"
        report["selection_for_first_visual_review"] = next(
            (
                record["asset_path"]
                for record in report["meshes"]
                if "_a_LOD0" in record["asset_path"]
            ),
            report["meshes"][0]["asset_path"],
        )
        write_report(report)
        unreal.log(f"RaftSim imported reviewed biome candidate {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
