"""Build RaftSim's project-owned production 14-foot paddle raft in Blender.

Run with Blender, not the system Python::

    Blender --background --python unreal/Scripts/build_production_whitewater_raft.py

The mesh is authored in the same centimetre-space rest pose consumed by the
runtime D4 visual deformer.  It is presentation source art only: collision,
buoyancy, wrap, pin, flip, damage, and rescue remain native gameplay authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Rafts/ProductionPaddleRaft"
FBX_PATH = OUTPUT_ROOT / "SM_RaftSim_ProductionPaddleRaft.fbx"
BLEND_PATH = OUTPUT_ROOT / "SM_RaftSim_ProductionPaddleRaft.blend"
MANIFEST_PATH = OUTPUT_ROOT / "production_paddle_raft_manifest.json"
GENERATOR_VERSION = 2
MATERIAL_NAMES = [
    "RaftTube",
    "RaftFloor",
    "RaftRigging",
    "RaftMetal",
    "RaftRubber",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def material(
    name: str,
    color: tuple[float, float, float, float],
    roughness: float,
    metallic: float = 0.0,
) -> bpy.types.Material:
    result = bpy.data.materials.new(name)
    result.diffuse_color = color
    result.roughness = roughness
    result.metallic = metallic
    return result


def shade_smooth(obj: bpy.types.Object) -> None:
    if obj.type != "MESH":
        return
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def superellipse_path(
    segments: int = 160,
) -> list[tuple[Vector, Vector, float, float]]:
    """Return centre, tangent, radius, and end-rise samples for the tube loop."""

    half_x = 188.0
    half_y = 73.0
    exponent = 3.65
    centres: list[Vector] = []
    radii: list[float] = []
    rises: list[float] = []
    for index in range(segments):
        angle = math.tau * index / segments
        cosine = math.cos(angle)
        sine = math.sin(angle)
        x = half_x * math.copysign(abs(cosine) ** (2.0 / exponent), cosine)
        y = half_y * math.copysign(abs(sine) ** (2.0 / exponent), sine)
        end = max(0.0, min(1.0, (abs(x) / half_x - 0.58) / 0.42))
        end = end * end * (3.0 - 2.0 * end)
        radius = 27.2 - 2.0 * end
        rise = 20.5 * end * end
        centres.append(Vector((x, y, radius + rise)))
        radii.append(radius)
        rises.append(rise)

    result: list[tuple[Vector, Vector, float, float]] = []
    for index, centre in enumerate(centres):
        previous = centres[(index - 1) % segments]
        following = centres[(index + 1) % segments]
        tangent = (following - previous).normalized()
        result.append((centre, tangent, radii[index], rises[index]))
    return result


def build_outer_tube(
    tube_material: bpy.types.Material,
) -> tuple[bpy.types.Object, list[tuple[Vector, Vector, float, float]]]:
    path = superellipse_path()
    radial_segments = 28
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    up = Vector((0.0, 0.0, 1.0))

    for centre, tangent, radius, _rise in path:
        horizontal = up.cross(tangent).normalized()
        ring_up = tangent.cross(horizontal).normalized()
        for radial_index in range(radial_segments):
            angle = math.tau * radial_index / radial_segments
            direction = horizontal * math.cos(angle) + ring_up * math.sin(angle)
            # A restrained lower-chamber flattening gives a fabric-supported
            # waterline instead of the toy-perfect torus silhouette.
            lower = max(-direction.z, 0.0)
            point = centre + direction * radius
            point.z += 0.7 * lower * lower
            vertices.append(tuple(point))

    for path_index in range(len(path)):
        next_path = (path_index + 1) % len(path)
        for radial_index in range(radial_segments):
            next_radial = (radial_index + 1) % radial_segments
            a = path_index * radial_segments + radial_index
            b = next_path * radial_segments + radial_index
            c = next_path * radial_segments + next_radial
            d = path_index * radial_segments + next_radial
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("SM_RaftSim_ProductionPaddleRaft_Tube")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("ProductionOuterTube", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(tube_material)
    shade_smooth(obj)
    return obj, path


def add_uv_sphere(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    piece_material: bpy.types.Material,
    segments: int = 36,
    rings: int = 20,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        location=location,
    )
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
    piece_material: bpy.types.Material,
    bevel_resolution: int = 3,
    cyclic: bool = False,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = bevel_resolution
    curve.use_fill_caps = True
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(piece_material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    shade_smooth(obj)
    return obj


def build_floor(floor_material: bpy.types.Material) -> bpy.types.Object:
    nx = 32
    ny = 18
    half_x = 157.0
    half_y = 49.0
    top_vertices: list[tuple[float, float, float]] = []
    bottom_vertices: list[tuple[float, float, float]] = []
    for iy in range(ny + 1):
        v = iy / ny
        y = -half_y + 2.0 * half_y * v
        for ix in range(nx + 1):
            u = ix / nx
            x = -half_x + 2.0 * half_x * u
            edge_x = abs(2.0 * u - 1.0)
            edge_y = abs(2.0 * v - 1.0)
            edge_lift = 2.5 * max(edge_x**5, edge_y**5)
            dish = -2.2 * (1.0 - edge_x**2) * (1.0 - edge_y**2)
            ibeam = 1.7 * (0.5 + 0.5 * math.cos(v * math.tau * 5.0)) ** 5
            top_vertices.append((x, y, 15.5 + edge_lift + dish + ibeam))
            bottom_vertices.append((x, y, 7.0 + edge_lift * 0.35))

    vertices = top_vertices + bottom_vertices
    stride = nx + 1
    layer_size = stride * (ny + 1)
    faces: list[tuple[int, int, int, int]] = []
    for iy in range(ny):
        for ix in range(nx):
            a = iy * stride + ix
            b = a + 1
            c = a + stride + 1
            d = a + stride
            faces.append((a, d, c, b))
            faces.append(
                (
                    layer_size + a,
                    layer_size + b,
                    layer_size + c,
                    layer_size + d,
                )
            )
    for ix in range(nx):
        for y_row in (0, ny):
            a = y_row * stride + ix
            b = a + 1
            faces.append((a, b, layer_size + b, layer_size + a))
    for iy in range(ny):
        for x_col in (0, nx):
            a = iy * stride + x_col
            b = (iy + 1) * stride + x_col
            faces.append((a, layer_size + a, layer_size + b, b))

    mesh = bpy.data.meshes.new("SM_RaftSim_ProductionPaddleRaft_Floor")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("InflatedSelfBailingFloor", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(floor_material)
    shade_smooth(obj)
    bevel = obj.modifiers.new("FloorEdgeSoftening", "BEVEL")
    bevel.width = 0.45
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def add_torus(
    name: str,
    location: tuple[float, float, float],
    major_radius: float,
    minor_radius: float,
    piece_material: bpy.types.Material,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    major_segments: int = 28,
    minor_segments: int = 8,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=major_segments,
        minor_segments=minor_segments,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(piece_material)
    shade_smooth(obj)
    return obj


def add_box(
    name: str,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    piece_material: bpy.types.Material,
    bevel_width: float,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new("MoldedEdge", "BEVEL")
    bevel.width = bevel_width
    bevel.segments = 4
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    obj.data.materials.append(piece_material)
    shade_smooth(obj)
    return obj


def build_details(
    path: list[tuple[Vector, Vector, float, float]],
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    details: list[bpy.types.Object] = []

    # Two high, removable paddle thwarts follow current 14-foot outfitter
    # construction rather than reading as rigid benches.
    for index, x in enumerate((-58.0, 57.0)):
        details.append(
            add_uv_sphere(
                f"InflatableThwart_{index + 1}",
                (x, 0.0, 35.0),
                (17.0, 55.0, 15.0),
                materials["RaftTube"],
            )
        )

    # Raised perimeter grab line follows the tube rest centreline and remains
    # deformable at runtime because it is part of the same source topology.
    grab_points: list[tuple[float, float, float]] = []
    for sample_index in range(0, len(path), 5):
        centre, _tangent, radius, _rise = path[sample_index]
        outward = Vector((centre.x / 188.0, centre.y / 73.0, 0.0)).normalized()
        point = centre + outward * (radius + 1.5) + Vector((0.0, 0.0, 5.8))
        grab_points.append(tuple(point))
    details.append(
        add_curve(
            "PerimeterGrabLine",
            grab_points,
            1.2,
            materials["RaftRigging"],
            bevel_resolution=3,
            cyclic=True,
        )
    )

    # Four chamber-divider bands make the inflatable construction legible.
    for seam_index in (0, 40, 80, 120):
        centre, tangent, radius, _rise = path[seam_index]
        rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(tangent).to_euler()
        details.append(
            add_torus(
                f"MainChamberSeam_{seam_index:03d}",
                tuple(centre),
                radius + 0.18,
                0.62,
                materials["RaftRubber"],
                tuple(rotation),
                major_segments=32,
                minor_segments=6,
            )
        )

    # Side-tube armor and thwart attachment collars are separate bonded
    # rubber layers, not texture-only stripes.
    for side in (-1.0, 1.0):
        for x in (-116.0, -38.0, 38.0, 116.0):
            details.append(
                add_uv_sphere(
                    f"SideArmor_{side:+.0f}_{x:+04.0f}",
                    (x, side * 76.0, 38.0),
                    (21.0, 1.15, 7.2),
                    materials["RaftRubber"],
                    segments=24,
                    rings=12,
                )
            )
        for x in (-58.0, 57.0):
            details.append(
                add_uv_sphere(
                    f"ThwartCollar_{side:+.0f}_{x:+04.0f}",
                    (x, side * 55.5, 37.0),
                    (13.0, 2.0, 12.0),
                    materials["RaftRubber"],
                    segments=24,
                    rings=12,
                )
            )

    # Twelve 2-inch-class attachment rings with broad bonded pads.
    for side in (-1.0, 1.0):
        for ring_index, x in enumerate((-135.0, -82.0, -26.0, 30.0, 86.0, 139.0)):
            y = side * 97.5
            z = 38.0 + 3.5 * (abs(x) / 139.0) ** 3
            details.append(
                add_uv_sphere(
                    f"DRingPad_{side:+.0f}_{ring_index:02d}",
                    (x, side * 96.0, z),
                    (6.2, 1.0, 5.3),
                    materials["RaftRubber"],
                    segments=20,
                    rings=10,
                )
            )
            details.append(
                add_torus(
                    f"StainlessDRing_{side:+.0f}_{ring_index:02d}",
                    (x, y, z + 2.0),
                    3.6,
                    0.58,
                    materials["RaftMetal"],
                    (math.pi / 2.0, 0.0, 0.0),
                    major_segments=24,
                    minor_segments=8,
                )
            )

    # Four carry handles, one on each port/starboard quarter of each kicked
    # end. Each arch remains on its own side rather than crossing the center.
    for end in (-1.0, 1.0):
        for lateral in (-1.0, 1.0):
            points = [
                (end * 184.0, lateral * 54.0, 54.0),
                (end * 201.0, lateral * 47.0, 65.0),
                (end * 207.0, lateral * 37.0, 65.0),
                (end * 198.0, lateral * 28.0, 54.0),
            ]
            details.append(
                add_curve(
                    f"CarryHandle_{end:+.0f}_{lateral:+.0f}",
                    points,
                    1.55,
                    materials["RaftRubber"],
                    bevel_resolution=3,
                )
            )

    # Four protected chamber valves plus the floor pressure-relief valve.
    for side in (-1.0, 1.0):
        for x in (-88.0, 91.0):
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=24,
                radius=3.6,
                depth=3.2,
                location=(x, side * 52.0, 53.5),
            )
            valve = bpy.context.object
            valve.name = f"TubeValve_{side:+.0f}_{x:+04.0f}"
            valve.data.materials.append(materials["RaftRubber"])
            shade_smooth(valve)
            details.append(valve)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=3.9,
        depth=2.8,
        location=(-118.0, 29.0, 20.0),
    )
    floor_valve = bpy.context.object
    floor_valve.name = "FloorPressureReliefValve"
    floor_valve.data.materials.append(materials["RaftRubber"])
    shade_smooth(floor_valve)
    details.append(floor_valve)

    # Eight open drain grommets and dark recesses make the self-bailing floor
    # function visible from the guide seat.
    for x in (-112.0, -38.0, 38.0, 112.0):
        for y in (-42.5, 42.5):
            details.append(
                add_torus(
                    f"DrainGrommet_{x:+04.0f}_{y:+03.0f}",
                    (x, y, 18.2),
                    3.3,
                    0.62,
                    materials["RaftRubber"],
                    major_segments=20,
                    minor_segments=6,
                )
            )
            details.append(
                add_uv_sphere(
                    f"DrainRecess_{x:+04.0f}_{y:+03.0f}",
                    (x, y, 17.35),
                    (2.8, 2.8, 0.45),
                    materials["RaftRubber"],
                    segments=18,
                    rings=8,
                )
            )

    # Low-profile identification plate is deliberately blank and project-owned.
    details.append(
        add_box(
            "BlankSpecificationPlate",
            (-24.0, -99.0, 40.0),
            (28.0, 0.8, 8.0),
            materials["RaftRubber"],
            0.8,
        )
    )
    return details


def join_and_uv(
    primary: bpy.types.Object,
    objects: list[bpy.types.Object],
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    # Seed the active object with the exact contract order. Blender's join then
    # maps each source polygon onto these existing material datablocks.
    for name in MATERIAL_NAMES[1:]:
        primary.data.materials.append(materials[name])
    bpy.ops.object.select_all(action="DESELECT")
    for obj in [primary, *objects]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = primary
    bpy.ops.object.join()
    primary.name = "SM_RaftSim_ProductionPaddleRaft"
    primary.data.name = "SM_RaftSim_ProductionPaddleRaft"
    bpy.context.view_layer.objects.active = primary
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.008)
    bpy.ops.object.mode_set(mode="OBJECT")
    shade_smooth(primary)
    return primary


def validate(mesh_object: bpy.types.Object) -> dict[str, object]:
    slot_names = [slot.name for slot in mesh_object.data.materials]
    if slot_names != MATERIAL_NAMES:
        raise RuntimeError(f"Production raft material contract changed: {slot_names}")
    if not mesh_object.data.uv_layers:
        raise RuntimeError("Production raft has no UV channel")
    # The joined source intentionally keeps broad inflatable surfaces as quads;
    # FBX triangulation yields roughly twice this count for runtime rendering.
    if len(mesh_object.data.polygons) < 18_000:
        raise RuntimeError(
            "Production raft mesh is unexpectedly low detail: "
            f"{len(mesh_object.data.vertices)} vertices / "
            f"{len(mesh_object.data.polygons)} polygons"
        )
    coordinates = [mesh_object.matrix_world @ vertex.co for vertex in mesh_object.data.vertices]
    minimum = Vector((min(v.x for v in coordinates), min(v.y for v in coordinates), min(v.z for v in coordinates)))
    maximum = Vector((max(v.x for v in coordinates), max(v.y for v in coordinates), max(v.z for v in coordinates)))
    dimensions = maximum - minimum
    if not (420.0 <= dimensions.x <= 450.0 and 195.0 <= dimensions.y <= 220.0):
        raise RuntimeError(f"Production raft dimensions are implausible: {tuple(dimensions)}")
    return {
        "vertex_count": len(mesh_object.data.vertices),
        "polygon_count": len(mesh_object.data.polygons),
        "material_slots": slot_names,
        "uv_channel_count": len(mesh_object.data.uv_layers),
        "bounds_min_cm": [round(value, 4) for value in minimum],
        "bounds_max_cm": [round(value, 4) for value in maximum],
        "dimensions_cm": [round(value, 4) for value in dimensions],
    }


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    materials = {
        "RaftTube": material("RaftTube", (0.12, 0.018, 0.022, 1.0), 0.52),
        "RaftFloor": material("RaftFloor", (0.035, 0.038, 0.04, 1.0), 0.66),
        "RaftRigging": material("RaftRigging", (0.9, 0.37, 0.035, 1.0), 0.8),
        "RaftMetal": material("RaftMetal", (0.3, 0.34, 0.36, 1.0), 0.28, 0.82),
        "RaftRubber": material("RaftRubber", (0.018, 0.02, 0.021, 1.0), 0.77),
    }
    outer_tube, path = build_outer_tube(materials["RaftTube"])
    floor = build_floor(materials["RaftFloor"])
    details = build_details(path, materials)
    mesh_object = join_and_uv(outer_tube, [floor, *details], materials)
    audit = validate(mesh_object)

    bpy.context.view_layer.objects.active = mesh_object
    mesh_object.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)
    bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH),
        use_selection=True,
        object_types={"MESH"},
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        bake_anim=False,
        axis_forward="-Z",
        axis_up="Y",
        apply_unit_scale=True,
        use_space_transform=True,
        path_mode="AUTO",
    )

    manifest = {
        "schema": "raftsim.production_paddle_raft_source.v1",
        "generator_version": GENERATOR_VERSION,
        "ownership": "Project-owned deterministic source art; no external mesh or texture input.",
        "source_inputs": [],
        "reference_only_sources": [
            {
                "url": "https://www.nrs.com/nrs-e-140-self-bailing-raft/ppyq",
                "facts_used": "14 ft length, 7 ft width, 20 in tubes, two thwarts, four main chambers, reinforced side/floor, drain holes, valves, D-rings and handles",
                "asset_content_copied": False,
            },
            {
                "url": "https://www.aire.com/products/aire-146dd-self-bailing-raft",
                "facts_used": "14-foot-class dimensional cross-check, diminished ends, self-bailing construction, valves, handles and D-rings",
                "asset_content_copied": False,
            },
        ],
        "fbx": str(FBX_PATH.relative_to(REPO_ROOT)),
        "blend": str(BLEND_PATH.relative_to(REPO_ROOT)),
        "fbx_sha256": sha256(FBX_PATH),
        "blend_sha256": sha256(BLEND_PATH),
        "material_slots": MATERIAL_NAMES,
        "construction": {
            "nominal_length_m": 4.3,
            "nominal_width_m": 2.0,
            "nominal_side_tube_diameter_m": 0.544,
            "main_chambers": 4,
            "thwarts": 2,
            "d_rings": 12,
            "carry_handles": 4,
            "tube_valves": 4,
            "floor_pressure_relief_valves": 1,
            "self_bailing_drain_recesses": 8,
        },
        "runtime_boundary": "Collisionless deformable presentation rest mesh; D3/D4 physics, hidden hull collision, buoyancy, flip, wrap, pin, damage and rescue remain native.",
        **audit,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
