"""Author and assemble the five reviewed RaftSim production characters.

Run this file through UnrealEditor-Cmd after installing **MetaHuman Creator
Core Data** for UE 5.8 and signing in to Epic's MetaHuman services. The script
is intentionally fail-closed: a partial roster never activates at runtime.

The generated MetaHuman source assets remain editable under Authoring; the
optimized, cookable Blueprints are written under Production/MetaHumans. Set
``RAFTSIM_METAHUMAN_REBUILD=1`` only when intentionally replacing both sets.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import traceback

import unreal


SCHEMA = "raftsim.metahuman.production_roster.v1"
AUTHORING_ROOT = "/Game/RaftSim/Characters/Authoring/MetaHumans"
BUILD_ROOT = "/Game/RaftSim/Characters/Production/MetaHumans"
COMMON_ROOT = f"{BUILD_ROOT}/Common"
REPORT_PATH = (
    Path(unreal.Paths.project_saved_dir())
    / "RaftSimValidation"
    / "m9"
    / "metahuman-production-roster.json"
)
OPTIONAL_ROOT = "/MetaHumanCharacter/Optional"
DEFAULT_OUTFIT = (
    "/MetaHumanCharacter/Optional/Clothing/"
    "WI_DefaultGarment.WI_DefaultGarment"
)
TEXTURE_SYNTHESIS_MODEL = (
    Path(unreal.Paths.engine_plugins_dir())
    / "MetaHuman"
    / "MetaHumanCharacter"
    / "Content"
    / "Optional"
    / "TextureSynthesis"
    / "TS-1.3-F_UE_res-1024_nchr-153"
)
PRODUCTION_QUALITY = unreal.MetaHumanQualityLevel.HIGH
PRODUCTION_QUALITY_NAME = "high"


CHARACTERS = (
    {
        "role": "guide",
        "name": "MHC_RaftSim_Guide",
        "height_cm": 184.0,
        "upper_arm_cm": 37.0,
        "face_scale": (1.025, 0.985, 1.010),
        "face_coefficient_offset": 0.35,
        "skin_uv": (0.34, 0.44),
        "body_texture": 1,
        "face_texture": 1,
        "roughness": 0.64,
        "freckles": (0.18, 0.38),
        "hair_preference": ("brushcut", "clean", "sweptup", "buzzcut"),
        "brow_preference": ("natural", "fine", "slightarch"),
        "lash_preference": ("s_fine", "s_thin", "s_sparse"),
        "hair_melanin": 0.62,
        "outfit_color": (0.035, 0.055, 0.075, 1.0),
    },
    {
        "role": "crew_01",
        "name": "MHC_RaftSim_Crew_01",
        "height_cm": 190.0,
        "upper_arm_cm": 39.0,
        "face_scale": (0.985, 1.025, 1.018),
        "face_coefficient_offset": -1.05,
        "skin_uv": (0.72, 0.30),
        "body_texture": 2,
        "face_texture": 2,
        "roughness": 0.67,
        "freckles": (0.05, 0.20),
        "hair_preference": ("cornrows", "360waves", "coil", "buzzcut"),
        "brow_preference": ("dense", "full", "flatthick"),
        "lash_preference": ("s_thin", "s_sparse", "s_fine"),
        "hair_melanin": 0.92,
        "outfit_color": (0.025, 0.045, 0.065, 1.0),
    },
    {
        "role": "crew_02",
        "name": "MHC_RaftSim_Crew_02",
        "height_cm": 176.0,
        "upper_arm_cm": 34.5,
        "face_scale": (1.012, 1.010, 0.976),
        "face_coefficient_offset": 1.15,
        "skin_uv": (0.23, 0.63),
        "body_texture": 3,
        "face_texture": 3,
        "roughness": 0.61,
        "freckles": (0.10, 0.30),
        # BuzzCut can collapse to an empty optimized Hair component. Casual is
        # still short enough for rafting PPE clearance and produces packaged
        # groom/cards representations in UE 5.8.
        "hair_preference": ("casual", "coilbuzzcut", "clean", "buzzcut"),
        "brow_preference": ("wide", "thick", "swept"),
        "lash_preference": ("s_sparse", "s_fine", "s_thin"),
        "hair_melanin": 0.78,
        "outfit_color": (0.045, 0.060, 0.070, 1.0),
    },
    {
        "role": "crew_03",
        "name": "MHC_RaftSim_Crew_03",
        "height_cm": 169.0,
        "upper_arm_cm": 32.5,
        "face_scale": (1.035, 0.970, 0.990),
        "face_coefficient_offset": -0.40,
        "skin_uv": (0.42, 0.73),
        "body_texture": 0,
        "face_texture": 0,
        "roughness": 0.58,
        "freckles": (0.28, 0.50),
        "hair_preference": ("pixie", "boblayers", "bobmessy", "bobstraight"),
        "brow_preference": ("slightarch", "fine", "natural"),
        "lash_preference": ("l_slightcurl", "l_curl", "s_fine"),
        "hair_melanin": 0.54,
        "outfit_color": (0.030, 0.050, 0.080, 1.0),
    },
    {
        "role": "crew_04",
        "name": "MHC_RaftSim_Crew_04",
        "height_cm": 181.0,
        "upper_arm_cm": 36.0,
        "face_scale": (0.972, 1.018, 1.028),
        "face_coefficient_offset": 0.75,
        "skin_uv": (0.80, 0.58),
        "body_texture": 2,
        "face_texture": 2,
        "roughness": 0.69,
        "freckles": (0.03, 0.15),
        "hair_preference": ("afrofade", "coilbuzzcut", "360waves", "cornrows"),
        "brow_preference": ("full", "dense", "thick"),
        "lash_preference": ("l_curl", "l_thickcurl", "l_slightcurl"),
        "hair_melanin": 0.96,
        "outfit_color": (0.025, 0.040, 0.060, 1.0),
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_report(report: dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )


def class_path(config: dict[str, object]) -> str:
    name = str(config["name"])
    return f"{BUILD_ROOT}/{name}/BP_{name}.BP_{name}_C"


def object_path_to_package(path: str) -> str:
    return path.rsplit(".", 1)[0]


def game_directory_record(virtual_directory: str) -> dict[str, object]:
    prefix = "/Game/"
    if not virtual_directory.startswith(prefix):
        raise ValueError(f"Expected a /Game directory: {virtual_directory}")
    disk_root = Path(unreal.Paths.project_content_dir()) / virtual_directory.removeprefix(
        prefix
    )
    files = sorted(path for path in disk_root.rglob("*") if path.is_file())
    tree_digest = hashlib.sha256()
    byte_count = 0
    for path in files:
        relative = path.relative_to(disk_root).as_posix()
        size = path.stat().st_size
        file_digest = sha256(path)
        byte_count += size
        tree_digest.update(relative.encode("utf-8"))
        tree_digest.update(b"\0")
        tree_digest.update(str(size).encode("ascii"))
        tree_digest.update(b"\0")
        tree_digest.update(file_digest.encode("ascii"))
        tree_digest.update(b"\n")
    return {
        "virtual_directory": virtual_directory,
        "local_directory": str(disk_root),
        "file_count": len(files),
        "byte_count": byte_count,
        "tree_sha256": tree_digest.hexdigest(),
    }


def list_optional_assets() -> list[str]:
    return sorted(
        unreal.EditorAssetLibrary.list_assets(
            OPTIONAL_ROOT, recursive=True, include_folder=False
        )
    )


def optional_candidates(inventory: list[str], fragment: str) -> list[str]:
    lowered = fragment.lower()
    return [path for path in inventory if lowered in path.lower() and "/WI_" in path]


def choose_asset(
    candidates: list[str], preferences: tuple[str, ...], used: set[str]
) -> str:
    if not candidates:
        return ""
    ranked: list[tuple[int, int, str]] = []
    for path in candidates:
        lower = path.lower()
        token_rank = next(
            (index for index, token in enumerate(preferences) if token in lower),
            len(preferences),
        )
        ranked.append((token_rank, 1 if path in used else 0, path))
    chosen = min(ranked)[2]
    used.add(chosen)
    return chosen


def inspect_core_data(inventory: list[str]) -> dict[str, object]:
    outfit = unreal.load_asset(DEFAULT_OUTFIT)
    hair = optional_candidates(inventory, "/Grooms/Bindings/Hair/")
    eyebrows = optional_candidates(inventory, "/Grooms/Bindings/Eyebrow")
    eyelashes = optional_candidates(inventory, "/Grooms/Bindings/Eyelash")
    core = {
        "optional_asset_count": len(inventory),
        "texture_synthesis_model": str(TEXTURE_SYNTHESIS_MODEL),
        "texture_synthesis_model_present": TEXTURE_SYNTHESIS_MODEL.exists(),
        "default_outfit_present": outfit is not None,
        "hair_item_count": len(hair),
        "eyebrow_item_count": len(eyebrows),
        "eyelash_item_count": len(eyelashes),
    }
    missing = [
        label
        for label, available in (
            ("texture synthesis model", TEXTURE_SYNTHESIS_MODEL.exists()),
            ("default garment", outfit is not None),
            ("hair grooms", bool(hair)),
            ("eyebrow grooms", bool(eyebrows)),
            ("eyelash grooms", bool(eyelashes)),
        )
        if not available
    ]
    core["missing_components"] = missing
    return core


def add_wardrobe_item(collection, slot_name: str, asset_path: str):
    item = unreal.load_asset(asset_path)
    if item is None:
        raise RuntimeError(f"Unable to load {slot_name} wardrobe item: {asset_path}")
    item_key = collection.try_add_item_from_wardrobe_item(
        slot_name, item
    )
    if item_key is None:
        raise RuntimeError(
            f"MetaHuman collection rejected {slot_name} item: {asset_path}"
        )
    selection = unreal.MetaHumanPipelineSlotSelection(
        slot_name=slot_name, selected_item=item_key
    )
    if not collection.default_instance.try_add_slot_selection(
        selection
    ):
        raise RuntimeError(
            f"MetaHuman palette rejected {slot_name} selection: {asset_path}"
        )
    return item_key


def set_float_parameter(collection, item_key, parameter_name: str, value: float) -> bool:
    item_path = unreal.MetaHumanPaletteItemPath(item_key=item_key)
    parameters = (
        collection.default_instance.get_instance_parameters(
            item_path=item_path
        )
    )
    parameter = next((item for item in parameters if item.name == parameter_name), None)
    if parameter is None:
        return False
    parameter.set_float(value=value)
    return True


def set_color_parameter(
    collection, item_key, parameter_name: str, rgba: tuple[float, float, float, float]
) -> bool:
    item_path = unreal.MetaHumanPaletteItemPath(item_key=item_key)
    parameters = (
        collection.default_instance.get_instance_parameters(
            item_path=item_path
        )
    )
    parameter = next((item for item in parameters if item.name == parameter_name), None)
    if parameter is None:
        return False
    parameter.set_color(value=unreal.LinearColor(*rgba))
    return True


def apply_body(subsystem, character, config: dict[str, object]) -> list[str]:
    constraints = subsystem.get_body_constraints(character)
    by_name = {
        str(constraint.name).lower().replace(" ", "_"): constraint
        for constraint in constraints
    }
    applied: list[str] = []
    for name, measurement in (
        ("height", float(config["height_cm"])),
        ("upper_arm_length", float(config["upper_arm_cm"])),
    ):
        constraint = by_name.get(name)
        if constraint is None:
            raise RuntimeError(f"UE 5.8 MetaHuman body constraint missing: {name}")
        constraint.is_active = True
        constraint.target_measurement = measurement
        applied.append(f"{name}={measurement:.2f}")
    subsystem.set_body_constraints(character, list(by_name.values()))
    subsystem.commit_body_state(character)
    return applied


def apply_face(subsystem, character, config: dict[str, object]) -> dict[str, object]:
    coefficients = subsystem.get_face_model_coefficients(character=character)
    if len(coefficients) < 11:
        raise RuntimeError("MetaHuman subsystem returned no editable face coefficients")
    first_patch_count = int(coefficients[9])
    first_patch_end = 10 + first_patch_count
    if first_patch_count <= 0 or first_patch_end > len(coefficients):
        raise RuntimeError("MetaHuman face-coefficient header is invalid")
    coefficient_offset = float(config["face_coefficient_offset"])
    coefficients[10:first_patch_end] = [
        value + coefficient_offset for value in coefficients[10:first_patch_end]
    ]
    subsystem.set_face_model_coefficients(
        character=character, coefficients=coefficients
    )
    subsystem.commit_face_state(character=character)

    landmarks = subsystem.get_face_landmarks(character=character)
    if not landmarks:
        raise RuntimeError("MetaHuman subsystem returned no editable face landmarks")
    center = unreal.Vector(
        sum(point.x for point in landmarks) / len(landmarks),
        sum(point.y for point in landmarks) / len(landmarks),
        sum(point.z for point in landmarks) / len(landmarks),
    )
    scale_x, scale_y, scale_z = config["face_scale"]
    deltas = [
        unreal.Vector(
            (point.x - center.x) * (float(scale_x) - 1.0),
            (point.y - center.y) * (float(scale_y) - 1.0),
            (point.z - center.z) * (float(scale_z) - 1.0),
        )
        for point in landmarks
    ]
    subsystem.translate_face_landmarks(
        character=character,
        landmark_indices=list(range(len(deltas))),
        deltas=deltas,
    )
    subsystem.commit_face_state(character=character)
    return {
        "landmark_count": len(deltas),
        "first_patch_coefficient_count": first_patch_count,
        "coefficient_offset": coefficient_offset,
        "scale": [float(scale_x), float(scale_y), float(scale_z)],
    }


def apply_skin(subsystem, character, config: dict[str, object]) -> None:
    skin = unreal.MetaHumanCharacterSkinProperties()
    skin.u = float(config["skin_uv"][0])
    skin.v = float(config["skin_uv"][1])
    skin.show_top_underwear = True
    skin.body_texture_index = int(config["body_texture"])
    skin.face_texture_index = int(config["face_texture"])
    skin.roughness = float(config["roughness"])

    freckles = unreal.MetaHumanCharacterFrecklesProperties()
    freckles.density = float(config["freckles"][0])
    freckles.strength = float(config["freckles"][1])
    freckles.saturation = 0.72
    freckles.tone_shift = 0.02
    freckles.mask = unreal.MetaHumanCharacterFrecklesMask.TYPE2

    accent = unreal.MetaHumanCharacterAccentRegionProperties()
    accent.lightness = 0.02
    accent.redness = 0.08
    accent.saturation = 0.10
    accents = unreal.MetaHumanCharacterAccentRegions()
    for region in (
        "cheeks",
        "chin",
        "ears",
        "forehead",
        "lips",
        "nose",
        "scalp",
        "under_eye",
    ):
        setattr(accents, region, accent)

    settings = unreal.MetaHumanCharacterSkinSettings()
    settings.skin = skin
    settings.freckles = freckles
    settings.accents = accents
    settings.enable_texture_overrides = False
    character.preview_material_type = unreal.MetaHumanCharacterSkinPreviewMaterial.EDITABLE
    subsystem.commit_skin_settings(character, settings)


def create_or_load_character(config: dict[str, object], rebuild: bool):
    name = str(config["name"])
    asset_path = f"{AUTHORING_ROOT}/{name}.{name}"
    existing = unreal.load_asset(asset_path)
    recovered_partial = False
    if existing is not None:
        if not rebuild:
            workflow = unreal.EditorAssetLibrary.get_metadata_tag(
                existing, "RaftSimAuthoringWorkflow"
            )
            if workflow != SCHEMA:
                raise RuntimeError(
                    f"Refusing to replace non-RaftSim authoring asset {asset_path}; "
                    "set RAFTSIM_METAHUMAN_REBUILD=1 only after review"
                )
            partial_build = f"{BUILD_ROOT}/{name}"
            if unreal.EditorAssetLibrary.does_directory_exist(partial_build):
                unreal.EditorAssetLibrary.delete_directory(partial_build)
            recovered_partial = True
        if not unreal.EditorAssetLibrary.delete_asset(asset_path):
            raise RuntimeError(f"Unable to replace authoring asset: {asset_path}")
    character = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=name,
        package_path=AUTHORING_ROOT,
        asset_class=unreal.MetaHumanCharacter,
        factory=unreal.new_object(type=unreal.MetaHumanCharacterFactoryNew),
    )
    if character is None:
        raise RuntimeError(f"MetaHuman factory returned no asset for {name}")
    # Mark ownership before any service or pipeline operation so an interrupted
    # run can safely replace only its own deterministic partial output.
    unreal.EditorAssetLibrary.set_metadata_tag(
        character, "RaftSimAuthoringWorkflow", SCHEMA
    )
    unreal.EditorAssetLibrary.set_metadata_tag(
        character, "RaftSimProductionRole", str(config["role"])
    )
    unreal.EditorAssetLibrary.save_loaded_asset(character, only_if_is_dirty=False)
    return character, True, recovered_partial


def build_one(
    subsystem,
    config: dict[str, object],
    inventory: list[str],
    used_hair: set[str],
    used_brows: set[str],
    used_lashes: set[str],
    rebuild: bool,
) -> dict[str, object]:
    name = str(config["name"])
    expected_class = class_path(config)
    hair_candidates = optional_candidates(inventory, "/Grooms/Bindings/Hair/")
    brow_candidates = optional_candidates(inventory, "/Grooms/Bindings/Eyebrow")
    lash_candidates = optional_candidates(inventory, "/Grooms/Bindings/Eyelash")
    hair_path = choose_asset(
        hair_candidates, tuple(config["hair_preference"]), used_hair
    )
    brow_path = choose_asset(
        brow_candidates, tuple(config["brow_preference"]), used_brows
    )
    lash_path = choose_asset(
        lash_candidates, tuple(config["lash_preference"]), used_lashes
    )
    if unreal.load_class(None, expected_class) is not None and not rebuild:
        return {
            "name": name,
            "role": config["role"],
            "status": "existing_build_validated",
            "blueprint_class": expected_class,
            "hair": hair_path,
            "eyebrows": brow_path,
            "eyelashes": lash_path,
            "requested_body_constraints": {
                "height_cm": config["height_cm"],
                "upper_arm_cm": config["upper_arm_cm"],
            },
            "requested_face_sculpt": {
                "scale": config["face_scale"],
                "coefficient_offset": config["face_coefficient_offset"],
            },
            "local_build": game_directory_record(f"{BUILD_ROOT}/{name}"),
        }

    character, created, recovered_partial = create_or_load_character(config, rebuild)
    if not subsystem.try_add_object_to_edit(character):
        raise RuntimeError(f"MetaHuman editor subsystem rejected {name}")
    preview_collection = subsystem.get_preview_collection(character)
    if preview_collection is None:
        subsystem.remove_object_to_edit(character)
        raise RuntimeError(f"MetaHuman preview collection unavailable for {name}")

    record: dict[str, object] = {
        "name": name,
        "role": config["role"],
        "authoring_asset": f"{AUTHORING_ROOT}/{name}.{name}",
        "created": created,
        "recovered_schema_owned_partial": recovered_partial,
        "blueprint_class": expected_class,
        "hair": hair_path,
        "eyebrows": brow_path,
        "eyelashes": lash_path,
        "status": "editing",
    }
    try:
        record["body_constraints"] = apply_body(subsystem, character, config)
        record["face_sculpt"] = apply_face(subsystem, character, config)
        apply_skin(subsystem, character, config)

        outfit_key = add_wardrobe_item(preview_collection, "Outfits", DEFAULT_OUTFIT)
        hair_key = add_wardrobe_item(preview_collection, "Hair", hair_path)
        brow_key = add_wardrobe_item(preview_collection, "Eyebrows", brow_path)
        lash_key = add_wardrobe_item(preview_collection, "Eyelashes", lash_path)
        # UE 5.8 edits the live preview collection while a character is open.
        # Explicit propagation is required or the wardrobe selection can look
        # correct in the editor yet disappear from the saved/assembled asset.
        subsystem.on_edit_preview_collection(character)
        subsystem.assemble_for_preview(character=character)
        record["hair_melanin_parameter"] = set_float_parameter(
            preview_collection, hair_key, "Melanin", float(config["hair_melanin"])
        )
        record["brow_melanin_parameter"] = set_float_parameter(
            preview_collection, brow_key, "Melanin", float(config["hair_melanin"])
        )
        record["lash_melanin_parameter"] = set_float_parameter(
            preview_collection, lash_key, "Melanin", float(config["hair_melanin"])
        )
        outfit_parameters = {}
        for parameter_name in (
            "PrimaryColorShirt",
            "PrimaryColorPants",
            "PrimaryColor",
        ):
            outfit_parameters[parameter_name] = set_color_parameter(
                preview_collection,
                outfit_key,
                parameter_name,
                tuple(config["outfit_color"]),
            )
        record["outfit_color_parameters"] = outfit_parameters
        subsystem.on_edit_preview_collection(character)

        unreal.EditorAssetLibrary.set_metadata_tag(
            character, "RaftSimProductionRole", str(config["role"])
        )
        unreal.EditorAssetLibrary.set_metadata_tag(
            character, "RaftSimAuthoringWorkflow", SCHEMA
        )
        unreal.EditorAssetLibrary.save_loaded_asset(character, only_if_is_dirty=False)

        rig = unreal.MetaHumanCharacterAutoRiggingRequestParams()
        rig.blocking = True
        rig.report_progress = False
        rig.rig_type = unreal.MetaHumanRigType.JOINTS_AND_BLEND_SHAPES
        subsystem.request_auto_rigging(character=character, params=rig)
        record["auto_rig_completed"] = True

        textures = unreal.MetaHumanCharacterTextureRequestParams()
        textures.blocking = True
        textures.report_progress = False
        subsystem.request_texture_sources(character=character, params=textures)
        record["high_resolution_textures"] = bool(
            character.has_high_resolution_textures
        )
        if not record["high_resolution_textures"]:
            raise RuntimeError(f"High-resolution texture request failed for {name}")
        record["can_build"] = bool(
            subsystem.can_build_meta_human(character=character)
        )
        if not record["can_build"]:
            raise RuntimeError(f"MetaHuman remains ineligible for assembly: {name}")
        unreal.EditorAssetLibrary.save_loaded_asset(character, only_if_is_dirty=False)

        build = unreal.MetaHumanCharacterEditorBuildParameters()
        build.pipeline_type = unreal.MetaHumanDefaultPipelineType.OPTIMIZED
        build.pipeline_quality = PRODUCTION_QUALITY
        build.absolute_build_path = BUILD_ROOT
        build.common_folder_path = COMMON_ROOT
        build.enable_wardrobe_item_validation = False
        subsystem.build_meta_human(character=character, params=build)
        unreal.EditorAssetLibrary.save_directory(
            directory_path=f"{BUILD_ROOT}/{name}",
            only_if_is_dirty=False,
            recursive=True,
        )
        unreal.EditorAssetLibrary.save_directory(
            directory_path=COMMON_ROOT,
            only_if_is_dirty=False,
            recursive=True,
        )
        if unreal.load_class(None, expected_class) is None:
            raise RuntimeError(f"Assembly produced no expected Blueprint: {expected_class}")
        build_assets = unreal.EditorAssetLibrary.list_assets(
            f"{BUILD_ROOT}/{name}", recursive=True, include_folder=False
        )
        record["build_asset_count"] = len(build_assets)
        record["local_build"] = game_directory_record(f"{BUILD_ROOT}/{name}")
        record["status"] = "assembled"
        return record
    finally:
        if subsystem.is_object_added_for_editing(character):
            subsystem.remove_object_to_edit(character)


def main() -> None:
    rebuild = os.environ.get("RAFTSIM_METAHUMAN_REBUILD") == "1"
    rebuild_target = os.environ.get("RAFTSIM_METAHUMAN_REBUILD_TARGET", "").strip()
    if rebuild and rebuild_target:
        raise RuntimeError(
            "Set either RAFTSIM_METAHUMAN_REBUILD=1 or "
            "RAFTSIM_METAHUMAN_REBUILD_TARGET, not both"
        )
    if rebuild_target and not any(
        rebuild_target in (str(config["name"]), str(config["role"]))
        for config in CHARACTERS
    ):
        raise RuntimeError(f"Unknown MetaHuman rebuild target: {rebuild_target}")
    script_path = Path(__file__).resolve()
    report: dict[str, object] = {
        "schema": SCHEMA,
        "status": "starting",
        "rebuild": rebuild,
        "rebuild_target": rebuild_target or None,
        "authoring_root": AUTHORING_ROOT,
        "build_root": BUILD_ROOT,
        "pipeline_type": "optimized",
        "pipeline_quality": PRODUCTION_QUALITY_NAME,
        "script": str(script_path),
        "script_sha256": sha256(script_path),
        "license": {
            "content": "MetaHuman Content",
            "terms": [
                "https://www.unrealengine.com/eula/unreal",
                "https://www.unrealengine.com/eula/mhc",
                "https://www.unrealengine.com/eula/content",
            ],
            "runtime_cloud_dependency": False,
            "source_distribution": "local_only",
            "public_repository_asset_binaries": False,
            "release_distribution": "cooked_object_code_only",
        },
        "characters": [],
    }
    write_report(report)
    try:
        inventory = list_optional_assets()
        report["core_data"] = inspect_core_data(inventory)
        write_report(report)
        if report["core_data"]["missing_components"]:
            raise RuntimeError(
                "MetaHuman Creator Core Data is incomplete: "
                + ", ".join(report["core_data"]["missing_components"])
            )
        if rebuild:
            if unreal.EditorAssetLibrary.does_directory_exist(AUTHORING_ROOT):
                unreal.EditorAssetLibrary.delete_directory(AUTHORING_ROOT)
            if unreal.EditorAssetLibrary.does_directory_exist(BUILD_ROOT):
                unreal.EditorAssetLibrary.delete_directory(BUILD_ROOT)

        subsystem = unreal.get_editor_subsystem(
            unreal.MetaHumanCharacterEditorSubsystem
        )
        used_hair: set[str] = set()
        used_brows: set[str] = set()
        used_lashes: set[str] = set()
        for config in CHARACTERS:
            report["active_character"] = config["name"]
            write_report(report)
            character_record = build_one(
                subsystem,
                config,
                inventory,
                used_hair,
                used_brows,
                used_lashes,
                rebuild
                or rebuild_target
                in (str(config["name"]), str(config["role"])),
            )
            report["characters"].append(character_record)
            write_report(report)

            # UE 5.8 can retain stale Control Rig/Skeleton object identities
            # after an optimized build writes the shared Common folder. A
            # second character in the same process can then fail even though
            # the serialized Common assets are valid. End the clean editor
            # session after one new assembly; the next invocation validates
            # existing classes and continues with the first missing roster
            # entry. This is deterministic and prevents an in-memory plugin
            # defect from deleting or rebuilding already accepted work.
            if character_record["status"] == "assembled":
                missing_after_build = [
                    class_path(candidate)
                    for candidate in CHARACTERS
                    if unreal.load_class(None, class_path(candidate)) is None
                ]
                if missing_after_build:
                    report.pop("active_character", None)
                    report["assembled_character_count"] = (
                        len(CHARACTERS) - len(missing_after_build)
                    )
                    report["remaining_blueprint_classes"] = missing_after_build
                    report["status"] = (
                        "partial_roster_assembled_clean_editor_restart_required"
                    )
                    return

        missing_classes = [
            class_path(config)
            for config in CHARACTERS
            if unreal.load_class(None, class_path(config)) is None
        ]
        if missing_classes:
            raise RuntimeError(
                "Production roster is incomplete: " + ", ".join(missing_classes)
            )
        report.pop("active_character", None)
        report["assembled_character_count"] = len(CHARACTERS)
        report["status"] = "production_roster_assembled"
    except Exception as error:
        report["status"] = "error"
        report["error_type"] = type(error).__name__
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        unreal.log_error(f"RaftSim production character build failed: {error}")
        raise
    finally:
        write_report(report)


if __name__ == "__main__":
    main()
