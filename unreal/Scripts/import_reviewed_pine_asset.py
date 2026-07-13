"""Import the rights-reviewed Poly Haven Pine Tree 01 set for isolated review."""

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


ASSET_ID = "polyhaven_pine_tree_01_1k"
DESTINATION = "/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K"
SOURCE_FILES = {
    "pine_tree_01_1k.fbx": "b220661091fb81046d9af751259c5d3e4f1cde3b79b48cdaddc79b4762515dc3",
    "textures/pine_tree_01_bark_diff_1k.png": "91e79e9bd1d5d68922262b4eee752808c49c55c2941b531a65b586dae8984bc9",
    "textures/pine_tree_01_bark_disp_1k.png": "8cce79758590f833bd8435c428110bcd656ff8e242c899acbd416b6eeb7e8606",
    "textures/pine_tree_01_bark_nor_gl_1k.png": "d0cdc8ff2f74da8023a1f18512f9db643284d94a698a4ac491f63c4c11c95211",
    "textures/pine_tree_01_bark_rough_1k.png": "63c3785c47a2f4193e5054d9f8481da0bd41bc2bfc1a993cd8785fad6339fe97",
    "textures/pine_tree_01_trunk_a_diff_1k.png": "50e8911ac39d8eeb720d7412495d00f8639f2a0ad01dec1c22aa79efc16e9f08",
    "textures/pine_tree_01_trunk_a_nor_gl_1k.png": "e1dfe1dcfd4d92eb7dd732cff98ac32c8a3aa5a36b9eea220e22030ea604ec09",
    "textures/pine_tree_01_trunk_a_rough_1k.png": "ebda61e833608c3df8d65018330c9e0bb80ec39b30d9416de0cc088c520ca8b6",
    "textures/pine_tree_01_trunk_b_diff_1k.png": "41bd8a65e0a827646b3a33dc1607eba2082ddc25fe714752259447c49d0600cc",
    "textures/pine_tree_01_trunk_b_nor_gl_1k.png": "fe5f1dafe611a7f04142abf7878622a6212ed7c1737711d548ec3301b3210cf7",
    "textures/pine_tree_01_trunk_b_rough_1k.png": "ff399f6d054f903deee0e4d455c09f12ac3441f5c9547a0e9d06c163e6958dee",
    "textures/pine_tree_01_trunk_c_diff_1k.png": "edbceb8657a036e98831a3550433ab2d78928fcf9060e400ca84748cedcaf962",
    "textures/pine_tree_01_trunk_c_nor_gl_1k.png": "08a40a7486ad3a8d97cf3da0afe5951f1a038cb51395020e2c4a2113f46d1610",
    "textures/pine_tree_01_trunk_c_rough_1k.png": "48fcced840b4beed4e03e09a352a67dd36185c9cd4247090069391bfb9746de9",
    "textures/pine_tree_01_twig_diff_1k.png": "d02c031de64b8ad671f3dd0da19870fa4783d912ae6674aeab0702871deeaeaa",
    "textures/pine_tree_01_twig_nor_gl_1k.png": "4b79eda7fe8843d71f9289bd0d3897a1b0a7310b1872b390a589a04b510b0597",
    "textures/pine_tree_01_twig_rough_1k.png": "c12da3dd6c1588f50307d96807d78115757f110bc562811369d90b86bd6fddc7",
}


def texture_asset_name(relative_path: str) -> str:
    stem = Path(relative_path).stem.removeprefix("pine_tree_01_")
    tokens = "".join(token.title() for token in stem.split("_"))
    return f"T_PineTree01_{tokens}"


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
    task.filename = str(source_root / "pine_tree_01_1k.fbx")
    task.destination_path = DESTINATION
    task.destination_name = "SM_PineTree01"
    task.replace_existing = False
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    imported_paths = import_tasks([task])
    meshes = [unreal.load_asset(path) for path in imported_paths]
    meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    if len(meshes) != 3:
        raise RuntimeError(f"Expected three pine meshes, imported {len(meshes)}: {imported_paths}")
    return meshes


def import_textures(source_root: Path) -> dict[str, unreal.Texture2D]:
    textures: dict[str, unreal.Texture2D] = {}
    tasks = []
    task_keys = []
    texture_paths = [path for path in SOURCE_FILES if path.startswith("textures/")]
    for relative_path in texture_paths:
        asset_name = texture_asset_name(relative_path)
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
        elif "_rough_" in relative_path or "_disp_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
            )
        texture.modify()
    return textures


