"""Import Poly Haven River Small Rocks as an isolated terrain-material review."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import traceback

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_reviewed_biome_asset import import_tasks, sha256


ASSET_ID = "polyhaven_river_small_rocks_2k"
DESTINATION = (
    "/Game/RaftSim/Environment/ExternalReview/PolyHaven/RiverSmallRocks_2K"
)
SOURCE_FILES = {
    "river_small_rocks_diff_2k.jpg": (
        "656a20860f5960cc0f442dd425bfe4607052ab1749efdde35d60c5df9639beac"
    ),
    "river_small_rocks_nor_gl_2k.jpg": (
        "4468fc6354767fd959b74e4cb7095d061e533268189c2336e03cb0be1bddc250"
    ),
    "river_small_rocks_arm_2k.jpg": (
        "073109b53a7b909c4eb705546c03b853c7bcaac92c8e6803ed0382f377e4184f"
    ),
    "river_small_rocks_disp_2k.png": (
        "32216ca0d31a15489cb166afff2756ff90c6cac77bb6af0c30bfdebbe2c676bc"
    ),
}
TEXTURES = {
    "river_small_rocks_diff_2k.jpg": "T_RiverSmallRocks_BaseColor_2K",
    "river_small_rocks_nor_gl_2k.jpg": "T_RiverSmallRocks_NormalGL_2K",
    "river_small_rocks_arm_2k.jpg": "T_RiverSmallRocks_ARM_2K",
    "river_small_rocks_disp_2k.png": "T_RiverSmallRocks_Displacement_2K",
}


def verify_source(root: Path) -> list[dict[str, object]]:
    verified: list[dict[str, object]] = []
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
        verified.append(
            {
                "relative_path": relative_path,
                "sha256": actual_hash,
                "bytes": path.stat().st_size,
            }
        )
    return verified


def import_textures(source_root: Path) -> list[dict[str, object]]:
    tasks: list[unreal.AssetImportTask] = []
    task_keys: list[str] = []
    for relative_path, asset_name in TEXTURES.items():
        existing = unreal.load_asset(f"{DESTINATION}/{asset_name}")
        if isinstance(existing, unreal.Texture2D):
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
            if len(task.imported_object_paths) != 1:
                raise RuntimeError(
                    f"Texture import for {relative_path} produced "
                    f"{list(task.imported_object_paths)}"
                )

    rows: list[dict[str, object]] = []
    for relative_path, asset_name in TEXTURES.items():
        texture = unreal.load_asset(f"{DESTINATION}/{asset_name}")
        if not isinstance(texture, unreal.Texture2D):
            raise RuntimeError(f"Imported texture is unavailable: {asset_name}")
        texture.set_editor_property("srgb", "_diff_" in relative_path)
        if "_nor_gl_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP
            )
            texture.set_editor_property("flip_green_channel", True)
        elif "_arm_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
            )
        elif "_disp_" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE
            )
        texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
        texture.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
        rows.append(
            {
                "asset_path": texture.get_path_name(),
                "width": texture.blueprint_get_size_x(),
                "height": texture.blueprint_get_size_y(),
                "srgb": texture.get_editor_property("srgb"),
                "compression_settings": str(
                    texture.get_editor_property("compression_settings")
                ),
                "flip_green_channel": texture.get_editor_property(
                    "flip_green_channel"
                ),
            }
        )
    return rows


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_RIVER_SMALL_ROCKS_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir())
        / "RaftSim"
        / "river_small_rocks_import.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim River Small Rocks import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_environment_texture_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        root_text = os.environ.get(
            "RAFTSIM_RIVER_SMALL_ROCKS_SOURCE_ROOT", ""
        ).strip()
        if not root_text:
            raise RuntimeError("RAFTSIM_RIVER_SMALL_ROCKS_SOURCE_ROOT is required")
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        report["textures"] = import_textures(source_root)
        report["status"] = "isolated_review_candidate_imported"
        unreal.EditorAssetLibrary.save_directory(DESTINATION, only_if_is_dirty=False)
    except Exception as exc:
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        raise
    write_report(report)


if __name__ == "__main__":
    main()
