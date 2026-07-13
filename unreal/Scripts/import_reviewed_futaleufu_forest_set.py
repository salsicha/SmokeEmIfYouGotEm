"""Import the rights-reviewed Futaleufu temperate-forest candidate set."""

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


ASSET_ID = "polyhaven_futaleufu_temperate_forest_set_1k"
DESTINATION = (
    "/Game/RaftSim/Environment/ExternalReview/PolyHaven/FutaleufuTemperateForestSet_1K"
)
SOURCE_FILES = {
    "fir_sapling_medium/fir_sapling_medium_1k.fbx": "f09677355367e2a4a29b9542474049fcee311a2cc8aa561f9d316153cf5c33c4",
    "fir_sapling_medium/textures/fir_sapling_medium_branches_diff_1k.png": "508ca0a40d118beec98e8375b4611e8a16123eec94b5d2b4870617cf4d24e6fa",
    "fir_sapling_medium/textures/fir_sapling_medium_branches_nor_gl_1k.png": "b889e7080d6efb0592f83e64cc5a5afa5fb7787b4b7d1ae13a65602689e793e8",
    "fir_sapling_medium/textures/fir_sapling_medium_branches_rough_1k.png": "b198105d3022db6c459ae9c307ecdb7b644832ee20bcbfd89c3741cecc77881f",
    "fir_sapling_medium/textures/fir_sapling_medium_twigs_alpha_1k.png": "3f399629337e7ac3af27a01b08ffb9c0d60224a9dd374a1427761a5c2eea9d6e",
    "fir_sapling_medium/textures/fir_sapling_medium_twigs_diff_1k.png": "581df52e36fa3ea1d348df6b84e276fb3c88ee33cc182c2987eff61bf3daa513",
    "fir_sapling_medium/textures/fir_sapling_medium_twigs_nor_gl_1k.png": "cbb6b8179a9f7f6e84fd15d1f422bc342841d20845b2bad437612f03fb0067de",
    "fir_sapling_medium/textures/fir_sapling_medium_twigs_rough_1k.png": "a4f0a4c8bc93946dea229def779ffe5d32c555c717e4bf7b0e4b4d86bc21987a",
    "fir_sapling/fir_sapling_1k.fbx": "5eafd5fd2914639960238a6beef97c4d64be9fb0a5b690fd03d13b2291f71db1",
    "fir_sapling/textures/fir_sapling_branches_diff_1k.png": "8813b75888f3d76ae8581a09b7f9fdb8d2b7b0d3c7977ba32be1678373eee657",
    "fir_sapling/textures/fir_sapling_branches_nor_gl_1k.png": "86e1b91b1f7bfdf4505b465ea0e6271ed526d7a6354a0260119aa143bacc0671",
    "fir_sapling/textures/fir_sapling_branches_rough_1k.png": "8d96bd806bd7ebe73b69ddc38516533f0a616c1bfd0e6670fe7a99a34b23e371",
    "fir_sapling/textures/fir_sapling_twigs_alpha_1k.png": "91e8a6114e2f180de3d2fa60d397d69fee0d3c745a15e012da705c86cd4de976",
    "fir_sapling/textures/fir_sapling_twigs_diff_1k.png": "c29cb18884dc4cd24a72d0e39f01c1baeadb798d0fe3d196d82b8cb11b18f061",
    "fir_sapling/textures/fir_sapling_twigs_nor_gl_1k.png": "5e1ca8d4c227fae4dab854028775b9cac49201966cb18817a1040194b33ec98b",
    "fir_sapling/textures/fir_sapling_twigs_rough_1k.png": "64e351910b74d2450029713dc08f7cd1ff0bb0c0c5a17ce271a0c87527e38812",
    "fern_02/fern_02_1k.fbx": "6d8238b9cc1bbb5f5766396c2db26f2219c0d0e5ca226fb81dcc44bdb35045e8",
    "fern_02/textures/fern_02_alpha_1k.png": "ea3c64284c7ebdeedf484d2d816eae92825ec526140c3bb83859ddc7a64001f9",
    "fern_02/textures/fern_02_diff_1k.png": "f8f504bce117647f1df386cd7bc99a79c664bb49f82d1dd6412c83a700c48e94",
    "fern_02/textures/fern_02_nor_gl_1k.png": "438c065c60754ad410c5b4690df6547d06d9907b8d2c9c3a908cb135ffd52b97",
    "fern_02/textures/fern_02_rough_1k.png": "1485a265bcd40e5d9362c0ed56f9024df3ab5241dc9f83c8011165d2223c5d20",
}
MESH_SOURCES = (
    {
        "relative_path": "fir_sapling_medium/fir_sapling_medium_1k.fbx",
        "asset_prefix": "SM_FirSaplingMedium",
        "collection": "fir_sapling_medium",
        "stratum": "canopy",
        "expected_count": 3,
        "height_range_cm": (500.0, 3000.0),
    },
    {
        "relative_path": "fir_sapling/fir_sapling_1k.fbx",
        "asset_prefix": "SM_FirSapling",
        "collection": "fir_sapling",
        "stratum": "sapling",
        "expected_count": 3,
        "height_range_cm": (50.0, 500.0),
    },
    {
        "relative_path": "fern_02/fern_02_1k.fbx",
        "asset_prefix": "SM_Fern02",
        "collection": "fern_02",
        "stratum": "understory",
        "expected_count": 4,
        "height_range_cm": (10.0, 250.0),
    },
)


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


