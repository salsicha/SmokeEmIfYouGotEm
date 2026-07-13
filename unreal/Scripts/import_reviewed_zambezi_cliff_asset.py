"""Import Poly Haven Namaqualand Cliff 02 for isolated Zambezi review."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import traceback

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_reviewed_biome_asset import import_tasks, sha256, texture_sample


ASSET_ID = "polyhaven_namaqualand_cliff_02_2k"
DESTINATION = "/Game/RaftSim/Environment/ExternalReview/PolyHaven/NamaqualandCliff02_2K"
SOURCE_FILES = {
    "namaqualand_cliff_02_2k.fbx": "465bf72788387b5ef4306bd3858610c942a7cf127b8a84a555e6aa5cd39b209d",
    "namaqualand_cliff_02_diff_2k.jpg": "9618e2a42155b93189e0bac9edebcc46a6af1357f4f6ed56f79ca1714690d4f0",
    "namaqualand_cliff_02_nor_gl_2k.jpg": "634bc52174130d6992a7539d1f7bb923c4a103f117ab09966782c0e89eb571f6",
    "namaqualand_cliff_02_arm_2k.jpg": "3b4d733be37186ab6b62b8ddde90f9dc439f5b42a17293f1b65844a0f0d9e02f",
}
TEXTURE_NAMES = {
    "namaqualand_cliff_02_diff_2k.jpg": "T_NamaqualandCliff02_BaseColor_2K",
    "namaqualand_cliff_02_nor_gl_2k.jpg": "T_NamaqualandCliff02_NormalGL_2K",
    "namaqualand_cliff_02_arm_2k.jpg": "T_NamaqualandCliff02_ARM_2K",
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


def import_mesh(source_root: Path) -> unreal.StaticMesh:
    existing = unreal.load_asset(f"{DESTINATION}/SM_NamaqualandCliff02")
    if isinstance(existing, unreal.StaticMesh):
        return existing

    options = unreal.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_mesh = True
    options.import_as_skeletal = False
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.original_import_type = unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_materials = False
    options.import_textures = False
    options.import_animations = False
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.generate_lightmap_u_vs = True
    options.static_mesh_import_data.remove_degenerates = True
    options.static_mesh_import_data.transform_vertex_to_absolute = False
    options.static_mesh_import_data.bake_pivot_in_vertex = True

    task = unreal.AssetImportTask()
    task.filename = str(source_root / "namaqualand_cliff_02_2k.fbx")
    task.destination_path = DESTINATION
    task.destination_name = "SM_NamaqualandCliff02"
    task.replace_existing = False
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    imported_paths = import_tasks([task])
    meshes = [unreal.load_asset(path) for path in imported_paths]
    meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one cliff mesh, imported {len(meshes)}: {imported_paths}")
    return meshes[0]


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
        elif "_arm_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
            )
        texture.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return textures


def load_or_create_material(textures: dict[str, unreal.Texture2D]) -> unreal.Material:
    name = "M_NamaqualandCliff02_ReviewLit"
    existing = unreal.load_asset(f"{DESTINATION}/{name}")
    if isinstance(existing, unreal.Material):
        return existing
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, DESTINATION, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create {DESTINATION}/{name}")
    base = texture_sample(
        material,
        textures["namaqualand_cliff_02_diff_2k.jpg"],
        -500,
        -160,
        unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    )
    normal = texture_sample(
        material,
        textures["namaqualand_cliff_02_nor_gl_2k.jpg"],
        -500,
        40,
        unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    )
    arm = texture_sample(
        material,
        textures["namaqualand_cliff_02_arm_2k.jpg"],
        -500,
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
    material.modify()
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def configure_mesh(mesh: unreal.StaticMesh, material: unreal.Material) -> dict[str, object]:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not subsystem:
        raise RuntimeError("StaticMeshEditorSubsystem is unavailable")
    bounds = mesh.get_bounding_box()
    raw_dimensions = [
        bounds.max.x - bounds.min.x,
        bounds.max.y - bounds.min.y,
        bounds.max.z - bounds.min.z,
    ]
    settings = subsystem.get_lod_build_settings(mesh, 0)
    if max(raw_dimensions) < 100.0 and settings.build_scale3d.z < 99.0:
        settings.build_scale3d = unreal.Vector(100.0, 100.0, 100.0)
        subsystem.set_lod_build_settings(mesh, 0, settings)
    nanite = subsystem.get_nanite_settings(mesh)
    nanite.enabled = True
    subsystem.set_nanite_settings(mesh, nanite)
    for slot_index in range(len(mesh.static_materials)):
        mesh.set_material(slot_index, material)
    mesh.set_editor_property("customized_collision", False)
    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    persisted = subsystem.get_lod_build_settings(mesh, 0)
    scale = persisted.build_scale3d.z
    bounds = mesh.get_bounding_box()
    dimensions_cm = [
        (bounds.max.x - bounds.min.x) * scale,
        (bounds.max.y - bounds.min.y) * scale,
        (bounds.max.z - bounds.min.z) * scale,
    ]
    maximum = max(dimensions_cm)
    if not 1800.0 <= maximum <= 2300.0:
        raise RuntimeError(f"Cliff failed 18-23 m publisher-scale gate: {dimensions_cm}")
    return {
        "asset_path": mesh.get_path_name(),
        "dimensions_cm": dimensions_cm,
        "base_z_cm": bounds.min.z * scale,
        "lod0_build_scale": [
            persisted.build_scale3d.x,
            persisted.build_scale3d.y,
            persisted.build_scale3d.z,
        ],
        "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
        "nanite_fallback_triangle_count_lod0": mesh.get_num_triangles(0),
        "material_slot_count": len(mesh.static_materials),
        "material": material.get_path_name(),
    }


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_REVIEWED_ZAMBEZI_CLIFF_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir()) / "RaftSim" / "reviewed_zambezi_cliff.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed Zambezi cliff import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_environment_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        root_text = os.environ.get("RAFTSIM_REVIEWED_ZAMBEZI_CLIFF_SOURCE_ROOT", "").strip()
        if not root_text:
            raise RuntimeError("RAFTSIM_REVIEWED_ZAMBEZI_CLIFF_SOURCE_ROOT is required")
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        textures = import_textures(source_root)
        material = load_or_create_material(textures)
        mesh = import_mesh(source_root)
        report["mesh"] = configure_mesh(mesh, material)
        report["textures"] = sorted(texture.get_path_name() for texture in textures.values())
        report["materials"] = [material.get_path_name()]
        report["status"] = "isolated_review_candidate_imported"
        write_report(report)
        unreal.log(f"RaftSim imported reviewed Zambezi cliff candidate {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
