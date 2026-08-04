"""Render the packaged CC0 fallback with exclusive full-body ownership.

The primary assembled-character turntable cannot prove the shipping fallback
because it deliberately selects the MetaHuman adapter when that roster is
installed. This capture forces the public validation path on the ordinary
gameplay host, then records the guide and four crew identities from front,
profile, rear, face, grip-front, and grip-profile views. Safety gear and the
paddle remain host-owned; redundant procedural anatomy must be hidden behind
the complete CC0 body. The close grip views fail closed on palm anchoring and
finger/thumb chain closure before any evidence is promoted.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import traceback

import unreal


SCHEMA = "raftsim.cc0.exclusive_body_capture.v2"
CHARACTER_NAMES = (
    "RaftSim_CC0_Guide",
    "RaftSim_CC0_Crew01",
    "RaftSim_CC0_Crew02",
    "RaftSim_CC0_Crew03",
    "RaftSim_CC0_Crew04",
)
HOST_CLASS = "/Script/RaftSimRaft.RaftSimCrewAvatarActor"
CC0_CLASS = "/Script/RaftSimRaft.RaftSimCC0CrewVisualActor"
OUTPUT_ROOT = (
    Path(unreal.Paths.project_saved_dir())
    / "RaftSimValidation"
    / "m9"
    / "cc0-exclusive-body-captures"
)
REPORT_PATH = OUTPUT_ROOT.parent / "cc0-exclusive-body-captures.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_report(report: dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )


def spawn(actor_class, location: unreal.Vector, rotation=unreal.Rotator()):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        actor_class, location, rotation
    )
    if actor is None:
        raise RuntimeError(f"Failed to spawn {actor_class}")
    return actor


def look_at(location: unreal.Vector, target: unreal.Vector) -> unreal.Rotator:
    return unreal.MathLibrary.find_look_at_rotation(location, target)


def vector_values(vector: unreal.Vector) -> list[float]:
    return [float(vector.x), float(vector.y), float(vector.z)]


def finite_vector(vector: unreal.Vector) -> bool:
    return all(abs(value) < 1.0e8 for value in vector_values(vector))


def configure_rect_light(
    location: unreal.Vector,
    target: unreal.Vector,
    intensity: float,
    width: float,
    height: float,
    color: unreal.Color,
):
    actor = spawn(unreal.RectLight, location, look_at(location, target))
    component = actor.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("source_width", width)
    component.set_editor_property("source_height", height)
    component.set_editor_property("light_color", color)
    component.set_editor_property("cast_shadows", False)
    return actor


def export_capture(world, component, render_target, name: str) -> Path:
    component.capture_scene()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(
        world, render_target, str(OUTPUT_ROOT), f"{name}.png"
    )
    path = OUTPUT_ROOT / f"{name}.png"
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"Renderer produced no valid capture: {path}")
    return path


def main() -> None:
    script_path = Path(__file__).resolve()
    report: dict[str, object] = {
        "schema": SCHEMA,
        "status": "starting",
        "script": str(script_path),
        "script_sha256": sha256(script_path),
        "capture_resolution": [1536, 1024],
        "characters": [],
    }
    write_report(report)
    try:
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        host_class = unreal.load_class(None, HOST_CLASS)
        cc0_class = unreal.load_class(None, CC0_CLASS)
        if host_class is None or cc0_class is None:
            raise RuntimeError("Gameplay host or packaged CC0 adapter class is missing")
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        world = unreal.EditorLevelLibrary.get_editor_world()
        if world is None:
            raise RuntimeError("No editor world is available for CC0 capture")

        floor_actor = spawn(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, -1.0))
        floor_actor.static_mesh_component.set_static_mesh(
            unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
        )
        floor_actor.set_actor_scale3d(unreal.Vector(5.0, 5.0, 5.0))

        target = unreal.Vector(0.0, 0.0, 100.0)
        configure_rect_light(
            unreal.Vector(180.0, 240.0, 235.0),
            target,
            150.0,
            165.0,
            165.0,
            unreal.Color(255, 239, 222, 255),
        )
        configure_rect_light(
            unreal.Vector(-180.0, 175.0, 165.0),
            target,
            85.0,
            220.0,
            220.0,
            unreal.Color(205, 224, 255, 255),
        )
        configure_rect_light(
            unreal.Vector(75.0, -165.0, 215.0),
            unreal.Vector(0.0, 0.0, 135.0),
            80.0,
            100.0,
            100.0,
            unreal.Color(186, 211, 255, 255),
        )
        sky = spawn(unreal.SkyLight, unreal.Vector())
        sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
        sky_component.set_editor_property("intensity", 0.25)
        sky_component.recapture_sky()

        capture = spawn(unreal.SceneCapture2D, unreal.Vector())
        capture_component = capture.capture_component2d
        capture_component.set_editor_property("fov_angle", 36.0)
        capture_component.set_editor_property(
            "capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
        )
        capture_component.set_editor_property("capture_every_frame", False)
        capture_component.set_editor_property("capture_on_movement", False)
        render_target = unreal.RenderingLibrary.create_render_target2d(
            world,
            1536,
            1024,
            unreal.TextureRenderTargetFormat.RTF_RGBA8,
            unreal.LinearColor(0.018, 0.022, 0.028, 1.0),
            False,
        )
        capture_component.set_editor_property("texture_target", render_target)

        unreal.SystemLibrary.execute_console_command(world, "r.EyeAdaptationQuality 0")
        unreal.SystemLibrary.execute_console_command(world, "r.ExposureOffset -0.55")
        unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
        unreal.SystemLibrary.execute_console_command(world, "r.SkeletalMeshLODBias 0")
        unreal.SystemLibrary.execute_console_command(world, "r.VolumetricCloud 0")
        unreal.SystemLibrary.execute_console_command(world, "r.Lumen.GlobalIllumination 0")
        unreal.SystemLibrary.execute_console_command(world, "r.Lumen.Reflections 0")
        unreal.SystemLibrary.execute_console_command(world, "r.SSR.Quality 0")
        unreal.SystemLibrary.execute_console_command(world, "r.PostProcessAAQuality 2")

        for roster_index, character_name in enumerate(CHARACTER_NAMES):
            is_guide = roster_index == 0
            variant_index = max(roster_index - 1, 0)
            actor = spawn(host_class, unreal.Vector())
            actor.initialize_avatar_visual()
            actor.configure_appearance(variant_index, 0, is_guide)
            if not actor.activate_cc0_fallback_for_validation():
                raise RuntimeError(
                    f"{character_name} could not activate the packaged CC0 fallback"
                )
            actor.set_avatar_action(
                unreal.RaftSimCrewAvatarAction.SEATED_IDLE, 1.0
            )
            visual_actor = actor.get_production_visual_actor()
            if visual_actor is None or visual_actor.get_class() != cc0_class:
                raise RuntimeError(
                    f"Gameplay host did not select CC0 adapter: {character_name}"
                )
            if (
                not actor.is_using_production_visual()
                or not actor.has_exclusive_cc0_body_ownership()
                or not actor.has_layered_commercial_safety_gear()
                or not actor.has_production_whitewater_helmet()
                or not actor.has_production_whitewater_pfd()
                or not actor.has_production_river_boots()
                or not actor.has_fitted_upright_production_river_boots()
                or not actor.has_commercial_paddle_silhouette()
                or not actor.has_finite_visual_transforms()
                or not visual_actor.is_body_ready()
                or not visual_actor.has_finite_pose()
            ):
                raise RuntimeError(
                    f"Incomplete exclusive CC0 presentation: {character_name}"
                )

            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
            selected_mesh = unreal.load_asset(visual_actor.get_selected_mesh_path())
            if not isinstance(selected_mesh, unreal.SkeletalMesh):
                raise RuntimeError(f"Selected CC0 mesh is unavailable: {character_name}")
            eye_material_paths = []
            for slot in selected_mesh.get_editor_property("materials"):
                slot_name = str(slot.get_editor_property("material_slot_name"))
                material = slot.get_editor_property("material_interface")
                if "eye" in slot_name.lower() and material is not None:
                    eye_material_paths.append(material.get_path_name())
            expected_eye_material = (
                "/Game/RaftSim/Characters/Production/CC0/Materials/"
                "M_RaftSim_CC0_Eyes.M_RaftSim_CC0_Eyes"
            )
            if eye_material_paths != [expected_eye_material]:
                raise RuntimeError(
                    f"Unexpected eye material binding for {character_name}: "
                    f"{eye_material_paths}"
                )

            origin, extent = actor.get_actor_bounds(False, False)
            if not finite_vector(origin) or not finite_vector(extent) or extent.z < 45.0:
                raise RuntimeError(
                    f"Invalid CC0 bounds for {character_name}: {origin}, {extent}"
                )
            stem = character_name.lower()
            target_point = unreal.Vector(origin.x, origin.y, 92.0)
            solved_head = visual_actor.get_solved_head_world_location()
            face_forward = visual_actor.get_solved_face_forward_world_vector()
            face_up = visual_actor.get_solved_face_up_world_vector()
            minimum_solved_head_z = origin.z + extent.z * 0.45
            if solved_head.z < minimum_solved_head_z:
                raise RuntimeError(
                    f"Rendered eye/head anchor fell below the upper body for "
                    f"{character_name}: z={solved_head.z:.3f}cm, "
                    f"minimum={minimum_solved_head_z:.3f}cm"
                )
            face_target = unreal.Vector(origin.x, origin.y, 92.0)
            # The deterministic seated-idle pose still holds the production
            # paddle. These two matched close views frame both the inboard
            # T-grip and outboard shaft hand so fingers cannot pass a full-body
            # review merely by being hidden behind the PFD or paddle.
            grip_target = unreal.Vector(34.0, -11.0, 52.0)
            views = {
                "full": (
                    unreal.Vector(origin.x + 430.0, origin.y, 104.0),
                    target_point,
                    36.0,
                ),
                "profile": (
                    unreal.Vector(origin.x, origin.y + 430.0, 104.0),
                    target_point,
                    36.0,
                ),
                "rear": (
                    unreal.Vector(origin.x - 430.0, origin.y, 104.0),
                    target_point,
                    36.0,
                ),
                "face": (
                    unreal.Vector(origin.x, origin.y + 115.0, 95.2),
                    face_target,
                    36.0,
                ),
                "grip": (
                    grip_target + unreal.Vector(155.0, 0.0, 18.0),
                    grip_target,
                    28.0,
                ),
                "grip_profile": (
                    grip_target + unreal.Vector(0.0, 155.0, 18.0),
                    grip_target,
                    28.0,
                ),
            }
            captures: dict[str, object] = {}
            for view_name, (location, view_target, fov) in views.items():
                capture.set_actor_location(location, False, False)
                capture.set_actor_rotation(look_at(location, view_target), False)
                capture_component.set_editor_property("fov_angle", fov)
                path = export_capture(
                    world, capture_component, render_target, f"{stem}_{view_name}"
                )
                captures[view_name] = {
                    "path": str(path),
                    "sha256": sha256(path),
                }

            helmet_head_error_cm = actor.get_production_helmet_head_error_cm()
            helmet_forward_alignment = (
                actor.get_production_helmet_forward_alignment()
            )
            helmet_fit_scale = actor.get_production_helmet_fit_scale()
            paddle_grip_anchor_error_cm = (
                visual_actor.get_maximum_paddle_grip_anchor_error_cm()
            )
            upper_finger_closure_degrees = (
                visual_actor.get_minimum_upper_paddle_finger_closure_degrees()
            )
            lower_finger_closure_degrees = (
                visual_actor.get_minimum_lower_paddle_finger_closure_degrees()
            )
            thumb_closure_degrees = (
                visual_actor.get_minimum_paddle_thumb_closure_degrees()
            )
            if helmet_head_error_cm > 1.0:
                raise RuntimeError(
                    f"Helmet head error exceeds 1 cm for {character_name}: "
                    f"{helmet_head_error_cm:.6f}"
                )
            if helmet_forward_alignment < 0.98:
                raise RuntimeError(
                    f"Helmet faces away from {character_name}: "
                    f"{helmet_forward_alignment:.6f}"
                )
            if not 0.90 <= helmet_fit_scale <= 1.02:
                raise RuntimeError(
                    f"Helmet fit scale is invalid for {character_name}: "
                    f"{helmet_fit_scale:.6f}"
                )
            if not visual_actor.has_articulated_paddle_grip_rig():
                raise RuntimeError(
                    f"{character_name} has no complete articulated paddle-grip rig"
                )
            if not visual_actor.has_active_paddle_grip_pose():
                raise RuntimeError(
                    f"{character_name} did not retain an active seated paddle grip"
                )
            if paddle_grip_anchor_error_cm > 0.25:
                raise RuntimeError(
                    f"Palm anchor exceeds 0.25 cm for {character_name}: "
                    f"{paddle_grip_anchor_error_cm:.6f}"
                )
            if upper_finger_closure_degrees < 120.0:
                raise RuntimeError(
                    f"Upper T-grip finger closure is below 120 degrees for "
                    f"{character_name}: {upper_finger_closure_degrees:.6f}"
                )
            if lower_finger_closure_degrees < 210.0:
                raise RuntimeError(
                    f"Lower shaft finger closure is below 210 degrees for "
                    f"{character_name}: {lower_finger_closure_degrees:.6f}"
                )
            if thumb_closure_degrees < 50.0:
                raise RuntimeError(
                    f"Opposed thumb closure is below 50 degrees for "
                    f"{character_name}: {thumb_closure_degrees:.6f}"
                )

            report["characters"].append(
                {
                    "name": character_name,
                    "guide": is_guide,
                    "variant_index": variant_index,
                    "selected_mesh": visual_actor.get_selected_mesh_path(),
                    "runtime_eye_materials": eye_material_paths,
                    "runtime_solved_head_cm": vector_values(solved_head),
                    "runtime_solved_head_minimum_z_cm": minimum_solved_head_z,
                    "runtime_face_forward": vector_values(face_forward),
                    "runtime_face_up": vector_values(face_up),
                    "runtime_exclusive_cc0_body_ownership": (
                        actor.has_exclusive_cc0_body_ownership()
                    ),
                    "runtime_body_ready": visual_actor.is_body_ready(),
                    "runtime_finite_pose": visual_actor.has_finite_pose(),
                    "runtime_articulated_paddle_grip": (
                        visual_actor.has_articulated_paddle_grip_rig()
                    ),
                    "runtime_active_paddle_grip_pose": (
                        visual_actor.has_active_paddle_grip_pose()
                    ),
                    "runtime_paddle_grip_anchor_error_cm": (
                        paddle_grip_anchor_error_cm
                    ),
                    "runtime_upper_paddle_finger_closure_degrees": (
                        upper_finger_closure_degrees
                    ),
                    "runtime_lower_paddle_finger_closure_degrees": (
                        lower_finger_closure_degrees
                    ),
                    "runtime_paddle_thumb_closure_degrees": (
                        thumb_closure_degrees
                    ),
                    "runtime_production_pfd": (
                        actor.has_production_whitewater_pfd()
                    ),
                    "runtime_production_helmet": (
                        actor.has_production_whitewater_helmet()
                    ),
                    "runtime_helmet_head_error_cm": helmet_head_error_cm,
                    "runtime_helmet_forward_alignment": helmet_forward_alignment,
                    "runtime_helmet_fit_scale": helmet_fit_scale,
                    "runtime_production_boots": actor.has_production_river_boots(),
                    "bounds_origin_cm": vector_values(origin),
                    "bounds_extent_cm": vector_values(extent),
                    "captures": captures,
                    "status": "captured",
                }
            )
            write_report(report)
            unreal.EditorLevelLibrary.destroy_actor(actor)

        report["captured_character_count"] = len(report["characters"])
        report["exclusive_body_count"] = sum(
            1
            for character in report["characters"]
            if character["runtime_exclusive_cc0_body_ownership"]
        )
        report["articulated_paddle_grip_count"] = sum(
            1
            for character in report["characters"]
            if character["runtime_articulated_paddle_grip"]
        )
        report["maximum_paddle_grip_anchor_error_cm"] = max(
            character["runtime_paddle_grip_anchor_error_cm"]
            for character in report["characters"]
        )
        report["minimum_upper_paddle_finger_closure_degrees"] = min(
            character["runtime_upper_paddle_finger_closure_degrees"]
            for character in report["characters"]
        )
        report["minimum_lower_paddle_finger_closure_degrees"] = min(
            character["runtime_lower_paddle_finger_closure_degrees"]
            for character in report["characters"]
        )
        report["minimum_paddle_thumb_closure_degrees"] = min(
            character["runtime_paddle_thumb_closure_degrees"]
            for character in report["characters"]
        )
        report["status"] = "capture_complete"
    except Exception as error:
        report["status"] = "error"
        report["error_type"] = type(error).__name__
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        unreal.log_error(f"RaftSim CC0 character capture failed: {error}")
        raise
    finally:
        write_report(report)


if __name__ == "__main__":
    main()
