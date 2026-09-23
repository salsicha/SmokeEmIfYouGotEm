"""Inspect renderer-owned paddles and CC0 grip anchors on the production raft.

Supporting posed views, not river-motion or performance acceptance. No assets
or level are saved. RAFTSIM_PADDLE_REVIEW_OUTPUT must name a fresh directory.
"""
import importlib.util
import json
import math
import os
from pathlib import Path

import unreal

spec = importlib.util.spec_from_file_location(
    "crew_helpers", Path(__file__).with_name("capture_cc0_production_roster.py"))
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
output = Path(os.environ["RAFTSIM_PADDLE_REVIEW_OUTPUT"])
output.mkdir(parents=True, exist_ok=False)
helpers.OUTPUT_ROOT = output
world = unreal.EditorLevelLibrary.get_editor_world()
raft = helpers.spawn(unreal.load_class(None, "/Script/RaftSimRaft.RaftSimRaftActor"), unreal.Vector())
raft.initialize_crew_seating_for_validation()
crew = [a for a in unreal.EditorLevelLibrary.get_all_level_actors()
        if a.get_class().get_path_name() == helpers.HOST_CLASS and a.get_owner() == raft]
if len(crew) != 5:
    raise RuntimeError("Expected five actual gameplay crew")
for eye in (unreal.Vector(200, 350, 400), unreal.Vector(-250, -350, 300)):
    helpers.configure_rect_light(eye, unreal.Vector(0, 0, 50), 180, 300, 300,
                                 unreal.Color(245, 241, 235, 255))
capture = helpers.spawn(unreal.SceneCapture2D, unreal.Vector())
component = capture.capture_component2d
component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
component.set_editor_property("capture_every_frame", False)
component.set_editor_property("capture_on_movement", False)
target = unreal.RenderingLibrary.create_render_target2d(
    world, 1280, 960, unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.03, 0.03, 0.03, 1), False)
component.set_editor_property("texture_target", target)
for command in ("r.EyeAdaptationQuality 0", "r.TextureStreaming 0", "r.Nanite 0"):
    unreal.SystemLibrary.execute_console_command(world, command)
report = {"schema": "raftsim.crew_rigid_paddle_views.v1", "passed": False,
          "visual_accepted": False, "motion_accepted": False, "poses": [], "images": []}
failures = []
for action_name in ("SEATED_IDLE", "FORWARD_STROKE", "BACK_STROKE", "TURN_LEFT",
                    "TURN_RIGHT", "BRACE", "HIGH_SIDE_PORT", "HIGH_SIDE_STARBOARD"):
    for index, host in enumerate(crew):
        host.set_avatar_action(getattr(unreal.RaftSimCrewAvatarAction, action_name), 1.0)
        parts = {p.get_name(): p for p in host.get_components_by_class(unreal.ProceduralMeshComponent)}
        top = parts["PaddleGrip"].get_editor_property("relative_location")
        bottom = parts["PaddleBlade"].get_editor_property("relative_location")
        delta = helpers.vector_values(bottom - top)
        length = math.sqrt(sum(v*v for v in delta))
        visual = host.get_production_visual_actor()
        error = visual.get_maximum_paddle_grip_anchor_error_cm()
        row = {"action": action_name, "crew": index, "shaft_cm": length,
               "grip_anchor_error_cm": error, "finite": host.has_finite_visual_transforms()}
        report["poses"].append(row)
        if (not math.isfinite(length) or abs(length - 120) > 0.001 or
                not row["finite"] or not math.isfinite(error) or error > 0.25):
            failures.append(row)
    if action_name in ("SEATED_IDLE", "FORWARD_STROKE", "BRACE", "HIGH_SIDE_PORT"):
        for label, eye in (("side", unreal.Vector(60, 850, 230)),
                           ("rear", unreal.Vector(-650, 440, 320))):
            aim = unreal.Vector(0, 0, 45)
            capture.set_actor_location(eye, False, False)
            capture.set_actor_rotation(helpers.look_at(eye, aim), False)
            component.set_editor_property("fov_angle", 48)
            report["images"].append(str(helpers.export_capture(
                world, component, target, action_name.lower()+"_"+label)))
report["failures"] = failures
report["passed"] = not failures
(output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("Rendered paddle or grip failed; retained report contains failures")
unreal.log("Rigid crew paddle review complete: " + str(output))
