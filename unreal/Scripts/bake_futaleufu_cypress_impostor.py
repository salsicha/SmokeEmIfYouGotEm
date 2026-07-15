"""Bake the local Cordillera cypress far-distance impostor review asset.

Run with UnrealEditor-Cmd using a persistent ``-ExecCmds=\"py ...\"`` launch and
a rendering RHI. ``-ExecutePythonScript`` closes the editor before the latent
Impostor Baker render graph finishes.
The source, preset, baked assets, and result report stay in ignored local-review
namespaces. The tracked structural report records the reproducible bake contract.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import time
import traceback

import unreal


SOURCE_ASSET = (
    "/Game/RaftSim/Environment/GeneratedLocalReview/"
    "PVEFutaleufuCordilleraCypress/Impostor/"
    "SM_FutaleufuPveCordilleraCypress_OpenGrownConicalAdult_ImpostorSource"
)
REVIEW_DIRECTORY = (
    "/Game/RaftSim/Environment/GeneratedLocalReview/"
    "PVEFutaleufuCordilleraCypress/Impostor"
)
DEFAULT_PRESET = "/ImpostorBaker/BP/DataAsset/ImpostorPresets_Default"
COLOR_MAP_ENUM_DONOR_PRESET = (
    "/ImpostorBaker/BP/DataAsset/DA_ImpostorPreset_TranslucentCloud"
)
BATCH_WIDGET = "/ImpostorBaker/BP/EUW_Generate_Impostor_using_Preset"
BATCH_WIDGET_CLASS = (
    "/ImpostorBaker/BP/EUW_Generate_Impostor_using_Preset."
    "EUW_Generate_Impostor_using_Preset_C"
)
TAB_ID = unreal.Name("RaftSimFutaleufuCypressImpostorBake")


def command_line_int(name: str, default: int) -> int:
    match = re.search(
        rf"(?:^|\s)-{re.escape(name)}=(\d+)(?=\s|$)",
        unreal.SystemLibrary.get_command_line(),
    )
    return int(match.group(1)) if match else default


FRAMES_XY = command_line_int("RaftSimImpostorFrames", 12)
RESOLUTION = command_line_int("RaftSimImpostorResolution", 2048)
SCENE_CAPTURE_RESOLUTION = command_line_int("RaftSimImpostorCaptureResolution", 512)
TIMEOUT_SECONDS = float(command_line_int("RaftSimImpostorTimeout", 900))
PROFILE_LABEL = f"{FRAMES_XY}x{FRAMES_XY}_{RESOLUTION}px"
PRESET_ASSET = f"{REVIEW_DIRECTORY}/DA_FutaleufuCypress_UpperHemisphere_{PROFILE_LABEL}"
OUTPUT_LEAF = f"ImpostorLODs_{PROFILE_LABEL}"
OUTPUT_DIRECTORY = f"{REVIEW_DIRECTORY}/{OUTPUT_LEAF}"
RESULT_PATH = (
    Path(unreal.Paths.project_saved_dir())
    / "RaftSimPveReview"
    / "FutaleufuCordilleraCypress"
    / f"open_grown_conical_impostor_bake_{PROFILE_LABEL}_result.json"
)
STABLE_SECONDS = 20.0


_state: dict[str, object] = {
    "started": time.monotonic(),
    "phase": "initializing",
    "last_assets": [],
    "last_change": time.monotonic(),
    "tick_handle": None,
    "widget": None,
    "quit_after": None,
}


def log(message: str) -> None:
    unreal.log(f"[RaftSimImpostorBake] {message}")


def write_result(status: str, error: str | None = None) -> None:
    assets = list_output_assets()
    classified_assets = []
    for asset_path in assets:
        asset = unreal.load_asset(asset_path)
        classified_assets.append(
            {
                "path": asset_path,
                "class": asset.get_class().get_name() if asset else "unresolved",
            }
        )
    result = {
        "schema": "raftsim.unreal.local_impostor_bake_result.v1",
        "status": status,
        "source_asset": SOURCE_ASSET,
        "preset_asset": PRESET_ASSET,
        "output_directory": OUTPUT_DIRECTORY,
        "bake_contract": {
            "plugin": "ImpostorBaker",
            "impostor_type": "upper_hemisphere_only",
            "frames_xy": FRAMES_XY,
            "resolution": RESOLUTION,
            "scene_capture_resolution": SCENE_CAPTURE_RESOLUTION,
            "capture_using_gbuffer": True,
            "parallax_mode": "single_sample_parallax",
        },
        "generated_assets": classified_assets,
        "elapsed_seconds": round(time.monotonic() - float(_state["started"]), 3),
        "error": error,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


def fail(message: str) -> None:
    unreal.log_error(f"[RaftSimImpostorBake] {message}")
    write_result("failed", message)
    finish()


def finish() -> None:
    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    if not subsystem.close_tab_by_id(TAB_ID):
        unreal.log_warning(
            f"[RaftSimImpostorBake] Could not close utility tab {TAB_ID} before exit"
        )
    _state["widget"] = None
    _state["phase"] = "closing"
    _state["quit_after"] = time.monotonic() + 2.0


def list_output_assets() -> list[str]:
    if not unreal.EditorAssetLibrary.does_directory_exist(OUTPUT_DIRECTORY):
        return []
    return sorted(
        str(path)
        for path in unreal.EditorAssetLibrary.list_assets(
            OUTPUT_DIRECTORY,
            recursive=True,
            include_folder=False,
        )
    )


def output_is_complete(assets: list[str]) -> bool:
    classes = []
    for asset_path in assets:
        asset = unreal.load_asset(asset_path)
        if asset:
            classes.append(asset.get_class().get_name())
    has_mesh = "StaticMesh" in classes
    has_material = any(name in {"Material", "MaterialInstanceConstant"} for name in classes)
    texture_count = sum(name == "Texture2D" for name in classes)
    return has_mesh and has_material and texture_count >= 2


def configure_preset() -> unreal.PrimaryDataAsset:
    preset = unreal.load_asset(PRESET_ASSET)
    if not preset:
        if not unreal.EditorAssetLibrary.duplicate_asset(DEFAULT_PRESET, PRESET_ASSET):
            raise RuntimeError(f"Could not duplicate Impostor Baker preset to {PRESET_ASSET}")
        preset = unreal.load_asset(PRESET_ASSET)
    if not isinstance(preset, unreal.PrimaryDataAsset):
        raise RuntimeError(f"Impostor preset did not resolve as PrimaryDataAsset: {PRESET_ASSET}")

    preset.set_editor_property("Frames XY", FRAMES_XY)
    current_layout = preset.get_editor_property("Impostor Type")
    preset.set_editor_property(
        "Impostor Type",
        getattr(type(current_layout), "UPPER_HEMISPHERE_ONLY"),
    )
    preset.set_editor_property("Resolution", RESOLUTION)
    preset.set_editor_property("Scene Capture Resolution", SCENE_CAPTURE_RESOLUTION)
    preset.set_editor_property("CaptureUsingGBuffer", True)
    preset.set_editor_property("Center XY On Mesh Pivot", False)
    preset.set_editor_property("Use Relative Path", True)
    preset.set_editor_property("New Asset Path", f"/{OUTPUT_LEAF}/")
    donor_preset = unreal.load_asset(COLOR_MAP_ENUM_DONOR_PRESET)
    if not donor_preset:
        raise RuntimeError(
            "Could not load Impostor Baker color-map enum donor preset: "
            f"{COLOR_MAP_ENUM_DONOR_PRESET}"
        )
    donor_color_maps = list(
        donor_preset.get_editor_property("Color Maps To Render")
    )
    if not donor_color_maps:
        raise RuntimeError("Impostor Baker enum donor preset exposes no color maps")
    color_map_type = type(donor_color_maps[0])
    preset.set_editor_property(
        "Color Maps To Render",
        [
            getattr(color_map_type, "BASE_COLOR"),
            getattr(color_map_type, "NORMAL"),
        ],
    )
    current_parallax = preset.get_editor_property("Parallax Mode")
    preset.set_editor_property(
        "Parallax Mode",
        getattr(type(current_parallax), "SINGLE_SAMPLE_PARALLAX"),
    )
    preset.modify()
    if not unreal.EditorAssetLibrary.save_asset(PRESET_ASSET, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save configured Impostor Baker preset: {PRESET_ASSET}")

    checks = {
        "Frames XY": FRAMES_XY,
        "Resolution": RESOLUTION,
        "Scene Capture Resolution": SCENE_CAPTURE_RESOLUTION,
        "CaptureUsingGBuffer": True,
        "Use Relative Path": True,
        "New Asset Path": f"/{OUTPUT_LEAF}/",
    }
    for property_name, expected in checks.items():
        actual = preset.get_editor_property(property_name)
        if actual != expected:
            raise RuntimeError(
                f"Preset property {property_name!r} is {actual!r}, expected {expected!r}"
            )
    configured_color_maps = preset.get_editor_property("Color Maps To Render")
    configured_color_map_names = [value.name for value in configured_color_maps]
    if configured_color_map_names != ["BASE_COLOR", "NORMAL"]:
        raise RuntimeError(
            f"Preset color maps are {configured_color_map_names}, expected BaseColor and Normal"
        )
    return preset


def start_bake() -> None:
    source_mesh = unreal.load_asset(SOURCE_ASSET)
    if not isinstance(source_mesh, unreal.StaticMesh):
        raise RuntimeError(f"Impostor source is not a StaticMesh: {SOURCE_ASSET}")
    preset = configure_preset()
    widget_blueprint = unreal.load_asset(BATCH_WIDGET)
    if not widget_blueprint:
        raise RuntimeError(f"Could not load Impostor Baker batch widget: {BATCH_WIDGET}")
    widget_class = unreal.load_object(None, BATCH_WIDGET_CLASS)
    if not widget_class:
        raise RuntimeError(f"Could not load Impostor Baker widget class: {BATCH_WIDGET_CLASS}")
    widget_default = unreal.get_default_object(widget_class)
    widget_default.set_editor_property("StaticMeshes", [source_mesh])
    widget_default.set_editor_property("SettingsPreset", preset)
    widget_default.set_editor_property("DefaultSettingsAssetPath", PRESET_ASSET)

    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    widget = subsystem.spawn_and_register_tab_with_id(widget_blueprint, TAB_ID)
    if not widget:
        raise RuntimeError("Impostor Baker batch widget did not spawn")
    _state["widget"] = widget
    if list(widget.get_editor_property("StaticMeshes")) != [source_mesh]:
        raise RuntimeError("Spawned Impostor Baker widget did not inherit the source mesh")
    if widget.get_editor_property("SettingsPreset") != preset:
        raise RuntimeError("Spawned Impostor Baker widget did not inherit the configured preset")
    _state["phase"] = "baking"
    _state["last_assets"] = list_output_assets()
    _state["last_change"] = time.monotonic()
    log(
        f"Starting {FRAMES_XY}x{FRAMES_XY} upper-hemisphere {RESOLUTION}px "
        f"GBuffer bake ({SCENE_CAPTURE_RESOLUTION}px capture) for "
        f"{source_mesh.get_name()}"
    )
    render_button = widget.get_editor_property("Button_Render")
    if not isinstance(render_button, unreal.Button):
        raise RuntimeError("Impostor Baker widget did not expose Button_Render")
    render_button.on_clicked.broadcast()
    log("Broadcast Button_Render.OnClicked to invoke the batch render/save graph")


def tick(_delta_seconds: float) -> None:
    now = time.monotonic()
    try:
        phase = str(_state["phase"])
        if phase == "closing":
            quit_after = _state.get("quit_after")
            if quit_after is not None and now >= float(quit_after):
                handle = _state.get("tick_handle")
                if handle is not None:
                    unreal.unregister_slate_post_tick_callback(handle)
                    _state["tick_handle"] = None
                unreal.SystemLibrary.quit_editor()
            return
        if phase == "initializing":
            _state["phase"] = "preparing"
            start_bake()
            return
        if phase != "baking":
            return

        assets = list_output_assets()
        if assets != _state["last_assets"]:
            _state["last_assets"] = assets
            _state["last_change"] = now
            log(f"Observed {len(assets)} generated output assets")
        stable_for = now - float(_state["last_change"])
        if output_is_complete(assets) and stable_for >= STABLE_SECONDS:
            write_result("baked_pending_visual_review")
            log(f"Bake completed with {len(assets)} assets; result -> {RESULT_PATH}")
            _state["phase"] = "finished"
            finish()
            return
        if now - float(_state["started"]) > TIMEOUT_SECONDS:
            fail(
                f"Timed out after {TIMEOUT_SECONDS:.0f}s with {len(assets)} output assets"
            )
    except Exception:
        fail(traceback.format_exc())


_state["tick_handle"] = unreal.register_slate_post_tick_callback(tick)
log("Automation registered; waiting for the first editor tick")
