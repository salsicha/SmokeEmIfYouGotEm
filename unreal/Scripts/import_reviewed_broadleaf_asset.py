"""Import the rights-reviewed Poly Haven Tree Small 02 broadleaf candidate."""

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


ASSET_ID = "polyhaven_tree_small_02_1k"
DESTINATION = "/Game/RaftSim/Environment/ExternalReview/PolyHaven/TreeSmall02_1K"
SOURCE_FILES = {
    "tree_small_02_1k.fbx": "442394b4d39dcefef6c54358becea3c86735f040f2601b2c0c082e3ecf3685c5",
    "textures/tree_small_02_branch_diff_1k.png": "a93ce54213c4a98cd01cb5c5f7ab46b77defcd66e1dd082e6912f6e60632e630",
    "textures/tree_small_02_branch_nor_gl_1k.png": "0338a1400391893fdf6c6cbd1c22a573d6ab2300ad771d4916184bf206e1a671",
    "textures/tree_small_02_branch_rough_1k.png": "f285a54d141f30e39c7741e84a813c5cbccd9e9ee397af687176213f77d3e9a5",
    "textures/tree_small_02_diff_1k.jpg": "4e0093f407b3a1120a36de49a48ebe5a465a9a9b77e361c7a3e66866e115e404",
    "textures/tree_small_02_leaves_alpha_1k.png": "4f143e2dda8a6a572f427ac378b92255d21761e4611de0d26e21816c01aa533b",
    "textures/tree_small_02_leaves_diff_1k.png": "d3fc48522c76aa1f91076c6b86f302669822ebe4e2acabd67d42c4d57eaa5ba0",
    "textures/tree_small_02_leaves_nor_gl_1k.png": "fa4ad390f2e68b745db8f568cad64c3272696c5e01312ae564795e37724d79b8",
    "textures/tree_small_02_leaves_rough_1k.png": "f005213467e38bcb355b00c9a6eb9896b8d810ee885d5c7fa308d9f3326ef602",
    "textures/tree_small_02_nor_gl_1k.exr": "cf999e30663267b55b6fab43ca97c1e96176bdc67268e6c25854d53f15267d64",
    "textures/tree_small_02_rough_1k.exr": "1ed5ad24397c065beb2b2d3521470730f24e957cbd5fb323ad3f9b6d267b4585",
}
TEXTURE_NAMES = {
    "textures/tree_small_02_branch_diff_1k.png": "T_TreeSmall02_Branch_BaseColor_1K",
    "textures/tree_small_02_branch_nor_gl_1k.png": "T_TreeSmall02_Branch_NormalGL_1K",
    "textures/tree_small_02_branch_rough_1k.png": "T_TreeSmall02_Branch_Roughness_1K",
    "textures/tree_small_02_diff_1k.jpg": "T_TreeSmall02_Trunk_BaseColor_1K",
    "textures/tree_small_02_leaves_alpha_1k.png": "T_TreeSmall02_Leaves_Opacity_1K",
    "textures/tree_small_02_leaves_diff_1k.png": "T_TreeSmall02_Leaves_BaseColor_1K",
    "textures/tree_small_02_leaves_nor_gl_1k.png": "T_TreeSmall02_Leaves_NormalGL_1K",
    "textures/tree_small_02_leaves_rough_1k.png": "T_TreeSmall02_Leaves_Roughness_1K",
    "textures/tree_small_02_nor_gl_1k.exr": "T_TreeSmall02_Trunk_NormalGL_1K",
    "textures/tree_small_02_rough_1k.exr": "T_TreeSmall02_Trunk_Roughness_1K",
}
MATERIAL_SPECS = {
    "branches": {
        "name": "M_TreeSmall02_Branches",
        "base": "textures/tree_small_02_branch_diff_1k.png",
        "normal": "textures/tree_small_02_branch_nor_gl_1k.png",
        "roughness": "textures/tree_small_02_branch_rough_1k.png",
    },
    "leaves": {
        "name": "M_TreeSmall02_Leaves",
        "base": "textures/tree_small_02_leaves_diff_1k.png",
        "normal": "textures/tree_small_02_leaves_nor_gl_1k.png",
        "roughness": "textures/tree_small_02_leaves_rough_1k.png",
        "opacity": "textures/tree_small_02_leaves_alpha_1k.png",
    },
    "trunk": {
        "name": "M_TreeSmall02_Trunk",
        "base": "textures/tree_small_02_diff_1k.jpg",
        "normal": "textures/tree_small_02_nor_gl_1k.exr",
        "roughness": "textures/tree_small_02_rough_1k.exr",
    },
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


def import_mesh(source_root: Path) -> tuple[unreal.StaticMesh, int | None, str]:
    existing = [
        unreal.load_asset(path)
        for path in unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=False)
    ]
    existing_meshes = [asset for asset in existing if isinstance(asset, unreal.StaticMesh)]
    if existing_meshes:
        mesh = existing_meshes[0]
        return mesh, None, "not_recomputed_from_existing_nanite_asset"

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
    task.filename = str(source_root / "tree_small_02_1k.fbx")
    task.destination_path = DESTINATION
    task.destination_name = "SM_TreeSmall02"
    task.replace_existing = False
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    paths = import_tasks([task])
    meshes = [unreal.load_asset(path) for path in paths]
    meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one broadleaf mesh, imported {len(meshes)}: {paths}")
    return meshes[0], meshes[0].get_num_triangles(0), "measured_before_nanite_enable"


