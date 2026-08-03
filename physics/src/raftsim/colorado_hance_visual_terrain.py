"""Reach-local visual terrain bundle for the runnable Colorado Hance map.

The committed Hance C3 window provides a 600 m by 78 m interpreted solver bed.
That strip remains unchanged.  Because no surveyed Hance canyon terrain is
committed, this module deterministically extends the strip to a 320 m-wide
desert-canyon Landscape.  The extension is presentation/collision infill, not
surveyed geography, bathymetry, or solver authority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


SCHEMA = "raftsim.colorado.hance_visual_terrain.v3"
DEFAULT_OUTPUT_RELATIVE = Path(
    "physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/hance_visual"
)
WINDOW_ROOT_RELATIVE = Path(
    "physics/data/real_world/colorado_river_grand_canyon_rowing/scenario_hance"
)
REFERENCE_BAND = "moderate_release_planning"
OUTPUT_CROSS_SPAN_M = 320.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _value_noise_2d(
    x: np.ndarray,
    y: np.ndarray,
    scale_x: float,
    scale_y: float,
    seed: int,
) -> np.ndarray:
    """Deterministic, non-periodic value noise over the local metric grid."""

    grid_x = x / scale_x
    grid_y = y / scale_y
    x0 = np.floor(grid_x)
    y0 = np.floor(grid_y)
    tx = _smoothstep(0.0, 1.0, grid_x - x0)
    ty = _smoothstep(0.0, 1.0, grid_y - y0)

    def hashed(ix: np.ndarray, iy: np.ndarray) -> np.ndarray:
        phase = ix * 127.1 + iy * 311.7 + float(seed) * 74.7
        raw = np.sin(phase) * 43758.5453123
        return raw - np.floor(raw)

    n00 = hashed(x0, y0)
    n10 = hashed(x0 + 1.0, y0)
    n01 = hashed(x0, y0 + 1.0)
    n11 = hashed(x0 + 1.0, y0 + 1.0)
    nx0 = n00 * (1.0 - tx) + n10 * tx
    nx1 = n01 * (1.0 - tx) + n11 * tx
    return nx0 * (1.0 - ty) + nx1 * ty


def _fbm_2d(
    x: np.ndarray,
    y: np.ndarray,
    scale_x: float,
    scale_y: float,
    seed: int,
    octaves: int,
) -> np.ndarray:
    value = np.zeros_like(x, dtype=np.float64)
    weight_sum = 0.0
    amplitude = 1.0
    for octave in range(octaves):
        value += amplitude * _value_noise_2d(
            x,
            y,
            scale_x / (2.03**octave),
            scale_y / (1.97**octave),
            seed + octave * 101,
        )
        weight_sum += amplitude
        amplitude *= 0.52
    return value / weight_sum


def _resample_clamped_regular_grid(
    source: np.ndarray,
    source_x: np.ndarray,
    source_y: np.ndarray,
    target_x: np.ndarray,
    target_y: np.ndarray,
) -> np.ndarray:
    """Bilinearly resample a grid and clamp outside its cross-channel extent."""

    along_x = np.empty((source.shape[0], target_x.size), dtype=np.float64)
    for row in range(source.shape[0]):
        along_x[row] = np.interp(target_x, source_x, source[row])
    output = np.empty((target_y.size, target_x.size), dtype=np.float64)
    for column in range(target_x.size):
        output[:, column] = np.interp(
            target_y,
            source_y,
            along_x[:, column],
            left=along_x[0, column],
            right=along_x[-1, column],
        )
    return output


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_colorado_hance_visual_terrain(
    repo_root: Path,
    *,
    output_dir: Path | None = None,
    output_size_px: int = 1009,
) -> dict[str, object]:
    """Build the deterministic Hance Landscape, centerline, and provenance."""

    if output_size_px < 127:
        raise ValueError("Hance visual terrain requires at least 127 samples")

    repo_root = repo_root.resolve()
    window_root = repo_root / WINDOW_ROOT_RELATIVE
    band_root = window_root / "cooked_flow_fields" / REFERENCE_BAND
    output_root = (output_dir or (repo_root / DEFAULT_OUTPUT_RELATIVE)).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    bed_path = band_root / "bed.npy"
    depth_path = band_root / "h.npy"
    wet_path = band_root / "wet_mask.npy"
    cooked_manifest_path = window_root / "cooked_flow_fields/manifest.json"
    window_manifest_path = window_root / "window_manifest.json"
    for required in (
        bed_path,
        depth_path,
        wet_path,
        cooked_manifest_path,
        window_manifest_path,
    ):
        if not required.is_file():
            raise FileNotFoundError(required)

    cooked_manifest = json.loads(cooked_manifest_path.read_text(encoding="utf-8"))
    window_manifest = json.loads(window_manifest_path.read_text(encoding="utf-8"))
    grid = cooked_manifest["grid"]
    nx = int(grid["nx"])
    ny = int(grid["ny"])
    dx_m = float(grid["dx_m"])
    dy_m = float(grid["dy_m"])
    origin_x_m = float(grid["origin_x_m"])
    origin_y_m = float(grid["origin_y_m"])

    bed = np.asarray(np.load(bed_path), dtype=np.float64)
    depth = np.asarray(np.load(depth_path), dtype=np.float64)
    wet = np.asarray(np.load(wet_path), dtype=bool)
    if bed.shape != (ny, nx) or depth.shape != bed.shape or wet.shape != bed.shape:
        raise ValueError("Hance cooked arrays do not match their manifest grid")

    span_x_m = (nx - 1) * dx_m
    source_span_y_m = (ny - 1) * dy_m
    source_x = origin_x_m + np.arange(nx, dtype=np.float64) * dx_m
    source_y = origin_y_m + np.arange(ny, dtype=np.float64) * dy_m
    target_x = np.linspace(origin_x_m, origin_x_m + span_x_m, output_size_px)
    target_y = np.linspace(
        -OUTPUT_CROSS_SPAN_M * 0.5,
        OUTPUT_CROSS_SPAN_M * 0.5,
        output_size_px,
    )
    base = _resample_clamped_regular_grid(bed, source_x, source_y, target_x, target_y)
    xx, yy = np.meshgrid(target_x, target_y)

    # Preserve the complete interpreted C3 bed. Outside it, V3 replaces the
    # smooth quadratic/sine-dominated valley with non-periodic fractal canyon
    # massing, incised drainage, irregular basement-rock buttresses, talus, and
    # a review-gated debris-fan analog near the solver rapid. The latter follows
    # the documented geomorphic class only: it is not a surveyed Red Canyon fan
    # and never enters the solver strip. Every added term remains exactly zero
    # at the source boundary.
    source_half_width_m = source_span_y_m * 0.5
    bank_distance = np.maximum(np.abs(yy) - source_half_width_m, 0.0)
    bank_fade = _smoothstep(0.0, 11.0, bank_distance)
    outer_bank_mask = bank_distance > 0.0
    macro_noise = _fbm_2d(xx, yy, 104.0, 82.0, 1801, 4)
    meso_noise = _fbm_2d(xx, yy, 31.0, 24.0, 2903, 4)
    fine_noise = _fbm_2d(xx, yy, 9.2, 7.4, 3911, 3)
    drainage_noise = _fbm_2d(
        xx + (macro_noise - 0.5) * 38.0,
        yy + (meso_noise - 0.5) * 24.0,
        58.0,
        46.0,
        4933,
        3,
    )
    side_scale = np.where(yy >= 0.0, 1.10, 0.90)
    longitudinal_mass = 0.86 + 0.30 * macro_noise
    broad_rise = side_scale * (
        0.128 * bank_distance + 0.00315 * np.square(bank_distance)
    ) * longitudinal_mass
    roughness_gain = _smoothstep(4.0, 72.0, bank_distance)
    # Fade sub-grid rock roughness before the finite Landscape boundary. This
    # preserves the broad wall slope while preventing one noisy outermost cell
    # from becoming a false vertical rim at coarse review resolutions.
    outer_roughness_taper = 1.0 - _smoothstep(88.0, 118.0, bank_distance)
    eroded_rock = bank_fade * roughness_gain * outer_roughness_taper * (
        (macro_noise - 0.5) * (1.2 + 0.020 * bank_distance)
        + (meso_noise - 0.5) * (1.5 + 0.015 * bank_distance)
        + (fine_noise - 0.5) * 0.72
    )
    drainage_ridge = np.clip(1.0 - np.abs(drainage_noise * 2.0 - 1.0), 0.0, 1.0)
    gullies = (
        -bank_fade
        * outer_roughness_taper
        * _smoothstep(10.0, 54.0, bank_distance)
        * (0.32 + 0.010 * bank_distance)
        * np.power(drainage_ridge, 6.0)
    )
    buttress_ridge = np.clip(1.0 - np.abs(macro_noise * 2.0 - 1.0), 0.0, 1.0)
    basement_buttresses = (
        bank_fade
        * outer_roughness_taper
        * _smoothstep(16.0, 64.0, bank_distance)
        * (0.7 + 2.7 * np.power(buttress_ridge, 3.0))
        * (0.55 + 0.45 * meso_noise)
    )
    talus = (
        bank_fade
        * outer_roughness_taper
        * _smoothstep(18.0, 92.0, bank_distance)
        * ((meso_noise - 0.5) * 0.95 + np.abs(fine_noise - 0.5) * 0.62)
    )

    rapid_station_m = 405.0
    fan_side_mask = yy < -source_half_width_m
    fan_longitudinal = np.exp(-np.square((xx - rapid_station_m) / 86.0))
    fan_cross_bank = np.exp(-np.square((bank_distance - 27.0) / 31.0))
    debris_fan_analog = (
        bank_fade
        * fan_side_mask
        * 8.8
        * fan_longitudinal
        * fan_cross_bank
        * (0.72 + 0.48 * meso_noise)
    )
    opposite_side_mask = yy > source_half_width_m
    opposing_bedrock_buttress = (
        bank_fade
        * opposite_side_mask
        * 4.8
        * np.exp(-np.square((xx - rapid_station_m) / 112.0))
        * _smoothstep(7.0, 28.0, bank_distance)
        * (1.0 - _smoothstep(70.0, 112.0, bank_distance))
        * (0.78 + 0.34 * macro_noise)
    )
    procedural_infill = np.where(
        outer_bank_mask,
        broad_rise
        + eroded_rock
        + gullies
        + basement_buttresses
        + talus
        + debris_fan_analog
        + opposing_bedrock_buttress,
        0.0,
    )
    # A heightfield cannot represent true overhangs. Limit only the generated
    # outer-bank grade, walking away from each protected solver-strip edge, so
    # isolated noise/taper extrema cannot become raster-scale cliff spikes.
    # The 1.18 rise/run cap is about 49.7 degrees; it leaves the underlying C3
    # bed, its boundary sample, and every in-strip value bit-exact.
    maximum_outer_cross_bank_grade = 1.18
    positive_outer_rows = np.flatnonzero(target_y > source_half_width_m)
    previous_row = np.zeros(target_x.shape, dtype=np.float64)
    previous_y_m = source_half_width_m
    for row_index in positive_outer_rows:
        maximum_delta_m = maximum_outer_cross_bank_grade * (
            target_y[row_index] - previous_y_m
        )
        procedural_infill[row_index] = np.clip(
            procedural_infill[row_index],
            previous_row - maximum_delta_m,
            previous_row + maximum_delta_m,
        )
        previous_row = procedural_infill[row_index].copy()
        previous_y_m = target_y[row_index]

    negative_outer_rows = np.flatnonzero(target_y < -source_half_width_m)[::-1]
    previous_row = np.zeros(target_x.shape, dtype=np.float64)
    previous_y_m = -source_half_width_m
    for row_index in negative_outer_rows:
        maximum_delta_m = maximum_outer_cross_bank_grade * (
            previous_y_m - target_y[row_index]
        )
        procedural_infill[row_index] = np.clip(
            procedural_infill[row_index],
            previous_row - maximum_delta_m,
            previous_row + maximum_delta_m,
        )
        previous_row = procedural_infill[row_index].copy()
        previous_y_m = target_y[row_index]

    conditioned = base + procedural_infill

    terrain_min_m = float(conditioned.min())
    terrain_max_m = float(conditioned.max())
    terrain_span_m = terrain_max_m - terrain_min_m
    if terrain_span_m <= 0.0:
        raise ValueError("Hance conditioned terrain has no elevation range")
    heightfield_u16 = np.round(
        np.clip((conditioned - terrain_min_m) / terrain_span_m, 0.0, 1.0) * 65535.0
    ).astype(np.uint16)

    heightfield_path = (
        output_root / f"hance_conditioned_heightfield_{output_size_px}.png"
    )
    centerline_path = output_root / "hance_local_centerline.json"
    coordinate_map_path = output_root / "hance_runtime_coordinate_map.json"
    manifest_path = output_root / "hance_visual_terrain_manifest.json"
    Image.fromarray(heightfield_u16).save(heightfield_path)

    eta = bed + depth
    runtime_vertical_datum_m = float(np.mean(eta[wet]))
    channel_half_width_m = float(
        window_manifest["conditioning"]["channel_half_width_m"]
    )
    channel_rows = np.abs(source_y) <= channel_half_width_m
    centerline_surface = np.empty(nx, dtype=np.float64)
    centerline_bed = np.empty(nx, dtype=np.float64)
    for column in range(nx):
        wet_rows = channel_rows & wet[:, column]
        rows = wet_rows if wet_rows.any() else channel_rows
        centerline_surface[column] = float(np.median(eta[rows, column]))
        centerline_bed[column] = float(np.median(bed[rows, column]))

    local_center_y_cm = OUTPUT_CROSS_SPAN_M * 50.0
    centerline_points: list[dict[str, object]] = []
    for column in range(nx):
        station_m = origin_x_m + column * dx_m
        surface_m = float(centerline_surface[column])
        bed_m = float(centerline_bed[column])
        centerline_points.append(
            {
                "station_m": station_m,
                "unreal_local_cm": [station_m * 100.0, local_center_y_cm],
                "conditioned_visual_surface_elevation_m": surface_m,
                "conditioned_visual_bed_elevation_m": bed_m,
                "conditioned_visual_surface_normalized": (surface_m - terrain_min_m)
                / terrain_span_m,
                "conditioned_visual_bed_normalized": (bed_m - terrain_min_m)
                / terrain_span_m,
            }
        )
    centerline = {
        "schema": "raftsim.local_centerline.v1",
        "river_id": "colorado_river",
        "section_id": "hance_corridor_station_1250m_c3_window",
        "local_metric_policy": (
            "channel-following C3 coordinates; Unreal X is downstream station and "
            "Unreal Y shifts solver lateral 0 to the center of a 320 m visual canyon"
        ),
        "points": centerline_points,
    }
    centerline_path.write_text(
        json.dumps(centerline, indent=2) + "\n", encoding="utf-8"
    )

    coordinate_map = {
        "schema": "raftsim.curved_river_coordinate_map.v1",
        "river_id": "colorado_river",
        "section_id": "hance_corridor_station_1250m_c3_window",
        "vertical_datum_m": runtime_vertical_datum_m,
        "mapping_policy": (
            "identity station/lateral map for the straight interpreted C3 grid; "
            "vertical datum aligns absolute cooked elevations to the local Unreal reach"
        ),
        "points": [
            [station_m, station_m, 0.0, 0.0, 1.0] for station_m in source_x.tolist()
        ],
    }
    coordinate_map_path.write_text(
        json.dumps(coordinate_map, indent=2) + "\n", encoding="utf-8"
    )

    protected_mask = np.abs(yy) <= source_half_width_m
    source_join_mask = np.abs(np.abs(yy) - source_half_width_m) <= (
        OUTPUT_CROSS_SPAN_M / (output_size_px - 1)
    )
    runtime_vertical_offset_cm = -(runtime_vertical_datum_m - terrain_min_m) * 100.0
    static_centerline_world_surface_m = (
        centerline_surface - terrain_min_m + runtime_vertical_offset_cm / 100.0
    )
    runtime_centerline_surface_m = centerline_surface - runtime_vertical_datum_m
    outer_profile_dominant_band_ratios: list[float] = []
    outer_max_adjacent_steps_m: list[float] = []
    for side_mask in (target_y < -source_half_width_m, target_y > source_half_width_m):
        side_distance = np.abs(target_y[side_mask]) - source_half_width_m
        mean_profile = np.mean(conditioned[side_mask], axis=1)
        trend = np.polyval(np.polyfit(side_distance, mean_profile, 2), side_distance)
        residual = mean_profile - trend
        power = np.square(np.abs(np.fft.rfft(residual - np.mean(residual))))
        non_dc_power = power[1:]
        outer_profile_dominant_band_ratios.append(
            float(np.max(non_dc_power) / np.sum(non_dc_power))
            if np.sum(non_dc_power) > 0.0
            else 0.0
        )
        outer_max_adjacent_steps_m.append(
            float(np.max(np.abs(np.diff(conditioned[side_mask], axis=0))))
        )
    manifest: dict[str, object] = {
        "schema": SCHEMA,
        "status": (
            "generated_review_gated_reach_local_visual_and_collision_infill_"
            "not_survey_solver_or_production_terrain_authority"
        ),
        "river_id": "colorado_river",
        "section_id": "hance_corridor_station_1250m_c3_window",
        "reference_flow_band": REFERENCE_BAND,
        "inputs": {
            "window_manifest": _relative(window_manifest_path, repo_root),
            "window_manifest_sha256": _sha256(window_manifest_path),
            "cooked_manifest": _relative(cooked_manifest_path, repo_root),
            "cooked_manifest_sha256": _sha256(cooked_manifest_path),
            "bed": _relative(bed_path, repo_root),
            "bed_sha256": _sha256(bed_path),
            "depth": _relative(depth_path, repo_root),
            "depth_sha256": _sha256(depth_path),
            "wet_mask": _relative(wet_path, repo_root),
            "wet_mask_sha256": _sha256(wet_path),
        },
        "outputs": {
            "heightfield": _relative(heightfield_path, repo_root),
            "heightfield_sha256": _sha256(heightfield_path),
            "local_centerline": _relative(centerline_path, repo_root),
            "local_centerline_sha256": _sha256(centerline_path),
            "runtime_coordinate_map": _relative(coordinate_map_path, repo_root),
            "runtime_coordinate_map_sha256": _sha256(coordinate_map_path),
        },
        "landscape": {
            "size_px": output_size_px,
            "pixel_format": "16_bit_grayscale_png",
            "horizontal_span_x_m": span_x_m,
            "horizontal_span_y_m": OUTPUT_CROSS_SPAN_M,
            "source_solver_span_y_m": source_span_y_m,
            "sample_spacing_x_m": span_x_m / (output_size_px - 1),
            "sample_spacing_y_m": OUTPUT_CROSS_SPAN_M / (output_size_px - 1),
            "terrain_min_m": terrain_min_m,
            "terrain_max_m": terrain_max_m,
            "target_relief_cm": terrain_span_m * 100.0,
            "world_vertical_offset_cm": runtime_vertical_offset_cm,
            "runtime_vertical_datum_m": runtime_vertical_datum_m,
        },
        "procedural_infill": {
            "algorithm": "deterministic_nonperiodic_debris_fan_desert_canyon_v3",
            "source_solver_half_width_m": source_half_width_m,
            "protected_solver_strip_change_m": float(
                np.max(np.abs(procedural_infill[protected_mask]))
            ),
            "maximum_source_join_step_m": float(
                np.max(np.abs(procedural_infill[source_join_mask]))
            ),
            "maximum_added_canyon_relief_m": float(procedural_infill.max()),
            "maximum_outer_cross_bank_grade": maximum_outer_cross_bank_grade,
            "maximum_modeled_debris_fan_analog_relief_m": float(
                debris_fan_analog.max()
            ),
            "maximum_opposing_bedrock_buttress_relief_m": float(
                opposing_bedrock_buttress.max()
            ),
            "maximum_outer_adjacent_cross_bank_step_m": max(
                outer_max_adjacent_steps_m
            ),
            "maximum_outer_mean_profile_dominant_band_energy_ratio": max(
                outer_profile_dominant_band_ratios
            ),
            "regular_terrace_reduction_policy": (
                "replace sine-dominated cross-bank relief with seeded non-periodic "
                "fractal massing, incised drainage, irregular basement-rock "
                "buttresses, talus, and a bounded rapid-adjacent debris-fan analog"
            ),
            "official_reference_contract": {
                "usgs_hance_geomorphology": "https://pubs.usgs.gov/pp/1492/report.pdf",
                "usgs_debris_fan_process": "https://pubs.usgs.gov/fs/FS-019-01/",
                "nps_geologic_formations": "https://www.nps.gov/grca/learn/nature/geologicformations.htm",
                "nps_river_corridor_ecology": "https://www.nps.gov/grca/learn/nature/naturalfeaturesandecosystems.htm",
                "interpretation_boundary": (
                    "references constrain landform and ecology classes only; no "
                    "downloaded geometry, surveyed Hance registration, lithologic "
                    "boundary, rapid-rock coordinate, or hydraulic input is claimed"
                ),
            },
            "authority": (
                "visual and Landscape collision infill only outside the complete C3 "
                "solver strip; cooked bed, water state, and raft forces are unchanged"
            ),
        },
        "alignment": {
            "world_x_matches_runtime_station_m": True,
            "world_y_center_matches_runtime_lateral_zero": True,
            "maximum_static_to_runtime_centerline_surface_error_m": float(
                np.max(
                    np.abs(
                        static_centerline_world_surface_m - runtime_centerline_surface_m
                    )
                )
            ),
            "static_water_flow_offset_cm": 0.0,
        },
        "honesty": {
            "source_bed_geometry_authority": window_manifest["honesty"][
                "bed_geometry_authority"
            ],
            "source_reach_limitation": window_manifest["honesty"][
                "hance_outside_committed_corridor"
            ],
            "procedural_gap_fill_authority": "visual_and_collision_infill_not_survey",
            "solver_authority": _relative(cooked_manifest_path, repo_root),
            "production_promoted": False,
            "pending_human_review": True,
            "missing": [
                "surveyed Hance bathymetry, bank breaklines, and canyon terrain",
                "reviewed Hance planform and river-mile registration",
                "USGS release-history calibration",
                "guide, geospatial, ecology, art, and performance acceptance",
            ],
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


__all__ = [
    "DEFAULT_OUTPUT_RELATIVE",
    "OUTPUT_CROSS_SPAN_M",
    "REFERENCE_BAND",
    "SCHEMA",
    "build_colorado_hance_visual_terrain",
]
