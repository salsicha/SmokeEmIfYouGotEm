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


def build_scenario(repo_root: Path, digitization: dict[str, Any]) -> dict[str, Any]:
    corridor = json.loads((repo_root / CORRIDOR_MANIFEST_RELATIVE).read_text(encoding="utf-8"))
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
        "status": "map_and_run_definition_ready_hydraulic_windows_and_guide_review_pending",
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
            "control_mode": "guided_paddle_crew",
            "voice_paddle_commands_enabled": True,
            "flexible_raft_enabled": True,
            "rock_wrap_and_flip_enabled": True,
            "swimmer_and_rescue_enabled": True,
            "rapid_9_policy": "mandatory_commercial_portage_not_normal_runnable_line",
        },
        "route_variants": [
            {
                "variant_id": "full_reference_run_1_to_25",
                "start_rapid": "1",
                "end_rapid": "25",
                "status": "editor_preview_ready_not_physics_runnable",
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
            "each rapid receives validated hydraulic geometry and C++ solver windows before gameplay promotion",
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
    }
