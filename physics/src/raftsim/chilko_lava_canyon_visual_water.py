"""Build a provenance-locked Lava Canyon capture-water derivative.

The RGBA field drives only the non-colliding authored ribbon and foam used by
deterministic editor captures.  Gameplay continues to load the cooked arrays
and uses the custom C++ shallow-water solver as the physical authority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


SCHEMA = "raftsim.unreal.chilko_lava_canyon_solver_visualization.v1"
GENERATED_ON = "2026-08-01"
RIVER_ID = "chilko_river_lava_canyon"
FLOW_BAND = "median_runnable"
OUTPUT_SIZE = (1024, 256)
SOURCE_ROOT_RELATIVE = Path(
    "physics/data/real_world/chilko_river_lava_canyon/"
    "scenario_lava_canyon/cooked_flow_fields"
)
SOURCE_MANIFEST_RELATIVE = SOURCE_ROOT_RELATIVE / "manifest.json"
OUTPUT_ROOT_RELATIVE = Path(
    "unreal/Content/RaftSim/Rendering/SolverVisualizationFields"
)
PACKED_TEXTURE_RELATIVE = (
    OUTPUT_ROOT_RELATIVE
    / "chilko_lava_canyon_median_depth_speed_froude_surface_v1.png"
)
MANIFEST_RELATIVE = (
    OUTPUT_ROOT_RELATIVE / "chilko_lava_canyon_median_visualization_manifest.json"
)
NORMALIZATION_CAPS = {
    "depth_m": 5.0,
    "speed_mps": 8.0,
    "froude": 4.5,
    "surface_relief_m": 1.5,
}
RENDER_HEIGHT_SCALE = 0.26


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact(repo_root: Path, relative_path: Path) -> dict[str, object]:
    path = repo_root / relative_path
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": str(relative_path),
        "sha256": _hash_file(path),
        "size_bytes": path.stat().st_size,
    }


def _load_source(
    repo_root: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, np.ndarray]]:
    manifest = json.loads(
        (repo_root / SOURCE_MANIFEST_RELATIVE).read_text(encoding="utf-8")
    )
    if manifest.get("schema") != "raftsim.cooked_flow_fields.v1":
        raise ValueError("Lava Canyon cooked-field manifest has an unexpected schema")
    if manifest.get("solver", {}).get("solver") != "raftsim_water_cpp_v1":
        raise ValueError("Lava Canyon visualization must come from the C++ solver")
    if manifest.get("solver", {}).get("feature_strength_scale") != 0.0:
        raise ValueError("Lava Canyon source must keep feature forcing disabled")

    matches = [
        band for band in manifest.get("bands", []) if band.get("band_id") == FLOW_BAND
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one {FLOW_BAND!r} cooked-field band")
    band = matches[0]

    arrays: dict[str, np.ndarray] = {}
    for field_id in ("bed", "h", "u", "v", "wet_mask"):
        record = band["arrays"][field_id]
        relative_path = SOURCE_ROOT_RELATIVE / record["file"]
        path = repo_root / relative_path
        if _hash_file(path) != record["sha256"]:
            raise ValueError(f"{field_id} does not match the cooked manifest hash")
        array = np.load(path, allow_pickle=False)
        if list(array.shape) != record["shape"] or str(array.dtype) != record["dtype"]:
            raise ValueError(f"{field_id} shape/dtype differs from the cooked manifest")
        if not np.all(np.isfinite(array)):
            raise ValueError(f"{field_id} contains non-finite values")
        arrays[field_id] = array

    wet = arrays["wet_mask"].astype(bool)
    if not np.any(wet) or np.any(arrays["h"][wet] <= 0.0):
        raise ValueError("Lava Canyon cooked source must contain wet positive depths")
    return manifest, band, arrays


def _range(values: np.ndarray) -> list[float]:
    return [float(np.min(values)), float(np.max(values))]


def build_chilko_lava_canyon_visual_water(
    repo_root: Path, output_dir: Path | None = None
) -> dict[str, object]:
    """Generate the committed Lava Canyon capture derivative and manifest."""

    repo_root = repo_root.resolve()
    source_manifest, band, arrays = _load_source(repo_root)
    bed = arrays["bed"].astype(np.float64)
    depth = arrays["h"].astype(np.float64)
    speed = np.hypot(arrays["u"], arrays["v"]).astype(np.float64)
    wet = arrays["wet_mask"].astype(bool)
    froude = np.zeros_like(depth)
    froude[wet] = speed[wet] / np.sqrt(9.80665 * depth[wet])

    grid = source_manifest["grid"]
    station_m = grid["origin_x_m"] + np.arange(grid["nx"]) * grid["dx_m"]
    surface = bed + depth
    column_surface = np.asarray(
        [
            np.median(surface[:, column][wet[:, column]])
            for column in range(surface.shape[1])
        ],
        dtype=np.float64,
    )
    trend_slope, trend_intercept = np.polyfit(station_m, column_surface, 1)
    surface_relief = surface - (trend_slope * station_m + trend_intercept)[None, :]
    surface_relief[~wet] = 0.0

    packed = np.stack(
        (
            np.clip(depth / NORMALIZATION_CAPS["depth_m"], 0.0, 1.0),
            np.clip(speed / NORMALIZATION_CAPS["speed_mps"], 0.0, 1.0),
            np.clip(froude / NORMALIZATION_CAPS["froude"], 0.0, 1.0),
            np.clip(
                surface_relief / (2.0 * NORMALIZATION_CAPS["surface_relief_m"])
                + 0.5,
                0.0,
                1.0,
            ),
        ),
        axis=2,
    )
    packed[~wet, 0:3] = 0.0
    packed[~wet, 3] = 0.5
    image = Image.fromarray(
        np.clip(np.rint(packed * 255.0), 0, 255).astype(np.uint8), mode="RGBA"
    ).resize(OUTPUT_SIZE, Image.Resampling.BILINEAR)
    packed_path = (
        output_dir / PACKED_TEXTURE_RELATIVE.name
        if output_dir is not None
        else repo_root / PACKED_TEXTURE_RELATIVE
    )
    packed_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(packed_path, optimize=True)

    wet_froude = froude[wet]
    wet_speed = speed[wet]
    eligible_foam = wet & (froude >= 0.80) & (speed >= 1.20)
    supercritical = wet & (froude >= 1.0)
    column_mean_froude = np.asarray(
        [
            np.mean(froude[:, column][wet[:, column]])
            for column in range(froude.shape[1])
        ]
    )
    strongest_column = int(np.argmax(column_mean_froude))
    strongest_progress = strongest_column / max(1, froude.shape[1] - 1)

    source_artifacts = {"manifest": _artifact(repo_root, SOURCE_MANIFEST_RELATIVE)}
    for field_id, record in band["arrays"].items():
        source_artifacts[field_id] = _artifact(
            repo_root, SOURCE_ROOT_RELATIVE / record["file"]
        )

    convergence = band["convergence"]
    provenance = source_manifest["window_provenance"]
    manifest: dict[str, object] = {
        "schema": SCHEMA,
        "generated_on": GENERATED_ON,
        "status": "reference_runnable_capture_visualization_not_production_promoted",
        "river_id": RIVER_ID,
        "rapid_name": "Lava Canyon",
        "flow_band": FLOW_BAND,
        "source_scenario_id": band["scenario_id"],
        "source_artifacts": source_artifacts,
        "source_grid": grid,
        "solver_evidence": {
            "solver": source_manifest["solver"]["solver"],
            "solver_mode": source_manifest["solver"]["solver_mode"],
            "flux_scheme": source_manifest["solver"]["flux_scheme"],
            "spatial_order": source_manifest["solver"]["spatial_order"],
            "feature_strength_scale": source_manifest["solver"][
                "feature_strength_scale"
            ],
            "converged": convergence["converged"],
            "final_convergence_window": convergence["final_window"],
            "bed_geometry_authority": provenance["bed_geometry_authority"],
            "discharge_authority": "scenario_planning_band_pending_review",
            "pending_human_review": provenance["pending_human_review"],
            "production_promoted": provenance["production_promoted"],
        },
        "field_ranges": {
            "wet_depth_m": _range(depth[wet]),
            "wet_speed_mps": _range(wet_speed),
            "wet_froude": _range(wet_froude),
            "wet_surface_relief_m": _range(surface_relief[wet]),
        },
        "normalization": {
            "policy": "fixed_physical_caps_clamp_to_unit_interval",
            "caps": NORMALIZATION_CAPS,
        },
        "surface_relief_derivation": {
            "source_field": "bed_plus_h",
            "detrending": (
                "subtract_least_squares_fit_of_per_column_wet_cell_median_surface"
            ),
            "trend_slope_m_per_m": float(trend_slope),
            "trend_intercept_m": float(trend_intercept),
            "wet_cell_clipped_fraction": float(
                np.count_nonzero(
                    wet
                    & (np.abs(surface_relief) > NORMALIZATION_CAPS["surface_relief_m"])
                )
                / np.count_nonzero(wet)
            ),
            "render_height_scale": RENDER_HEIGHT_SCALE,
            "render_height_cap_cm": (
                NORMALIZATION_CAPS["surface_relief_m"]
                * 100.0
                * RENDER_HEIGHT_SCALE
            ),
        },
        "hydraulic_visualization_evidence": {
            "wet_cell_count": int(np.count_nonzero(wet)),
            "supercritical_cell_count": int(np.count_nonzero(supercritical)),
            "foam_eligible_cell_count": int(np.count_nonzero(eligible_foam)),
            "foam_mask": "wet_and_froude_at_least_0.80_and_speed_at_least_1.20_mps",
            "strongest_column_index": strongest_column,
            "strongest_column_station_m": float(station_m[strongest_column]),
            "strongest_column_mean_froude": float(
                column_mean_froude[strongest_column]
            ),
            "camera_progress": {
                "guide": float(np.clip(strongest_progress - 0.11, 0.05, 0.78)),
                "guide_target": float(
                    np.clip(strongest_progress - 0.01, 0.15, 0.92)
                ),
                "river_eye": float(
                    np.clip(strongest_progress - 0.075, 0.08, 0.82)
                ),
                "river_eye_target": float(
                    np.clip(strongest_progress + 0.025, 0.18, 0.95)
                ),
                "solver_rapid": float(
                    np.clip(strongest_progress - 0.055, 0.10, 0.84)
                ),
                "solver_rapid_target": float(
                    np.clip(strongest_progress + 0.045, 0.20, 0.96)
                ),
            },
        },
        "texture": {
            "path": str(PACKED_TEXTURE_RELATIVE),
            "sha256": _hash_file(packed_path),
            "width": OUTPUT_SIZE[0],
            "height": OUTPUT_SIZE[1],
            "channels": (
                "R=depth_m/5 G=speed_mps/8 B=froude/4.5 "
                "A=detrended_surface_relief_m/3+0.5"
            ),
            "source_orientation": (
                "image_x_increases_downstream_station; image_y_increases_from_"
                "river_right_to_river_left"
            ),
        },
        "render_binding": {
            "map": "/Game/RaftSim/Maps/L_LavaCanyon",
            "surface_actor": (
                "RaftSim_PhysicalCorridorRiverRibbon_chilko_river_lava_canyon"
            ),
            "foam_actor": "RaftSim_SolverFieldFoam_chilko_river_lava_canyon",
            "capture_only": True,
            "hidden_in_game": True,
            "collision_enabled": False,
            "runtime_water_owner": "ARaftSimWaterSurfaceActor_live_cooked_field_window",
            "foam_surface_offset_cm": 1.4,
            "foam_downstream_persistence_m": 8.0,
        },
        "authority_policy": {
            "physical_authority": "live_custom_cxx_shallow_water_solver",
            "derivative_scope": (
                "capture_only_noncolliding_authored_ribbon_color_relief_and_foam"
            ),
            "changes_collision_or_raft_forces": False,
            "changes_solver_state": False,
            "changes_cooked_fields": False,
            "may_be_used_as_production_calibration_evidence": False,
            "reason": (
                "source convergence is false and Lava Canyon geometry, flow bands, "
                "stationing, hazards, and guide lines remain review-gated"
            ),
        },
    }
    manifest_path = (
        output_dir / MANIFEST_RELATIVE.name
        if output_dir is not None
        else repo_root / MANIFEST_RELATIVE
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


__all__ = [
    "FLOW_BAND",
    "MANIFEST_RELATIVE",
    "NORMALIZATION_CAPS",
    "PACKED_TEXTURE_RELATIVE",
    "SCHEMA",
    "build_chilko_lava_canyon_visual_water",
]
