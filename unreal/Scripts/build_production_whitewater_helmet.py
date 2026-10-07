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
import numpy as np
from mathutils import Matrix, Vector


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionHelmet"
FBX_PATH = OUTPUT_ROOT / "SM_RaftSim_WhitewaterHelmet.fbx"
MANIFEST_PATH = OUTPUT_ROOT / "production_whitewater_helmet_manifest.json"
BLEND_PATH = OUTPUT_ROOT / "SM_RaftSim_WhitewaterHelmet.blend"
GENERATOR_VERSION = 9

# V9 is a full-cut river helmet. The v8 bowl stopped at the skull equator and
# read as a skate helmet ("the helmets look more like skating helmets than
# white water helmets, which usually cover more of the head", 2026-10-07).
# Like the Rocker/Trident/Shred Ready full cuts, the shell now drops over the
# temples into moulded ear covers, carries the occiput down toward the neck,
# and ends at the brow in a short integrated peak. Sizes were fitted to the
# five CC0 wearers in this frame (game fit applied), hair included, so the
# shared shell clears every head with a liner gap.
#
# Outer surface, mesh frame (cm): +X forward, +Y left, +Z up, origin at the
# fitted skull centre. Every meridian runs from the crown down a
# superelliptic dome to the equator, then down a near-vertical skirt to the
# rim; the rim height varies with azimuth.
SHELL_AXIS_X = 0.4
CROWN_Z = 16.6
FRONT_REACH = 16.3
REAR_REACH = 15.6
HALF_WIDTH = 13.2
PLAN_EXPONENT = 2.6
DOME_EXPONENT = 2.4
# The widest band rises toward the brow, as on a real shell, so the forehead
# stays full while the back and ear covers drop straight down.
EQUATOR_Z = 0.5
EQUATOR_FRONT_RISE = 2.5
# Inward tuck of the skirt 10 cm below the equator: the ear covers close
# toward the jaw, the occiput stays wide enough to pass braids under the rim.
SIDE_TUCK = 0.08
REAR_TUCK = 0.02
SHELL_THICKNESS = 0.4
SIDES = 112
RINGS = 42
# The dome's rings sit at the same arc length from the crown on every
# meridian; only the band below UPPER_ARC stretches to meet the rim. Rings
# spread by fraction of the whole meridian sheared across the steep ear-cover
# edges and showed as cross-hatched shading up to the crown.
UPPER_ARC = 16.0
UPPER_RINGS = 22
# The lower band's rings crowd toward the rim, where the peak needs detail.
RING_WARP = 1.2
# Lower edge height (cm) by azimuth (degrees from +X toward +Y, mirrored):
# brow line above the eyebrows, a temple step that stays behind the eyes,
# ear covers below the lobes, a scallop behind the ear, occipital tail.
RIM_PROFILE = (
    (0.0, 3.5), (25.0, 3.3), (50.0, 2.4), (62.0, 0.4), (74.0, -7.0),
    (84.0, -9.0), (112.0, -9.0), (130.0, -7.4), (152.0, -6.8), (180.0, -7.6),
)
# Short integrated peak: the brow wall flares forward over its last arc. The
# occiput gets a smaller kick-out, the moulded tail of a full-cut shell.
BRIM_REACH = 1.3
BRIM_DROP = 0.25
BRIM_ARC = 2.2
BRIM_FULL_DEG = 22.0
BRIM_END_DEG = 56.0
TAIL_REACH = 0.45
TAIL_ARC = 1.6
TAIL_START_DEG = 140.0


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


# --- Shell surface -----------------------------------------------------------

