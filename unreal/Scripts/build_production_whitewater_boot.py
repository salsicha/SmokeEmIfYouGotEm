"""Build RaftSim's project-owned production whitewater river boot in Blender.

Run with Blender, not the system Python::

    Blender --background --python unreal/Scripts/build_production_whitewater_boot.py

The source mesh is centred at the solved ankle/foot point used by
``ARaftSimCrewAvatarActor``. It is presentation-only and does not participate
in collision, crew mass, raft contact, rescue, or hydraulic authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionRiverBoot"
FBX_PATH = OUTPUT_ROOT / "SM_RaftSim_WhitewaterRiverBoot.fbx"
BLEND_PATH = OUTPUT_ROOT / "SM_RaftSim_WhitewaterRiverBoot.blend"
MANIFEST_PATH = OUTPUT_ROOT / "production_whitewater_river_boot_manifest.json"
GENERATOR_VERSION = 1


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def material(name: str, color: tuple[float, float, float, float], roughness: float):
    result = bpy.data.materials.new(name)
    result.diffuse_color = color
    result.roughness = roughness
    result.metallic = 0.0
    return result


def shade_smooth(obj: bpy.types.Object) -> None:
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def rounded_box(
    name: str,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    bevel_width: float,
    assigned_material: bpy.types.Material,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new(f"{name}_MoldedRadius", "BEVEL")
    bevel.width = bevel_width
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    obj.data.materials.append(assigned_material)
    shade_smooth(obj)
    return obj


def build_foot_shell(upper: bpy.types.Material) -> bpy.types.Object:
    sections = 36
    sides = 48
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for section in range(sections + 1):
        t = section / sections
        x = -5.0 + 29.0 * t
        toe_taper = max((t - 0.70) / 0.30, 0.0)
        heel_taper = max((0.12 - t) / 0.12, 0.0)
        half_width = 5.65 + 0.90 * math.sin(math.pi * t) - 1.45 * toe_taper
        half_width -= 0.45 * heel_taper
        half_height = 4.9 - 0.85 * t + 0.55 * math.sin(math.pi * t)
        center_z = 1.25 + 0.85 * t
        for side in range(sides):
            angle = math.tau * side / sides
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            # A softened superellipse reads as a lasted boot rather than a
            # scaled sphere while retaining smooth deterministic topology.
            y = half_width * math.copysign(abs(cos_a) ** 0.82, cos_a)
            z = center_z + half_height * math.copysign(abs(sin_a) ** 0.72, sin_a)
            vertices.append((x, y, z))
    for section in range(sections):
        for side in range(sides):
            next_side = (side + 1) % sides
            a = section * sides + side
            b = section * sides + next_side
            c = (section + 1) * sides + next_side
            d = (section + 1) * sides + side
            faces.append((a, b, c, d))
    faces.append(tuple(reversed(tuple(range(sides)))))
    front = tuple(sections * sides + side for side in range(sides))
    faces.append(front)
    mesh = bpy.data.meshes.new("SM_RaftSim_WhitewaterRiverBoot_Upper")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("BootUpper", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(upper)
    shade_smooth(obj)
    return obj


def build_cuff(upper: bpy.types.Material) -> bpy.types.Object:
    rings = 18
    sides = 48
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for ring in range(rings + 1):
        t = ring / rings
        z = 3.2 + 14.8 * t
        radius_scale = 1.0 - 0.10 * t + 0.025 * math.sin(math.pi * t)
        center_x = -2.15 - 0.35 * t
        for side in range(sides):
            angle = math.tau * side / sides
            x = center_x + math.cos(angle) * 5.65 * radius_scale
            y = math.sin(angle) * 6.20 * radius_scale
            vertices.append((x, y, z))
    for ring in range(rings):
        for side in range(sides):
            next_side = (side + 1) % sides
            a = ring * sides + side
            b = ring * sides + next_side
            c = (ring + 1) * sides + next_side
            d = (ring + 1) * sides + side
            faces.append((a, b, c, d))
    faces.append(tuple(reversed(tuple(range(sides)))))
    top = tuple(rings * sides + side for side in range(sides))
    faces.append(top)
    mesh = bpy.data.meshes.new("SM_RaftSim_WhitewaterRiverBoot_Cuff")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("BootCuff", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(upper)
    shade_smooth(obj)
    return obj


def build_details(
    upper: bpy.types.Material,
    sole: bpy.types.Material,
    reinforcement: bpy.types.Material,
) -> tuple[list[bpy.types.Object], dict[str, int]]:
    details: list[bpy.types.Object] = []
    details.append(rounded_box("Outsole", (9.25, 0.0, -3.55), (31.5, 13.5, 2.3), 0.85, sole))
    details.append(rounded_box("ToeRand", (19.6, 0.0, 0.15), (7.4, 12.0, 5.9), 2.2, reinforcement))
    details.append(rounded_box("HeelRand", (-5.55, 0.0, 2.4), (2.4, 11.7, 8.5), 0.9, reinforcement))
    details.append(rounded_box("PullTab", (-7.25, 0.0, 13.1), (1.0, 2.1, 7.4), 0.45, reinforcement))

    lug_count = 0
    for x in (-1.0, 5.5, 12.0, 18.5):
        for y in (-3.8, 0.0, 3.8):
            width = 2.3 if y == 0.0 else 2.7
            details.append(
                rounded_box(
                    f"OutsoleLug_{lug_count:02d}",
                    (x, y, -5.0),
                    (4.1, width, 1.15),
                    0.28,
                    sole,
                )
            )
            lug_count += 1

    # Molded ankle and vamp seam bands break the single-volume silhouette.
    bpy.ops.mesh.primitive_torus_add(
        major_radius=5.75,
        minor_radius=0.24,
        major_segments=48,
        minor_segments=8,
        location=(-2.35, 0.0, 13.9),
    )
    ankle_seam = bpy.context.object
    ankle_seam.name = "AnkleSeamBand"
    ankle_seam.scale.y = 1.08
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ankle_seam.data.materials.append(reinforcement)
    shade_smooth(ankle_seam)
    details.append(ankle_seam)

    for index, x in enumerate((4.0, 9.0, 14.0)):
        band = rounded_box(
            f"VampDrainBand_{index:02d}",
            (x, 0.0, 5.0 - index * 0.25),
            (0.55, 11.5 - index * 0.55, 1.15),
            0.25,
            reinforcement,
        )
        details.append(band)
    return details, {"outsole_lugs": lug_count, "vamp_drain_bands": 3, "pull_tabs": 1}


def join_for_export(objects: list[bpy.types.Object]) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    result = bpy.context.object
    result.name = "SM_RaftSim_WhitewaterRiverBoot"
    expected = ["BootUpper", "BootSole", "BootReinforcement"]
    actual = [slot.name for slot in result.data.materials]
    if actual != expected:
        raise RuntimeError(f"Unexpected material slot order: {actual}")
    return result


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    upper = material("BootUpper", (0.010, 0.015, 0.020, 1.0), 0.72)
    sole = material("BootSole", (0.004, 0.006, 0.008, 1.0), 0.86)
    reinforcement = material("BootReinforcement", (0.018, 0.023, 0.028, 1.0), 0.64)
    foot = build_foot_shell(upper)
    cuff = build_cuff(upper)
    details, construction = build_details(upper, sole, reinforcement)
    boot = join_for_export([foot, cuff, *details])

    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 0.01
    bpy.context.scene.unit_settings.length_unit = "CENTIMETERS"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), compress=True)
    bpy.ops.object.select_all(action="DESELECT")
    boot.select_set(True)
    bpy.context.view_layer.objects.active = boot
    bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH),
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="X",
        axis_up="Z",
        bake_space_transform=False,
        object_types={"MESH"},
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        path_mode="AUTO",
    )

    bounds = [Vector(boot.bound_box[index]) for index in range(8)]
    minimum = Vector((min(p.x for p in bounds), min(p.y for p in bounds), min(p.z for p in bounds)))
    maximum = Vector((max(p.x for p in bounds), max(p.y for p in bounds), max(p.z for p in bounds)))
    manifest = {
        "schema_version": 1,
        "generator": "unreal/Scripts/build_production_whitewater_boot.py",
        "generator_version": GENERATOR_VERSION,
        "ownership": "Project-owned deterministic source art; no external mesh or texture input.",
        "license": "RaftSim project source license",
        "source_inputs": [],
        "fbx": str(FBX_PATH.relative_to(REPO_ROOT)),
        "fbx_sha256": hashlib.sha256(FBX_PATH.read_bytes()).hexdigest(),
        "blend": str(BLEND_PATH.relative_to(REPO_ROOT)),
        "blend_sha256": hashlib.sha256(BLEND_PATH.read_bytes()).hexdigest(),
        "object_name": boot.name,
        "material_slots": [slot.name for slot in boot.data.materials],
        "vertex_count": len(boot.data.vertices),
        "polygon_count": len(boot.data.polygons),
        "bounds_cm": {
            "min": [round(value, 4) for value in minimum],
            "max": [round(value, 4) for value in maximum],
        },
        "construction": construction,
        "runtime_boundary": "Visual-only river footwear; crew pose, mass, D3/D4 physics, collision and rescue authority remain native.",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("RAFTSIM_PRODUCTION_RIVER_BOOT=" + json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
