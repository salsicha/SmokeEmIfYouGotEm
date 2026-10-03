"""Render the river wildlife models (docs/river-wildlife-reference.md).

Spawns every species with ARaftSimWildlifeCreature.configure_for_review in a
lineup over a flat waterline, and photographs each one close up, plus the
flyers from below as a rafter sees them. Run in the editor (UnrealEditor
-ExecutePythonScript=... -RenderOffscreen) with RAFTSIM_WILDLIFE_REVIEW_OUTPUT
naming a fresh directory. Nothing is saved.
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
output = Path(os.environ["RAFTSIM_WILDLIFE_REVIEW_OUTPUT"])
output.mkdir(parents=True, exist_ok=False)
helpers.OUTPUT_ROOT = output
world = unreal.EditorLevelLibrary.get_editor_world()

water = helpers.spawn(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
water.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane"))
water.static_mesh_component.set_material(0, unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial"))
water.set_actor_scale3d(unreal.Vector(400, 400, 1))
water.static_mesh_component.create_dynamic_material_instance(0).set_vector_parameter_value(
    "Color", unreal.LinearColor(0.05, 0.10, 0.12, 1))
for eye in (unreal.Vector(400, 600, 900), unreal.Vector(-500, -600, 600), unreal.Vector(800, -200, 500)):
    helpers.configure_rect_light(eye, unreal.Vector(0, 0, 50), 220, 600, 600, unreal.Color(245, 241, 235, 255))

species = unreal.RaftSimWildlifeSpecies
CLASS = unreal.load_class(None, "/Script/SmokeEmIfYouGotEm.RaftSimWildlifeCreature")
# (species, ground height cm (0 = waterline), framing distance cm, from below)
LINEUP = [
    ("BALD_EAGLE", 300, 420, True), ("OSPREY", 300, 360, True), ("TURKEY_VULTURE", 300, 380, True),
    ("CALIFORNIA_CONDOR", 300, 560, True), ("ANDEAN_CONDOR", 300, 580, True),
    ("AFRICAN_FISH_EAGLE", 300, 420, True), ("VERREAUXS_EAGLE", 300, 420, True),
    ("COMMON_RAVEN", 300, 300, True), ("AUSTRAL_PARAKEET", 300, 150, True), ("TRUMPETER_HORNBILL", 300, 260, True),
    ("GREAT_BLUE_HERON", 0, 320, False), ("COMMON_MERGANSER", 0, 160, False), ("TORRENT_DUCK", 0, 140, False),
    ("HARLEQUIN_DUCK", 0, 140, False), ("MANTLED_HOWLER", 200, 230, False), ("KEEL_BILLED_TOUCAN", 200, 160, False),
    ("MONTEZUMA_OROPENDOLA", 200, 160, False), ("DESERT_BIGHORN", 0, 420, False), ("BLACK_TAILED_DEER", 0, 420, False),
    ("GRIZZLY_BEAR", 0, 520, False), ("CHACMA_BABOON", 0, 260, False), ("HIPPOPOTAMUS", 0, 650, False),
    ("NILE_CROCODILE", 0, 300, False), ("SOCKEYE_SALMON", 80, 150, False),
    ("SUNBITTERN", 0, 180, False), ("FASCIATED_TIGER_HERON", 0, 230, False), ("SOUTHERN_LAPWING", 0, 150, False),
    ("BLACK_FACED_IBIS", 300, 300, True), ("ROCK_PRATINCOLE", 0, 90, False),
]
capture = helpers.spawn(unreal.SceneCapture2D, unreal.Vector())
component = capture.capture_component2d
component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
component.set_editor_property("capture_every_frame", False)
component.set_editor_property("capture_on_movement", False)
target = unreal.RenderingLibrary.create_render_target2d(
    world, 960, 720, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0.03, 0.03, 0.03, 1), False)
component.set_editor_property("texture_target", target)
for command in ("r.EyeAdaptationQuality 0", "r.TextureStreaming 0", "r.Nanite 0"):
    unreal.SystemLibrary.execute_console_command(world, command)

report = {"schema": "raftsim.river_wildlife_review.v1", "images": []}
for index, (name, height, distance, from_below) in enumerate(LINEUP):
    # Each animal in its own spot, far enough apart to frame alone.
    origin = unreal.Vector((index % 6) * 2500.0, (index // 6) * 2500.0, 0.0)
    home = unreal.Vector(origin.x, origin.y, float(height))
    creature = helpers.spawn(CLASS, home)
    creature.configure_for_review(getattr(species, name), home, 0.0, 1.3)
    aim = unreal.Vector(home.x, home.y, home.z + (0 if from_below else distance * 0.12))
    views = [("three_quarter", unreal.Vector(home.x + distance * 0.75, home.y - distance * 0.65, home.z + distance * 0.35))]
    if from_below:
        views.append(("below", unreal.Vector(home.x - distance * 0.2, home.y - distance * 0.3, home.z - distance * 0.9)))
    else:
        views.append(("side", unreal.Vector(home.x, home.y - distance, home.z + distance * 0.15)))
    for view, eye in views:
        capture.set_actor_location(eye, False, False)
        capture.set_actor_rotation(helpers.look_at(eye, aim), False)
        component.set_editor_property("fov_angle", 50)
        report["images"].append(str(helpers.export_capture(world, component, target, f"{name.lower()}_{view}")))
(output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("River wildlife review complete: " + str(output))