def load_or_create_material(
    name: str,
    prefix: str,
    textures: dict[str, unreal.Texture2D],
    foliage: bool = False,
) -> unreal.Material:
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
        textures[f"textures/{prefix}_diff_1k.png"],
        -640,
        -120,
        unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    )
    normal = texture_sample(
        material,
        textures[f"textures/{prefix}_nor_gl_1k.png"],
        -640,
        80,
        unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    )
    roughness = texture_sample(
        material,
        textures[f"textures/{prefix}_rough_1k.png"],
        -640,
        280,
        unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        normal, "RGB", unreal.MaterialProperty.MP_NORMAL
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness, "R", unreal.MaterialProperty.MP_ROUGHNESS
    )
    if foliage:
        unreal.MaterialEditingLibrary.connect_material_property(
            base, "A", unreal.MaterialProperty.MP_OPACITY_MASK
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            base, "RGB", unreal.MaterialProperty.MP_SUBSURFACE_COLOR
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


def material_role(slot_name: str) -> str:
    lower = slot_name.lower()
    if "twig" in lower:
        return "needles"
    for role in ("trunk_a", "trunk_b", "trunk_c"):
        if role in lower:
            return role
    return "bark"


def configure_meshes(
    meshes: list[unreal.StaticMesh], materials: dict[str, unreal.Material]
) -> list[dict[str, object]]:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not subsystem:
        raise RuntimeError("StaticMeshEditorSubsystem is unavailable")
    records = []
    for mesh in sorted(meshes, key=lambda asset: asset.get_name()):
        bounds = mesh.get_bounding_box()
        raw_height = bounds.max.z - bounds.min.z
        build_settings = subsystem.get_lod_build_settings(mesh, 0)
        if raw_height < 100.0 and build_settings.build_scale3d.z < 99.0:
            build_settings.build_scale3d = unreal.Vector(100.0, 100.0, 100.0)
            subsystem.set_lod_build_settings(mesh, 0, build_settings)

        nanite_settings = subsystem.get_nanite_settings(mesh)
        nanite_settings.enabled = True
        if hasattr(unreal, "NaniteShapePreservation"):
            nanite_settings.shape_preservation = unreal.NaniteShapePreservation.PRESERVE_AREA
        subsystem.set_nanite_settings(mesh, nanite_settings)

        slots = []
        assigned_roles = set()
        for slot_index, static_material in enumerate(mesh.static_materials):
            slot_name = str(static_material.material_slot_name)
            role = material_role(slot_name)
            mesh.set_material(slot_index, materials[role])
            assigned_roles.add(role)
            slots.append(
                {
                    "index": slot_index,
                    "slot_name": slot_name,
                    "role": role,
                    "material": materials[role].get_path_name(),
                }
            )
        if "needles" not in assigned_roles or not assigned_roles.intersection(
            {"bark", "trunk_a", "trunk_b", "trunk_c"}
        ):
            raise RuntimeError(
                f"Pine mesh {mesh.get_name()} lacks expected woody/needle material slots: {slots}"
            )
        mesh.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

        bounds = mesh.get_bounding_box()
        persisted = subsystem.get_lod_build_settings(mesh, 0)
        scale = persisted.build_scale3d.z if (bounds.max.z - bounds.min.z) < 100.0 else 1.0
        height_cm = (bounds.max.z - bounds.min.z) * scale
        record = {
            "asset_path": mesh.get_path_name(),
            "nanite_fallback_triangle_count_lod0": mesh.get_num_triangles(0),
            "height_cm": height_cm,
            "plausible_tree_height": 1000.0 <= height_cm <= 3000.0,
            "base_z_cm": bounds.min.z * scale,
            "lod0_build_scale": [
                persisted.build_scale3d.x,
                persisted.build_scale3d.y,
                persisted.build_scale3d.z,
            ],
            "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
            "nanite_shape_preservation": str(
                subsystem.get_nanite_settings(mesh).shape_preservation
            ),
            "material_slots": slots,
        }
        if not record["plausible_tree_height"]:
            raise RuntimeError(
                "Pine candidate failed the 10-30 m physical-height gate: "
                + json.dumps(record, sort_keys=True)
            )
        records.append(record)
    return records


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_REVIEWED_PINE_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir()) / "RaftSim" / "reviewed_pine_import.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed pine import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_environment_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        root_text = os.environ.get("RAFTSIM_REVIEWED_PINE_SOURCE_ROOT", "").strip()
        if not root_text:
            raise RuntimeError("RAFTSIM_REVIEWED_PINE_SOURCE_ROOT is required")
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        meshes = import_meshes(source_root)
        textures = import_textures(source_root)
        materials = {
            "bark": load_or_create_material(
                "M_PineTree01_Bark", "pine_tree_01_bark", textures
            ),
            "trunk_a": load_or_create_material(
                "M_PineTree01_TrunkA", "pine_tree_01_trunk_a", textures
            ),
            "trunk_b": load_or_create_material(
                "M_PineTree01_TrunkB", "pine_tree_01_trunk_b", textures
            ),
            "trunk_c": load_or_create_material(
                "M_PineTree01_TrunkC", "pine_tree_01_trunk_c", textures
            ),
            "needles": load_or_create_material(
                "M_PineTree01_NeedlesMasked", "pine_tree_01_twig", textures, foliage=True
            ),
        }
        for asset in [*textures.values(), *materials.values()]:
            unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        report["meshes"] = configure_meshes(meshes, materials)
        report["textures"] = sorted(texture.get_path_name() for texture in textures.values())
        report["materials"] = sorted(material.get_path_name() for material in materials.values())
        report["status"] = "isolated_review_candidate_imported"
        write_report(report)
        unreal.log(f"RaftSim imported reviewed pine candidate {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
