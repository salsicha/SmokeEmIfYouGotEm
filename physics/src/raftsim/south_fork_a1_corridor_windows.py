"""Plan South Fork A1 full-reach corridor windows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .south_fork_a1_anchor_review import FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH
from .south_fork_a1_directed_station_candidates import (
    FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH,
    FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH,
)
from .south_fork_a1_flow_window_review import FULL_REACH_FLOW_WINDOW_REVIEW_RELATIVE_PATH
from .south_fork_a1_full_reach_acquisition import FULL_REACH_ACQUISITION_RELATIVE_PATH
from .south_fork_a1_stationing import (
    FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
    PRODUCTION_CORRIDOR_MANIFEST_RELATIVE_PATH,
)


FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_window_manifest.json"
)

WINDOW_SPECS = [
    {
        "window_id": "chili_bar_existing_pilot_0_2500m",
        "display_name": "Chili Bar Existing Pilot",
        "station_start_m": 0.0,
        "station_end_m": 2500.0,
        "status": "existing_source_attached_pilot_review_gated",
        "existing_artifact": PRODUCTION_CORRIDOR_MANIFEST_RELATIVE_PATH,
    },
    {
        "window_id": "upper_chili_bar_to_coloma_2500_10000m",
        "display_name": "Upper Chili Bar To Coloma Checkpoint",
        "station_start_m": 2500.0,
        "station_end_m": 10000.0,
        "status": "planned_source_pull_required",
    },
    {
        "window_id": "coloma_valley_10000_24000m",
        "display_name": "Coloma Valley Transit",
        "station_start_m": 10000.0,
        "station_end_m": 24000.0,
        "status": "planned_source_pull_required",
    },
    {
        "window_id": "upper_gorge_24000_28500m",
        "display_name": "Upper Gorge Rapid Windows",
        "station_start_m": 24000.0,
        "station_end_m": 28500.0,
        "status": "planned_source_pull_required",
    },
    {
        "window_id": "lower_gorge_to_salmon_falls_28500_32991m",
        "display_name": "Lower Gorge To Salmon Falls Source Window",
        "station_start_m": 28500.0,
        "station_end_m": 32991.552,
        "status": "planned_source_pull_required",
    },
    {
        "window_id": "salmon_falls_folsom_review_32991_33796m",
        "display_name": "Salmon Falls/Folsom Downstream Anchor Review",
        "station_start_m": 32991.552,
        "station_end_m": 33796.224,
        "status": "planned_anchor_resolution_window",
        "downstream_anchor_note": (
            "Window exists to resolve the 20.5-21.0 mile Salmon Falls/Folsom "
            "take-out source basis."
        ),
    },
    {
        "window_id": "below_full_run_alias_33796_41500m",
        "display_name": "Below Published Full-Run Alias Transit",
        "station_start_m": 33796.224,
        "station_end_m": 41500.0,
        "status": "planned_source_pull_required",
        "downstream_anchor_note": (
            "Adopted-axis extension window: the official Salmon Falls take-out "
            "anchor sits at 49077.732 m, beyond the published 21.0-mile "
            "full-run alias; this span follows the adopted NHD directed "
            "mainstem axis."
        ),
    },
    {
        "window_id": "salmon_falls_takeout_approach_41500_49077m",
        "display_name": "Salmon Falls Take-out Approach",
        "station_start_m": 41500.0,
        "station_end_m": 49077.732,
        "status": "planned_source_pull_required",
        "downstream_anchor_note": (
            "Ends at the adopted official Salmon Falls take-out anchor "
            "(station 49077.732 m); the bank-landing refinement rides the P7 "
            "owner packet and does not block source acquisition."
        ),
    },
]


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _window_for_station(station_m: float) -> dict[str, Any]:
    for window in WINDOW_SPECS:
        if window["station_start_m"] <= station_m <= window["station_end_m"]:
            return window
    raise ValueError(f"Station {station_m} is outside the planned corridor windows")


def _rapid_assignments(candidates: dict[str, Any]) -> list[dict[str, Any]]:
    assignments: list[dict[str, Any]] = []
    for rapid in candidates["named_rapid_station_candidates"]:
        window = _window_for_station(float(rapid["station_m"]))
        assignments.append(
            {
                "name": rapid["name"],
                "order": rapid["order"],
                "published_river_mile": rapid["published_river_mile"],
                "candidate_station_m": rapid["station_m"],
                "candidate_lon_lat": rapid["lon_lat"],
                "window_id": window["window_id"],
                "review_priority": rapid["review_priority"],
                "can_bind_editor_geometry": False,
                "can_bind_solver_window": False,
            }
        )
    return assignments


def _window_records(
    candidates: dict[str, Any],
    existing_corridor: dict[str, Any],
) -> list[dict[str, Any]]:
    rapids = _rapid_assignments(candidates)
    records: list[dict[str, Any]] = []
    for spec in WINDOW_SPECS:
        rapid_names = [
            rapid["name"]
            for rapid in rapids
            if rapid["window_id"] == spec["window_id"]
        ]
        record = {
            **spec,
            "length_m": round(spec["station_end_m"] - spec["station_start_m"], 6),
            "rapid_names": rapid_names,
            "rapid_count": len(rapid_names),
            "required_source_classes": [
                "3DEP terrain",
                "NAIP/aerial imagery",
                "directed centerline clip",
                "bank/cross-section interpretation",
                "guide/geospatial review notes",
            ],
            "production_promoted": False,
            "can_build_unreal_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
        }
        if spec["window_id"] == "chili_bar_existing_pilot_0_2500m":
            record["existing_corridor_status"] = existing_corridor["status"]
            record["existing_reach_id"] = existing_corridor["reach_id"]
            record["existing_artifact"] = PRODUCTION_CORRIDOR_MANIFEST_RELATIVE_PATH
            record["coverage_gap"] = (
                "Existing pilot source package covers only the first 2.5 km and "
                "must be stitched into the full-reach window set."
            )
        else:
            record["source_pull_status"] = "not_started"
        records.append(record)
    return records


def build_south_fork_a1_full_reach_corridor_window_manifest(
    repo_root: Path,
) -> dict[str, Any]:
    """Build the review-gated full-reach corridor window manifest."""

    repo_root = repo_root.resolve()
    candidates = _load_json(repo_root, FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH)
    route_clips = _load_json(repo_root, FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH)
    existing_corridor = _load_json(repo_root, PRODUCTION_CORRIDOR_MANIFEST_RELATIVE_PATH)
    adopted_stationing = _load_json(
        repo_root, FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH
    )
    adopted_axis_end_m = float(
        adopted_stationing["station_axis"]["adopted_route_length_m"]
    )
    rapids = _rapid_assignments(candidates)
    windows = _window_records(candidates, existing_corridor)

    return {
        "schema": "raftsim.south_fork.a1_full_reach_corridor_window_manifest.v1",
        "generated_on": "2026-07-17",
        "task_id": "A1",
        "river_id": candidates["river_id"],
        "status": "planned_full_reach_windows_review_gated_not_source_complete",
        "production_promoted": False,
        "inputs": {
            "full_reach_acquisition_plan": FULL_REACH_ACQUISITION_RELATIVE_PATH,
            "anchor_review": FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH,
            "directed_station_candidates": (
                FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH
            ),
            "directed_route_clips": FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH,
            "full_reach_flow_window_review": FULL_REACH_FLOW_WINDOW_REVIEW_RELATIVE_PATH,
            "existing_pilot_corridor": PRODUCTION_CORRIDOR_MANIFEST_RELATIVE_PATH,
            "adopted_route_stationing": (
                FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH
            ),
        },
        "route_clip_status": route_clips["status"],
        "route_clip_candidate_count": route_clips["feature_count"],
        "windowing_policy": {
            "authority": "planning_manifest_only_not_terrain_or_gameplay_geometry",
            "reason": (
                "A1 needs full Chili Bar-to-Salmon Falls corridor coverage along "
                "the adopted official-access axis. Windows through the published "
                "21.0-mile alias keep their reviewed directed-clip spans; the "
                "adopted-axis extension windows make the remaining source-pull "
                "work explicit without promoting candidate linework."
            ),
            "max_planned_window_length_m": max(window["length_m"] for window in windows),
            "requires_stitched_validation_outputs": True,
        },
        "windows": windows,
        "rapid_window_assignments": rapids,
        "coverage_summary": {
            "window_count": len(windows),
            "planned_station_start_m": windows[0]["station_start_m"],
            "planned_station_end_m": windows[-1]["station_end_m"],
            "planned_length_m": round(
                windows[-1]["station_end_m"] - windows[0]["station_start_m"],
                6,
            ),
            "adopted_axis_end_station_m": adopted_axis_end_m,
            "covers_adopted_axis": abs(
                windows[-1]["station_end_m"] - adopted_axis_end_m
            )
            <= 1e-6,
            "existing_source_attached_length_m": 2500.0,
            "remaining_source_pull_length_m": round(windows[-1]["station_end_m"] - 2500.0, 6),
            "named_rapid_count": len(rapids),
            "named_rapids_assigned_to_windows": len(rapids),
            "all_named_rapids_assigned": len(rapids)
            == len(candidates["named_rapid_station_candidates"]),
        },
        "promotion_gate": {
            "can_promote_full_reach_corridor": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_south_fork_named_rapid_geometry": False,
            "can_bind_meat_grinder_troublemaker_solver_windows": False,
            "exit_criteria": [
                "Anchors adopted per release-1.0-plan section 6; the Salmon Falls bank-landing refinement rides the P7 owner packet.",
                "Pull and hash-lock terrain and imagery for every planned window.",
                "Generate stitched whole-window validation outputs across seams.",
                "Review bank/cross-section interpretation with guide/geospatial evidence.",
                "Regenerate named-rapid editor geometry only after stationing review passes.",
            ],
        },
    }


def write_south_fork_a1_full_reach_corridor_window_manifest(repo_root: Path) -> Path:
    payload = build_south_fork_a1_full_reach_corridor_window_manifest(repo_root)
    path = repo_root / FULL_REACH_CORRIDOR_WINDOW_MANIFEST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
