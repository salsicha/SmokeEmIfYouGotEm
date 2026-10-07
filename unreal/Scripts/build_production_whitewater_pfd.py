"""Build RaftSim's project-owned low-profile whitewater PFD.

A modern guide/rafting vest: slim contoured foam front and back panels, a front
zip with one large zippered chest pocket, a short cut that rides above the seat,
large open armholes, closed side panels under side adjustment straps, small
reflective accents and a lash tab. The padded shoulder straps are fitted to
each wearer as separate meshes (build_production_pfd_shoulder_straps.py); this
shell carries their chest-tab ladder-locks and back-panel anchors.

The local origin is the deterministic torso centre used by
``ARaftSimCrewAvatarActor`` (X toward the face, Z up the spine, centimetres).
No commercial mesh, texture, branding, or product image is copied; current
manufacturer pages are construction references only.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import bmesh
import bpy
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionPfd"
FBX_PATH = OUTPUT_ROOT / "SM_RaftSim_WhitewaterRescuePfd.fbx"
BLEND_PATH = OUTPUT_ROOT / "SM_RaftSim_WhitewaterRescuePfd.blend"
MANIFEST_PATH = OUTPUT_ROOT / "production_whitewater_pfd_manifest.json"
GENERATOR_VERSION = 15
MATERIAL_NAMES = [
    "PfdShell",
    "PfdWebbing",
    "PfdHardware",
    "PfdReflective",
    "PfdLabel",
]
# BuildPfdMaterials tiles the 1K ripstop once per ~30 cm of UV; authoring UVs
# in developed centimetres keeps the weave at its real 3 mm scale everywhere.
UV_CM_PER_REPEAT = 30.0

# ---------------------------------------------------------------------------
# Seated crew torso envelope.
#
# One rigid vest is shared by all five crew bodies, so its inner face is the
# envelope of all of them: the seated, posed torso vertices of each wearer in
# this mesh's own frame (runtime fit scale removed), mirrored left/right,
# closed horizontally into a convex section (foam bridges the spine groove
# and cleavage) and vertically by a 30 cm rolling ball (foam bridges the
# crease under the chest but still follows the lumbar curve), plus
# ENVELOPE_CLEARANCE_CM. Only torso under (or within 2 cm of) the cut panels
# counts: the armholes leave the arms free. `--fit-torsos DIR
# [--update-source]` re-measures it from torso-vertices-{1..5}.csv dumps; the
# table below is the fit to the seated rest-pose dumps of 2026-10-07
# (tmp/crew-round3-b).
# ---------------------------------------------------------------------------
ENVELOPE_CLEARANCE_CM = 0.6
ENVELOPE_ROLLING_BALL_CM = 30.0
ENVELOPE_DZ_CM = 2.0
ENVELOPE_ANGLE_STEP_DEG = 7.5
# The shoulder straps' plane: inboard over the trapezius, between the neck
# and its steep rise (|y| <= 10) and the acromion (|y| >= 17), so a raised
# paddling arm's deltoid passes outboard of the strap, never under it.
SHOULDER_STRAP_Y_CM = 12.0
# >>> fitted envelope
ENVELOPE_AXIS_X_CM = 1.55
ENVELOPE_Z0_CM = -18.0
# Rows rise by ENVELOPE_DZ_CM from ENVELOPE_Z0_CM; columns sweep 0 (front)
# to 180 degrees (spine) by ENVELOPE_ANGLE_STEP_DEG.
ENVELOPE_RADIUS_CM: tuple[tuple[float, ...], ...] = (
    (11.37, 11.47, 11.57, 11.66, 11.94, 12.39, 13.10, 14.11, 15.09, 16.45, 16.62, 16.34, 16.34, 16.28, 16.09, 16.16, 15.18, 14.07, 13.23, 12.68, 12.38, 11.72, 11.21, 10.92, 10.82),
    (11.46, 11.55, 11.66, 11.73, 12.01, 12.46, 13.16, 14.21, 15.25, 16.64, 16.80, 16.47, 16.43, 16.37, 16.18, 16.23, 15.25, 14.13, 13.30, 12.75, 12.44, 11.78, 11.27, 10.98, 10.89),
    (11.44, 11.54, 11.64, 11.73, 12.01, 12.52, 13.19, 14.18, 15.45, 16.96, 17.00, 16.57, 16.43, 16.40, 16.18, 16.23, 15.25, 14.13, 13.30, 12.75, 12.44, 11.78, 11.27, 10.98, 10.89),
    (11.22, 11.32, 11.55, 11.71, 12.08, 12.66, 13.34, 14.37, 15.86, 17.24, 17.00, 16.39, 16.09, 16.03, 15.84, 15.89, 15.05, 13.93, 13.10, 12.48, 11.96, 11.30, 10.81, 10.53, 10.44),
    (11.16, 11.25, 11.51, 11.76, 12.24, 12.86, 13.53, 14.53, 15.99, 17.22, 16.66, 16.12, 15.87, 15.80, 15.62, 15.68, 14.93, 13.86, 13.03, 12.28, 11.62, 10.96, 10.49, 10.22, 10.13),
    (11.22, 11.32, 11.57, 11.91, 12.44, 13.20, 13.75, 14.56, 15.75, 16.55, 16.40, 15.93, 15.75, 15.72, 15.55, 15.48, 14.86, 13.93, 13.10, 12.21, 11.42, 10.76, 10.29, 10.03, 9.94),
    (11.37, 11.47, 11.77, 12.19, 12.69, 13.36, 13.98, 14.64, 15.41, 16.08, 16.01, 15.72, 15.68, 15.65, 15.62, 15.41, 14.93, 14.02, 13.20, 12.28, 11.36, 10.70, 10.23, 9.97, 9.88),
    (11.37, 11.47, 11.77, 12.19, 12.73, 13.56, 14.26, 14.85, 15.39, 15.87, 15.95, 15.79, 15.75, 15.72, 15.78, 15.48, 15.13, 14.22, 13.40, 12.48, 11.46, 10.76, 10.29, 10.03, 9.94),
    (11.17, 11.27, 11.55, 11.98, 12.61, 13.56, 14.23, 14.85, 15.41, 15.81, 16.01, 15.99, 15.95, 15.92, 15.98, 15.68, 15.47, 14.56, 13.74, 12.77, 11.70, 10.97, 10.49, 10.22, 10.13),
    (11.09, 11.15, 11.39, 11.84, 12.49, 13.46, 14.27, 14.85, 15.41, 15.84, 16.08, 16.21, 16.15, 16.26, 16.32, 16.01, 15.95, 15.04, 14.22, 13.11, 12.03, 11.30, 10.81, 10.53, 10.44),
    (11.02, 11.09, 11.33, 11.80, 12.53, 13.53, 14.34, 14.90, 15.46, 16.03, 16.28, 16.36, 16.44, 16.78, 16.84, 16.57, 16.58, 15.67, 14.85, 13.59, 12.51, 11.78, 11.27, 10.99, 10.89),
    (11.06, 11.15, 11.41, 11.89, 12.64, 13.73, 14.54, 15.11, 15.66, 16.31, 16.62, 16.42, 16.51, 16.78, 17.12, 17.17, 17.37, 16.45, 15.64, 14.22, 13.10, 12.35, 11.81, 11.50, 11.41),
    (11.12, 11.22, 11.51, 12.04, 12.84, 14.00, 14.88, 15.44, 16.00, 16.65, 17.04, 16.69, 16.63, 16.85, 17.28, 17.75, 18.33, 17.42, 16.60, 15.01, 13.86, 12.99, 12.43, 12.11, 12.00),
    (11.12, 11.22, 11.51, 12.04, 12.84, 14.01, 15.36, 15.90, 16.42, 17.13, 17.26, 16.96, 16.84, 17.01, 17.49, 18.31, 19.07, 18.28, 17.36, 15.97, 14.66, 13.76, 13.17, 12.83, 12.72),
    (11.12, 11.21, 11.51, 12.03, 12.84, 14.01, 15.36, 15.95, 16.66, 17.56, 17.47, 17.03, 16.90, 17.05, 17.51, 18.32, 19.30, 19.04, 18.00, 17.00, 15.57, 14.60, 13.96, 13.60, 13.49),
    (10.92, 11.02, 11.31, 11.83, 12.62, 13.77, 15.17, 15.94, 16.86, 17.89, 17.50, 17.08, 16.96, 17.13, 17.61, 18.44, 19.72, 19.82, 18.69, 17.40, 16.02, 15.01, 14.36, 13.99, 13.87),
    (10.18, 10.27, 10.54, 11.02, 11.75, 12.81, 14.20, 15.16, 16.56, 17.95, 17.51, 17.08, 16.94, 17.10, 17.57, 18.38, 19.63, 20.26, 19.03, 17.64, 16.27, 15.25, 14.59, 14.21, 14.09),
    (9.54, 9.62, 9.87, 10.32, 11.01, 12.02, 13.41, 14.60, 16.32, 17.55, 17.48, 17.00, 16.83, 16.95, 17.37, 18.12, 19.29, 20.28, 19.38, 17.74, 16.34, 15.32, 14.65, 14.28, 14.15),
    (9.04, 9.12, 9.36, 9.78, 10.44, 11.39, 12.78, 13.94, 15.62, 17.26, 16.78, 16.36, 16.23, 16.38, 16.82, 17.60, 18.79, 20.40, 19.23, 17.79, 16.36, 15.34, 14.67, 14.29, 14.17),
    (8.70, 8.78, 9.01, 9.42, 10.05, 10.97, 12.30, 13.46, 15.14, 16.78, 16.30, 15.94, 15.86, 16.05, 16.53, 17.35, 18.59, 20.40, 19.20, 17.76, 16.36, 15.34, 14.67, 14.29, 14.17),
    (8.46, 8.53, 8.76, 9.16, 9.77, 10.67, 11.97, 13.12, 14.80, 16.44, 15.96, 15.61, 15.54, 15.73, 16.21, 17.02, 18.25, 20.03, 18.89, 17.45, 16.02, 15.02, 14.37, 14.00, 13.88),
    (8.32, 8.39, 8.61, 9.00, 9.61, 10.49, 11.76, 12.92, 14.60, 16.24, 15.76, 15.42, 15.35, 15.55, 16.03, 16.84, 18.05, 19.83, 18.69, 17.25, 15.82, 14.83, 14.19, 13.82, 13.70),
    (8.27, 8.34, 8.56, 8.95, 9.55, 10.43, 11.70, 12.85, 14.53, 16.18, 15.69, 15.36, 15.29, 15.49, 15.97, 16.77, 17.99, 19.76, 18.63, 17.19, 15.76, 14.77, 14.13, 13.76, 13.65),
)
# <<< fitted envelope


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smoothstep(edge0: float, edge1: float, value):
    t = np.clip((np.asarray(value, dtype=float) - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ---------------------------------------------------------------------------
# Envelope surface
# ---------------------------------------------------------------------------
def catmull_rom_weights(t: np.ndarray) -> tuple[np.ndarray, ...]:
    t2 = t * t
    t3 = t2 * t
    return (
        -0.5 * t3 + t2 - 0.5 * t,
        1.5 * t3 - 2.5 * t2 + 1.0,
        -1.5 * t3 + 2.0 * t2 + 0.5 * t,
        0.5 * t3 - 0.5 * t2,
    )


def envelope_radius(theta_deg, z) -> np.ndarray:
    """Inner-shell radius about the envelope axis (bicubic, mirror-symmetric).

    The table already carries the body clearance, so the shell's inner face
    lies directly on this surface.
    """
    table = np.asarray(ENVELOPE_RADIUS_CM, dtype=float)
    rows, columns = table.shape
    theta = np.mod(np.asarray(theta_deg, dtype=float), 360.0)
    # One vest is shared by every wearer, so the envelope is mirror-symmetric:
    # the left half of the shell is the right half reflected.
    theta = np.where(theta > 180.0, 360.0 - theta, theta)
    angle = theta / ENVELOPE_ANGLE_STEP_DEG
    a0 = np.minimum(np.floor(angle).astype(int), columns - 2)
    ta = angle - a0
    height = np.clip(
        (np.asarray(z, dtype=float) - ENVELOPE_Z0_CM) / ENVELOPE_DZ_CM,
        0.0,
        rows - 1.0,
    )
    z0 = np.minimum(np.floor(height).astype(int), rows - 2)
    tz = height - z0
    last = columns - 1
    result = np.zeros(np.broadcast(theta, height).shape)
    for i, weight_a in enumerate(catmull_rom_weights(ta)):
        column = np.abs(a0 - 1 + i)
        column = np.where(column > last, 2 * last - column, column)
        for j, weight_z in enumerate(catmull_rom_weights(tz)):
            row = np.clip(z0 - 1 + j, 0, rows - 1)
            result = result + weight_a * weight_z * table[row, column]
    return result


def envelope_point(theta_deg, z) -> np.ndarray:
    theta_deg = np.asarray(theta_deg, dtype=float)
    z = np.asarray(z, dtype=float)
    radius = envelope_radius(theta_deg, z)
    angle = np.radians(theta_deg)
    return np.stack(
        np.broadcast_arrays(
            ENVELOPE_AXIS_X_CM + radius * np.cos(angle),
            radius * np.sin(angle),
            z,
        ),
        axis=-1,
    )


def envelope_frame(theta_deg, z):
    """Point, outward unit normal and the two surface tangents (per deg, per cm)."""
    theta_deg, z = np.broadcast_arrays(
        np.asarray(theta_deg, dtype=float), np.asarray(z, dtype=float)
    )
    point = envelope_point(theta_deg, z)
    d_theta = (
        envelope_point(theta_deg + 0.25, z) - envelope_point(theta_deg - 0.25, z)
    ) / 0.5
    d_z = (envelope_point(theta_deg, z + 0.05) - envelope_point(theta_deg, z - 0.05)) / 0.1
    normal = np.cross(d_theta, d_z)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    return point, normal, d_theta, d_z


def surface_offset_point(theta_deg, z, offset) -> np.ndarray:
    point, normal, _, _ = envelope_frame(theta_deg, z)
    return point + normal * np.asarray(offset, dtype=float)[..., None]


# ---------------------------------------------------------------------------
# Small numeric helpers
# ---------------------------------------------------------------------------
def pchip(xs, ys) -> Callable[[np.ndarray], np.ndarray]:
    """Shape-preserving cubic through authored outline control points."""
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    h = np.diff(xs)
    delta = np.diff(ys) / h
    slopes = np.zeros_like(ys)
    for k in range(1, len(xs) - 1):
        if delta[k - 1] * delta[k] > 0.0:
            w1 = 2.0 * h[k] + h[k - 1]
            w2 = h[k] + 2.0 * h[k - 1]
            slopes[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])

    def evaluate(x) -> np.ndarray:
        x = np.clip(np.asarray(x, dtype=float), xs[0], xs[-1])
        k = np.clip(np.searchsorted(xs, x) - 1, 0, len(xs) - 2)
        t = (x - xs[k]) / h[k]
        t2 = t * t
        t3 = t2 * t
        return (
            (2.0 * t3 - 3.0 * t2 + 1.0) * ys[k]
            + (t3 - 2.0 * t2 + t) * h[k] * slopes[k]
            + (-2.0 * t3 + 3.0 * t2) * ys[k + 1]
            + (t3 - t2) * h[k] * slopes[k + 1]
        )

    return evaluate


def upper_concave_envelope(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Taut-line envelope: webbing under tension bridges dips instead of sinking."""
    hull: list[tuple[float, float]] = []
    for point in zip(x.tolist(), y.tolist()):
        while len(hull) >= 2:
            (ox, oy), (ax, ay) = hull[-2], hull[-1]
            if (ax - ox) * (point[1] - oy) - (ay - oy) * (point[0] - ox) >= 0.0:
                hull.pop()
            else:
                break
        hull.append(point)
    hx, hy = zip(*hull)
    return np.interp(x, hx, hy)


