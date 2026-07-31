"""Verify and import the rights-compatible guide/crew source set into Unreal.

Run through UnrealEditor-Cmd with ``-ExecutePythonScript``. The import is
idempotent by default; set ``RAFTSIM_CC0_REIMPORT=1`` to replace existing
assets after intentionally regenerating the source FBXs.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import traceback

import unreal


DESTINATION = "/Game/RaftSim/Characters/Production/CC0"
TEXTURE_DESTINATION = f"{DESTINATION}/Textures"
MATERIAL_DESTINATION = f"{DESTINATION}/Materials"
FBX_IMPORT_UNIFORM_SCALE = 1.0
MIN_PRODUCTION_BODY_HEIGHT_CM = 140.0
MAX_PRODUCTION_BODY_HEIGHT_CM = 220.0
SOURCE_SHA256_METADATA_TAG = "RaftSimSourceSHA256"
MIN_REFERENCE_HEAD_HEIGHT_CM = 120.0
MAX_REFERENCE_HEAD_HEIGHT_CM = 220.0
SOURCE_ROOT = (
    Path(unreal.Paths.project_dir())
    / "SourceArt"
    / "RaftSim"
    / "Characters"
    / "CC0Production"
)

ATLASES = {
    "brownlight_eye.png": ("T_RaftSim_CC0_BrownEye", "3f43a4de70e446186dac1760cfa01dfe36d530ed7564208455395b0ebcdf788a"),
    "young_darkskinned_female_diffuse.png": ("T_RaftSim_CC0_DarkFemale", "96aa4a96b247fc90d371587bb88e6ae3bfc77e83f5126f17e6bbb713aa200470"),
    "young_darkskinned_male_diffuse.png": ("T_RaftSim_CC0_DarkMale", "e3f0dbb634e4c68561338f0087f7a122444e84ec56df102212f1222aa12e4d50"),
    "young_lightskinned_female_diffuse.png": ("T_RaftSim_CC0_LightFemale", "b2a6ac8cd4f9febdb447368e29c76cd68410bb66e46d9dcfa2d5f75126eea8fc"),
    "young_lightskinned_male_diffuse.png": ("T_RaftSim_CC0_LightMale", "862a26e335e958b70534cb5f0d7c47ef30ab148a56c42b3e9da969cf76f12963"),
    "young_lightskinned_male_diffuse3.png": ("T_RaftSim_CC0_AsianMale", "f50016a5507fc687dc8df06599c8ea48de950cd185de33a71cafc1319ddab4d5"),
}

HAIR_TEXTURES = {
    "grump_diffuse": (
        "Hair/Hair02/elvs_grump_hair/elvs_grumphair.png",
        "T_RaftSim_Hair_Grump_D",
        "2fb446705b13298d5c55c38a6a4dcb089c440c1b00ccab91ddd05dee26aba83a",
        False,
    ),
    "braided_rows_diffuse": (
        "Hair/Hair02/elvs_braided_rows/mh_cornrowstex1.png",
        "T_RaftSim_Hair_BraidedRows_D",
        "f23aea7a2b04c1030319fc6fb5e39f0d9c588d23d6f604526551a4975af3fe8f",
        False,
    ),
    "braided_rows_normal": (
        "Hair/Hair02/elvs_braided_rows/normals.png",
        "T_RaftSim_Hair_BraidedRows_N",
        "c166083c581905a4297bb74ee2e6de621c699b488234b69209acbf962e506ac0",
        True,
    ),
    "short_side_diffuse": (
        "Hair/Hair02/elvs_short_side_do/darkmaggiehair.png",
        "T_RaftSim_Hair_ShortSide_D",
        "230bebbe9c1ce436ebd210cee4c41c470db9d1c58e4d22aabd7c22dc9dd11d72",
        False,
    ),
}

CHARACTERS = {
    "Guide": ("young_lightskinned_male_diffuse.png", "c5d4dffdaccc91f934920f35db53be3dc70dcc448abd6198503e5beff4ca6b40"),
    "Crew01": ("young_darkskinned_male_diffuse.png", "a285c7c16c7742767ef60abe158601c2722f0f710f62854edefca78fd5cade92"),
    "Crew02": ("young_lightskinned_male_diffuse3.png", "096d2a8d9f75bd2d247db6cde0059c4bbbe2f26ad188a092160bfe626bfc8f0b"),
    "Crew03": ("young_lightskinned_female_diffuse.png", "b176f8e3ca9e0426ef508f1676cfb68d7766562eba85d3c4b783a70d372355ed"),
    "Crew04": ("young_darkskinned_female_diffuse.png", "831fdd467a8d729c29556b3e4f27b512a25f722ca06f3157fcfcd34bea4a044a"),
}

CHARACTER_HAIR = {
    "Guide": ("grump_diffuse", None, unreal.LinearColor(0.22, 0.13, 0.08, 1.0)),
    "Crew01": (
        "braided_rows_diffuse",
        "braided_rows_normal",
        unreal.LinearColor(0.18, 0.12, 0.09, 1.0),
    ),
    "Crew02": ("grump_diffuse", None, unreal.LinearColor(0.11, 0.07, 0.05, 1.0)),
    "Crew03": ("short_side_diffuse", None, unreal.LinearColor(0.21, 0.09, 0.05, 1.0)),
    "Crew04": (
        "braided_rows_diffuse",
        "braided_rows_normal",
        unreal.LinearColor(0.10, 0.06, 0.04, 1.0),
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sources() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for filename, (_, expected_hash) in ATLASES.items():
        path = SOURCE_ROOT / "Atlases" / filename
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise RuntimeError(f"Atlas hash mismatch for {path}: {actual_hash}")
        records.append({"file": str(path), "sha256": actual_hash, "bytes": path.stat().st_size})
    for _, (relative_path, _, expected_hash, _) in HAIR_TEXTURES.items():
        path = SOURCE_ROOT / relative_path
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise RuntimeError(f"Hair texture hash mismatch for {path}: {actual_hash}")
        records.append({"file": str(path), "sha256": actual_hash, "bytes": path.stat().st_size})
    for variant, (_, expected_hash) in CHARACTERS.items():
        path = SOURCE_ROOT / "FBX" / f"RaftSim_CC0_{variant}.fbx"
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise RuntimeError(f"FBX hash mismatch for {path}: {actual_hash}")
        records.append({"file": str(path), "sha256": actual_hash, "bytes": path.stat().st_size})
    return records


def run_import_tasks(tasks: list[unreal.AssetImportTask]) -> None:
    if tasks:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)


def reference_skeleton_status(mesh: unreal.SkeletalMesh) -> tuple[bool, str]:
    skeleton = mesh.get_editor_property("skeleton")
    if not skeleton:
        return False, "missing skeleton"
    reference_pose = skeleton.get_reference_pose()
    bone_names = [str(name) for name in reference_pose.get_bone_names()]
    promoted_details = [
        name for name in bone_names if "_Eyes" in name or "_Brow_" in name
    ]
    head_height_cm = reference_pose.get_ref_bone_pose(
        "head", unreal.AnimPoseSpaces.WORLD
    ).translation.z
    if not MIN_REFERENCE_HEAD_HEIGHT_CM <= head_height_cm <= MAX_REFERENCE_HEAD_HEIGHT_CM:
        return False, f"reference head={head_height_cm:.3f}cm"
    if promoted_details:
        return False, f"promoted detail nodes={promoted_details}"
    return True, f"reference head={head_height_cm:.3f}cm"


def import_textures(replace_existing: bool) -> dict[str, unreal.Texture2D]:
    textures: dict[str, unreal.Texture2D] = {}
    imported_paths: set[str] = set()
    tasks: list[unreal.AssetImportTask] = []
    task_files: list[str] = []
    texture_sources = [
        (filename, SOURCE_ROOT / "Atlases" / filename, asset_name, False)
        for filename, (asset_name, _) in ATLASES.items()
    ]
    texture_sources.extend(
        (key, SOURCE_ROOT / relative_path, asset_name, is_normal)
        for key, (relative_path, asset_name, _, is_normal) in HAIR_TEXTURES.items()
    )
    normal_keys = {key for key, _, _, is_normal in texture_sources if is_normal}
    for key, source_path, asset_name, _ in texture_sources:
        existing = unreal.load_asset(f"{TEXTURE_DESTINATION}/{asset_name}")
        if isinstance(existing, unreal.Texture2D) and not replace_existing:
            textures[key] = existing
            continue
        task = unreal.AssetImportTask()
        task.filename = str(source_path)
        task.destination_path = TEXTURE_DESTINATION
        task.destination_name = asset_name
        task.automated = True
        task.replace_existing = replace_existing
        task.save = False
        tasks.append(task)
        task_files.append(key)
    run_import_tasks(tasks)
    for key, task in zip(task_files, tasks):
        imported = [unreal.load_asset(path) for path in task.imported_object_paths]
        texture = next((asset for asset in imported if isinstance(asset, unreal.Texture2D)), None)
        if not texture:
            raise RuntimeError(f"Texture import failed for {key}: {task.imported_object_paths}")
        textures[key] = texture
        imported_paths.add(texture.get_path_name())
    for key, texture in textures.items():
        changed = False
        expected_srgb = key not in normal_keys
        if texture.get_editor_property("srgb") != expected_srgb:
            texture.modify()
            texture.set_editor_property("srgb", expected_srgb)
            changed = True
        if key in normal_keys and texture.get_editor_property(
            "compression_settings"
        ) != unreal.TextureCompressionSettings.TC_NORMALMAP:
            if not changed:
                texture.modify()
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP
            )
            changed = True
        if changed or texture.get_path_name() in imported_paths:
            unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return textures


def import_characters(replace_existing: bool) -> dict[str, unreal.SkeletalMesh]:
    result: dict[str, unreal.SkeletalMesh] = {}
    for variant in CHARACTERS:
        asset_name = f"SK_RaftSim_CC0_{variant}"
        existing = unreal.load_asset(f"{DESTINATION}/{asset_name}")
        should_replace = replace_existing
        if isinstance(existing, unreal.SkeletalMesh) and not should_replace:
            existing_height = existing.get_imported_bounds().box_extent.z * 2.0
            skeleton_valid, skeleton_reason = reference_skeleton_status(existing)
            imported_source_hash = unreal.EditorAssetLibrary.get_metadata_tag(
                existing, SOURCE_SHA256_METADATA_TAG
            )
            expected_source_hash = CHARACTERS[variant][1]
            if (
                MIN_PRODUCTION_BODY_HEIGHT_CM <= existing_height <= MAX_PRODUCTION_BODY_HEIGHT_CM
                and imported_source_hash == expected_source_hash
                and skeleton_valid
            ):
                result[variant] = existing
                continue
            reasons: list[str] = []
            if not MIN_PRODUCTION_BODY_HEIGHT_CM <= existing_height <= MAX_PRODUCTION_BODY_HEIGHT_CM:
                reasons.append(f"height={existing_height:.3f}cm")
            if imported_source_hash != expected_source_hash:
                reasons.append("source hash changed or was not recorded")
            if not skeleton_valid:
                reasons.append(skeleton_reason)
            unreal.log_warning(f"Reimporting {asset_name}: {', '.join(reasons)}")
            should_replace = True

            # Unreal preserves an existing Skeleton when replacing a mesh,
            # including stale meter-scale rest bones. These exact assets are
            # deterministic outputs of this importer, so regenerate the pair
            # when its reference skeleton fails the centimeter/detail checks.
            if not skeleton_valid:
                mesh_path = f"{DESTINATION}/{asset_name}"
                referenced_skeleton = existing.get_editor_property("skeleton")
                skeleton_path = (
                    referenced_skeleton.get_path_name().split(".", 1)[0]
                    if referenced_skeleton
                    else f"{DESTINATION}/{asset_name}_Skeleton"
                )
                if not unreal.EditorAssetLibrary.delete_asset(mesh_path):
                    raise RuntimeError(f"Could not remove stale generated mesh {mesh_path}")
                if unreal.EditorAssetLibrary.does_asset_exist(skeleton_path):
                    if not unreal.EditorAssetLibrary.delete_asset(skeleton_path):
                        raise RuntimeError(
                            f"Could not remove stale generated skeleton {skeleton_path}"
                        )
                unreal.SystemLibrary.collect_garbage()
                should_replace = False

        options = unreal.FbxImportUI()
        options.automated_import_should_detect_type = False
        options.import_mesh = True
        options.import_as_skeletal = True
        options.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
        options.original_import_type = unreal.FBXImportType.FBXIT_SKELETAL_MESH
        options.import_materials = False
        options.import_textures = False
        options.import_animations = False
        options.create_physics_asset = False
        options.skeletal_mesh_import_data.set_editor_property(
            "import_uniform_scale", FBX_IMPORT_UNIFORM_SCALE
        )

        task = unreal.AssetImportTask()
        task.filename = str(SOURCE_ROOT / "FBX" / f"RaftSim_CC0_{variant}.fbx")
        task.destination_path = DESTINATION
        task.destination_name = asset_name
        task.automated = True
        task.replace_existing = should_replace
        task.save = False
        task.factory = unreal.FbxFactory()
        task.options = options
        run_import_tasks([task])
        imported = [unreal.load_asset(path) for path in task.imported_object_paths]
        for asset in imported:
            if asset:
                unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        mesh = next((asset for asset in imported if isinstance(asset, unreal.SkeletalMesh)), None)
        if not mesh:
            mesh = unreal.load_asset(f"{DESTINATION}/{asset_name}")
        if not isinstance(mesh, unreal.SkeletalMesh):
            raise RuntimeError(f"Skeletal import failed for {variant}: {task.imported_object_paths}")
        result[variant] = mesh
    return result


def texture_material(name: str, texture: unreal.Texture2D, roughness: float) -> unreal.Material:
    existing = unreal.load_asset(f"{MATERIAL_DESTINATION}/{name}")
    if isinstance(existing, unreal.Material):
        return existing
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_DESTINATION, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create material {name}")
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -360, -80
    )
    sample.texture = texture
    sample.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_COLOR
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -360, 140
    )
    rough.r = roughness
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    material.modify()
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    return material


def hair_material(
    name: str,
    diffuse: unreal.Texture2D,
    tint: unreal.LinearColor,
    normal: unreal.Texture2D | None = None,
    rebuild_existing: bool = False,
) -> unreal.Material:
    existing = unreal.load_asset(f"{MATERIAL_DESTINATION}/{name}")
    if isinstance(existing, unreal.Material) and not rebuild_existing:
        return existing
    if isinstance(existing, unreal.Material):
        material = existing
        material.modify()
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    else:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MATERIAL_DESTINATION, unreal.Material, unreal.MaterialFactoryNew()
        )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create material {name}")
    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -620, -120
    )
    base.texture = diffuse
    base.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_COLOR
    color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -620, 80
    )
    color.constant = tint
    tinted = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -320, -80
    )
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -320, 180
    )
    rough.r = 0.68
    unreal.MaterialEditingLibrary.connect_material_expressions(base, "RGB", tinted, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(color, "", tinted, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        tinted, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "A", unreal.MaterialProperty.MP_OPACITY_MASK
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    if normal is not None:
        normal_sample = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, -620, 300
        )
        normal_sample.texture = normal
        normal_sample.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
        unreal.MaterialEditingLibrary.connect_material_property(
            normal_sample, "RGB", unreal.MaterialProperty.MP_NORMAL
        )
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    material.set_editor_property("two_sided", True)
    material.set_editor_property("opacity_mask_clip_value", 0.20)
    material.modify()
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    return material


def color_material(name: str, color: unreal.LinearColor, roughness: float) -> unreal.Material:
    existing = unreal.load_asset(f"{MATERIAL_DESTINATION}/{name}")
    if isinstance(existing, unreal.Material):
        return existing
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_DESTINATION, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create material {name}")
    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -360, -80
    )
    base.constant = color
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -360, 140
    )
    rough.r = roughness
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    material.modify()
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    return material


def build_materials(
    textures: dict[str, unreal.Texture2D], rebuild_hair: bool = False
) -> dict[str, unreal.MaterialInterface]:
    materials: dict[str, unreal.MaterialInterface] = {
        "eyes": texture_material("M_RaftSim_CC0_Eyes", textures["brownlight_eye.png"], 0.31),
        "wetsuit": color_material(
            "M_RaftSim_CC0_Wetsuit", unreal.LinearColor(0.008, 0.014, 0.019, 1.0), 0.52
        ),
        "brows": color_material(
            "M_RaftSim_CC0_Brows", unreal.LinearColor(0.012, 0.0045, 0.002, 1.0), 0.79
        ),
    }
    for variant, (atlas_name, _) in CHARACTERS.items():
        materials[f"skin_{variant}"] = texture_material(
            f"M_RaftSim_CC0_{variant}_Skin", textures[atlas_name], 0.54
        )
        diffuse_key, normal_key, tint = CHARACTER_HAIR[variant]
        materials[f"hair_{variant}"] = hair_material(
            f"M_RaftSim_CC0_{variant}_Hair",
            textures[diffuse_key],
            tint,
            textures[normal_key] if normal_key else None,
            rebuild_hair,
        )
    for material in materials.values():
        has_skeletal_usage = unreal.MaterialEditingLibrary.has_material_usage(
            material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH
        )
        if not has_skeletal_usage:
            unreal.MaterialEditingLibrary.set_base_material_usage(
                material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH, True
            )
            unreal.MaterialEditingLibrary.recompile_material(material)
            unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
        if not unreal.MaterialEditingLibrary.has_material_usage(
            material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH
        ):
            raise RuntimeError(f"SkeletalMesh usage was not applied to {material.get_path_name()}")
    return materials


def configure_mesh(
    variant: str,
    mesh: unreal.SkeletalMesh,
    materials: dict[str, unreal.MaterialInterface],
) -> dict[str, object]:
    imported_height_cm = mesh.get_imported_bounds().box_extent.z * 2.0
    if not MIN_PRODUCTION_BODY_HEIGHT_CM <= imported_height_cm <= MAX_PRODUCTION_BODY_HEIGHT_CM:
        raise RuntimeError(
            f"{variant} imported at {imported_height_cm:.3f} cm tall; expected "
            f"{MIN_PRODUCTION_BODY_HEIGHT_CM:.0f}-{MAX_PRODUCTION_BODY_HEIGHT_CM:.0f} cm"
        )
    slots = list(mesh.get_editor_property("materials"))
    slot_records: list[dict[str, str]] = []
    slots_changed = False
    for index, slot in enumerate(slots):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        normalized = slot_name.lower()
        if "skin" in normalized:
            selected = materials[f"skin_{variant}"]
        elif "wetsuit" in normalized:
            selected = materials["wetsuit"]
        elif "eye" in normalized:
            selected = materials["eyes"]
        elif "brow" in normalized:
            selected = materials["brows"]
        elif "hair" in normalized:
            selected = materials[f"hair_{variant}"]
        else:
            raise RuntimeError(f"Unrecognized {variant} skeletal material slot: {slot_name}")
        if slot.get_editor_property("material_interface") != selected:
            slot.set_editor_property("material_interface", selected)
            slots[index] = slot
            slots_changed = True
        slot_records.append({"slot": slot_name, "material": selected.get_path_name()})
    mesh_changed = False
    if slots_changed:
        mesh.modify()
        mesh.set_editor_property("materials", slots)
        mesh_changed = True
    expected_source_hash = CHARACTERS[variant][1]
    if (
        unreal.EditorAssetLibrary.get_metadata_tag(mesh, SOURCE_SHA256_METADATA_TAG)
        != expected_source_hash
    ):
        if not mesh_changed:
            mesh.modify()
        unreal.EditorAssetLibrary.set_metadata_tag(
            mesh, SOURCE_SHA256_METADATA_TAG, expected_source_hash
        )
        mesh_changed = True

    skeleton = mesh.get_editor_property("skeleton")
    if not skeleton:
        raise RuntimeError(f"{variant} has no imported skeleton")
    skeleton_valid, skeleton_reason = reference_skeleton_status(mesh)
    if not skeleton_valid:
        raise RuntimeError(f"{variant} has invalid reference skeleton: {skeleton_reason}")
    subsystem = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
    if not subsystem:
        raise RuntimeError("SkeletalMeshEditorSubsystem is unavailable")
    lod_count = subsystem.get_lod_count(mesh)
    if lod_count < 3:
        if not mesh_changed:
            mesh.modify()
        subsystem.regenerate_lod(mesh, 3, True, False)
        lod_count = subsystem.get_lod_count(mesh)
        mesh_changed = True
    if lod_count < 3:
        raise RuntimeError(f"{variant} generated only {lod_count} skeletal LODs")

    if mesh_changed:
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    return {
        "variant": variant,
        "asset": mesh.get_path_name(),
        "skeleton": skeleton.get_path_name(),
        "reference_skeleton": skeleton_reason,
        "imported_height_cm": imported_height_cm,
        "fbx_import_uniform_scale": FBX_IMPORT_UNIFORM_SCALE,
        "lod_count": lod_count,
        "material_slots": slot_records,
    }


def write_report(report: dict[str, object]) -> None:
    path = Path(unreal.Paths.project_saved_dir()) / "RaftSim" / "cc0_character_import_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim CC0 character import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.cc0_character_import.v1",
        "destination": DESTINATION,
        "status": "failed",
    }
    try:
        report["verified_sources"] = verify_sources()
        replace_existing = os.environ.get("RAFTSIM_CC0_REIMPORT", "0") == "1"
        textures = import_textures(replace_existing)
        materials = build_materials(textures, rebuild_hair=replace_existing)
        meshes = import_characters(replace_existing)
        report["characters"] = [
            configure_mesh(variant, meshes[variant], materials) for variant in CHARACTERS
        ]
        report["status"] = "imported"
        write_report(report)
        unreal.log("RaftSim CC0 production character import complete")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
