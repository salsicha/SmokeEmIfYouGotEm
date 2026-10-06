"""Render actual gameplay crew on the production raft; no river physics needed."""
import importlib.util
import json
import os
from pathlib import Path

import unreal

spec = importlib.util.spec_from_file_location(
    "helpers", Path(__file__).with_name("capture_cc0_production_roster.py"))
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
output = Path(unreal.Paths.project_dir()).resolve().parent / "docs/crew-review-2026-09-06"
output /= os.environ.get("RAFTSIM_SEAT_REVIEW_LABEL", "seat-contact")
output.mkdir(parents=True, exist_ok=True)
helpers.OUTPUT_ROOT = output
world = unreal.EditorLevelLibrary.get_editor_world()
for command in (
    "r.EyeAdaptationQuality 0", "r.ExposureOffset -0.55", "r.ScreenPercentage 100",
    "r.SkeletalMeshLODBias 0", "r.VolumetricCloud 0", "r.Lumen.GlobalIllumination 0",
    "r.Lumen.Reflections 0", "r.SSR.Quality 0", "r.PostProcessAAQuality 2",
    "r.Nanite 0", "r.TextureStreaming 0",
):
    unreal.SystemLibrary.execute_console_command(world, command)
for location, intensity in ((unreal.Vector(300, 280, 330), 180),
                            (unreal.Vector(100, -300, 250), 140),
                            (unreal.Vector(-350, 50, 220), 150)):
    helpers.configure_rect_light(location, unreal.Vector(0, 0, 55), intensity,
                                 250, 250, unreal.Color(245, 241, 235, 255))
sky = helpers.spawn(unreal.SkyLight, unreal.Vector())
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 0.25)
sky.get_component_by_class(unreal.SkyLightComponent).recapture_sky()
capture = helpers.spawn(unreal.SceneCapture2D, unreal.Vector())
component = capture.capture_component2d
component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
component.set_editor_property("capture_every_frame", False)
component.set_editor_property("capture_on_movement", False)
target = unreal.RenderingLibrary.create_render_target2d(
    world, 1400, 1100, unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.028, 0.032, 0.040, 1), False)
component.set_editor_property("texture_target", target)
raft = helpers.spawn(unreal.load_class(None, "/Script/RaftSimRaft.RaftSimRaftActor"), unreal.Vector())
raft.initialize_crew_seating_for_validation()
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
crew = [actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()
        if actor.get_class().get_path_name() == helpers.HOST_CLASS and actor.get_owner() == raft]
if len(crew) != 5:
    raise RuntimeError(f"Expected five gameplay crew, got {len(crew)}")

def render(name, eye, aim, fov=42):
    capture.set_actor_location(eye, False, False)
    capture.set_actor_rotation(helpers.look_at(eye, aim), False)
    component.set_editor_property("fov_angle", fov)
    return str(helpers.export_capture(world, component, target, name))

report = {"status": "capturing", "characters": [], "views": {}}
for index, host in enumerate(crew):
    pos = host.get_actor_location()
    name = f"seat_{index}"
    points = host.get_seated_contact_points_local_cm()
    row = {"name": name, "mesh": host.get_production_visual_actor().get_selected_mesh_path(),
           "position": helpers.vector_values(pos), "sample_count": len(points), "images": {}, "poses": []}
    if not points:
        raise RuntimeError(f"No actual body contact samples: {name}")
    aim = pos + unreal.Vector(-4, 0, 31)
    side = -1 if pos.y < 0 else 1
    for label, offset in (("side", unreal.Vector(0, side * 210, 5)),
                          ("rear", unreal.Vector(-170, side * 100, 0)),
                          ("upper", unreal.Vector(-140, side * 190, 95))):
        row["images"][label] = render(f"{name}_{label}", aim + offset, aim, 36)
    for action in ("SEATED_IDLE", "FORWARD_STROKE", "BRACE"):
        host.set_avatar_action(getattr(unreal.RaftSimCrewAvatarAction, action), 1.0)
        row["poses"].append({"action": action,
            "clearance_cm": raft.get_crew_seat_contact_clearance_cm(host),
            "finite": host.has_finite_visual_transforms()})
    host.set_avatar_action(unreal.RaftSimCrewAvatarAction.SEATED_IDLE, 1.0)
    report["characters"].append(row)
report["views"]["rear"] = render("raft_rear", unreal.Vector(-720, 330, 220), unreal.Vector(0, 0, 50), 48)
report["views"]["side"] = render("raft_side", unreal.Vector(0, 760, 85), unreal.Vector(0, 0, 45), 48)
raft.set_actor_location(unreal.Vector(10300, -7400, 2300), False, False)
raft.set_actor_rotation(unreal.Rotator(pitch=7, yaw=35, roll=-9), False)
report["transformed_raft_clearances_cm"] = [
    raft.get_crew_seat_contact_clearance_cm(host) for host in crew]
report["status"] = "complete"
if any(abs(value + 1.0) > 0.05 for value in report["transformed_raft_clearances_cm"]):
    report["status"] = "failed_transform_invariance"
for row in report["characters"]:
    for pose in row["poses"]:
        if not pose["finite"] or not -1.5 <= pose["clearance_cm"] <= 0.25:
            report["status"] = "failed_contact"
(output / "capture.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
if report["status"] != "complete":
    raise RuntimeError("Crew contact failed; see capture.json")
unreal.log(f"Crew seat review complete: {output}")
