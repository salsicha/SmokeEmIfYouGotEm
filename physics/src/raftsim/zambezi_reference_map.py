"""Convert the user-supplied Zambezi references into review-gated game data.

The supplied height image is a colourised web-map screenshot, not a raw DEM.  Its
legend is nevertheless sufficient to reconstruct a useful *visual morphology
reference*.  This module deliberately keeps that reconstruction separate from
the georeferenced Copernicus DEM that remains terrain/collision authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image, ImageFilter


SCHEMA = "raftsim.zambezi.user_reference_bundle.v1"
RAPID_MAP_SCHEMA = "raftsim.zambezi.rapid_map_digitization.v1"
SCENARIO_SCHEMA = "raftsim.zambezi.run_scenario.v1"
OUTPUT_RELATIVE = Path(
    "physics/data/real_world/zambezi_batoka_gorge/reference/user_supplied"
)
SCENARIO_RELATIVE = Path(
    "physics/data/real_world/zambezi_batoka_gorge/scenario_zambezi_run/scenario.json"
)
CATALOG_RELATIVE = Path("physics/data/real_world/named_rapid_source_catalog.json")
CORRIDOR_MANIFEST_RELATIVE = Path(
    "physics/data/real_world/zambezi_batoka_gorge/production_corridor/"
    "boiling_pot_to_mukuni_beach/manifest.json"
)
CORRIDOR_CENTERLINE_RELATIVE = Path(
    "physics/data/real_world/zambezi_batoka_gorge/production_corridor/"
    "boiling_pot_to_mukuni_beach/hydrography/centerline_local.json"
)
RUNTIME_RELATIVE = Path(
    "physics/data/real_world/zambezi_batoka_gorge/scenario_zambezi_run/runtime"
)
COORDINATE_MAP_RELATIVE = RUNTIME_RELATIVE / "river_coordinate_map.json"
COOKED_FIELDS_RELATIVE = RUNTIME_RELATIVE / "cooked_flow_fields"

SOURCE_HEIGHT_IMAGE = Path("zambezi_batoka_heightmap.png")
SOURCE_RAPID_MAP = Path("victoria-falls-rapids-map.pdf")
EXPECTED_HEIGHT_IMAGE_SIZE = (2126, 1076)
HEIGHT_IMAGE_SHA256 = "f54d690504cc3841b472f2f958262777c768263adb3f046c316f638c7a7342b4"
RAPID_MAP_SHA256 = "8000a0d2f319fdd1ee37b60070a16a45189fbb98294fab3756cac505a2564a09"

# The map viewport ends immediately before the right-side control/legend and
# above the attribution footer. Coordinates use PIL's (left, top, right, bottom).
HEIGHT_MAP_CROP = (0, 0, 2000, 1040)
REFERENCE_HEIGHTFIELD_SIZE = (1009, 625)
REFERENCE_MESH_SIZE = (513, 321)
OVERLAY_REJECTION_DISTANCE_RGB = 32.0
RUNTIME_GRID_DX_M = 5.0
RUNTIME_GRID_DY_M = 10.0
RUNTIME_GRID_HALF_WIDTH_M = 120.0
RUNTIME_WET_HALF_WIDTH_M = 72.0
RUNTIME_COORDINATE_MAX_STEP_M = 5.0
RUNTIME_COORDINATE_MAX_CORRIDOR_EDGE_STEP_M = 15.5
RUNTIME_PRESENTATION_SAMPLE_SPACING_M = 3.0
RUNTIME_BREAKING_UPSTREAM_FROUDE_MIN = 1.12
RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX = 0.94
RUNTIME_LAUNCH_STATION_M = 75.0
RUNTIME_FIRST_RAPID_CONTROL_STATION_M = 160.0
RUNTIME_MINIMUM_SAFE_LAUNCH_APRON_M = 50.0

# Legend colours are sampled from x=2016 at the centre of each 40-pixel band in
# the supplied screenshot. Keeping the byte colours avoids any dependency on
# host colour-profile conversion: both terrain and legend are in the same image.
LEGEND_ELEVATIONS_M = np.asarray(
    [
        1029.0,
        1005.0,
        982.0,
        959.0,
        937.0,
        914.0,
        892.0,
        871.0,
        850.0,
        829.0,
        808.0,
        788.0,
        769.0,
        750.0,
        732.0,
        715.0,
        698.0,
        683.0,
        669.0,
        659.0,
    ],
    dtype=np.float32,
)
LEGEND_RGB = np.asarray(
    [
        (250, 226, 226),
        (245, 181, 180),
        (241, 140, 136),
        (240, 109, 100),
        (240, 109, 91),
        (241, 142, 97),
        (245, 182, 106),
        (250, 222, 118),
        (248, 255, 127),
        (214, 254, 124),
        (184, 253, 123),
        (163, 253, 122),
        (153, 252, 121),
        (152, 252, 128),
        (152, 252, 149),
        (152, 252, 178),
        (152, 252, 211),
        (152, 252, 242),
        (142, 232, 252),
        (129, 206, 251),
    ],
    dtype=np.float32,
)


@dataclass(frozen=True)
class RapidPin:
    number: int
    pin_tips_px: tuple[tuple[float, float], ...]

    @property
    def representative_tip_px(self) -> tuple[float, float]:
        points = np.asarray(self.pin_tips_px, dtype=np.float64)
        return (float(points[:, 0].mean()), float(points[:, 1].mean()))


# Pin tips digitised from the complete 3827x3260, 72-DPI rendering of page one.
# Rapids 12 and 16 intentionally preserve the multiple pins printed on the map.
RAPID_PINS = (
    RapidPin(1, ((809.5, 1176.0),)),
    RapidPin(2, ((673.5, 1185.0),)),
    RapidPin(3, ((542.5, 1195.0),)),
    RapidPin(4, ((584.5, 1248.0),)),
    RapidPin(5, ((813.5, 1284.0),)),
    RapidPin(6, ((509.5, 1491.0),)),
    RapidPin(7, ((784.5, 1695.0),)),
    RapidPin(8, ((841.5, 1898.0),)),
    RapidPin(9, ((776.5, 2052.0),)),
    RapidPin(10, ((838.5, 2203.0),)),
    RapidPin(11, ((884.5, 2404.0),)),
    RapidPin(12, ((1150.5, 2384.0), (1207.5, 2387.0), (1264.5, 2392.0))),
    RapidPin(13, ((1224.5, 2481.0),)),
    RapidPin(14, ((1572.5, 2633.0),)),
    RapidPin(15, ((1925.5, 2669.0),)),
    RapidPin(16, ((2033.5, 2716.0), (2107.5, 2716.0))),
    RapidPin(17, ((2191.5, 2759.0),)),
    RapidPin(18, ((2273.5, 2981.0),)),
    RapidPin(19, ((2765.0, 2991.0),)),
    RapidPin(20, ((2874.5, 3038.0),)),
    RapidPin(21, ((2985.5, 3052.0),)),
    RapidPin(22, ((3286.5, 3113.0),)),
    RapidPin(23, ((3427.5, 3184.0),)),
    RapidPin(24, ((3577.5, 3122.0),)),
    RapidPin(25, ((3674.5, 2797.0),)),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _array_metadata(
    path: Path, array: np.ndarray, description: str, units: str
) -> dict[str, Any]:
    return {
        "file": path.name,
        "sha256": _sha256(path),
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "description": description,
        "units": units,
    }


def _smooth_tangent_angles(positions: np.ndarray) -> np.ndarray:
    """Return normals smooth enough for the runtime coordinate-map fold guard."""

    look = min(20, max(1, len(positions) // 20))
    tangents = np.empty_like(positions)
    for index in range(len(positions)):
        before = positions[max(0, index - look)]
        after = positions[min(len(positions) - 1, index + look)]
        delta = after - before
        tangents[index] = delta / max(float(np.linalg.norm(delta)), 1.0e-9)
    angles = np.unwrap(np.arctan2(tangents[:, 1], tangents[:, 0]))

    # The C++ runtime rejects coordinate maps whose +/-256 m corridor edges
    # jump more than 16 m between samples. Widen the angular smoothing window
    # deterministically until the generated map is inside that guard.
    window = 81
    while True:
        maximum_odd_window = len(angles) if len(angles) % 2 else len(angles) - 1
        window = max(3, min(window, maximum_odd_window))
        pad = window // 2
        padded = np.pad(angles, (pad, pad), mode="edge")
        smoothed = np.convolve(padded, np.ones(window) / window, mode="valid")
        tangent = np.column_stack((np.cos(smoothed), np.sin(smoothed)))
        normal = np.column_stack((-tangent[:, 1], tangent[:, 0]))
        left_edge = positions + normal * 256.0
        right_edge = positions - normal * 256.0
        edge_steps = np.maximum(
            np.linalg.norm(np.diff(left_edge, axis=0), axis=1),
            np.linalg.norm(np.diff(right_edge, axis=0), axis=1),
        )
        if (
            float(edge_steps.max(initial=0.0))
            <= RUNTIME_COORDINATE_MAX_CORRIDOR_EDGE_STEP_M
        ):
            return normal
        if window >= maximum_odd_window:
            raise ValueError("Could not produce a fold-safe Zambezi runtime coordinate map")
        window = min(window * 2 + 1, maximum_odd_window)


def build_runtime_coordinate_map(repo_root: Path) -> dict[str, Any]:
    """Convert the source-scale centerline into the runtime curved-river schema."""

    corridor = json.loads(
        (repo_root / CORRIDOR_MANIFEST_RELATIVE).read_text(encoding="utf-8")
    )
    source = json.loads(
        (repo_root / CORRIDOR_CENTERLINE_RELATIVE).read_text(encoding="utf-8")
    )
    half_height_m = float(corridor["physical_size_m"]["height"]) * 0.5
    source_points = source["points"]

    dense_positions: list[np.ndarray] = []
    for index, (start, finish) in enumerate(zip(source_points, source_points[1:])):
        start_xy = np.asarray(
            (-58.0 + float(start["x_m"]), -half_height_m + float(start["y_m"])),
            dtype=np.float64,
        )
        finish_xy = np.asarray(
            (-58.0 + float(finish["x_m"]), -half_height_m + float(finish["y_m"])),
            dtype=np.float64,
        )
        segment_length = float(np.linalg.norm(finish_xy - start_xy))
        subdivisions = max(
            1, int(math.ceil(segment_length / RUNTIME_COORDINATE_MAX_STEP_M))
        )
        for step in range(subdivisions):
            if index > 0 and step == 0:
                continue
            dense_positions.append(
                start_xy + (finish_xy - start_xy) * (step / subdivisions)
            )
    last = source_points[-1]
    dense_positions.append(
        np.asarray(
            (-58.0 + float(last["x_m"]), -half_height_m + float(last["y_m"])),
            dtype=np.float64,
        )
    )
    positions = np.asarray(dense_positions, dtype=np.float64)
    segment_lengths = np.linalg.norm(np.diff(positions, axis=0), axis=1)
    stations = np.concatenate((np.asarray([0.0]), np.cumsum(segment_lengths)))
    normals = _smooth_tangent_angles(positions)
    left_edge = positions + normals * 256.0
    right_edge = positions - normals * 256.0
    max_edge_step = float(
        np.maximum(
            np.linalg.norm(np.diff(left_edge, axis=0), axis=1),
            np.linalg.norm(np.diff(right_edge, axis=0), axis=1),
        ).max(initial=0.0)
    )
    return {
        "schema": "raftsim.curved_river_coordinate_map.v1",
        "river_id": "zambezi_batoka_gorge",
        "status": "reference_runnable_source_scale_centerline_review_gated",
        "vertical_datum_m": 0.0,
        "station_domain_m": [
            round(float(stations[0]), 6),
            round(float(stations[-1]), 6),
        ],
        "point_spacing_policy": (
            f"source_segments_subdivided_to_at_most_"
            f"{RUNTIME_COORDINATE_MAX_STEP_M:g}_m"
        ),
        "runtime_corridor_half_width_m": 256.0,
        "maximum_runtime_corridor_edge_step_m": round(max_edge_step, 6),
        "source": CORRIDOR_CENTERLINE_RELATIVE.as_posix(),
        "authority": (
            "source_scale_osm_and_satellite_review_centerline_"
            "not_navigation_or_survey_authority"
        ),
        "points": [
            [
                round(float(station), 6),
                round(float(position[0]), 6),
                round(float(position[1]), 6),
                round(float(normal[0]), 8),
                round(float(normal[1]), 8),
            ]
            for station, position, normal in zip(stations, positions, normals)
        ],
    }


def _validate_sources(repo_root: Path) -> tuple[Path, Path]:
    image_path = repo_root / SOURCE_HEIGHT_IMAGE
    map_path = repo_root / SOURCE_RAPID_MAP
    if not image_path.is_file() or not map_path.is_file():
        raise FileNotFoundError("Both supplied Zambezi reference files are required")
    if _sha256(image_path) != HEIGHT_IMAGE_SHA256:
        raise ValueError("The supplied Zambezi height image changed; recalibrate its legend")
    if _sha256(map_path) != RAPID_MAP_SHA256:
        raise ValueError("The supplied Victoria Falls rapid map changed; redigitise its pins")
    with Image.open(image_path) as image:
        if image.size != EXPECTED_HEIGHT_IMAGE_SIZE:
            raise ValueError(f"Unexpected height-image size: {image.size}")
    return image_path, map_path


def decode_colour_height_image(image: Image.Image) -> tuple[np.ndarray, np.ndarray]:
    """Return reconstructed elevation metres and legend-fit error for the map crop."""

    rgb = np.asarray(image.convert("RGB").crop(HEIGHT_MAP_CROP), dtype=np.float32)
    flat = rgb.reshape((-1, 3))
    best_squared_distance = np.full(flat.shape[0], np.inf, dtype=np.float32)
    elevation = np.zeros(flat.shape[0], dtype=np.float32)

    # Project each source colour onto every adjacent legend-colour segment. This
    # retains smooth relief instead of quantising the screenshot to 20 bands.
    for index in range(len(LEGEND_RGB) - 1):
        start = LEGEND_RGB[index]
        delta = LEGEND_RGB[index + 1] - start
        denominator = max(float(np.dot(delta, delta)), 1.0e-6)
        fraction = np.clip(np.sum((flat - start) * delta, axis=1) / denominator, 0.0, 1.0)
        projected = start + fraction[:, None] * delta
        squared_distance = np.sum((flat - projected) ** 2, axis=1)
        better = squared_distance < best_squared_distance
        elevation[better] = LEGEND_ELEVATIONS_M[index] + fraction[better] * (
            LEGEND_ELEVATIONS_M[index + 1] - LEGEND_ELEVATIONS_M[index]
        )
        best_squared_distance[better] = squared_distance[better]

    elevation = elevation.reshape(rgb.shape[:2])
    distance = np.sqrt(best_squared_distance).reshape(rgb.shape[:2])

    # OSM text, roads, boundaries, and UI strokes do not belong in terrain. A
    # median neighbourhood gives a deterministic local repair for pixels whose
    # colour lies too far from the legend curve. A small blur suppresses the
    # remaining antialiasing without inventing large-scale terrain features.
    normalized = np.clip(
        (elevation - float(LEGEND_ELEVATIONS_M.min()))
        / float(np.ptp(LEGEND_ELEVATIONS_M)),
        0.0,
        1.0,
    )
    normalized_u8 = np.rint(normalized * 255.0).astype(np.uint8)
    median = np.asarray(
        Image.fromarray(normalized_u8).filter(ImageFilter.MedianFilter(9)),
        dtype=np.uint8,
    )
    repaired = normalized_u8.copy()
    rejected = distance > OVERLAY_REJECTION_DISTANCE_RGB
    repaired[rejected] = median[rejected]
    repaired_image = Image.fromarray(repaired).filter(ImageFilter.GaussianBlur(1.0))
    repaired_f32 = np.asarray(repaired_image, dtype=np.float32) / 255.0
    reconstructed = float(LEGEND_ELEVATIONS_M.min()) + repaired_f32 * float(
        np.ptp(LEGEND_ELEVATIONS_M)
    )
    return reconstructed.astype(np.float32), distance.astype(np.float32)


def _resize_float(values: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    image = Image.fromarray(values.astype(np.float32), mode="F")
    return np.asarray(image.resize(size, Image.Resampling.BICUBIC), dtype=np.float32)


def _write_heightfield_16bit(path: Path, elevations_m: np.ndarray) -> None:
    minimum = float(LEGEND_ELEVATIONS_M.min())
    relief = float(np.ptp(LEGEND_ELEVATIONS_M))
    encoded = np.rint(np.clip((elevations_m - minimum) / relief, 0.0, 1.0) * 65535.0)
    Image.fromarray(encoded.astype(np.uint16), mode="I;16").save(path)


def _write_height_preview(path: Path, elevations_m: np.ndarray, width_m: float, height_m: float) -> None:
    spacing_x = width_m / max(elevations_m.shape[1] - 1, 1)
    spacing_y = height_m / max(elevations_m.shape[0] - 1, 1)
    gradient_y, gradient_x = np.gradient(elevations_m, spacing_y, spacing_x)
    normal_x = -gradient_x
    normal_y = -gradient_y
    normal_z = np.ones_like(elevations_m)
    magnitude = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
    light = np.asarray((-0.45, -0.45, 0.77), dtype=np.float32)
    light /= np.linalg.norm(light)
    hillshade = np.clip(
        (normal_x * light[0] + normal_y * light[1] + normal_z * light[2]) / magnitude,
        0.0,
        1.0,
    )
    normalized = np.clip(
        (elevations_m - float(LEGEND_ELEVATIONS_M.min()))
        / float(np.ptp(LEGEND_ELEVATIONS_M)),
        0.0,
        1.0,
    )
    preview = np.rint(np.clip(normalized * 0.65 + hillshade * 0.35, 0.0, 1.0) * 255.0)
    Image.fromarray(preview.astype(np.uint8), mode="L").save(path)


def _iter_obj_faces(width: int, height: int) -> Iterable[tuple[int, int, int]]:
    for row in range(height - 1):
        for column in range(width - 1):
            top_left = row * width + column + 1
            top_right = top_left + 1
            bottom_left = top_left + width
            bottom_right = bottom_left + 1
            yield (top_left, top_right, bottom_left)
            yield (top_right, bottom_right, bottom_left)


def _write_obj(
    path: Path,
    elevations_m: np.ndarray,
    width_m: float,
    height_m: float,
    base_elevation_m: float,
) -> dict[str, Any]:
    height, width = elevations_m.shape
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("# RaftSim Zambezi Batoka user-reference morphology mesh\n")
        stream.write("# visual review only; Copernicus DEM remains physics authority\n")
        stream.write("o SM_RaftSim_ZambeziBatoka_UserReferenceMorphology\n")
        for row in range(height):
            y_m = height_m * row / max(height - 1, 1)
            for column in range(width):
                x_m = width_m * column / max(width - 1, 1)
                z_m = float(elevations_m[row, column]) - base_elevation_m
                stream.write(f"v {x_m:.4f} {y_m:.4f} {z_m:.4f}\n")
        for row in range(height):
            v = 1.0 - row / max(height - 1, 1)
            for column in range(width):
                u = column / max(width - 1, 1)
                stream.write(f"vt {u:.7f} {v:.7f}\n")
        for a, b, c in _iter_obj_faces(width, height):
            stream.write(f"f {a}/{a} {b}/{b} {c}/{c}\n")
    return {
        "format": "Wavefront OBJ",
        "coordinate_system": "local_x_east_y_south_z_up_metres",
        "base_elevation_m": base_elevation_m,
        "vertex_count": width * height,
        "triangle_count": (width - 1) * (height - 1) * 2,
        "grid_size": [width, height],
        "import_scale_cm_per_unit": 100.0,
        "collision_authority": False,
        "physics_authority": False,
    }


def _rapid_lookup(repo_root: Path) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    catalog = json.loads((repo_root / CATALOG_RELATIVE).read_text(encoding="utf-8"))
    river = next(
        river for river in catalog["rivers"] if river["river_id"] == "zambezi_batoka_gorge"
    )
    return river, {int(rapid["rapid_number"]): rapid for rapid in river["rapids"]}


def build_rapid_map_digitization(repo_root: Path) -> dict[str, Any]:
    river, rapid_lookup = _rapid_lookup(repo_root)
    representative = [np.asarray(pin.representative_tip_px) for pin in RAPID_PINS]
    segment_lengths = [0.0]
    for previous, current in zip(representative, representative[1:]):
        segment_lengths.append(float(np.linalg.norm(current - previous)))
    cumulative = np.cumsum(np.asarray(segment_lengths, dtype=np.float64))
    fractions = cumulative / cumulative[-1]
    run_length_m = float(river["run_length_m"])
    page_size = np.asarray((3827.0, 3260.0), dtype=np.float64)

    rapids: list[dict[str, Any]] = []
    for index, pin in enumerate(RAPID_PINS):
        source = rapid_lookup[pin.number]
        point = np.asarray(pin.representative_tip_px, dtype=np.float64)
        fraction = float(fractions[index])
        rapids.append(
            {
                "rapid_number": str(pin.number),
                "catalog_name": source["name"],
                "pdf_label": (
                    "The Wall" if pin.number == 1 else
                    "The Three Ugly Sisters" if pin.number == 12 else
                    "The Terminator 1&2" if pin.number == 16 else
                    source["name"]
                ),
                "pin_tips_px": [[round(x, 3), round(y, 3)] for x, y in pin.pin_tips_px],
                "representative_tip_px": [round(float(point[0]), 3), round(float(point[1]), 3)],
                "representative_tip_normalized": [
                    round(float(point[0] / page_size[0]), 8),
                    round(float(point[1] / page_size[1]), 8),
                ],
                "map_segment_length_px": round(segment_lengths[index], 4),
                "map_cumulative_length_px": round(float(cumulative[index]), 4),
                "map_relative_station_fraction": round(fraction, 8),
                "station_m": round(run_length_m * fraction, 3),
                "difficulty_label": source["class"],
                "feature_tags": source["feature_tags"],
                "stationing_authority": "stylized_map_relative_spacing_not_surveyed",
                "production_authoritative": False,
                "guide_review_status": "required",
            }
        )
    return {
        "schema": RAPID_MAP_SCHEMA,
        "status": "digitized_relative_stationing_ready_exact_survey_and_guide_review_required",
        "river_id": "zambezi_batoka_gorge",
        "source": {
            "path": SOURCE_RAPID_MAP.as_posix(),
            "sha256": RAPID_MAP_SHA256,
            "page": 1,
            "page_count": 1,
            "render_dpi": 72,
            "rendered_reference_size_px": [3827, 3260],
            "rights_status": "user_supplied_reference_rights_review_required",
        },
        "method": {
            "pin_policy": "manual_red_pin_tip_digitization_on_complete_page_render",
            "duplicate_pin_policy": "mean_tip_position_for_rapids_12_and_16",
            "station_policy": "cumulative_euclidean_distance_between_ordered_pin_tips_scaled_to_published_17_mile_run",
            "run_length_m": run_length_m,
            "run_length_source": "named_rapid_source_catalog_and_linked_17_mile_guide_reference",
            "limitations": [
                "The PDF is illustrative and is not a surveyed or georeferenced river map.",
                "Pin-to-pin curves approximate relative spacing; they do not establish exact coordinates.",
                "Stations may drive editor markers but cannot authorize hydraulic geometry or production lines.",
            ],
        },
        "rapid_count": len(rapids),
        "rapids": rapids,
        "production_promoted": False,
    }


def _write_runtime_water_bundle(
    repo_root: Path,
    corridor: dict[str, Any],
    digitization: dict[str, Any],
) -> dict[str, Path]:
    """Write a lightweight full-run solver seed where bathymetry is unavailable."""

    runtime_root = repo_root / RUNTIME_RELATIVE
    cooked_root = repo_root / COOKED_FIELDS_RELATIVE
    runtime_root.mkdir(parents=True, exist_ok=True)
    cooked_root.mkdir(parents=True, exist_ok=True)

    coordinate_map = build_runtime_coordinate_map(repo_root)
    coordinate_path = repo_root / COORDINATE_MAP_RELATIVE
    _write_json(coordinate_path, coordinate_map)

    source_centerline = json.loads(
        (repo_root / CORRIDOR_CENTERLINE_RELATIVE).read_text(encoding="utf-8")
    )["points"]
    source_stations = np.asarray(
        [float(point["station_m"]) for point in source_centerline], dtype=np.float64
    )
    source_surface_normalized = np.asarray(
        [
            float(point["conditioned_visual_surface_normalized"])
            for point in source_centerline
        ],
        dtype=np.float64,
    )
    route_length_m = float(coordinate_map["station_domain_m"][1])
    nx = int(math.floor(route_length_m / RUNTIME_GRID_DX_M)) + 1
    ny = int(round(2.0 * RUNTIME_GRID_HALF_WIDTH_M / RUNTIME_GRID_DY_M)) + 1
    station_m = np.arange(nx, dtype=np.float64) * RUNTIME_GRID_DX_M
    lateral_m = (
        np.arange(ny, dtype=np.float64) * RUNTIME_GRID_DY_M
        - RUNTIME_GRID_HALF_WIDTH_M
    )

    relief_m = float(corridor["artifacts"]["relief_m"])
    center_surface_m = (
        np.interp(station_m, source_stations, source_surface_normalized)
        * relief_m
        + 0.12
    )
    rapid_intensity = np.zeros_like(station_m)
    rapid_controls: list[dict[str, Any]] = []
    for rapid in digitization["rapids"]:
        difficulty = str(rapid["difficulty_label"])
        weight = (
            0.48
            + 0.10 * difficulty.count("V")
            + 0.018 * len(rapid["feature_tags"])
        )
        distance = (station_m - float(rapid["station_m"])) / 95.0
        rapid_intensity = np.maximum(
            rapid_intensity, weight * np.exp(-0.5 * distance**2)
        )
        is_first_rapid = str(rapid["rapid_number"]) == "1"
        control_station_target_m = (
            RUNTIME_FIRST_RAPID_CONTROL_STATION_M
            if is_first_rapid
            else float(rapid["station_m"])
        )
        rapid_controls.append(
            {
                "rapid": rapid,
                "severity": float(
                    np.clip(
                        0.56
                        + 0.08 * difficulty.count("V")
                        + 0.016 * len(rapid["feature_tags"]),
                        0.58,
                        0.92,
                    )
                ),
                # Rapid 1 is printed at the route origin, while the runnable
                # raft starts at station 75 m. Put its procedural control far
                # enough downstream to preserve a measured calm launch and a
                # full approach before the first supercritical cell. Every
                # other control stays on the nearest five-metre source station.
                "control_index": int(
                    np.clip(
                        round(control_station_target_m / RUNTIME_GRID_DX_M),
                        0,
                        nx - 10,
                    )
                ),
                "repositioned_for_safe_launch": is_first_rapid,
            }
        )
    rapid_intensity = np.clip(rapid_intensity, 0.0, 1.0)
    center_surface_m += (
        0.12 * rapid_intensity * np.sin(station_m * 0.055)
    )

    cross_fraction = np.clip(
        1.0 - (np.abs(lateral_m) / RUNTIME_WET_HALF_WIDTH_M) ** 2,
        0.0,
        1.0,
    )[:, None]
    cross_depth_profile = np.power(cross_fraction, 0.65)
    center_depth_m = (4.2 - 0.35 * rapid_intensity)[None, :]
    h = center_depth_m * cross_depth_profile
    wet_mask = (h > 0.05).astype(np.uint8)
    target_froude = (
        (0.36 + 0.08 * rapid_intensity)[None, :]
        * (0.86 + 0.14 * cross_fraction)
    )

    # Missing surveyed rapid bathymetry is filled with an explicit, bounded
    # reference-only hydraulic-control contract. The five-metre station grid
    # is fine enough for the live three-metre presentation mesh to see a real
    # supercritical-to-subcritical transition instead of a broad Gaussian
    # speed tint. Difficulty and feature tags scale the cue, but never assert
    # an exact line, rock, bathymetry, or navigationally authoritative shape.
    approach_profile = (0.12, 0.20, 0.34, 0.52, 0.70, 0.86, 1.0)
    surface_profile = (
        (-6, 0.02),
        (-5, 0.04),
        (-4, 0.07),
        (-3, 0.11),
        (-2, 0.16),
        (-1, 0.23),
        (0, 0.31),
        (1, -0.08),
        (2, 0.13),
        (3, -0.07),
        (4, 0.08),
        (5, -0.04),
        (6, 0.03),
    )
    for control in rapid_controls:
        rapid = control["rapid"]
        severity = float(control["severity"])
        control_index = int(control["control_index"])
        tags = {str(tag) for tag in rapid["feature_tags"]}
        broad_feature = any(
            token in " ".join(tags)
            for token in ("river_wide", "large_wave", "wave_train", "multiple")
        )
        lane_sigma_m = 55.0 if broad_feature else 46.0
        lane = np.exp(-0.5 * (np.abs(lateral_m) / lane_sigma_m) ** 4)
        lane = np.where(wet_mask[:, control_index] != 0, lane, 0.0)
        control_depth_m = 2.15 - 0.48 * severity
        control_froude = 1.58 + 0.34 * severity
        for profile_index, profile_strength in enumerate(approach_profile):
            offset = profile_index - (len(approach_profile) - 1)
            column = control_index + offset
            blend = np.clip(lane * profile_strength, 0.0, 1.0)
            h[:, column] = np.where(
                wet_mask[:, column] != 0,
                h[:, column] * (1.0 - blend) + control_depth_m * blend,
                0.0,
            )
            target_froude[:, column] = np.maximum(
                target_froude[:, column],
                target_froude[:, column] * (1.0 - blend)
                + control_froude * blend,
            )

        # The first tailwater station is intentionally abrupt: it is the
        # hydraulic jump. Deeper, slower water then releases into a decaying
        # feature-tagged wave train. The renderer owns any overhanging crest,
        # foam, roller, aerosol, and mist; these fields remain physics inputs.
        pile_depth_m = 4.45 + 0.42 * severity
        pile_froude = 0.46 - 0.04 * severity
        for tail_offset in range(1, 9):
            column = control_index + tail_offset
            decay = math.exp(-0.34 * (tail_offset - 1))
            phase = math.cos(2.05 * tail_offset)
            blend = np.clip(lane * decay, 0.0, 1.0)
            tail_depth_m = pile_depth_m + 0.24 * severity * phase * decay
            tail_froude = pile_froude + 0.09 * max(phase, 0.0) * decay
            h[:, column] = np.where(
                wet_mask[:, column] != 0,
                h[:, column] * (1.0 - blend) + tail_depth_m * blend,
                0.0,
            )
            target_froude[:, column] = np.where(
                wet_mask[:, column] != 0,
                target_froude[:, column] * (1.0 - blend)
                + tail_froude * blend,
                0.0,
            )

        for offset, relative_surface_m in surface_profile:
            center_surface_m[control_index + offset] += (
                relative_surface_m * severity
            )

    h = h.astype(np.float32)
    dry_bank_rise = (
        np.maximum(np.abs(lateral_m) - RUNTIME_WET_HALF_WIDTH_M, 0.0)[:, None]
        * 0.035
    )
    bed = np.where(
        wet_mask != 0,
        center_surface_m[None, :] - h,
        center_surface_m[None, :] + dry_bank_rise,
    ).astype(np.float32)
    u = (
        wet_mask
        * target_froude
        * np.sqrt(9.80665 * np.maximum(h, 1.0e-6))
    ).astype(np.float32)
    v = (
        wet_mask
        * 0.38
        * rapid_intensity[None, :]
        * np.sin(np.pi * lateral_m[:, None] / RUNTIME_WET_HALF_WIDTH_M)
        * np.sin(station_m[None, :] * 0.011)
    ).astype(np.float32)

    center_row = int(np.argmin(np.abs(lateral_m)))
    center_h = h[center_row].astype(np.float64)
    center_u = u[center_row].astype(np.float64)
    center_v = v[center_row].astype(np.float64)
    rapid_transition_records: list[dict[str, Any]] = []
    for control in rapid_controls:
        rapid = control["rapid"]
        control_index = int(control["control_index"])
        control_station_m = float(station_m[control_index])
        sample_stations = np.arange(
            max(0.0, control_station_m - 15.0),
            min(float(station_m[-1]), control_station_m + 25.0)
            + 0.5 * RUNTIME_PRESENTATION_SAMPLE_SPACING_M,
            RUNTIME_PRESENTATION_SAMPLE_SPACING_M,
        )
        sample_h = np.interp(sample_stations, station_m, center_h)
        sample_u = np.interp(sample_stations, station_m, center_u)
        sample_v = np.interp(sample_stations, station_m, center_v)
        sample_froude = np.hypot(sample_u, sample_v) / np.sqrt(
            9.80665 * np.maximum(sample_h, 1.0e-6)
        )
        transitions = np.flatnonzero(
            (sample_froude[:-1] >= RUNTIME_BREAKING_UPSTREAM_FROUDE_MIN)
            & (sample_froude[1:] <= RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX)
        )
        if transitions.size == 0:
            raise RuntimeError(
                "Procedural Zambezi rapid "
                f"{rapid['rapid_number']} does not satisfy the live breaking-water "
                "transition contract"
            )
        transition_index = int(transitions[0])
        rapid_transition_records.append(
            {
                "rapid_number": str(rapid["rapid_number"]),
                "display_name": str(rapid["catalog_name"]),
                "source_station_m": float(rapid["station_m"]),
                "control_station_m": control_station_m,
                "difficulty_label": str(rapid["difficulty_label"]),
                "feature_tags": list(rapid["feature_tags"]),
                "mandatory_commercial_portage": str(rapid["rapid_number"]) == "9",
                "upstream_froude": round(float(sample_froude[transition_index]), 4),
                "tailwater_froude": round(float(sample_froude[transition_index + 1]), 4),
                "transition_station_m": round(
                    float(sample_stations[transition_index + 1]), 3
                ),
                "runtime_sample_spacing_m": RUNTIME_PRESENTATION_SAMPLE_SPACING_M,
                "production_authoritative": False,
            }
        )

    first_control = rapid_controls[0]
    first_control_index = int(first_control["control_index"])
    first_approach_index = first_control_index - (len(approach_profile) - 1)
    launch_index = int(round(RUNTIME_LAUNCH_STATION_M / RUNTIME_GRID_DX_M))
    safe_launch_apron_m = float(
        station_m[first_approach_index] - station_m[launch_index]
    )
    maximum_launch_froude = float(
        np.max(
            np.hypot(
                center_u[launch_index:first_approach_index],
                center_v[launch_index:first_approach_index],
            )
            / np.sqrt(
                9.80665
                * np.maximum(
                    center_h[launch_index:first_approach_index],
                    1.0e-6,
                )
            )
        )
    )
    if safe_launch_apron_m < RUNTIME_MINIMUM_SAFE_LAUNCH_APRON_M:
        raise RuntimeError(
            "Procedural Zambezi launch apron is shorter than the gameplay contract: "
            f"{safe_launch_apron_m:.1f} m"
        )
    if maximum_launch_froude > RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX:
        raise RuntimeError(
            "Procedural Zambezi launch apron is not subcritical: "
            f"maximum Froude {maximum_launch_froude:.3f}"
        )
    launch_apron_contract = {
        "schema": "raftsim.zambezi.safe_launch_apron.v1",
        "raft_spawn_station_m": RUNTIME_LAUNCH_STATION_M,
        "first_rapid_source_station_m": float(
            first_control["rapid"]["station_m"]
        ),
        "first_rapid_control_station_m": float(
            station_m[first_control_index]
        ),
        "first_rapid_approach_start_station_m": float(
            station_m[first_approach_index]
        ),
        "safe_subcritical_clearance_m": safe_launch_apron_m,
        "minimum_required_clearance_m": RUNTIME_MINIMUM_SAFE_LAUNCH_APRON_M,
        "maximum_centerline_froude_before_approach": round(
            maximum_launch_froude, 4
        ),
        "maximum_allowed_froude_before_approach": (
            RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX
        ),
        "crew_ejection_policy": (
            "no_forced_ejection_before_player_reaches_first_rapid_approach"
        ),
        "production_authoritative": False,
    }

    arrays = {
        "bed": (
            bed,
            "Procedural channel bed aligned to the conditioned visual surface.",
            "m",
        ),
        "h": (h, "Procedural reference-run water depth above bed.", "m"),
        "u": (u, "Downstream reference-run seed velocity.", "m_per_s"),
        "v": (v, "Bounded cross-stream rapid cue velocity.", "m_per_s"),
        "wet_mask": (
            wet_mask,
            "One where the procedural reference channel is wet.",
            "boolean",
        ),
    }
    array_metadata: dict[str, Any] = {}
    for name, (array, description, units) in arrays.items():
        path = cooked_root / f"{name}.npy"
        np.save(path, array, allow_pickle=False)
        array_metadata[name] = _array_metadata(path, array, description, units)

    manifest = {
        "schema": "raftsim.cooked_flow_fields.v1",
        "generator": (
            "raftsim.zambezi_reference_map.feature_tagged_hydraulic_seed.v3"
        ),
        "river_id": "zambezi_batoka_gorge",
        "section_id": "boiling_pot_to_mukuni_beach_reference_run",
        "window_id": "zambezi_full_reference_corridor",
        "status": (
            "reference_runnable_feature_tagged_procedural_hydraulics_"
            "not_validated_real_world_hydraulics"
        ),
        "production_promoted": False,
        "source_package": SCENARIO_RELATIVE.parent.as_posix(),
        "source_elevation_datum_m": 0.0,
        "grid": {
            "crs": (
                "curved river coordinates; x is station downstream and y is river-left"
            ),
            "downstream_axis": "+x",
            "layout": "row_major_c_order",
            "index_to_world": (
                "station_m = origin_x_m + col * dx_m; "
                "lateral_m = origin_y_m + row * dy_m"
            ),
            "nx": nx,
            "ny": ny,
            "dx_m": RUNTIME_GRID_DX_M,
            "dy_m": RUNTIME_GRID_DY_M,
            "origin_x_m": 0.0,
            "origin_y_m": -RUNTIME_GRID_HALF_WIDTH_M,
        },
        "solver": {
            "solver_mode": "finite_volume",
            "flux_scheme": "hll",
            "spatial_order": 2,
            "cfl": 0.35,
            "dry_tolerance": 1.0e-6,
            "roughness_scale": 1.0,
            "bed_slope_source_scale": 1.0,
            "feature_strength_scale": 0.0,
            "fixed_dt_s": 0.02,
            "preserve_initial_mass": False,
            "disable_fixture_calibrations": True,
        },
        "bands": [
            {
                "band_id": "normal_big_water",
                "roughness_manning_n": 0.041,
                "arrays": array_metadata,
                "convergence": {
                    "converged": False,
                    "status": "procedural_seed_not_a_steady_state_solver_claim",
                },
            }
        ],
        "procedural_infill": {
            "reason": (
                "surveyed bathymetry and rapid-scale hydraulic geometry are unavailable"
            ),
            "surface_alignment": (
                "conditioned visual centerline profile in the Copernicus source-scale map"
            ),
            "wet_half_width_m": RUNTIME_WET_HALF_WIDTH_M,
            "rapid_cues": (
                "bounded feature-tagged hydraulic controls from the user-supplied "
                "25-rapid map"
            ),
            "hydraulic_transition_contract": {
                "schema": "raftsim.zambezi.procedural_hydraulic_transitions.v1",
                "runtime_station_resolution_m": RUNTIME_GRID_DX_M,
                "presentation_sample_spacing_m": RUNTIME_PRESENTATION_SAMPLE_SPACING_M,
                "upstream_froude_minimum": RUNTIME_BREAKING_UPSTREAM_FROUDE_MIN,
                "tailwater_froude_maximum": RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX,
                "rapid_transition_count": len(rapid_transition_records),
                "all_rapid_transitions_detected": (
                    len(rapid_transition_records) == len(rapid_controls)
                ),
                "rapid_9_policy": (
                    "hazard_visualization_only_mandatory_commercial_portage_"
                    "not_a_runnable_line"
                ),
                "transitions": rapid_transition_records,
            },
            "safe_launch_apron": launch_apron_contract,
            "authority": (
                "gameplay_reference_only_not_navigation_or_real_world_hydraulic_authority"
            ),
        },
        "notes": [
            (
                "This lightweight full-corridor seed makes the generated Zambezi map "
                "runnable with the live finite-volume runtime."
            ),
            (
                "Every mapped rapid now contains a bounded five-metre procedural "
                "control and a live-renderer-detectable supercritical-to-subcritical "
                "transition; exact geometry, lines, and hydraulic fidelity remain open."
            ),
            (
                "It does not claim surveyed bathymetry, exact rapid lines, guide approval, "
                "seasonal calibration, or production hydraulic fidelity."
            ),
            (
                "The Copernicus DEM remains terrain/collision authority and the generated "
                "river-coordinate map remains review-gated."
            ),
        ],
    }
    manifest_path = cooked_root / "manifest.json"
    _write_json(manifest_path, manifest)
    return {
        "coordinate_map": coordinate_path,
        "cooked_fields_manifest": manifest_path,
    }


def build_scenario(repo_root: Path, digitization: dict[str, Any]) -> dict[str, Any]:
    corridor = json.loads((repo_root / CORRIDOR_MANIFEST_RELATIVE).read_text(encoding="utf-8"))
    runtime_manifest = json.loads(
        (repo_root / COOKED_FIELDS_RELATIVE / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    launch_apron_contract = runtime_manifest["procedural_infill"][
        "safe_launch_apron"
    ]
    rapid_entries = []
    for rapid in digitization["rapids"]:
        rapid_entries.append(
            {
                "rapid_number": rapid["rapid_number"],
                "display_name": rapid["catalog_name"],
                "map_label": rapid["pdf_label"],
                "station_m": rapid["station_m"],
                "difficulty_label": rapid["difficulty_label"],
                "feature_tags": rapid["feature_tags"],
                "mandatory_commercial_portage": rapid["rapid_number"] == "9",
                "exact_geometry_status": "required_before_production",
                "guide_review_status": "required",
            }
        )
    return {
        "schema": SCENARIO_SCHEMA,
        "scenario_id": "zambezi_boiling_pot_to_mukuni_beach_reference_run",
        "display_name": "Zambezi: Boiling Pot to Mukuni Beach",
        "river_id": "zambezi_batoka_gorge",
        "status": (
            "reference_runnable_with_procedural_full_corridor_water_"
            "production_hydraulics_and_reviews_pending"
        ),
        "production_promoted": False,
        "unreal_map_package": (
            "/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/"
            "L_ZambeziBatokaGorge_PhysicalCorridorCandidate"
        ),
        "run_length_m": digitization["method"]["run_length_m"],
        "terrain": {
            "collision_and_height_query_authority": CORRIDOR_MANIFEST_RELATIVE.as_posix(),
            "heightfield": corridor["artifacts"]["heightfield"],
            "authority": "copernicus_dem_glo30_source_scale_technical_corridor",
            "user_reference_morphology_mesh": (
                OUTPUT_RELATIVE / "zambezi_batoka_user_reference_morphology.obj"
            ).as_posix(),
            "user_reference_authority": "visual_comparison_only_not_collision_or_physics",
        },
        "rapid_map_digitization": (
            OUTPUT_RELATIVE / "rapid_map_digitization.json"
        ).as_posix(),
        "route_evidence": [
            {
                "source_id": "zambezi_whitewater_guidebook",
                "url": "https://www.whitewaterguidebook.com/africa/zambezi-river-batoka-gorge/",
                "supports": [
                    "approximately_17_miles_to_rapid_25",
                    "boiling_pot_rapid_1_put_in",
                    "rapid_25_standard_full_day_takeout",
                    "rapid_9_commercial_portage",
                    "rapid_11_high_water_put_in_context",
                    "rapid_23_high_water_takeout_context",
                ],
                "rights_status": "link_only_factual_index",
            },
            {
                "source_id": "zambezi_shearwater_operator_guide",
                "url": "https://www.shearwatervictoriafalls.com/experience/white-water-rafting/",
                "supports": [
                    "low_water_boiling_pot_start",
                    "january_to_april_candidate_rapid_11_to_23",
                ],
                "rights_status": "link_only_factual_index",
            },
            {
                "source_id": "zambezi_victoria_falls_guide",
                "url": "https://www.victoriafalls-guide.net/victoria-falls-rafting.html",
                "supports": [
                    "low_water_candidate_rapid_1_to_25",
                    "high_water_candidate_rapid_14_to_25",
                    "rapid_names_and_flow_behavior_context",
                ],
                "rights_status": "link_only_factual_index",
            },
        ],
        "gameplay": {
            "portfolio_role": "runnable_river",
            "control_mode": "guided_paddle_crew",
            "voice_paddle_commands_enabled": True,
            "flexible_raft_enabled": True,
            "rock_wrap_and_flip_enabled": True,
            "swimmer_and_rescue_enabled": True,
            "rapid_9_policy": "mandatory_commercial_portage_not_normal_runnable_line",
            "runnable": True,
            "runnable_tier": "reference_free_run",
            "default_flow_band": "normal_big_water",
            "runtime_coordinate_map": COORDINATE_MAP_RELATIVE.as_posix(),
            "runtime_cooked_fields": COOKED_FIELDS_RELATIVE.as_posix(),
            "hydraulic_authority": (
                "feature_tagged_procedural_reference_only_not_validated_"
                "real_world_hydraulics"
            ),
            "safe_launch_apron": launch_apron_contract,
        },
        "route_variants": [
            {
                "variant_id": "full_reference_run_1_to_25",
                "start_rapid": "1",
                "end_rapid": "25",
                "status": (
                    "reference_runnable_with_feature_tagged_procedural_"
                    "hydraulics_not_production_rapid_hydraulics"
                ),
                "selection_policy": "default_reference_corridor",
            },
            {
                "variant_id": "high_water_candidate_11_to_23",
                "start_rapid": "11",
                "end_rapid": "23",
                "status": "operator_source_candidate_requires_local_guide_and_flow_review",
                "source_id": "zambezi_shearwater_operator_guide",
                "selection_policy": "disabled_until_flow_band_review",
            },
            {
                "variant_id": "high_water_candidate_14_to_25",
                "start_rapid": "14",
                "end_rapid": "25",
                "status": "alternate_published_candidate_requires_local_guide_and_flow_review",
                "source_id": "zambezi_victoria_falls_guide",
                "selection_policy": "disabled_until_flow_band_review",
            },
        ],
        "rapid_count": len(rapid_entries),
        "rapids": rapid_entries,
        "acceptance_gates": [
            "local guide approves put-in, take-out, rapid stations, lines, portages, and rescue routes",
            "geospatial reviewer approves centerline alignment and terrain datum",
            "rights reviewer approves supplied PDF/image use and all shipped source products",
            "seasonal-flow reviewer resolves high-water start/take-out variants and flow bands",
            (
                "each rapid receives validated hydraulic geometry and C++ solver windows "
                "before production hydraulic-fidelity promotion"
            ),
            "desktop and VR performance plus lifelike visual review pass on the generated Unreal map",
        ],
    }


def generate_zambezi_reference_bundle(repo_root: Path) -> dict[str, Path]:
    repo_root = repo_root.resolve()
    image_path, map_path = _validate_sources(repo_root)
    output_root = repo_root / OUTPUT_RELATIVE
    output_root.mkdir(parents=True, exist_ok=True)

    with Image.open(image_path) as source_image:
        reconstructed, fit_distance = decode_colour_height_image(source_image)
    corridor = json.loads((repo_root / CORRIDOR_MANIFEST_RELATIVE).read_text(encoding="utf-8"))
    width_m = float(corridor["physical_size_m"]["width"])
    height_m = float(corridor["physical_size_m"]["height"])

    heightfield = _resize_float(reconstructed, REFERENCE_HEIGHTFIELD_SIZE)
    mesh_heights = _resize_float(reconstructed, REFERENCE_MESH_SIZE)
    heightfield_path = output_root / "zambezi_batoka_user_reference_heightfield_16bit.png"
    preview_path = output_root / "zambezi_batoka_user_reference_height_preview.png"
    mesh_path = output_root / "zambezi_batoka_user_reference_morphology.obj"
    _write_heightfield_16bit(heightfield_path, heightfield)
    _write_height_preview(preview_path, heightfield, width_m, height_m)
    mesh = _write_obj(
        mesh_path,
        mesh_heights,
        width_m,
        height_m,
        float(LEGEND_ELEVATIONS_M.min()),
    )

    digitization = build_rapid_map_digitization(repo_root)
    digitization_path = output_root / "rapid_map_digitization.json"
    _write_json(digitization_path, digitization)
    runtime = _write_runtime_water_bundle(repo_root, corridor, digitization)
    scenario = build_scenario(repo_root, digitization)
    scenario_path = repo_root / SCENARIO_RELATIVE
    _write_json(scenario_path, scenario)

    rejected_fraction = float(np.mean(fit_distance > OVERLAY_REJECTION_DISTANCE_RGB))
    manifest = {
        "schema": SCHEMA,
        "river_id": "zambezi_batoka_gorge",
        "status": "reference_products_generated_review_gated_not_terrain_authority",
        "production_promoted": False,
        "sources": [
            {
                "role": "colour_height_reference",
                "path": SOURCE_HEIGHT_IMAGE.as_posix(),
                "sha256": _sha256(image_path),
                "size_px": list(EXPECTED_HEIGHT_IMAGE_SIZE),
                "pixel_format": "8_bit_rgba_display_p3_screenshot",
                "rights_status": "user_supplied_reference_rights_review_required",
                "authority": "visual_morphology_reference_not_dem_or_physics_authority",
            },
            {
                "role": "rapid_order_and_relative_spacing_reference",
                "path": SOURCE_RAPID_MAP.as_posix(),
                "sha256": _sha256(map_path),
                "page_count": 1,
                "rights_status": "user_supplied_reference_rights_review_required",
                "authority": "illustrative_map_not_surveyed_or_georeferenced",
            },
        ],
        "height_conversion": {
            "method": "piecewise_rgb_projection_onto_sampled_20_band_legend",
            "legend_elevation_range_m": [
                float(LEGEND_ELEVATIONS_M.min()),
                float(LEGEND_ELEVATIONS_M.max()),
            ],
            "source_crop_px": list(HEIGHT_MAP_CROP),
            "overlay_rejection_distance_rgb": OVERLAY_REJECTION_DISTANCE_RGB,
            "overlay_rejected_fraction": round(rejected_fraction, 8),
            "repair": "9_pixel_median_for_rejected_pixels_then_1_pixel_gaussian",
            "registration": (
                "provisional_affine_fit_to_existing_corridor_physical_extents_for_visual_comparison"
            ),
            "limitations": [
                "The source is colourised, compressed, and composited over OpenStreetMap labels and roads.",
                "Legend inversion cannot recover elevation precision lost before the screenshot was captured.",
                "The affine fit is not a geospatial registration and cannot replace the Copernicus DEM.",
            ],
        },
        "physical_extents_m": {"width": width_m, "height": height_m},
        "artifacts": {
            "heightfield_16bit": {
                "path": heightfield_path.relative_to(repo_root).as_posix(),
                "sha256": _sha256(heightfield_path),
                "size_px": list(REFERENCE_HEIGHTFIELD_SIZE),
                "encoding": "unsigned_16_bit_linear_659_to_1029_m",
                "physics_authority": False,
            },
            "height_preview": {
                "path": preview_path.relative_to(repo_root).as_posix(),
                "sha256": _sha256(preview_path),
            },
            "morphology_mesh": {
                "path": mesh_path.relative_to(repo_root).as_posix(),
                "sha256": _sha256(mesh_path),
                **mesh,
            },
            "rapid_map_digitization": {
                "path": digitization_path.relative_to(repo_root).as_posix(),
                "sha256": _sha256(digitization_path),
            },
            "scenario": {
                "path": scenario_path.relative_to(repo_root).as_posix(),
                "sha256": _sha256(scenario_path),
            },
            "runtime_coordinate_map": {
                "path": runtime["coordinate_map"].relative_to(repo_root).as_posix(),
                "sha256": _sha256(runtime["coordinate_map"]),
                "authority": "review_gated_runtime_mapping_not_survey_authority",
            },
            "runtime_cooked_fields": {
                "path": runtime["cooked_fields_manifest"].relative_to(repo_root).as_posix(),
                "sha256": _sha256(runtime["cooked_fields_manifest"]),
                "authority": (
                    "procedural_gameplay_seed_not_real_world_hydraulic_authority"
                ),
            },
        },
        "terrain_authority": {
            "manifest": CORRIDOR_MANIFEST_RELATIVE.as_posix(),
            "heightfield": corridor["artifacts"]["heightfield"],
            "policy": "Copernicus DEM remains Unreal Landscape collision and height-query authority",
        },
    }
    manifest_path = output_root / "source_and_conversion_manifest.json"
    _write_json(manifest_path, manifest)
    return {
        "manifest": manifest_path,
        "heightfield": heightfield_path,
        "preview": preview_path,
        "mesh": mesh_path,
        "digitization": digitization_path,
        "scenario": scenario_path,
        "coordinate_map": runtime["coordinate_map"],
        "cooked_fields_manifest": runtime["cooked_fields_manifest"],
    }