def bridge_narrow_dips(values: np.ndarray, spacing: float, width: float) -> np.ndarray:
    """Flat morphological closing: fill dips narrower than `width` only.

    Tensioned webbing wrapping the convex torso spans seam grooves and rolled
    panel edges, but still steps down onto a thinner panel it crosses.
    """
    reach = max(int(round(0.5 * width / spacing)), 1)
    padded = np.pad(values, reach, mode="edge")
    dilated = np.max([padded[k : k + len(values)] for k in range(2 * reach + 1)], axis=0)
    padded = np.pad(dilated, reach, mode="edge")
    return np.min([padded[k : k + len(values)] for k in range(2 * reach + 1)], axis=0)


def convex_hull_2d(points: np.ndarray) -> np.ndarray:
    """Counter-clockwise monotone-chain hull."""
    unique = sorted(set(map(tuple, np.round(points, 5).tolist())))
    if len(unique) < 3:
        return np.asarray(unique)

    def cross(o, a, b) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0.0:
            lower.pop()
        lower.append(point)
    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0.0:
            upper.pop()
        upper.append(point)
    return np.asarray(lower[:-1] + upper[:-1])


def distance_to_polyline(points: np.ndarray, polyline: np.ndarray) -> np.ndarray:
    start = polyline[:-1]
    segment = polyline[1:] - start
    length2 = np.maximum((segment * segment).sum(-1), 1e-12)
    result = np.empty(len(points))
    for first in range(0, len(points), 2048):
        chunk = points[first : first + 2048, None, :]
        t = np.clip(((chunk - start) * segment).sum(-1) / length2, 0.0, 1.0)
        nearest = start + t[..., None] * segment
        result[first : first + 2048] = np.sqrt(((chunk - nearest) ** 2).sum(-1)).min(1)
    return result


def clustered_positions(length: float, step: float) -> np.ndarray:
    """Sample positions dense at both ends so rolled foam edges stay round."""
    edge = np.cumsum([0.05, 0.09, 0.14, 0.2, 0.27, 0.36, 0.48, 0.62])
    if length < 2.0 * edge[-1] + step:
        edge = edge * (length / (2.0 * edge[-1] + step))
    middle_count = max(int(math.ceil((length - 2.0 * edge[-1]) / step)), 1)
    middle = np.linspace(edge[-1], length - edge[-1], middle_count + 1)
    return np.concatenate([[0.0], edge, middle[1:-1], length - edge[::-1], [length]])


# ---------------------------------------------------------------------------
# Mesh assembly
# ---------------------------------------------------------------------------
class MeshBuilder:
    """Accumulates one multi-material mesh with authored centimetre UVs."""

    def __init__(self, material_names: list[str] | None = None) -> None:
        self.material_names = list(material_names or MATERIAL_NAMES)
        self.chunks: list[np.ndarray] = []
        self.count = 0
        self.faces: list[tuple[int, ...]] = []
        self.face_materials: list[int] = []
        self.face_uvs: list[tuple[tuple[float, float], ...]] = []
        self.sharp_edges: list[tuple[int, int]] = []
        self.piece_ranges: dict[str, tuple[int, int]] = {}
        self.piece_roles: dict[str, str] = {}

    def add_points(self, coordinates) -> np.ndarray:
        coordinates = np.asarray(coordinates, dtype=float).reshape(-1, 3)
        indices = np.arange(self.count, self.count + len(coordinates))
        self.chunks.append(coordinates)
        self.count += len(coordinates)
        return indices

    def add_face(self, indices, material: str, uvs) -> None:
        self.faces.append(tuple(int(index) for index in indices))
        self.face_materials.append(self.material_names.index(material))
        self.face_uvs.append(tuple((float(u), float(v)) for u, v in uvs))

    def begin_piece(self, name: str, role: str) -> None:
        self._piece = (name, role, self.count)

    def end_piece(self) -> None:
        name, role, first = self._piece
        self.piece_ranges[name] = (first, self.count)
        self.piece_roles[name] = role

    def points(self) -> np.ndarray:
        return np.concatenate(self.chunks) if self.chunks else np.zeros((0, 3))

    def to_object(self, name: str, materials: dict[str, bpy.types.Material]) -> bpy.types.Object:
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.points().tolist(), [], self.faces)
        for material_name in self.material_names:
            mesh.materials.append(materials[material_name])
        mesh.polygons.foreach_set("material_index", self.face_materials)
        uv_layer = mesh.uv_layers.new(name="UVMap")
        uv_layer.data.foreach_set(
            "uv",
            [
                coordinate / UV_CM_PER_REPEAT
                for face_uvs in self.face_uvs
                for uv in face_uvs
                for coordinate in uv
            ],
        )
        edge_lookup = {
            tuple(sorted(edge.vertices)): edge.index for edge in mesh.edges
        }
        sharp = [False] * len(mesh.edges)
        for a, b in self.sharp_edges:
            index = edge_lookup.get((min(a, b), max(a, b)))
            if index is not None:
                sharp[index] = True
        attribute = mesh.attributes.get("sharp_edge") or mesh.attributes.new(
            "sharp_edge", "BOOLEAN", "EDGE"
        )
        attribute.data.foreach_set("value", sharp)
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        return obj


