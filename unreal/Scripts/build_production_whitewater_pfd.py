"""Build RaftSim's project-owned high-profile whitewater rescue PFD.

The local origin is the deterministic torso centre used by
``ARaftSimCrewAvatarActor``. No commercial mesh, texture, branding, or product
image is copied; current manufacturer pages are dimensional/construction
references only.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionPfd"
FBX_PATH = OUTPUT_ROOT / "SM_RaftSim_WhitewaterRescuePfd.fbx"
BLEND_PATH = OUTPUT_ROOT / "SM_RaftSim_WhitewaterRescuePfd.blend"
MANIFEST_PATH = OUTPUT_ROOT / "production_whitewater_pfd_manifest.json"
GENERATOR_VERSION = 12
MATERIAL_NAMES = [
    "PfdShell",
    "PfdWebbing",
    "PfdHardware",
    "PfdReflective",
    "PfdLabel",
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
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def add_uv_piece(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    piece_material: bpy.types.Material,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    segments: int = 40,
    rings: int = 24,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(piece_material)
    shade_smooth(obj)
    return obj


def add_rounded_box(
    name: str,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    piece_material: bpy.types.Material,
    bevel_width: float,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new("SoftGoodsEdge", "BEVEL")
    bevel.width = bevel_width
    bevel.segments = 6
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    obj.data.materials.append(piece_material)
    shade_smooth(obj)
    return obj


def add_extruded_panel(
    name: str,
    x_center: float,
    thickness: float,
    outline_yz: list[tuple[float, float]],
    piece_material: bpy.types.Material,
    bevel_width: float,
) -> bpy.types.Object:
    """Create a flat, softly edged foam panel from an authored Y/Z outline."""
    half_depth = thickness * 0.5
    vertices = [(x_center + half_depth, y, z) for y, z in outline_yz] + [
        (x_center - half_depth, y, z) for y, z in outline_yz
    ]
    count = len(outline_yz)
    faces: list[tuple[int, ...]] = [
        tuple(range(count)),
        tuple(reversed(range(count, count * 2))),
    ]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index, next_index, count + next_index, count + index))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(piece_material)
    bevel = obj.modifiers.new("SoftFoamEdge", "BEVEL")
    bevel.width = bevel_width
    bevel.segments = 8
    bevel.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    shade_smooth(obj)
    return obj


def rounded_outline(
    outline_yz: list[tuple[float, float]],
    iterations: int = 4,
) -> list[tuple[float, float]]:
    """Round every closed-outline corner without changing its authored silhouette."""
    result = list(outline_yz)
    for _ in range(iterations):
        softened: list[tuple[float, float]] = []
        for index, current in enumerate(result):
            following = result[(index + 1) % len(result)]
            softened.extend(
                [
                    (
                        current[0] * 0.75 + following[0] * 0.25,
                        current[1] * 0.75 + following[1] * 0.25,
                    ),
                    (
                        current[0] * 0.25 + following[0] * 0.75,
                        current[1] * 0.25 + following[1] * 0.75,
                    ),
                ]
            )
        result = softened
    return result


def add_crowned_foam_panel(
    name: str,
    x_center: float,
    thickness: float,
    outline_yz: list[tuple[float, float]],
    piece_material: bpy.types.Material,
    edge_roll: float,
    crown_depth: float,
    outward_sign: float = 1.0,
    depth_axis: str = "x",
    lateral_wrap_depth: float = 0.0,
) -> bpy.types.Object:
    """Loft a fabric-covered foam cell with rounded corners and a soft crown.

    The prior bevel-only construction left a large planar exterior face. These
    nested perimeter rings roll the shell over the foam edge and progressively
    crown the visible face, so specular response reads as compliant padding
    instead of a hard plate.
    """
    outline = rounded_outline(outline_yz)
    centroid_y = sum(point[0] for point in outline) / len(outline)
    centroid_z = sum(point[1] for point in outline) / len(outline)

    def scaled_outline(scale: float) -> list[tuple[float, float]]:
        return [
            (
                centroid_y + (y - centroid_y) * scale,
                centroid_z + (z - centroid_z) * scale,
            )
            for y, z in outline
        ]

    half_depth = thickness * 0.5
    # Depth is expressed from the torso-facing surface toward the visible shell.
    # Closely spaced inset rings approximate a cosine loft: the face stays broad
    # enough to read as flotation foam but rolls continuously into its seam
    # instead of converging through a few visibly faceted triangles.
    ring_profiles = [
        (-half_depth, 0.90),
        (-half_depth + edge_roll * 0.58, 0.975),
        (-half_depth + edge_roll, 1.0),
        (half_depth - edge_roll * 0.78, 1.0),
        (half_depth - edge_roll * 0.30, 0.992),
        (half_depth, 0.965),
        (half_depth + crown_depth * 0.24, 0.93),
        (half_depth + crown_depth * 0.48, 0.84),
        (half_depth + crown_depth * 0.69, 0.70),
        (half_depth + crown_depth * 0.85, 0.52),
        (half_depth + crown_depth * 0.96, 0.30),
    ]
    maximum_lateral_radius = max(abs(point[0] - centroid_y) for point in outline)

    def coordinate(
        signed_depth: float,
        outline_a: float,
        outline_b: float,
    ) -> tuple[float, float, float]:
        depth = x_center + outward_sign * signed_depth
        # Back and chest cells must follow a torso arc rather than remain
        # broad planar plates. The quadratic falloff preserves the authored
        # centre crown while bringing each lateral edge toward the flank.
        lateral_alpha = min(
            abs(outline_a - centroid_y) / maximum_lateral_radius,
            1.0,
        )
        wrapped_depth = depth + lateral_wrap_depth * lateral_alpha**2
        if depth_axis == "x":
            return (wrapped_depth, outline_a, outline_b)
        if depth_axis == "y":
            return (outline_a, depth, outline_b)
        raise ValueError(f"Unsupported foam-panel depth axis: {depth_axis}")

    vertices: list[tuple[float, float, float]] = []
    for signed_depth, scale in ring_profiles:
        vertices.extend(
            coordinate(signed_depth, outline_a, outline_b)
            for outline_a, outline_b in scaled_outline(scale)
        )

    count = len(outline)
    faces: list[tuple[int, ...]] = []
    for ring_index in range(len(ring_profiles) - 1):
        current = ring_index * count
        following = current + count
        for index in range(count):
            next_index = (index + 1) % count
            faces.append(
                (
                    current + index,
                    current + next_index,
                    following + next_index,
                    following + index,
                )
            )

    inner_center_index = len(vertices)
    vertices.append(coordinate(-half_depth, centroid_y, centroid_z))
    outer_center_index = len(vertices)
    vertices.append(coordinate(half_depth + crown_depth, centroid_y, centroid_z))
    final_ring = (len(ring_profiles) - 1) * count
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((inner_center_index, next_index, index))
        faces.append(
            (
                outer_center_index,
                final_ring + index,
                final_ring + next_index,
            )
        )

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(piece_material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    shade_smooth(obj)
    return obj


def add_flat_webbing_run(
    name: str,
    path_xz: list[tuple[float, float]],
    y_center: float,
    width: float,
    thickness: float,
    piece_material: bpy.types.Material,
) -> bpy.types.Object:
    """Sweep a thin rectangular strap across a shoulder without foam volume."""
    half_width = width * 0.5
    half_thickness = thickness * 0.5
    vertices: list[tuple[float, float, float]] = []
    for x, z in path_xz:
        vertices.extend(
            [
                (x, y_center - half_width, z - half_thickness),
                (x, y_center + half_width, z - half_thickness),
                (x, y_center + half_width, z + half_thickness),
                (x, y_center - half_width, z + half_thickness),
            ]
        )
    faces: list[tuple[int, ...]] = [(3, 2, 1, 0)]
    for section in range(len(path_xz) - 1):
        start = section * 4
        following = start + 4
        faces.extend(
            [
                (start, start + 1, following + 1, following),
                (start + 1, start + 2, following + 2, following + 1),
                (start + 2, start + 3, following + 3, following + 2),
                (start + 3, start, following, following + 3),
            ]
        )
    last = (len(path_xz) - 1) * 4
    faces.append((last, last + 1, last + 2, last + 3))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(piece_material)
    bevel = obj.modifiers.new("SoftWebbingEdge", "BEVEL")
    bevel.width = 0.10
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    shade_smooth(obj)
    return obj


def add_flat_belt_loop(
    name: str,
    path_xy: list[tuple[float, float]],
    z_center: float,
    height: float,
    thickness: float,
    piece_material: bpy.types.Material,
) -> bpy.types.Object:
    """Build a flat, torso-following rescue belt instead of a rubbery tube."""
    half_height = height * 0.5
    half_thickness = thickness * 0.5
    vertices: list[tuple[float, float, float]] = []
    for index, (x, y) in enumerate(path_xy):
        previous = Vector(path_xy[(index - 1) % len(path_xy)])
        following = Vector(path_xy[(index + 1) % len(path_xy)])
        tangent = (following - previous).normalized()
        outward = Vector((tangent.y, -tangent.x)).normalized()
        centre = Vector((x, y))
        inner = centre - outward * half_thickness
        outer = centre + outward * half_thickness
        vertices.extend(
            [
                (inner.x, inner.y, z_center - half_height),
                (outer.x, outer.y, z_center - half_height),
                (outer.x, outer.y, z_center + half_height),
                (inner.x, inner.y, z_center + half_height),
            ]
        )
    faces: list[tuple[int, ...]] = []
    for section in range(len(path_xy)):
        start = section * 4
        following = ((section + 1) % len(path_xy)) * 4
        faces.extend(
            [
                (start, start + 1, following + 1, following),
                (start + 1, start + 2, following + 2, following + 1),
                (start + 2, start + 3, following + 3, following + 2),
                (start + 3, start, following, following + 3),
            ]
        )
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(piece_material)
    bevel = obj.modifiers.new("SoftBeltEdge", "BEVEL")
    bevel.width = min(thickness * 0.35, 0.12)
    bevel.segments = 3
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    shade_smooth(obj)
    return obj


def add_side_webbing_arc(
    name: str,
    path_xy: list[tuple[float, float]],
    z_center: float,
    height: float,
    thickness: float,
    piece_material: bpy.types.Material,
) -> bpy.types.Object:
    """Sweep open side webbing around the torso instead of through it."""
    half_height = height * 0.5
    half_thickness = thickness * 0.5
    vertices: list[tuple[float, float, float]] = []
    for x, y in path_xy:
        radial = Vector((x, y)).normalized()
        centre = Vector((x, y))
        inner = centre - radial * half_thickness
        outer = centre + radial * half_thickness
        vertices.extend(
            [
                (inner.x, inner.y, z_center - half_height),
                (outer.x, outer.y, z_center - half_height),
                (outer.x, outer.y, z_center + half_height),
                (inner.x, inner.y, z_center + half_height),
            ]
        )
    faces: list[tuple[int, ...]] = [(3, 2, 1, 0)]
    for section in range(len(path_xy) - 1):
        start = section * 4
        following = start + 4
        faces.extend(
            [
                (start, start + 1, following + 1, following),
                (start + 1, start + 2, following + 2, following + 1),
                (start + 2, start + 3, following + 3, following + 2),
                (start + 3, start, following, following + 3),
            ]
        )
    last = (len(path_xy) - 1) * 4
    faces.append((last, last + 1, last + 2, last + 3))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(piece_material)
    bevel = obj.modifiers.new("SoftSideWebbingEdge", "BEVEL")
    bevel.width = 0.08
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    shade_smooth(obj)
    return obj


def add_curve(
    name: str,
    points: list[tuple[float, float, float]],
    radius: float,
    piece_material: bpy.types.Material,
    cyclic: bool = False,
    resolution: int = 3,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = resolution
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


def add_torus(
    name: str,
    location: tuple[float, float, float],
    major_radius: float,
    minor_radius: float,
    piece_material: bpy.types.Material,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=24,
        minor_segments=8,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(piece_material)
    shade_smooth(obj)
    return obj


def build_pfd(materials: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    pieces: list[bpy.types.Object] = []

    # A real rescue vest is a sewn carrier holding separate foam cells, not a
    # collection of flotation blocks suspended around an empty torso. Two thin
    # front carrier halves and one rear carrier sit against the body, visibly
    # bridge the cell seams and give the zipper, straps and hardware a fabric
    # substrate. They remain sleeveless and add no shoulder flotation.
    for side in (-1.0, 1.0):

        def mirrored_carrier(
            points: list[tuple[float, float]],
        ) -> list[tuple[float, float]]:
            result = [(side * y, z) for y, z in points]
            return result if side > 0.0 else list(reversed(result))

        pieces.append(
            add_crowned_foam_panel(
                f"FrontCarrier_{side:+.0f}",
                12.5,
                0.7,
                mirrored_carrier(
                    [
                        (0.5, -16.0),
                        (14.7, -15.8),
                        (16.2, -11.2),
                        (16.4, 5.0),
                        (14.5, 15.5),
                        (10.5, 20.3),
                        (5.0, 21.0),
                        (0.8, 18.2),
                    ]
                ),
                materials["PfdShell"],
                0.20,
                0.14,
                lateral_wrap_depth=-1.9,
            )
        )
    pieces.append(
        add_crowned_foam_panel(
            "RearCarrier",
            -11.8,
            0.8,
            [
                (-14.0, -18.8),
                (14.0, -18.8),
                (16.0, -12.5),
                (16.4, 7.0),
                (13.8, 17.5),
                (7.0, 24.0),
                (-7.0, 24.0),
                (-13.8, 17.5),
                (-16.4, 7.0),
                (-16.0, -12.5),
            ],
            materials["PfdShell"],
            0.22,
            0.18,
            outward_sign=-1.0,
            lateral_wrap_depth=2.0,
        )
    )

    # Four contoured front foam cells. Rounded outlines, rolled edge rings, and
    # shallow exterior crowns read as soft fabric-covered flotation foam. The
    # authored inner edges create the entry V while the outer edges preserve
    # arm clearance.
    for side in (-1.0, 1.0):

        def mirrored(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
            result = [(side * y, z) for y, z in points]
            return result if side > 0.0 else list(reversed(result))

        pieces.append(
            add_crowned_foam_panel(
                f"FrontUpperCell_{side:+.0f}",
                14.2,
                3.0,
                mirrored(
                    [
                        (0.8, -0.6),
                        (11.9, -0.9),
                        (14.2, 3.7),
                        (13.5, 12.8),
                        (9.8, 18.8),
                        (4.7, 18.2),
                    ]
                ),
                materials["PfdShell"],
                0.75,
                0.65,
                lateral_wrap_depth=-3.0,
            )
        )
        pieces.append(
            add_crowned_foam_panel(
                f"FrontLowerCell_{side:+.0f}",
                14.2,
                3.0,
                mirrored(
                    [
                        (0.8, -14.2),
                        (12.1, -13.8),
                        (14.0, -10.0),
                        (13.6, -2.4),
                        (1.1, -1.1),
                    ]
                ),
                materials["PfdShell"],
                0.75,
                0.65,
                lateral_wrap_depth=-3.0,
            )
        )

    # Two thin, independently rounded rear cells replace the former single
    # 31.5 x 42 cm plate. A visible horizontal flex channel lets the lumbar
    # section move independently, while 3.2 cm of lateral arc wraps both cells
    # toward the flanks instead of presenting a rectangular backpack profile.
    rear_cells = [
        (
            "ProtectiveBackUpperCell",
            [
                (-13.4, 0.3),
                (13.4, 0.3),
                (15.2, 5.0),
                (14.3, 12.3),
                (10.7, 19.1),
                (6.3, 23.0),
                (-6.3, 23.0),
                (-10.7, 19.1),
                (-14.3, 12.3),
                (-15.2, 5.0),
            ],
        ),
        (
            "ProtectiveBackLumbarCell",
            [
                (-9.5, -17.8),
                (9.5, -17.8),
                (13.5, -13.2),
                (14.8, -6.0),
                (13.4, -0.3),
                (-13.4, -0.3),
                (-14.8, -6.0),
                (-13.5, -13.2),
            ],
        ),
    ]
    for name, outline in rear_cells:
        pieces.append(
            add_crowned_foam_panel(
                name,
                -13.0,
                2.4,
                outline,
                materials["PfdShell"],
                0.65,
                0.75,
                outward_sign=-1.0,
                lateral_wrap_depth=3.2,
            )
        )
    # Four open side adjustments match the referenced rescue-PFD construction.
    # Each thin textile run curves around the torso and overlaps the front and
    # rear carriers, preserving articulation without the former rigid yellow
    # wings or a solid side armour panel.
    for side in (-1.0, 1.0):
        path_xy = [
            (-13.8, side * 13.2),
            (-10.5, side * 15.2),
            (-6.0, side * 16.5),
            (0.0, side * 17.0),
            (6.0, side * 16.5),
            (10.5, side * 15.2),
            (13.8, side * 13.2),
        ]
        for index, z in enumerate((-8.7, 3.7)):
            pieces.append(
                add_side_webbing_arc(
                    f"SideWebbingConnector_{side:+.0f}_{index + 1}",
                    path_xy,
                    z,
                    1.05,
                    0.22,
                    materials["PfdWebbing"],
                )
            )

    # The flotation cells terminate below the shoulders. Only flexible fit
    # webbing crosses from the chest to the back so the vest does not create a
    # rigid shoulder-pad silhouette on the crew avatars.
    for side in (-1.0, 1.0):
        pieces.append(
            add_flat_webbing_run(
                f"ShoulderWebbingRun_{side:+.0f}",
                [
                    (14.8, 17.2),
                    (12.4, 20.0),
                    (5.5, 21.4),
                    (0.0, 21.8),
                    (-7.0, 20.8),
                    (-12.8, 18.5),
                    (-14.8, 16.5),
                ],
                side * 11.0,
                1.7,
                0.18,
                materials["PfdWebbing"],
            )
        )

    # Two useful front pockets sit low enough to preserve the paddle stroke.
    for side in (-1.0, 1.0):
        center_y = side * 8.6
        center_z = -7.4
        pieces.append(
            add_crowned_foam_panel(
                f"ZipperedFrontPocket_{side:+.0f}",
                15.45,
                0.35,
                [
                    (center_y - 4.1, center_z - 3.4),
                    (center_y + 4.1, center_z - 3.4),
                    (center_y + 5.4, center_z - 2.1),
                    (center_y + 5.4, center_z + 2.1),
                    (center_y + 4.1, center_z + 3.4),
                    (center_y - 4.1, center_z + 3.4),
                    (center_y - 5.4, center_z + 2.1),
                    (center_y - 5.4, center_z - 2.1),
                ],
                materials["PfdShell"],
                0.14,
                0.12,
            )
        )

    # Front entry zipper, two backup buckles, and pulls are explicit hardware.
    pieces.append(
        add_curve(
            "FrontEntryZipper",
            [(16.40, 0.0, -13.0), (16.55, 0.0, 2.0), (16.30, 0.0, 18.0)],
            0.22,
            materials["PfdHardware"],
            resolution=2,
        )
    )
    for index, z in enumerate((-9.5, 5.5)):
        pieces.append(
            add_rounded_box(
                f"BackupBuckle_{index + 1}",
                (16.72, 0.0, z),
                (0.9, 3.2, 1.8),
                materials["PfdHardware"],
                0.32,
            )
        )

    # Visible low-profile backup webbing ties the four foam cells together and
    # prevents the broad front from reading as a rigid plate carrier.
    for index, z in enumerate((-8.8, 4.8)):
        for side in (-1.0, 1.0):
            lateral_samples = [0.8, 4.0, 7.5, 10.8, 13.2]
            if side < 0.0:
                lateral_samples.reverse()
            pieces.append(
                add_side_webbing_arc(
                    f"FrontBackupWebbing_{index + 1}_{side:+.0f}",
                    [
                        (
                            16.48 - 3.0 * (lateral / 14.2) ** 2,
                            side * lateral,
                        )
                        for lateral in lateral_samples
                    ],
                    z,
                    1.05,
                    0.22,
                    materials["PfdWebbing"],
                )
            )

    # Four low-profile side sliders and four shoulder-end adjustments provide
    # the referenced eight fit points without hardware on the shoulder crest.
    adjustment_points = []
    for side in (-1.0, 1.0):
        adjustment_points.extend(
            [
                (4.5, side * 16.7, 3.7),
                (4.5, side * 16.7, -8.7),
            ]
        )
    for index, point in enumerate(adjustment_points):
        pieces.append(
            add_rounded_box(
                f"AdjustmentSlider_{index + 1:02d}",
                point,
                (2.0, 0.55, 1.45),
                materials["PfdHardware"],
                0.28,
            )
        )

    # A distinct 2-inch-class quick-release rescue belt and tether ring.
    belt_points = [
        (15.0, -11.0),
        (10.0, -16.8),
        (-8.0, -16.8),
        (-14.4, -11.0),
        (-15.3, 0.0),
        (-14.4, 11.0),
        (-8.0, 16.8),
        (10.0, 16.8),
        (15.0, 11.0),
        (16.7, 0.0),
    ]
    pieces.append(
        add_flat_belt_loop(
            "QuickReleaseRescueBelt",
            belt_points,
            -13.6,
            2.7,
            0.36,
            materials["PfdWebbing"],
        )
    )
    pieces.append(
        add_rounded_box(
            "QuickReleaseBuckle",
            (17.05, 0.0, -13.6),
            (0.75, 3.8, 2.2),
            materials["PfdHardware"],
            0.38,
        )
    )
    pieces.append(
        add_torus(
            "RescueTetherRing",
            (-15.6, 0.0, -10.8),
            1.8,
            0.32,
            materials["PfdHardware"],
            rotation=(0.0, math.pi / 2.0, 0.0),
        )
    )

    # Night-readability and blank placarding zones; no brand marks are used.
    for side in (-1.0, 1.0):
        pieces.append(
            add_rounded_box(
                f"ChestReflective_{side:+.0f}",
                (15.45, side * 8.6, 12.5),
                (0.36, 4.0, 1.4),
                materials["PfdReflective"],
                0.24,
            )
        )
    pieces.append(
        add_rounded_box(
            "BackPlacard",
            (-15.25, 0.0, 11.5),
            (0.7, 18.0, 5.2),
            materials["PfdLabel"],
            0.7,
        )
    )
    for side in (-1.0, 0.0, 1.0):
        pieces.append(
            add_rounded_box(
                f"FrontLashTab_{side:+.0f}",
                (
                    16.45 - 3.0 * (abs(side) * 7.5 / 14.2) ** 2,
                    side * 7.5,
                    2.3,
                ),
                (0.34, 1.5, 1.5),
                materials["PfdLabel"],
                0.24,
            )
        )
    return pieces


def join_and_uv(
    objects: list[bpy.types.Object],
    materials: dict[str, bpy.types.Material],
) -> bpy.types.Object:
    primary = objects[0]
    for name in MATERIAL_NAMES[1:]:
        primary.data.materials.append(materials[name])
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = primary
    bpy.ops.object.join()
    primary.name = "SM_RaftSim_WhitewaterRescuePfd"
    primary.data.name = "SM_RaftSim_WhitewaterRescuePfd"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.01)
    bpy.ops.object.mode_set(mode="OBJECT")
    shade_smooth(primary)
    return primary


def validate(mesh_object: bpy.types.Object) -> dict[str, object]:
    slots = [slot.name for slot in mesh_object.data.materials]
    if slots != MATERIAL_NAMES:
        raise RuntimeError(f"Production PFD material contract changed: {slots}")
    if not mesh_object.data.uv_layers:
        raise RuntimeError("Production PFD has no UV channel")
    if len(mesh_object.data.polygons) < 10_000:
        raise RuntimeError(
            f"Production PFD is unexpectedly low detail: {len(mesh_object.data.polygons)} polygons"
        )
    coordinates = [
        mesh_object.matrix_world @ vertex.co for vertex in mesh_object.data.vertices
    ]
    minimum = Vector(
        (
            min(v.x for v in coordinates),
            min(v.y for v in coordinates),
            min(v.z for v in coordinates),
        )
    )
    maximum = Vector(
        (
            max(v.x for v in coordinates),
            max(v.y for v in coordinates),
            max(v.z for v in coordinates),
        )
    )
    dimensions = maximum - minimum
    if not (
        32.0 <= dimensions.x <= 44.0
        and 32.0 <= dimensions.y <= 44.0
        and 40.0 <= dimensions.z <= 56.0
    ):
        raise RuntimeError(
            f"Production PFD bounds are implausible: {tuple(dimensions)}"
        )
    return {
        "vertex_count": len(mesh_object.data.vertices),
        "polygon_count": len(mesh_object.data.polygons),
        "material_slots": slots,
        "uv_channel_count": len(mesh_object.data.uv_layers),
        "bounds_min_cm": [round(value, 4) for value in minimum],
        "bounds_max_cm": [round(value, 4) for value in maximum],
        "dimensions_cm": [round(value, 4) for value in dimensions],
    }


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    materials = {
        "PfdShell": material("PfdShell", (0.7, 0.03, 0.01, 1.0), 0.78),
        "PfdWebbing": material("PfdWebbing", (0.01, 0.012, 0.014, 1.0), 0.72),
        "PfdHardware": material("PfdHardware", (0.04, 0.045, 0.05, 1.0), 0.55),
        "PfdReflective": material("PfdReflective", (0.72, 0.75, 0.72, 1.0), 0.24),
        "PfdLabel": material("PfdLabel", (0.08, 0.085, 0.09, 1.0), 0.68),
    }
    mesh_object = join_and_uv(build_pfd(materials), materials)
    audit = validate(mesh_object)
    bpy.context.view_layer.objects.active = mesh_object
    mesh_object.select_set(True)
    # Deterministic source builds must not overwrite the user's protected
    # `.blend1` recovery file when Blender saves the generated working copy.
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)
    bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH),
        use_selection=True,
        object_types={"MESH"},
        # The authored coordinates are centimetres. Custom mesh data does not
        # inherit the primitive operators' historical FBX unit conversion, so
        # make the centimetre-to-metre export scale explicit and deterministic.
        global_scale=0.01,
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
        "schema": "raftsim.production_whitewater_pfd_source.v1",
        "generator_version": GENERATOR_VERSION,
        "ownership": "Project-owned deterministic source art; no external mesh or texture input.",
        "source_inputs": [],
        "reference_only_sources": [
            {
                "url": "https://www.nrs.com/nrs-rapid-rescuer-pfd/pvdx",
                "facts_used": "high profile, four-panel chest, thin back, front zip, two pockets, eight adjustment points, reflective/placard zones and quick-release rescue belt",
                "asset_content_copied": False,
            },
            {
                "url": "https://astraldesigns.com/products/greenjacket",
                "facts_used": "whitewater/rafting rescue use, contoured layered foam, adjustable shoulder webbing, fitted sides and rescue hardware",
                "asset_content_copied": False,
            },
        ],
        "fbx": str(FBX_PATH.relative_to(REPO_ROOT)),
        "blend": str(BLEND_PATH.relative_to(REPO_ROOT)),
        "fbx_sha256": sha256(FBX_PATH),
        "blend_sha256": sha256(BLEND_PATH),
        "material_slots": MATERIAL_NAMES,
        "construction": {
            "front_carrier_panels": 2,
            "back_carrier_panels": 1,
            "front_foam_panels": 4,
            "back_panels": 2,
            "rear_flex_channels": 1,
            "side_wings": 0,
            "side_webbing_connectors": 4,
            "side_adjustment_sliders": 4,
            "shoulder_adjustment_points": 4,
            "shoulder_foam_pads": 0,
            "shoulder_webbing_runs": 2,
            "front_pockets": 2,
            "front_zip": 1,
            "backup_buckles": 2,
            "front_backup_webbing_runs": 4,
            "adjustment_points": 8,
            "quick_release_rescue_belts": 1,
            "rescue_tether_rings": 1,
            "reflective_chest_zones": 2,
            "blank_back_placards": 1,
            "front_lash_tabs": 3,
        },
        "soft_geometry": {
            "outline_corner_rounding": "four-pass closed Chaikin",
            "outline_corner_rounding_passes": 4,
            "flat_exterior_foam_faces": 0,
            "crown_profile": "eleven-ring soft cosine loft",
            "carrier_shell_thickness_cm": 0.7,
            "front_panel_foam_thickness_cm": 3.0,
            "front_panel_edge_roll_cm": 0.75,
            "front_panel_crown_depth_cm": 0.65,
            "front_panel_lateral_wrap_depth_cm": 3.0,
            "back_panel_foam_thickness_cm": 2.4,
            "back_panel_edge_roll_cm": 0.65,
            "back_panel_crown_depth_cm": 0.75,
            "back_panel_lateral_wrap_depth_cm": 3.2,
            "rigid_side_foam_wings": 0,
            "side_webbing_connector_profile": "curved torso-following fabric",
            "side_webbing_connector_thickness_cm": 0.22,
            "side_webbing_connector_height_cm": 1.05,
            "front_pocket_flat_exterior_faces": 0,
            "front_pocket_crown_depth_cm": 0.12,
            "front_backup_webbing_profile": "curved torso-following fabric",
            "rescue_belt_profile": "flat torso-following webbing",
            "rescue_belt_thickness_cm": 0.36,
            "duplicate_tubular_side_adjustment_runs": 0,
            "smooth_shaded": True,
        },
        "runtime_boundary": "Collisionless torso-following safety-gear visual; body animation, seat mass, D3/D4, rescue and swimmer authority remain native.",
        **audit,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
