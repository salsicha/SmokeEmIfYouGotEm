"""Import the rights-reviewed Poly Haven Batoka macro-surface analog."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import traceback

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_reviewed_biome_asset import import_tasks, sha256


ASSET_ID = "polyhaven_aerial_rocks_02_4k"
DESTINATION = (
    "/Game/RaftSim/Environment/ExternalReview/PolyHaven/AerialRocks02_4K"
)
SOURCE_FILES = {
    "aerial_rocks_02_ao_4k.jpg": (
        "ad455647f8d6bab2527ad596b548f5fd76d641b0343945afc5a549dec5ccf571"
    ),
    "aerial_rocks_02_diff_4k.jpg": (
        "51bbf941f0f096d627811055bc826d04ea6506c0387c72a57267fcda10ae7e83"
    ),
    "aerial_rocks_02_disp_4k.jpg": (
        "fffebf5a8dbe0d9f58bef24324815994f358501f7fd922f92576dfe35c567ee5"
    ),
    "aerial_rocks_02_nor_dx_4k.jpg": (
        "a67cf6332fa989d215d788f0badab34c89ff6f81756ff1391d0bd4bf27522135"
    ),
    "aerial_rocks_02_rough_4k.jpg": (
        "c089e713c509a4d347c664932dbabd703bf5abb1468a5059f187f6df5c92d4ae"
    ),
}
TEXTURE_NAMES = {
    "aerial_rocks_02_ao_4k.jpg": "T_RaftSim_Batoka_AerialRocks02_AO_4K",
    "aerial_rocks_02_diff_4k.jpg": "T_RaftSim_Batoka_AerialRocks02_Diffuse_4K",
    "aerial_rocks_02_disp_4k.jpg": "T_RaftSim_Batoka_AerialRocks02_Displacement_4K",
    "aerial_rocks_02_nor_dx_4k.jpg": "T_RaftSim_Batoka_AerialRocks02_NormalDX_4K",
    "aerial_rocks_02_rough_4k.jpg": "T_RaftSim_Batoka_AerialRocks02_Roughness_4K",
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
        texture.set_editor_property("srgb", "_diff_" in relative_path)
        if "_nor_dx_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP
            )
            texture.set_editor_property("flip_green_channel", False)
        elif any(
            token in relative_path for token in ("_ao_", "_disp_", "_rough_")
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
        "RAFTSIM_REVIEWED_BATOKA_MACRO_REPORT_PATH", ""
    ).strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir())
        / "RaftSim"
        / "reviewed_batoka_macro_surface.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim reviewed Batoka macro-surface import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_environment_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
        "corridor_substitution_performed": False,
        "batoka_basalt_match": (
            "not_established_generic_large_scale_natural_rock_analog_only"
        ),
    }
    try:
        root_text = os.environ.get(
            "RAFTSIM_REVIEWED_BATOKA_MACRO_SOURCE_ROOT", ""
        ).strip()
        if not root_text:
            raise RuntimeError(
                "RAFTSIM_REVIEWED_BATOKA_MACRO_SOURCE_ROOT is required"
            )
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        textures = import_textures(source_root)
        report["textures"] = sorted(
            texture.get_path_name() for texture in textures.values()
        )
        report["texture_contract"] = {
            "diffuse_srgb": True,
            "normal_space": "DirectX",
            "normal_green_channel_flipped": False,
            "ao_displacement_roughness_linear_masks": True,
            "never_stream_for_isolated_review": True,
            "publisher_scale_m": 50,
        }
        report["status"] = "isolated_review_macro_surface_candidate_imported"
        write_report(report)
        unreal.log(f"RaftSim imported reviewed Batoka macro surface {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
