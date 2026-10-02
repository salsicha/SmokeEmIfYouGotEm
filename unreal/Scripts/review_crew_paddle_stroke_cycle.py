"""Render the crew through one forward paddle stroke on the production raft.

Supporting posed views for reviewing how the paddle is held: catch, mid
power, exit and mid recovery, from the side and from ahead. Run in the
editor (UnrealEditor -ExecutePythonScript=... -RenderOffscreen) with
RAFTSIM_STROKE_REVIEW_OUTPUT naming a fresh directory. Nothing is saved.
"""
import importlib.util
import json
import os
from pathlib import Path

import unreal

spec = importlib.util.spec_from_file_location(
    "crew_helpers", Path(__file__).with_name("capture_cc0_production_roster.py"))
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
output = Path(os.environ["RAFTSIM_STROKE_REVIEW_OUTPUT"])
output.mkdir(parents=True, exist_ok=False)
helpers.OUTPUT_ROOT = output
world = unreal.EditorLevelLibrary.get_editor_world()
raft = helpers.spawn(unreal.load_class(None, "/Script/RaftSimRaft.RaftSimRaftActor"), unreal.Vector())
raft.initialize_crew_seating_for_validation()
crew = [a for a in unreal.EditorLevelLibrary.get_all_level_actors()
        if a.get_class().get_path_name() == helpers.HOST_CLASS and a.get_owner() == raft]
if len(crew) != 5:
    raise RuntimeError("Expected five actual gameplay crew")
for eye in (unreal.Vector(200, 350, 400), unreal.Vector(-250, -350, 300), unreal.Vector(400, -100, 250)):
    helpers.configure_rect_light(eye, unreal.Vector(0, 0, 50), 160, 300, 300,
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

PHASES = (("catch", 0.0), ("power", 0.24), ("exit", 0.58), ("recovery", 0.79))
VIEWS = (("side", unreal.Vector(40, 560, 170), unreal.Vector(10, 0, 70)),
         ("ahead", unreal.Vector(520, 260, 200), unreal.Vector(0, 0, 70)))
report = {"schema": "raftsim.crew_paddle_stroke_cycle.v1", "images": [], "poses": []}
for label, phase in PHASES:
    for host in crew:
        host.set_avatar_action_phase_for_validation(unreal.RaftSimCrewAvatarAction.FORWARD_STROKE, phase)
        visual = host.get_production_visual_actor()
        report["poses"].append({
            "phase": label, "host": host.get_name(),
            "grip_anchor_error_cm": visual.get_maximum_paddle_grip_anchor_error_cm()})
    for view, eye, aim in VIEWS:
        capture.set_actor_location(eye, False, False)
        capture.set_actor_rotation(helpers.look_at(eye, aim), False)
        component.set_editor_property("fov_angle", 40)
        report["images"].append(str(helpers.export_capture(
            world, component, target, f"stroke_{label}_{view}")))
(output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("Crew paddle stroke cycle review complete: " + str(output))
