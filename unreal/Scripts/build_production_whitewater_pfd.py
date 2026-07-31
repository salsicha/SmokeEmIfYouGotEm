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
GENERATOR_VERSION = 4
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
    vertices = [
        (x_center + half_depth, y, z) for y, z in outline_yz
    ] + [
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


def add_swept_shoulder_bridge(
    name: str,
    path_xz: list[tuple[float, float]],
    y_center: float,
    width: float,
    thickness: float,
    piece_material: bpy.types.Material,
) -> bpy.types.Object:
    """Sweep a flattened foam band over one shoulder as a continuous shell."""
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
    bevel = obj.modifiers.new("ShoulderBandEdge", "BEVEL")
    bevel.width = 0.65
    bevel.segments = 6
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

    # Four contoured front foam cells. Broad, shallow extrusions read as layered
    # flotation foam instead of inflated balloons. The authored inner edges
    # create the front-entry V while the outer edges preserve arm clearance.
    for side in (-1.0, 1.0):
        def mirrored(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
            result = [(side * y, z) for y, z in points]
            return result if side > 0.0 else list(reversed(result))

        pieces.append(
            add_extruded_panel(
                f"FrontUpperCell_{side:+.0f}",
                17.0,
                7.2,
                mirrored(
                    [
                        (2.3, -0.7),
                        (13.8, -1.0),
                        (16.9, 4.8),
                        (15.8, 14.8),
                        (11.0, 21.7),
                        (6.2, 20.6),
                    ]
                ),
                materials["PfdShell"],
                1.15,
            )
        )
        pieces.append(
            add_extruded_panel(
                f"FrontLowerCell_{side:+.0f}",
                17.1,
                7.4,
                mirrored(
                    [
                        (1.8, -14.5),
                        (14.8, -14.2),
                        (16.8, -10.2),
                        (16.2, -2.3),
                        (3.0, -1.3),
                    ]
                ),
                materials["PfdShell"],
                1.1,
            )
        )

    # A thin, contoured back turns the front cells into one wearable shell.
    # The former 31.5 x 42 cm rounded rectangle read as a rigid backpack from
    # the guide camera. This authored perimeter narrows at the lumbar hem and
    # between the shoulder blades while retaining lateral flotation volume.
    pieces.append(
        add_extruded_panel(
            "ProtectiveBackPanel",
            -14.6,
            4.8,
            [
                (-10.0, -17.5),
                (10.0, -17.5),
                (14.5, -13.0),
                (16.0, -5.0),
                (15.0, 11.5),
                (11.5, 19.5),
                (6.8, 23.0),
                (-6.8, 23.0),
                (-11.5, 19.5),
                (-15.0, 11.5),
                (-16.0, -5.0),
                (-14.5, -13.0),
            ],
            materials["PfdShell"],
            1.35,
        )
    )
    for side in (-1.0, 1.0):
        pieces.append(
            add_rounded_box(
                f"SideWing_{side:+.0f}",
                (0.5, side * 18.4, -0.5),
                (25.5, 4.2, 15.0),
                materials["PfdShell"],
                1.65,
                rotation=(0.0, 0.0, math.radians(side * 2.0)),
            )
        )

    # Each reinforced shoulder is a single continuous swept foam band. This
    # preserves the low body-hugging arc without the visible joints that made
    # the prior three-box construction look mechanical in portrait framing.
    for side in (-1.0, 1.0):
        pieces.append(
            add_swept_shoulder_bridge(
                f"ShoulderFoamBand_{side:+.0f}",
                [
                    (14.0, 21.0),
                    (8.0, 24.0),
                    (1.0, 25.6),
                    (-6.0, 24.3),
                    (-12.5, 21.2),
                ],
                side * 11.5,
                5.2,
                2.6,
                materials["PfdShell"],
            )
        )

    # Two useful front pockets sit low enough to preserve the paddle stroke.
    for side in (-1.0, 1.0):
        pieces.append(
            add_rounded_box(
                f"ZipperedFrontPocket_{side:+.0f}",
                (21.8, side * 8.6, -7.4),
                (1.8, 10.8, 6.8),
                materials["PfdShell"],
                0.85,
            )
        )

    # Front entry zipper, two backup buckles, and pulls are explicit hardware.
    pieces.append(
        add_curve(
            "FrontEntryZipper",
            [(21.1, 0.0, -13.0), (21.3, 0.0, 2.0), (20.8, 0.0, 19.5)],
            0.30,
            materials["PfdHardware"],
            resolution=2,
        )
    )
    for index, z in enumerate((-9.5, 5.5)):
        pieces.append(
            add_rounded_box(
                f"BackupBuckle_{index + 1}",
                (21.8, 0.0, z),
                (1.6, 3.8, 2.3),
                materials["PfdHardware"],
                0.45,
            )
        )

    # Visible low-profile backup webbing ties the four foam cells together and
    # prevents the broad front from reading as a rigid plate carrier.
    for index, z in enumerate((-8.8, 4.8)):
        pieces.append(
            add_rounded_box(
                f"FrontBackupWebbing_{index + 1}",
                (21.05, 0.0, z),
                (0.55, 29.0, 1.35),
                materials["PfdWebbing"],
                0.28,
            )
        )

    # Eight fit points: four side, two shoulder, and two waist adjustments.
    adjustment_runs = []
    for side in (-1.0, 1.0):
        adjustment_runs.extend(
            [
                [(11.0, side * 20.0, 9.0), (-8.0, side * 20.0, 9.0)],
                [(11.0, side * 20.0, -6.0), (-8.0, side * 20.0, -6.0)],
                [(11.5, side * 12.8, 23.0), (-6.0, side * 12.8, 25.5)],
                [(15.0, side * 18.0, -13.0), (-10.0, side * 17.5, -13.0)],
            ]
        )
    for index, points in enumerate(adjustment_runs):
        pieces.append(
            add_curve(
                f"AdjustmentWebbing_{index + 1:02d}",
                points,
                0.62,
                materials["PfdWebbing"],
                resolution=2,
            )
        )
        midpoint = Vector(points[0]).lerp(Vector(points[-1]), 0.5)
        pieces.append(
            add_rounded_box(
                f"AdjustmentSlider_{index + 1:02d}",
                tuple(midpoint),
                (2.0, 2.8, 1.5),
                materials["PfdHardware"],
                0.35,
            )
        )

    # A distinct 2-inch-class quick-release rescue belt and tether ring.
    belt_points = [
        (18.5, -16.5, -14.0),
        (0.0, -21.5, -14.0),
        (-15.5, -15.5, -14.0),
        (-18.5, 0.0, -14.0),
        (-15.5, 15.5, -14.0),
        (0.0, 21.5, -14.0),
        (18.5, 16.5, -14.0),
        (21.0, 0.0, -14.0),
    ]
    pieces.append(
        add_curve(
            "QuickReleaseRescueBelt",
            belt_points,
            0.95,
            materials["PfdWebbing"],
            cyclic=True,
            resolution=2,
        )
    )
    pieces.append(
        add_rounded_box(
            "QuickReleaseBuckle",
            (21.8, 0.0, -14.0),
            (1.8, 4.8, 2.8),
            materials["PfdHardware"],
            0.5,
        )
    )
    pieces.append(
        add_torus(
            "RescueTetherRing",
            (-19.0, 0.0, -11.0),
            2.7,
            0.5,
            materials["PfdHardware"],
            rotation=(0.0, math.pi / 2.0, 0.0),
        )
    )

    # Night-readability and blank placarding zones; no brand marks are used.
    for side in (-1.0, 1.0):
        pieces.append(
            add_rounded_box(
                f"ChestReflective_{side:+.0f}",
                (21.1, side * 9.2, 13.0),
                (0.6, 4.5, 1.8),
                materials["PfdReflective"],
                0.35,
            )
        )
    pieces.append(
        add_rounded_box(
            "BackPlacard",
            (-18.5, 0.0, 11.5),
            (1.0, 18.0, 5.2),
            materials["PfdLabel"],
            0.7,
        )
    )
    for side in (-1.0, 0.0, 1.0):
        pieces.append(
            add_rounded_box(
                f"FrontLashTab_{side:+.0f}",
                (21.2, side * 8.0, 2.5),
                (0.7, 2.6, 2.6),
                materials["PfdLabel"],
                0.35,
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
    coordinates = [mesh_object.matrix_world @ vertex.co for vertex in mesh_object.data.vertices]
    minimum = Vector((min(v.x for v in coordinates), min(v.y for v in coordinates), min(v.z for v in coordinates)))
    maximum = Vector((max(v.x for v in coordinates), max(v.y for v in coordinates), max(v.z for v in coordinates)))
    dimensions = maximum - minimum
    if not (38.0 <= dimensions.x <= 50.0 and 40.0 <= dimensions.y <= 52.0 and 44.0 <= dimensions.z <= 60.0):
        raise RuntimeError(f"Production PFD bounds are implausible: {tuple(dimensions)}")
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
                "facts_used": "whitewater/rafting rescue use, contoured layered foam, reinforced shoulders/sides and rescue hardware",
                "asset_content_copied": False,
            },
        ],
        "fbx": str(FBX_PATH.relative_to(REPO_ROOT)),
        "blend": str(BLEND_PATH.relative_to(REPO_ROOT)),
        "fbx_sha256": sha256(FBX_PATH),
        "blend_sha256": sha256(BLEND_PATH),
        "material_slots": MATERIAL_NAMES,
        "construction": {
            "front_foam_panels": 4,
            "back_panels": 1,
            "side_wings": 2,
            "shoulder_bridges": 2,
            "front_pockets": 2,
            "front_zip": 1,
            "backup_buckles": 2,
            "front_backup_webbing_runs": 2,
            "adjustment_points": 8,
            "quick_release_rescue_belts": 1,
            "rescue_tether_rings": 1,
            "reflective_chest_zones": 2,
            "blank_back_placards": 1,
            "front_lash_tabs": 3,
        },
        "runtime_boundary": "Collisionless torso-following safety-gear visual; body animation, seat mass, D3/D4, rescue and swimmer authority remain native.",
        **audit,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
