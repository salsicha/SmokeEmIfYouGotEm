"""Import the rights-reviewed Poly Haven Jacaranda candidate for isolated review."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_reviewed_biome_asset import (  # noqa: E402
    configure_existing_sampler_types,
    import_tasks,
    texture_sample,
)


ASSET_ID = "polyhaven_jacaranda_tree_1k"
DESTINATION = "/Game/RaftSim/Environment/ExternalReview/PolyHaven/JacarandaTree_1K"
SOURCE_FILES = {
    "jacaranda_tree_1k.fbx": "392c74d85100efc8ee045fed820ec4fbe79d62e154e4c54156ef1e0ec0465a5a",
    "textures/jacaranda_tree_branches_diff_1k.png": "fe671f7fae88e269e4a517b6ff7be74ae3c2d1fdedfea206ebfa9941af0d9e20",
    "textures/jacaranda_tree_branches_nor_gl_1k.png": "e72c3bf652d998d75ef98fc51fb7a10de3b7efd072c191a8eb9c92b6f93340f0",
    "textures/jacaranda_tree_branches_rough_1k.png": "c6db3c33f23654a8d31dcf5609d19d97ab1036b36b3d9a6bcd50ecc975f8fb3c",
    "textures/jacaranda_tree_leaves_alpha_1k.png": "c708a7e928a2e4d26981b021a22deeefc0ebb0e467f60b53cfa636a7e24d68f7",
    "textures/jacaranda_tree_leaves_diff_1k.png": "5729978e92649ee6cc70bdc457aac1b28b16a10bde0a55004b659a1923c8861b",
    "textures/jacaranda_tree_leaves_nor_gl_1k.png": "4dc58cca117cb193629bf6a2b909bd281451c60a5d85f1b1d438d296b90a1091",
    "textures/jacaranda_tree_leaves_rough_1k.png": "2f6b89e7a1983cfa6fc2050f993c2c91c9afc86ce285607fa5a5f8f6b1b4c879",
    "textures/jacaranda_tree_trunk_diff_1k.png": "9ba4a3af9d38d54638df35a2bae4f30455f5fb25c080825f6e22af4e5d65c7f2",
    "textures/jacaranda_tree_trunk_nor_gl_1k.png": "d2c1dd8a274983731e2418b4eb6b49bddcf375d170c70010b799d7417eafbfac",
    "textures/jacaranda_tree_trunk_rough_1k.png": "9262a1d4e8cc848a29bfc93333e8ad844c7e470e592787604b7e090e0ed149f2",
}
TEXTURE_NAMES = {
    "textures/jacaranda_tree_branches_diff_1k.png": "T_JacarandaTree_Branches_BaseColor_1K",
    "textures/jacaranda_tree_branches_nor_gl_1k.png": "T_JacarandaTree_Branches_NormalGL_1K",
    "textures/jacaranda_tree_branches_rough_1k.png": "T_JacarandaTree_Branches_Roughness_1K",
    "textures/jacaranda_tree_leaves_alpha_1k.png": "T_JacarandaTree_Leaves_Opacity_1K",
    "textures/jacaranda_tree_leaves_diff_1k.png": "T_JacarandaTree_Leaves_BaseColor_1K",
    "textures/jacaranda_tree_leaves_nor_gl_1k.png": "T_JacarandaTree_Leaves_NormalGL_1K",
    "textures/jacaranda_tree_leaves_rough_1k.png": "T_JacarandaTree_Leaves_Roughness_1K",
    "textures/jacaranda_tree_trunk_diff_1k.png": "T_JacarandaTree_Trunk_BaseColor_1K",
    "textures/jacaranda_tree_trunk_nor_gl_1k.png": "T_JacarandaTree_Trunk_NormalGL_1K",
    "textures/jacaranda_tree_trunk_rough_1k.png": "T_JacarandaTree_Trunk_Roughness_1K",
}
MATERIAL_SPECS = {
    "branches": {
        "name": "M_JacarandaTree_Branches",
        "base": "textures/jacaranda_tree_branches_diff_1k.png",
        "normal": "textures/jacaranda_tree_branches_nor_gl_1k.png",
        "roughness": "textures/jacaranda_tree_branches_rough_1k.png",
    },
    "leaves": {
        "name": "M_JacarandaTree_Leaves",
        "base": "textures/jacaranda_tree_leaves_diff_1k.png",
        "normal": "textures/jacaranda_tree_leaves_nor_gl_1k.png",
        "roughness": "textures/jacaranda_tree_leaves_rough_1k.png",
        "opacity": "textures/jacaranda_tree_leaves_alpha_1k.png",
    },
    "trunk": {
        "name": "M_JacarandaTree_Trunk",
        "base": "textures/jacaranda_tree_trunk_diff_1k.png",
        "normal": "textures/jacaranda_tree_trunk_nor_gl_1k.png",
        "roughness": "textures/jacaranda_tree_trunk_rough_1k.png",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source(root: Path) -> list[dict[str, object]]:
    records = []
    for relative_path, expected_hash in SOURCE_FILES.items():
        path = root / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Missing reviewed source file: {path}")
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"Hash mismatch for {relative_path}: expected {expected_hash}, got {actual_hash}"
            )
        records.append(
            {"relative_path": relative_path, "sha256": actual_hash, "bytes": path.stat().st_size}
        )
    return records


def import_mesh(source_root: Path) -> tuple[unreal.StaticMesh, int | None, str]:
    existing = [
        unreal.load_asset(path)
        for path in unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=False)
    ]
    existing_meshes = [asset for asset in existing if isinstance(asset, unreal.StaticMesh)]
    if existing_meshes:
        return existing_meshes[0], None, "not_recomputed_from_existing_nanite_asset"

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
    task.filename = str(source_root / "jacaranda_tree_1k.fbx")
    task.destination_path = DESTINATION
    task.destination_name = "SM_JacarandaTree"
    task.replace_existing = False
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    imported_paths = import_tasks([task])
    meshes = [unreal.load_asset(path) for path in imported_paths]
    meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one Jacaranda mesh, imported {len(meshes)}: {imported_paths}")
    return meshes[0], meshes[0].get_num_triangles(0), "measured_before_nanite_enable"


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
        elif "_rough_" in relative_path or "_alpha_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
            )
        texture.modify()
    return textures


def load_or_create_material(
    role: str,
    spec: dict[str, str],
    textures: dict[str, unreal.Texture2D],
) -> unreal.Material:
    asset_path = f"{DESTINATION}/{spec['name']}"
    existing = unreal.load_asset(asset_path)
    if isinstance(existing, unreal.Material):
        configure_existing_sampler_types(existing)
        unreal.MaterialEditingLibrary.recompile_material(existing)
        return existing

    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        spec["name"], DESTINATION, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create material {asset_path}")
    base_color = texture_sample(
        material, textures[spec["base"]], -640, -140, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR
    )
    normal = texture_sample(
        material, textures[spec["normal"]], -640, 40, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    )
    roughness = texture_sample(
        material,
        textures[spec["roughness"]],
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
    if role == "leaves":
        opacity = texture_sample(
            material,
            textures[spec["opacity"]],
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
        material.set_editor_property("opacity_mask_clip_value", 0.30)
    material.modify()
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    return material


def configure_mesh(
    mesh: unreal.StaticMesh,
    source_triangle_count: int | None,
    source_triangle_count_status: str,
    materials: dict[str, unreal.Material],
) -> dict[str, object]:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not subsystem:
        raise RuntimeError("StaticMeshEditorSubsystem is unavailable")
    raw_bounds = mesh.get_bounding_box()
    raw_height = raw_bounds.max.z - raw_bounds.min.z
    build_settings = subsystem.get_lod_build_settings(mesh, 0)
    if raw_height < 100.0 and build_settings.build_scale3d.z < 99.0:
        build_settings.build_scale3d = unreal.Vector(100.0, 100.0, 100.0)
        subsystem.set_lod_build_settings(mesh, 0, build_settings)

    nanite_settings = subsystem.get_nanite_settings(mesh)
    nanite_settings.enabled = True
    if hasattr(unreal, "NaniteShapePreservation"):
        nanite_settings.shape_preservation = unreal.NaniteShapePreservation.PRESERVE_AREA
    subsystem.set_nanite_settings(mesh, nanite_settings)

    slot_records = []
    assigned_roles = set()
    for index, static_material in enumerate(mesh.static_materials):
        slot_name = str(static_material.material_slot_name)
        lower_name = slot_name.lower()
        if "leave" in lower_name or "leaf" in lower_name:
            role = "leaves"
        elif "branch" in lower_name:
            role = "branches"
        else:
            role = "trunk"
        mesh.set_material(index, materials[role])
        assigned_roles.add(role)
        slot_records.append(
            {
                "index": index,
                "slot_name": slot_name,
                "role": role,
                "material": materials[role].get_path_name(),
            }
        )
    if assigned_roles != {"branches", "leaves", "trunk"}:
        raise RuntimeError(f"Expected trunk/branches/leaves slots, assigned {sorted(assigned_roles)}")

    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    bounds = mesh.get_bounding_box()
    persisted = subsystem.get_lod_build_settings(mesh, 0)
    bounds_scale = persisted.build_scale3d.z if (bounds.max.z - bounds.min.z) < 100.0 else 1.0
    height_cm = (bounds.max.z - bounds.min.z) * bounds_scale
    width_cm = max(bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y) * bounds_scale
    footprint_min_x = bounds.min.x * bounds_scale
    footprint_max_x = bounds.max.x * bounds_scale
    footprint_min_y = bounds.min.y * bounds_scale
    footprint_max_y = bounds.max.y * bounds_scale
    base_z = bounds.min.z * bounds_scale
    pivot_within_footprint = (
        footprint_min_x <= 0.0 <= footprint_max_x
        and footprint_min_y <= 0.0 <= footprint_max_y
    )
    base_contact_tolerance = max(12.0, height_cm * 0.025)
    pivot_meets_ground = abs(base_z) <= base_contact_tolerance
    record = {
        "asset_path": mesh.get_path_name(),
        "source_triangle_count_lod0": source_triangle_count,
        "source_triangle_count_status": source_triangle_count_status,
        "publisher_reported_triangle_count_label": "312K",
        "nanite_fallback_triangle_count_lod0": mesh.get_num_triangles(0),
        "effective_height_cm": height_cm,
        "effective_width_cm": width_cm,
        "plausible_tree_height": 600.0 <= height_cm <= 2600.0,
        "plausible_tree_width": 800.0 <= width_cm <= 3200.0,
        "footprint_bounds_xy_cm": [
            footprint_min_x,
            footprint_min_y,
            footprint_max_x,
            footprint_max_y,
        ],
        "pivot_within_footprint": pivot_within_footprint,
        "base_z_cm": base_z,
        "base_contact_tolerance_cm": base_contact_tolerance,
        "pivot_meets_ground": pivot_meets_ground,
        "valid_for_instancing": pivot_within_footprint and pivot_meets_ground,
        "lod0_build_scale": [
            persisted.build_scale3d.x,
            persisted.build_scale3d.y,
            persisted.build_scale3d.z,
        ],
        "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
        "nanite_shape_preservation": str(subsystem.get_nanite_settings(mesh).shape_preservation),
        "material_slots": slot_records,
    }
    if not (
        record["plausible_tree_height"]
        and record["plausible_tree_width"]
        and record["valid_for_instancing"]
    ):
        raise RuntimeError(
            "Jacaranda candidate failed physical-scale or instancing-pivot validation: "
            + json.dumps(record, sort_keys=True)
        )
    return record


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_REVIEWED_JACARANDA_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir()) / "RaftSim" / "reviewed_jacaranda_import.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed Jacaranda import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_biome_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        root_text = os.environ.get("RAFTSIM_REVIEWED_JACARANDA_SOURCE_ROOT", "").strip()
        if not root_text:
            raise RuntimeError("RAFTSIM_REVIEWED_JACARANDA_SOURCE_ROOT is required")
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        mesh, source_triangle_count, triangle_status = import_mesh(source_root)
        textures = import_textures(source_root)
        materials = {
            role: load_or_create_material(role, spec, textures)
            for role, spec in MATERIAL_SPECS.items()
        }
        for asset in [*textures.values(), *materials.values()]:
            unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        report["mesh"] = configure_mesh(
            mesh, source_triangle_count, triangle_status, materials
        )
        report["textures"] = sorted(texture.get_path_name() for texture in textures.values())
        report["materials"] = sorted(material.get_path_name() for material in materials.values())
        report["status"] = "isolated_review_candidate_imported"
        write_report(report)
        unreal.log(f"RaftSim imported reviewed Jacaranda candidate {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
