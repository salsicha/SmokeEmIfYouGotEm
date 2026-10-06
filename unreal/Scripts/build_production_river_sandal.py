"""Build RaftSim's project-owned river sandals in Blender.

Run with Blender, not the system Python::

    Blender --background --python unreal/Scripts/build_production_river_sandal.py

The crew paddle barefoot in river sandals: a rubber outsole and footbed held
on by a toe strap, an instep strap and a heel strap. The sandal is fitted to
the five CC0 production feet: each foot is read from its dressed FBX,
normalised by its ankle-to-ball length and ankle height, and the sole outline
and strap paths are offset just outside the union of those feet. The runtime
scales each sandal by its wearer's own ankle-to-ball length and ankle height,
so the straps sit on the foot rather than through it.

The mesh origin is the ankle (the solved foot point used by
``ARaftSimCrewAvatarActor``), +X toward the toes and +Z up, so it drops into
the same footwear slot the river boot used. Left and right sandals are
mirror images. The sandals are presentation-only: crew pose, mass, collision,
contact and rescue authority stay native.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector


REPO_ROOT = Path(__file__).resolve().parents[2]
CHARACTER_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Characters/CC0Production/Dressed"
CHARACTERS = ["RaftSim_CC0_Crew01", "RaftSim_CC0_Crew02", "RaftSim_CC0_Crew03", "RaftSim_CC0_Crew04", "RaftSim_CC0_Guide"]
OUTPUT_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionRiverSandal"
MANIFEST_PATH = OUTPUT_ROOT / "production_river_sandal_manifest.json"
GENERATOR_VERSION = 1

# Reference foot the mesh is authored for; the runtime scales by the wearer's
# own ankle-to-ball length (X, and half of it in Y) and ankle height (Z).
REFERENCE_ANKLE_TO_BALL_CM = 12.0
REFERENCE_ANKLE_HEIGHT_CM = 7.05
# The ball joint sits this far above the sole in every CC0 foot.
BALL_ABOVE_SOLE_CM = 0.88

FOOTBED_TOP = -REFERENCE_ANKLE_HEIGHT_CM - 0.05
MIDSOLE_THICKNESS = 1.05
OUTSOLE_THICKNESS = 1.0
LUG_DEPTH = 0.25
STRAP_WIDTH = 2.2
STRAP_THICKNESS = 0.32
SKIN_CLEARANCE = 0.33


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name: str, color: tuple[float, float, float, float], roughness: float):
    result = bpy.data.materials.new(name)
    result.diffuse_color = color
    result.roughness = roughness
    result.metallic = 0.0
    return result


# --- Fitting -------------------------------------------------------------

def normalised_feet() -> np.ndarray:
    """Every CC0 left foot in the ankle frame, scaled to the reference foot."""
    points = []
    for name in CHARACTERS:
        reset_scene()
        bpy.ops.import_scene.fbx(filepath=str(CHARACTER_ROOT / f"{name}.fbx"))
        armature = next(obj for obj in bpy.data.objects if obj.type == "ARMATURE")
        bones = armature.data.bones
        ankle = armature.matrix_world @ bones["foot_l"].head_local
        ball = armature.matrix_world @ bones["ball_l"].head_local
        forward = Vector((ball.x - ankle.x, ball.y - ankle.y, 0.0)).normalized()
        up = Vector((0.0, 0.0, 1.0))
        medial = forward.cross(up)
        ankle_to_ball = (ball - ankle).to_2d().length * 100.0
        ankle_height = (ankle.z - ball.z) * 100.0 + BALL_ABOVE_SOLE_CM
        sx = ankle_to_ball / REFERENCE_ANKLE_TO_BALL_CM
        sy = 0.5 * (1.0 + sx)
        sz = ankle_height / REFERENCE_ANKLE_HEIGHT_CM
        for obj in (o for o in bpy.data.objects if o.type == "MESH"):
            for vertex in obj.data.vertices:
                p = obj.matrix_world @ vertex.co
                if p.z > ankle.z + 0.09 or p.x < 0.05:
                    continue
                d = p - ankle
                f, m, u = d.dot(forward) * 100.0, d.dot(medial) * 100.0, d.dot(up) * 100.0
                if -15.0 < f < 35.0 and abs(m) < 12.0:
                    points.append((f / sx, m / sy, u / sz))
    return np.array(points)


def convex_hull(points: np.ndarray) -> np.ndarray:
    """Counter-clockwise monotone-chain hull of 2-D points."""
    pts = sorted(set(map(tuple, np.round(points, 4))))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def offset_polygon(polygon: np.ndarray, distance: float) -> np.ndarray:
    result = []
    count = len(polygon)
    for index in range(count):
        a, b, c = polygon[index - 1], polygon[index], polygon[(index + 1) % count]
        e1, e2 = b - a, c - b
        n1 = np.array([e1[1], -e1[0]]) / np.linalg.norm(e1)
        n2 = np.array([e2[1], -e2[0]]) / np.linalg.norm(e2)
        normal = n1 + n2
        normal /= np.linalg.norm(normal)
        result.append(b + normal * distance / max(0.3, float(np.dot(normal, n1))))
    return np.array(result)


def resample(polygon: np.ndarray, step: float, closed: bool = True) -> np.ndarray:
    pts = np.vstack([polygon, polygon[:1]]) if closed else polygon
    lengths = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    arc = np.concatenate([[0.0], np.cumsum(lengths)])
    samples = np.arange(0.0, arc[-1], step)
    return np.column_stack([np.interp(samples, arc, pts[:, i]) for i in range(pts.shape[1])])


def longest_run(polygon: np.ndarray, keep: np.ndarray) -> np.ndarray:
    """The longest contiguous stretch of a closed polygon where keep holds."""
    count = len(polygon)
    start = int(np.argmin(keep))
    runs, current = [], []
    for offset in range(1, count + 1):
        index = (start + offset) % count
        if keep[index]:
            current.append(index)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    return polygon[max(runs, key=len)]


def fit_to_feet() -> dict[str, np.ndarray]:
    feet = normalised_feet()
    f, m, u = feet.T
    sole = -REFERENCE_ANKLE_HEIGHT_CM
    low = u < sole + 4.5
    outline = resample(offset_polygon(convex_hull(np.column_stack([f[low], m[low]])), 0.7), 0.8)

    def cross_strap(x: float) -> np.ndarray:
        near = (np.abs(f - x) < 0.8) & (u < sole + 6.5)
        section = resample(offset_polygon(convex_hull(np.column_stack([m[near], u[near]])), SKIN_CLEARANCE), 0.5)
        over = longest_run(section, section[:, 1] > sole + 1.0)
        # Run from the lateral edge over the top to the medial edge, then drop
        # each end straight into the sole at the outline.
        if over[0, 0] > over[-1, 0]:
            over = over[::-1]
        edge = outline[np.abs(outline[:, 0] - x) < 0.8, 1]
        lateral, medial = float(edge.min()) + 0.35, float(edge.max()) - 0.35
        path = [(x, lateral, FOOTBED_TOP - 0.6), (x, lateral, sole + 0.4)]
        path += [(x, float(mm), float(uu)) for mm, uu in over]
        path += [(x, medial, sole + 0.4), (x, medial, FOOTBED_TOP - 0.6)]
        return np.array(path)

    heel_z = sole + 3.2
    band = (np.abs(u - heel_z) < 0.6) & (f < 8.0)
    ring = resample(offset_polygon(convex_hull(np.column_stack([f[band], m[band]])), SKIN_CLEARANCE), 0.5)
    heel = longest_run(ring, ring[:, 0] < 5.5)
    heel = np.column_stack([heel[:, 0], heel[:, 1], np.full(len(heel), heel_z)])
    return {
        "outline": outline,
        "toe": cross_strap(12.0),
        "instep": cross_strap(5.5),
        "heel": heel,
        "foot_points": len(feet),
    }


# --- Geometry --------------------------------------------------------------

def mesh_object(name: str, bm: bmesh.types.BMesh, assigned_material) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(assigned_material)
    return obj


def slab(name: str, outline: np.ndarray, bottom: float, top: float, assigned_material) -> bpy.types.Object:
    bm = bmesh.new()
    low = [bm.verts.new((float(x), float(y), bottom)) for x, y in outline]
    high = [bm.verts.new((float(x), float(y), top)) for x, y in outline]
    bm.faces.new(list(reversed(low)))
    bm.faces.new(high)
    count = len(outline)
    for index in range(count):
        j = (index + 1) % count
        bm.faces.new((low[index], low[j], high[j], high[index]))
    bm.normal_update()
    obj = mesh_object(name, bm, assigned_material)
    bevel = obj.modifiers.new("Rounded", "BEVEL")
    bevel.width = min(0.35, 0.3 * (top - bottom))
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    return obj


def ribbon(name: str, path: np.ndarray, width_axis: Vector, assigned_material) -> bpy.types.Object:
    """Flat webbing along a path; width along width_axis, thickness outward."""
    points = [Vector(p) for p in path]
    bm = bmesh.new()
    rings = []
    for index, p in enumerate(points):
        a = points[max(index - 1, 0)]
        b = points[min(index + 1, len(points) - 1)]
        tangent = (b - a).normalized()
        across = (width_axis - tangent * width_axis.dot(tangent)).normalized()
        outward = tangent.cross(across).normalized()
        half_w, half_t = across * (0.5 * STRAP_WIDTH), outward * (0.5 * STRAP_THICKNESS)
        rings.append([
            bm.verts.new(p - half_w - half_t),
            bm.verts.new(p + half_w - half_t),
            bm.verts.new(p + half_w + half_t),
            bm.verts.new(p - half_w + half_t),
        ])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_object(name, bm, assigned_material)


def box(name: str, center, size, assigned_material) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return mesh_object(name, bm, assigned_material)


def build_left_sandal(fit: dict[str, np.ndarray], materials: dict[str, bpy.types.Material]) -> bpy.types.Object:
    # Blender +Y is the wearer's left: a left foot's medial (big-toe) side is -Y.
    outline = np.column_stack([fit["outline"][:, 0], -fit["outline"][:, 1]])
    outsole_bottom = FOOTBED_TOP - MIDSOLE_THICKNESS - OUTSOLE_THICKNESS
    parts = [
        slab("Outsole", outline, outsole_bottom, FOOTBED_TOP - MIDSOLE_THICKNESS, materials["SandalSole"]),
        slab("Footbed", outline * 0.995, FOOTBED_TOP - MIDSOLE_THICKNESS - 0.05, FOOTBED_TOP, materials["SandalFootbed"]),
    ]
    # Chevron tread lugs across the outsole.
    lugs = 0
    for x in np.arange(-4.5, 18.5, 2.4):
        edge = outline[np.abs(outline[:, 0] - x) < 0.9, 1]
        if len(edge) < 2:
            continue
        inner = 0.5 * (edge.max() - edge.min()) - 1.0
        center = 0.5 * (edge.max() + edge.min())
        for side in (-1.0, 1.0):
            parts.append(box(
                f"Lug_{lugs:02d}",
                (float(x), float(center + side * inner * 0.5), outsole_bottom - 0.5 * LUG_DEPTH),
                (0.8, float(inner) * 0.85, LUG_DEPTH),
                materials["SandalSole"],
            ))
            lugs += 1

    def mirrored(path: np.ndarray) -> np.ndarray:
        return np.column_stack([path[:, 0], -path[:, 1], path[:, 2]])

    parts.append(ribbon("ToeStrap", mirrored(fit["toe"]), Vector((1.0, 0.0, 0.0)), materials["SandalStrap"]))
    parts.append(ribbon("InstepStrap", mirrored(fit["instep"]), Vector((1.0, 0.0, 0.0)), materials["SandalStrap"]))
    parts.append(ribbon("HeelStrap", mirrored(fit["heel"]), Vector((0.0, 0.0, 1.0)), materials["SandalStrap"]))
    # Ladder-lock buckle on the outside of the instep strap, and a
    # hook-and-loop tab over the top of it.
    instep = mirrored(fit["instep"])
    outer = instep[np.argmax(instep[:, 1])]
    top = instep[np.argmax(instep[:, 2])]
    parts.append(box("Buckle", (outer[0], outer[1] + 0.25, outer[2] + 0.4), (2.6, 0.35, 1.6), materials["SandalHardware"]))
    parts.append(box("InstepTab", (top[0], top[1], top[2] + 0.22), (2.5, 2.8, 0.2), materials["SandalStrap"]))

    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    sandal = bpy.context.object
    # Material slot order is the import contract.
    order = ["SandalSole", "SandalFootbed", "SandalStrap", "SandalHardware"]
    current = [slot.material.name.split(".")[0] if slot.material else "" for slot in sandal.material_slots]
    # Clearing the slots resets every face to slot 0, so read faces first.
    face_slots = [order.index(current[polygon.material_index]) for polygon in sandal.data.polygons]
    sandal.data.materials.clear()
    for name in order:
        sandal.data.materials.append(materials[name])
    for polygon, slot in zip(sandal.data.polygons, face_slots):
        polygon.material_index = slot
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40.0))
    return sandal, lugs


def export(obj: bpy.types.Object, path: Path) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(path),
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


def bounds(obj: bpy.types.Object) -> dict[str, list[float]]:
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return {
        "min": [round(min(c[i] for c in corners), 4) for i in range(3)],
        "max": [round(max(c[i] for c in corners), 4) for i in range(3)],
    }


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    fit = fit_to_feet()
    reset_scene()
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 0.01
    bpy.context.scene.unit_settings.length_unit = "CENTIMETERS"
    materials = {
        "SandalSole": material("SandalSole", (0.004, 0.006, 0.008, 1.0), 0.86),
        "SandalFootbed": material("SandalFootbed", (0.030, 0.026, 0.022, 1.0), 0.8),
        "SandalStrap": material("SandalStrap", (0.010, 0.015, 0.020, 1.0), 0.7),
        "SandalHardware": material("SandalHardware", (0.02, 0.02, 0.02, 1.0), 0.5),
    }
    left, lugs = build_left_sandal(fit, materials)
    left.name = "SM_RaftSim_RiverSandal_L"
    right = left.copy()
    right.data = left.data.copy()
    right.name = "SM_RaftSim_RiverSandal_R"
    bpy.context.scene.collection.objects.link(right)
    right.scale = (1.0, -1.0, 1.0)
    bpy.ops.object.select_all(action="DESELECT")
    right.select_set(True)
    bpy.context.view_layer.objects.active = right
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    blend_path = OUTPUT_ROOT / "SM_RaftSim_RiverSandal.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), compress=True)
    entries = {}
    for obj in (left, right):
        fbx_path = OUTPUT_ROOT / f"{obj.name}.fbx"
        export(obj, fbx_path)
        entries[obj.name] = {
            "fbx": fbx_path.relative_to(REPO_ROOT).as_posix(),
            "fbx_sha256": hashlib.sha256(fbx_path.read_bytes()).hexdigest(),
            "vertex_count": len(obj.data.vertices),
            "polygon_count": len(obj.data.polygons),
            "bounds_cm": bounds(obj),
        }
    manifest = {
        "schema_version": 1,
        "generator": "unreal/Scripts/build_production_river_sandal.py",
        "generator_version": GENERATOR_VERSION,
        "ownership": "Project-owned deterministic source art; no external mesh or texture input.",
        "license": "RaftSim project source license",
        "source_inputs": [f"unreal/SourceArt/RaftSim/Characters/CC0Production/Dressed/{name}.fbx" for name in CHARACTERS],
        "blend": blend_path.relative_to(REPO_ROOT).as_posix(),
        "material_slots": ["SandalSole", "SandalFootbed", "SandalStrap", "SandalHardware"],
        "meshes": entries,
        "fit": {
            "reference_ankle_to_ball_cm": REFERENCE_ANKLE_TO_BALL_CM,
            "reference_ankle_height_cm": REFERENCE_ANKLE_HEIGHT_CM,
            "ball_above_sole_cm": BALL_ABOVE_SOLE_CM,
            "skin_clearance_cm": SKIN_CLEARANCE,
            "fitted_foot_points": int(fit["foot_points"]),
        },
        "construction": {"straps": ["toe", "instep", "heel"], "outsole_lugs": lugs, "buckles": 1},
        "runtime_boundary": "Visual-only river footwear; crew pose, mass, D3/D4 physics, collision and rescue authority remain native.",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("RAFTSIM_PRODUCTION_RIVER_SANDAL=" + json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
