"""Import the rights-reviewed Poly Haven South Fork bank kit in isolation."""

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


ASSET_ID = "polyhaven_south_fork_bank_kit_2k"
DESTINATION = "/Game/RaftSim/Environment/ExternalReview/PolyHaven/SouthForkBankKit_2K"
SOURCE_FILES = {
    "rock_face_01_2k.fbx": "c459ad32e8a0253db5efcf21d292a5c8308e1d07637dbbeb701ae193d9b622ae",
    "rock_face_01_diff_2k.jpg": "447525a84e88138bdaecd90d6a3dd957bd81031a8652fa1809c7a3af0033f465",
    "rock_face_01_nor_gl_2k.jpg": "751749444a78cedbb0e1fcde38eb5cbb8ac30095fafec823c64f67fb7a04d8c6",
    "rock_face_01_arm_2k.jpg": "4738d73c0cd757971dcb32e52ba644b9e520173127108a342a3478a8586a805d",
    "tree_stump_02_2k.fbx": "6d291e6ad6ddcee45cd32c8572b80698bcd0042ff17bebcd062c40adc389d52c",
    "tree_stump_02_diff_2k.jpg": "8078862e35578a8f7ea1e82072cb7e6f5d7f137290c2d0da6c783b3080a782b0",
    "tree_stump_02_nor_gl_2k.jpg": "e59283307ef698f9a43e95db5493d98b2b03b5b90682d9bb6158c4187f6154ab",
    "tree_stump_02_arm_2k.jpg": "d34610d4d6133c28688eb68208c9be223580f6c7b43e98c5d35dea48266512d3",
    "roots_diff_2k.jpg": "45f2bce14592e5c1794b128a3992f18ab63a37e4b81fcb823f18094d8537d784",
    "roots_nor_gl_2k.jpg": "801f39e0b21e87369424c5b498648b9a79617cd5ab20d8518949a3e38348f3cb",
    "roots_arm_2k.jpg": "ec8a1e4862c640164bfdf7da01dbab657750449164486cba402f2591d37f906e",
    "roots_disp_2k.png": "3c51f8556aec080992025edda292fe8bbcfa6c914214ad3deaf987bd25ca9fbb",
    "rocky_gravel_diff_2k.jpg": "641b0a87d3c793c1670f6e6c68f4799e8c5045268b5c42632b8a4b6dddef4697",
    "rocky_gravel_nor_gl_2k.jpg": "12769e23229fa996ac5b8173410304cbe6f536baf69969def7c2d0ee1d8fc2a3",
    "rocky_gravel_arm_2k.jpg": "856d37d4ab6b2e0ab6e4e217ef3f5f0264995fdf9040367e19af8e60f3e16adc",
    "rocky_gravel_disp_2k.png": "265ed30519843be15118da2427ba1ad02b5f52441d8ab9960cd35de849c7b114",
}
TEXTURES = {
    "rock_face_01_diff_2k.jpg": "T_RockFace01_BaseColor_2K",
    "rock_face_01_nor_gl_2k.jpg": "T_RockFace01_NormalGL_2K",
    "rock_face_01_arm_2k.jpg": "T_RockFace01_ARM_2K",
    "tree_stump_02_diff_2k.jpg": "T_TreeStump02_BaseColor_2K",
    "tree_stump_02_nor_gl_2k.jpg": "T_TreeStump02_NormalGL_2K",
    "tree_stump_02_arm_2k.jpg": "T_TreeStump02_ARM_2K",
    "roots_diff_2k.jpg": "T_Roots_BaseColor_2K",
    "roots_nor_gl_2k.jpg": "T_Roots_NormalGL_2K",
    "roots_arm_2k.jpg": "T_Roots_ARM_2K",
    "roots_disp_2k.png": "T_Roots_Displacement_2K",
    "rocky_gravel_diff_2k.jpg": "T_RockyGravel_BaseColor_2K",
    "rocky_gravel_nor_gl_2k.jpg": "T_RockyGravel_NormalGL_2K",
    "rocky_gravel_arm_2k.jpg": "T_RockyGravel_ARM_2K",
    "rocky_gravel_disp_2k.png": "T_RockyGravel_Displacement_2K",
}
MESHES = {
    "rock_face_01_2k.fbx": ("SM_RockFace01", 600.0, 780.0),
    "tree_stump_02_2k.fbx": ("SM_TreeStump02", 125.0, 180.0),
}
MATERIALS = {
    "rock_face_01": (
        "M_RockFace01_ReviewLit",
        "rock_face_01_diff_2k.jpg",
        "rock_face_01_nor_gl_2k.jpg",
        "rock_face_01_arm_2k.jpg",
    ),
    "tree_stump_02": (
        "M_TreeStump02_ReviewLit",
        "tree_stump_02_diff_2k.jpg",
        "tree_stump_02_nor_gl_2k.jpg",
        "tree_stump_02_arm_2k.jpg",
    ),
    "roots": (
        "M_Roots_ReviewLit",
        "roots_diff_2k.jpg",
        "roots_nor_gl_2k.jpg",
        "roots_arm_2k.jpg",
    ),
    "rocky_gravel": (
        "M_RockyGravel_ReviewLit",
        "rocky_gravel_diff_2k.jpg",
        "rocky_gravel_nor_gl_2k.jpg",
        "rocky_gravel_arm_2k.jpg",
    ),
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
        elif "_arm_" in relative_path or "_disp_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
            )
        texture.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return textures


