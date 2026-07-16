"""Preflight review for South Fork A1 full-reach source downloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .south_fork_a1_anchor_review import FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH
from .south_fork_a1_corridor_windows import (
    FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH,
)
from .south_fork_a1_window_source_execution import (
    FULL_REACH_WINDOW_SOURCE_PULL_EXECUTION_PLAN_RELATIVE_PATH,
)
from .south_fork_a1_window_source_status import (
    FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
)


FULL_REACH_WINDOW_SOURCE_PULL_PREFLIGHT_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_window_source_pull_preflight_review.json"
)
_STATION_TOLERANCE_M = 0.01


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _downstream_anchor(anchor_review: dict[str, Any]) -> dict[str, Any]:
    return next(
        anchor for anchor in anchor_review["anchor_reviews"] if anchor["role"] == "downstream_end"
    )


def _window_gap_report(windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps = []
    for left, right in zip(windows, windows[1:], strict=False):
        gap_m = float(right["station_start_m"]) - float(left["station_end_m"])
        if abs(gap_m) > _STATION_TOLERANCE_M:
            gaps.append(
                {
                    "from_window_id": left["window_id"],
                    "to_window_id": right["window_id"],
                    "gap_m": round(gap_m, 6),
                }
            )
    return gaps


def build_south_fork_a1_window_source_pull_preflight(repo_root: Path) -> dict[str, Any]:
    """Review planned source downloads against the unresolved downstream anchor."""

    repo_root = repo_root.resolve()
    anchor_review = _load_json(repo_root, FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH)
    window_manifest = _load_json(repo_root, FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH)
    execution_plan = _load_json(repo_root, FULL_REACH_WINDOW_SOURCE_PULL_EXECUTION_PLAN_RELATIVE_PATH)
    status_report = _load_json(repo_root, FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH)
    downstream = _downstream_anchor(anchor_review)
    source_window = downstream["source_mile_window"]
    windows = window_manifest["windows"]
    final_window = windows[-1]
    gap_report = _window_gap_report(windows)
    planned_end_m = float(window_manifest["coverage_summary"]["planned_station_end_m"])
    source_window_min_m = float(source_window["minimum_mile"]) * 1609.344
    source_window_max_m = float(source_window["maximum_mile"]) * 1609.344
    final_window_matches_ambiguity = (
        abs(float(final_window["station_start_m"]) - source_window_min_m) <= _STATION_TOLERANCE_M
        and abs(float(final_window["station_end_m"]) - source_window_max_m) <= _STATION_TOLERANCE_M
    )
    can_execute_overcover = (
        downstream["current_seed_status"] == "missing_exact_anchor"
        and final_window_matches_ambiguity
        and not gap_report
        and execution_plan["summary"]["task_count"] == 12
        and status_report["summary"]["expected_source_file_count"] == 12
    )
    source_files_present = status_report["summary"]["all_source_files_present"]
    if not can_execute_overcover:
        status = "source_pull_preflight_blocked"
    elif source_files_present:
        status = "nonpromotional_source_files_present_window_manifests_pending_exact_anchor_pending"
    else:
        status = "nonpromotional_overcover_source_pull_preflight_passed_exact_anchor_pending"
    next_required_actions = (
        [
            "Generate per-window manifests plus source terms, CRS, resolution, bounds, and derivative targets.",
            "Produce stitched seam-validation previews before Unreal import.",
            "Resolve the exact Salmon Falls/Folsom downstream anchor before any cropping, Unreal import, or rapid binding.",
        ]
        if source_files_present
        else [
            "Run the bounded source-pull executor for the official DEM/NAIP URLs.",
            "Regenerate the source-pull status report and verify all 12 source files have byte counts and SHA-256 hashes.",
            "Generate per-window manifests plus stitched seam-validation previews.",
            "Resolve the exact Salmon Falls/Folsom downstream anchor before any cropping, Unreal import, or rapid binding.",
        ]
    )

    return {
        "schema": "raftsim.south_fork.a1_window_source_pull_preflight_review.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": window_manifest["river_id"],
        "status": status,
        "production_promoted": False,
        "inputs": {
            "anchor_review": FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH,
            "corridor_window_manifest": FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH,
            "source_pull_execution_plan": FULL_REACH_WINDOW_SOURCE_PULL_EXECUTION_PLAN_RELATIVE_PATH,
            "source_pull_status": FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
        },
        "downstream_anchor_review": {
            "anchor_id": downstream["anchor_id"],
            "current_seed_status": downstream["current_seed_status"],
            "exact_anchor_available": downstream["current_seed_lon_lat"] is not None,
            "source_mile_window": source_window,
            "source_window_min_station_m": round(source_window_min_m, 6),
            "source_window_max_station_m": round(source_window_max_m, 6),
            "planned_station_end_m": planned_end_m,
            "final_window_id": final_window["window_id"],
            "final_window_start_m": final_window["station_start_m"],
            "final_window_end_m": final_window["station_end_m"],
            "final_window_matches_source_mile_ambiguity": final_window_matches_ambiguity,
            "interpretation": (
                "The final planned source-pull window intentionally over-covers the "
                "20.5-21.0 mile Salmon Falls/Folsom ambiguity. This is acceptable "
                "for source acquisition, but not for corridor cropping, editor "
                "binding, or solver-window promotion."
            ),
        },
        "window_continuity": {
            "window_count": len(windows),
            "gap_count": len(gap_report),
            "gap_report": gap_report,
            "contiguous": not gap_report,
        },
        "execution_readiness": {
            "can_execute_overcover_source_pull": can_execute_overcover,
            "source_pull_needed": not source_files_present,
            "source_files_present": source_files_present,
            "source_pull_task_count": execution_plan["summary"]["task_count"],
            "expected_source_file_count": status_report["summary"]["expected_source_file_count"],
            "present_source_file_count": status_report["summary"]["present_source_file_count"],
            "destination_missing_count": execution_plan["summary"]["destination_missing_count"],
            "download_command": execution_plan["download_command"],
            "allowed_use": [
                "official source acquisition",
                "hash recording",
                "per-window manifest generation",
                "stitched validation preview preparation",
            ],
            "forbidden_use": [
                "final take-out coordinate",
                "cropped production centerline",
                "Unreal full-reach landscape import",
                "named-rapid editor geometry binding",
                "Meat Grinder or Troublemaker solver-window promotion",
            ],
        },
        "promotion_gate": {
            "can_download_source_files": can_execute_overcover,
            "can_promote_full_reach_corridor": False,
            "can_crop_to_final_downstream_anchor": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "next_required_actions": next_required_actions,
        },
    }


def write_south_fork_a1_window_source_pull_preflight(repo_root: Path) -> Path:
    payload = build_south_fork_a1_window_source_pull_preflight(repo_root)
    path = repo_root / FULL_REACH_WINDOW_SOURCE_PULL_PREFLIGHT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
