"""Dress a CC0 crew body in its own river clothes instead of the wetsuit.

The MPFB bodies carry no garments: their "Wetsuit" slot is the bare body
surface from the neck to the toes, so all five crew read as one black suit.
This post-process (stock Blender, no MPFB) builds two skinned garment shells
per person -- a top and a bottom -- from the body surface itself:

- the body faces under each garment are copied, cut along bone-relative
  planes (neckline, hems, sleeve and leg openings) with Blender's bisect,
  which interpolates the skin weights on the new edges, so every opening is
  a clean loop rather than the body's per-face saw-tooth;
- the copy is pushed out along the rest-pose normals (snug on the torso,
  flaring toward loose hems) and solidified to fabric thickness;
- body faces fully under a garment take the garment's slot (anything that
  pokes through while posed shows the same fabric), and the rest of the
  former wetsuit -- forearms, lower legs, feet -- becomes skin;
- a top's collar closes in to hug the neck, and its skin weights are
  smoothed round the neckline so the collar moves as one band.

The shells keep the body's skeleton and weights, so the poseable mesh drives
them like the body. One correction to those weights: the seat's midline
takes the thigh share of the buttocks beside it, so it does not stay behind
them when the crew sits (see _fill_seat_thigh_share). Run from Blender::

    blender --background --python build_cc0_river_clothing.py -- \
      --input RaftSim_CC0_Crew01.fbx --output dressed.fbx --variant Crew01 \
      --manifest outfit.json [--preview preview.png]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

GENERATOR_VERSION = 4

# Sides: MPFB's game_engine rig puts the character's left at +X; the front
# faces -Y; metres, rest pose standing in an A-pose.
SIDES = ("l", "r")

# Per person: the garment cut and fit. Offsets are metres along the rest
# normal; "flare" is added over the last FlareLength before a loose hem.
OUTFITS = {
    # Rhys, head guide: long-sleeved sun shirt (UPF), quick-dry shorts.
    "Guide": {
        "top": {"name": "long-sleeved sun shirt", "neck": "crew", "sleeve": ("lowerarm", 0.86),
                "hem_z": 0.955, "offset": 0.011, "sleeve_offset": 0.012, "flare": 0.010},
        "bottom": {"name": "quick-dry shorts", "leg": ("thigh", 0.74), "waist_z": 1.035,
                   "offset": 0.007, "flare": 0.020},
    },
    # Kwame: loose short-sleeved T-shirt, knee-length board shorts.
    "Crew01": {
        "top": {"name": "loose T-shirt", "neck": "crew", "sleeve": ("upperarm", 0.58),
                "hem_z": 0.935, "offset": 0.013, "sleeve_offset": 0.016, "flare": 0.022},
        "bottom": {"name": "board shorts", "leg": ("thigh", 0.97), "waist_z": 1.025,
                   "offset": 0.008, "flare": 0.034},
    },
    # Kenji: T-shirt, knee-length walking shorts.
    "Crew02": {
        "top": {"name": "T-shirt", "neck": "crew", "sleeve": ("upperarm", 0.50),
                "hem_z": 0.945, "offset": 0.011, "sleeve_offset": 0.013, "flare": 0.016},
        "bottom": {"name": "walking shorts", "leg": ("thigh", 0.88), "waist_z": 1.04,
                   "offset": 0.007, "flare": 0.024},
    },
    # Ingrid: sleeveless athletic top, three-quarter leggings.
    "Crew03": {
        "top": {"name": "sleeveless athletic top", "neck": "crew", "sleeve": ("upperarm", -1.0),
                "hem_z": 0.95, "offset": 0.005, "sleeve_offset": 0.005, "flare": 0.0},
        "bottom": {"name": "three-quarter leggings", "leg": ("calf", 0.42), "waist_z": 1.03,
                   "offset": 0.0035, "flare": 0.0},
    },
    # Amara: oversized T-shirt, mid-thigh shorts.
    "Crew04": {
        "top": {"name": "oversized T-shirt", "neck": "crew", "sleeve": ("upperarm", 0.62),
                "hem_z": 0.925, "offset": 0.014, "sleeve_offset": 0.017, "flare": 0.020},
        "bottom": {"name": "running shorts", "leg": ("thigh", 0.50), "waist_z": 1.03,
                   "offset": 0.006, "flare": 0.016},
    },
}

# Tops relax more: shirt fabric hangs off the chest instead of showing it.
SMOOTH_PASSES = {"top": 14, "bottom": 6}
FABRIC_THICKNESS = 0.0035
TIGHT_FABRIC_THICKNESS = 0.0015
# A body face takes a garment's slot only when it lies this far inside the
# garment's cuts, so the saw-tooth slot boundary stays under the shell.
COVER_MARGIN = 0.012
PREVIEW_COLOURS = {"top": (0.55, 0.62, 0.68, 1.0), "bottom": (0.30, 0.31, 0.24, 1.0)}
# The seat midline whose thigh share is filled in from the buttocks beside
# it (metres): half-width about the midline, extent below and above the hip
# joints, the neighbourhood each pass averages over, the number of passes,
# and the height over which the change fades out at the top and bottom.
SEAT_FILL = {"half_width": 0.05, "below": 0.16, "above": 0.04, "radius": 0.035, "passes": 25, "fade": 0.03}
# A top's collar (metres): the band below the neckline that closes in on the
# neck, the shell's offset at the neckline itself (just over the fabric's
# thickness, which solidify lays inward), and the weight-smoothing passes.
COLLAR_BAND = 0.04
COLLAR_OFFSET = FABRIC_THICKNESS + 0.002
COLLAR_WEIGHT_BAND = 0.02
COLLAR_WEIGHT_PASSES = 6
# Body faces right under the snug collar wear the shirt, so skin that moves
# through the collar band while posed reads as fabric (the general
# COVER_MARGIN left a ring of skin there that showed through in patches).
NECKLINE_COVER_MARGIN = 0.002
MAX_INFLUENCES = 4


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--variant", required=True, choices=sorted(OUTFITS))
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--preview")
    script_args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(script_args)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Bones:
    """Rest-pose bone segments in the mesh's frame (metres)."""

    def __init__(self, rig: bpy.types.Object):
        world = rig.matrix_world
        self.head = {bone.name: world @ bone.head_local for bone in rig.data.bones}
        self.tail = {bone.name: world @ bone.tail_local for bone in rig.data.bones}

    def point(self, name: str, t: float) -> Vector:
        return self.head[name].lerp(self.tail[name], t)

    def axis(self, name: str) -> Vector:
        return (self.tail[name] - self.head[name]).normalized()


