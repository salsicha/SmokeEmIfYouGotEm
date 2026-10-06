"""Import the rights-reviewed Poly Haven rock scan through a clean preview path.

This is an isolated renderer-review path. It writes only below
``/Game/RaftSim/Experiments/RockMossSet01_BakedScale`` and never replaces the
existing external-review assets or production boulder.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import unreal


DESTINATION = "/Game/RaftSim/Experiments/RockMossSet01_BakedScale"
TEXTURE_NAMES = {
    "textures/rock_moss_set_01_diff_1k.jpg":
        "T_RockMossSet01_BaseColor_PhysicalPreview",
    "textures/rock_moss_set_01_nor_gl_1k.exr":
        "T_RockMossSet01_NormalGL_PhysicalPreview",
    "textures/rock_moss_set_01_rough_1k.jpg":
        "T_RockMossSet01_Roughness_PhysicalPreview",
}
SOURCE_FILES = {
    "rock_moss_set_01_1k.fbx":
        "8fa2a2666ecc4591f59e1d45db05d86857115b55492c8522917f3de5e650e6f9",
    "textures/rock_moss_set_01_diff_1k.jpg":
        "40cea65d8aa4ee73a93b04af19963834d061eee9779c3fc2c1cba76eef812ccc",
    "textures/rock_moss_set_01_nor_gl_1k.exr":
        "d86555deabb910ed82b2b770d852ba5aa931d373689ff7ae028574c7b310be99",
    "textures/rock_moss_set_01_rough_1k.jpg":
        "4d6ec46623abd8e2cdb855f59c7ce31873ad61b36b60e4de579e9e776a497c6b",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
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
                f"Hash mismatch for {relative_path}: "
                f"expected {expected_hash}, got {actual_hash}"
            )
        records.append(
            {
                "relative_path": relative_path,
                "sha256": actual_hash,
                "bytes": path.stat().st_size,
            }
        )
    return records


def import_preview(source_root: Path) -> list[unreal.StaticMesh]:
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
    # Request the FBX metre-to-centimetre conversion during import rather than
    # storing it in the 100x LOD build scale used by the original, non-rendering
    # review import. UE 5.8 preserves the source-sized bounds in this path; the
    # capture-only reviewed-rock component therefore performs explicit bounded
    # normalization from the imported mesh bounds at runtime.
    options.static_mesh_import_data.import_uniform_scale = 100.0

    task = unreal.AssetImportTask()
    task.filename = str(source_root / "rock_moss_set_01_1k.fbx")
    task.destination_path = DESTINATION
    task.destination_name = "SM_RockMossSet01_BakedScale"
    task.replace_existing = True
    task.automated = True
    task.save = False
    task.factory = unreal.FbxFactory()
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes = [unreal.load_asset(path) for path in task.imported_object_paths]
    meshes = [mesh for mesh in meshes if isinstance(mesh, unreal.StaticMesh)]
    if len(meshes) != 6:
        raise RuntimeError(
            f"Expected six baked-scale rock meshes, got {len(meshes)}: "
            f"{list(task.imported_object_paths)}"
        )
    return meshes


def import_preview_textures(source_root: Path) -> dict[str, unreal.Texture2D]:
    tasks = []
    task_keys = []
    for relative_path, asset_name in TEXTURE_NAMES.items():
        task = unreal.AssetImportTask()
        task.filename = str(source_root / relative_path)
        task.destination_path = DESTINATION
        task.destination_name = asset_name
        task.replace_existing = True
        task.automated = True
        task.save = False
        tasks.append(task)
        task_keys.append(relative_path)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    textures = {}
    for relative_path, task in zip(task_keys, tasks):
        imported_paths = list(task.imported_object_paths)
        if len(imported_paths) != 1:
            raise RuntimeError(
                f"Texture import for {relative_path} produced {imported_paths}"
            )
        texture = unreal.load_asset(imported_paths[0])
        if not isinstance(texture, unreal.Texture2D):
            raise RuntimeError(f"Imported object is not Texture2D: {imported_paths[0]}")
        texture.set_editor_property("srgb", "_diff_" in relative_path)
        if "_nor_gl_" in relative_path:
            texture.set_editor_property(
                "compression_settings",
                unreal.TextureCompressionSettings.TC_NORMALMAP,
            )
            texture.set_editor_property("flip_green_channel", True)
        elif "_rough_" in relative_path:
            texture.set_editor_property(
                "compression_settings",
                unreal.TextureCompressionSettings.TC_MASKS,
            )
        texture.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
        textures[relative_path] = texture
    return textures


def build_physical_preview_material(
    textures: dict[str, unreal.Texture2D]
) -> unreal.Material:
    name = "M_RockMossSet01_PhysicalPreview"
    asset_path = f"{DESTINATION}/{name}"
    existing = unreal.load_asset(asset_path)
    if isinstance(existing, unreal.Material):
        material = existing
        material.modify()
        for property_ in (
            unreal.MaterialProperty.MP_BASE_COLOR,
            unreal.MaterialProperty.MP_NORMAL,
            unreal.MaterialProperty.MP_ROUGHNESS,
        ):
            unreal.MaterialEditingLibrary.disconnect_material_property(
                material, property_
            )
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    else:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, DESTINATION, unreal.Material, unreal.MaterialFactoryNew()
        )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create {asset_path}")

    base_texture = textures["textures/rock_moss_set_01_diff_1k.jpg"]
    normal_texture = textures["textures/rock_moss_set_01_nor_gl_1k.exr"]
    roughness_texture = textures["textures/rock_moss_set_01_rough_1k.jpg"]

    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -640, -160
    )
    base.texture = base_texture
    base.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_COLOR
    albedo_scale = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -640, 20
    )
    # The source material's 1.15x base multiplier plus emissive fill clipped in
    # the locked +1.75 EV rapid-evidence exposure. A sub-unity diffuse scale and
    # zero emissive preserve texture detail under that same renderer contract.
    albedo_scale.r = 0.55
    scaled_base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -340, -120
    )
    normal = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -640, 220
    )
    normal.texture = normal_texture
    normal.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    roughness = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -640, 400
    )
    roughness.texture = roughness_texture
    roughness.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
    unreal.MaterialEditingLibrary.connect_material_expressions(
        base, "RGB", scaled_base, "A"
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(
        albedo_scale, "", scaled_base, "B"
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
    material.set_editor_property("two_sided", False)
    material.modify()
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    compile_errors = unreal.MaterialEditingLibrary.recompile_material(material)
    if compile_errors:
        raise RuntimeError(
            "Physical preview material failed to compile: "
            + "; ".join(str(error) for error in compile_errors)
        )
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def configure_preview(
    meshes: list[unreal.StaticMesh], material: unreal.Material
) -> list[dict[str, object]]:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if subsystem is None:
        raise RuntimeError("Static-mesh subsystem is unavailable")

    records = []
    for mesh in sorted(meshes, key=lambda item: item.get_name()):
        build_settings = subsystem.get_lod_build_settings(mesh, 0)
        build_settings.build_scale3d = unreal.Vector(1.0, 1.0, 1.0)
        subsystem.set_lod_build_settings(mesh, 0, build_settings)
        nanite_settings = subsystem.get_nanite_settings(mesh)
        nanite_settings.enabled = False
        subsystem.set_nanite_settings(mesh, nanite_settings)
        for material_index in range(len(mesh.static_materials)):
            mesh.set_material(material_index, material)
        mesh.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        bounds = mesh.get_bounding_box()
        dimensions = [
            bounds.max.x - bounds.min.x,
            bounds.max.y - bounds.min.y,
            bounds.max.z - bounds.min.z,
        ]
        records.append(
            {
                "asset_path": mesh.get_path_name(),
                "dimensions_cm": dimensions,
                "triangles_lod0": mesh.get_num_triangles(0),
                "lod0_build_scale": [
                    build_settings.build_scale3d.x,
                    build_settings.build_scale3d.y,
                    build_settings.build_scale3d.z,
                ],
                "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
                "material": material.get_path_name(),
            }
        )
    return records


def main() -> None:
    source_text = os.environ.get("RAFTSIM_REVIEWED_ROCK_SOURCE_ROOT", "").strip()
    if not source_text:
        raise RuntimeError("RAFTSIM_REVIEWED_ROCK_SOURCE_ROOT is required")
    source_root = Path(source_text).expanduser().resolve()
    verified_source = verify_source(source_root)
    meshes = import_preview(source_root)
    textures = import_preview_textures(source_root)
    material = build_physical_preview_material(textures)
    records = configure_preview(meshes, material)
    report = {
        "schema": "raftsim.unreal.reviewed_rock_baked_scale_preview.v1",
        "status": "isolated_preview_imported",
        "production_promoted": False,
        "destination": DESTINATION,
        "import_scale_request": 100.0,
        "lod0_build_scale": [1.0, 1.0, 1.0],
        "runtime_diagnostic_normalizes_from_mesh_bounds": True,
        "scale_conversion_baked_into_reported_bounds": False,
        "production_approval_required": [
            "geology",
            "rafting_guide",
            "art_direction",
            "performance",
        ],
        "source_root": str(source_root),
        "verified_source": verified_source,
        "material": material.get_path_name(),
        "material_albedo_scale": 0.55,
        "material_emissive": False,
        "textures": [texture.get_path_name() for texture in textures.values()],
        "meshes": records,
    }
    report_path = Path(
        os.environ.get(
            "RAFTSIM_REVIEWED_ROCK_REPORT_PATH",
            str(
                Path(unreal.Paths.project_saved_dir())
                / "Diagnostics"
                / "m9_reviewed_rock_baked_scale_preview.json"
            ),
        )
    ).expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim baked-scale rock preview report: {report_path}")


if __name__ == "__main__":
    main()
