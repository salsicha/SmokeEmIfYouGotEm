"""Build the raft guide's flip line, fitted snug to the production PFD.

A guide's flip line is a length of 1-inch tubular webbing worn wrapped twice
round the waist at the vest's hem, its sewn end loop clipped back over the
wraps with a locking carabiner, ready to right a flipped raft. The mesh is
authored in the production PFD's own frame (X toward the face, Z up the
spine, centimetres) so the game attaches it to the guide's vest component
with an identity transform and it inherits that vest's per-wearer fit scale.

The wraps are fitted to the vest geometry itself, rebuilt here from
``build_production_whitewater_pfd.py``: at every angle round the waist each
wrap lies a fixed small distance outside whatever the vest carries at that
height (foam, side straps, buckles, zip), bridging hollows like a tensioned
strap. The vest's inner face already clears the guide's torso, so the line
cannot reach the body. No external mesh or texture is used.
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
import build_production_whitewater_pfd as pfd  # noqa: E402  (the vest it wraps)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment/ProductionFlipLine"
FBX_PATH = OUTPUT_ROOT / "SM_RaftSim_GuideFlipLine.fbx"
BLEND_PATH = OUTPUT_ROOT / "SM_RaftSim_GuideFlipLine.blend"
MANIFEST_PATH = OUTPUT_ROOT / "production_guide_flip_line_manifest.json"
GENERATOR_VERSION = 1
MATERIAL_NAMES = ["FlipLineWebbing", "FlipLineHardware"]

# 1-inch tubular webbing lies flat at about 25 x 2.5 mm.
WEBBING_WIDTH_CM = 2.5
WEBBING_THICKNESS_CM = 0.26
# Snug: each wrap's inner face sits this far outside the vest beneath it.
WRAP_CLEARANCE_CM = 0.3
WRAP_SPACING_CM = 0.15
# The lower wrap's lower edge stays this far above the vest hem so the line
# rides on foam rather than hanging off the hem's rolled edge.
HEM_CLEARANCE_CM = 0.5
# Degrees about the vest's envelope axis (0 front, 90 the +Y flank). The
# clip sits low on the guide's left front, clear of the vest's lash tab.
CARABINER_THETA_DEG = 312.0
WRAP_START_THETA_DEG = CARABINER_THETA_DEG + 10.0
CROSSOVER_SPAN_DEG = 50.0
END_LOOP_LENGTH_CM = 5.0
CARABINER_HALF_LENGTH_CM = 5.2
CARABINER_HALF_WIDTH_CM = 2.7
CARABINER_ROD_RADIUS_CM = 0.45


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class VestSlices:
    """Outer radius of the vest (plus clearance) by height and angle."""

    def __init__(self, points: np.ndarray, z_low: float, z_high: float) -> None:
        self.centre = np.array([pfd.ENVELOPE_AXIS_X_CM, 0.0])
        self.angles = np.arange(0.0, 360.0, 1.0)
        self.heights = np.arange(z_low, z_high + 1e-6, 0.25)
        rows = []
        for height in self.heights:
            # A 1 cm window keeps every slice dense with vest vertices.
            window = points[np.abs(points[:, 2] - height) <= 0.5][:, :2]
            hull = pfd.offset_convex_polygon(pfd.convex_hull_2d(window), WRAP_CLEARANCE_CM)
            rows.append(pfd.ray_polygon_radius(hull, self.centre, self.angles))
        self.radius = np.asarray(rows)

    def band_max(self, theta: float, z_low: float, z_high: float) -> float:
        column = int(round(theta % 360.0)) % 360
        rows = (self.heights >= z_low - 0.13) & (self.heights <= z_high + 0.13)
        return float(self.radius[rows, column].max())


def wrap_section(slices: VestSlices, theta: float, z_bottom: float) -> tuple[float, float, float]:
    """Taut straight section over a band: bottom radius, top radius, top z.

    The webbing cannot curl across its width, so its inner face is a straight
    line from its lower to its upper edge, raised until every third of the
    band clears the vest under it.
    """
    thirds = [
        (z_bottom + WEBBING_WIDTH_CM * k / 3.0, z_bottom + WEBBING_WIDTH_CM * (k + 1) / 3.0)
        for k in range(3)
    ]
    needed = [slices.band_max(theta, low, high) for low, high in thirds]
    bottom, top = needed[0], needed[2]
    deficit = 0.0
    for (low, high), radius in zip(thirds, needed):
        for z in (low, high):
            line = bottom + (top - bottom) * (z - z_bottom) / WEBBING_WIDTH_CM
            deficit = max(deficit, radius - line)
    return bottom + deficit, top + deficit, z_bottom + WEBBING_WIDTH_CM


def build_line(builder: pfd.MeshBuilder, slices: VestSlices, z_lower: float) -> dict[str, object]:
    z_upper = z_lower + WEBBING_WIDTH_CM + WRAP_SPACING_CM
    end_alpha = 720.0 - (WRAP_START_THETA_DEG - CARABINER_THETA_DEG) + 2.0
    alphas = np.linspace(0.0, end_alpha, int(end_alpha / 1.5) + 1)
    crossover_start = 360.0
    crossover_end = 360.0 + CROSSOVER_SPAN_DEG
    rise = pfd.smoothstep(crossover_start, crossover_end, alphas)
    # Where the second turn climbs over the start of the first it rides one
    # webbing thickness further out, so the tucked start is covered, not cut.
    lift = (WEBBING_THICKNESS_CM + 0.04) * pfd.smoothstep(crossover_start - 15.0, crossover_start, alphas) * (
        1.0 - pfd.smoothstep(crossover_end, crossover_end + 15.0, alphas)
    )
    profile = pfd.stadium_profile(WEBBING_WIDTH_CM * 0.5, WEBBING_THICKNESS_CM, 4, 3)
    rings = []
    outwards = []
    for alpha, climb, extra in zip(alphas, rise, lift):
        theta = WRAP_START_THETA_DEG + alpha
        z_bottom = z_lower + (z_upper - z_lower) * climb
        r_bottom, r_top, z_top = wrap_section(slices, theta, z_bottom)
        angle = math.radians(theta)
        radial = np.array([math.cos(angle), math.sin(angle), 0.0])
        bottom = np.array([*(slices.centre + (r_bottom + extra) * radial[:2]), z_bottom])
        top = np.array([*(slices.centre + (r_top + extra) * radial[:2]), z_top])
        across = (top - bottom) / np.linalg.norm(top - bottom)
        outward = radial - across * float(radial @ across)
        outward /= np.linalg.norm(outward)
        origin = 0.5 * (bottom + top)
        rings.append(origin + np.outer(profile[:, 0], across) + np.outer(profile[:, 1], outward))
        outwards.append(outward)
    rings = np.asarray(rings)
    outwards = np.asarray(outwards)
    centres = rings.mean(axis=1)
    lengths = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(centres, axis=0), axis=-1))])
    perimeter = np.concatenate(
        [[0.0], np.cumsum(np.linalg.norm(np.diff(np.vstack([profile, profile[:1]]), axis=0), axis=-1))]
    )
    uvs = np.stack(np.broadcast_arrays(lengths[:, None], perimeter[None, :]), -1)
    builder.begin_piece("FlipLineWraps", "webbing")
    pfd.add_ring_sweep(builder, rings, "FlipLineWebbing", uvs)
    builder.end_piece()

    # Sewn end loop: the last few centimetres doubled back over the wrap.
    loop_samples = lengths >= lengths[-1] - END_LOOP_LENGTH_CM
    loop_rings = rings[loop_samples] + outwards[loop_samples, None, :] * (WEBBING_THICKNESS_CM + 0.03)
    loop_lengths = lengths[loop_samples] - lengths[loop_samples][0]
    builder.begin_piece("FlipLineSewnEndLoop", "webbing")
    pfd.add_ring_sweep(
        builder,
        loop_rings,
        "FlipLineWebbing",
        np.stack(np.broadcast_arrays(loop_lengths[:, None], perimeter[None, :]), -1),
    )
    builder.end_piece()
    return {
        "z_lower_wrap_cm": [round(z_lower, 3), round(z_lower + WEBBING_WIDTH_CM, 3)],
        "z_upper_wrap_cm": [round(z_upper, 3), round(z_upper + WEBBING_WIDTH_CM, 3)],
        "modelled_length_cm": round(float(lengths[-1] + END_LOOP_LENGTH_CM), 1),
        "rings": rings,
        "loop_rings": loop_rings,
    }


def add_tube(builder: pfd.MeshBuilder, name: str, path: np.ndarray, radius: float, closed: bool, sides: int = 14) -> None:
    """Round rod swept along a path (carabiner frame, gate sleeve)."""
    count = len(path)
    if closed:
        tangent = np.roll(path, -1, axis=0) - np.roll(path, 1, axis=0)
    else:
        tangent = np.gradient(path, axis=0)
    tangent /= np.linalg.norm(tangent, axis=-1, keepdims=True)
    reference = np.array([0.0, 0.0, 1.0]) if abs(tangent[0, 2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    normal = np.cross(reference, tangent[0])
    normal /= np.linalg.norm(normal)
    frames = []
    for i in range(count):
        # Parallel transport keeps the rod's facets from twisting.
        normal = normal - tangent[i] * float(normal @ tangent[i])
        normal /= np.linalg.norm(normal)
        frames.append((normal, np.cross(tangent[i], normal)))
    angles = np.linspace(0.0, 2.0 * math.pi, sides, endpoint=False)
    rings = np.asarray(
        [
            path[i] + radius * (np.outer(np.cos(angles), frames[i][1]) + np.outer(np.sin(angles), frames[i][0]))
            for i in range(count)
        ]
    )
    # Rings must run counter-clockwise about the direction of travel.
    probe = np.cross(rings[0, 1] - rings[0, 0], rings[0, 2] - rings[0, 1])
    if float(probe @ tangent[0]) < 0.0:
        rings = rings[:, ::-1, :]
    lengths = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=-1))])
    if closed:
        lengths = np.append(lengths, lengths[-1] + np.linalg.norm(path[0] - path[-1]))
    around = np.linspace(0.0, 2.0 * math.pi * radius, sides + 1)
    uvs = np.stack(np.broadcast_arrays(lengths[:, None], around[None, :]), -1)
    builder.begin_piece(name, "hardware")
    pfd.add_ring_sweep(builder, rings, "FlipLineHardware", uvs, closed=closed)
    builder.end_piece()


def build_carabiner(builder: pfd.MeshBuilder, slices: VestSlices, line: dict[str, object], vest_points: np.ndarray) -> dict[str, float]:
    """Locking D carabiner lying flat over the wraps and the end loop."""
    angle = math.radians(CARABINER_THETA_DEG)
    radial = np.array([math.cos(angle), math.sin(angle), 0.0])
    tangent = np.array([-math.sin(angle), math.cos(angle), 0.0])
    up = np.array([0.0, 0.0, 1.0])
    z_centre = 0.5 * (line["z_lower_wrap_cm"][0] + line["z_upper_wrap_cm"][1]) - 1.0
    origin = np.array([*slices.centre, z_centre])
    # The carabiner's plane lies outside everything in its footprint: the
    # wraps, the doubled end loop, and any vest hardware above/below them.
    obstacles = np.concatenate([line["rings"].reshape(-1, 3), line["loop_rings"].reshape(-1, 3), vest_points])
    local = obstacles - origin
    u = local @ tangent
    v = local @ up
    footprint = (np.abs(u) <= CARABINER_HALF_WIDTH_CM + 1.0) & (np.abs(v) <= CARABINER_HALF_LENGTH_CM + 1.0)
    plane = float((local[footprint] @ radial).max()) + 0.05 + CARABINER_ROD_RADIUS_CM
    centre = origin + radial * plane
    # D shape: straight spine, straight gate, a tighter nose at the bottom.
    half_w = CARABINER_HALF_WIDTH_CM - CARABINER_ROD_RADIUS_CM
    half_l = CARABINER_HALF_LENGTH_CM - CARABINER_ROD_RADIUS_CM
    top_radius = half_w
    bottom_radius = half_w * 0.75
    outline = []
    for t in np.linspace(-half_l + bottom_radius, half_l - top_radius, 8):
        outline.append((-half_w, t))
    for a in np.linspace(math.pi, 0.0, 14)[1:-1]:
        outline.append((half_w * math.cos(a), half_l - top_radius + top_radius * math.sin(a)))
    for t in np.linspace(half_l - top_radius, -half_l + bottom_radius, 8):
        outline.append((half_w, t))
    for a in np.linspace(0.0, -math.pi, 14)[1:-1]:
        outline.append((half_w * math.cos(a), -half_l + bottom_radius + bottom_radius * math.sin(a)))
    outline = np.asarray(outline)
    path = centre + np.outer(outline[:, 0], tangent) + np.outer(outline[:, 1], up)
    add_tube(builder, "LockingCarabinerFrame", path, CARABINER_ROD_RADIUS_CM, closed=True)
    # Screw-gate sleeve on the gate side, near the nose.
    sleeve_path = centre + np.outer(np.full(6, half_w), tangent) + np.outer(np.linspace(-0.6, 1.8, 6), up)
    add_tube(builder, "LockingCarabinerSleeve", sleeve_path, CARABINER_ROD_RADIUS_CM + 0.22, closed=False)
    return {"theta_deg": CARABINER_THETA_DEG, "plane_radius_cm": round(plane, 3), "z_centre_cm": round(z_centre, 3)}


def validate(mesh_object: bpy.types.Object, open_edges: int) -> dict[str, object]:
    slots = [slot.name for slot in mesh_object.data.materials]
    if slots != MATERIAL_NAMES:
        raise RuntimeError(f"Flip line material contract changed: {slots}")
    if open_edges:
        raise RuntimeError(f"Flip line pieces are not closed: {open_edges} open edges")
    coordinates = np.empty(len(mesh_object.data.vertices) * 3)
    mesh_object.data.vertices.foreach_get("co", coordinates)
    coordinates = coordinates.reshape(-1, 3)
    minimum = coordinates.min(0)
    maximum = coordinates.max(0)
    dimensions = maximum - minimum
    if not (25.0 <= dimensions[0] <= 50.0 and 30.0 <= dimensions[1] <= 50.0 and 5.0 <= dimensions[2] <= 15.0):
        raise RuntimeError(f"Flip line bounds are implausible: {tuple(dimensions)}")
    return {
        "vertex_count": len(mesh_object.data.vertices),
        "polygon_count": len(mesh_object.data.polygons),
        "triangle_count": sum(len(polygon.vertices) - 2 for polygon in mesh_object.data.polygons),
        "open_edges": open_edges,
        "material_slots": slots,
        "uv_channel_count": len(mesh_object.data.uv_layers),
        "bounds_min_cm": [round(float(value), 4) for value in minimum],
        "bounds_max_cm": [round(float(value), 4) for value in maximum],
        "dimensions_cm": [round(float(value), 4) for value in dimensions],
    }


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    pfd.reset_scene()
    # One Blender unit is one centimetre. UE 5.8's Interchange FBX import
    # applies node transforms, so the unit must live in the scene: a metre
    # scene exports Lcl Scaling 100 (a 100x mesh) or needs a compensating
    # export scale. Matches the helmet, sandal and boot generators.
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 0.01
    bpy.context.scene.unit_settings.length_unit = "CENTIMETERS"
    vest = pfd.MeshBuilder()
    pfd.build_vest(vest)
    vest_points = vest.points()
    z_lower = pfd.VEST_BOTTOM_Z_CM + 0.4 + HEM_CLEARANCE_CM
    z_top = z_lower + 2.0 * WEBBING_WIDTH_CM + WRAP_SPACING_CM
    slices = VestSlices(vest_points, z_lower - 0.5, z_top + 0.5)
    builder = pfd.MeshBuilder(MATERIAL_NAMES)
    line = build_line(builder, slices, z_lower)
    clip = build_carabiner(builder, slices, line, vest_points)
    materials = {
        "FlipLineWebbing": pfd.material("FlipLineWebbing", (0.02, 0.16, 0.55, 1.0), 0.8),
        "FlipLineHardware": pfd.material("FlipLineHardware", (0.55, 0.57, 0.6, 1.0), 0.35, metallic=1.0),
    }
    mesh_object = builder.to_object("SM_RaftSim_GuideFlipLine", materials)
    open_edges = pfd.orient_outward(mesh_object)
    audit = validate(mesh_object, open_edges)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = mesh_object
    mesh_object.select_set(True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)
    bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH),
        use_selection=True,
        object_types={"MESH"},
        # Same centimetre scene units and export as the PFD so both share
        # one frame: FBX unit factor 1, no node scaling.
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
    pfd_manifest = json.loads(pfd.MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest = {
        "schema": "raftsim.production_guide_flip_line_source.v1",
        "generator_version": GENERATOR_VERSION,
        "ownership": "Project-owned deterministic source art; no external mesh or texture input.",
        "source_inputs": [],
        "fbx": str(FBX_PATH.relative_to(REPO_ROOT)),
        "blend": str(BLEND_PATH.relative_to(REPO_ROOT)),
        "fbx_sha256": sha256(FBX_PATH),
        "blend_sha256": sha256(BLEND_PATH),
        "material_slots": MATERIAL_NAMES,
        "frame": "SM_RaftSim_WhitewaterRescuePfd local frame; attach to the guide's ProductionPfd component with an identity relative transform",
        "fitted_to_pfd": {
            "generator_version": pfd.GENERATOR_VERSION,
            "fbx_sha256": pfd_manifest.get("fbx_sha256"),
        },
        "construction": {
            "webbing": "1-inch tubular webbing",
            "wraps": 2,
            "sewn_end_loops": 1,
            "locking_carabiners": 1,
            "webbing_width_cm": WEBBING_WIDTH_CM,
            "webbing_thickness_cm": WEBBING_THICKNESS_CM,
            "wrap_clearance_cm": WRAP_CLEARANCE_CM,
            "z_lower_wrap_cm": line["z_lower_wrap_cm"],
            "z_upper_wrap_cm": line["z_upper_wrap_cm"],
            "modelled_wrapped_length_cm": line["modelled_length_cm"],
            "carabiner": clip,
        },
        "runtime_boundary": "Collisionless visual worn by the guide only; flip and rescue behaviour remain native.",
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