def _limb_bones(side: str) -> dict[str, set[str]]:
    fingers = {f"{digit}_0{i}_{side}" for digit in ("thumb", "index", "middle", "ring", "pinky")
               for i in (1, 2, 3)}
    return {
        "arm": {f"clavicle_{side}", f"upperarm_{side}", f"lowerarm_{side}", f"hand_{side}"} | fingers,
        "leg": {f"thigh_{side}", f"calf_{side}", f"foot_{side}", f"ball_{side}"},
    }


# Which faces a garment may keep before its cuts. Only the planes trim: a
# face filter at a garment edge would leave the body's per-face saw-tooth
# (head-weighted faces reach down the neck, thigh-weighted faces up the
# hips). The filter only drops parts a plane cannot separate: the hanging
# A-pose hands for the top, the arms beside the hips for the bottom.
HAND_BONES = {name for side in SIDES for name in _limb_bones(side)["arm"]
              if not name.startswith(("clavicle", "upperarm", "lowerarm"))}
ARM_BONES = {name for side in SIDES for name in _limb_bones(side)["arm"]}


class Garment:
    """One garment's region: a bone set and the half-spaces that bound it."""

    def __init__(self, kind: str, spec: dict, bones: Bones):
        self.kind = kind
        self.spec = spec
        self.excluded = HAND_BONES if kind == "top" else ARM_BONES | {"head", "neck_01"}
        # A top's neckline plane (point, outward normal); None for a bottom.
        self.neckline: tuple[Vector, Vector] | None = None
        # A top hangs over the bottom garment's waistband (set by main()).
        self.under_waist_z: float | None = None
        self.under_offset = 0.0
        # (plane point, outward normal, bone filter or None): geometry on the
        # normal's side is outside the garment.
        self.cuts: list[tuple[Vector, Vector, set[str] | None]] = []
        # Planes whose nearby open edge flares (loose hems): point, normal,
        # bone filter, extra offset at the hem, ramp length up from the hem.
        self.hems: list[tuple[Vector, Vector, set[str] | None, float, float]] = []
        flare = spec["flare"]
        if kind == "top":
            # A crew neckline, lower in front than behind. (A flat plane
            # cannot cut a scoop and keep shoulder straps: a scoop deep
            # enough to read would also take the shoulders.)
            neck_base = bones.head["neck_01"]
            neckline = (Vector((0.0, neck_base.y, neck_base.z - 0.016)), Vector((0.0, -0.45, 1.0)))
            self.cuts.append((neckline[0], neckline[1].normalized(), None))
            self.neckline = (neckline[0], neckline[1].normalized())
            hem = (Vector((0.0, 0.0, spec["hem_z"])), Vector((0.0, 0.0, -1.0)))
            self.cuts.append((hem[0], hem[1], None))
            self.hems.append((hem[0], hem[1], None, flare * 0.6, 0.12))
            bone, t = spec["sleeve"]
            for side in SIDES:
                arm = _limb_bones(side)["arm"]
                name = f"{bone}_{side}"
                axis = bones.axis(name)
                if t < 0.0:
                    # Sleeveless: the armhole rises from the armpit to a
                    # strap about 60 % along the collarbone, leaving the
                    # deltoid bare. The plane leans outward going down, so
                    # it clears the torso's side and needs no bone filter;
                    # filtering it to arm faces left a step where the
                    # shoulder's faces meet the chest's.
                    outward = 1.0 if side == "l" else -1.0
                    normal = Vector((outward, 0.0, 0.35)).normalized()
                    point = bones.point(f"clavicle_{side}", 0.62)
                    self.cuts.append((point, normal, None))
                    continue
                normal = axis
                point = bones.point(name, t)
                self.cuts.append((point, normal, arm))
                self.hems.append((point, normal, arm, flare, 0.10))
        else:
            waist = (Vector((0.0, 0.0, spec["waist_z"])), Vector((0.0, 0.10, 1.0)).normalized())
            self.cuts.append((waist[0], waist[1], None))
            bone, t = spec["leg"]
            for side in SIDES:
                leg = _limb_bones(side)["leg"]
                name = f"{bone}_{side}"
                point = bones.point(name, t)
                normal = bones.axis(name)
                self.cuts.append((point, normal, leg))
                # Shorts hang straight from the seat: the leg widens over
                # its whole length rather than belling at the hem.
                self.hems.append((point, normal, leg, flare, 0.32))

    def inside(self, position: Vector, dominant: str, margin: float) -> bool:
        if dominant in self.excluded or not dominant:
            return False
        for point, normal, bone_filter in self.cuts:
            if bone_filter is not None and dominant not in bone_filter:
                continue
            cut_margin = NECKLINE_COVER_MARGIN if self.neckline is not None and point is self.neckline[0] else margin
            if (position - point).dot(normal) > -cut_margin:
                return False
        return True


