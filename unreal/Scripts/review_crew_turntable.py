"""Capture the actual gameplay crew at multiple angles without hiding failed fits.

Run with UnrealEditor-Cmd -ExecutePythonScript and a rendering RHI.
RAFTSIM_CREW_REVIEW_LABEL selects a separate baseline/candidate output folder.
"""
import importlib.util
import json
import math
import os
from pathlib import Path

import unreal

spec = importlib.util.spec_from_file_location(
    "crew_capture_helpers", Path(__file__).with_name("capture_cc0_production_roster.py")
)
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
output = Path(unreal.Paths.project_dir()).resolve().parent / "docs/crew-review-2026-09-04"
output /= os.environ.get("RAFTSIM_CREW_REVIEW_LABEL", "baseline")
output.mkdir(parents=True, exist_ok=True)
helpers.OUTPUT_ROOT = output

world = unreal.EditorLevelLibrary.get_editor_world()
target = unreal.Vector(0, 0, 85)
for location, intensity, color in (
    (unreal.Vector(230, 180, 240), 150, unreal.Color(255, 239, 222, 255)),
    (unreal.Vector(150, -220, 165), 100, unreal.Color(215, 232, 255, 255)),
    (unreal.Vector(-180, 50, 200), 110, unreal.Color(225, 236, 255, 255)),
):
    helpers.configure_rect_light(location, target, intensity, 160, 160, color)
sky = helpers.spawn(unreal.SkyLight, unreal.Vector())
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 0.25)
sky.get_component_by_class(unreal.SkyLightComponent).recapture_sky()
capture = helpers.spawn(unreal.SceneCapture2D, unreal.Vector())
component = capture.capture_component2d
component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
component.set_editor_property("capture_every_frame", False)
component.set_editor_property("capture_on_movement", False)
render_target = unreal.RenderingLibrary.create_render_target2d(
    world, 1280, 1280, unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.028, 0.032, 0.040, 1), False,
)
component.set_editor_property("texture_target", render_target)
for command in (
    "r.EyeAdaptationQuality 0", "r.ExposureOffset -0.55", "r.ScreenPercentage 100",
    "r.SkeletalMeshLODBias 0", "r.VolumetricCloud 0", "r.Lumen.GlobalIllumination 0",
    "r.Lumen.Reflections 0", "r.SSR.Quality 0", "r.PostProcessAAQuality 2",
    # A synchronous SceneCapture does not tick Nanite page streaming between
    # views. The full-detail authored fallback gives deterministic geometry.
    "r.Nanite 0", "r.TextureStreaming 0",
):
    unreal.SystemLibrary.execute_console_command(world, command)

report = {"status": "capturing", "characters": [], "output": str(output)}
host_class = unreal.load_class(None, helpers.HOST_CLASS)
for index in range(5):
    name = "guide" if index == 0 else f"crew{index:02d}"
    host = helpers.spawn(host_class, unreal.Vector())
    host.initialize_avatar_visual()
    host.configure_appearance(max(0, index - 1), 0, index == 0)
    host.set_avatar_action(unreal.RaftSimCrewAvatarAction.SEATED_IDLE, 1.0)
    visual = host.get_production_visual_actor()
    if visual is None:
        raise RuntimeError(f"No gameplay visual for {name}")
    # Publish readiness just as the first gameplay tick does, before assessing
    # overlaps. Capture helpers must never approve temporary fallback anatomy.
    if visual.get_class().get_path_name() == helpers.CC0_CLASS:
        if not host.activate_cc0_fallback_for_validation():
            raise RuntimeError(f"Incomplete CC0 ownership: {name}")
        host.set_avatar_action(unreal.RaftSimCrewAvatarAction.SEATED_IDLE, 1.0)
        visual = host.get_production_visual_actor()
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    row = {"identity": name, "visual_class": visual.get_class().get_path_name(), "images": {},
           "helmet_fit_scale": host.get_production_helmet_fit_scale()}
    if hasattr(visual, "get_selected_mesh_path"):
        row["mesh"] = visual.get_selected_mesh_path()
    views = {}
    for label, degrees in (("front", 0), ("front_right", 45), ("right", 90),
                           ("rear_right", 135), ("rear", 180), ("left", 270)):
        radians = math.radians(degrees)
        views[label] = (unreal.Vector(320 * math.cos(radians), 320 * math.sin(radians), 108),
                        unreal.Vector(12, 0, 68), 38)
    head = visual.get_solved_head_world_location()
    for label, offset in (("head_front", unreal.Vector(100, 0, 12)),
                          ("head_rear", unreal.Vector(-100, 0, 12)),
                          ("head_side", unreal.Vector(0, 100, 8))):
        views[label] = (head + offset, head, 32)
    views["boots"] = (unreal.Vector(145, 105, 65), unreal.Vector(33, 0, 12), 32)
    for label, (location, aim, fov) in views.items():
        capture.set_actor_location(location, False, False)
        capture.set_actor_rotation(helpers.look_at(location, aim), False)
        component.set_editor_property("fov_angle", fov)
        path = helpers.export_capture(world, component, render_target, f"{name}_{label}")
        row["images"][label] = str(path)
    row["pose_checks"] = []
    for action_name in ("FORWARD_STROKE", "BRACE", "REENTRY"):
        host.set_avatar_action(getattr(unreal.RaftSimCrewAvatarAction, action_name), 1.0)
        check = {
            "action": action_name,
            "finite": host.has_finite_visual_transforms(),
            "exclusive_body": host.has_exclusive_cc0_body_ownership(),
            "helmet_anchor_error_cm": host.get_production_helmet_head_error_cm(),
            "helmet_forward_alignment": host.get_production_helmet_forward_alignment(),
        }
        if not check["finite"] or not check["exclusive_body"]:
            raise RuntimeError(f"Invalid gameplay pose: {name} {check}")
        location, aim, fov = views["front_right"]
        capture.set_actor_location(location, False, False)
        capture.set_actor_rotation(helpers.look_at(location, aim), False)
        component.set_editor_property("fov_angle", fov)
        label = action_name.lower()
        row["images"][label] = str(helpers.export_capture(
            world, component, render_target, f"{name}_{label}"))
        row["pose_checks"].append(check)
    report["characters"].append(row)
    (output / "capture.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.EditorLevelLibrary.destroy_actor(visual)
    unreal.EditorLevelLibrary.destroy_actor(host)
    unreal.log(f"Crew review captured {name}")
report["status"] = "complete"
(output / "capture.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"Crew review complete: {output}")
