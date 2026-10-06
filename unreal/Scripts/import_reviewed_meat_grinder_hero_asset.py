"""Import the rights-reviewed Meat Grinder hero boulder in isolation."""

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


ASSET_ID = "polyhaven_boulder_01_meat_grinder_hero_2k"
DESTINATION = "/Game/RaftSim/Environment/ExternalReview/PolyHaven/MeatGrinderHero_2K"
SOURCE_FILES = {
    "boulder_01_2k.gltf": "52d118b56748a18509e4ec0075d07b254d72a0401793f22363c0bb3a682e7361",
    "boulder_01.bin": "7f5b06503d62bd95bfe9c6b8a354a5cc8ff04a4d271a8cf87a3e3125db4232d7",
    "textures/boulder_01_diff_2k.jpg": "90bbaa17c1fe0254d2b0b6e5148264fa834953a72724d566f14af029eebe3ca3",
    "textures/boulder_01_nor_gl_2k.jpg": "5174b318712ac7725cbcb55d422607f9c66d7f8d035c5412ab897b5939e2db6b",
    "textures/boulder_01_arm_2k.jpg": "ab52859dde519b4822111aa60916b6d21f8a6966c67b6cec44d1cd0775b8a86a",
}
TEXTURES = {
    "textures/boulder_01_diff_2k.jpg": "T_Boulder01_BaseColor_2K",
    "textures/boulder_01_nor_gl_2k.jpg": "T_Boulder01_NormalGL_2K",
    "textures/boulder_01_arm_2k.jpg": "T_Boulder01_ARM_2K",
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


def import_textures(source_root: Path) -> dict[str, unreal.Texture2D]:
    textures: dict[str, unreal.Texture2D] = {}
    tasks: list[unreal.AssetImportTask] = []
    task_keys: list[str] = []
    for relative_path, asset_name in TEXTURES.items():
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
        elif "_arm_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
            )
        texture.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return textures