def import_textures(source_root: Path) -> dict[str, unreal.Texture2D]:
    textures = {}
    tasks = []
    task_keys = []
    for relative_path, asset_name in TEXTURE_NAMES.items():
        texture = unreal.load_asset(f"{DESTINATION}/{asset_name}")
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
            paths = list(task.imported_object_paths)
            if len(paths) != 1:
                raise RuntimeError(f"Texture import for {relative_path} produced {paths}")
            texture = unreal.load_asset(paths[0])
            if not isinstance(texture, unreal.Texture2D):
                raise RuntimeError(f"Imported object is not Texture2D: {paths[0]}")
            textures[relative_path] = texture
    for relative_path, texture in textures.items():
        texture.set_editor_property("srgb", "_diff_" in relative_path)
        if "_nor_gl_" in relative_path:
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            texture.set_editor_property("flip_green_channel", True)
        elif "_rough_" in relative_path or "_alpha_" in relative_path:
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        texture.modify()
    return textures


def load_or_create_material(
    spec: dict[str, str], textures: dict[str, unreal.Texture2D]
) -> unreal.Material:
    existing = unreal.load_asset(f"{DESTINATION}/{spec['name']}")
    if isinstance(existing, unreal.Material):
        configure_existing_sampler_types(existing)
        existing.modify()
        unreal.MaterialEditingLibrary.recompile_material(existing)
        return existing
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        spec["name"], DESTINATION, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create {spec['name']}")
    base = texture_sample(
        material, textures[spec["base"]], -640, -160, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR
    )
    normal = texture_sample(
        material, textures[spec["normal"]], -640, 40, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    )
    roughness = texture_sample(
        material, textures[spec["roughness"]], -640, 240, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
    )
    unreal.MaterialEditingLibrary.connect_material_property(base, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
    unreal.MaterialEditingLibrary.connect_material_property(roughness, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    if "opacity" in spec:
        opacity = texture_sample(
            material,
            textures[spec["opacity"]],
            -640,
            430,
            unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            opacity, "R", unreal.MaterialProperty.MP_OPACITY_MASK
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            base, "RGB", unreal.MaterialProperty.MP_SUBSURFACE_COLOR
        )
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        material.set_editor_property("two_sided", True)
        material.set_editor_property(
            "shading_model", unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE
        )
        material.set_editor_property("opacity_mask_clip_value", 0.22)
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
        role = "leaves" if "leaves" in lower_name else ("branches" if "branch" in lower_name else "trunk")
        mesh.set_material(index, materials[role])
        assigned_roles.add(role)
        slot_records.append(
            {"index": index, "slot_name": slot_name, "role": role, "material": materials[role].get_path_name()}
        )
    if assigned_roles != {"branches", "leaves", "trunk"}:
        raise RuntimeError(f"Expected trunk/branches/leaves slots, assigned {sorted(assigned_roles)}")

    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    bounds = mesh.get_bounding_box()
    persisted = subsystem.get_lod_build_settings(mesh, 0)
    bounds_scale = persisted.build_scale3d.z if (bounds.max.z - bounds.min.z) < 100.0 else 1.0
    height_cm = (bounds.max.z - bounds.min.z) * bounds_scale
    center_x = (bounds.min.x + bounds.max.x) * 0.5 * bounds_scale
    center_y = (bounds.min.y + bounds.max.y) * 0.5 * bounds_scale
    pivot_offset = (center_x * center_x + center_y * center_y) ** 0.5
    footprint_min_x = bounds.min.x * bounds_scale
    footprint_max_x = bounds.max.x * bounds_scale
    footprint_min_y = bounds.min.y * bounds_scale
    footprint_max_y = bounds.max.y * bounds_scale
    base_z = bounds.min.z * bounds_scale
    pivot_within_footprint = (
        footprint_min_x <= 0.0 <= footprint_max_x
        and footprint_min_y <= 0.0 <= footprint_max_y
    )
    base_contact_tolerance = max(5.0, height_cm * 0.025)
    pivot_meets_ground = abs(base_z) <= base_contact_tolerance
    record = {
        "asset_path": mesh.get_path_name(),
        "source_triangle_count_lod0": source_triangle_count,
        "source_triangle_count_status": source_triangle_count_status,
        "publisher_reported_triangle_count_label": "5M",
        "nanite_fallback_triangle_count_lod0": mesh.get_num_triangles(0),
        "effective_height_cm": height_cm,
        "plausible_tree_height": 350.0 <= height_cm <= 700.0,
        "canopy_center_xy_offset_from_pivot_cm": pivot_offset,
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
    if not record["plausible_tree_height"] or not record["valid_for_instancing"]:
        raise RuntimeError(
            "Broadleaf candidate failed physical-scale or instancing-pivot validation: "
            + json.dumps(record, sort_keys=True)
        )
    return record


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_REVIEWED_BROADLEAF_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir()) / "RaftSim" / "reviewed_broadleaf_import.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed broadleaf import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_biome_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        root_text = os.environ.get("RAFTSIM_REVIEWED_BROADLEAF_SOURCE_ROOT", "").strip()
        if not root_text:
            raise RuntimeError("RAFTSIM_REVIEWED_BROADLEAF_SOURCE_ROOT is required")
        root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(root)
        mesh, source_triangle_count, source_triangle_count_status = import_mesh(root)
        textures = import_textures(root)
        materials = {
            role: load_or_create_material(spec, textures) for role, spec in MATERIAL_SPECS.items()
        }
        for asset in [*textures.values(), *materials.values()]:
            unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        report["mesh"] = configure_mesh(
            mesh,
            source_triangle_count,
            source_triangle_count_status,
            materials,
        )
        report["textures"] = sorted(texture.get_path_name() for texture in textures.values())
        report["materials"] = sorted(material.get_path_name() for material in materials.values())
        report["status"] = "isolated_review_candidate_imported"
        write_report(report)
        unreal.log(f"RaftSim imported reviewed broadleaf candidate {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