def _vertex_weights(mesh: bpy.types.Object) -> list[dict[str, float]]:
    names = {group.index: group.name for group in mesh.vertex_groups}
    return [
        {names[g.group]: g.weight for g in vertex.groups if g.weight > 1.0e-6}
        for vertex in mesh.data.vertices
    ]


def _face_dominant_bones(mesh: bpy.types.Object, weights: list[dict[str, float]]) -> list[str]:
    dominant = []
    for polygon in mesh.data.polygons:
        totals: dict[str, float] = {}
        for index in polygon.vertices:
            for name, weight in weights[index].items():
                totals[name] = totals.get(name, 0.0) + weight
        dominant.append(max(totals, key=totals.get) if totals else "")
    return dominant


def _material_index(mesh: bpy.types.Object, term: str) -> int:
    found = [i for i, m in enumerate(mesh.data.materials) if m is not None and term in m.name.casefold()]
    if len(found) != 1:
        raise RuntimeError(f"Expected one {term} material on {mesh.name}; found {found}")
    return found[0]


def _new_material(name: str, colour: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = colour
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = colour
        principled.inputs["Roughness"].default_value = 0.85
    return material


def _build_shell(body: bpy.types.Object, garment: Garment, dominant: list[str],
                 body_slots: set[int], material: bpy.types.Material) -> tuple[bpy.types.Object, dict]:
    shell = body.copy()
    shell.data = body.data.copy()
    shell.name = f"{body.name}_{garment.kind}"
    bpy.context.collection.objects.link(shell)

    bm = bmesh.new()
    bm.from_mesh(shell.data)
    bm.faces.ensure_lookup_table()
    # Keep each face's dominant bone through the cuts: split faces copy it.
    bone_names = sorted(set(dominant))
    bone_layer = bm.faces.layers.int.new("raftsim_dominant_bone")
    for face in bm.faces:
        face[bone_layer] = bone_names.index(dominant[face.index])
    remove = [f for f in bm.faces
              if f.material_index not in body_slots or bone_names[f[bone_layer]] in garment.excluded]
    bmesh.ops.delete(bm, geom=remove, context="FACES")

    for point, normal, bone_filter in garment.cuts:
        faces = [f for f in bm.faces
                 if bone_filter is None or bone_names[f[bone_layer]] in bone_filter]
        if not faces:
            continue
        edges = {e for f in faces for e in f.edges}
        verts = {v for f in faces for v in f.verts}
        bmesh.ops.bisect_plane(bm, geom=list(verts) + list(edges) + faces, dist=1.0e-6,
                               plane_co=point, plane_no=normal, clear_outer=True)
    # Cuts can strand slivers that no longer touch the garment.
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    islands = _islands(bm)
    if len(islands) > 1:
        largest = max(islands, key=len)
        bmesh.ops.delete(bm, geom=[f for island in islands if island is not largest for f in island],
                         context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")

    # The collar hugs the neck: within COLLAR_BAND of the neckline the shell
    # closes in to just over the fabric's thickness, and its skin weights are
    # smoothed round and across the band. Pushed out a full offset, the
    # collar stood off the neck and from above showed a dark trench behind
    # it; and the cut edge mixed neck and spine weights vertex by vertex, so
    # with the head bowed the collar went saw-toothed ("the crew necks
    # aren't attached to the back, there is a gap where the spine would
    # be", 2026-10-07).
    collar: dict = {}
    if garment.neckline is not None:
        point, normal = garment.neckline
        for vertex in bm.verts:
            depth = -(vertex.co - point).dot(normal)
            if depth < COLLAR_BAND:
                collar[vertex] = max(depth, 0.0)
        deform = bm.verts.layers.deform.active
        if deform is not None:
            edge = {vertex: depth for vertex, depth in collar.items() if depth < COLLAR_WEIGHT_BAND}
            _smooth_weights(edge, deform, COLLAR_WEIGHT_PASSES)

    bm.normal_update()
    spec = garment.spec
    rest = {vertex: (vertex.co.copy(), vertex.normal.copy()) for vertex in bm.verts}
    minimum = {}
    for vertex in bm.verts:
        bone = _vertex_bone(vertex, bone_layer, bone_names)
        offset = spec["offset"]
        if bone in _limb_bones("l")["arm"] | _limb_bones("r")["arm"]:
            offset = spec.get("sleeve_offset", offset)
        extra = 0.0
        for point, normal, bone_filter, flare, length in garment.hems:
            if flare <= 0.0 or (bone_filter is not None and bone not in bone_filter):
                continue
            distance = (vertex.co - point).dot(normal)  # <= 0 inside
            ramp = max(0.0, min(1.0, 1.0 + distance / length))
            extra = max(extra, flare * ramp * ramp * (3.0 - 2.0 * ramp))
        push = offset + extra
        if vertex in collar:
            push = COLLAR_OFFSET + (push - COLLAR_OFFSET) * _smoothstep(collar[vertex] / COLLAR_BAND)
        vertex.co += vertex.normal * push
        # Relaxing below pulls the shell back in on convex body parts; keep
        # most of the offset, and over the bottom garment's waistband keep
        # the top clear of it.
        floor = min(0.6 * offset, push)
        if garment.under_waist_z is not None and vertex.co.z < garment.under_waist_z + 0.02:
            floor = max(floor, garment.under_offset + FABRIC_THICKNESS + 0.003)
        minimum[vertex] = floor
    # Cloth bridges the body's hollows (between the pectorals, the navel,
    # the small of the back) instead of shrink-wrapping them. Relax the
    # shell's interior a few passes; the hem loops stay on their cut planes.
    # Second-skin garments are not relaxed: smoothing pulls the shell in on
    # convex muscle (the calf) and the skin pokes through.
    tight = spec["offset"] < 0.006
    interior = [v for v in bm.verts if not v.is_boundary]
    for _ in range(0 if tight else SMOOTH_PASSES[garment.kind]):
        bmesh.ops.smooth_vert(bm, verts=interior, factor=0.5,
                              use_axis_x=True, use_axis_y=True, use_axis_z=True)
    for vertex, (origin, normal) in rest.items():
        clearance = (vertex.co - origin).dot(normal)
        if clearance < minimum[vertex]:
            vertex.co += normal * (minimum[vertex] - clearance)
    bm.faces.layers.int.remove(bone_layer)
    open_edges = sum(1 for e in bm.edges if e.is_boundary)
    bm.to_mesh(shell.data)
    bm.free()

    shell.data.materials.clear()
    shell.data.materials.append(material)
    for polygon in shell.data.polygons:
        polygon.material_index = 0
    solidify = shell.modifiers.new("Fabric", "SOLIDIFY")
    solidify.thickness = TIGHT_FABRIC_THICKNESS if tight else FABRIC_THICKNESS
    solidify.offset = -1.0
    solidify.use_even_offset = True
    solidify.use_rim = True
    # Solidify must run before the armature deform it would otherwise follow.
    shell.modifiers.move(len(shell.modifiers) - 1, 0)
    bpy.ops.object.select_all(action="DESELECT")
    shell.select_set(True)
    bpy.context.view_layer.objects.active = shell
    bpy.ops.object.modifier_apply(modifier=solidify.name)
    strays = _return_strays_to_body(shell, body, spec)
    return shell, {"name": spec["name"], "faces": len(shell.data.polygons),
                   "vertices": len(shell.data.vertices), "open_edges": open_edges,
                   "stray_vertices_returned_to_body": strays}


def _return_strays_to_body(shell: bpy.types.Object, body: bpy.types.Object, spec: dict) -> int:
    """Put back on the body any shell vertex standing further off it than the
    garment allows; returns how many moved.

    Even-thickness solidify divides by the angle between neighbouring faces,
    so where a second-skin shell folds sharply it can throw a vertex far off
    the body: one at the gluteal cleft of Ingrid's leggings stood 10 cm behind
    the seat and, seated, stuck out behind her ("something sticking out of
    their butt", 2026-10-05). The shell is a copy of the body object, so both
    meshes share one local frame.
    """
    body_bm = bmesh.new()
    body_bm.from_mesh(body.data)
    surface = BVHTree.FromBMesh(body_bm)
    limit = (spec["offset"] + spec.get("flare", 0.0) +
             max(0.0, spec.get("sleeve_offset", 0.0) - spec["offset"]) + FABRIC_THICKNESS + 0.02)
    strays = 0
    for vertex in shell.data.vertices:
        location, normal, _, distance = surface.find_nearest(vertex.co)
        if location is not None and distance > limit:
            vertex.co = location + normal * spec["offset"]
            strays += 1
    body_bm.free()
    shell.data.update()
    return strays


def _smoothstep(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _smooth_weights(region: dict, deform, passes: int) -> None:
    """Average each region vertex's skin weights with its edge neighbours'
    (neighbours outside the region anchor it), keeping the strongest
    MAX_INFLUENCES and renormalising."""
    for _ in range(passes):
        updated = {}
        for vertex in region:
            neighbours = [edge.other_vert(vertex) for edge in vertex.link_edges]
            if not neighbours:
                continue
            mixed: dict[int, float] = {}
            for group, weight in vertex[deform].items():
                mixed[group] = mixed.get(group, 0.0) + 0.5 * weight
            for neighbour in neighbours:
                for group, weight in neighbour[deform].items():
                    mixed[group] = mixed.get(group, 0.0) + 0.5 * weight / len(neighbours)
            strongest = sorted(mixed.items(), key=lambda item: -item[1])[:MAX_INFLUENCES]
            total = sum(weight for _, weight in strongest)
            if total > 0.0:
                updated[vertex] = [(group, weight / total) for group, weight in strongest]
        for vertex, weights in updated.items():
            layer = vertex[deform]
            layer.clear()
            for group, weight in weights:
                layer[group] = weight


def _fill_seat_thigh_share(mesh: bpy.types.Object, bones: Bones) -> int:
    """Give the seat's midline the thigh share of the buttocks beside it;
    returns how many vertices changed.

    Seated, the thighs swing forward about the hips and each vertex goes with
    them by its thigh share. MPFB weights the gluteal cleft and the perineum
    almost wholly to the pelvis (thigh share 0.1-0.2) while the buttocks a
    few centimetres either side carry 0.3-0.8. So seated, the buttocks roll
    forward and the midline stays behind them: on every crew body the cleft
    stood 2-4 cm proud of the buttocks at the seat, a fin of fabric "sticking
    out of their butts" (2026-10-06). Each pass raises a midline vertex's
    thigh share to the mean of its neighbours' (never lowers it), so the
    valley fills from the buttocks inward. The share is split between the
    thighs by side, and the vertex's other weights scale down to make room.
    """
    spec = SEAT_FILL
    hip_z = 0.5 * (bones.head["thigh_l"].z + bones.head["thigh_r"].z)
    names = {group.index: group.name for group in mesh.vertex_groups}
    groups = {group.name: group for group in mesh.vertex_groups}
    margin = spec["radius"] + spec["fade"]
    weights: dict[int, dict[str, float]] = {}
    for vertex in mesh.data.vertices:
        height = vertex.co.z - hip_z
        if abs(vertex.co.x) < spec["half_width"] + margin and -spec["below"] - margin < height < spec["above"] + margin:
            weight = {names[g.group]: g.weight for g in vertex.groups if g.weight > 1.0e-6}
            total = sum(weight.values())
            if total > 0.0:
                weights[vertex.index] = {name: value / total for name, value in weight.items()}
    vertices = mesh.data.vertices
    tree = KDTree(len(weights))
    for index in weights:
        tree.insert(vertices[index].co, index)
    tree.balance()
    share = {index: w.get("thigh_l", 0.0) + w.get("thigh_r", 0.0) for index, w in weights.items()}
    region = [index for index in weights if abs(vertices[index].co.x) < spec["half_width"]
              and -spec["below"] < vertices[index].co.z - hip_z < spec["above"]]
    neighbours = {index: [other for _, other, distance in tree.find_range(vertices[index].co, spec["radius"])
                          if other != index and distance > 0.0005] for index in region}
    filled = dict(share)
    for _ in range(spec["passes"]):
        step = dict(filled)
        for index in region:
            if neighbours[index]:
                mean = sum(filled[other] for other in neighbours[index]) / len(neighbours[index])
                step[index] = max(filled[index], mean)
        filled = step
    changed = 0
    for index in region:
        co = vertices[index].co
        height = co.z - hip_z
        fade = _smoothstep(min((height + spec["below"]) / spec["fade"], (spec["above"] - height) / spec["fade"]))
        target = share[index] + (filled[index] - share[index]) * fade
        if target - share[index] < 0.005:
            continue
        # Only the added share is split by side, so a thigh vertex near the
        # midline keeps its own thigh's weight and takes little of the other.
        gain = target - share[index]
        left = _smoothstep(0.5 + co.x / spec["half_width"])
        others = {name: value for name, value in weights[index].items() if name not in ("thigh_l", "thigh_r")}
        rest = sum(others.values())
        for name, value in others.items():
            groups[name].add([index], value * (1.0 - target) / rest if rest > 0.0 else 0.0, "REPLACE")
        groups["thigh_l"].add([index], weights[index].get("thigh_l", 0.0) + gain * left, "REPLACE")
        groups["thigh_r"].add([index], weights[index].get("thigh_r", 0.0) + gain * (1.0 - left), "REPLACE")
        changed += 1
    return changed


def _vertex_bone(vertex, layer, bone_names) -> str:
    counts: dict[str, int] = {}
    for face in vertex.link_faces:
        name = bone_names[face[layer]]
        counts[name] = counts.get(name, 0) + 1
    return max(counts, key=counts.get) if counts else ""


def _islands(bm) -> list[list]:
    seen: set = set()
    islands = []
    for start in bm.faces:
        if start in seen:
            continue
        island = []
        stack = [start]
        seen.add(start)
        while stack:
            face = stack.pop()
            island.append(face)
            for edge in face.edges:
                for other in edge.link_faces:
                    if other not in seen:
                        seen.add(other)
                        stack.append(other)
        islands.append(island)
    return islands


def _render_preview(path: Path, objects: list[bpy.types.Object]) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1000
    scene.render.film_transparent = False
    camera_data = bpy.data.cameras.new("PreviewCamera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 2.05
    camera = bpy.data.objects.new("PreviewCamera", camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    shots = []
    for label, location, rotation, scale in (
            ("front", (0.0, -4.0, 0.92), (math.radians(90), 0.0, 0.0), 2.05),
            ("side", (4.0, 0.0, 0.92), (math.radians(90), 0.0, math.radians(90)), 2.05),
            ("torso", (-2.4, -3.2, 1.30), (math.radians(90), 0.0, math.radians(-37)), 0.80),
            ("legs", (2.4, -3.2, 0.62), (math.radians(90), 0.0, math.radians(37)), 0.95)):
        camera_data.ortho_scale = scale
        camera.location = location
        camera.rotation_euler = rotation
        shot = path.with_name(f"{path.stem}_{label}{path.suffix}")
        scene.render.filepath = str(shot)
        bpy.ops.render.render(write_still=True)
        shots.append(shot)
    bpy.data.objects.remove(camera)


def main() -> None:
    args = _arguments()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    outfit = OUTFITS[args.variant]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(input_path))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    rigs = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    if len(meshes) != 1 or len(rigs) != 1:
        raise RuntimeError(f"Expected one mesh and one rig; found {len(meshes)} and {len(rigs)}")
    body, rig = meshes[0], rigs[0]
    bones = Bones(rig)
    weights = _vertex_weights(body)
    dominant = _face_dominant_bones(body, weights)
    skin_slot = _material_index(body, "skin")
    wetsuit_slot = _material_index(body, "wetsuit")
    body_slots = {skin_slot, wetsuit_slot}

    prefix = body.data.materials[wetsuit_slot].name.rsplit("_", 1)[0]
    garments = {kind: Garment(kind, outfit[kind], bones) for kind in ("top", "bottom")}
    garments["top"].under_waist_z = outfit["bottom"]["waist_z"]
    garments["top"].under_offset = outfit["bottom"]["offset"]
    materials = {kind: _new_material(f"{prefix}_{kind.capitalize()}", PREVIEW_COLOURS[kind])
                 for kind in garments}

    shells = {}
    report = {}
    for kind, garment in garments.items():
        shells[kind], report[kind] = _build_shell(body, garment, dominant, body_slots, materials[kind])

    # Re-slot the body: covered faces wear the garment, the rest is skin.
    body.data.materials.append(materials["top"])
    body.data.materials.append(materials["bottom"])
    top_slot = len(body.data.materials) - 2
    bottom_slot = top_slot + 1
    covered = {"top": 0, "bottom": 0, "skin": 0}
    vertices = body.data.vertices
    for polygon in body.data.polygons:
        if polygon.material_index not in body_slots:
            continue
        name = dominant[polygon.index]
        corners = [vertices[i].co for i in polygon.vertices]
        if all(garments["top"].inside(c, name, COVER_MARGIN) for c in corners):
            polygon.material_index = top_slot
            covered["top"] += 1
        elif all(garments["bottom"].inside(c, name, COVER_MARGIN) for c in corners):
            polygon.material_index = bottom_slot
            covered["bottom"] += 1
        else:
            polygon.material_index = skin_slot
            covered["skin"] += 1

    bpy.ops.object.select_all(action="DESELECT")
    for shell in shells.values():
        shell.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    # The wetsuit slot is now empty; drop it so no section is left behind.
    body.active_material_index = wetsuit_slot
    bpy.ops.object.material_slot_remove()
    names = [m.name for m in body.data.materials]
    if any("wetsuit" in n.casefold() for n in names):
        raise RuntimeError(f"Wetsuit slot survived: {names}")
    seat_reweighted = _fill_seat_thigh_share(body, bones)

    if args.preview:
        _render_preview(Path(args.preview).resolve(), [body])

    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.length_unit = "METERS"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.fbx(
        filepath=str(output_path),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_scale_options="FBX_SCALE_ALL",
        global_scale=1.0,
        apply_unit_scale=True,
        axis_forward="-Y",
        axis_up="Z",
        add_leaf_bones=False,
        use_mesh_modifiers=True,
        use_armature_deform_only=True,
        bake_anim=False,
        path_mode="COPY",
        embed_textures=False,
    )
    manifest = {
        "schema": "raftsim.cc0_river_clothing.v1",
        "generator_version": GENERATOR_VERSION,
        "variant": args.variant,
        "input_fbx": input_path.name,
        "input_sha256": _sha256(input_path),
        "output_fbx": output_path.name,
        "output_sha256": _sha256(output_path),
        "material_slots": names,
        "garments": {kind: {**report[kind], "spec": {k: v for k, v in outfit[kind].items()}}
                     for kind in garments},
        "body_faces": covered,
        "fabric_thickness_m": FABRIC_THICKNESS,
        "cover_margin_m": COVER_MARGIN,
        "seat_fill": SEAT_FILL,
        "seat_vertices_reweighted": seat_reweighted,
        "notes": "Garment shells are inferred everyday river clothing generated from the CC0 body "
                 "surface; colours and patterns are applied in Unreal from the crew roster.",
    }
    Path(args.manifest).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("RAFTSIM_CC0_CLOTHING_COMPLETE", args.variant, json.dumps(covered),
          json.dumps({k: v["faces"] for k, v in report.items()}), "slots", names)


if __name__ == "__main__":
    main()