def load_or_create_material(textures: dict[str, unreal.Texture2D]) -> unreal.Material:
    name = "M_Boulder01_ReviewLit"
    existing = unreal.load_asset(f"{DESTINATION}/{name}")
    if isinstance(existing, unreal.Material):
        configure_existing_sampler_types(existing)
        unreal.MaterialEditingLibrary.set_base_material_usage(
            existing, unreal.MaterialUsage.MATUSAGE_NANITE, True
        )
        unreal.MaterialEditingLibrary.set_base_material_usage(
            existing,
            unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES,
            True,
        )
        existing.modify()
        unreal.MaterialEditingLibrary.recompile_material(existing)
        unreal.EditorAssetLibrary.save_loaded_asset(existing, only_if_is_dirty=False)
        return existing

    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, DESTINATION, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create {DESTINATION}/{name}")
    base = texture_sample(
        material,
        textures["textures/boulder_01_diff_2k.jpg"],
        -520,
        -160,
        unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    )
    normal = texture_sample(
        material,
        textures["textures/boulder_01_nor_gl_2k.jpg"],
        -520,
        40,
        unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    )
    arm = texture_sample(
        material,
        textures["textures/boulder_01_arm_2k.jpg"],
        -520,
        240,
        unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        normal, "RGB", unreal.MaterialProperty.MP_NORMAL
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        arm, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        arm, "G", unreal.MaterialProperty.MP_ROUGHNESS
    )
    material.set_editor_property("two_sided", False)
    unreal.MaterialEditingLibrary.set_base_material_usage(
        material, unreal.MaterialUsage.MATUSAGE_NANITE, True
    )
    unreal.MaterialEditingLibrary.set_base_material_usage(
        material,
        unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES,
        True,
    )
    material.modify()
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def load_or_create_bank_material() -> unreal.Material:
    name = "M_MeatGrinderBank_ReviewLit"
    existing = unreal.load_asset(f"{DESTINATION}/{name}")
    if isinstance(existing, unreal.Material):
        configure_existing_sampler_types(existing)
        existing.set_editor_property("two_sided", True)
        existing.modify()
        unreal.MaterialEditingLibrary.recompile_material(existing)
        unreal.EditorAssetLibrary.save_loaded_asset(existing, only_if_is_dirty=False)
        return existing

    source_root = (
        "/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
        "SouthForkBankKit_2K"
    )
    base_texture = unreal.load_asset(f"{source_root}/T_RockyGravel_BaseColor_2K")
    normal_texture = unreal.load_asset(f"{source_root}/T_RockyGravel_NormalGL_2K")
    arm_texture = unreal.load_asset(f"{source_root}/T_RockyGravel_ARM_2K")
    if not all(
        isinstance(texture, unreal.Texture2D)
        for texture in (base_texture, normal_texture, arm_texture)
    ):
        raise RuntimeError("Reviewed rocky-gravel dependency is unavailable")

    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, DESTINATION, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create {DESTINATION}/{name}")
    base = texture_sample(
        material,
        base_texture,
        -700,
        -180,
        unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    )
    darken = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -430, -60
    )
    darken.r = 0.42
    dark_base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -170, -160
    )
    normal = texture_sample(
        material,
        normal_texture,
        -700,
        60,
        unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    )
    arm = texture_sample(
        material,
        arm_texture,
        -700,
        280,
        unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(base, "RGB", dark_base, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(darken, "", dark_base, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        dark_base, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        normal, "RGB", unreal.MaterialProperty.MP_NORMAL
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        arm, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        arm, "G", unreal.MaterialProperty.MP_ROUGHNESS
    )
    material.set_editor_property("two_sided", True)
    material.modify()
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    errors = unreal.MaterialEditingLibrary.recompile_material(material)
    if errors:
        raise RuntimeError(
            f"{name} failed to compile: " + "; ".join(str(error) for error in errors)
        )
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def import_mesh(source_root: Path) -> unreal.StaticMesh:
    asset_name = "SM_Boulder01"
    existing = unreal.load_asset(f"{DESTINATION}/{asset_name}")
    if isinstance(existing, unreal.StaticMesh):
        return existing
    task = unreal.AssetImportTask()
    task.filename = str(source_root / "boulder_01_2k.gltf")
    task.destination_path = DESTINATION
    task.destination_name = asset_name
    task.replace_existing = False
    task.automated = True
    task.save = False
    imported_paths = import_tasks([task])
    meshes = [unreal.load_asset(path) for path in imported_paths]
    meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one boulder mesh, imported {imported_paths}")
    mesh = meshes[0]
    final_path = f"{DESTINATION}/{asset_name}"
    if mesh.get_path_name().split(".", 1)[0] != final_path:
        if not unreal.EditorAssetLibrary.rename_asset(
            mesh.get_path_name().split(".", 1)[0], final_path
        ):
            raise RuntimeError(f"Could not rename imported boulder to {final_path}")
        mesh = unreal.load_asset(final_path)
        if not isinstance(mesh, unreal.StaticMesh):
            raise RuntimeError(f"Renamed boulder is unavailable at {final_path}")
    return mesh


def configure_mesh(mesh: unreal.StaticMesh, material: unreal.Material) -> dict[str, object]:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    bounds = mesh.get_bounding_box()
    raw_dimensions = [
        bounds.max.x - bounds.min.x,
        bounds.max.y - bounds.min.y,
        bounds.max.z - bounds.min.z,
    ]
    if max(raw_dimensions) < 100.0:
        raise RuntimeError(
            "glTF Interchange did not convert publisher metres to Unreal centimetres: "
            f"{raw_dimensions}"
        )
    nanite_settings = mesh.get_editor_property("nanite_settings")
    nanite_settings.enabled = True
    mesh.set_editor_property("nanite_settings", nanite_settings)
    for slot_index in range(len(mesh.static_materials)):
        mesh.set_material(slot_index, material)
    mesh.set_editor_property("customized_collision", False)
    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    bounds = mesh.get_bounding_box()
    dimensions_cm = [
        bounds.max.x - bounds.min.x,
        bounds.max.y - bounds.min.y,
        bounds.max.z - bounds.min.z,
    ]
    if not 150.0 <= max(dimensions_cm) <= 220.0:
        raise RuntimeError(f"Boulder 01 failed publisher-scale gate: {dimensions_cm}")
    return {
        "asset_path": mesh.get_path_name(),
        "dimensions_cm": dimensions_cm,
        "base_z_cm": bounds.min.z,
        "lod0_build_scale": [1.0, 1.0, 1.0],
        "nanite_enabled": mesh.get_editor_property("nanite_settings").enabled,
        "static_mesh_editor_subsystem_available": subsystem is not None,
        "nanite_fallback_triangle_count_lod0": mesh.get_num_triangles(0),
        "material_slot_count": len(mesh.static_materials),
        "material": material.get_path_name(),
        "collision_policy": "disabled_on_transient_review_components",
    }


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_MEAT_GRINDER_HERO_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir()) / "RaftSim" / "meat_grinder_hero_import.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim Meat Grinder hero import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_environment_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        root_text = os.environ.get("RAFTSIM_MEAT_GRINDER_HERO_SOURCE_ROOT", "").strip()
        if not root_text:
            raise RuntimeError("RAFTSIM_MEAT_GRINDER_HERO_SOURCE_ROOT is required")
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        textures = import_textures(source_root)
        material = load_or_create_material(textures)
        bank_material = load_or_create_bank_material()
        mesh = import_mesh(source_root)
        report["meshes"] = [configure_mesh(mesh, material)]
        report["textures"] = sorted(texture.get_path_name() for texture in textures.values())
        report["materials"] = [
            material.get_path_name(),
            bank_material.get_path_name(),
        ]
        report["status"] = "isolated_review_candidate_imported"
        write_report(report)
        unreal.log(f"RaftSim imported reviewed Meat Grinder hero asset {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
