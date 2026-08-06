"""Import the rights-reviewed ambientCG CC0 water-detail texture set.

Whitewater froth surfaces (Foam001/002/003: light lace, medium lace, dense
clotted froth) plus water-surface detail masks/normals
(SurfaceImperfections001/009). CC0 1.0 — committed to the repo per policy;
recorded in unreal/Content/RaftSim/Rendering/CC0WaterDetail/
cc0_water_detail_intake_manifest.json. Visual water presentation only: no
hydraulic, collision, buoyancy, or raft-force authority.

Run inside the editor:
  RAFTSIM_CC0_WATER_DETAIL_SOURCE_ROOT=<dir with Foam001/... subdirs> \
    UnrealEditor-Cmd <project> -ExecutePythonScript=.../this_script.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import traceback

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_reviewed_biome_asset import import_tasks, sha256


ASSET_ID = "ambientcg_cc0_water_detail_2k"
DESTINATION = "/Game/RaftSim/Rendering/CC0WaterDetail"
SOURCE_FILES = {
    "Foam001/Foam001_2K-JPG_Color.jpg": "3ef67800f7b5018e4bb1e1c63e37397c21d1ea7df21d1511fcf07c2c3d6f56d2",
    "Foam001/Foam001_2K-JPG_Opacity.jpg": "0dc4101735f2f279cff8be23161af96db72992cdc32f09f10e16f330cb3bdb7d",
    "Foam001/Foam001_2K-JPG_NormalDX.jpg": "c308fb4cc783ca25f534ee2221636a5a1308a51869478e820d934f102874939a",
    "Foam001/Foam001_2K-JPG_Roughness.jpg": "ad5932258cfe5251f0ec2d9e747bb8f8ba04900c1e6c5581934ab11523c07d95",
    "Foam002/Foam002_2K-JPG_Color.jpg": "4df4472006755ade7ff74f44c648e5e1eb214f6f8d330c387bd425c3a1a5ad64",
    "Foam002/Foam002_2K-JPG_Opacity.jpg": "591b4fe2d69bd7e7c6f6ace830e338b841b809808e06dac3c69ed0936c4780aa",
    "Foam002/Foam002_2K-JPG_NormalDX.jpg": "104fc90c4e490acc85afdee0113141ed1005cd50e81b21a3f009782d04ceb5fa",
    "Foam002/Foam002_2K-JPG_Roughness.jpg": "28325b8666d10b4edd0d7be71ec446caa1ace0fd06364f9a4604f6a58acc5a4f",
    "Foam003/Foam003_2K-JPG_Color.jpg": "7406a100c6f363665568591c82424410aea59408b78b30dfc0c07321142a7b3a",
    "Foam003/Foam003_2K-JPG_Opacity.jpg": "c6a942c1d35f5f1f823e4d906cdbb436985860c494ed027365a170faa7afa30f",
    "Foam003/Foam003_2K-JPG_NormalDX.jpg": "d6fb7c1c16a132ed4ac21ca54886398285db6c9d1e04a002b7ed661516cfdb51",
    "Foam003/Foam003_2K-JPG_Roughness.jpg": "f4588bb24772dacbdcb28c8df5d4a1445521f1b7c970d959c16caaf867e10929",
    "SurfaceImperfections001/SurfaceImperfections001_2K-JPG_NormalDX.jpg": "03333502e276db38faca0fbe07667c2628fa950b54c7d3c3f0e8746c12e0fc08",
    "SurfaceImperfections001/SurfaceImperfections001_2K-JPG_Opacity.jpg": "a95ae019bd983747e0694efe920224253c43edd6b4da17f8221f2604388dea83",
    "SurfaceImperfections009/SurfaceImperfections009_2K-JPG_NormalDX.jpg": "80f3d07724194e2459282c15f0271c61eb842369a143e102d5994103709c0ca0",
    "SurfaceImperfections009/SurfaceImperfections009_2K-JPG_Opacity.jpg": "c391a288966067476d958d3dbeed1861219f31060e99897dd7574d6bd6316c34",
}
TEXTURE_NAMES = {
    "Foam001/Foam001_2K-JPG_Color.jpg": "T_CC0_Foam001_Color",
    "Foam001/Foam001_2K-JPG_Opacity.jpg": "T_CC0_Foam001_Opacity",
    "Foam001/Foam001_2K-JPG_NormalDX.jpg": "T_CC0_Foam001_Normal",
    "Foam001/Foam001_2K-JPG_Roughness.jpg": "T_CC0_Foam001_Roughness",
    "Foam002/Foam002_2K-JPG_Color.jpg": "T_CC0_Foam002_Color",
    "Foam002/Foam002_2K-JPG_Opacity.jpg": "T_CC0_Foam002_Opacity",
    "Foam002/Foam002_2K-JPG_NormalDX.jpg": "T_CC0_Foam002_Normal",
    "Foam002/Foam002_2K-JPG_Roughness.jpg": "T_CC0_Foam002_Roughness",
    "Foam003/Foam003_2K-JPG_Color.jpg": "T_CC0_Foam003_Color",
    "Foam003/Foam003_2K-JPG_Opacity.jpg": "T_CC0_Foam003_Opacity",
    "Foam003/Foam003_2K-JPG_NormalDX.jpg": "T_CC0_Foam003_Normal",
    "Foam003/Foam003_2K-JPG_Roughness.jpg": "T_CC0_Foam003_Roughness",
    "SurfaceImperfections001/SurfaceImperfections001_2K-JPG_NormalDX.jpg": "T_CC0_WaterImperfections001_Normal",
    "SurfaceImperfections001/SurfaceImperfections001_2K-JPG_Opacity.jpg": "T_CC0_WaterImperfections001_Mask",
    "SurfaceImperfections009/SurfaceImperfections009_2K-JPG_NormalDX.jpg": "T_CC0_WaterImperfections009_Normal",
    "SurfaceImperfections009/SurfaceImperfections009_2K-JPG_Opacity.jpg": "T_CC0_WaterImperfections009_Mask",
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
                raise RuntimeError(f"Texture import for {relative_path} produced {imported_paths}")
            texture = unreal.load_asset(imported_paths[0])
            if not isinstance(texture, unreal.Texture2D):
                raise RuntimeError(f"Imported object is not Texture2D: {imported_paths[0]}")
            textures[relative_path] = texture

    for relative_path, texture in textures.items():
        texture.set_editor_property("srgb", "_Color" in relative_path)
        if "_NormalDX" in relative_path:
            # ambientCG NormalDX is already the UE (-Y) convention; no flip.
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP
            )
        elif "_Opacity" in relative_path or "_Roughness" in relative_path:
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
            )
        texture.modify()
        unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return textures


def write_report(report: dict[str, object]) -> None:
    report_text = os.environ.get("RAFTSIM_CC0_WATER_DETAIL_REPORT_PATH", "").strip()
    path = (
        Path(report_text).expanduser().resolve()
        if report_text
        else Path(unreal.Paths.project_saved_dir()) / "RaftSim" / "cc0_water_detail_import.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"RaftSim CC0 water-detail import report: {path}")


def main() -> None:
    report: dict[str, object] = {
        "schema": "raftsim.unreal.reviewed_environment_asset_import.v1",
        "asset_id": ASSET_ID,
        "destination": DESTINATION,
        "status": "failed",
        "production_promoted": False,
    }
    try:
        root_text = os.environ.get("RAFTSIM_CC0_WATER_DETAIL_SOURCE_ROOT", "").strip()
        if not root_text:
            raise RuntimeError("RAFTSIM_CC0_WATER_DETAIL_SOURCE_ROOT is required")
        source_root = Path(root_text).expanduser().resolve()
        report["verified_source_files"] = verify_source(source_root)
        textures = import_textures(source_root)
        report["textures"] = sorted(texture.get_path_name() for texture in textures.values())
        report["status"] = "cc0_water_detail_imported"
        write_report(report)
        unreal.log(f"RaftSim imported CC0 water-detail set {ASSET_ID}")
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        unreal.log_error(report["traceback"])
        raise


if __name__ == "__main__":
    main()
