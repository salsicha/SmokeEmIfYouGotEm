"""Build stitched source-window validation status for South Fork A1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .south_fork_a1_window_manifests import (
    FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH,
)
from .south_fork_a1_window_source_status import (
    FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
)


FULL_REACH_WINDOW_STITCHED_VALIDATION_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_window_stitched_validation_report.json"
)

_STATION_TOLERANCE_M = 1e-6


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _manifest_path(root: Path, entry: dict[str, Any]) -> Path:
    return root / str(entry["manifest_path"])


def _interval_gap(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    if a_max < b_min:
        return b_min - a_max
    if b_max < a_min:
        return a_min - b_max
    return 0.0


def _interval_overlap(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))


def _bbox_relationship(left: list[float], right: list[float]) -> dict[str, Any]:
    x_gap = _interval_gap(left[0], left[2], right[0], right[2])
    y_gap = _interval_gap(left[1], left[3], right[1], right[3])
    x_overlap = _interval_overlap(left[0], left[2], right[0], right[2])
    y_overlap = _interval_overlap(left[1], left[3], right[1], right[3])
    return {
        "x_gap_m": round(x_gap, 6),
        "y_gap_m": round(y_gap, 6),
        "x_overlap_m": round(x_overlap, 6),
        "y_overlap_m": round(y_overlap, 6),
        "overlaps_or_touches_in_epsg3857": x_gap <= _STATION_TOLERANCE_M
        and y_gap <= _STATION_TOLERANCE_M,
    }


def _resolution_ratio(left: list[float], right: list[float]) -> dict[str, float]:
    x_ratio = max(left[0], right[0]) / max(min(left[0], right[0]), _STATION_TOLERANCE_M)
    y_ratio = max(left[1], right[1]) / max(min(left[1], right[1]), _STATION_TOLERANCE_M)
    return {
        "x_ratio": round(x_ratio, 6),
        "y_ratio": round(y_ratio, 6),
    }


def _window_check(repo_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    manifest = _load_json(repo_root, str(entry["manifest_path"]))
    dem = manifest["source_artifacts"]["dem"]
    aerial = manifest["source_artifacts"]["aerial"]
    return {
        "window_id": manifest["window_id"],
        "display_name": manifest["display_name"],
        "manifest_path": entry["manifest_path"],
        "manifest_present": _manifest_path(repo_root, entry).exists(),
        "station_range_m": manifest["station_range_m"],
        "source_bounds_epsg3857": dem["source_bounds_epsg3857"],
        "source_hashes_recorded": len(dem["sha256"]) == 64
        and len(aerial["sha256"]) == 64,
        "source_dimensions": {
            "dem": dem["dimensions"],
            "aerial": aerial["dimensions"],
        },
        "pixel_resolution_m_approx": {
            "dem": dem["pixel_resolution_m_approx"],
            "aerial": aerial["pixel_resolution_m_approx"],
        },
        "can_enter_stitched_validation_review": manifest["promotion_gate"][
            "can_enter_stitched_validation_review"
        ],
        "can_generate_window_derivatives": manifest["promotion_gate"][
            "can_generate_window_derivatives"
        ],
        "can_import_unreal_landscape": manifest["promotion_gate"][
            "can_import_unreal_landscape"
        ],
        "production_promoted": manifest["production_promoted"],
    }


def _seam_check(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_station = left["station_range_m"]
    right_station = right["station_range_m"]
    station_gap = float(right_station["start"]) - float(left_station["end"])
    station_overlap = max(0.0, float(left_station["end"]) - float(right_station["start"]))
    bbox = _bbox_relationship(
        left["source_bounds_epsg3857"],
        right["source_bounds_epsg3857"],
    )
    return {
        "seam_id": f"{left['window_id']}__to__{right['window_id']}",
        "upstream_window_id": left["window_id"],
        "downstream_window_id": right["window_id"],
        "station_gap_m": round(station_gap, 6),
        "station_overlap_m": round(station_overlap, 6),
        "station_contiguous": abs(station_gap) <= _STATION_TOLERANCE_M
        and station_overlap <= _STATION_TOLERANCE_M,
        "source_bbox_relationship": bbox,
        "source_grid_relationship": {
            "same_crs": True,
            "dem_dimension_match": left["source_dimensions"]["dem"]
            == right["source_dimensions"]["dem"],
            "aerial_dimension_match": left["source_dimensions"]["aerial"]
            == right["source_dimensions"]["aerial"],
            "dem_resolution_ratio": _resolution_ratio(
                left["pixel_resolution_m_approx"]["dem"],
                right["pixel_resolution_m_approx"]["dem"],
            ),
            "aerial_resolution_ratio": _resolution_ratio(
                left["pixel_resolution_m_approx"]["aerial"],
                right["pixel_resolution_m_approx"]["aerial"],
            ),
        },
        "review_required": True,
        "can_hide_physics_errors": False,
    }


def build_south_fork_a1_window_stitched_validation_report(
    repo_root: Path,
) -> dict[str, Any]:
    """Build a deterministic report for stitched A1 source-window review."""

    repo_root = repo_root.resolve()
    index = _load_json(repo_root, FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH)
    status = _load_json(repo_root, FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH)
    windows = [_window_check(repo_root, entry) for entry in index["window_manifests"]]
    windows = sorted(
        windows,
        key=lambda window: float(window["station_range_m"]["start"]),
    )
    seams = [
        _seam_check(left, right)
        for left, right in zip(windows, windows[1:], strict=False)
    ]
    station_gap_count = sum(
        not seam["station_contiguous"]
        for seam in seams
    )
    bbox_touch_count = sum(
        seam["source_bbox_relationship"]["overlaps_or_touches_in_epsg3857"]
        for seam in seams
    )
    all_window_manifests_present = all(window["manifest_present"] for window in windows)
    all_hashes_recorded = all(window["source_hashes_recorded"] for window in windows)
    return {
        "schema": "raftsim.south_fork.a1_full_reach_window_stitched_validation.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": index["river_id"],
        "status": "stitched_source_window_validation_ready_derivatives_pending",
        "production_promoted": False,
        "inputs": {
            "source_manifest_index": FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH,
            "source_pull_status": FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
        },
        "summary": {
            "window_count": len(windows),
            "seam_count": len(seams),
            "all_window_manifests_present": all_window_manifests_present,
            "all_source_files_present": status["summary"]["all_source_files_present"],
            "all_hashes_recorded": all_hashes_recorded,
            "station_gap_count": station_gap_count,
            "station_overlap_count": sum(
                seam["station_overlap_m"] > _STATION_TOLERANCE_M
                for seam in seams
            ),
            "source_bbox_overlaps_or_touches_count": bbox_touch_count,
            "source_bbox_gap_count": len(seams) - bbox_touch_count,
            "can_generate_stitched_validation_derivatives": (
                all_window_manifests_present
                and all_hashes_recorded
                and status["summary"]["all_source_files_present"]
                and station_gap_count == 0
            ),
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "can_promote_full_reach_corridor": False,
        },
        "review_scope": {
            "validates": [
                "Per-window manifests are present and hash locked.",
                "Station ranges are contiguous across the six source windows.",
                "Every source-window seam is visible as an explicit review object.",
                "Source bbox overlap/gap metadata is recorded before preview generation.",
            ],
            "does_not_validate": [
                "Photoreal material quality.",
                "Hydrologically conditioned terrain correctness.",
                "Exact Salmon Falls/Folsom downstream anchor.",
                "Named rapid bank/cross-section geometry.",
                "Unreal landscape import readiness.",
            ],
        },
        "windows": windows,
        "seams": seams,
        "promotion_gate": {
            "can_generate_stitched_validation_derivatives": (
                all_window_manifests_present
                and all_hashes_recorded
                and status["summary"]["all_source_files_present"]
                and station_gap_count == 0
            ),
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "can_promote_full_reach_corridor": False,
            "next_required_actions": [
                "Generate hillshade, heightfield, NAIP-centerline, and seam-preview derivatives.",
                "Review source bbox gaps/overlaps visually against the whole route before stitching.",
                "Resolve the exact Salmon Falls/Folsom downstream anchor before final crop.",
                "Attach bank, cross-section, guide, and geospatial review before Unreal import.",
            ],
        },
    }


def write_south_fork_a1_window_stitched_validation_report(repo_root: Path) -> Path:
    payload = build_south_fork_a1_window_stitched_validation_report(repo_root)
    path = repo_root.resolve() / FULL_REACH_WINDOW_STITCHED_VALIDATION_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
