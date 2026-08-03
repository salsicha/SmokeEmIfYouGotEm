"""Render deterministic full-body and helmet turntable evidence for the roster.

Run after ``build_metahuman_production_characters.py``. Captures and a
hash-addressed report are written to ``Saved/RaftSimValidation/m9``. The script
fails closed if any optimized Blueprint, output PNG, or finite actor bound is
missing; visual approval still requires review of the rendered pixels.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import traceback

import unreal


SCHEMA = "raftsim.metahuman.production_capture.v1"
BUILD_ROOT = "/Game/RaftSim/Characters/Production/MetaHumans"
CHARACTER_NAMES = (
    "MHC_RaftSim_Guide",
    "MHC_RaftSim_Crew_01",
    "MHC_RaftSim_Crew_02",
    "MHC_RaftSim_Crew_03",
    "MHC_RaftSim_Crew_04",
)
RUNTIME_ADAPTER_CLASS = "/Script/RaftSimRaft.RaftSimMetaHumanCrewVisualActor"
RUNTIME_HOST_CLASS = "/Script/RaftSimRaft.RaftSimCrewAvatarActor"
OUTPUT_ROOT = (
    Path(unreal.Paths.project_saved_dir())
    / "RaftSimValidation"
    / "m9"
    / "metahuman-captures"
)
REPORT_PATH = OUTPUT_ROOT.parent / "metahuman-production-captures.json"


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


def class_path(character_name: str) -> str:
    return (
        f"{BUILD_ROOT}/{character_name}/BP_{character_name}."
        f"BP_{character_name}_C"
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


def describe_groom_lods(asset) -> dict[str, object]:
    """Expose packaged geometry choices so a populated groom is auditable."""
    try:
        groups = []
        for group_index, group in enumerate(
            asset.get_editor_property("hair_groups_lod")
        ):
            lods = []
            for lod_index, lod in enumerate(group.get_editor_property("lods")):
                lods.append(
                    {
                        "lod": lod_index,
                        "geometry_type": str(
                            lod.get_editor_property("geometry_type")
                        ),
                        "screen_size": float(
                            lod.get_editor_property("screen_size")
                        ),
                        "visible": bool(lod.get_editor_property("visible")),
                    }
                )
            groups.append({"group": group_index, "lods": lods})
        cards = [
            {
                "group": int(card.get_editor_property("group_index")),
                "lod": int(card.get_editor_property("lod_index")),
                "mesh": (
                    card.get_editor_property("imported_mesh").get_path_name()
                    if card.get_editor_property("imported_mesh")
                    else None
                ),
            }
            for card in asset.get_editor_property("hair_groups_cards")
        ]
        meshes = []
        for mesh in asset.get_editor_property("hair_groups_meshes"):
            imported_mesh = mesh.get_editor_property("imported_mesh")
            meshes.append(
                {
                    "group": int(mesh.get_editor_property("group_index")),
                    "lod": int(mesh.get_editor_property("lod_index")),
                    "mesh": (
                        imported_mesh.get_path_name() if imported_mesh else None
                    ),
                }
            )
        return {"groups": groups, "cards": cards, "meshes": meshes}
    except Exception as error:
        return {"diagnostic_error": f"{type(error).__name__}: {error}"}


def configure_rect_light(
    location: unreal.Vector,
    target: unreal.Vector,
    intensity: float,
    width: float,
    height: float,
    color: unreal.Color,
    cast_shadows: bool = False,
):
    actor = spawn(unreal.RectLight, location, look_at(location, target))
    component = actor.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("source_width", width)
    component.set_editor_property("source_height", height)
    component.set_editor_property("light_color", color)
    # This is a deterministic asset/fit turntable, not final gameplay
    # evidence. Area-light shadow noise can obscure geometry and fabric color
    # in a single-frame SceneCapture, so matched hero captures own the separate
    # lit-shadow acceptance gate.
    component.set_editor_property("cast_shadows", cast_shadows)
    return actor


def export_capture(world, component, render_target, name: str) -> Path:
    # Material shader jobs are not necessarily submitted until the first scene
    # render sees an assembled MetaHuman. Prime that render, then use Unreal's
    # screenshot barrier to submit/drain shaders and stream virtual textures.
    # Without this barrier the first roster member can be exported with the
    # engine's gray checkerboard fallback even though its assets are valid.
    component.capture_scene()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    component.capture_scene()
    filename = f"{name}.png"
    unreal.RenderingLibrary.export_render_target(
        world, render_target, str(OUTPUT_ROOT), filename
    )
    path = OUTPUT_ROOT / filename
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
        classes = {}
        for character_name in CHARACTER_NAMES:
            path = class_path(character_name)
            actor_class = unreal.load_class(None, path)
            if actor_class is None:
                raise RuntimeError(f"Missing assembled production class: {path}")
            classes[character_name] = actor_class
        adapter_class = unreal.load_class(None, RUNTIME_ADAPTER_CLASS)
        if adapter_class is None:
            raise RuntimeError(
                f"Missing production gameplay adapter: {RUNTIME_ADAPTER_CLASS}"
            )
        host_class = unreal.load_class(None, RUNTIME_HOST_CLASS)
        if host_class is None:
            raise RuntimeError(
                f"Missing production gameplay host: {RUNTIME_HOST_CLASS}"
            )
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

        world = unreal.EditorLevelLibrary.get_editor_world()
        if world is None:
            raise RuntimeError("No editor world is available for character capture")

        floor_actor = spawn(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, -1.0))
        floor_actor.static_mesh_component.set_static_mesh(
            unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
        )
        floor_actor.set_actor_scale3d(unreal.Vector(5.0, 5.0, 5.0))

        target = unreal.Vector(0.0, 0.0, 105.0)
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

        capture_location = unreal.Vector(0.0, 430.0, 106.0)
        capture = spawn(
            unreal.SceneCapture2D,
            capture_location,
            look_at(capture_location, unreal.Vector(0.0, 0.0, 96.0)),
        )
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
        # Keep both renderer representations available, but disable global
        # overrides. The spawned gameplay adapter must itself select the
        # reviewed generated-card representation and exact audited LOD.
        unreal.SystemLibrary.execute_console_command(world, "r.HairStrands.Strands 1")
        unreal.SystemLibrary.execute_console_command(world, "r.HairStrands.Cards 1")
        unreal.SystemLibrary.execute_console_command(
            world, "r.HairStrands.UseCardsInsteadOfStrands 0"
        )
        unreal.SystemLibrary.execute_console_command(world, "r.HairStrands.MinLOD 0")

        for roster_index, character_name in enumerate(CHARACTER_NAMES):
            is_guide = roster_index == 0
            variant_index = max(roster_index - 1, 0)
            actor = spawn(host_class, unreal.Vector())
            actor.initialize_avatar_visual()
            actor.configure_appearance(variant_index, 0, is_guide)
            visual_actor = actor.get_production_visual_actor()
            if visual_actor is None or visual_actor.get_class() != adapter_class:
                raise RuntimeError(
                    f"Gameplay host did not select MetaHuman adapter: {character_name}"
                )
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
            assembled_actor = visual_actor.get_assembled_character_actor()
            if (
                assembled_actor is None
                or not actor.is_using_production_visual()
                or not actor.has_layered_commercial_safety_gear()
                or not actor.has_production_whitewater_helmet()
                or not actor.has_production_whitewater_pfd()
                or not actor.has_live_pfd_material_response()
                or not actor.has_live_splash_jacket_material_response()
                or not actor.has_production_river_boots()
                or not actor.has_fitted_upright_production_river_boots()
                or not actor.has_commercial_paddle_silhouette()
                or not actor.has_finite_visual_transforms()
                or not visual_actor.is_using_assembled_character()
                or not visual_actor.has_complete_assembled_presentation()
                or not visual_actor.has_articulated_paddle_grip_rig()
                or visual_actor.get_maximum_paddle_grip_anchor_error_cm() > 0.25
                or visual_actor.get_maximum_paddle_grip_contact_error_cm() > 0.25
                or not visual_actor.is_assembled_body_using_wetsuit()
                or not visual_actor.is_assembled_face_using_cropped_skin()
                or not visual_actor.is_assembled_wardrobe_suppressed_for_safety_gear()
                or not visual_actor.is_using_hair_mesh_fallback()
                or not visual_actor.is_hair_mesh_fallback_suppressed_for_helmet()
                or not visual_actor.is_assembled_hair_groom_suppressed_for_helmet()
                or not visual_actor.are_assembled_grooms_suppressed_for_gameplay()
                or visual_actor.get_hair_mesh_fallback_head_error_cm() > 1.0
                or actor.get_production_helmet_head_error_cm() > 1.0
                or actor.get_production_helmet_forward_alignment() < 0.98
                or not 0.899 <= actor.get_production_helmet_fit_scale() <= 1.021
                or actor.get_production_pfd_torso_error_cm() > 1.0
                or not actor.has_visible_waist_hip_silhouette()
                or actor.get_waist_hip_center_error_cm() > 0.1
                or not actor.is_waist_hip_material_opaque()
                or actor.get_maximum_hip_thigh_bridge_coverage_error_cm() > 0.25
                or not actor.has_continuous_thigh_knee_silhouette()
                or actor.get_minimum_thigh_mesh_vertex_count() < 650
                or actor.get_minimum_thigh_forward_alignment() < 0.98
                or actor.get_maximum_thigh_knee_bridge_coverage_error_cm() > 0.25
                or not actor.has_visible_shoulder_silhouette()
                or actor.get_minimum_shoulder_sleeve_vertex_count() < 1000
                or actor.get_maximum_shoulder_sleeve_anchor_error_cm() > 0.25
            ):
                raise RuntimeError(
                    f"Gameplay adapter rejected assembled production character: "
                    f"{character_name}; shoulder_silhouette="
                    f"{actor.has_visible_shoulder_silhouette()}, "
                    f"shoulder_sleeve_extent_cm="
                    f"{vector_values(actor.get_minimum_shoulder_sleeve_extent_cm())}, "
                    f"shoulder_sleeve_vertex_count="
                    f"{actor.get_minimum_shoulder_sleeve_vertex_count()}, "
                    f"shoulder_sleeve_anchor_error_cm="
                    f"{actor.get_maximum_shoulder_sleeve_anchor_error_cm():.3f}"
                )
            skeletal_components = []
            wardrobe_mesh_count = 0
            has_face_eyelash_material = False
            for component in assembled_actor.get_components_by_class(
                unreal.SkeletalMeshComponent
            ):
                mesh = component.get_editor_property("skeletal_mesh_asset")
                component_name = component.get_name()
                materials = [
                    material.get_path_name() if material else None
                    for material in component.get_materials()
                ]
                skeletal_components.append(
                    {
                        "component": component_name,
                        "mesh": mesh.get_path_name() if mesh else None,
                        "material_count": len(materials),
                        "materials": materials,
                        "visible": bool(component.is_visible()),
                    }
                )
                if component_name.lower() == "face":
                    has_face_eyelash_material = any(
                        material and "eyelash" in material.lower()
                        for material in materials
                    )
                if mesh and component_name.lower() not in ("body", "face"):
                    wardrobe_mesh_count += 1
            groom_components = []
            populated_groom_names = set()
            for component in assembled_actor.get_components_by_class(
                unreal.GroomComponent
            ):
                asset = component.get_editor_property("groom_asset")
                component_name = component.get_name()
                groom_components.append(
                    {
                        "component": component_name,
                        "asset": asset.get_path_name() if asset else None,
                        "lod_diagnostic": describe_groom_lods(asset) if asset else None,
                        "use_cards": bool(
                            component.get_editor_property("use_cards")
                        ),
                        "visible": bool(component.is_visible()),
                    }
                )
                if asset:
                    populated_groom_names.add(component_name.lower())
            runtime_hair_forced_lod = visual_actor.get_assembled_hair_forced_lod()
            runtime_hair_uses_cards = any(
                component["component"].lower() == "hair"
                and component["use_cards"]
                for component in groom_components
            )
            required_grooms = {"hair", "eyebrows"}
            missing_grooms = sorted(required_grooms - populated_groom_names)
            has_eyelash_representation = (
                "eyelashes" in populated_groom_names
                or has_face_eyelash_material
            )
            if (
                wardrobe_mesh_count < 1
                or missing_grooms
                or not has_eyelash_representation
                or not runtime_hair_uses_cards
                or runtime_hair_forced_lod != 5
            ):
                report["failed_presentation_diagnostic"] = {
                    "name": character_name,
                    "skeletal_components": skeletal_components,
                    "wardrobe_mesh_count": wardrobe_mesh_count,
                    "groom_components": groom_components,
                    "missing_populated_grooms": missing_grooms,
                    "has_face_eyelash_material": has_face_eyelash_material,
                    "runtime_hair_uses_cards": runtime_hair_uses_cards,
                    "runtime_hair_forced_lod": runtime_hair_forced_lod,
                }
                write_report(report)
                raise RuntimeError(
                    f"Incomplete assembled presentation for {character_name}: "
                    f"wardrobe_mesh_count={wardrobe_mesh_count}, "
                    f"missing_grooms={missing_grooms}"
                )
            origin, extent = actor.get_actor_bounds(False, False)
            if not finite_vector(origin) or not finite_vector(extent) or extent.z < 45.0:
                raise RuntimeError(
                    f"Invalid assembled bounds for {character_name}: {origin}, {extent}"
                )
            stem = character_name.lower()
            full_location = unreal.Vector(
                origin.x + 430.0,
                origin.y,
                106.0,
            )
            capture.set_actor_location(full_location, False, False)
            capture.set_actor_rotation(
                look_at(
                    full_location,
                    unreal.Vector(origin.x, origin.y, 96.0),
                ),
                False,
            )
            capture_component.set_editor_property("fov_angle", 36.0)
            full_path = export_capture(
                world, capture_component, render_target, f"{stem}_full"
            )

            full_profile_location = unreal.Vector(
                origin.x,
                origin.y + 430.0,
                106.0,
            )
            capture.set_actor_location(full_profile_location, False, False)
            capture.set_actor_rotation(
                look_at(
                    full_profile_location,
                    unreal.Vector(origin.x, origin.y, 96.0),
                ),
                False,
            )
            full_profile_path = export_capture(
                world, capture_component, render_target, f"{stem}_full_profile"
            )

            full_rear_location = unreal.Vector(
                origin.x - 430.0,
                origin.y,
                106.0,
            )
            capture.set_actor_location(full_rear_location, False, False)
            capture.set_actor_rotation(
                look_at(
                    full_rear_location,
                    unreal.Vector(origin.x, origin.y, 96.0),
                ),
                False,
            )
            full_rear_path = export_capture(
                world, capture_component, render_target, f"{stem}_full_rear"
            )

            portrait_target = visual_actor.get_solved_head_world_location()
            portrait_location = unreal.Vector(
                origin.x + 185.0,
                origin.y,
                portrait_target.z,
            )
            capture.set_actor_location(portrait_location, False, False)
            capture.set_actor_rotation(
                look_at(portrait_location, portrait_target), False
            )
            capture_component.set_editor_property("fov_angle", 31.0)
            portrait_path = export_capture(
                world, capture_component, render_target, f"{stem}_portrait"
            )

            # The production shell is authored with its visor/brow facing +X.
            # Capture both orthogonal sides of that axis so helmet direction and
            # skull seating can be reviewed from pixels, rather than inferred
            # only from the runtime forward-vector assertion above.
            profile_location = unreal.Vector(
                origin.x,
                origin.y + 185.0,
                portrait_target.z,
            )
            capture.set_actor_location(profile_location, False, False)
            capture.set_actor_rotation(
                look_at(profile_location, portrait_target), False
            )
            profile_path = export_capture(
                world, capture_component, render_target, f"{stem}_profile"
            )

            rear_location = unreal.Vector(
                origin.x - 185.0,
                origin.y,
                portrait_target.z,
            )
            capture.set_actor_location(rear_location, False, False)
            capture.set_actor_rotation(
                look_at(rear_location, portrait_target), False
            )
            rear_path = export_capture(
                world, capture_component, render_target, f"{stem}_rear"
            )
            pfd_material_evidence = None
            if is_guide:
                # Match one close torso camera before/after saturation. The
                # swimmer transition publishes wetness immediately; returning
                # to the seated pose preserves that material state so the two
                # frames compare fabric response without a pose confound.
                pfd_target = unreal.Vector(
                    origin.x,
                    origin.y,
                    origin.z + 25.0,
                )
                pfd_location = unreal.Vector(
                    origin.x + 180.0,
                    origin.y,
                    pfd_target.z,
                )
                capture.set_actor_location(pfd_location, False, False)
                capture.set_actor_rotation(
                    look_at(pfd_location, pfd_target), False
                )
                capture_component.set_editor_property("fov_angle", 30.0)
                dry_wetness = actor.get_pfd_presentation_wetness()
                dry_pfd_path = export_capture(
                    world, capture_component, render_target, f"{stem}_pfd_dry"
                )
                actor.set_avatar_action(
                    unreal.RaftSimCrewAvatarAction.SWIMMING, 1.0
                )
                actor.set_avatar_action(
                    unreal.RaftSimCrewAvatarAction.SEATED_IDLE, 1.0
                )
                wet_wetness_before_capture = actor.get_pfd_presentation_wetness()
                if wet_wetness_before_capture < 0.82:
                    raise RuntimeError(
                        "Swimmer transition did not saturate the guide PFD: "
                        f"{wet_wetness_before_capture:.4f}"
                    )
                wet_pfd_path = export_capture(
                    world, capture_component, render_target, f"{stem}_pfd_wet"
                )
                pfd_material_evidence = {
                    "dry_presentation_wetness": dry_wetness,
                    "wet_presentation_wetness_before_capture": (
                        wet_wetness_before_capture
                    ),
                    "wet_presentation_wetness_after_capture": (
                        actor.get_pfd_presentation_wetness()
                    ),
                    "dry_capture": str(dry_pfd_path),
                    "dry_capture_sha256": sha256(dry_pfd_path),
                    "wet_capture": str(wet_pfd_path),
                    "wet_capture_sha256": sha256(wet_pfd_path),
                }
            report["characters"].append(
                {
                    "name": character_name,
                    "blueprint_class": class_path(character_name),
                    "runtime_adapter_class": RUNTIME_ADAPTER_CLASS,
                    "runtime_host_class": RUNTIME_HOST_CLASS,
                    "runtime_safety_gear": actor.has_layered_commercial_safety_gear(),
                    "runtime_production_whitewater_helmet": (
                        actor.has_production_whitewater_helmet()
                    ),
                    "runtime_production_whitewater_pfd": (
                        actor.has_production_whitewater_pfd()
                    ),
                    "runtime_live_pfd_material_response": (
                        actor.has_live_pfd_material_response()
                    ),
                    "runtime_live_splash_jacket_material_response": (
                        actor.has_live_splash_jacket_material_response()
                    ),
                    "runtime_pfd_presentation_wetness": (
                        actor.get_pfd_presentation_wetness()
                    ),
                    "runtime_production_river_boots": (
                        actor.has_production_river_boots()
                    ),
                    "runtime_fitted_upright_river_boots": (
                        actor.has_fitted_upright_production_river_boots()
                    ),
                    "runtime_paddle": actor.has_commercial_paddle_silhouette(),
                    "runtime_articulated_paddle_grip": (
                        visual_actor.has_articulated_paddle_grip_rig()
                    ),
                    "runtime_paddle_grip_anchor_error_cm": (
                        visual_actor.get_maximum_paddle_grip_anchor_error_cm()
                    ),
                    "runtime_paddle_grip_contact_error_cm": (
                        visual_actor.get_maximum_paddle_grip_contact_error_cm()
                    ),
                    "runtime_hair_uses_cards": runtime_hair_uses_cards,
                    "runtime_hair_forced_lod": runtime_hair_forced_lod,
                    "runtime_hair_mesh_fallback": (
                        visual_actor.is_using_hair_mesh_fallback()
                    ),
                    "runtime_hair_suppressed_for_helmet": (
                        visual_actor.is_hair_mesh_fallback_suppressed_for_helmet()
                    ),
                    "runtime_hair_groom_suppressed_for_helmet": (
                        visual_actor.is_assembled_hair_groom_suppressed_for_helmet()
                    ),
                    "runtime_assembled_grooms_suppressed": (
                        visual_actor.are_assembled_grooms_suppressed_for_gameplay()
                    ),
                    "runtime_wardrobe_suppressed_for_safety_gear": (
                        visual_actor.is_assembled_wardrobe_suppressed_for_safety_gear()
                    ),
                    "runtime_assembled_body_uses_wetsuit": (
                        visual_actor.is_assembled_body_using_wetsuit()
                    ),
                    "runtime_assembled_face_uses_cropped_skin": (
                        visual_actor.is_assembled_face_using_cropped_skin()
                    ),
                    "runtime_hair_head_error_cm": (
                        visual_actor.get_hair_mesh_fallback_head_error_cm()
                    ),
                    "runtime_helmet_head_error_cm": (
                        actor.get_production_helmet_head_error_cm()
                    ),
                    "runtime_helmet_forward_alignment": (
                        actor.get_production_helmet_forward_alignment()
                    ),
                    "runtime_helmet_fit_scale": (
                        actor.get_production_helmet_fit_scale()
                    ),
                    "runtime_pfd_torso_error_cm": (
                        actor.get_production_pfd_torso_error_cm()
                    ),
                    "runtime_waist_hip_silhouette": (
                        actor.has_visible_waist_hip_silhouette()
                    ),
                    "runtime_waist_hip_extent_cm": vector_values(
                        actor.get_waist_hip_extent_cm()
                    ),
                    "runtime_waist_hip_center_error_cm": (
                        actor.get_waist_hip_center_error_cm()
                    ),
                    "runtime_waist_hip_material_opaque": (
                        actor.is_waist_hip_material_opaque()
                    ),
                    "runtime_hip_thigh_bridge_minimum_extent_cm": vector_values(
                        actor.get_minimum_hip_thigh_bridge_extent_cm()
                    ),
                    "runtime_hip_thigh_bridge_coverage_error_cm": (
                        actor.get_maximum_hip_thigh_bridge_coverage_error_cm()
                    ),
                    "runtime_thigh_knee_silhouette": (
                        actor.has_continuous_thigh_knee_silhouette()
                    ),
                    "runtime_thigh_minimum_vertex_count": (
                        actor.get_minimum_thigh_mesh_vertex_count()
                    ),
                    "runtime_thigh_minimum_forward_alignment": (
                        actor.get_minimum_thigh_forward_alignment()
                    ),
                    "runtime_thigh_knee_bridge_coverage_error_cm": (
                        actor.get_maximum_thigh_knee_bridge_coverage_error_cm()
                    ),
                    "runtime_shoulder_silhouette": (
                        actor.has_visible_shoulder_silhouette()
                    ),
                    "runtime_shoulder_sleeve_minimum_extent_cm": vector_values(
                        actor.get_minimum_shoulder_sleeve_extent_cm()
                    ),
                    "runtime_shoulder_sleeve_minimum_vertex_count": (
                        actor.get_minimum_shoulder_sleeve_vertex_count()
                    ),
                    "runtime_shoulder_sleeve_anchor_error_cm": (
                        actor.get_maximum_shoulder_sleeve_anchor_error_cm()
                    ),
                    "solved_head_world_cm": vector_values(
                        visual_actor.get_solved_head_world_location()
                    ),
                    "face_reference_head_component_cm": vector_values(
                        visual_actor.get_assembled_face_reference_head_component_location()
                    ),
                    "face_pre_skinned_bounds_origin_cm": vector_values(
                        visual_actor.get_assembled_face_pre_skinned_bounds_origin()
                    ),
                    "face_pre_skinned_bounds_extent_cm": vector_values(
                        visual_actor.get_assembled_face_pre_skinned_bounds_extent()
                    ),
                    "face_crop_height_cm": (
                        visual_actor.get_assembled_face_crop_height_cm()
                    ),
                    "bounds_origin_cm": vector_values(origin),
                    "bounds_extent_cm": vector_values(extent),
                    "skeletal_components": skeletal_components,
                    "wardrobe_mesh_count": wardrobe_mesh_count,
                    "groom_components": groom_components,
                    "eyelash_representation": (
                        "populated_groom"
                        if "eyelashes" in populated_groom_names
                        else "face_material"
                    ),
                    "full_capture": str(full_path),
                    "full_capture_sha256": sha256(full_path),
                    "full_profile_capture": str(full_profile_path),
                    "full_profile_capture_sha256": sha256(full_profile_path),
                    "full_rear_capture": str(full_rear_path),
                    "full_rear_capture_sha256": sha256(full_rear_path),
                    "portrait_capture": str(portrait_path),
                    "portrait_capture_sha256": sha256(portrait_path),
                    "profile_capture": str(profile_path),
                    "profile_capture_sha256": sha256(profile_path),
                    "rear_capture": str(rear_path),
                    "rear_capture_sha256": sha256(rear_path),
                    "pfd_material_evidence": pfd_material_evidence,
                    "status": "captured",
                }
            )
            write_report(report)
            unreal.EditorLevelLibrary.destroy_actor(actor)

        report["captured_character_count"] = len(report["characters"])
        report["status"] = "capture_complete"
    except Exception as error:
        report["status"] = "error"
        report["error_type"] = type(error).__name__
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        unreal.log_error(f"RaftSim production character capture failed: {error}")
        raise
    finally:
        write_report(report)


if __name__ == "__main__":
    main()