def import_mesh_collection(
    source_root: Path, source: dict[str, object]
) -> list[unreal.StaticMesh]:
    prefix = str(source["asset_prefix"])
    existing = []
    for path in unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=False):
        asset = unreal.load_asset(path)
        if isinstance(asset, unreal.StaticMesh) and asset.get_name().startswith(f"{prefix}_"):
            existing.append(asset)
    expected_count = int(source["expected_count"])
    if len(existing) == expected_count:
        meshes = existing
    else:
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
        task.filename = str(source_root / str(source["relative_path"]))
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

    if len(meshes) != expected_count:
        raise RuntimeError(
            f"Expected {expected_count} {source['collection']} meshes, imported {len(meshes)}"
        )
    return sorted(meshes, key=lambda asset: asset.get_name())


def texture_asset_name(relative_path: str) -> str:
    collection, _, filename = relative_path.partition("/textures/")
    stem = Path(filename).stem
    tokens = "".join(token.title() for token in stem.split("_"))
    collection_token = "".join(token.title() for token in collection.split("_"))
    return f"T_{collection_token}_{tokens}"


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


def create_materials(textures: dict[str, unreal.Texture2D]) -> dict[str, unreal.Material]:
    materials = {}
    for collection, label in (
        ("fir_sapling_medium", "FirSaplingMedium"),
        ("fir_sapling", "FirSapling"),
    ):
        root = f"{collection}/textures/{collection}"
        materials[f"{collection}_branches"] = load_or_create_material(
            f"M_{label}_Branches",
            f"{root}_branches_diff_1k.png",
            f"{root}_branches_nor_gl_1k.png",
            f"{root}_branches_rough_1k.png",
            None,
            textures,
        )
        materials[f"{collection}_twigs"] = load_or_create_material(
            f"M_{label}_Twigs",
            f"{root}_twigs_diff_1k.png",
            f"{root}_twigs_nor_gl_1k.png",
            f"{root}_twigs_rough_1k.png",
            f"{root}_twigs_alpha_1k.png",
            textures,
        )
    materials["fern_02_fronds"] = load_or_create_material(
        "M_Fern02_Fronds",
        "fern_02/textures/fern_02_diff_1k.png",
        "fern_02/textures/fern_02_nor_gl_1k.png",
        "fern_02/textures/fern_02_rough_1k.png",
        "fern_02/textures/fern_02_alpha_1k.png",
        textures,
    )
    return materials