def smoothstep(edge0: float, edge1: float, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def azimuth_degrees(theta: float) -> float:
    return abs(math.degrees(math.atan2(math.sin(theta), math.cos(theta))))


def rim_slopes() -> list[float]:
    """Monotone (Fritsch-Carlson) slopes through RIM_PROFILE, flat at 0/180.

    Easing each segment separately stalled the edge at every control point,
    which read as small steps in the temple and ear-cover lines.
    """
    xs = [a for a, _ in RIM_PROFILE]
    ys = [z for _, z in RIM_PROFILE]
    secants = [(ys[k + 1] - ys[k]) / (xs[k + 1] - xs[k]) for k in range(len(xs) - 1)]
    slopes = [0.0]
    for k in range(1, len(xs) - 1):
        before, after = secants[k - 1], secants[k]
        if before * after <= 0.0:
            slopes.append(0.0)
            continue
        h0, h1 = xs[k] - xs[k - 1], xs[k + 1] - xs[k]
        w0, w1 = 2.0 * h1 + h0, h1 + 2.0 * h0
        slopes.append((w0 + w1) / (w0 / before + w1 / after))
    return slopes + [0.0]


def rim_height(theta: float) -> float:
    degrees = azimuth_degrees(theta)
    slopes = rim_slopes()
    for k, ((a0, z0), (a1, z1)) in enumerate(zip(RIM_PROFILE, RIM_PROFILE[1:])):
        if degrees <= a1:
            h = a1 - a0
            t = (degrees - a0) / h
            return (
                (2 * t**3 - 3 * t**2 + 1) * z0
                + (t**3 - 2 * t**2 + t) * h * slopes[k]
                + (-2 * t**3 + 3 * t**2) * z1
                + (t**3 - t**2) * h * slopes[k + 1]
            )
    return RIM_PROFILE[-1][1]


def plan_radius(theta: float) -> float:
    c, s = math.cos(theta), math.sin(theta)
    reach = FRONT_REACH if c >= 0.0 else REAR_REACH
    n = PLAN_EXPONENT
    return (abs(c / reach) ** n + abs(s / HALF_WIDTH) ** n) ** (-1.0 / n)


def brim_weight(theta: float) -> float:
    return 1.0 - float(smoothstep(BRIM_FULL_DEG, BRIM_END_DEG, azimuth_degrees(theta)))


def meridian(theta: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Dense outer profile (rho from the axis, z, arc length), crown to rim."""
    radius = plan_radius(theta)
    front = max(math.cos(theta), 0.0)
    rear = max(-math.cos(theta), 0.0)
    equator = EQUATOR_Z + EQUATOR_FRONT_RISE * front * front
    tuck = SIDE_TUCK + (REAR_TUCK - SIDE_TUCK) * rear * rear
    t = np.linspace(0.0, 0.5 * math.pi, 241)
    exponent = 2.0 / DOME_EXPONENT
    dome_rho = radius * np.clip(np.sin(t), 0.0, 1.0) ** exponent
    dome_z = equator + (CROWN_Z - equator) * np.clip(np.cos(t), 0.0, 1.0) ** exponent
    depth = np.linspace(0.0, 16.0, 161)[1:]
    skirt_rho = radius * (1.0 - tuck * (depth / 10.0) ** 2)
    rho = np.concatenate([dome_rho, skirt_rho])
    z = np.concatenate([dome_z, equator - depth])
    rim = rim_height(theta)
    end = int(np.argmax(z <= rim))
    f = (z[end - 1] - rim) / (z[end - 1] - z[end])
    rho = np.append(rho[:end], rho[end - 1] + f * (rho[end] - rho[end - 1]))
    z = np.append(z[:end], rim)
    arc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(rho), np.diff(z)))])
    brim = brim_weight(theta)
    tail = float(smoothstep(TAIL_START_DEG, 180.0, azimuth_degrees(theta)))
    if brim > 0.0 or tail > 0.0:
        u = np.clip(1.0 - (arc[-1] - arc) / BRIM_ARC, 0.0, 1.0) ** 2
        w = np.clip(1.0 - (arc[-1] - arc) / TAIL_ARC, 0.0, 1.0) ** 2
        rho = rho + BRIM_REACH * brim * u + TAIL_REACH * tail * w
        z = z - BRIM_DROP * brim * u
        arc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(rho), np.diff(z)))])
    return rho, z, arc


def surface_point(theta: float, arc_length: float) -> np.ndarray:
    rho, z, arc = meridian(theta)
    s = float(np.clip(arc_length, 0.0, arc[-1]))
    r = float(np.interp(s, arc, rho))
    return np.array([SHELL_AXIS_X + r * math.cos(theta), r * math.sin(theta), float(np.interp(s, arc, z))])


def surface_frame(theta: float, arc_length: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Outer point, outward normal and downhill meridian tangent."""
    point = surface_point(theta, arc_length)
    down = surface_point(theta, arc_length + 0.05) - surface_point(theta, arc_length - 0.05)
    across = surface_point(theta + 0.004, arc_length) - surface_point(theta - 0.004, arc_length)
    normal = np.cross(down, across)
    tangent = down / np.linalg.norm(down)
    return point, normal / np.linalg.norm(normal), tangent


def arc_at_height(theta: float, height: float) -> float:
    _, z, arc = meridian(theta)
    return float(np.interp(-height, -z, arc))


def arc_at_radius(theta: float, radius: float) -> float:
    rho, _, arc = meridian(theta)
    crown = int(np.argmax(rho))
    return float(np.interp(radius, rho[: crown + 1], arc[: crown + 1]))


def side_azimuth(x: float, height: float, side: float) -> float:
    """Azimuth of the side-wall point at the given forward position and height."""
    low, high = math.radians(20.0), math.radians(160.0)
    for _ in range(40):
        middle = 0.5 * (low + high)
        if surface_point(middle, arc_at_height(middle, height))[0] > x:
            low = middle
        else:
            high = middle
    return side * 0.5 * (low + high)


def shell_azimuths() -> np.ndarray:
    """Meridian azimuths spaced evenly along the rim, not in angle.

    Equal angles left the steep front edges of the ear covers with a few
    long, visibly faceted rim segments; this spends meridians where the rim
    drops. The spacing is mirror-symmetric about the XZ plane.
    """
    fine = np.linspace(0.0, math.tau, 2881)
    middle = 0.5 * (fine[:-1] + fine[1:])
    radius = np.array([plan_radius(theta) for theta in middle])
    height = np.array([rim_height(theta) for theta in fine])
    step = np.hypot(radius * np.diff(fine), np.diff(height))
    measure = np.concatenate([[0.0], np.cumsum(step)])
    return np.interp(np.arange(SIDES) * measure[-1] / SIDES, measure, fine)


def shell_grids() -> tuple[np.ndarray, np.ndarray]:
    """Outer and inner surfaces as (RINGS + 1, SIDES, 3); row 0 is the crown."""
    outer = np.zeros((RINGS + 1, SIDES, 3))
    lower = np.linspace(0.0, 1.0, RINGS - UPPER_RINGS + 1)[1:]
    lower = 1.0 - (1.0 - lower) ** RING_WARP
    for side, theta in enumerate(shell_azimuths()):
        rho, z, arc = meridian(theta)
        samples = np.concatenate([np.linspace(0.0, UPPER_ARC, UPPER_RINGS + 1), UPPER_ARC + (arc[-1] - UPPER_ARC) * lower])
        r = np.interp(samples, arc, rho)
        outer[:, side, 0] = SHELL_AXIS_X + r * math.cos(theta)
        outer[:, side, 1] = r * math.sin(theta)
        outer[:, side, 2] = np.interp(samples, arc, z)
    # Offset along the surface normal so the wall is the same thickness under
    # the peak and ear covers as at the crown.
    across = np.roll(outer, -1, axis=1) - np.roll(outer, 1, axis=1)
    down = np.empty_like(outer)
    down[1:-1] = outer[2:] - outer[:-2]
    down[0] = outer[1] - outer[0]
    down[-1] = outer[-1] - outer[-2]
    normals = np.cross(down, across)
    normals[0] = (0.0, 0.0, 1.0)
    normals /= np.linalg.norm(normals, axis=2, keepdims=True)
    return outer, outer - SHELL_THICKNESS * normals


def build_shell(shell_material: bpy.types.Material) -> bpy.types.Object:
    """Create the watertight, physically thick full-cut shell."""

    outer, inner = shell_grids()
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    layer_stride = 1 + RINGS * SIDES

    def index(layer: int, ring: int, side: int) -> int:
        if ring == 0:
            return layer * layer_stride
        return layer * layer_stride + 1 + (ring - 1) * SIDES + side % SIDES

    for grid in (outer, inner):
        vertices.append(tuple(grid[0, 0]))
        for ring in range(1, RINGS + 1):
            vertices.extend(tuple(point) for point in grid[ring])

    for layer in range(2):
        layer_faces: list[tuple[int, ...]] = []
        for side in range(SIDES):
            layer_faces.append((index(layer, 0, 0), index(layer, 1, side), index(layer, 1, side + 1)))
            for ring in range(1, RINGS):
                layer_faces.append(
                    (
                        index(layer, ring, side),
                        index(layer, ring + 1, side),
                        index(layer, ring + 1, side + 1),
                        index(layer, ring, side + 1),
                    )
                )
        # The inner wall faces the head: same topology, reversed winding.
        faces.extend(layer_faces if layer == 0 else [tuple(reversed(face)) for face in layer_faces])

    # Close the lower edge through the real wall thickness.
    for side in range(SIDES):
        faces.append(
            (
                index(0, RINGS, side),
                index(1, RINGS, side),
                index(1, RINGS, side + 1),
                index(0, RINGS, side + 1),
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


# --- Vents and drainage --------------------------------------------------------

def oriented_cutter(
    name: str,
    centre: np.ndarray,
    axes: tuple[np.ndarray, np.ndarray, np.ndarray],
    dimensions: tuple[float, float, float],
    rounded: bool = True,
) -> bpy.types.Object:
    """A cutter whose local X/Y/Z follow the given surface-aligned axes."""
    if rounded:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
    else:
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.5, depth=1.0)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rounded:
        bevel = obj.modifiers.new("RoundedSlot", "BEVEL")
        bevel.width = min(dimensions[:2]) * 0.46
        bevel.segments = 6
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    basis = Matrix([list(axis) for axis in axes]).transposed()
    obj.matrix_world = Matrix.Translation(Vector(centre)) @ basis.to_4x4()
    return obj


def slot_frame(point: np.ndarray, normal: np.ndarray, along: np.ndarray):
    """Surface-aligned (slot length, slot width, through-wall) axes."""
    along = along - normal * float(np.dot(along, normal))
    along /= np.linalg.norm(along)
    return along, np.cross(normal, along), normal


def vent_cutters() -> list[bpy.types.Object]:
    # Six cut-through slots expose the shell thickness: four crown slots and
    # two rear upper slots. Narrow, well-separated openings keep substantial
    # moulded bridges at 720p under gameplay TAA (wide first-pass cutters
    # visually merged and made the crown read as broken).
    cutters = []
    # The crown slots sit forward of the top so front and quarter views,
    # not only the overhead camera, see them.
    crown = [((4.0, -5.6), 4.4, 0.74), ((5.4, -1.9), 4.6, 0.70), ((5.4, 1.9), 4.6, 0.70), ((4.0, 5.6), 4.4, 0.74)]
    for index, ((x, y), length, width) in enumerate(crown):
        theta = math.atan2(y, x - SHELL_AXIS_X)
        point, normal, _ = surface_frame(theta, arc_at_radius(theta, math.hypot(x - SHELL_AXIS_X, y)))
        axes = slot_frame(point, normal, np.array([1.0, 0.0, 0.0]))
        centre = point - normal * 0.5 * SHELL_THICKNESS
        cutters.append(oriented_cutter(f"VentCutter_{index:02d}", centre, axes, (length, width, 2.4)))
    for index, side in enumerate((-1.0, 1.0), start=len(cutters)):
        theta = side * math.radians(152.0)
        point, normal, tangent = surface_frame(theta, arc_at_height(theta, 9.4))
        axes = slot_frame(point, normal, tangent)
        centre = point - normal * 0.5 * SHELL_THICKNESS
        cutters.append(oriented_cutter(f"VentCutter_{index:02d}", centre, axes, (3.6, 0.78, 2.4)))
    return cutters


def ear_port_cutters() -> list[bpy.types.Object]:
    # Two drainage/hearing ports per ear cover, over the ear canal of every
    # wearer (ears span x -4..2.5, z -8.4..2.6 in this frame).
    cutters = []
    for side in (-1.0, 1.0):
        for index, (x, z) in enumerate(((-0.2, -2.0), (-1.6, -3.9))):
            theta = side_azimuth(x, z, side)
            point, normal, tangent = surface_frame(theta, arc_at_height(theta, z))
            axes = slot_frame(point, normal, tangent)
            centre = point - normal * 0.5 * SHELL_THICKNESS
            name = f"EarPortCutter_{'L' if side > 0 else 'R'}{index}"
            cutters.append(oriented_cutter(name, centre, axes, (0.95, 0.95, 2.4), rounded=False))
    return cutters


def cut_vents(shell: bpy.types.Object, cutters: list[bpy.types.Object]) -> int:
    applied = 0
    for cutter in cutters:
        modifier = shell.modifiers.new(f"Cut_{cutter.name}", "BOOLEAN")
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


# --- Liner, webbing and hardware -----------------------------------------------

def mesh_object(
    name: str,
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    piece_material: bpy.types.Material,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(piece_material)
    shade_smooth(obj)
    return obj


def rim_gasket(liner_material: bpy.types.Material) -> bpy.types.Object:
    """Closed foam bead around the whole lower edge, showing just below it."""
    # The bead straddles the wall rather than hanging inside it: an inboard
    # bead came within 0.01 cm of the braids and the bob under the rim.
    radius = 0.32
    segments = 8
    azimuths = np.append(shell_azimuths(), math.tau)
    thetas = np.concatenate([np.linspace(a, b, 3, endpoint=False) for a, b in zip(azimuths[:-1], azimuths[1:])])
    samples = len(thetas)
    centres = []
    normals = []
    for theta in thetas:
        _, _, arc = meridian(theta)
        point, normal, tangent = surface_frame(theta, arc[-1] - 0.02)
        centres.append(point - normal * (0.5 * SHELL_THICKNESS) - tangent * (radius - 0.22))
        normals.append(normal)
    vertices = []
    for index, (centre, normal) in enumerate(zip(centres, normals)):
        along = centres[(index + 1) % samples] - centres[index - 1]
        along /= np.linalg.norm(along)
        inward = -(normal - along * float(np.dot(normal, along)))
        inward /= np.linalg.norm(inward)
        binormal = np.cross(along, inward)
        for k in range(segments):
            angle = math.tau * k / segments
            vertices.append(tuple(centre + radius * (math.cos(angle) * inward + math.sin(angle) * binormal)))
    faces = []
    for index in range(samples):
        a, b = index * segments, ((index + 1) % samples) * segments
        for k in range(segments):
            k1 = (k + 1) % segments
            faces.append((a + k, a + k1, b + k1, b + k))
    obj = mesh_object("LowerEdgeGasket", vertices, faces, liner_material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)
    return obj


# Retention anchors (left side; the right mirrors in Y): the lower front and
# rear corners of each ear cover. build_production_helmet_straps.py hangs each
# wearer's fitted straps from these points.
FRONT_ANCHOR_DEG = 76.0
REAR_ANCHOR_DEG = 120.0
ANCHOR_TAB_LENGTH = 2.0
ANCHOR_TAB_DROP = 0.25


def anchor_tab_ends(theta: float) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
    """(outer point, normal) where the tab is riveted and where it leaves the rim."""
    _, _, arc = meridian(theta)
    top, top_normal, _ = surface_frame(theta, arc[-1] - ANCHOR_TAB_LENGTH)
    rim, rim_normal, tangent = surface_frame(theta, arc[-1] - 0.02)
    return (top, top_normal), (rim + tangent * ANCHOR_TAB_DROP, rim_normal)


def retention_anchor(theta: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Strap start (lower end of the tab, inside the rim), rivet point, normal."""
    _, _, arc = meridian(theta)
    rivet, normal, _ = surface_frame(theta, arc[-1] - ANCHOR_TAB_LENGTH + 0.6)
    _, (bottom, bottom_normal) = anchor_tab_ends(theta)
    return bottom - bottom_normal * (SHELL_THICKNESS + 0.15), rivet, normal


def anchor_tabs(webbing_material: bpy.types.Material) -> list[bpy.types.Object]:
    # Short webbing tabs riveted inside each ear cover; the fitted straps
    # continue from their lower ends.
    tabs = []
    for side in (-1.0, 1.0):
        for label, degrees in (("Front", FRONT_ANCHOR_DEG), ("Rear", REAR_ANCHOR_DEG)):
            theta = side * math.radians(degrees)
            (top, normal_top), (bottom, normal_bottom) = anchor_tab_ends(theta)
            vertices = []
            for point, normal in ((top, normal_top), (bottom, normal_bottom)):
                along = bottom - top
                along /= np.linalg.norm(along)
                across = np.cross(normal, along)
                across /= np.linalg.norm(across)
                for depth in (SHELL_THICKNESS + 0.04, SHELL_THICKNESS + 0.26):
                    for width in (-0.75, 0.75):
                        vertices.append(tuple(point - normal * depth + across * width))
            faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
            tab = mesh_object(f"RetentionWebbing_{label}{'L' if side > 0 else 'R'}", vertices, faces, webbing_material)
            bpy.context.view_layer.objects.active = tab
            tab.select_set(True)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode="OBJECT")
            tab.select_set(False)
            tabs.append(tab)
    return tabs


def rivet(name: str, point: np.ndarray, normal: np.ndarray, radius: float, hardware_material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=0.3)
    obj = bpy.context.object
    obj.name = name
    z_axis = Vector(normal).normalized()
    obj.matrix_world = Matrix.Translation(Vector(point) + z_axis * 0.04) @ z_axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bevel = obj.modifiers.new("DomedHead", "BEVEL")
    bevel.width = 0.1
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    obj.data.materials.append(hardware_material)
    shade_smooth(obj)
    return obj


def build_details(
    liner_material: bpy.types.Material,
    webbing_material: bpy.types.Material,
    hardware_material: bpy.types.Material,
) -> list[bpy.types.Object]:
    # Creation order sets the joined slot order: liner, webbing, hardware.
    details: list[bpy.types.Object] = [rim_gasket(liner_material)]
    # The four-point retention straps and chin strap that hang from the
    # anchors are fitted to each wearer's own head and chin
    # (build_production_helmet_straps.py); one shared set cut through the
    # deeper chins ("the helmet chin straps should go under the chin, not
    # cut through it", 2026-10-05).
    details.extend(anchor_tabs(webbing_material))
    for side in (-1.0, 1.0):
        for label, degrees in (("Front", FRONT_ANCHOR_DEG), ("Rear", REAR_ANCHOR_DEG)):
            _, point, normal = retention_anchor(side * math.radians(degrees))
            details.append(rivet(f"AnchorRivet_{label}{'L' if side > 0 else 'R'}", point, normal, 0.55, hardware_material))
        # Peak screws at the temples, as on removable-peak river shells.
        theta = side * math.radians(40.0)
        _, _, arc = meridian(theta)
        point, normal, _ = surface_frame(theta, arc[-1] - 3.2)
        details.append(rivet(f"PeakScrew_{'L' if side > 0 else 'R'}", point, normal, 0.42, hardware_material))
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


def rounded(values) -> list[float]:
    return [round(float(value), 3) for value in values]


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    shell_material = material("HelmetShell", (0.06, 0.18, 0.31, 1.0), 0.38)
    liner_material = material("HelmetLiner", (0.012, 0.015, 0.018, 1.0), 0.78)
    webbing_material = material("HelmetWebbing", (0.018, 0.021, 0.024, 1.0), 0.86)
    hardware_material = material("HelmetHardware", (0.08, 0.09, 0.10, 1.0), 0.54)

    shell = build_shell(shell_material)
    vent_count = cut_vents(shell, vent_cutters())
    ear_port_count = cut_vents(shell, ear_port_cutters())
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
    front_anchor = retention_anchor(math.radians(FRONT_ANCHOR_DEG))[0]
    rear_anchor = retention_anchor(math.radians(REAR_ANCHOR_DEG))[0]
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
        "cut": "full-cut river shell: ear covers, occipital tail, integrated peak",
        "physical_cut_through_vents": vent_count,
        "ear_drainage_ports": ear_port_count,
        "rear_occipital_shell": True,
        "rim_height_cm": {"brow": RIM_PROFILE[0][1], "ear_cover": RIM_PROFILE[5][1], "occiput": RIM_PROFILE[-1][1]},
        "retention_anchor_count": 4,
        "retention_anchors_cm": {"front_left": rounded(front_anchor), "rear_left": rounded(rear_anchor)},
        "retention_straps": "fitted per wearer by unreal/Scripts/build_production_helmet_straps.py",
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
