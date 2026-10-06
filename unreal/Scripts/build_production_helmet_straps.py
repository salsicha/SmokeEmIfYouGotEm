"""Build the production helmet's retention straps, fitted to each crew head.

Run with Blender, not the system Python::

    Blender --background --python unreal/Scripts/build_production_helmet_straps.py

The shell (build_production_whitewater_helmet.py) carries the four retention
anchors. Each wearer gets their own strap set in the shell's mesh frame: a
front and a rear strap from each side's anchors down to a junction below the
ear, and one chin strap from junction to junction passing UNDER the chin with
its buckle. One shared set either cut through the deeper chins or hung loose
under the shallower ones ("the helmet chin straps should go under the chin,
not cut through it", 2026-10-05).

Each head is read from its dressed CC0 FBX and placed in the helmet frame with
the same fit the game uses (ARaftSimCC0CrewVisualActor: rendered eye centre,
per-variant anchor drop/back and shell scale; ARaftSimCrewAvatarActor:
skull-centre offset). Every strap is held a few millimetres off the skin.
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
OUTPUT_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionHelmet/Straps"
MANIFEST_PATH = OUTPUT_ROOT / "production_helmet_straps_manifest.json"
GENERATOR_VERSION = 1

# (character, anchor drop cm, anchor back cm, shell scale): the per-variant
# fit in RaftSimCC0CrewVisualActor.cpp (CrewHelmetAnchorDropsCm,
# CrewHelmetAnchorBackCm, CrewHelmetFitScale, GuideHelmet*).
FITS = [
    ("Crew01", 3.0, 5.0, 0.84),
    ("Crew02", 4.0, 5.5, 0.84),
    ("Crew03", 4.0, 5.0, 0.84),
    ("Crew04", 4.0, 5.0, 0.84),
    ("Guide", 5.0, 5.5, 0.90),
]
# kProductionHelmetSkullCenterOffsetCm and kProductionHelmetReferenceFit.
SKULL_CENTRE_OFFSET = (-2.6, 0.0, 5.7)
REFERENCE_FIT = 0.96

# Shell anchors (helmet frame, +X forward, +Y left, +Z up): the front pair at
# the temples and the rear pair behind the ears.
FRONT_ANCHOR = (6.4, 10.6, 1.5)
REAR_ANCHOR = (-7.0, 9.5, 0.0)
CLEARANCE = 0.5
STRAP_WIDTH = 1.5
STRAP_THICKNESS = 0.22


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def head_in_helmet_frame(name: str, drop: float, back: float, scale: float) -> np.ndarray:
    """The wearer's head and neck, in the fitted shell's mesh units."""
    reset_scene()
    bpy.ops.import_scene.fbx(filepath=str(CHARACTER_ROOT / f"RaftSim_CC0_{name}.fbx"))
    armature = next(obj for obj in bpy.data.objects if obj.type == "ARMATURE")
    bone = armature.data.bones["head"]
    head = armature.matrix_world @ bone.head_local * 100.0
    crown = armature.matrix_world @ bone.tail_local * 100.0
    up = (crown - head).normalized()
    forward = Vector((0.0, -1.0, 0.0))
    forward = (forward - up * forward.dot(up)).normalized()
    left = up.cross(forward)
    eyes, points = [], []
    for obj in (o for o in bpy.data.objects if o.type == "MESH"):
        eye_slots = {i for i, slot in enumerate(obj.material_slots) if slot.material and "Eyes" in slot.material.name}
        for polygon in obj.data.polygons:
            if polygon.material_index in eye_slots:
                eyes.extend(obj.matrix_world @ obj.data.vertices[i].co * 100.0 for i in polygon.vertices)
        for vertex in obj.data.vertices:
            p = obj.matrix_world @ vertex.co * 100.0
            if (p - head).length < 30.0:
                points.append(p)
    eye_centre = sum(eyes, Vector()) / len(eyes)
    lift = scale / REFERENCE_FIT
    origin = (eye_centre - up * drop - forward * back
              + forward * SKULL_CENTRE_OFFSET[0] * lift + up * SKULL_CENTRE_OFFSET[2] * lift)
    return np.array([[(p - origin).dot(forward) / scale, (p - origin).dot(left) / scale,
                      (p - origin).dot(up) / scale] for p in points])


# --- Routing ---------------------------------------------------------------

def convex_hull(points: np.ndarray) -> np.ndarray:
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
        normal = (n1 + n2) / np.linalg.norm(n1 + n2)
        result.append(b + normal * distance / max(0.3, float(np.dot(normal, n1))))
    return np.array(result)


def resample(points: np.ndarray, step: float) -> np.ndarray:
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    arc = np.concatenate([[0.0], np.cumsum(lengths)])
    samples = np.linspace(0.0, arc[-1], max(2, int(arc[-1] / step) + 1))
    return np.column_stack([np.interp(samples, arc, points[:, i]) for i in range(points.shape[1])])


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


def side_clear(head: np.ndarray, path: np.ndarray, side: float) -> np.ndarray:
    """Push each point of a side strap out over the skin beneath it."""
    out = path.copy()
    for point in out:
        near = head[(np.abs(head[:, 0] - point[0]) < 0.8) & (np.abs(head[:, 2] - point[2]) < 0.8)
                    & (head[:, 1] * side > 0)]
        if len(near):
            point[1] = side * max(abs(point[1]), float(np.abs(near[:, 1]).max()) + CLEARANCE)
    return out


def route(head: np.ndarray) -> dict[str, np.ndarray]:
    # The straps never reach below the chin; keep the chest out of the fit.
    head = head[head[:, 2] > -21.0]
    x, y, z = head.T
    # Junction below each ear lobe, outside the jaw at that height.
    jaw = (x > -2.5) & (x < 2.5) & (np.abs(z + 9.5) < 1.0)
    junction_y = float(np.abs(y[jaw]).max()) + CLEARANCE + 0.2
    junction = np.array([0.3, junction_y, -9.5])
    # The chin strap lies in the plane through both junctions and the point
    # under the chin. Its path is the offset hull of the head's section in
    # that plane, from one junction round under the chin to the other.
    under = (x > 5.5) & (x < 9.5) & (np.abs(y) < 3.0) & (z < -8.0)
    chin = np.array([7.5, 0.0, float(z[under].min()) - CLEARANCE])
    u_axis = np.array([0.0, 1.0, 0.0])
    v_axis = chin - junction * np.array([1.0, 0.0, 1.0])
    v_axis /= np.linalg.norm(v_axis)
    normal = np.cross(u_axis, v_axis)
    base = junction * np.array([1.0, 0.0, 1.0])
    rel = head - base
    slab = np.abs(rel @ normal) < 0.7
    section = np.column_stack([rel[slab] @ u_axis, rel[slab] @ v_axis])
    section = section[section[:, 1] > -1.0]
    hull = resample(np.vstack([h := offset_polygon(convex_hull(section), CLEARANCE), h[:1]]), 0.4)
    # The hull's far side (largest v) is the jaw underside: keep that arc, in
    # hull order, and close it onto the two junctions.
    far = longest_run(hull, hull[:, 1] > 0.35 * hull[:, 1].max())
    if far[0, 0] > far[-1, 0]:
        far = far[::-1]
    arc = np.vstack([[-junction_y, 0.0], far, [junction_y, 0.0]])
    chin_loop = resample(np.array([base + a * u_axis + b * v_axis for a, b in arc]), 0.6)
    straps = {"chin": chin_loop}
    for side, label in ((1.0, "left"), (-1.0, "right")):
        j = junction * np.array([1.0, side, 1.0])
        for anchor, name in ((FRONT_ANCHOR, "front"), (REAR_ANCHOR, "rear")):
            a = np.array(anchor) * np.array([1.0, side, 1.0])
            straps[f"{name}_{label}"] = side_clear(head, resample(np.array([a, j]), 0.5), side)
    straps["buckle"] = chin_loop[int(np.argmin(chin_loop[:, 2]))]
    straps["chin_point"] = chin
    return straps


# --- Geometry ----------------------------------------------------------------

def ribbon(bm: bmesh.types.BMesh, path: np.ndarray, face_normal_hint: np.ndarray, slot: int) -> None:
    """Flat webbing along a path, its face turned toward face_normal_hint."""
    points = [Vector(p) for p in path]
    rings = []
    for index, p in enumerate(points):
        a = points[max(index - 1, 0)]
        b = points[min(index + 1, len(points) - 1)]
        tangent = (b - a).normalized()
        outward = Vector(face_normal_hint(p) if callable(face_normal_hint) else face_normal_hint)
        outward = (outward - tangent * outward.dot(tangent)).normalized()
        across = tangent.cross(outward).normalized()
        hw, ht = across * (0.5 * STRAP_WIDTH), outward * (0.5 * STRAP_THICKNESS)
        rings.append([bm.verts.new(p - hw - ht), bm.verts.new(p + hw - ht),
                      bm.verts.new(p + hw + ht), bm.verts.new(p - hw + ht)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(4):
            face = bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]))
            face.material_index = slot
    for cap in (list(reversed(rings[0])), rings[-1]):
        bm.faces.new(cap).material_index = slot


def build(name: str, straps: dict[str, np.ndarray], materials) -> bpy.types.Object:
    bm = bmesh.new()
    # Side straps lie on the side of the face; the chin strap's face turns
    # away from the jaw it wraps.
    for key in ("front_left", "rear_left", "front_right", "rear_right"):
        side = 1.0 if key.endswith("left") else -1.0
        ribbon(bm, straps[key], np.array([0.0, side, 0.0]), 0)
    centre = np.array([straps["chin"][:, 0].mean(), 0.0, -4.0])
    ribbon(bm, straps["chin"], lambda p: np.array(p) - centre, 0)
    # Side-release buckle under the chin and a keeper at each junction.
    buckle = Vector(straps["buckle"])
    for centre_point, size in ((buckle + Vector((0.0, 0.0, -0.35)), (1.6, 2.4, 0.5)),):
        geom = bmesh.ops.create_cube(bm, size=1.0)
        verts = geom["verts"]
        bmesh.ops.scale(bm, vec=Vector(size), verts=verts)
        bmesh.ops.translate(bm, vec=centre_point, verts=verts)
        for face in {f for v in verts for f in v.link_faces}:
            face.material_index = 1
    for key in ("front_left", "front_right"):
        j = Vector(straps[key][-1])
        geom = bmesh.ops.create_cube(bm, size=1.0)
        verts = geom["verts"]
        bmesh.ops.scale(bm, vec=Vector((1.0, 0.35, 1.3)), verts=verts)
        bmesh.ops.translate(bm, vec=j + Vector((0.0, math.copysign(0.2, j.y), 0.0)), verts=verts)
        for face in {f for v in verts for f in v.link_faces}:
            face.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for material in materials:
        obj.data.materials.append(material)
    return obj


def clearance(head: np.ndarray, obj: bpy.types.Object) -> float:
    """Smallest distance from any strap vertex to the skin."""
    verts = np.array([tuple(v.co) for v in obj.data.vertices])
    worst = math.inf
    for v in verts:
        near = head[np.abs(head - v).max(axis=1) < 3.0]
        if len(near):
            worst = min(worst, float(np.linalg.norm(near - v, axis=1).min()))
    return worst


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    heads = {name: head_in_helmet_frame(name, drop, back, scale) for name, drop, back, scale in FITS}
    reset_scene()
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 0.01
    bpy.context.scene.unit_settings.length_unit = "CENTIMETERS"
    webbing = bpy.data.materials.new("HelmetWebbing")
    hardware = bpy.data.materials.new("HelmetHardware")
    entries = {}
    for name, head in heads.items():
        straps = route(head)
        head = head[head[:, 2] > -21.0]
        obj = build(f"SM_RaftSim_HelmetStraps_{name}", straps, [webbing, hardware])
        fbx_path = OUTPUT_ROOT / f"{obj.name}.fbx"
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.fbx(
            filepath=str(fbx_path), use_selection=True, apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_ALL", axis_forward="X", axis_up="Z",
            bake_space_transform=False, object_types={"MESH"}, use_mesh_modifiers=True,
            mesh_smooth_type="FACE", add_leaf_bones=False, path_mode="AUTO",
        )
        entries[obj.name] = {
            "fbx": fbx_path.relative_to(REPO_ROOT).as_posix(),
            "fbx_sha256": hashlib.sha256(fbx_path.read_bytes()).hexdigest(),
            "vertex_count": len(obj.data.vertices),
            "chin_point": [round(float(v), 3) for v in straps["chin_point"]],
            "min_skin_clearance_cm": round(clearance(head, obj), 3),
        }
    blend_path = OUTPUT_ROOT / "SM_RaftSim_HelmetStraps.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), compress=True)
    manifest = {
        "schema_version": 1,
        "generator": "unreal/Scripts/build_production_helmet_straps.py",
        "generator_version": GENERATOR_VERSION,
        "ownership": "Project-owned deterministic source art; no external mesh or texture input.",
        "source_inputs": [f"unreal/SourceArt/RaftSim/Characters/CC0Production/Dressed/RaftSim_CC0_{name}.fbx" for name, *_ in FITS],
        "blend": blend_path.relative_to(REPO_ROOT).as_posix(),
        "material_slots": ["HelmetWebbing", "HelmetHardware"],
        "frame": "Production helmet mesh frame: +X forward, +Y left, +Z up, shell units.",
        "fits": {name: {"anchor_drop_cm": d, "anchor_back_cm": b, "shell_scale": s} for name, d, b, s in FITS},
        "meshes": entries,
        "runtime_boundary": "Visual-only headgear; D3/D4 physics and rescue authority remain native.",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("RAFTSIM_PRODUCTION_HELMET_STRAPS=" + json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
