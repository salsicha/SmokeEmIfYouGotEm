"""Preflight review for South Fork A1 full-reach source downloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .south_fork_a1_anchor_review import FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH
from .south_fork_a1_corridor_windows import (
    FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH,
)
from .south_fork_a1_stationing import (
    FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
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
    """Review planned source downloads against the adopted downstream anchor."""

    repo_root = repo_root.resolve()
    anchor_review = _load_json(repo_root, FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH)
    adopted = _load_json(repo_root, FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH)
    window_manifest = _load_json(repo_root, FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH)
    execution_plan = _load_json(repo_root, FULL_REACH_WINDOW_SOURCE_PULL_EXECUTION_PLAN_RELATIVE_PATH)
    status_report = _load_json(repo_root, FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH)
    downstream = _downstream_anchor(anchor_review)
    source_window = downstream["source_mile_window"]
    adopted_anchor = adopted["downstream_anchor"]
    adopted_station_m = float(adopted_anchor["station_m"])
    windows = window_manifest["windows"]
    final_window = windows[-1]
    gap_report = _window_gap_report(windows)
    planned_end_m = float(window_manifest["coverage_summary"]["planned_station_end_m"])
    final_window_ends_at_adopted_anchor = (
        abs(float(final_window["station_end_m"]) - adopted_station_m)
        <= _STATION_TOLERANCE_M
    )
    expected_task_count = 2 * len(windows)
    can_execute_full_axis_pull = (
        adopted["status"] == "adopted_official_access_anchor_route_stationing_active"
        and adopted["promotion_gate"]["can_plan_corridor_windows_against_adopted_axis"] is True
        and final_window_ends_at_adopted_anchor
        and not gap_report
        and execution_plan["summary"]["task_count"] == expected_task_count
        and status_report["summary"]["expected_source_file_count"] == expected_task_count
    )
    source_files_present = status_report["summary"]["all_source_files_present"]
    window_manifests_present = status_report["summary"]["all_window_manifests_present"]
    if not can_execute_full_axis_pull:
        status = "source_pull_preflight_blocked"
    elif source_files_present and window_manifests_present:
        status = "adopted_axis_source_manifests_ready_for_stitched_validation"
    elif source_files_present:
        status = "adopted_axis_source_files_present_window_manifests_pending"
    else:
        status = "adopted_axis_full_reach_source_pull_preflight_passed"
    if source_files_present and window_manifests_present:
        next_required_actions = [
            "Produce stitched seam-validation previews before Unreal import.",
            "Attach bank/cross-section interpretation and guide/geospatial review.",
            "Confirm the adopted Salmon Falls take-out bank landing via the P7 owner packet before any cropping, Unreal import, or rapid binding.",
        ]
    elif source_files_present:
        next_required_actions = [
            "Generate per-window manifests plus source terms, CRS, resolution, bounds, and derivative targets.",
            "Produce stitched seam-validation previews before Unreal import.",
            "Confirm the adopted Salmon Falls take-out bank landing via the P7 owner packet before any cropping, Unreal import, or rapid binding.",
        ]
    else:
        next_required_actions = [
            "Run the bounded source-pull executor for the official DEM/NAIP URLs.",
            f"Regenerate the source-pull status report and verify all {expected_task_count} source files have byte counts and SHA-256 hashes.",
            "Generate per-window manifests plus stitched seam-validation previews.",
            "Confirm the adopted Salmon Falls take-out bank landing via the P7 owner packet before any cropping, Unreal import, or rapid binding.",
        ]

    return {
        "schema": "raftsim.south_fork.a1_window_source_pull_preflight_review.v2",
        "generated_on": "2026-07-17",
        "task_id": "A1",
        "river_id": window_manifest["river_id"],
        "status": status,
        "production_promoted": False,
        "inputs": {
            "anchor_review": FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH,
            "adopted_route_stationing": FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
            "corridor_window_manifest": FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH,
            "source_pull_execution_plan": FULL_REACH_WINDOW_SOURCE_PULL_EXECUTION_PLAN_RELATIVE_PATH,
            "source_pull_status": FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
        },
        "downstream_anchor_review": {
            "anchor_status": adopted_anchor["anchor_status"],
            "anchor_name": adopted_anchor["name"],
            "anchor_authority": adopted_anchor["authority"],
            "anchor_lon_lat": adopted_anchor["lon_lat"],
            "adopted_station_m": adopted_station_m,
            "snap_distance_m": adopted_anchor["snap_distance_m"],
            "pending_human_review": adopted_anchor["pending_human_review"],
            "planned_station_end_m": planned_end_m,
            "final_window_id": final_window["window_id"],
            "final_window_start_m": final_window["station_start_m"],
            "final_window_end_m": final_window["station_end_m"],
            "final_window_ends_at_adopted_anchor": final_window_ends_at_adopted_anchor,
            "superseded_source_mile_window": {
                "source_mile_window": source_window,
                "historical_review_window_id": "salmon_falls_folsom_review_32991_33796m",
                "disposition": (
                    "The 20.5-21.0 mile published-mile ambiguity window remains "
                    "committed as discrepancy evidence; the release-1.0-plan "
                    "section 6 adoption resolved the downstream anchor to the "
                    "official Salmon Falls take-out access geometry."
                ),
            },
            "interpretation": (
                "The corridor windows now extend along the adopted NHD directed "
                "mainstem axis to the official Salmon Falls take-out anchor at "
                f"{adopted_station_m} m. Source acquisition covers the full "
                "adopted axis; corridor cropping, editor binding, and "
                "solver-window promotion remain P3/P4 work with the bank-landing "
                "refinement batched to the P7 owner packet."
            ),
        },
        "window_continuity": {
            "window_count": len(windows),
            "gap_count": len(gap_report),
            "gap_report": gap_report,
            "contiguous": not gap_report,
        },
        "execution_readiness": {
            "can_execute_full_axis_source_pull": can_execute_full_axis_pull,
            "source_pull_needed": not source_files_present,
            "source_files_present": source_files_present,
            "window_manifests_present": window_manifests_present,
            "can_enter_stitched_validation_review": status_report["promotion_gate"][
                "can_enter_stitched_validation_review"
            ],
            "source_pull_task_count": execution_plan["summary"]["task_count"],
            "expected_source_file_count": status_report["summary"]["expected_source_file_count"],
            "present_source_file_count": status_report["summary"]["present_source_file_count"],
            "present_window_manifest_count": status_report["summary"][
                "present_window_manifest_count"
            ],
            "destination_missing_count": execution_plan["summary"]["destination_missing_count"],
            "download_command": execution_plan["download_command"],
            "allowed_use": [
                "official source acquisition",
                "hash recording",
                "per-window manifest generation",
                "stitched validation preview preparation",
            ],
            "forbidden_use": [
                "bank-landing confirmation authority",
                "cropped production centerline",
                "Unreal full-reach landscape import",
                "named-rapid editor geometry binding",
                "Meat Grinder or Troublemaker solver-window promotion",
            ],
        },
        "promotion_gate": {
            "can_download_source_files": can_execute_full_axis_pull,
            "can_promote_full_reach_corridor": False,
            "can_crop_to_final_downstream_anchor": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "authority_note": (
                "This preflight authorizes bounded source downloads only. Crop "
                "and solver-window binding authority is governed by the adopted "
                "route stationing artifact and executes inside P3/P4."
            ),
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
