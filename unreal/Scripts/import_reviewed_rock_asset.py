"""Import the rights-reviewed Poly Haven mossy rock set into an isolated UE folder."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import traceback

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_reviewed_biome_asset import (
    configure_existing_sampler_types,
    import_tasks,
    sha256,
    texture_sample,
)


ASSET_ID = "polyhaven_rock_moss_set_01_1k"
DESTINATION = "/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockMossSet01_1K"
SOURCE_FILES = {
    "rock_moss_set_01_1k.fbx": "8fa2a2666ecc4591f59e1d45db05d86857115b55492c8522917f3de5e650e6f9",
    "textures/rock_moss_set_01_diff_1k.jpg": "40cea65d8aa4ee73a93b04af19963834d061eee9779c3fc2c1cba76eef812ccc",
    "textures/rock_moss_set_01_nor_gl_1k.exr": "d86555deabb910ed82b2b770d852ba5aa931d373689ff7ae028574c7b310be99",
    "textures/rock_moss_set_01_rough_1k.jpg": "4d6ec46623abd8e2cdb855f59c7ce31873ad61b36b60e4de579e9e776a497c6b",
}
TEXTURE_NAMES = {
    "textures/rock_moss_set_01_diff_1k.jpg": "T_RockMossSet01_BaseColor_1K",
    "textures/rock_moss_set_01_nor_gl_1k.exr": "T_RockMossSet01_NormalGL_1K",
    "textures/rock_moss_set_01_rough_1k.jpg": "T_RockMossSet01_Roughness_1K",
}


def verify_source(root: Path) -> list[dict[str, object]]:
    verified = []
    for relative_path, expected_hash in SOURCE_FILES.items():
        path = root / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Missing reviewed source file: {path}")
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"Hash mismatch for {relative_path}: expected {expected_hash}, got {actual_hash}"
            )
        verified.append(
            {"relative_path": relative_path, "sha256": actual_hash, "bytes": path.stat().st_size}
        )
    return verified


def import_meshes(source_root: Path) -> list[unreal.StaticMesh]:
    existing = [
        unreal.load_asset(path)
        for path in unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=False)
    ]
    existing_meshes = [asset for asset in existing if isinstance(asset, unreal.StaticMesh)]
    if existing_meshes:
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
    task.filename = str(source_root / "rock_moss_set_01_1k.fbx")
    task.destination_path = DESTINATION
    task.destination_name = "SM_RockMossSet01"
    task.replace_existing = False
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    imported_paths = import_tasks([task])
    meshes = [unreal.load_asset(path) for path in imported_paths]
    meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    if len(meshes) != 6:
        raise RuntimeError(f"Expected six rock meshes, imported {len(meshes)}: {imported_paths}")
    return meshes


def import_textures(source_root: Path) -> dict[str, unreal.Texture2D]:
    textures: dict[str, unreal.Texture2D] = {}
    tasks = []
    task_keys = []
    for relative_path, asset_name in TEXTURE_NAMES.items():
        existing = unreal.load_asset(f"{DESTINATION}/{asset_name}")
        if isinstance(existing, unreal.Texture2D):
            textures[relative_path] = existing
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
        texture.set_editor_property("srgb", "_diff_" in relative_path)
        if "_nor_gl_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP
            )
            texture.set_editor_property("flip_green_channel", True)
        elif "_rough_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
            )
        texture.modify()
    return textures


def load_or_create_material(textures: dict[str, unreal.Texture2D]) -> unreal.Material:
    name = "M_RockMossSet01_ReviewLit"
    existing = unreal.load_asset(f"{DESTINATION}/{name}")
    if isinstance(existing, unreal.Material):
        configure_existing_sampler_types(existing)
        existing.modify()
        unreal.MaterialEditingLibrary.recompile_material(existing)
        return existing

    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, DESTINATION, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create {DESTINATION}/{name}")
    base = texture_sample(
        material,
        textures["textures/rock_moss_set_01_diff_1k.jpg"],
        -640,
        -120,
        unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    )
    normal = texture_sample(
        material,
        textures["textures/rock_moss_set_01_nor_gl_1k.exr"],
        -640,
        80,
        unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    )
    roughness = texture_sample(
        material,
        textures["textures/rock_moss_set_01_rough_1k.jpg"],
        -640,
        280,
        unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    )
    base_color_scale = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -360, -160
    )
    base_color_scale.r = 1.15
    scaled_base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -120, -120
    )
    ambient_fill_scale = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -360, 430
    )
    ambient_fill_scale.r = 0.08
    ambient_fill = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -120, 420
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(base, "RGB", scaled_base, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        base_color_scale, "", scaled_base, "B"
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(base, "RGB", ambient_fill, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(
        ambient_fill_scale, "", ambient_fill, "B"
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        scaled_base, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        normal, "RGB", unreal.MaterialProperty.MP_NORMAL
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness, "R", unreal.MaterialProperty.MP_ROUGHNESS
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        ambient_fill, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    material.set_editor_property("two_sided", False)
    material.modify()
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    return material


def configure_meshes(
    meshes: list[unreal.StaticMesh], material: unreal.Material
) -> list[dict[str, object]]:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not subsystem:
        raise RuntimeError("StaticMeshEditorSubsystem is unavailable")
    records = []
    for mesh in sorted(meshes, key=lambda asset: asset.get_name()):
        bounds = mesh.get_bounding_box()
        raw_max_dimension = max(
            bounds.max.x - bounds.min.x,
            bounds.max.y - bounds.min.y,
            bounds.max.z - bounds.min.z,
        )
        build_settings = subsystem.get_lod_build_settings(mesh, 0)
        if raw_max_dimension < 20.0 and build_settings.build_scale3d.z < 99.0:
            build_settings.build_scale3d = unreal.Vector(100.0, 100.0, 100.0)
            subsystem.set_lod_build_settings(mesh, 0, build_settings)

        nanite_settings = subsystem.get_nanite_settings(mesh)
        nanite_settings.enabled = True
        subsystem.set_nanite_settings(mesh, nanite_settings)
        for slot_index in range(len(mesh.static_materials)):
            mesh.set_material(slot_index, material)
        mesh.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

        persisted = subsystem.get_lod_build_settings(mesh, 0)
        bounds = mesh.get_bounding_box()
        scale = persisted.build_scale3d.z if max(
            bounds.max.x - bounds.min.x,
            bounds.max.y - bounds.min.y,
            bounds.max.z - bounds.min.z,
        ) < 20.0 else 1.0
        dimensions_cm = [
            (bounds.max.x - bounds.min.x) * scale,
            (bounds.max.y - bounds.min.y) * scale,
            (bounds.max.z - bounds.min.z) * scale,
        ]
        record = {
            "asset_path": mesh.get_path_name(),
            "nanite_fallback_triangle_count_lod0": mesh.get_num_triangles(0),
            "dimensions_cm": dimensions_cm,
            "base_z_cm": bounds.min.z * scale,
            "lod0_build_scale": [
                persisted.build_scale3d.x,
                persisted.build_scale3d.y,
                persisted.build_scale3d.z,
            ],
            "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
            "material_slot_count": len(mesh.static_materials),
            "material": material.get_path_name(),
        }
        if not (15.0 <= max(dimensions_cm) <= 500.0):
            raise RuntimeError(
                "Rock candidate failed the 0.15-5.0 m physical-size gate: "
                + json.dumps(record, sort_keys=True)
            )
        if record["material_slot_count"] < 1:
            raise RuntimeError("Rock candidate has no material slot: " + json.dumps(record))
        records.append(record)
    return records


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_REVIEWED_ROCK_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir()) / "RaftSim" / "reviewed_rock_import.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed rock import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_environment_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        root_text = os.environ.get("RAFTSIM_REVIEWED_ROCK_SOURCE_ROOT", "").strip()
        if not root_text:
            raise RuntimeError("RAFTSIM_REVIEWED_ROCK_SOURCE_ROOT is required")
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        meshes = import_meshes(source_root)
        textures = import_textures(source_root)
        material = load_or_create_material(textures)
        for asset in [*textures.values(), material]:
            unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        report["meshes"] = configure_meshes(meshes, material)
        report["textures"] = sorted(texture.get_path_name() for texture in textures.values())
        report["materials"] = [material.get_path_name()]
        report["status"] = "isolated_review_candidate_imported"
        write_report(report)
        unreal.log(f"RaftSim imported reviewed rock candidate {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
