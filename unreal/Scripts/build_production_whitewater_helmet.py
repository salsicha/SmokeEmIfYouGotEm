"""Build RaftSim's project-owned production whitewater helmet in Blender.

Run with Blender, not the system Python::

    Blender --background --python unreal/Scripts/build_production_whitewater_helmet.py

The resulting FBX is deterministic source art.  Its local origin is the fitted
skull centre used by ``ARaftSimCrewAvatarActor``; Unreal can therefore swap the
visual mesh without changing animation, rescue, contact, or raft authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionHelmet"
FBX_PATH = OUTPUT_ROOT / "SM_RaftSim_WhitewaterHelmet.fbx"
MANIFEST_PATH = OUTPUT_ROOT / "production_whitewater_helmet_manifest.json"
BLEND_PATH = OUTPUT_ROOT / "SM_RaftSim_WhitewaterHelmet.blend"
GENERATOR_VERSION = 3


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
    if obj.type != "MESH":
        return
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def build_shell(shell_material: bpy.types.Material) -> bpy.types.Object:
    """Create a watertight, asymmetric, physically thick river-helmet shell."""

    rings = 32
    sides = 72
    thickness = 0.36
    outer_scale = Vector((13.4, 12.35, 14.45))
    shell_center = Vector((2.5, 0.0, 0.0))
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    # The front terminates at the brow; temples and rear extend below the skull
    # equator.  The small crown ridge and flattened rear break the generic
    # hemisphere silhouette while staying plausible for a molded ABS shell.
    for layer in range(2):
        scale = outer_scale - Vector((thickness, thickness, thickness)) * layer
        for ring in range(rings + 1):
            v = ring / rings
            for side in range(sides):
                theta = math.tau * side / sides
                facing_front = max(math.cos(theta), 0.0)
                facing_rear = max(-math.cos(theta), 0.0)
                side_bias = 1.0 - facing_front - facing_rear
                max_phi = (
                    1.72
                    - 0.24 * facing_front
                    + 0.08 * facing_rear
                    + 0.035 * side_bias
                )
                phi = max_phi * v
                radial = math.sin(phi)
                crown_ridge = 1.0 + 0.025 * math.cos(theta * 2.0) * math.sin(phi) ** 4
                x = shell_center.x + radial * math.cos(theta) * scale.x * crown_ridge
                y = radial * math.sin(theta) * scale.y
                z = math.cos(phi) * scale.z
                if facing_rear > 0.0:
                    x += 0.45 * facing_rear * math.sin(phi) ** 3
                vertices.append((x, y, z))

    stride = sides
    layer_stride = (rings + 1) * sides
    for layer in range(2):
        offset = layer * layer_stride
        for ring in range(rings):
            for side in range(sides):
                next_side = (side + 1) % sides
                a = offset + ring * stride + side
                b = offset + ring * stride + next_side
                c = offset + (ring + 1) * stride + next_side
                d = offset + (ring + 1) * stride + side
                faces.append((a, b, c, d) if layer == 0 else (d, c, b, a))

    # Close the lower edge through the real wall thickness.
    outer_last = rings * stride
    inner_last = layer_stride + rings * stride
    for side in range(sides):
        next_side = (side + 1) % sides
        faces.append(
            (
                outer_last + side,
                outer_last + next_side,
                inner_last + next_side,
                inner_last + side,
            )
        )

    mesh = bpy.data.meshes.new("SM_RaftSim_WhitewaterHelmet_Shell")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("HelmetShell", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(shell_material)
    shade_smooth(obj)
    bevel = obj.modifiers.new("MoldedEdgeSoftening", "BEVEL")
    bevel.width = 0.08
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def rounded_box(
    name: str,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new("RoundedSlot", "BEVEL")
    bevel.width = min(dimensions) * 0.46
    bevel.segments = 6
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def cut_vents(shell: bpy.types.Object) -> int:
    # Six cut-through slots expose the liner and shell thickness. Wide first-
    # pass cutters visually merged under gameplay TAA and made the crown read
    # as broken. These narrow, well-separated openings preserve substantial
    # molded bridges at 720p while remaining true holes rather than dark decals.
    vents = [
        ((0.4, -5.6, 13.3), (4.2, 0.72, 4.2), (0.0, math.radians(-7), 0.0)),
        ((1.7, -1.85, 13.8), (4.4, 0.68, 4.0), (0.0, math.radians(-3), 0.0)),
        ((1.7, 1.85, 13.8), (4.4, 0.68, 4.0), (0.0, math.radians(-3), 0.0)),
        ((0.4, 5.6, 13.3), (4.2, 0.72, 4.2), (0.0, math.radians(-7), 0.0)),
        ((-7.9, -5.6, 8.8), (3.4, 0.76, 2.4), (0.0, math.radians(34), 0.0)),
        ((-7.9, 5.6, 8.8), (3.4, 0.76, 2.4), (0.0, math.radians(34), 0.0)),
    ]
    applied = 0
    for index, (location, dimensions, rotation) in enumerate(vents):
        cutter = rounded_box(f"VentCutter_{index:02d}", location, dimensions, rotation)
        modifier = shell.modifiers.new(f"PhysicalVent_{index:02d}", "BOOLEAN")
        modifier.operation = "DIFFERENCE"
        modifier.solver = "EXACT"
        modifier.object = cutter
        bpy.context.view_layer.objects.active = shell
        try:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            applied += 1
        finally:
            bpy.data.objects.remove(cutter, do_unlink=True)
    bpy.context.view_layer.objects.active = shell
    shell.select_set(True)
    bpy.ops.object.material_slot_remove_unused()
    return applied


def add_uv_piece(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    piece_material: bpy.types.Material,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(piece_material)
    shade_smooth(obj)
    return obj


def add_curve(
    name: str,
    points: list[tuple[float, float, float]],
    radius: float,
    curve_material: bpy.types.Material,
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
    obj.data.materials.append(curve_material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    shade_smooth(obj)
    return obj


def build_details(
    liner_material: bpy.types.Material,
    webbing_material: bpy.types.Material,
    hardware_material: bpy.types.Material,
) -> list[bpy.types.Object]:
    details: list[bpy.types.Object] = []

    # Segmented EPP liner remains visible behind the cut-through crown vents,
    # but is recessed far enough that oblique game cameras read dark vent
    # cavities rather than black pads protruding through the shell.
    for lateral in (-6.2, -2.1, 2.1, 6.2):
        details.append(
            add_uv_piece(
                f"LinerPad_{lateral:+04.1f}",
                (0.0, lateral, 9.2),
                (6.4, 1.1, 1.5),
                liner_material,
            )
        )
    details.append(
        add_uv_piece(
            "OccipitalLiner",
            (-7.8, 0.0, 4.6),
            (0.75, 6.8, 4.8),
            liner_material,
        )
    )

    # A real lower gasket follows the open brow, temples, and rear perimeter.
    details.append(
        add_curve(
            "LowerEdgeGasket",
            [
                (11.0, -8.3, 1.9),
                (5.5, -11.5, -0.4),
                (-4.8, -11.8, -1.6),
                (-10.6, -7.0, -2.2),
                (-11.8, 0.0, -2.6),
                (-10.6, 7.0, -2.2),
                (-4.8, 11.8, -1.6),
                (5.5, 11.5, -0.4),
                (11.0, 8.3, 1.9),
            ],
            0.34,
            liner_material,
        )
    )

    # Four-point retention system, rear stabilizer, chin bridge, and adjustment runs.
    strap_runs = [
        [(6.4, -10.6, 1.5), (1.6, -9.0, -4.2), (0.6, -5.0, -10.2)],
        [(-7.0, -9.5, 0.0), (-3.0, -7.4, -5.8), (0.6, -5.0, -10.2)],
        [(6.4, 10.6, 1.5), (1.6, 9.0, -4.2), (0.6, 5.0, -10.2)],
        [(-7.0, 9.5, 0.0), (-3.0, 7.4, -5.8), (0.6, 5.0, -10.2)],
        [(0.6, -5.0, -10.2), (2.2, 0.0, -12.0), (0.6, 5.0, -10.2)],
        [(-10.5, -5.0, 1.6), (-12.2, 0.0, 1.0), (-10.5, 5.0, 1.6)],
    ]
    for index, points in enumerate(strap_runs):
        details.append(add_curve(f"RetentionWebbing_{index:02d}", points, 0.27, webbing_material))

    for lateral in (-1.0, 1.0):
        details.append(
            add_uv_piece(
                f"EarPad_{lateral:+.0f}",
                (-1.0, lateral * 9.8, -1.3),
                (2.6, 0.5, 3.2),
                liner_material,
            )
        )

    # Low-profile adjustment discs and six corrosion-resistant shell fasteners.
    for lateral in (-1.0, 1.0):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=32,
            radius=1.25,
            depth=0.42,
            location=(-4.0, lateral * 11.9, 1.2),
            rotation=(math.pi / 2.0, 0.0, 0.0),
        )
        adjuster = bpy.context.object
        adjuster.name = f"StrapAdjuster_{lateral:+.0f}"
        adjuster.data.materials.append(hardware_material)
        shade_smooth(adjuster)
        details.append(adjuster)

    for index, (x, y, z) in enumerate(
        [(-7.4, -10.0, 2.7), (-7.4, 10.0, 2.7), (6.8, -10.0, 4.1),
         (6.8, 10.0, 4.1), (-10.4, -5.4, 5.0), (-10.4, 5.4, 5.0)]
    ):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=0.48, location=(x, y, z))
        fastener = bpy.context.object
        fastener.name = f"ShellFastener_{index:02d}"
        fastener.data.materials.append(hardware_material)
        shade_smooth(fastener)
        details.append(fastener)

    buckle = rounded_box("ChinBuckle", (2.3, 0.0, -11.9), (2.2, 1.35, 1.0))
    buckle.data.materials.append(hardware_material)
    details.append(buckle)
    return details


def join_for_export(objects: list[bpy.types.Object]) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    result = bpy.context.object
    result.name = "SM_RaftSim_WhitewaterHelmet"
    # Stable slot order is a runtime contract: shell, liner, webbing, hardware.
    expected = ["HelmetShell", "HelmetLiner", "HelmetWebbing", "HelmetHardware"]
    actual = [slot.name for slot in result.data.materials]
    if actual != expected:
        raise RuntimeError(f"Unexpected material slot order: {actual}")
    return result


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    shell_material = material("HelmetShell", (0.06, 0.18, 0.31, 1.0), 0.38)
    liner_material = material("HelmetLiner", (0.012, 0.015, 0.018, 1.0), 0.78)
    webbing_material = material("HelmetWebbing", (0.018, 0.021, 0.024, 1.0), 0.86)
    hardware_material = material("HelmetHardware", (0.08, 0.09, 0.10, 1.0), 0.54)

    shell = build_shell(shell_material)
    vent_count = cut_vents(shell)
    details = build_details(liner_material, webbing_material, hardware_material)
    helmet = join_for_export([shell, *details])
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 0.01
    bpy.context.scene.unit_settings.length_unit = "CENTIMETERS"

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), compress=True)
    bpy.ops.object.select_all(action="DESELECT")
    helmet.select_set(True)
    bpy.context.view_layer.objects.active = helmet
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

    bounds = [Vector(helmet.bound_box[index]) for index in range(8)]
    minimum = Vector((min(p.x for p in bounds), min(p.y for p in bounds), min(p.z for p in bounds)))
    maximum = Vector((max(p.x for p in bounds), max(p.y for p in bounds), max(p.z for p in bounds)))
    manifest = {
        "schema_version": 1,
        "generator": "unreal/Scripts/build_production_whitewater_helmet.py",
        "generator_version": GENERATOR_VERSION,
        "ownership": "Project-owned deterministic source art; no external mesh or texture input.",
        "license": "RaftSim project source license",
        "source_inputs": [],
        "fbx": str(FBX_PATH.relative_to(REPO_ROOT)),
        "fbx_sha256": hashlib.sha256(FBX_PATH.read_bytes()).hexdigest(),
        "blend": str(BLEND_PATH.relative_to(REPO_ROOT)),
        "blend_sha256": hashlib.sha256(BLEND_PATH.read_bytes()).hexdigest(),
        "object_name": helmet.name,
        "material_slots": [slot.name for slot in helmet.data.materials],
        "physical_cut_through_vents": vent_count,
        "retention_anchor_count": 4,
        "vertex_count": len(helmet.data.vertices),
        "polygon_count": len(helmet.data.polygons),
        "bounds_cm": {
            "min": [round(value, 4) for value in minimum],
            "max": [round(value, 4) for value in maximum],
        },
        "runtime_boundary": "Visual-only headgear; D3/D4 physics and rescue authority remain native.",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("RAFTSIM_PRODUCTION_HELMET=" + json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