def load_or_create_material(
    name: str,
    base_texture: unreal.Texture2D,
    normal_texture: unreal.Texture2D,
    arm_texture: unreal.Texture2D,
) -> unreal.Material:
    existing = unreal.load_asset(f"{DESTINATION}/{name}")
    if isinstance(existing, unreal.Material):
        configure_existing_sampler_types(existing)
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
        material, base_texture, -520, -160, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR
    )
    normal = texture_sample(
        material, normal_texture, -520, 40, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    )
    arm = texture_sample(
        material, arm_texture, -520, 240, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
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


def import_mesh(source_root: Path, relative_path: str, asset_name: str) -> unreal.StaticMesh:
    existing = unreal.load_asset(f"{DESTINATION}/{asset_name}")
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
    task.filename = str(source_root / relative_path)
    task.destination_path = DESTINATION
    task.destination_name = asset_name
    task.replace_existing = False
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    imported_paths = import_tasks([task])
    meshes = [unreal.load_asset(path) for path in imported_paths]
    meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    if len(meshes) != 1:
        raise RuntimeError(
            f"Expected one combined mesh for {relative_path}, imported {imported_paths}"
        )
    return meshes[0]


def configure_mesh(
    mesh: unreal.StaticMesh,
    material: unreal.Material,
    minimum_dimension_cm: float,
    maximum_dimension_cm: float,
) -> dict[str, object]:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not subsystem:
        raise RuntimeError("StaticMeshEditorSubsystem is unavailable")
    bounds = mesh.get_bounding_box()
    raw_dimensions = [
        bounds.max.x - bounds.min.x,
        bounds.max.y - bounds.min.y,
        bounds.max.z - bounds.min.z,
    ]
    build_settings = subsystem.get_lod_build_settings(mesh, 0)
    if max(raw_dimensions) < 100.0 and build_settings.build_scale3d.z < 99.0:
        build_settings.build_scale3d = unreal.Vector(100.0, 100.0, 100.0)
        subsystem.set_lod_build_settings(mesh, 0, build_settings)
    nanite_settings = subsystem.get_nanite_settings(mesh)
    nanite_settings.enabled = True
    subsystem.set_nanite_settings(mesh, nanite_settings)
    for slot_index in range(len(mesh.static_materials)):
        mesh.set_material(slot_index, material)
    mesh.set_editor_property("customized_collision", False)
    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    persisted = subsystem.get_lod_build_settings(mesh, 0)
    bounds = mesh.get_bounding_box()
    dimensions_cm = [
        (bounds.max.x - bounds.min.x) * persisted.build_scale3d.x,
        (bounds.max.y - bounds.min.y) * persisted.build_scale3d.y,
        (bounds.max.z - bounds.min.z) * persisted.build_scale3d.z,
    ]
    maximum = max(dimensions_cm)
    if not minimum_dimension_cm <= maximum <= maximum_dimension_cm:
        raise RuntimeError(
            f"{mesh.get_name()} failed publisher-scale gate "
            f"{minimum_dimension_cm}-{maximum_dimension_cm} cm: {dimensions_cm}"
        )
    return {
        "asset_path": mesh.get_path_name(),
        "dimensions_cm": dimensions_cm,
        "base_z_cm": bounds.min.z * persisted.build_scale3d.z,
        "lod0_build_scale": [
            persisted.build_scale3d.x,
            persisted.build_scale3d.y,
            persisted.build_scale3d.z,
        ],
        "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
        "nanite_fallback_triangle_count_lod0": mesh.get_num_triangles(0),
        "material_slot_count": len(mesh.static_materials),
        "material": material.get_path_name(),
        "collision_policy": "disabled_on_transient_review_components",
    }


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_REVIEWED_SOUTH_FORK_BANK_KIT_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir())
        / "RaftSim"
        / "reviewed_south_fork_bank_kit.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed South Fork bank-kit import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_environment_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        root_text = os.environ.get("RAFTSIM_REVIEWED_SOUTH_FORK_BANK_KIT_SOURCE_ROOT", "").strip()
        if not root_text:
            raise RuntimeError("RAFTSIM_REVIEWED_SOUTH_FORK_BANK_KIT_SOURCE_ROOT is required")
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        textures = import_textures(source_root)
        materials = {
            key: load_or_create_material(
                spec[0], textures[spec[1]], textures[spec[2]], textures[spec[3]]
            )
            for key, spec in MATERIALS.items()
        }
        mesh_records = []
        for relative_path, (asset_name, minimum_cm, maximum_cm) in MESHES.items():
            mesh = import_mesh(source_root, relative_path, asset_name)
            material_key = "rock_face_01" if "rock_face" in relative_path else "tree_stump_02"
            mesh_records.append(
                configure_mesh(mesh, materials[material_key], minimum_cm, maximum_cm)
            )
        report["meshes"] = mesh_records
        report["textures"] = sorted(texture.get_path_name() for texture in textures.values())
        report["materials"] = sorted(material.get_path_name() for material in materials.values())
        report["surface_displacement_maps_imported_not_connected"] = [
            textures["roots_disp_2k.png"].get_path_name(),
            textures["rocky_gravel_disp_2k.png"].get_path_name(),
        ]
        report["status"] = "isolated_review_candidate_imported"
        write_report(report)
        unreal.log(f"RaftSim imported reviewed South Fork bank kit {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
