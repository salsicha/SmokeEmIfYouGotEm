"""Build the production PFD's padded shoulder straps, fitted to each wearer.

Run with Blender, not the system Python::

    Blender --background --python unreal/Scripts/build_production_pfd_shoulder_straps.py
    Blender --background --python ... -- --fit-torsos DIR [DIR ...]   (re-measure)

The shared vest shell (build_production_whitewater_pfd.py) carries a
ladder-lock on each chest tab and a sewn webbing anchor on the back panel.
Every wearer gets their own pair of straps between those mounts, in the
vest's mesh frame: webbing out of the buckle, then a narrow padded strap
inboard over the trapezius, between the neck and the acromion, laid snug on
that wearer's own shoulder and down onto the back anchor. One rigid pair
could only rest on the highest of the five shoulders and stood several cm
proud of the lower ones ("the vest shoulder straps seem too high", and the
raised T-grip arm's deltoid passed under a strap that ran out over the
shoulder joint, 2026-10-07).

Each wearer's shoulders come from their seated torso dump in the vest frame
(runtime fit scale removed), reduced to the convex outline of the skin or
shirt under each lateral strip of the strap (crew_shoulder_profiles.json).
No external mesh or texture is used.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_production_whitewater_pfd as pfd  # noqa: E402  (the shell the straps join)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionPfd/ShoulderStraps"
PROFILE_PATH = OUTPUT_ROOT / "crew_shoulder_profiles.json"
MANIFEST_PATH = OUTPUT_ROOT / "production_pfd_shoulder_straps_manifest.json"
BLEND_PATH = OUTPUT_ROOT / "SM_RaftSim_PfdShoulderStraps.blend"
GENERATOR_VERSION = 1
WEARERS = ["Crew01", "Crew02", "Crew03", "Crew04", "Guide"]
# torso-vertices-N.csv -> wearer. Matched by geometry: each dump's head
# (head-vertices-N.csv, helmet frame) against the dressed CC0 heads placed
# with the helmet fit (build_production_helmet_straps.py), median nearest
# distance 0.22-0.78 cm for the match against 1.3+ cm for the next best.
DUMP_WEARERS = ("Crew01", "Crew02", "Crew04", "Crew03", "Guide")

STRAP_WIDTH_CM = 4.0
PADDED_THICKNESS_CM = 0.6
# The strap's flat face rides this far off the skin or shirt beneath it.
SKIN_GAP_CM = 0.35
STRIPS = 4
# Above this the dumps hold the head and hair (Crew03's bob ends above it
# over the strap band), which hang beside the strap, never under it.
HEAD_CUT_Z_CM = 33.0
# Shoulder footprint is measured from this height up (below it the strap
# lies on the vest's own panels).
PROFILE_FLOOR_Z_CM = 12.0
BINDING_CM = 0.35
# The strap's sagittal plane is read as radius per angle about this point
# (x, z): 0 degrees forward, 90 up, 180 backward. Every shoulder outline is
# star-shaped from here, from the chest tab over the trapezius to the back.
POLAR_CENTRE_XZ = (-1.0, 12.0)
POLAR_STEP_DEG = 1.0
# Only notches narrower than this ball are bridged by the strap.
SMOOTHING_BALL_CM = 10.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Shoulder profiles (only with --fit-torsos DIR [DIR ...])
# ---------------------------------------------------------------------------
def polar_profile(points_xz: np.ndarray, gap: float) -> np.ndarray:
    """Outermost radius (+gap) about POLAR_CENTRE_XZ per angle bin; NaN where empty."""
    angles = np.arange(0.0, 180.0 + 1e-6, POLAR_STEP_DEG)
    result = np.full(len(angles), np.nan)
    if len(points_xz):
        relative = points_xz - np.asarray(POLAR_CENTRE_XZ)
        angle = np.degrees(np.arctan2(relative[:, 1], relative[:, 0]))
        bins = np.rint(angle / POLAR_STEP_DEG).astype(int)
        valid = (bins >= 0) & (bins < len(angles))
        np.fmax.at(result, bins[valid], np.hypot(relative[valid, 0], relative[valid, 1]) + gap)
    return result


def fit_profiles(torso_dirs: list[Path]) -> dict[str, object]:
    """Profiles from one or more rest-pose dump sets; the outermost of them
    wins, so the strap clears every capture of the same seated pose."""
    half = STRAP_WIDTH_CM * 0.5
    edges = np.linspace(-half, half, STRIPS + 1)
    profiles: dict[str, dict[str, list]] = {}
    for index, wearer in enumerate(DUMP_WEARERS, start=1):
        body = np.concatenate(
            [pfd.load_torso_points(directory / f"torso-vertices-{index}.csv") for directory in torso_dirs]
        )
        body = body[(body[:, 2] >= PROFILE_FLOOR_Z_CM) & (body[:, 2] <= HEAD_CUT_Z_CM)]
        sides: dict[str, list] = {}
        for side in (1.0, -1.0):
            lateral = side * body[:, 1] - pfd.SHOULDER_STRAP_Y_CM
            strips = []
            for j in range(STRIPS):
                strip = body[(lateral >= edges[j] - 0.3) & (lateral <= edges[j + 1] + 0.3)]
                radius = polar_profile(strip[:, [0, 2]], 0.0)
                strips.append([None if np.isnan(r) else round(float(r), 2) for r in radius])
            sides["+1" if side > 0.0 else "-1"] = strips
        profiles[wearer] = sides
    sources = []
    for directory in torso_dirs:
        try:
            sources.append(directory.resolve().relative_to(REPO_ROOT).as_posix() + "/torso-vertices-{1..5}.csv")
        except ValueError:
            sources.append(directory.as_posix() + "/torso-vertices-{1..5}.csv")
    return {
        "schema": "raftsim.pfd_shoulder_profiles.v2",
        "description": (
            "Outermost radius (cm) of each wearer's skin or shirt about polar_centre_xz in the "
            "strap's sagittal plane, per polar_step_deg from 0 (forward) to 180 (backward), "
            "under each lateral strip of the strap, inner to outer; seated rest pose, vest frame."
        ),
        "sources": sources,
        "dump_wearers": list(DUMP_WEARERS),
        "strap_plane_y_cm": pfd.SHOULDER_STRAP_Y_CM,
        "strap_width_cm": STRAP_WIDTH_CM,
        "strips": STRIPS,
        "polar_centre_xz": list(POLAR_CENTRE_XZ),
        "polar_step_deg": POLAR_STEP_DEG,
        "floor_z_cm": PROFILE_FLOOR_Z_CM,
        "head_cut_z_cm": HEAD_CUT_Z_CM,
        "profiles": profiles,
    }


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
def supporting_slope_at_zero(points: np.ndarray) -> float:
    """Slope of the line resting on the upper hull of (a, h) points at a = 0."""
    if len(points) < 2:
        return 0.0
    hull: list[tuple[float, float]] = []
    for point in sorted(map(tuple, points.tolist())):
        while len(hull) >= 2:
            (ox, oy), (ax, ay) = hull[-2], hull[-1]
            if (ax - ox) * (point[1] - oy) - (ay - oy) * (point[0] - ox) >= 0.0:
                hull.pop()
            else:
                break
        hull.append(point)
    for (ax, ay), (bx, by) in zip(hull, hull[1:]):
        if ax <= 0.0 <= bx and bx > ax:
            return (by - ay) / (bx - ax)
    return 0.0


def pillow_profile(half_width: float, thickness: float, count: int = 24) -> np.ndarray:
    """Counter-clockwise padded-strap section with its flat face at h = 0."""
    angles = np.linspace(-math.pi / 2.0, 1.5 * math.pi, count, endpoint=False)
    c = np.cos(angles)
    s = np.sin(angles)
    half_height = thickness * 0.5
    return np.stack(
        [
            half_width * np.sign(c) * np.abs(c) ** 0.3,
            half_height + half_height * np.sign(s) * np.abs(s) ** 0.45,
        ],
        -1,
    )


def route(
    side: float,
    body_strips: list[list[float | None]],
    vest_points: np.ndarray,
    front_mount: dict[str, list[float]],
    back_mount: dict[str, object],
) -> dict[str, np.ndarray]:
    """Strap path over one shoulder in the strap's sagittal plane.

    Under each lateral strip, the wearer's skin (plus SKIN_GAP_CM) and the
    vest geometry (plus a webbing gap) give an outermost radius per angle
    about POLAR_CENTRE_XZ. The strap follows the outermost of the strips from
    the buckle, over the trapezius, to the back anchor, bridging only notches
    narrower than a small rolling ball: it lies on the wearer instead of
    spanning taut from the chest tab to the top of the shoulder. At each
    station its flat face then rolls about the path onto the strips, like a
    plank on the sloping trapezius, so it hugs the shoulder without entering
    it.
    """
    centre = np.asarray(POLAR_CENTRE_XZ)
    angles = np.arange(0.0, 180.0 + 1e-6, POLAR_STEP_DEG)
    half = STRAP_WIDTH_CM * 0.5
    edges = np.linspace(-half, half, STRIPS + 1)
    lateral = side * vest_points[:, 1] - pfd.SHOULDER_STRAP_Y_CM
    radii, bodies = [], []
    for j, values in enumerate(body_strips):
        body = np.array([np.nan if v is None else v for v in values], dtype=float)
        vest = polar_profile(
            vest_points[(lateral >= edges[j] - 0.3) & (lateral <= edges[j + 1] + 0.3)][:, [0, 2]],
            pfd.STRAP_GAP_CM,
        )
        radius = np.fmax(body + SKIN_GAP_CM, vest)
        known = np.isfinite(radius)
        radius = np.interp(angles, angles[known], radius[known])
        # A crest between two angle samples must not slip under the strap.
        radius = np.max([np.roll(radius, k) for k in (-1, 0, 1)], axis=0)
        radii.append(radius)
        bodies.append(body)
    radii = np.stack(radii, -1)
    bodies = np.stack(bodies, -1)
    # Each strip bridges the same hollows, so the roll below only tilts the
    # strap across its width and never drops it back into a bridged hollow.
    spacing = float(np.mean(radii)) * math.radians(POLAR_STEP_DEG)
    radii = np.stack(
        [pfd.rolling_ball_closing(radii[:, j], spacing, SMOOTHING_BALL_CM) for j in range(STRIPS)], -1
    )
    path_radius = radii.max(axis=1)

    def angle_of(x: float, z: float) -> float:
        return math.degrees(math.atan2(z - centre[1], x - centre[0]))

    fine = np.arange(
        angle_of(front_mount["point"][0], front_mount["point"][2]),
        angle_of(back_mount["point"][0], back_mount["z_range"][0] + 0.8),
        0.1,
    )
    fine_chain = centre + np.stack([np.cos(np.radians(fine)), np.sin(np.radians(fine))], -1) * np.interp(
        fine, angles, path_radius
    )[:, None]
    fine_length = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(fine_chain, axis=0), axis=-1))])
    # Stations every ~0.5 cm along the strap.
    phi = np.interp(
        np.linspace(0.0, fine_length[-1], max(int(fine_length[-1] / 0.5), 2) + 1), fine_length, fine
    )
    direction = np.stack([np.cos(np.radians(phi)), np.sin(np.radians(phi))], -1)
    path_r = np.interp(phi, angles, path_radius)[:, None]
    chain = centre + direction * path_r
    strip_radius = np.stack([np.interp(phi, angles, radii[:, j]) for j in range(STRIPS)], -1)
    body_radius = np.stack([np.interp(phi, angles, bodies[:, j]) for j in range(STRIPS)], -1)
    tangent2 = np.gradient(chain, axis=0)
    tangent2 /= np.linalg.norm(tangent2, axis=-1, keepdims=True)
    normal2 = np.stack([tangent2[:, 1], -tangent2[:, 0]], -1)
    # Radial reach of each strip past the path, measured along the path normal.
    cosine = np.maximum((direction * normal2).sum(-1), 0.2)[:, None]
    reach = (strip_radius - path_r) * cosine
    slopes = np.array([
        supporting_slope_at_zero(np.stack([np.concatenate([edges[:-1], edges[1:]]), np.concatenate([row, row])], -1))
        for row in reach
    ])
    # The trapezius falls up to ~0.8 cm per cm toward the acromion; a lightly
    # smoothed roll lets the strap's outer edge follow it down.
    slopes = np.clip(np.convolve(np.pad(slopes, 2, mode="edge"), np.ones(5) / 5.0, mode="valid"), -1.2, 1.2)
    # Lowest flat face with that roll that still clears every strip.
    lift = np.maximum(reach - slopes[:, None] * edges[:-1], reach - slopes[:, None] * edges[1:]).max(axis=1)
    path = np.stack([chain[:, 0], np.full(len(chain), side * pfd.SHOULDER_STRAP_Y_CM), chain[:, 1]], -1)
    tangent = np.stack([tangent2[:, 0], np.zeros(len(chain)), tangent2[:, 1]], -1)
    up = np.stack([normal2[:, 0], np.zeros(len(chain)), normal2[:, 1]], -1)
    outward = np.array([0.0, side, 0.0])
    across = outward[None, :] + up * slopes[:, None]
    across /= np.linalg.norm(across, axis=-1, keepdims=True)
    face = up - outward[None, :] * slopes[:, None]
    face /= np.linalg.norm(face, axis=-1, keepdims=True)
    # Sections must run counter-clockwise about the direction of travel.
    across *= np.sign((np.cross(across, face) * tangent).sum(-1))[:, None]
    lengths = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(chain, axis=0), axis=-1))])
    # Gap from the strap's flat face down to the wearer's skin or shirt.
    body_reach = (body_radius - path_r) * cosine
    face_low = np.minimum(lift[:, None] + slopes[:, None] * edges[:-1], lift[:, None] + slopes[:, None] * edges[1:])
    body_gap = np.where(np.isfinite(body_reach), face_low - body_reach, np.inf).min(axis=1)
    return {
        "body_gap": body_gap,
        "base": path + up * lift[:, None],
        "tangent": tangent,
        "across": across,
        "face": face,
        "length": lengths,
    }


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
def sweep(
    builder: pfd.MeshBuilder,
    name: str,
    strap: dict[str, np.ndarray],
    span: slice,
    profile: np.ndarray,
    face_offset: float,
    materials: list[str],
    cap_material: str,
) -> None:
    """Sweep a counter-clockwise (across, up) section along part of a strap,
    with a material per section segment (padded face vs sewn binding)."""
    base = strap["base"][span] + strap["face"][span] * face_offset
    rings = (
        base[:, None, :]
        + strap["across"][span][:, None, :] * profile[None, :, 0:1]
        + strap["face"][span][:, None, :] * profile[None, :, 1:2]
    )
    samples, count = rings.shape[:2]
    lengths = strap["length"][span] - strap["length"][span][0]
    perimeter = np.concatenate(
        [[0.0], np.cumsum(np.linalg.norm(np.diff(np.vstack([profile, profile[:1]]), axis=0), axis=-1))]
    )
    builder.begin_piece(name, "strap")
    index = builder.add_points(rings.reshape(-1, 3)).reshape(samples, count)
    for i in range(samples - 1):
        for m in range(count):
            n = (m + 1) % count
            builder.add_face(
                (index[i, m], index[i, n], index[i + 1, n], index[i + 1, m]),
                materials[m],
                ((lengths[i], perimeter[m]), (lengths[i], perimeter[m + 1]),
                 (lengths[i + 1], perimeter[m + 1]), (lengths[i + 1], perimeter[m])),
            )
    builder.add_face(tuple(reversed(index[0].tolist())), cap_material,
                     tuple(reversed([(p[0], p[1]) for p in profile])))
    builder.add_face(index[-1].tolist(), cap_material, [(p[0], p[1]) for p in profile])
    for ring in (index[0], index[-1]):
        for m in range(count):
            builder.sharp_edges.append((ring[m], ring[(m + 1) % count]))
    builder.end_piece()


def build_wearer(builder: pfd.MeshBuilder, routes: dict[float, dict[str, np.ndarray]]) -> dict[str, float]:
    padded = pillow_profile(STRAP_WIDTH_CM * 0.5, PADDED_THICKNESS_CM)
    padded_materials = [
        "PfdLabel" if abs(a) > STRAP_WIDTH_CM * 0.5 - BINDING_CM or abs(b) > STRAP_WIDTH_CM * 0.5 - BINDING_CM
        else "PfdShell"
        for (a, _), (b, _) in zip(padded, np.roll(padded, -1, axis=0))
    ]
    webbing = pfd.stadium_profile(pfd.WEBBING_WIDTH_CM * 0.5, pfd.WEBBING_THICKNESS_CM, 4, 3)
    reflective = pfd.stadium_profile(0.5, 0.05, 3, 2)
    stats = {}
    for side, strap in routes.items():
        label = f"{side:+.0f}"
        z = strap["base"][:, 2]
        # Webbing from the buckle up over the chest tab's top edge; padding
        # from just below that edge (overlapping the webbing) to the anchor.
        pad_start = int(np.argmax(z > pfd.FRONT_SHOULDER_Z_CM + 0.8))
        overlap = int(np.searchsorted(strap["length"], strap["length"][pad_start] - 1.2))
        sweep(builder, f"ShoulderWebbing_{label}", strap, slice(0, pad_start + 1), webbing, 0.0,
              ["PfdWebbing"] * len(webbing), "PfdWebbing")
        sweep(builder, f"PaddedShoulderStrap_{label}", strap, slice(overlap, None), padded, 0.0,
              padded_materials, "PfdLabel")
        # A webbing keeper at the foot of the padding.
        k = max(overlap - 1, 0)
        pfd.add_rounded_block(
            builder,
            f"ShoulderWebbingKeeper_{label}",
            strap["base"][k] + strap["face"][k] * (pfd.WEBBING_THICKNESS_CM + 0.04 + 0.12),
            np.stack([strap["tangent"][k], strap["across"][k], strap["face"][k]]),
            (0.45, 1.5, 0.12),
        )
        # Reflective piping on the front of the padding.
        start = int(np.searchsorted(strap["length"], strap["length"][pad_start] + 1.5))
        stop = int(np.searchsorted(strap["length"], strap["length"][pad_start] + 6.5))
        sweep(builder, f"ShoulderReflective_{label}", strap, slice(start, stop + 1), reflective,
              PADDED_THICKNESS_CM + 0.02, ["PfdReflective"] * len(reflective), "PfdReflective")
        # Over the shoulder (above the panel tops) the strap lies on the
        # wearer; where it leaves a chest tab or the back panel it spans the
        # hollow under the collarbone or across the upper back.
        above_panels = (z > max(pfd.FRONT_SHOULDER_Z_CM, pfd.BACK_TOP_Z_CM) + 1.0) & np.isfinite(strap["body_gap"])
        gap = strap["body_gap"][above_panels]
        stations = np.diff(strap["length"], prepend=strap["length"][0])[above_panels]
        stats[label] = {
            "length_cm": round(float(strap["length"][-1]), 2),
            "top_z_cm": round(float(z.max() + PADDED_THICKNESS_CM), 2),
            "min_skin_gap_cm": round(float(strap["body_gap"].min()), 3),
            "median_skin_gap_above_panels_cm": round(float(np.median(gap)), 3),
            "length_within_0_6_cm_of_skin_cm": round(float(stations[gap <= 0.6].sum()), 1),
            "length_above_panels_cm": round(float(stations.sum()), 1),
        }
    return stats


def main() -> None:
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if "--fit-torsos" in arguments:
        directories = [Path(a) for a in arguments[arguments.index("--fit-torsos") + 1 :] if not a.startswith("--")]
        profiles = fit_profiles(directories)
        PROFILE_PATH.write_text(json.dumps(profiles, indent=1) + "\n", encoding="utf-8")
        print("RAFTSIM_PFD_SHOULDER_PROFILES=" + PROFILE_PATH.as_posix())
        return
    profiles = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    if (
        profiles["strap_plane_y_cm"] != pfd.SHOULDER_STRAP_Y_CM
        or profiles["strap_width_cm"] != STRAP_WIDTH_CM
        or profiles["polar_centre_xz"] != list(POLAR_CENTRE_XZ)
    ):
        raise RuntimeError("Shoulder profiles were measured for another strap layout; re-run --fit-torsos")
    pfd.reset_scene()
    # One Blender unit is one centimetre, exported with FBX_SCALE_ALL, exactly
    # like the vest these straps are parented to.
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 0.01
    bpy.context.scene.unit_settings.length_unit = "CENTIMETERS"
    vest = pfd.MeshBuilder()
    layout = pfd.build_vest(vest)
    vest_points = vest.points()
    mounts = layout["mounts"]
    materials = {
        "PfdShell": pfd.material("PfdShell", (0.7, 0.03, 0.01, 1.0), 0.78),
        "PfdWebbing": pfd.material("PfdWebbing", (0.01, 0.012, 0.014, 1.0), 0.72),
        "PfdHardware": pfd.material("PfdHardware", (0.04, 0.045, 0.05, 1.0), 0.55),
        "PfdReflective": pfd.material("PfdReflective", (0.72, 0.75, 0.72, 1.0), 0.24),
        "PfdLabel": pfd.material("PfdLabel", (0.08, 0.085, 0.09, 1.0), 0.68),
    }
    pfd_manifest = json.loads(pfd.MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = {}
    objects = []
    for wearer in WEARERS:
        routes = {}
        for side in (1.0, -1.0):
            key = "+1" if side > 0.0 else "-1"
            routes[side] = route(
                side,
                profiles["profiles"][wearer][key],
                vest_points,
                mounts[f"front_buckle_{key}"],
                mounts[f"back_anchor_{key}"],
            )
        builder = pfd.MeshBuilder()
        stats = build_wearer(builder, routes)
        name = f"SM_RaftSim_PfdShoulderStraps_{wearer}"
        obj = builder.to_object(name, materials)
        open_edges = pfd.orient_outward(obj)
        if open_edges:
            raise RuntimeError(f"{name} pieces are not closed: {open_edges} open edges")
        slots = [slot.name for slot in obj.data.materials]
        if slots != pfd.MATERIAL_NAMES:
            raise RuntimeError(f"{name} material contract changed: {slots}")
        used = {polygon.material_index for polygon in obj.data.polygons}
        if used != set(range(len(pfd.MATERIAL_NAMES))):
            # Unused slots would be dropped on import and shift the order.
            raise RuntimeError(f"{name} leaves material slots unused: {sorted(used)}")
        objects.append(obj)
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        fbx_path = OUTPUT_ROOT / f"{name}.fbx"
        bpy.ops.export_scene.fbx(
            filepath=str(fbx_path),
            use_selection=True,
            object_types={"MESH"},
            # Same frame and units as SM_RaftSim_WhitewaterRescuePfd.fbx so
            # the runtime attaches each pair with an identity transform.
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
        coordinates = np.empty(len(obj.data.vertices) * 3)
        obj.data.vertices.foreach_get("co", coordinates)
        coordinates = coordinates.reshape(-1, 3)
        entries[name] = {
            "fbx": fbx_path.relative_to(REPO_ROOT).as_posix(),
            "fbx_sha256": sha256(fbx_path),
            "vertex_count": len(obj.data.vertices),
            "triangle_count": sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons),
            "bounds_min_cm": [round(float(v), 3) for v in coordinates.min(0)],
            "bounds_max_cm": [round(float(v), 3) for v in coordinates.max(0)],
            "straps": stats,
        }
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)
    manifest = {
        "schema": "raftsim.production_pfd_shoulder_straps_source.v1",
        "generator": "unreal/Scripts/build_production_pfd_shoulder_straps.py",
        "generator_version": GENERATOR_VERSION,
        "ownership": "Project-owned deterministic source art; no external mesh or texture input.",
        "source_inputs": [
            {"path": PROFILE_PATH.relative_to(REPO_ROOT).as_posix(), "sha256": sha256(PROFILE_PATH)},
        ],
        "blend": BLEND_PATH.relative_to(REPO_ROOT).as_posix(),
        "blend_sha256": sha256(BLEND_PATH),
        "material_slots": pfd.MATERIAL_NAMES,
        "frame": "SM_RaftSim_WhitewaterRescuePfd local frame; attach each pair to the wearer's ProductionPfd component with an identity relative transform",
        "fitted_to_pfd": {
            "generator_version": pfd.GENERATOR_VERSION,
            "fbx_sha256": pfd_manifest.get("fbx_sha256"),
        },
        "construction": {
            "strap_plane_y_cm": pfd.SHOULDER_STRAP_Y_CM,
            "padded_width_cm": STRAP_WIDTH_CM,
            "padded_thickness_cm": PADDED_THICKNESS_CM,
            "skin_gap_cm": SKIN_GAP_CM,
            "webbing_width_cm": pfd.WEBBING_WIDTH_CM,
            "per_side": ["buckle webbing", "keeper", "padded strap", "reflective piping"],
        },
        "dump_wearers": list(DUMP_WEARERS),
        "meshes": entries,
        "runtime_boundary": "Collisionless safety-gear visual; body animation and rescue authority remain native.",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("RAFTSIM_PFD_SHOULDER_STRAPS=" + json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