def configure_meshes(
    meshes_by_collection: dict[str, list[unreal.StaticMesh]],
    materials: dict[str, unreal.Material],
) -> list[dict[str, object]]:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not subsystem:
        raise RuntimeError("StaticMeshEditorSubsystem is unavailable")
    records = []
    source_by_collection = {str(source["collection"]): source for source in MESH_SOURCES}
    for collection, meshes in meshes_by_collection.items():
        source = source_by_collection[collection]
        height_min, height_max = source["height_range_cm"]
        for mesh in meshes:
            initial_bounds = mesh.get_bounding_box()
            preconfiguration_triangle_count = mesh.get_num_triangles(0)
            build_settings = subsystem.get_lod_build_settings(mesh, 0)
            if (
                initial_bounds.max.z - initial_bounds.min.z < 100.0
                and build_settings.build_scale3d.z < 99.0
            ):
                build_settings.build_scale3d = unreal.Vector(100.0, 100.0, 100.0)
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
                if collection == "fern_02":
                    role = "fronds"
                elif "twig" in slot_name.lower():
                    role = "twigs"
                else:
                    role = "branches"
                material = materials[f"{collection}_{role}"]
                mesh.set_material(slot_index, material)
                roles.add(role)
                slots.append(
                    {
                        "index": slot_index,
                        "slot_name": slot_name,
                        "role": role,
                        "material": material.get_path_name(),
                    }
                )
            expected_roles = {"fronds"} if collection == "fern_02" else {"branches", "twigs"}
            if not expected_roles.issubset(roles):
                raise RuntimeError(
                    f"{collection} mesh {mesh.get_name()} lacks expected roles {expected_roles}: {slots}"
                )
            mesh.modify()
            unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

            bounds = mesh.get_bounding_box()
            persisted = subsystem.get_lod_build_settings(mesh, 0)
            raw_height = bounds.max.z - bounds.min.z
            scale = persisted.build_scale3d.z if raw_height < 100.0 else 1.0
            height_cm = raw_height * scale
            width_cm = max(bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y) * scale
            base_z_cm = bounds.min.z * scale
            base_tolerance_cm = max(5.0, height_cm * 0.025)
            record = {
                "asset_path": mesh.get_path_name(),
                "collection": collection,
                "stratum": source["stratum"],
                "preconfiguration_triangle_count_lod0": preconfiguration_triangle_count,
                "nanite_fallback_triangle_count_lod0": mesh.get_num_triangles(0),
                "height_cm": height_cm,
                "width_cm": width_cm,
                "plausible_physical_height": height_min <= height_cm <= height_max,
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
                "nanite_shape_preservation": str(
                    subsystem.get_nanite_settings(mesh).shape_preservation
                ),
                "material_slots": slots,
            }
            if not record["plausible_physical_height"]:
                raise RuntimeError(
                    f"{collection} candidate failed physical-height gate: "
                    + json.dumps(record, sort_keys=True)
                )
            if not record["pivot_meets_ground"] or not record["pivot_within_footprint"]:
                raise RuntimeError(
                    f"{collection} candidate failed grounded-pivot gate: "
                    + json.dumps(record, sort_keys=True)
                )
            records.append(record)
    return records


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_FUTALEUFU_FOREST_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir())
        / "RaftSim"
        / "reviewed_futaleufu_forest_import.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed Futaleufu forest import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_environment_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        root_text = os.environ.get("RAFTSIM_FUTALEUFU_FOREST_SOURCE_ROOT", "").strip()
        if not root_text:
            raise RuntimeError("RAFTSIM_FUTALEUFU_FOREST_SOURCE_ROOT is required")
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        meshes_by_collection = {
            str(source["collection"]): import_mesh_collection(source_root, source)
            for source in MESH_SOURCES
        }
        textures = import_textures(source_root)
        materials = create_materials(textures)
        for asset in [*textures.values(), *materials.values()]:
            unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        report["meshes"] = configure_meshes(meshes_by_collection, materials)
        report["variant_counts"] = {
            collection: len(meshes) for collection, meshes in meshes_by_collection.items()
        }
        report["textures"] = sorted(texture.get_path_name() for texture in textures.values())
        report["materials"] = sorted(material.get_path_name() for material in materials.values())
        report["status"] = "isolated_review_candidate_imported"
        write_report(report)
        unreal.log(f"RaftSim imported reviewed Futaleufu forest candidate {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
