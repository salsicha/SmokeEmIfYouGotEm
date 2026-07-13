"""Import the rights-reviewed Futaleufu adult broadleaf structure-analog set."""

from __future__ import annotations

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
    sha256,
    texture_sample,
)


ASSET_ID = "polyhaven_futaleufu_island_tree_set_1k"
DESTINATION = "/Game/RaftSim/Environment/ExternalReview/PolyHaven/FutaleufuIslandTreeSet_1K"
TREE_IDS = ("island_tree_01", "island_tree_02", "island_tree_03")
PUBLISHER_WIDTH_CM = {
    "island_tree_01": 1250.0,
    "island_tree_02": 850.0,
    "island_tree_03": 850.0,
}
SOURCE_FILES = {
    "island_tree_01/island_tree_01_1k.fbx": "3f193c0ca27977b001682aa4ba3eef654b31c1af60a166af4024a11cc19a2948",
    "island_tree_01/textures/island_tree_01_diff_1k.png": "519a34062e3eb42e14d9f2b6454669d8e71ccf0ab0b95fe05e00f31ee7ffdf29",
    "island_tree_01/textures/island_tree_01_nor_gl_1k.png": "039b67b309fd3cf7333fbd8e2a8db0f253a87def5e7e9d88b06401d8f605ed1f",
    "island_tree_01/textures/island_tree_01_rough_1k.png": "eab3874d010768431baac106ca2904e8bfb7736e6fa17fecf24855ca37bcf565",
    "island_tree_01/textures/island_tree_01_branches_diff_1k.png": "4485125d88b9dcce618220e8850f8b3ec586d9cdebe08e28aca777206eef56e2",
    "island_tree_01/textures/island_tree_01_branches_nor_gl_1k.png": "e72c3bf652d998d75ef98fc51fb7a10de3b7efd072c191a8eb9c92b6f93340f0",
    "island_tree_01/textures/island_tree_01_branches_rough_1k.png": "c6db3c33f23654a8d31dcf5609d19d97ab1036b36b3d9a6bcd50ecc975f8fb3c",
    "island_tree_01/textures/island_tree_01_leaves_alpha_1k.png": "f4341f147988dbe6b58d9ca841a8f0e4bcff25bc40d05f9877da82006d489c39",
    "island_tree_01/textures/island_tree_01_leaves_diff_1k.png": "63d3563a22a62151f338ceb4e992de7c31b62e8e3582e2762d5071f02d286349",
    "island_tree_01/textures/island_tree_01_leaves_nor_gl_1k.png": "e58402f30c7108ec6321e0c689009508f6ab138c81612d9a67238038ac108211",
    "island_tree_01/textures/island_tree_01_leaves_rough_1k.png": "b7e9a1857f63617344968bb43693786bfed7dd15bedca3193ce333f233fbab78",
    "island_tree_02/island_tree_02_1k.fbx": "ac2489d7c5b76cbe050a4f78d1984d614c2a7b0cfbe617b95836859613ab6d76",
    "island_tree_02/textures/island_tree_02_diff_1k.png": "398424083d2db299f5445e7c6422498688643f634767383ba8cd8bbfbfb0b27b",
    "island_tree_02/textures/island_tree_02_nor_gl_1k.png": "0c300f7a5da76c57b5e8475d32e3e60fa7605a29f52c1a38f2501f537aa2f3e2",
    "island_tree_02/textures/island_tree_02_rough_1k.png": "59add752a4dc6d898c54bef061e31a92b1632be6cdb638b15ea446f2d2d03603",
    "island_tree_02/textures/island_tree_02_branches_diff_1k.png": "4485125d88b9dcce618220e8850f8b3ec586d9cdebe08e28aca777206eef56e2",
    "island_tree_02/textures/island_tree_02_branches_nor_gl_1k.png": "e72c3bf652d998d75ef98fc51fb7a10de3b7efd072c191a8eb9c92b6f93340f0",
    "island_tree_02/textures/island_tree_02_branches_rough_1k.png": "c6db3c33f23654a8d31dcf5609d19d97ab1036b36b3d9a6bcd50ecc975f8fb3c",
    "island_tree_02/textures/island_tree_02_leaves_alpha_1k.png": "f4341f147988dbe6b58d9ca841a8f0e4bcff25bc40d05f9877da82006d489c39",
    "island_tree_02/textures/island_tree_02_leaves_diff_1k.png": "63d3563a22a62151f338ceb4e992de7c31b62e8e3582e2762d5071f02d286349",
    "island_tree_02/textures/island_tree_02_leaves_nor_gl_1k.png": "e58402f30c7108ec6321e0c689009508f6ab138c81612d9a67238038ac108211",
    "island_tree_02/textures/island_tree_02_leaves_rough_1k.png": "b7e9a1857f63617344968bb43693786bfed7dd15bedca3193ce333f233fbab78",
    "island_tree_03/island_tree_03_1k.fbx": "32b2a158689fde1df5f55bad89b1eb4f131bacf534fac45155fc1d4c49afba49",
    "island_tree_03/textures/island_tree_03_diff_1k.png": "264330f1ae3998fe5620ec85fd175628bfabd79f80d25f777e18274997fd916f",
    "island_tree_03/textures/island_tree_03_nor_gl_1k.png": "886c7e7468e9485626510308d03160d7b73789d584165bfa412e7b36ee5dc5b6",
    "island_tree_03/textures/island_tree_03_rough_1k.png": "7a49a0de9979eaf33a2226aebb6e540cb0bc2e5a2725b19046f1bf1026953fb8",
    "island_tree_03/textures/island_tree_03_branches_diff_1k.png": "4485125d88b9dcce618220e8850f8b3ec586d9cdebe08e28aca777206eef56e2",
    "island_tree_03/textures/island_tree_03_branches_nor_gl_1k.png": "e72c3bf652d998d75ef98fc51fb7a10de3b7efd072c191a8eb9c92b6f93340f0",
    "island_tree_03/textures/island_tree_03_branches_rough_1k.png": "c6db3c33f23654a8d31dcf5609d19d97ab1036b36b3d9a6bcd50ecc975f8fb3c",
    "island_tree_03/textures/island_tree_03_leaves_alpha_1k.png": "f4341f147988dbe6b58d9ca841a8f0e4bcff25bc40d05f9877da82006d489c39",
    "island_tree_03/textures/island_tree_03_leaves_diff_1k.png": "63d3563a22a62151f338ceb4e992de7c31b62e8e3582e2762d5071f02d286349",
    "island_tree_03/textures/island_tree_03_leaves_nor_gl_1k.png": "e58402f30c7108ec6321e0c689009508f6ab138c81612d9a67238038ac108211",
    "island_tree_03/textures/island_tree_03_leaves_rough_1k.png": "b7e9a1857f63617344968bb43693786bfed7dd15bedca3193ce333f233fbab78",
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


def label(tree_id: str) -> str:
    return "".join(token.title() for token in tree_id.split("_"))


def import_tree_mesh(source_root: Path, tree_id: str) -> unreal.StaticMesh:
    prefix = f"SM_{label(tree_id)}"
    existing = []
    for path in unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=False):
        asset = unreal.load_asset(path)
        if isinstance(asset, unreal.StaticMesh) and (
            asset.get_name() == prefix or asset.get_name().startswith(f"{prefix}_")
        ):
            existing.append(asset)
    if len(existing) == 1:
        return existing[0]

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
    task.filename = str(source_root / tree_id / f"{tree_id}_1k.fbx")
    task.destination_path = DESTINATION
    task.destination_name = prefix
    task.replace_existing = bool(existing)
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    imported_paths = import_tasks([task])
    meshes = [unreal.load_asset(path) for path in imported_paths]
    meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one {tree_id} mesh, imported {len(meshes)}: {imported_paths}")
    return meshes[0]


