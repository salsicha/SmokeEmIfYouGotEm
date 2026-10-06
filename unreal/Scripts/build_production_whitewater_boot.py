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
GENERATOR_VERSION = 6


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


def add_curve(
    name: str,
    points: list[tuple[float, float, float]],
    radius: float,
    assigned_material: bpy.types.Material,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 3
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(assigned_material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    shade_smooth(obj)
    return obj


def build_lasted_volume(
    name: str,
    assigned_material: bpy.types.Material,
    x_min: float,
    x_max: float,
    center_z: float,
    half_width: float,
    half_height: float,
    section_count: int,
    side_count: int,
) -> bpy.types.Object:
    """Build a rounded heel-to-toe volume with an anatomical plan outline."""

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for section in range(section_count + 1):
        t = section / section_count
        x = x_min + (x_max - x_min) * t
        if t < 0.18:
            end_round = math.sqrt(max(1.0 - ((0.18 - t) / 0.18) ** 2, 0.0))
        elif t > 0.70:
            end_round = math.sqrt(max(1.0 - ((t - 0.70) / 0.30) ** 2, 0.0))
        else:
            end_round = 1.0
        width = half_width * (0.18 + 0.82 * end_round)
        height = half_height * (0.42 + 0.58 * end_round)
        arch = 0.16 * math.sin(math.pi * t)
        for side in range(side_count):
            angle = math.tau * side / side_count
            vertices.append(
                (
                    x,
                    width * math.cos(angle),
                    center_z + arch + height * math.sin(angle),
                )
            )
    for section in range(section_count):
        for side in range(side_count):
            next_side = (side + 1) % side_count
            a = section * side_count + side
            b = section * side_count + next_side
            c = (section + 1) * side_count + next_side
            d = (section + 1) * side_count + side
            faces.append((a, b, c, d))
    faces.append(tuple(reversed(tuple(range(side_count)))))
    faces.append(
        tuple(section_count * side_count + side for side in range(side_count))
    )
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(assigned_material)
    shade_smooth(obj)
    return obj


def foot_section(t: float) -> tuple[float, float, float]:
    """Shared shoe last for the upper, toe reinforcement and stitched bands."""
    toe_taper = max((t - 0.74) / 0.26, 0.0)
    toe_round = math.sqrt(max(1.0 - toe_taper * toe_taper, 0.0))
    heel_round = 0.62 + 0.38 * math.sqrt(
        max(1.0 - (max(0.12 - t, 0.0) / 0.12) ** 2, 0.0))
    width = (5.15 + 1.45 * math.sin(math.pi * min(t / 0.88, 1.0)))
    width *= heel_round * (0.30 + 0.70 * toe_round)
    bottom = -2.75 + 0.70 * toe_taper * toe_taper
    top = 4.05 + 3.55 * math.exp(-((t - 0.34) / 0.24) ** 2)
    top += -0.55 * t + 0.45 * (1.0 - toe_round)
    return width, bottom, top


def build_foot_shell(upper: bpy.types.Material) -> bpy.types.Object:
    sections = 36
    sides = 48
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for section in range(sections + 1):
        t = section / sections
        x = -5.0 + 29.0 * t
        # V5 uses an actual shoe last rather than a constant rounded tube. The
        # heel is narrow, the ball is broad, the toe stays full until its final
        # quarter, and the upper has a raised instep followed by a low toe box.
        half_width, bottom_z, top_z = foot_section(t)
        center_z = 0.5 * (bottom_z + top_z)
        half_height = 0.5 * (top_z - bottom_z)
        for side in range(sides):
            angle = math.tau * side / sides
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            # A lightly pinched crown and flatter lower quarter distinguish
            # the fabric upper from both the ankle and the rubber outsole.
            exponent = 1.18 if sin_a >= 0.0 else 0.82
            y = half_width * math.copysign(abs(cos_a) ** 1.08, cos_a)
            z = center_z + half_height * math.copysign(abs(sin_a) ** exponent, sin_a)
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
        for side in range(sides):
            angle = math.tau * side / sides
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            # Low front collar, higher heel counter, oval ankle opening. The
            # previous constant-height circular cap was the cylinder visible
            # in the chase camera. This collar is open so the shin enters it.
            top_z = 8.45 - 1.35 * cos_a
            z = 3.45 + (top_z - 3.45) * t
            radius_scale = 1.0 - 0.17 * t
            center_x = -2.45 - 0.20 * t
            x = center_x + cos_a * 4.45 * radius_scale
            y = sin_a * 5.25 * radius_scale
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
    # Deliberately no top face: the collar is a real opening, not a solid cap.
    mesh = bpy.data.meshes.new("SM_RaftSim_WhitewaterRiverBoot_Cuff")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("BootCuff", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(upper)
    shade_smooth(obj)
    # Thin neoprene wall makes the open cuff readable from inside as well.
    wall = obj.modifiers.new("NeopreneCuffWall", "SOLIDIFY")
    wall.thickness = 0.18
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=wall.name)
    return obj


def build_details(
    upper: bpy.types.Material,
    sole: bpy.types.Material,
    reinforcement: bpy.types.Material,
) -> tuple[list[bpy.types.Object], dict[str, int]]:
    details: list[bpy.types.Object] = []
    # V4 removes the three large beveled cubes that dominated the gameplay
    # silhouette. The outsole now follows a rounded lasted footprint, while
    # toe and heel protection are curved overlays matching the upper.
    details.append(
        build_lasted_volume(
            "Outsole", sole, -6.6, 24.8, -3.95, 6.45, 1.15, 42, 36
        )
    )
    details.append(
        build_lasted_volume(
            "ToeRand", reinforcement, 17.2, 24.5, -0.05, 5.45, 3.35, 22, 36
        )
    )
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=40,
        ring_count=24,
        location=(-5.55, 0.0, 1.45),
        scale=(1.35, 5.15, 3.65),
    )
    heel_rand = bpy.context.object
    heel_rand.name = "HeelRand"
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    heel_rand.data.materials.append(reinforcement)
    shade_smooth(heel_rand)
    details.append(heel_rand)
    details.append(rounded_box("PullTab", (-6.1, 0.0, 7.7), (0.9, 1.8, 3.5), 0.40, reinforcement))

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
        major_radius=5.35,
        minor_radius=0.26,
        major_segments=48,
        minor_segments=8,
        location=(-2.45, 0.0, 5.15),
    )
    ankle_seam = bpy.context.object
    ankle_seam.name = "AnkleSeamBand"
    ankle_seam.scale.x = 0.78
    ankle_seam.scale.y = 0.96
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ankle_seam.data.materials.append(reinforcement)
    shade_smooth(ankle_seam)
    details.append(ankle_seam)

    for index, x in enumerate((4.0, 9.0, 14.0)):
        width, bottom, top = foot_section((x + 5.0) / 29.0)
        center = (bottom + top) * 0.5
        height = (top - bottom) * 0.5
        # Stitch the band to the actual last. Former fixed heights alternated
        # between disappearing inside the instep and floating over the toe.
        points = []
        for sample in range(17):
            angle = math.pi * (0.06 + 0.88 * sample / 16)
            cosine, sine = math.cos(angle), math.sin(angle)
            y = (width + 0.08) * math.copysign(abs(cosine) ** 1.08, cosine)
            z = center + height * sine ** 1.18 + 0.10
            points.append((x, y, z))
        band = add_curve(
            f"VampDrainBand_{index:02d}",
            points,
            0.13,
            reinforcement,
        )
        details.append(band)
    return details, {
        "outsole_lugs": lug_count,
        "vamp_drain_bands": 3,
        "pull_tabs": 1,
        "curved_lasted_outsole": True,
        "curved_toe_and_heel_rands": True,
    }


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
