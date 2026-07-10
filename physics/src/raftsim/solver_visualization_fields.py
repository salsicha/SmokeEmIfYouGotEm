"""Generate provenance-locked visual fields from an accepted C++ water frame."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


OUTPUT_ROOT_RELATIVE_PATH = Path("unreal/Content/RaftSim/Rendering/SolverVisualizationFields")
TEXTURE_ASSET_ROOT_RELATIVE_PATH = OUTPUT_ROOT_RELATIVE_PATH / "Textures"
MANIFEST_RELATIVE_PATH = OUTPUT_ROOT_RELATIVE_PATH / "cpp_solver_visualization_field_manifest.json"
NORMAL_TEXTURE_RELATIVE_PATH = (
    OUTPUT_ROOT_RELATIVE_PATH / "american_south_fork_median_cpp_solver_surface_normal_v1.png"
)
PACKED_TEXTURE_RELATIVE_PATH = (
    OUTPUT_ROOT_RELATIVE_PATH / "american_south_fork_median_cpp_solver_depth_speed_froude_v1.png"
)

SOURCE_FRAME_RELATIVE_PATH = Path(
    "physics/outputs/m16cpp/cg_med/finite_volume/cpp_solver/"
    "american_south_fork_chili_bar_to_coloma_median_runnable_intermediate_cascading/"
    "frames/frame_0008.csv"
)
SOURCE_RUN_MANIFEST_RELATIVE_PATH = SOURCE_FRAME_RELATIVE_PATH.parents[1] / "manifest.json"
PARITY_REPORT_RELATIVE_PATH = Path("physics/reports/milestone16/geoclaw_cpp_comparisons.json")
FULL_GATE_RELATIVE_PATH = Path("physics/reports/milestone16/full_cpp_validation_gate.json")
REPORT_SET_LOCK_RELATIVE_PATH = Path("physics/reports/milestone20/report_set_lock.json")

RIVER_ID = "american_south_fork"
SCENARIO_ID = "american_south_fork_chili_bar_to_coloma_median_runnable_intermediate_cascading"
GATE_SCENARIO_ID = "south_fork_cascading_median_runnable"
SOLVER_MODE = "finite_volume"
OUTPUT_SIZE = (1024, 512)
GENERATED_ON = "2026-07-10"
EXPECTED_REPORT_SET_LOCK_HASH = "267dc418cf29bcf399e5af4cadcf1398510968b419c9466cd6e13afcc64fd627"
NORMALIZATION_CAPS = {
    "depth_m": 6.0,
    "speed_mps": 10.0,
    "froude": 7.0,
    "surface_relief_m": 4.0,
}


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact(repo_root: Path, relative_path: Path) -> dict:
    path = repo_root / relative_path
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": str(relative_path),
        "sha256": _hash_file(path),
        "size_bytes": path.stat().st_size,
    }


def _load_validated_source(repo_root: Path) -> tuple[np.ndarray, dict]:
    frame_path = repo_root / SOURCE_FRAME_RELATIVE_PATH
    required_columns = {
        "row",
        "col",
        "x",
        "y",
        "h",
        "eta",
        "u",
        "v",
        "wet",
        "normal_x",
        "normal_y",
        "normal_z",
        "froude",
    }
    with frame_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
            missing = sorted(required_columns.difference(reader.fieldnames or []))
            raise ValueError(f"solver frame is missing columns: {missing}")
        rows = list(reader)
    if not rows:
        raise ValueError("solver frame is empty")

    row_ids = sorted({int(row["row"]) for row in rows})
    col_ids = sorted({int(row["col"]) for row in rows})
    if row_ids != list(range(len(row_ids))) or col_ids != list(range(len(col_ids))):
        raise ValueError("solver frame row/column ids must be contiguous and zero based")
    if len(rows) != len(row_ids) * len(col_ids):
        raise ValueError("solver frame must contain exactly one cell for every row/column pair")

    fields = np.zeros((len(row_ids), len(col_ids), 9), dtype=np.float32)
    seen: set[tuple[int, int]] = set()
    for record in rows:
        row_index = int(record["row"])
        col_index = int(record["col"])
        key = (row_index, col_index)
        if key in seen:
            raise ValueError(f"duplicate solver frame cell {key}")
        seen.add(key)
        values = (
            float(record["h"]),
            float(record["eta"]),
            float(record["u"]),
            float(record["v"]),
            float(record["froude"]),
            float(record["normal_x"]),
            float(record["normal_y"]),
            float(record["normal_z"]),
            float(record["wet"]),
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"non-finite solver field at {key}")
        fields[row_index, col_index, :] = values

    normal_lengths = np.linalg.norm(fields[:, :, 5:8], axis=2)
    wet = fields[:, :, 8] >= 0.5
    if np.any(wet & (np.abs(normal_lengths - 1.0) > 1.0e-3)):
        raise ValueError("wet-cell solver normals are not unit length")

    x_values = [float(record["x"]) for record in rows]
    y_values = [float(record["y"]) for record in rows]
    metadata = {
        "row_count": len(row_ids),
        "column_count": len(col_ids),
        "cell_count": len(rows),
        "x_extent_m": [min(x_values), max(x_values)],
        "y_extent_m": [min(y_values), max(y_values)],
        "wet_cell_count": int(np.count_nonzero(wet)),
    }
    return fields, metadata


def _validate_acceptance_evidence(repo_root: Path) -> dict:
    run_manifest = _read_json(repo_root / SOURCE_RUN_MANIFEST_RELATIVE_PATH)
    if run_manifest.get("scenario_id") != SCENARIO_ID:
        raise ValueError("source run scenario id does not match the visualization contract")
    if run_manifest.get("solver_mode") != SOLVER_MODE:
        raise ValueError("source run is not the accepted finite-volume lane")
    if run_manifest.get("boundary_mode") != "scenario" or run_manifest.get("flux_scheme") != "hll":
        raise ValueError("source run boundary/flux semantics do not match the accepted lane")
    if run_manifest.get("feature_strength_scale") != 0:
        raise ValueError("solver visualization source must keep feature forcing disabled")

    parity_report = _read_json(repo_root / PARITY_REPORT_RELATIVE_PATH)
    comparisons = parity_report.get("comparisons", parity_report.get("records", []))
    matching = [
        comparison
        for comparison in comparisons
        if comparison.get("gate_scenario_id") == GATE_SCENARIO_ID
        and comparison.get("solver_mode") == SOLVER_MODE
    ]
    if len(matching) != 1:
        raise ValueError("expected one finite-volume South Fork cascading median parity record")
    comparison = matching[0]
    if not comparison.get("compared") or not comparison.get("threshold_passed"):
        raise ValueError("GeoClaw/C++ parity record is not accepted")
    if comparison.get("failing_checks"):
        raise ValueError("GeoClaw/C++ parity record still has failing checks")

    full_gate = _read_json(repo_root / FULL_GATE_RELATIVE_PATH)
    if not full_gate.get("passed") or full_gate.get("decision") != "PASS":
        raise ValueError("full C++ validation gate is not passing")
    if full_gate.get("blocked_component_count") != 0:
        raise ValueError("full C++ validation gate still has blocked components")

    report_lock = _read_json(repo_root / REPORT_SET_LOCK_RELATIVE_PATH)
    lock_hash = report_lock.get("lock", {}).get("lock_hash")
    if not report_lock.get("passed") or lock_hash != EXPECTED_REPORT_SET_LOCK_HASH:
        raise ValueError("Milestone 20 accepted report-set lock does not match")
    if report_lock.get("production_use", {}).get("authoritative_water_source") != (
        "custom_cxx_shallow_water_solver"
    ):
        raise ValueError("report-set lock does not assign water authority to the C++ solver")

    return {
        "feature_strength_scale": run_manifest["feature_strength_scale"],
        "boundary_mode": run_manifest["boundary_mode"],
        "flux_scheme": run_manifest["flux_scheme"],
        "threshold_tier": comparison["threshold_tier"],
        "threshold_report": comparison["threshold_report"],
        "report_set_lock_hash": lock_hash,
    }


def _resize_texture(array: np.ndarray) -> Image.Image:
    mode = "RGBA" if array.shape[2] == 4 else "RGB"
    image = Image.fromarray(np.clip(np.rint(array * 255.0), 0, 255).astype(np.uint8), mode=mode)
    return image.resize(OUTPUT_SIZE, Image.Resampling.BILINEAR)


def generate_solver_visualization_fields(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    fields, grid = _load_validated_source(repo_root)
    evidence = _validate_acceptance_evidence(repo_root)

    depth = fields[:, :, 0]
    eta = fields[:, :, 1]
    speed = np.hypot(fields[:, :, 2], fields[:, :, 3])
    froude = fields[:, :, 4]
    normals = fields[:, :, 5:8]
    wet = fields[:, :, 8] >= 0.5
    texture_normals = normals.copy()
    texture_normals[~wet] = (0.0, 0.0, 1.0)
    normal_encoded = np.clip(texture_normals * 0.5 + 0.5, 0.0, 1.0)

    column_eta = np.zeros(eta.shape[1], dtype=np.float64)
    for column_index in range(eta.shape[1]):
        wet_column = eta[:, column_index][wet[:, column_index]]
        if wet_column.size == 0:
            raise ValueError(f"solver frame column {column_index} has no wet free-surface samples")
        column_eta[column_index] = float(np.median(wet_column))
    column_coordinates = np.arange(eta.shape[1], dtype=np.float64)
    trend_slope, trend_intercept = np.polyfit(column_coordinates, column_eta, 1)
    eta_trend = trend_slope * column_coordinates + trend_intercept
    surface_relief = eta - eta_trend[np.newaxis, :]
    surface_relief[~wet] = 0.0
    surface_relief_encoded = np.clip(
        surface_relief / (2.0 * NORMALIZATION_CAPS["surface_relief_m"]) + 0.5,
        0.0,
        1.0,
    )
    packed = np.stack(
        (
            np.clip(depth / NORMALIZATION_CAPS["depth_m"], 0.0, 1.0),
            np.clip(speed / NORMALIZATION_CAPS["speed_mps"], 0.0, 1.0),
            np.clip(froude / NORMALIZATION_CAPS["froude"], 0.0, 1.0),
            surface_relief_encoded,
        ),
        axis=2,
    )

    normal_path = repo_root / NORMAL_TEXTURE_RELATIVE_PATH
    packed_path = repo_root / PACKED_TEXTURE_RELATIVE_PATH
    normal_path.parent.mkdir(parents=True, exist_ok=True)
    _resize_texture(normal_encoded).save(normal_path, optimize=True)
    _resize_texture(packed).save(packed_path, optimize=True)

    actual_ranges = {
        "depth_m": [float(np.min(depth)), float(np.max(depth))],
        "speed_mps": [float(np.min(speed)), float(np.max(speed))],
        "froude": [float(np.min(froude)), float(np.max(froude))],
        "surface_relief_m": [float(np.min(surface_relief)), float(np.max(surface_relief))],
        "normal_x": [float(np.min(normals[:, :, 0])), float(np.max(normals[:, :, 0]))],
        "normal_y": [float(np.min(normals[:, :, 1])), float(np.max(normals[:, :, 1]))],
        "normal_z": [float(np.min(normals[:, :, 2])), float(np.max(normals[:, :, 2]))],
    }
    manifest = {
        "schema": "raftsim.unreal.cpp_solver_visualization_fields.v1",
        "generated_on": GENERATED_ON,
        "status": "validated_cpp_solver_visualization_fields_generated_for_south_fork_review",
        "river_id": RIVER_ID,
        "scenario_id": SCENARIO_ID,
        "flow_band": "median",
        "solver": "raftsim_water_cpp_v1",
        "solver_mode": SOLVER_MODE,
        "source_frame_index": 8,
        "source_grid": grid,
        "source_artifacts": {
            "frame": _artifact(repo_root, SOURCE_FRAME_RELATIVE_PATH),
            "run_manifest": _artifact(repo_root, SOURCE_RUN_MANIFEST_RELATIVE_PATH),
            "geoclaw_cpp_parity": _artifact(repo_root, PARITY_REPORT_RELATIVE_PATH),
            "full_cpp_validation_gate": _artifact(repo_root, FULL_GATE_RELATIVE_PATH),
            "accepted_report_set_lock": _artifact(repo_root, REPORT_SET_LOCK_RELATIVE_PATH),
        },
        "acceptance_evidence": evidence,
        "field_ranges": actual_ranges,
        "normalization": {
            "policy": "fixed_physical_caps_clamp_to_unit_interval",
            "caps": NORMALIZATION_CAPS,
            "reason": "stable cross-frame authoring scale; accepted frame extrema remain inside every cap",
        },
        "surface_relief_derivation": {
            "source_field": "eta",
            "detrending": "subtract_least_squares_linear_fit_of_per_column_wet_cell_median_eta",
            "trend_slope_m_per_column": float(trend_slope),
            "trend_intercept_m": float(trend_intercept),
            "dry_cell_value_m": 0.0,
            "wet_cell_clipped_fraction": float(
                np.count_nonzero(wet & (np.abs(surface_relief) > NORMALIZATION_CAPS["surface_relief_m"]))
                / np.count_nonzero(wet)
            ),
            "render_height_scale": 0.09,
            "render_height_cap_cm": NORMALIZATION_CAPS["surface_relief_m"] * 100.0 * 0.09,
        },
        "textures": {
            "surface_normal": {
                "path": str(NORMAL_TEXTURE_RELATIVE_PATH),
                "sha256": _hash_file(normal_path),
                "width": OUTPUT_SIZE[0],
                "height": OUTPUT_SIZE[1],
                "channels": "RGB=(normal_xyz*0.5)+0.5; dry cells use flat-up (0,0,1)",
                "unreal_texture_asset": (
                    "/Game/RaftSim/Rendering/SolverVisualizationFields/Textures/"
                    "T_RaftSim_AmericanSouthFork_CppSolverSurfaceNormal"
                ),
                "material_parameter": "SolverVisualizationNormal",
            },
            "depth_speed_froude": {
                "path": str(PACKED_TEXTURE_RELATIVE_PATH),
                "sha256": _hash_file(packed_path),
                "width": OUTPUT_SIZE[0],
                "height": OUTPUT_SIZE[1],
                "channels": "R=depth_m/6 G=speed_mps/10 B=froude/7 A=detrended_eta_relief_m/8+0.5",
                "unreal_texture_asset": (
                    "/Game/RaftSim/Rendering/SolverVisualizationFields/Textures/"
                    "T_RaftSim_AmericanSouthFork_CppSolverDepthSpeedFroude"
                ),
                "material_parameter": "SolverVisualizationFields",
            },
        },
        "sampling": {
            "source_orientation": "image_x_increasing_solver_column_and_downstream_x; image_y_increasing_solver_row_and_lateral_y",
            "resampling": "bilinear_56x20_to_1024x512",
            "unreal_address_mode": "clamp_xy",
            "landscape_candidate_uv_contract": "procedural_ribbon_u_times_18_is_divided_by_18_in_material; v_is_cross_channel",
            "solver_rapid_capture": {
                "camera_world_x_cm": 240.0,
                "target_world_x_cm": 4740.0,
                "camera_solver_u": (240.0 + 11600.0) / 37800.0,
                "target_solver_u": (4740.0 + 11600.0) / 37800.0,
                "intent": "frame the accepted median field approach spanning the strongest mean-Froude columns",
            },
        },
        "render_binding": {
            "material_parent": "/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SingleLayerWaterCandidate",
            "material_instance": (
                "/Game/RaftSim/Materials/LandscapeCandidates/"
                "MI_RaftSim_AmericanSouthFork_SingleLayerWaterCandidate"
            ),
            "river_scope": [RIVER_ID],
            "other_river_status": "not_bound_until_equivalent_river_specific_validated_cpp_exports_exist",
            "feature_weights": {
                "macro_normal": 0.22,
                "depth_color": 0.20,
                "speed_froude_roughness": 0.10,
                "froude_aeration": 0.34,
                "surface_relief_geometry": 0.09,
            },
            "visual_decode_gains": {
                "speed": 1.50,
                "froude": 3.00,
                "policy": "bounded_decode_of_fixed_physical_normalization_not_feature_forcing",
            },
            "foam_overlay": {
                "material": (
                    "/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverFieldFoamCandidate"
                ),
                "mask": "decoded_speed_times_froude_hydraulic_presence_with_procedural_micro_breakup",
                "max_opacity": 0.72,
                "surface_offset_cm": 1.4,
                "collision_enabled": False,
                "policy": "procedural_breakup_is_confined_to_validated_hydraulic_aeration_mask",
            },
        },
        "authority_policy": {
            "physical_authority": "custom_cxx_shallow_water_solver",
            "derivative_scope": "review_only_noncolliding_render_geometry_and_material_response_on_landscape_candidate_ribbon",
            "feature_forcing_enabled": False,
            "changes_collision_or_raft_forces": False,
            "changes_solver_state": False,
            "may_hide_conservation_or_parity_failures": False,
            "promotion_requires_river_specific_live_bridge_alignment": True,
        },
    }
    manifest_path = repo_root / MANIFEST_RELATIVE_PATH
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
