"""Render the single-rower oar rig through its strokes on the production raft.

Supporting posed views for reviewing the rig (docs/oar-rig-reference.md):
the frame, gear and oars, and how the rower holds the handles at rest, through
a pull (catch, drive, finish, recovery), mid push and mid pivot, from the
side, from ahead, from above and over the rower's shoulder. A flat plane
marks the loaded waterline the blades work against. Run in the editor
(UnrealEditor -ExecutePythonScript=... -RenderOffscreen) with
RAFTSIM_OAR_REVIEW_OUTPUT naming a fresh directory and RAFTSIM_OAR_REVIEW_RIG
"colorado" (default) or "zambezi". Nothing is saved.
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
output = Path(os.environ["RAFTSIM_OAR_REVIEW_OUTPUT"])
output.mkdir(parents=True, exist_ok=False)
helpers.OUTPUT_ROOT = output
rig_name = os.environ.get("RAFTSIM_OAR_REVIEW_RIG", "colorado")
rig = (unreal.RaftSimRaftRig.ZAMBEZI_OAR_RIG if rig_name == "zambezi"
       else unreal.RaftSimRaftRig.COLORADO_OAR_RIG)
world = unreal.EditorLevelLibrary.get_editor_world()
raft = helpers.spawn(unreal.load_class(None, "/Script/RaftSimRaft.RaftSimRaftActor"), unreal.Vector())
raft.set_raft_rig_for_validation(rig)
raft.initialize_crew_seating_for_validation()
crew = [a for a in unreal.EditorLevelLibrary.get_all_level_actors()
        if a.get_class().get_path_name() == helpers.HOST_CLASS and a.get_owner() == raft]
if len(crew) != 1:
    raise RuntimeError(f"Expected one rower, found {len(crew)}")
rower = crew[0]

# The loaded waterline, 14 cm above the raft origin (RaftSimOarRig.cpp
# DefaultWaterLocalZ in the raft visual's frame, 28 cm below the origin).
water = helpers.spawn(unreal.StaticMeshActor, unreal.Vector(0, 0, 14))
water_mesh = water.static_mesh_component
water_mesh.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane"))
water_mesh.set_material(0, unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial"))
water.set_actor_scale3d(unreal.Vector(16, 16, 1))
water_material = water_mesh.create_dynamic_material_instance(0)
water_material.set_vector_parameter_value("Color", unreal.LinearColor(0.05, 0.10, 0.12, 1))

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

# (label, phase, left oar, right oar): +1 push, -1 pull, 0 rest.
POSES = (("rest", 0.0, 0.0, 0.0),
         ("pull_catch", 0.06, -1.0, -1.0),
         ("pull_drive", 0.32, -1.0, -1.0),
         ("pull_finish", 0.56, -1.0, -1.0),
         ("pull_recovery", 0.80, -1.0, -1.0),
         ("push_drive", 0.32, 1.0, 1.0),
         ("pivot_right", 0.32, 1.0, -1.0))
VIEWS = (("side", unreal.Vector(-20, 620, 190), unreal.Vector(-10, 0, 60), 50),
         ("ahead", unreal.Vector(560, -300, 240), unreal.Vector(-20, 0, 60), 45),
         ("above", unreal.Vector(-10, 1, 760), unreal.Vector(-10, 0, 0), 55),
         ("shoulder", unreal.Vector(-170, 70, 170), unreal.Vector(80, -10, 60), 70),
         ("hands", unreal.Vector(80, -70, 125), unreal.Vector(-20, 0, 85), 38))
report = {"schema": "raftsim.oar_rig_stroke_cycle.v1", "rig": rig_name, "images": [], "poses": []}
for label, phase, left, right in POSES:
    raft.pose_oar_rig_for_validation(phase, left, right)
    visual = rower.get_production_visual_actor()
    report["poses"].append({
        "pose": label,
        "grip_anchor_error_cm": visual.get_maximum_paddle_grip_anchor_error_cm() if visual else None})
    views = VIEWS if label in ("rest", "pull_drive", "pull_finish") else VIEWS[:2]
    for view, eye, aim, fov in views:
        capture.set_actor_location(eye, False, False)
        capture.set_actor_rotation(helpers.look_at(eye, aim), False)
        component.set_editor_property("fov_angle", fov)
        report["images"].append(str(helpers.export_capture(
            world, component, target, f"oar_{label}_{view}")))
(output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("Oar rig stroke cycle review complete: " + str(output))
