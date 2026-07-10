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

    fields = np.zeros((len(row_ids), len(col_ids), 8), dtype=np.float32)
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

    normal_lengths = np.linalg.norm(fields[:, :, 4:7], axis=2)
    wet = fields[:, :, 7] >= 0.5
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


def _resize_rgb(array: np.ndarray) -> Image.Image:
    image = Image.fromarray(np.clip(np.rint(array * 255.0), 0, 255).astype(np.uint8), mode="RGB")
    return image.resize(OUTPUT_SIZE, Image.Resampling.BILINEAR)


def generate_solver_visualization_fields(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    fields, grid = _load_validated_source(repo_root)
    evidence = _validate_acceptance_evidence(repo_root)

    depth = fields[:, :, 0]
    speed = np.hypot(fields[:, :, 1], fields[:, :, 2])
    froude = fields[:, :, 3]
    normals = fields[:, :, 4:7]
    wet = fields[:, :, 7] >= 0.5
    texture_normals = normals.copy()
    texture_normals[~wet] = (0.0, 0.0, 1.0)
    normal_encoded = np.clip(texture_normals * 0.5 + 0.5, 0.0, 1.0)
    packed = np.stack(
        (
            np.clip(depth / NORMALIZATION_CAPS["depth_m"], 0.0, 1.0),
            np.clip(speed / NORMALIZATION_CAPS["speed_mps"], 0.0, 1.0),
            np.clip(froude / NORMALIZATION_CAPS["froude"], 0.0, 1.0),
        ),
        axis=2,
    )

    normal_path = repo_root / NORMAL_TEXTURE_RELATIVE_PATH
    packed_path = repo_root / PACKED_TEXTURE_RELATIVE_PATH
    normal_path.parent.mkdir(parents=True, exist_ok=True)
    _resize_rgb(normal_encoded).save(normal_path, optimize=True)
    _resize_rgb(packed).save(packed_path, optimize=True)

    actual_ranges = {
        "depth_m": [float(np.min(depth)), float(np.max(depth))],
        "speed_mps": [float(np.min(speed)), float(np.max(speed))],
        "froude": [float(np.min(froude)), float(np.max(froude))],
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
                "channels": "R=depth_m/6 G=speed_mps/10 B=froude/7",
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
                "macro_normal": 0.55,
                "depth_color": 0.20,
                "speed_froude_roughness": 0.10,
                "froude_aeration": 0.18,
            },
        },
        "authority_policy": {
            "physical_authority": "custom_cxx_shallow_water_solver",
            "derivative_scope": "review_only_material_response_on_landscape_candidate_ribbon",
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
