"""Import the rights-reviewed ambientCG Rock037 Batoka surface analog."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import traceback

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_reviewed_biome_asset import import_tasks, sha256


ASSET_ID = "ambientcg_rock037_2k"
DESTINATION = "/Game/RaftSim/Environment/ExternalReview/AmbientCG/Rock037_2K"
SOURCE_FILES = {
    "Rock037_2K-JPG_AmbientOcclusion.jpg": (
        "2bbfaa7dcf74dd7e007373e1b5068132458ce1b2c1ba7bf99d86d58326290180"
    ),
    "Rock037_2K-JPG_Color.jpg": (
        "6416856bc34fcfe9100274beb679253d6440d1c5cfd37efc0f84450e7a5c66d2"
    ),
    "Rock037_2K-JPG_Displacement.jpg": (
        "aeb83afd914a593e271c11f46c69844245a5ddc1002b407902e7ee97aaf2305e"
    ),
    "Rock037_2K-JPG_NormalDX.jpg": (
        "7614883d4eba00cfef6df89166b8c54a109d1a577e57f187e7ed37309865ad87"
    ),
    "Rock037_2K-JPG_Roughness.jpg": (
        "c49ff1a57bd8d6db6c8a5dabf75dc39416c9468a6bdf1d6d938c50aef854fc9e"
    ),
}
TEXTURE_NAMES = {
    "Rock037_2K-JPG_AmbientOcclusion.jpg": "T_RaftSim_Batoka_Rock037_AO_2K",
    "Rock037_2K-JPG_Color.jpg": "T_RaftSim_Batoka_Rock037_Color_2K",
    "Rock037_2K-JPG_Displacement.jpg": "T_RaftSim_Batoka_Rock037_Displacement_2K",
    "Rock037_2K-JPG_NormalDX.jpg": "T_RaftSim_Batoka_Rock037_NormalDX_2K",
    "Rock037_2K-JPG_Roughness.jpg": "T_RaftSim_Batoka_Rock037_Roughness_2K",
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
            {
                "relative_path": relative_path,
                "sha256": actual_hash,
                "bytes": path.stat().st_size,
            }
        )
    return verified


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
                raise RuntimeError(
                    f"Texture import for {relative_path} produced {imported_paths}"
                )
            texture = unreal.load_asset(imported_paths[0])
            if not isinstance(texture, unreal.Texture2D):
                raise RuntimeError(
                    f"Imported object is not Texture2D: {imported_paths[0]}"
                )
            textures[relative_path] = texture

    for relative_path, texture in textures.items():
        texture.set_editor_property("srgb", "_Color." in relative_path)
        if "_NormalDX." in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP
            )
            texture.set_editor_property("flip_green_channel", False)
        elif any(
            token in relative_path
            for token in ("_AmbientOcclusion.", "_Displacement.", "_Roughness.")
        ):
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
            )
        texture.set_editor_property("never_stream", True)
        texture.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return textures


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get(
        "RAFTSIM_REVIEWED_BATOKA_BASALT_REPORT_PATH", ""
    ).strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir())
        / "RaftSim"
        / "reviewed_batoka_basalt_surface.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed Batoka basalt surface import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_environment_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "batoka_basalt_match": "not_established_dark_fractured_surface_analog_only",
    }
    try:
        root_text = os.environ.get(
            "RAFTSIM_REVIEWED_BATOKA_BASALT_SOURCE_ROOT", ""
        ).strip()
        if not root_text:
            raise RuntimeError(
                "RAFTSIM_REVIEWED_BATOKA_BASALT_SOURCE_ROOT is required"
            )
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        textures = import_textures(source_root)
        report["textures"] = sorted(
            texture.get_path_name() for texture in textures.values()
        )
        report["texture_contract"] = {
            "color_srgb": True,
            "normal_space": "DirectX",
            "normal_green_channel_flipped": False,
            "ao_displacement_roughness_linear_masks": True,
            "never_stream_for_isolated_review": True,
        }
        report["status"] = "isolated_review_surface_candidate_imported"
        write_report(report)
        unreal.log(f"RaftSim imported reviewed Batoka surface candidate {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