def add_ring_sweep(
    builder: MeshBuilder,
    rings: np.ndarray,
    material: str,
    uvs: np.ndarray,
    cap_material: str | None = None,
    closed: bool = False,
) -> None:
    """Skin closed cross-section rings (path samples x ring points) with caps.

    Each ring runs counter-clockwise when viewed back along the path, so the
    quads face outward and the end caps close the sweep into a solid. A
    `closed` path (a ring such as a carabiner) joins its ends instead.
    """
    samples, count = rings.shape[:2]
    indices = builder.add_points(rings.reshape(-1, 3)).reshape(samples, count)
    for i in range(samples if closed else samples - 1):
        j = (i + 1) % samples
        for m in range(count):
            n = (m + 1) % count
            wrapped = n + (count if n == 0 else 0)
            builder.add_face(
                (indices[i, m], indices[i, n], indices[j, n], indices[j, m]),
                material,
                (uvs[i, m], uvs[i, wrapped], uvs[i + 1 if closed else j, wrapped], uvs[i + 1 if closed else j, m]),
            )
    if closed:
        return
    cap = cap_material or material
    builder.add_face(
        tuple(reversed(indices[0].tolist())),
        cap,
        tuple(reversed([tuple(uv) for uv in uvs[0, :count]])),
    )
    builder.add_face(indices[-1].tolist(), cap, [tuple(uv) for uv in uvs[-1, :count]])
    for ring in (indices[0], indices[-1]):
        for m in range(count):
            builder.sharp_edges.append((ring[m], ring[(m + 1) % count]))


def add_rounded_block(
    builder: MeshBuilder,
    name: str,
    centre: np.ndarray,
    axes: np.ndarray,
    half_extents: tuple[float, float, float],
    material: str = "PfdHardware",
    exponent: float = 0.28,
    segments: int = 24,
    rings: int = 12,
) -> None:
    """Superellipsoid block: moulded buckle and zipper-pull hardware.

    `axes` rows are the block's local X/Y/Z in vest space; Z is the surface
    normal, so the block's underside sits `half_extents[2]` below `centre`.
    """
    builder.begin_piece(name, "hardware")
    latitudes = np.linspace(-math.pi / 2.0, math.pi / 2.0, rings + 1)[1:-1]
    longitudes = np.linspace(-math.pi, math.pi, segments, endpoint=False)

    def shaped(value: np.ndarray) -> np.ndarray:
        return np.sign(value) * np.abs(value) ** exponent

    lat, lon = np.meshgrid(latitudes, longitudes, indexing="ij")
    local = np.stack(
        [
            half_extents[0] * shaped(np.cos(lat) * np.cos(lon)),
            half_extents[1] * shaped(np.cos(lat) * np.sin(lon)),
            half_extents[2] * shaped(np.sin(lat)),
        ],
        axis=-1,
    )
    world = centre + local @ axes
    ring_indices = builder.add_points(world.reshape(-1, 3)).reshape(len(latitudes), segments)
    poles = builder.add_points(
        [centre - axes[2] * half_extents[2], centre + axes[2] * half_extents[2]]
    )
    step = 0.3
    for r in range(len(latitudes) - 1):
        for s in range(segments):
            t = (s + 1) % segments
            builder.add_face(
                (ring_indices[r, s], ring_indices[r, t], ring_indices[r + 1, t], ring_indices[r + 1, s]),
                material,
                ((s * step, r * step), ((s + 1) * step, r * step), ((s + 1) * step, (r + 1) * step), (s * step, (r + 1) * step)),
            )
    top = (len(latitudes) - 1) * step
    for s in range(segments):
        t = (s + 1) % segments
        builder.add_face(
            (poles[0], ring_indices[0, t], ring_indices[0, s]),
            material,
            ((s * step, -step), ((s + 1) * step, 0.0), (s * step, 0.0)),
        )
        builder.add_face(
            (poles[1], ring_indices[-1, s], ring_indices[-1, t]),
            material,
            ((s * step, top + step), (s * step, top), ((s + 1) * step, top)),
        )
    builder.end_piece()