def texture_asset_name(relative_path: str) -> str:
    tree_id, _, filename = relative_path.partition("/textures/")
    tokens = "".join(token.title() for token in Path(filename).stem.split("_"))
    return f"T_{label(tree_id)}_{tokens}"


def import_textures(source_root: Path) -> dict[str, unreal.Texture2D]:
    textures: dict[str, unreal.Texture2D] = {}
    tasks = []
    task_keys = []
    for relative_path in SOURCE_FILES:
        if "/textures/" not in relative_path:
            continue
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
        elif "_rough_" in relative_path or "_alpha_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
            )
        texture.modify()
    return textures


def load_or_create_material(
    name: str,
    base_path: str,
    normal_path: str,
    roughness_path: str,
    alpha_path: str | None,
    textures: dict[str, unreal.Texture2D],
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
        material, textures[base_path], -640, -140, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR
    )
    normal = texture_sample(
        material, textures[normal_path], -640, 40, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    )
    roughness = texture_sample(
        material, textures[roughness_path], -640, 220, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
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
    if alpha_path:
        alpha = texture_sample(
            material,
            textures[alpha_path],
            -640,
            400,
            unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            alpha, "R", unreal.MaterialProperty.MP_OPACITY_MASK
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


def create_materials(
    textures: dict[str, unreal.Texture2D]
) -> dict[str, dict[str, unreal.Material]]:
    materials = {}
    for tree_id in TREE_IDS:
        root = f"{tree_id}/textures/{tree_id}"
        tree_label = label(tree_id)
        materials[tree_id] = {
            "trunk": load_or_create_material(
                f"M_{tree_label}_Trunk",
                f"{root}_diff_1k.png",
                f"{root}_nor_gl_1k.png",
                f"{root}_rough_1k.png",
                None,
                textures,
            ),
            "branches": load_or_create_material(
                f"M_{tree_label}_Branches",
                f"{root}_branches_diff_1k.png",
                f"{root}_branches_nor_gl_1k.png",
                f"{root}_branches_rough_1k.png",
                None,
                textures,
            ),
            "leaves": load_or_create_material(
                f"M_{tree_label}_Leaves",
                f"{root}_leaves_diff_1k.png",
                f"{root}_leaves_nor_gl_1k.png",
                f"{root}_leaves_rough_1k.png",
                f"{root}_leaves_alpha_1k.png",
                textures,
            ),
        }
    return materials


def configure_mesh(
    tree_id: str,
    mesh: unreal.StaticMesh,
    materials: dict[str, unreal.Material],
) -> dict[str, object]:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not subsystem:
        raise RuntimeError("StaticMeshEditorSubsystem is unavailable")
    initial_bounds = mesh.get_bounding_box()
    preconfiguration_triangles = mesh.get_num_triangles(0)
    build_settings = subsystem.get_lod_build_settings(mesh, 0)
    if (
        initial_bounds.max.z - initial_bounds.min.z < 100.0
        and build_settings.build_scale3d.z < 99.0
    ):
        build_settings.build_scale3d = unreal.Vector(100.0, 100.0, 100.0)
        subsystem.set_lod_build_settings(mesh, 0, build_settings)

    build_settings = subsystem.get_lod_build_settings(mesh, 0)
    raw_width = max(
        initial_bounds.max.x - initial_bounds.min.x,
        initial_bounds.max.y - initial_bounds.min.y,
    )
    imported_width_cm = raw_width * build_settings.build_scale3d.z
    target_width_cm = PUBLISHER_WIDTH_CM[tree_id]
    width_scale_ratio = target_width_cm / max(1.0, imported_width_cm)
    if not 0.9 <= imported_width_cm / target_width_cm <= 1.1:
        build_settings.build_scale3d = unreal.Vector(
            build_settings.build_scale3d.x * width_scale_ratio,
            build_settings.build_scale3d.y * width_scale_ratio,
            build_settings.build_scale3d.z * width_scale_ratio,
        )
        subsystem.set_lod_build_settings(mesh, 0, build_settings)

    nanite_settings = subsystem.get_nanite_settings(mesh)
    nanite_settings.enabled = True
    if hasattr(unreal, "NaniteShapePreservation"):
        nanite_settings.shape_preservation = unreal.NaniteShapePreservation.PRESERVE_AREA
    subsystem.set_nanite_settings(mesh, nanite_settings)

    slots = []
    roles = set()
    for slot_index, static_material in enumerate(mesh.static_materials):
        slot_name = str(static_material.material_slot_name)
        lower = slot_name.lower()
        role = "leaves" if "leaves" in lower else ("branches" if "branches" in lower else "trunk")
        mesh.set_material(slot_index, materials[role])
        roles.add(role)
        slots.append(
            {
                "index": slot_index,
                "slot_name": slot_name,
                "role": role,
                "material": materials[role].get_path_name(),
            }
        )
    if roles != {"trunk", "branches", "leaves"}:
        raise RuntimeError(f"{tree_id} lacks expected material roles: {slots}")
    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    bounds = mesh.get_bounding_box()
    persisted = subsystem.get_lod_build_settings(mesh, 0)
    raw_height = bounds.max.z - bounds.min.z
    scale = persisted.build_scale3d.z if raw_height < 100.0 else 1.0
    height_cm = raw_height * scale
    width_cm = max(bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y) * scale
    base_z_cm = bounds.min.z * scale
    base_tolerance_cm = max(8.0, height_cm * 0.025)
    record = {
        "asset_path": mesh.get_path_name(),
        "tree_id": tree_id,
        "preconfiguration_triangle_count_lod0": preconfiguration_triangles,
        "nanite_fallback_triangle_count_lod0": mesh.get_num_triangles(0),
        "height_cm": height_cm,
        "width_cm": width_cm,
        "publisher_width_cm": target_width_cm,
        "publisher_width_scale_ratio": width_scale_ratio,
        "publisher_width_relative_error": abs(width_cm - target_width_cm) / target_width_cm,
        "plausible_physical_height": 300.0 <= height_cm <= 3000.0,
        "plausible_crown_width": 400.0 <= width_cm <= 2000.0,
        "base_z_cm": base_z_cm,
        "base_contact_tolerance_cm": base_tolerance_cm,
        "pivot_meets_ground": abs(base_z_cm) <= base_tolerance_cm,
        "pivot_within_footprint": (
            bounds.min.x <= 0.0 <= bounds.max.x and bounds.min.y <= 0.0 <= bounds.max.y
        ),
        "lod0_build_scale": [
            persisted.build_scale3d.x,
            persisted.build_scale3d.y,
            persisted.build_scale3d.z,
        ],
        "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
        "nanite_shape_preservation": str(subsystem.get_nanite_settings(mesh).shape_preservation),
        "material_slots": slots,
    }
    if (
        not record["plausible_physical_height"]
        or not record["plausible_crown_width"]
        or record["publisher_width_relative_error"] > 0.02
    ):
        raise RuntimeError("Island-tree candidate failed physical-size gate: " + json.dumps(record))
    if not record["pivot_meets_ground"] or not record["pivot_within_footprint"]:
        raise RuntimeError("Island-tree candidate failed grounded-pivot gate: " + json.dumps(record))
    return record


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_FUTALEUFU_ISLAND_TREE_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir()) / "RaftSim" / "reviewed_island_tree_import.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed Futaleufu island-tree import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_environment_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        root_text = os.environ.get("RAFTSIM_FUTALEUFU_ISLAND_TREE_SOURCE_ROOT", "").strip()
        if not root_text:
            raise RuntimeError("RAFTSIM_FUTALEUFU_ISLAND_TREE_SOURCE_ROOT is required")
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        meshes = {tree_id: import_tree_mesh(source_root, tree_id) for tree_id in TREE_IDS}
        textures = import_textures(source_root)
        materials = create_materials(textures)
        for asset in [
            *textures.values(),
            *(material for tree_materials in materials.values() for material in tree_materials.values()),
        ]:
            unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        report["meshes"] = [
            configure_mesh(tree_id, meshes[tree_id], materials[tree_id]) for tree_id in TREE_IDS
        ]
        report["textures"] = sorted(texture.get_path_name() for texture in textures.values())
        report["materials"] = sorted(
            material.get_path_name()
            for tree_materials in materials.values()
            for material in tree_materials.values()
        )
        report["status"] = "isolated_review_candidate_imported"
        write_report(report)
        unreal.log(f"RaftSim imported reviewed Futaleufu island-tree set {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
