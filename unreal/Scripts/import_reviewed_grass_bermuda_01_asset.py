"""Import Poly Haven Grass Bermuda 01 as an isolated CC0 ground-cover family."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_reviewed_biome_asset import import_tasks, texture_sample  # noqa: E402


ASSET_ID = "polyhaven_grass_bermuda_01_1k"
DESTINATION = (
    "/Game/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K"
)
SOURCE_FILES = {
    "grass_bermuda_01_1k.fbx": (
        "ec188edf028e1a76ed2e63f7483165ea765f0212b317e4b73fdc3d64610500cd"
    ),
    "grass_bermuda_01_1k_unreal.fbx": (
        "26922691fd6f21becacfd9aa5946feaefa97ac80d96aa9fe113eed8a3f8d4f87"
    ),
    "grass_bermuda_01_alpha_1k.png": (
        "e58b3052aad2f107cdd763e437f80ed8fb5a31bcc43b44023f7f767cb3d9888e"
    ),
    "grass_bermuda_01_diff_1k.jpg": (
        "ef202eeb8f8fb3312446009acecc87e5679a7d612e4dee859d8a849e00af5fcb"
    ),
    "grass_bermuda_01_nor_gl_1k.png": (
        "a76b2da43fd741ffbf37e9fd7f37db241d6684afcbe84962dac08cfdc59ff385"
    ),
    "grass_bermuda_01_rough_1k.png": (
        "e316fd8d508cd3afaf686cee2a7bee139f2461b85e5ddc4a8c456cad07363483"
    ),
}
TEXTURES = {
    "grass_bermuda_01_alpha_1k.png": "T_GrassBermuda01_Opacity_1K",
    "grass_bermuda_01_diff_1k.jpg": "T_GrassBermuda01_BaseColor_1K",
    "grass_bermuda_01_nor_gl_1k.png": "T_GrassBermuda01_NormalGL_1K",
    "grass_bermuda_01_rough_1k.png": "T_GrassBermuda01_Roughness_1K",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sources(root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for relative_path, expected_hash in SOURCE_FILES.items():
        path = root / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Missing reviewed source file: {path}")
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"Hash mismatch for {relative_path}: expected {expected_hash}, "
                f"got {actual_hash}"
            )
        records.append(
            {
                "relative_path": relative_path,
                "sha256": actual_hash,
                "bytes": path.stat().st_size,
            }
        )
    return records


def import_textures(root: Path) -> dict[str, unreal.Texture2D]:
    result: dict[str, unreal.Texture2D] = {}
    tasks: list[unreal.AssetImportTask] = []
    task_keys: list[str] = []
    for relative_path, asset_name in TEXTURES.items():
        existing = unreal.load_asset(f"{DESTINATION}/{asset_name}")
        if isinstance(existing, unreal.Texture2D):
            result[relative_path] = existing
            continue
        task = unreal.AssetImportTask()
        task.filename = str(root / relative_path)
        task.destination_path = DESTINATION
        task.destination_name = asset_name
        task.replace_existing = False
        task.automated = True
        task.save = False
        tasks.append(task)
        task_keys.append(relative_path)
    import_tasks(tasks)
    for relative_path, task in zip(task_keys, tasks):
        paths = list(task.imported_object_paths)
        if len(paths) != 1:
            raise RuntimeError(f"Texture import for {relative_path} produced {paths}")
        texture = unreal.load_asset(paths[0])
        if not isinstance(texture, unreal.Texture2D):
            raise RuntimeError(f"Imported object is not Texture2D: {paths[0]}")
        texture.set_editor_property("srgb", "_diff_" in relative_path)
        if "_nor_gl_" in relative_path:
            texture.set_editor_property(
                "compression_settings",
                unreal.TextureCompressionSettings.TC_NORMALMAP,
            )
            texture.set_editor_property("flip_green_channel", True)
        elif "_rough_" in relative_path or "_alpha_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
            )
        texture.modify()
        result[relative_path] = texture
    return result


def create_material(textures: dict[str, unreal.Texture2D]) -> unreal.Material:
    existing = unreal.load_asset(f"{DESTINATION}/M_GrassBermuda01_Foliage")
    if isinstance(existing, unreal.Material):
        unreal.MaterialEditingLibrary.recompile_material(existing)
        return existing
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_GrassBermuda01_Foliage",
        DESTINATION,
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError("Could not create Grass Bermuda 01 material")
    base = texture_sample(
        material,
        textures["grass_bermuda_01_diff_1k.jpg"],
        -640,
        -180,
        unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
    )
    normal = texture_sample(
        material,
        textures["grass_bermuda_01_nor_gl_1k.png"],
        -640,
        20,
        unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    )
    roughness = texture_sample(
        material,
        textures["grass_bermuda_01_rough_1k.png"],
        -640,
        220,
        unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    )
    opacity = texture_sample(
        material,
        textures["grass_bermuda_01_alpha_1k.png"],
        -640,
        420,
        unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "RGB", unreal.MaterialProperty.MP_SUBSURFACE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        normal, "RGB", unreal.MaterialProperty.MP_NORMAL
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness, "R", unreal.MaterialProperty.MP_ROUGHNESS
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


def import_meshes(root: Path, material: unreal.Material) -> list[dict[str, object]]:
    existing_paths = unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=False)
    meshes = [
        unreal.load_asset(path)
        for path in existing_paths
        if "SM_GrassBermuda01_" in path
    ]
    meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    imported_paths: list[str] = []
    if not meshes:
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
        task.filename = str(root / "grass_bermuda_01_1k_unreal.fbx")
        task.destination_path = DESTINATION
        task.destination_name = "SM_GrassBermuda01"
        task.replace_existing = False
        task.automated = True
        task.save = False
        task.factory = unreal.FbxFactory()
        task.options = options
        imported_paths = import_tasks([task])
        meshes = [unreal.load_asset(path) for path in imported_paths]
        meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    meshes.sort(key=lambda mesh: mesh.get_path_name())
    if len(meshes) < 16:
        raise RuntimeError(
            "Expected at least sixteen Bermuda grass forms, imported "
            f"{len(meshes)}: {imported_paths}"
        )

    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not subsystem:
        raise RuntimeError("StaticMeshEditorSubsystem is unavailable")
    records: list[dict[str, object]] = []
    for mesh in meshes:
        raw_bounds = mesh.get_bounding_box()
        build_settings = subsystem.get_lod_build_settings(mesh, 0)
        if raw_bounds.max.z - raw_bounds.min.z < 10.0 and build_settings.build_scale3d.z < 999.0:
            # The FBX stores metre-authored foliage in Blender unit space.
            # Unreal's static-mesh source bounds are centimetres, so a 1000x
            # build scale restores the publisher form heights to roughly
            # 0.25--1.47 m instead of importing 2--15 cm miniatures.
            build_settings.build_scale3d = unreal.Vector(1000.0, 1000.0, 1000.0)
            subsystem.set_lod_build_settings(mesh, 0, build_settings)
        # These are 6--28 triangle masked cards. Conventional instanced
        # rasterization preserves their thin silhouettes; Nanite cluster
        # reduction can cull the entire form at guide-eye distance.
        nanite = subsystem.get_nanite_settings(mesh)
        nanite.enabled = False
        subsystem.set_nanite_settings(mesh, nanite)
        for index in range(len(mesh.static_materials)):
            mesh.set_material(index, material)
        mesh.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

        bounds = mesh.get_bounding_box()
        persisted = subsystem.get_lod_build_settings(mesh, 0)
        scale = persisted.build_scale3d.z if bounds.max.z - bounds.min.z < 10.0 else 1.0
        height_cm = (bounds.max.z - bounds.min.z) * scale
        width_cm = max(bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y) * scale
        base_z_cm = bounds.min.z * scale
        if not (20.0 <= height_cm <= 160.0 and 20.0 <= width_cm <= 100.0):
            raise RuntimeError(
                f"Grass form failed scale validation: {mesh.get_path_name()} "
                f"height={height_cm:.3f} width={width_cm:.3f}"
            )
        if abs(base_z_cm) > max(15.0, height_cm * 0.35):
            raise RuntimeError(
                f"Grass form failed base validation: {mesh.get_path_name()} "
                f"base={base_z_cm:.3f}"
            )
        records.append(
            {
                "asset_path": mesh.get_path_name(),
                "triangle_count_lod0": mesh.get_num_triangles(0),
                "effective_height_cm": height_cm,
                "effective_width_cm": width_cm,
                "base_z_cm": base_z_cm,
                "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
                "material_slots": len(mesh.static_materials),
            }
        )
    return records


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_REVIEWED_GRASS_BERMUDA_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir())
        / "RaftSim"
        / "reviewed_grass_bermuda_01_import.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed Grass Bermuda 01 import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_biome_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
        "source_page": "https://polyhaven.com/a/grass_bermuda_01",
        "license": "CC0",
        "author": "Rico Cilliers",
        "publisher_reported_triangle_count": 224000,
        "publisher_reported_collection_width_m": 3.1,
    }
    try:
        root_text = os.environ.get(
            "RAFTSIM_REVIEWED_GRASS_BERMUDA_SOURCE_ROOT", ""
        ).strip()
        if not root_text:
            raise RuntimeError(
                "RAFTSIM_REVIEWED_GRASS_BERMUDA_SOURCE_ROOT is required"
            )
        root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_sources(root)
        textures = import_textures(root)
        material = create_material(textures)
        unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
        for texture in textures.values():
            unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
        report["meshes"] = import_meshes(root, material)
        report["textures"] = sorted(
            texture.get_path_name() for texture in textures.values()
        )
        report["material"] = material.get_path_name()
        report["status"] = "isolated_review_candidate_imported"
        write_report(report)
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