# ---------------------------------------------------------------------------
# Foam panels
# ---------------------------------------------------------------------------
@dataclass
class FoamPanel:
    """A fabric-covered foam panel lying on (or over) the torso envelope.

    The outline is authored as bottom and top edges over an angular span; the
    cross-section is flat against the wearer and rolls over a quarter-round
    edge into a gently crowned face, like die-cut foam under a sewn binding.
    """

    name: str
    theta_start: float
    theta_end: float
    bottom: tuple[tuple[float, float], ...]
    top: tuple[tuple[float, float], ...]
    thickness: float
    edge_roll: float
    crown: float = 0.0
    corner_radius: tuple[float, float, float, float] = (2.5, 2.5, 2.5, 2.5)
    face_material: str = "PfdShell"
    edge_material: str = "PfdLabel"
    lining_material: str = "PfdLabel"
    binding_width: float = 0.7
    base: float | Callable[[np.ndarray, np.ndarray], np.ndarray] = 0.0
    step: float = 1.1
    role: str = "foam"
    # Foam thickness factor at the start/end of the angular span, blended in
    # over `thin_span_deg`: slim panels thin out toward the side seams.
    end_thickness: tuple[float, float] = (1.0, 1.0)
    thin_span_deg: float = 22.0
    _fine_theta: np.ndarray = field(init=False, repr=False)
    _fine_s: np.ndarray = field(init=False, repr=False)
    _boundary: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.span = self.theta_end - self.theta_start
        self._bottom_fn = pchip(*zip(*[(t - self.theta_start, z) for t, z in self.bottom]))
        self._top_fn = pchip(*zip(*[(t - self.theta_start, z) for t, z in self.top]))
        z_mid = 0.5 * (min(z for _, z in self.bottom) + max(z for _, z in self.top))
        self._fine_theta = np.linspace(0.0, self.span, 721)
        _, _, d_theta, _ = envelope_frame(
            self.theta_start + self._fine_theta, np.full(721, z_mid)
        )
        speed = np.linalg.norm(d_theta, axis=-1)
        self._fine_s = np.concatenate(
            [[0.0], np.cumsum(0.5 * (speed[1:] + speed[:-1]) * np.diff(self._fine_theta))]
        )
        self.length = float(self._fine_s[-1])
        rel = np.interp(np.linspace(0.0, self.length, 241), self._fine_s, self._fine_theta)
        bottom, top = self.edges(rel)
        s = self.s_of(rel)
        self._boundary = np.concatenate(
            [
                np.stack([s, bottom], -1),
                np.stack([s[::-1], top[::-1]], -1),
                [[s[0], bottom[0]]],
            ]
        )

    def s_of(self, rel: np.ndarray) -> np.ndarray:
        return np.interp(rel, self._fine_theta, self._fine_s)

    def edges(self, rel: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Bottom/top edge heights with rounded panel corners."""
        s = self.s_of(rel)
        bottom = self._bottom_fn(rel)
        top = self._top_fn(rel)
        lifts = []
        for radius, distance in (
            (self.corner_radius[0], s),
            (self.corner_radius[1], self.length - s),
            (self.corner_radius[2], s),
            (self.corner_radius[3], self.length - s),
        ):
            inset = np.clip(radius - distance, 0.0, radius)
            lifts.append(radius - np.sqrt(np.maximum(radius * radius - inset * inset, 0.0)))
        return bottom + lifts[0] + lifts[1], top - lifts[2] - lifts[3]

    def base_at(self, theta: np.ndarray, z: np.ndarray) -> np.ndarray:
        if callable(self.base):
            return np.asarray(self.base(theta, z), dtype=float)
        return np.full(np.shape(theta), float(self.base))

    def profile(self, distance: np.ndarray, rel: np.ndarray) -> np.ndarray:
        roll = np.clip(distance / self.edge_roll, 0.0, 1.0)
        scale = (
            1.0
            - (1.0 - self.end_thickness[0]) * smoothstep(self.thin_span_deg, 0.0, rel)
            - (1.0 - self.end_thickness[1]) * smoothstep(self.span - self.thin_span_deg, self.span, rel)
        )
        return scale * (
            self.thickness * np.sqrt(1.0 - (1.0 - roll) ** 2)
            + self.crown * smoothstep(self.edge_roll, self.edge_roll + 6.0, distance)
        )

    def outer_offset(self, theta: np.ndarray, z: np.ndarray) -> np.ndarray:
        """Outer-face offset over the envelope, or -inf outside the outline."""
        theta = np.asarray(theta, dtype=float)
        z = np.asarray(z, dtype=float)
        rel = np.mod(theta - self.theta_start, 360.0)
        inside = rel <= self.span
        rel = np.clip(rel, 0.0, self.span)
        bottom, top = self.edges(rel)
        inside &= (z >= bottom) & (z <= top)
        result = np.full(theta.shape, -np.inf)
        if inside.any():
            developed = np.stack([self.s_of(rel[inside]), z[inside]], -1)
            distance = distance_to_polyline(developed, self._boundary)
            result[inside] = self.base_at(theta[inside], z[inside]) + self.profile(distance, rel[inside])
        return result


def build_foam_panel(builder: MeshBuilder, panel: FoamPanel) -> np.ndarray:
    """Skin a closed pillow: flat lining, rolled edge, crowned face."""
    columns_s = clustered_positions(panel.length, panel.step)
    # Rows are fractions of each column's height, so where an outline edge is
    # steep (the armhole) neighbouring columns must not differ much in height
    # or their quads shear across the curved shell and cut under it (keep
    # neighbouring columns within 1 cm of each other in height).
    for _ in range(8):
        bottom, top = panel.edges(np.interp(columns_s, panel._fine_s, panel._fine_theta))
        splits = np.ceil(np.maximum(np.abs(np.diff(top)), np.abs(np.diff(bottom))) / 1.0).astype(int)
        if splits.max() <= 1:
            break
        refined = [columns_s[0]]
        for j, count in enumerate(splits):
            refined.extend(np.linspace(columns_s[j], columns_s[j + 1], max(count, 1) + 1)[1:])
        columns_s = np.asarray(refined)
    columns_rel = np.interp(columns_s, panel._fine_s, panel._fine_theta)
    bottom, top = panel.edges(columns_rel)
    heights = top - bottom
    if heights.min() <= 0.05:
        raise RuntimeError(f"{panel.name} outline collapses: {heights.min():.3f} cm")
    fractions = clustered_positions(float(heights.max()), panel.step) / float(heights.max())
    nu, nv = len(columns_s), len(fractions)
    s = np.repeat(columns_s[:, None], nv, 1)
    rel = np.repeat(columns_rel[:, None], nv, 1)
    z = bottom[:, None] + fractions[None, :] * heights[:, None]
    boundary = np.concatenate(
        [
            np.stack([s[:, 0], z[:, 0]], -1),
            np.stack([s[-1, 1:], z[-1, 1:]], -1),
            np.stack([s[::-1, -1], z[::-1, -1]], -1)[1:],
            np.stack([s[0, ::-1], z[0, ::-1]], -1)[1:],
        ]
    )
    distance = distance_to_polyline(
        np.stack([s, z], -1).reshape(-1, 2), boundary
    ).reshape(nu, nv)
    edge = np.zeros((nu, nv), dtype=bool)
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    distance[edge] = 0.0
    theta = panel.theta_start + rel
    point, normal, _, _ = envelope_frame(theta, z)
    base = panel.base_at(theta, z)
    lift = panel.profile(distance, rel)
    outer = point + normal * (base + lift)[..., None]
    inner = point + normal * base[..., None]
    builder.begin_piece(panel.name, panel.role)
    outer_index = builder.add_points(outer.reshape(-1, 3)).reshape(nu, nv)
    inner_index = outer_index.copy()
    inner_index[~edge] = builder.add_points(inner[~edge])
    for j in range(nu - 1):
        for k in range(nv - 1):
            corners = ((j, k), (j + 1, k), (j + 1, k + 1), (j, k + 1))
            uvs = [(s[a, b], z[a, b]) for a, b in corners]
            centre_distance = 0.25 * sum(distance[a, b] for a, b in corners)
            builder.add_face(
                [outer_index[a, b] for a, b in corners],
                panel.edge_material if centre_distance < panel.binding_width else panel.face_material,
                uvs,
            )
            builder.add_face(
                [inner_index[a, b] for a, b in reversed(corners)],
                panel.lining_material,
                list(reversed(uvs)),
            )
    ring = (
        [outer_index[j, 0] for j in range(nu)]
        + [outer_index[-1, k] for k in range(1, nv)]
        + [outer_index[j, -1] for j in range(nu - 2, -1, -1)]
        + [outer_index[0, k] for k in range(nv - 2, 0, -1)]
    )
    for a, b in zip(ring, ring[1:] + ring[:1]):
        builder.sharp_edges.append((a, b))
    builder.end_piece()
    return outer


class SurfaceLayers:
    """Outer-face height of everything already sewn onto the envelope."""

    def __init__(self, panels: list[FoamPanel] | None = None) -> None:
        self.panels: list[FoamPanel] = list(panels or [])

    def add(self, panel: FoamPanel) -> None:
        self.panels.append(panel)

    def outer_offset(self, theta, z) -> np.ndarray:
        theta, z = np.broadcast_arrays(np.asarray(theta, float), np.asarray(z, float))
        result = np.zeros(theta.shape)
        for panel in self.panels:
            result = np.maximum(result, panel.outer_offset(theta, z))
        return result


# ---------------------------------------------------------------------------
# Webbing and tape on the vest surface
# ---------------------------------------------------------------------------
def stadium_profile(half_width: float, thickness: float, width_samples: int, end_samples: int = 4):
    """(w, h) cross-section, counter-clockwise: flat-woven webbing edges."""
    radius = thickness * 0.5
    bottom = [(w, 0.0) for w in np.linspace(-half_width + radius, half_width - radius, width_samples)]
    right = [
        (half_width - radius + radius * math.sin(a), radius - radius * math.cos(a))
        for a in np.linspace(0.0, math.pi, end_samples + 2)[1:-1]
    ]
    top = [(w, thickness) for w in np.linspace(half_width - radius, -half_width + radius, width_samples)]
    left = [
        (-half_width + radius - radius * math.sin(a), radius + radius * math.cos(a))
        for a in np.linspace(0.0, math.pi, end_samples + 2)[1:-1]
    ]
    return np.asarray(bottom + right + top + left)


@dataclass
class RibbonResult:
    theta: np.ndarray
    z: np.ndarray
    s: np.ndarray
    base: np.ndarray  # (samples, width columns)
    thickness: float
    width_offsets: np.ndarray
    across: np.ndarray  # developed unit across-direction (samples, 2)


def add_surface_ribbon(
    builder: MeshBuilder,
    name: str,
    path_theta_z: list[tuple[float, float]],
    width: float,
    thickness: float,
    material: str,
    layers: SurfaceLayers,
    gap: float = 0.04,
    taut: bool = True,
    floor: float | None = None,
    spacing: float = 0.45,
    width_samples: int = 5,
    role: str = "strap",
) -> RibbonResult:
    """Sweep flat webbing/tape along a (theta, z) path ON the outer surface.

    Each strap edge rides on whatever is beneath it (foam, pocket) plus a
    small gap, so no webbing can sink into the vest or the wearer. Taut
    webbing bridges seam grooves through an upper concave envelope.
    """
    control = np.asarray(path_theta_z, dtype=float)
    dense_t = np.linspace(0.0, 1.0, 400)
    knots = np.linspace(0.0, 1.0, len(control))
    theta_dense = pchip(knots, control[:, 0])(dense_t) if len(control) > 2 else np.interp(dense_t, knots, control[:, 0])
    z_dense = pchip(knots, control[:, 1])(dense_t) if len(control) > 2 else np.interp(dense_t, knots, control[:, 1])
    _, _, d_theta, _ = envelope_frame(theta_dense, z_dense)
    speed = np.linalg.norm(d_theta, axis=-1)
    ds = np.hypot(np.diff(theta_dense) * 0.5 * (speed[1:] + speed[:-1]), np.diff(z_dense))
    s_dense = np.concatenate([[0.0], np.cumsum(ds)])
    samples = max(int(math.ceil(s_dense[-1] / spacing)), 2) + 1
    s = np.linspace(0.0, s_dense[-1], samples)
    theta = np.interp(s, s_dense, theta_dense)
    z = np.interp(s, s_dense, z_dense)
    _, _, d_theta, _ = envelope_frame(theta, z)
    speed = np.linalg.norm(d_theta, axis=-1)
    tangent = np.stack([np.gradient(theta) * speed, np.gradient(z)], -1)
    tangent /= np.linalg.norm(tangent, axis=-1, keepdims=True)
    # Rotating the developed tangent +90 degrees gives the across direction
    # for which across x normal = tangent, i.e. counter-clockwise profiles.
    across = np.stack([-tangent[:, 1], tangent[:, 0]], -1)
    half = width * 0.5
    profile = stadium_profile(half, thickness, width_samples)
    offsets = np.linspace(-half, half, 9)
    theta_w = theta[:, None] + offsets[None, :] * across[:, 0:1] / speed[:, None]
    z_w = z[:, None] + offsets[None, :] * across[:, 1:2]
    base = layers.outer_offset(theta_w, z_w)
    if floor is not None:
        base = np.maximum(base, floor)
    if taut:
        # Tensioned webbing bridges seam grooves along its run and, being
        # stiff across its width, any dip across it.
        for column in range(base.shape[1]):
            base[:, column] = bridge_narrow_dips(base[:, column], s[1] - s[0], 3.0)
        for row in range(base.shape[0]):
            base[row] = upper_concave_envelope(offsets, base[row])
    # Where webbing steps down off a panel's rolled edge it stays up over the
    # edge briefly instead of cutting the corner between path samples.
    reach = int(math.ceil(0.6 / (s[1] - s[0])))
    padded = np.pad(base, ((reach, reach), (0, 0)), mode="edge")
    base = np.max([padded[k : k + samples] for k in range(2 * reach + 1)], axis=0)
    base = base + gap
    rings = []
    for i in range(samples):
        ring_theta = theta[i] + profile[:, 0] * across[i, 0] / speed[i]
        ring_z = z[i] + profile[:, 0] * across[i, 1]
        ring_base = np.interp(profile[:, 0], offsets, base[i])
        rings.append(surface_offset_point(ring_theta, ring_z, ring_base + profile[:, 1]))
    perimeter = np.concatenate(
        [[0.0], np.cumsum(np.linalg.norm(np.diff(np.vstack([profile, profile[:1]]), axis=0), axis=-1))]
    )
    uvs = np.stack(np.broadcast_arrays(s[:, None], perimeter[None, :]), -1)
    builder.begin_piece(name, role)
    add_ring_sweep(builder, np.asarray(rings), material, uvs)
    builder.end_piece()
    return RibbonResult(theta, z, s, base, thickness, offsets, across)


def ribbon_frame(result: RibbonResult, fraction: float):
    """Envelope point under a placed ribbon, its axes (along, across, normal),
    theta, z and sample index; offsets along the normal match `result.base`."""
    index = int(round(fraction * (len(result.s) - 1)))
    theta = result.theta[index]
    z = result.z[index]
    point, normal, d_theta, d_z = envelope_frame(theta, z)
    along_dev = np.array([result.across[index, 1], -result.across[index, 0]])
    along = d_theta / np.linalg.norm(d_theta) * along_dev[0] + d_z / np.linalg.norm(d_z) * along_dev[1]
    along -= normal * np.dot(along, normal)
    along /= np.linalg.norm(along)
    across = np.cross(normal, along)
    return point, np.stack([along, across, normal]), theta, z, index


def surface_axes(theta: float, z: float):
    """Envelope point, outward normal, unit up-slope and across directions.

    (along, across, normal) is right-handed, as add_rounded_block expects.
    """
    point, normal, _, d_z = envelope_frame(theta, z)
    along = d_z - normal * float(np.dot(d_z, normal))
    along /= np.linalg.norm(along)
    across = np.cross(normal, along)
    return point, normal, along, across


def footprint_offset(layers: SurfaceLayers, theta: float, z: float, half_across: float, half_along: float) -> float:
    """Highest outer-surface offset under a small block lying at (theta, z)."""
    speed = float(np.linalg.norm(envelope_frame(theta, z)[2]))
    d_theta, d_z = np.meshgrid(
        np.linspace(-half_across, half_across, 9) / speed, np.linspace(-half_along, half_along, 7)
    )
    return float(layers.outer_offset(theta + d_theta.ravel(), z + d_z.ravel()).max())


# ---------------------------------------------------------------------------
# Vest layout
# ---------------------------------------------------------------------------
# Heights are vest-local cm. The hem sits at the seated waist so the vest
# rides above the seat; the armholes open from just under the armpit. The
# chest tabs and the back panel top stay a few cm under the lowest of the
# five shoulder lines (Crew03: 23.6 cm at the strap, 19.8 cm 18 cm out), so
# seen from behind or the side only the fitted straps cross the shoulders.
VEST_BOTTOM_Z_CM = -14.0
ARMPIT_Z_CM = 3.0
FRONT_NECK_Z_CM = 14.5
FRONT_SHOULDER_Z_CM = 20.0
BACK_TOP_Z_CM = 20.0
# Angles are degrees about the envelope axis: 0 front centre, 90 the +Y
# flank, 180 the spine.
FRONT_ZIP_HALF_GAP_DEG = 2.4
FRONT_SIDE_SEAM_DEG = 76.0
BACK_SIDE_SEAM_DEG = 114.0
SEAM_GAP_DEG = 0.05
FRONT_FOAM_CM = 2.4
BACK_FOAM_CM = 1.9
SIDE_FOAM_CM = 0.9
# The chest tab and back-panel shoulder for each strap sit where the shell
# reaches the strap's plane (SHOULDER_STRAP_Y_CM) this far below their tops.
SHOULDER_STRAP_OVERLAP_CM = 4.5
SHOULDER_BUCKLE_DROP_CM = 2.6
SHOULDER_ANCHOR_DROP_CM = 3.0
WEBBING_WIDTH_CM = 2.5
WEBBING_THICKNESS_CM = 0.18
STRAP_GAP_CM = 0.04
# Above the forearms that rest on the hips in the seated pose, and above
# the guide's flip line.
SIDE_STRAP_Z_CM = (-4.0, -0.5)
POCKET_THETA_DEG = (10.0, 48.0)


def flip_outline(points, side: float):
    """Mirror an authored right-side (theta, z) outline onto either side."""
    if side > 0.0:
        return tuple(points)
    return tuple((360.0 - theta, z) for theta, z in reversed(points))


def shoulder_strap_theta(z: float, back: bool = False) -> float:
    """Angle at which the inner shell meets the shoulder-strap line."""
    candidates = np.linspace(90.0, 180.0, 901) if back else np.linspace(0.0, 90.0, 901)
    y = envelope_point(candidates, np.full_like(candidates, z))[:, 1]
    order = np.argsort(y)
    return float(np.interp(SHOULDER_STRAP_Y_CM, y[order], candidates[order]))


def front_panel(side: float) -> FoamPanel:
    start, end = FRONT_ZIP_HALF_GAP_DEG, FRONT_SIDE_SEAM_DEG - SEAM_GAP_DEG
    strap = shoulder_strap_theta(FRONT_SHOULDER_Z_CM - SHOULDER_STRAP_OVERLAP_CM)
    bottom = ((start, VEST_BOTTOM_Z_CM), (end, VEST_BOTTOM_Z_CM + 0.4))
    # A scooped neckline rises from the zip to a tab under the shoulder
    # strap; the large armhole then drops steeply past the arm and curves
    # under it to the side seam, like the cut of a modern guide vest.
    armhole_top = (strap + 7.0, FRONT_SHOULDER_Z_CM - 2.5)
    top = (
        (start, FRONT_NECK_Z_CM),
        (strap - 10.0, FRONT_SHOULDER_Z_CM - 1.5),
        (strap + 2.0, FRONT_SHOULDER_Z_CM),
        armhole_top,
    ) + tuple(
        (
            armhole_top[0] + f * (end - armhole_top[0]),
            ARMPIT_Z_CM + (armhole_top[1] - ARMPIT_Z_CM) * (1.0 - f) ** 2,
        )
        for f in (0.35, 0.75, 1.0)
    )
    corners = (1.2, 3.0, 1.5, 0.8)
    end_thickness = (1.0, 0.55)
    if side < 0.0:
        start, end = 360.0 - end, 360.0 - start
        corners = (corners[1], corners[0], corners[3], corners[2])
        end_thickness = end_thickness[::-1]
    return FoamPanel(
        f"FrontFoamPanel_{side:+.0f}",
        start,
        end,
        flip_outline(bottom, side),
        flip_outline(top, side),
        FRONT_FOAM_CM,
        1.0,
        crown=0.25,
        corner_radius=corners,
        end_thickness=end_thickness,
    )


def back_panel() -> FoamPanel:
    seam = BACK_SIDE_SEAM_DEG + SEAM_GAP_DEG
    strap = shoulder_strap_theta(BACK_TOP_Z_CM - SHOULDER_STRAP_OVERLAP_CM, back=True)
    # The armhole rises from under the arm and steepens up to the strap.
    armhole_top = (strap - 7.0, BACK_TOP_Z_CM - 2.5)
    top_right = tuple(
        (seam + f * (armhole_top[0] - seam), ARMPIT_Z_CM + (armhole_top[1] - ARMPIT_Z_CM) * f**2)
        for f in (0.0, 0.25, 0.65)
    ) + (
        armhole_top,
        (strap + 2.0, BACK_TOP_Z_CM),
        (180.0, BACK_TOP_Z_CM - 0.6),
    )
    top = top_right + tuple((360.0 - t, z) for t, z in reversed(top_right[:-1]))
    bottom = (
        (seam, VEST_BOTTOM_Z_CM + 0.4),
        (180.0, VEST_BOTTOM_Z_CM - 0.6),
        (360.0 - seam, VEST_BOTTOM_Z_CM + 0.4),
    )
    return FoamPanel(
        "BackFoamPanel",
        seam,
        360.0 - seam,
        bottom,
        top,
        BACK_FOAM_CM,
        0.9,
        crown=0.2,
        corner_radius=(3.0, 3.0, 0.8, 0.8),
        end_thickness=(0.65, 0.65),
    )


def side_panel(side: float) -> FoamPanel:
    start = FRONT_SIDE_SEAM_DEG + SEAM_GAP_DEG
    end = BACK_SIDE_SEAM_DEG - SEAM_GAP_DEG
    bottom = ((start, VEST_BOTTOM_Z_CM + 0.4), (end, VEST_BOTTOM_Z_CM + 0.4))
    top = ((start, ARMPIT_Z_CM), (0.5 * (start + end), ARMPIT_Z_CM - 1.0), (end, ARMPIT_Z_CM))
    if side < 0.0:
        start, end = 360.0 - end, 360.0 - start
    return FoamPanel(
        f"SideFoamPanel_{side:+.0f}",
        start,
        end,
        flip_outline(bottom, side),
        flip_outline(top, side),
        SIDE_FOAM_CM,
        0.7,
        crown=0.1,
        corner_radius=(0.6, 0.6, 0.6, 0.6),
        # Dark side panels under the straps: the two-tone look of current
        # low-profile vests, and the flanks read slimmer from the side.
        face_material="PfdLabel",
    )


def offset_convex_polygon(
    hull: np.ndarray, gap: float, step: float = 0.35, arc_step_deg: float = 8.0
) -> np.ndarray:
    """Closed counter-clockwise outline at least `gap` outside a convex hull."""
    # Corner arcs are polygonised outside the true arc, never inside it.
    arc_radius = gap / math.cos(math.radians(arc_step_deg) * 0.5)
    count = len(hull)
    edges = np.roll(hull, -1, axis=0) - hull
    normals = np.stack([edges[:, 1], -edges[:, 0]], -1)
    normals /= np.linalg.norm(normals, axis=-1, keepdims=True)
    result = []
    for i in range(count):
        before = math.atan2(normals[i - 1, 1], normals[i - 1, 0])
        after = math.atan2(normals[i, 1], normals[i, 0])
        while after < before:
            after += 2.0 * math.pi
        for angle in np.linspace(before, after, max(int((after - before) / math.radians(arc_step_deg)), 1) + 1):
            result.append(hull[i] + arc_radius * np.array([math.cos(angle), math.sin(angle)]))
        start = hull[i] + gap * normals[i]
        end = hull[(i + 1) % count] + gap * normals[i]
        pieces = max(int(np.linalg.norm(end - start) / step), 1)
        for t in np.linspace(0.0, 1.0, pieces + 1)[1:-1]:
            result.append(start + (end - start) * t)
    return np.asarray(result)


def build_vest(builder: MeshBuilder) -> dict[str, object]:
    layers = SurfaceLayers()
    foam_panels = [front_panel(1.0), front_panel(-1.0), back_panel(), side_panel(1.0), side_panel(-1.0)]
    for panel in foam_panels:
        build_foam_panel(builder, panel)
        layers.add(panel)
    foam_only = SurfaceLayers(layers.panels)

    # One large zippered chest pocket on the right front panel, sewn on top
    # of the foam: the modern guide vest's main storage.
    pocket = FoamPanel(
        "ZipperedChestPocket",
        POCKET_THETA_DEG[0],
        POCKET_THETA_DEG[1],
        ((POCKET_THETA_DEG[0], -8.0), (POCKET_THETA_DEG[1], -9.0)),
        ((POCKET_THETA_DEG[0], 9.0), (0.5 * sum(POCKET_THETA_DEG), 10.0), (POCKET_THETA_DEG[1], 6.5)),
        0.55,
        0.6,
        crown=0.3,
        corner_radius=(2.0, 2.0, 2.0, 2.0),
        binding_width=0.45,
        base=lambda theta, z: foam_only.outer_offset(theta, z) + 0.03,
        step=0.7,
        role="pocket",
    )
    build_foam_panel(builder, pocket)
    layers.add(pocket)

    # Centre-front entry zip: tape closing the seam, coil teeth on top and a
    # moulded pull at the neck.
    zip_speed = float(np.linalg.norm(envelope_frame(0.0, 0.0)[2]))
    tape_width = 2.0 * FRONT_ZIP_HALF_GAP_DEG * zip_speed - 0.08
    zip_path = [(0.0, VEST_BOTTOM_Z_CM + 0.35), (0.0, FRONT_NECK_Z_CM - 0.5)]
    add_surface_ribbon(builder, "FrontZipTape", zip_path, tape_width, 0.1, "PfdLabel", layers,
                       gap=0.0, taut=False, floor=0.0, width_samples=4, role="zip")
    teeth = add_surface_ribbon(builder, "FrontZipCoil", zip_path, 0.62, 0.26, "PfdHardware", layers,
                               gap=0.0, taut=False, floor=0.12, width_samples=3, role="zip")
    point, axes, _, _, index = ribbon_frame(teeth, 0.97)
    # The pull is narrower than the zip gap so it never rides on the foam.
    add_rounded_block(builder, "FrontZipPull", point + axes[2] * (teeth.base[index].max() + 0.26 + 0.05 + 0.16),
                      axes, (1.0, 0.3, 0.16))

    # Pocket zip runs under the pocket's top edge.
    pocket_zip = add_surface_ribbon(
        builder,
        "ChestPocketZip",
        [(POCKET_THETA_DEG[0] + 4.0, 7.2), (0.5 * sum(POCKET_THETA_DEG), 8.0), (POCKET_THETA_DEG[1] - 4.0, 4.9)],
        0.55,
        0.22,
        "PfdHardware",
        layers,
        gap=0.02,
        taut=False,
        width_samples=3,
        role="zip",
    )
    point, axes, _, _, index = ribbon_frame(pocket_zip, 0.06)
    add_rounded_block(builder, "ChestPocketZipPull", point + axes[2] * (pocket_zip.base[max(index - 3, 0): index + 4].max() + 0.22 + 0.04 + 0.18),
                      axes, (1.0, 0.5, 0.18))

    # The padded shoulder straps are fitted to each wearer
    # (build_production_pfd_shoulder_straps.py): one rigid strap could only
    # rest on the highest shoulders and stood proud of the rest. The shared
    # shell carries their mounts: a ladder-lock on each chest tab, its
    # adjustment tail hanging below, and a sewn webbing anchor on the back
    # panel. Each strap is routed to meet them.
    mounts: dict[str, dict[str, list[float]]] = {}
    for side in (1.0, -1.0):
        z_buckle = FRONT_SHOULDER_Z_CM - SHOULDER_BUCKLE_DROP_CM
        theta = shoulder_strap_theta(z_buckle)
        theta = theta if side > 0.0 else 360.0 - theta
        point, normal, along, across = surface_axes(theta, z_buckle)
        half_extents = (1.0, 1.75, 0.24)
        base = footprint_offset(layers, theta, z_buckle, half_extents[1] + 0.2, half_extents[0] + 0.2)
        centre = point + normal * (base + STRAP_GAP_CM + half_extents[2])
        add_rounded_block(
            builder,
            f"ShoulderAdjustBuckle_{side:+.0f}",
            centre,
            np.stack([along, across, normal]),
            half_extents,
        )
        add_surface_ribbon(builder, f"ShoulderAdjustTail_{side:+.0f}",
                           [(theta, z_buckle - half_extents[0] - 0.3), (theta, z_buckle - 7.5)],
                           WEBBING_WIDTH_CM, WEBBING_THICKNESS_CM, "PfdWebbing", layers)
        z_anchor = BACK_TOP_Z_CM - SHOULDER_ANCHOR_DROP_CM
        back_theta = shoulder_strap_theta(z_anchor, back=True)
        back_theta = back_theta if side > 0.0 else 360.0 - back_theta
        anchor = add_surface_ribbon(
            builder,
            f"ShoulderStrapAnchor_{side:+.0f}",
            [(back_theta, z_anchor - 2.0), (back_theta, BACK_TOP_Z_CM - 1.2)],
            WEBBING_WIDTH_CM,
            WEBBING_THICKNESS_CM,
            "PfdWebbing",
            layers,
        )
        key = "+1" if side > 0.0 else "-1"
        mounts[f"front_buckle_{key}"] = {
            # The strap's webbing enters the buckle at its top edge.
            "point": [round(float(v), 4) for v in centre + along * half_extents[0]],
            "normal": [round(float(v), 4) for v in normal],
        }
        top = anchor.base[-1].max() + WEBBING_THICKNESS_CM
        anchor_point = surface_offset_point(anchor.theta[-1], anchor.z[-1], top)
        mounts[f"back_anchor_{key}"] = {
            "point": [round(float(v), 4) for v in anchor_point],
            "z_range": [round(z_anchor - 2.0, 3), round(BACK_TOP_Z_CM - 1.2, 3)],
        }

    # Side adjustment: webbing anchored on the back panel runs forward OVER
    # the side panel, through a ladder-lock on the front panel, and its tail
    # lies on the front foam. Every point rides on the foam beneath it.
    for side in (1.0, -1.0):
        for index, z in enumerate(SIDE_STRAP_Z_CM):
            path = [
                (BACK_SIDE_SEAM_DEG + 16.0, z),
                (0.5 * (BACK_SIDE_SEAM_DEG + FRONT_SIDE_SEAM_DEG), z),
                (FRONT_SIDE_SEAM_DEG - 24.0, z),
            ]
            if side < 0.0:
                path = [(360.0 - t, h) for t, h in path]
            strap = add_surface_ribbon(builder, f"SideAdjustStrap_{side:+.0f}_{index + 1}", path,
                                       WEBBING_WIDTH_CM, WEBBING_THICKNESS_CM, "PfdWebbing", layers)
            # The ladder-lock sits on the front panel just ahead of the seam.
            point, axes, _, _, k = ribbon_frame(strap, 0.8)
            footprint = slice(max(k - 4, 0), k + 5)
            add_rounded_block(
                builder,
                f"SideAdjustBuckle_{side:+.0f}_{index + 1}",
                point + axes[2] * (strap.base[footprint].max() + WEBBING_THICKNESS_CM + 0.04 + 0.22),
                axes,
                (1.15, 1.75, 0.22),
            )

    # Lash tab high on the left chest, where guides carry a river knife;
    # low-profile reflective accents front and back, and a blank back label
    # (no branding).
    add_surface_ribbon(builder, "LashTab", [(360.0 - 30.0, 4.5), (360.0 - 30.0, 11.5)],
                       WEBBING_WIDTH_CM, 0.22, "PfdWebbing", layers, role="strap")
    for side in (1.0, -1.0):
        strip = [(16.0, 12.8), (30.0, 13.6)]
        add_surface_ribbon(builder, f"ChestReflective_{side:+.0f}",
                           flip_outline(strip, side) if side < 0.0 else strip,
                           0.9, 0.06, "PfdReflective", layers, gap=0.02, taut=False, role="accent")
        back_strip = [(180.0 - 22.0 * side, BACK_TOP_Z_CM - 4.0), (180.0 - 8.0 * side, BACK_TOP_Z_CM - 3.4)]
        add_surface_ribbon(builder, f"BackReflective_{side:+.0f}", back_strip,
                           0.9, 0.06, "PfdReflective", layers, gap=0.02, taut=False, role="accent")
    add_surface_ribbon(builder, "BlankBackLabel", [(172.0, BACK_TOP_Z_CM - 8.5), (188.0, BACK_TOP_Z_CM - 8.5)],
                       3.2, 0.08, "PfdLabel", layers, gap=0.02, taut=False, role="accent")
    return {"foam_panels": [panel.name for panel in foam_panels], "layers": layers, "mounts": mounts}


# ---------------------------------------------------------------------------
# Torso fit (only with --fit-torsos DIR)
# ---------------------------------------------------------------------------
def load_torso_points(path: Path) -> np.ndarray:
    """x,y,z (cm, vest frame) from a dump with or without a header row."""
    lines = path.read_text(encoding="utf-8").splitlines()
    header = [cell.strip().lower() for cell in lines[0].split(",")]
    columns = [0, 1, 2]
    if any(cell and cell[0].isalpha() for cell in header):
        for names in (("x", "y", "z"), ("px", "py", "pz")):
            if all(name in header for name in names):
                columns = [header.index(name) for name in names]
                break
        lines = lines[1:]
    rows = [line.split(",") for line in lines if line.strip()]
    return np.asarray([[float(row[c]) for c in columns] for row in rows])


def fit_coverage(theta_folded: np.ndarray, z: np.ndarray) -> np.ndarray:
    """First guess at where foam will lie; the rest is armhole, neck or seat."""
    front_limit = np.interp(
        z,
        [ARMPIT_Z_CM, FRONT_SHOULDER_Z_CM - SHOULDER_STRAP_OVERLAP_CM, FRONT_SHOULDER_Z_CM],
        [FRONT_SIDE_SEAM_DEG + 8.0, 55.0, 42.0],
    )
    back_limit = np.interp(
        z,
        [ARMPIT_Z_CM, BACK_TOP_Z_CM - SHOULDER_STRAP_OVERLAP_CM, BACK_TOP_Z_CM],
        [BACK_SIDE_SEAM_DEG - 8.0, 125.0, 138.0],
    )
    covered = (z <= ARMPIT_Z_CM + 1.0) | (theta_folded <= front_limit) | (theta_folded >= back_limit)
    covered &= z >= VEST_BOTTOM_Z_CM - 2.0
    covered &= ~((theta_folded < 90.0) & (z > FRONT_SHOULDER_Z_CM + 1.0))
    covered &= ~((theta_folded >= 90.0) & (z > BACK_TOP_Z_CM + 1.0))
    return covered


def panel_coverage(theta_folded: np.ndarray, z: np.ndarray, margin_cm: float = 2.0) -> np.ndarray:
    """Torso under (or within `margin_cm` of) the actual foam panel outlines.

    Taken from the panels built on the current envelope, so the fit and the
    armhole cut agree: skin just past an armhole edge still pushes that edge
    clear, while the arm's own junction beyond it does not inflate the vest.
    """
    covered = np.zeros(np.shape(z), dtype=bool)
    for panel in (front_panel(1.0), back_panel(), side_panel(1.0)):
        rel = theta_folded - panel.theta_start
        inside = (rel >= 0.0) & (rel <= panel.span)
        bottom, top = panel.edges(np.clip(rel, 0.0, panel.span))
        inside &= (z >= bottom) & (z <= top)
        # Developed distance to the outline, so the margin also reaches
        # sideways past steep edges such as the armhole.
        per_degree = panel.length / panel.span
        s = np.where(
            rel < 0.0,
            rel * per_degree,
            np.where(rel > panel.span, panel.length + (rel - panel.span) * per_degree, panel.s_of(np.clip(rel, 0.0, panel.span))),
        )
        candidates = ~inside & (rel > -30.0) & (rel < panel.span + 30.0)
        near = np.zeros_like(inside)
        if candidates.any():
            near[candidates] = (
                distance_to_polyline(np.stack([s[candidates], z[candidates]], -1), panel._boundary) <= margin_cm
            )
        covered |= inside | near
    return covered


def ray_polygon_radius(polygon: np.ndarray, centre: np.ndarray, angles_deg: np.ndarray) -> np.ndarray:
    """Distance from `centre` to a convex polygon along each angle."""
    directions = np.stack([np.cos(np.radians(angles_deg)), np.sin(np.radians(angles_deg))], -1)
    a = polygon
    edge = np.roll(polygon, -1, axis=0) - polygon
    result = np.full(len(angles_deg), np.inf)
    for i, direction in enumerate(directions):
        denominator = direction[0] * edge[:, 1] - direction[1] * edge[:, 0]
        offset = a - centre
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (offset[:, 0] * edge[:, 1] - offset[:, 1] * edge[:, 0]) / denominator
            u = (offset[:, 0] * direction[1] - offset[:, 1] * direction[0]) / denominator
        valid = (np.abs(denominator) > 1e-12) & (u >= -1e-9) & (u <= 1.0 + 1e-9) & (t > 0.0)
        result[i] = t[valid].min()
    return result


def rolling_ball_closing(values: np.ndarray, spacing: float, radius: float) -> np.ndarray:
    """Morphological closing of r(z) by a ball: fills only tight concavities."""
    reach = int(radius // spacing)
    offsets = np.arange(-reach, reach + 1) * spacing
    cap = np.sqrt(np.maximum(radius * radius - offsets * offsets, 0.0)) - radius
    count = len(values)
    padded = np.concatenate([np.full(reach, values[0]), values, np.full(reach, values[-1])])
    dilated = np.array([max(padded[i + reach + k] + cap[k + reach] for k in range(-reach, reach + 1)) for i in range(count)])
    padded = np.concatenate([np.full(reach, dilated[0]), dilated, np.full(reach, dilated[-1])])
    return np.array([min(padded[i + reach + k] - cap[k + reach] for k in range(-reach, reach + 1)) for i in range(count)])


def torso_only(points: np.ndarray, axis_x: float) -> np.ndarray:
    """Keep the innermost skin layer at every height and angle: the torso.

    The dumps hold every body vertex in a box round the chest, so the arms
    beside the ribs, the hands on the paddle and the thighs share slices with
    the torso. Seen from the spine axis they always lie beyond the torso's own
    skin at that angle, so a thin innermost layer per 1 cm x 4 degree bin is
    the torso. One wearer at a time: wearers differ by more than the layer.
    A point must also lie within a few centimetres of its neighbouring bins'
    innermost skin, so a bin the sparse skin mesh happens to miss cannot
    promote a hand or forearm to "torso" (the chest's own curvature, up to
    about 2 cm between neighbouring bins, stays in).
    """
    theta = np.degrees(np.arctan2(points[:, 1], points[:, 0] - axis_x))
    radius = np.hypot(points[:, 0] - axis_x, points[:, 1])
    z_bin = np.floor(points[:, 2]).astype(int)
    z_bin -= z_bin.min()
    a_bin = np.floor((theta + 180.0) / 4.0).astype(int) % 90
    innermost = np.full((z_bin.max() + 1, 90), np.inf)
    np.minimum.at(innermost, (z_bin, a_bin), radius)
    padded = np.pad(innermost, ((1, 1), (0, 0)), constant_values=np.inf)
    neighbourhood = np.full_like(innermost, np.inf)
    for dz in (0, 1, 2):
        for da in (-2, -1, 0, 1, 2):
            neighbourhood = np.minimum(neighbourhood, np.roll(padded[dz : dz + len(innermost)], da, axis=1))
    keep = (radius <= innermost[z_bin, a_bin] + 1.5) & (radius <= neighbourhood[z_bin, a_bin] + 4.0)
    # Where an arm presses on the ribs (armpit, forearm on the hip) its inner
    # skin passes the layer test; the rib cage is no wider than the flanks
    # measured at the waist, where the arms hang clear.
    flank = keep & (np.abs(points[:, 0] - axis_x) < 3.0) & (np.abs(points[:, 2]) <= 3.0)
    widths = [
        np.sort(np.abs(points[flank & (np.floor(points[:, 2]) == level), 1]))[-2]
        for level in range(-3, 3)
        if np.count_nonzero(flank & (np.floor(points[:, 2]) == level)) >= 3
    ]
    keep &= np.abs(points[:, 1]) <= float(np.median(widths)) + 1.2
    return points[keep]


def fit_envelope(torso_dir: Path) -> dict[str, object]:
    global ENVELOPE_AXIS_X_CM, ENVELOPE_Z0_CM, ENVELOPE_RADIUS_CM
    bodies = [load_torso_points(torso_dir / f"torso-vertices-{i}.csv") for i in range(1, 6)]
    mirror = np.array([1.0, -1.0, 1.0])
    whole = np.concatenate(bodies)
    whole = np.concatenate([whole, whole * mirror])
    # The spine axis sits midway between chest and back at the waist, where
    # no arm or hand shares the central strip.
    strip = whole[(np.abs(whole[:, 1]) < 9.0) & (np.abs(whole[:, 2]) < 6.0)]
    axis_x = round(0.5 * (strip[:, 0].max() + strip[:, 0].min()), 2)
    torsos = [torso_only(body, axis_x) for body in bodies]
    points = np.concatenate(torsos)
    points = np.concatenate([points, points * mirror])
    centre = np.array([axis_x, 0.0])
    folded = np.abs(np.degrees(np.arctan2(points[:, 1], points[:, 0] - axis_x)))
    z0 = math.floor((VEST_BOTTOM_Z_CM - 3.0) / ENVELOPE_DZ_CM) * ENVELOPE_DZ_CM
    z1 = math.ceil((max(FRONT_SHOULDER_Z_CM, BACK_TOP_Z_CM) + 3.0) / ENVELOPE_DZ_CM) * ENVELOPE_DZ_CM
    levels = np.arange(z0, z1 + 1e-6, ENVELOPE_DZ_CM)
    angles = np.arange(0.0, 180.0 + 1e-6, ENVELOPE_ANGLE_STEP_DEG)
    ENVELOPE_AXIS_X_CM = axis_x
    ENVELOPE_Z0_CM = float(z0)

    def solve(covered: np.ndarray) -> np.ndarray:
        global ENVELOPE_RADIUS_CM
        table = np.zeros((len(levels), len(angles)))
        for row, level in enumerate(levels):
            window = covered[np.abs(covered[:, 2] - level) <= 0.75 * ENVELOPE_DZ_CM + 0.5]
            if len(window) < 30:
                table[row] = table[row - 1]
                continue
            section = offset_convex_polygon(convex_hull_2d(window[:, :2]), ENVELOPE_CLEARANCE_CM)
            table[row] = ray_polygon_radius(section, centre, angles)
        for column in range(len(angles)):
            table[:, column] = rolling_ball_closing(table[:, column], ENVELOPE_DZ_CM, ENVELOPE_ROLLING_BALL_CM)
        for _ in range(3):
            clearance = raise_to_clear(table, covered)
            table = convex_rows(table)
        return raise_to_clear(table, covered)

    def convex_rows(table: np.ndarray) -> np.ndarray:
        """Re-close each horizontal section into a convex outline.

        Local clearance bumps would otherwise leave narrow ridges that the
        panel mesh's chords cut under; foam bridges hollows anyway.
        """
        mirrored_angles = np.radians(np.concatenate([angles, -angles[1:-1]]))
        result = table.copy()
        for row in range(len(table)):
            radius = np.concatenate([table[row], table[row, 1:-1]])
            outline = np.stack([radius * np.cos(mirrored_angles), radius * np.sin(mirrored_angles)], -1)
            result[row] = np.maximum(
                table[row], ray_polygon_radius(convex_hull_2d(outline), np.zeros(2), angles)
            )
        return result

    def raise_to_clear(table: np.ndarray, covered: np.ndarray) -> np.ndarray:
        """Raise nodes until every covered vertex clears the bicubic surface."""
        global ENVELOPE_RADIUS_CM
        target = ENVELOPE_CLEARANCE_CM - 0.04
        p_theta = np.degrees(np.arctan2(covered[:, 1], covered[:, 0] - axis_x))
        p_radius = np.hypot(covered[:, 0] - axis_x, covered[:, 1])
        for _ in range(60):
            ENVELOPE_RADIUS_CM = tuple(tuple(row) for row in table)
            _, normal, _, _ = envelope_frame(p_theta, covered[:, 2])
            radial = np.stack([np.cos(np.radians(p_theta)), np.sin(np.radians(p_theta)), np.zeros(len(p_theta))], -1)
            cosine = np.maximum((normal * radial).sum(-1), 0.3)
            clearance = (envelope_radius(p_theta, covered[:, 2]) - p_radius) * cosine
            # The tangent-plane estimate overstates clearance where the shell
            # turns sharply (armhole edges); near the surface, measure the
            # true distance to it over a local patch instead.
            near = np.flatnonzero(clearance < target + 0.6)
            if len(near):
                d_theta, d_z = np.meshgrid(np.linspace(-8.0, 8.0, 33), np.linspace(-3.0, 3.0, 25))
                for first in range(0, len(near), 400):
                    chunk = near[first : first + 400]
                    patch = envelope_point(
                        p_theta[chunk, None] + d_theta.ravel()[None, :],
                        covered[chunk, 2, None] + d_z.ravel()[None, :],
                    )
                    distance = np.linalg.norm(patch - covered[chunk, None, :], axis=-1).min(axis=1)
                    clearance[chunk] = np.minimum(clearance[chunk], distance)
            deficit = target - clearance
            if deficit.max() <= 0.0:
                break
            bad = deficit > 0.0
            rows = np.clip(np.rint((covered[bad, 2] - z0) / ENVELOPE_DZ_CM).astype(int), 0, len(levels) - 1)
            cols = np.clip(np.rint(np.abs(p_theta[bad]) / ENVELOPE_ANGLE_STEP_DEG).astype(int), 0, len(angles) - 1)
            lift = deficit[bad] / cosine[bad] + 0.02
            bump = np.zeros_like(table)
            for r, c, value in zip(rows, cols, lift):
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr = min(max(r + dr, 0), len(levels) - 1)
                        cc = min(max(c + dc, 0), len(angles) - 1)
                        weight = 1.0 if dr == 0 and dc == 0 else 0.5
                        bump[rr, cc] = max(bump[rr, cc], value * weight)
            table += bump
        ENVELOPE_RADIUS_CM = tuple(tuple(float(v) for v in row) for row in np.round(table, 2))
        return clearance

    # Two passes: a first guess at the panel layout, then the coverage of the
    # panels actually cut on that first envelope.
    solve(points[fit_coverage(folded, points[:, 2])])
    clearance = solve(points[panel_coverage(folded, points[:, 2])])
    report = {}
    for index, (body, torso) in enumerate(zip(bodies, torsos), start=1):
        report[index] = {"vertices": len(body), "torso_vertices": len(torso)}
    return {"axis_x": axis_x, "z0": z0, "levels": len(levels), "bodies": report,
            "final_min_estimated_clearance_cm": float(clearance.min())}


def fitted_envelope_source() -> str:
    rows = ",\n".join(
        "    (" + ", ".join(f"{value:.2f}" for value in row) + ")" for row in ENVELOPE_RADIUS_CM
    )
    return (
        "# >>> fitted envelope\n"
        f"ENVELOPE_AXIS_X_CM = {ENVELOPE_AXIS_X_CM:.2f}\n"
        f"ENVELOPE_Z0_CM = {ENVELOPE_Z0_CM:.1f}\n"
        "# Rows rise by ENVELOPE_DZ_CM from ENVELOPE_Z0_CM; columns sweep 0 (front)\n"
        "# to 180 degrees (spine) by ENVELOPE_ANGLE_STEP_DEG.\n"
        "ENVELOPE_RADIUS_CM: tuple[tuple[float, ...], ...] = (\n"
        f"{rows},\n)\n"
        "# <<< fitted envelope\n"
    )


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


def orient_outward(mesh_object: bpy.types.Object) -> int:
    """Make every closed piece face outward; returns non-manifold edge count."""
    mesh = mesh_object.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    open_edges = sum(1 for edge in bm.edges if not edge.is_manifold)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return open_edges


def validate(mesh_object: bpy.types.Object, open_edges: int) -> dict[str, object]:
    slots = [slot.name for slot in mesh_object.data.materials]
    if slots != MATERIAL_NAMES:
        raise RuntimeError(f"Production PFD material contract changed: {slots}")
    if not mesh_object.data.uv_layers:
        raise RuntimeError("Production PFD has no UV channel")
    if open_edges:
        raise RuntimeError(f"Production PFD pieces are not closed: {open_edges} open edges")
    if len(mesh_object.data.polygons) < 10_000:
        raise RuntimeError(
            f"Production PFD is unexpectedly low detail: {len(mesh_object.data.polygons)} polygons"
        )
    coordinates = np.empty(len(mesh_object.data.vertices) * 3)
    mesh_object.data.vertices.foreach_get("co", coordinates)
    coordinates = coordinates.reshape(-1, 3)
    minimum = coordinates.min(0)
    maximum = coordinates.max(0)
    dimensions = maximum - minimum
    if not (
        26.0 <= dimensions[0] <= 44.0
        and 30.0 <= dimensions[1] <= 44.0
        and 30.0 <= dimensions[2] <= 56.0
    ):
        raise RuntimeError(f"Production PFD bounds are implausible: {tuple(dimensions)}")
    triangles = sum(len(polygon.vertices) - 2 for polygon in mesh_object.data.polygons)
    return {
        "vertex_count": len(mesh_object.data.vertices),
        "polygon_count": len(mesh_object.data.polygons),
        "triangle_count": triangles,
        "open_edges": open_edges,
        "material_slots": slots,
        "uv_channel_count": len(mesh_object.data.uv_layers),
        "bounds_min_cm": [round(float(value), 4) for value in minimum],
        "bounds_max_cm": [round(float(value), 4) for value in maximum],
        "dimensions_cm": [round(float(value), 4) for value in dimensions],
    }


def main() -> None:
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if "--fit-torsos" in arguments:
        report = fit_envelope(Path(arguments[arguments.index("--fit-torsos") + 1]))
        print(json.dumps(report, indent=2))
        if "--update-source" in arguments:
            source_path = Path(__file__)
            text = source_path.read_text(encoding="utf-8")
            start = text.index("# >>> fitted envelope\n")
            end = text.index("# <<< fitted envelope\n") + len("# <<< fitted envelope\n")
            source_path.write_text(text[:start] + fitted_envelope_source() + text[end:], encoding="utf-8", newline="\n")
        return
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    reset_scene()
    # One Blender unit is one centimetre. UE 5.8's Interchange FBX import
    # applies node transforms, so the unit must live in the scene: a metre
    # scene exports Lcl Scaling 100 (a 100x mesh) or needs a compensating
    # export scale. Matches the helmet, sandal and boot generators.
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 0.01
    bpy.context.scene.unit_settings.length_unit = "CENTIMETERS"
    materials = {
        "PfdShell": material("PfdShell", (0.7, 0.03, 0.01, 1.0), 0.78),
        "PfdWebbing": material("PfdWebbing", (0.01, 0.012, 0.014, 1.0), 0.72),
        "PfdHardware": material("PfdHardware", (0.04, 0.045, 0.05, 1.0), 0.55),
        "PfdReflective": material("PfdReflective", (0.72, 0.75, 0.72, 1.0), 0.24),
        "PfdLabel": material("PfdLabel", (0.08, 0.085, 0.09, 1.0), 0.68),
    }
    builder = MeshBuilder()
    layout = build_vest(builder)
    mesh_object = builder.to_object("SM_RaftSim_WhitewaterRescuePfd", materials)
    open_edges = orient_outward(mesh_object)
    audit = validate(mesh_object, open_edges)
    bpy.ops.object.select_all(action="DESELECT")
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
        # Centimetre scene units carry the scale: FBX unit factor 1, no
        # node scaling.
        apply_scale_options="FBX_SCALE_ALL",
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
                "url": "https://astraldesigns.com/products/greenjacket",
                "facts_used": "low-profile contoured foam guide vest, front entry, large chest pocket, padded adjustable shoulders, open armholes",
                "asset_content_copied": False,
            },
            {
                "url": "https://www.nrs.com/nrs-ninja-pfd/pvdx",
                "facts_used": "short cut that clears a seat, large armholes, side adjustment straps over the side panels, lash tab and reflective accents",
                "asset_content_copied": False,
            },
            {
                "url": "https://www.stohlquist.com/rocker-pfd",
                "facts_used": "slim front and back foam panels, padded shoulder straps with front adjusters",
                "asset_content_copied": False,
            },
        ],
        "fbx": str(FBX_PATH.relative_to(REPO_ROOT)),
        "blend": str(BLEND_PATH.relative_to(REPO_ROOT)),
        "fbx_sha256": sha256(FBX_PATH),
        "blend_sha256": sha256(BLEND_PATH),
        "material_slots": MATERIAL_NAMES,
        "construction": {
            "style": "low-profile front-entry whitewater guide vest",
            "front_foam_panels": 2,
            "back_panels": 1,
            "side_panels": 2,
            "side_wings": 0,
            # The padded straps are separate per-wearer meshes
            # (SM_RaftSim_PfdShoulderStraps_*); this shell carries their mounts.
            "padded_shoulder_straps": 0,
            "shoulder_adjustment_buckles": 2,
            "shoulder_strap_anchors": 2,
            "side_adjustment_straps": 4,
            "side_adjustment_buckles": 4,
            "adjustment_points": 6,
            "front_zip": 1,
            "front_pockets": 1,
            "front_lash_tabs": 1,
            "reflective_accents": 4,
            "blank_back_labels": 1,
            "quick_release_rescue_belts": 0,
            "rescue_tether_rings": 0,
        },
        "soft_geometry": {
            "panel_profile": "flat lining, quarter-round rolled edge under a sewn binding, gently crowned face",
            "front_panel_foam_thickness_cm": FRONT_FOAM_CM,
            "back_panel_foam_thickness_cm": BACK_FOAM_CM,
            "side_panel_foam_thickness_cm": SIDE_FOAM_CM,
            "webbing_width_cm": WEBBING_WIDTH_CM,
            "webbing_thickness_cm": WEBBING_THICKNESS_CM,
            "strap_surface_gap_cm": STRAP_GAP_CM,
            "hem_height_cm": VEST_BOTTOM_Z_CM,
            "smooth_shaded": True,
        },
        "fit": {
            "inner_surface": "convex envelope of the five seated crew torsos (runtime fit scale removed), mirrored, plus clearance",
            "envelope_clearance_cm": ENVELOPE_CLEARANCE_CM,
            "straps": "every strap, buckle and webbing piece rides on the outer surface of what lies beneath it",
            "panel_tops_cm": {"front_tab": FRONT_SHOULDER_Z_CM, "back": BACK_TOP_Z_CM},
        },
        "shoulder_straps": {
            "meshes": "SM_RaftSim_PfdShoulderStraps_{Crew01,Crew02,Crew03,Crew04,Guide}",
            "generator": "unreal/Scripts/build_production_pfd_shoulder_straps.py",
            "strap_plane_y_cm": SHOULDER_STRAP_Y_CM,
            "mounts": layout["mounts"],
        },
        "runtime_boundary": "Collisionless torso-following safety-gear visual; body animation, seat mass, D3/D4, rescue and swimmer authority remain native.",
        # Vertex ranges let fit audits test foam, straps and hardware apart.
        "pieces": {
            name: {"role": builder.piece_roles[name], "vertex_range": list(span)}
            for name, span in builder.piece_ranges.items()
        },
        **audit,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
