"""Record full-reach South Fork flow-window evidence for A1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .south_fork_a1_anchor_review import FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH
from .south_fork_a1_directed_station_candidates import (
    FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH,
    FULL_REACH_DIRECTED_STATION_CANDIDATES_GEOJSON_RELATIVE_PATH,
    FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH,
)
from .south_fork_a1_full_reach_acquisition import FULL_REACH_ACQUISITION_RELATIVE_PATH
from .south_fork_a1_stationing import FLOW_SOURCE_SELECTION_RELATIVE_PATH


FULL_REACH_FLOW_WINDOW_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrology/"
    "full_reach_flow_window_review.json"
)
FLOW_PRESETS_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/flow_presets.json"
)
FLOW_BAND_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrology/"
    "production_import_pilot/flow_band_review.json"
)
SEASONAL_WINDOW_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrology/"
    "production_import_pilot/cdec_seasonal_window_review_wy2026_to_2026-07-06.json"
)
MULTIYEAR_FLOW_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrology/"
    "production_import_pilot/cdec_multiyear_flow_review_2021-10-01_2026-07-06.json"
)


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _threshold_by_band(review: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        threshold["flow_band_hint"]: threshold
        for threshold in review["threshold_review"]
    }


def _band_by_id(flow_presets: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        band["flow_band"]: band
        for band in flow_presets["flow_bands"]
    }


def _reviewed_band_by_id(flow_review: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        band["flow_band"]: band
        for band in flow_review["reviewed_bands"]
    }


def _top_peak_dates(
    threshold: dict[str, Any],
    limit: int = 5,
) -> list[dict[str, Any]]:
    return threshold.get("top_peak_dates", [])[:limit]


def _flow_band_record(
    band_id: str,
    flow_presets: dict[str, Any],
    thirty_day_review: dict[str, Any],
    seasonal_review: dict[str, Any],
    multiyear_review: dict[str, Any],
) -> dict[str, Any]:
    presets = _band_by_id(flow_presets)
    thirty_day_bands = _reviewed_band_by_id(thirty_day_review)
    seasonal_thresholds = _threshold_by_band(seasonal_review)
    multiyear_thresholds = _threshold_by_band(multiyear_review)
    preset = presets[band_id]
    thirty_day = thirty_day_bands[band_id]
    seasonal = seasonal_thresholds[band_id]
    multiyear = multiyear_thresholds[band_id]

    return {
        "flow_band": band_id,
        "planning_discharge_cfs": preset["discharge_cfs"],
        "planning_discharge_m3s": preset["discharge_m3s"],
        "season": preset["season"],
        "planning_notes": preset["notes"],
        "planning_confidence": preset["confidence"],
        "preset_status": "planning_preset_attached_not_promoted",
        "thirty_day_window": {
            "observed_hours_ge_planning_flow": thirty_day[
                "observed_hours_ge_planning_flow"
            ],
            "observed_peak_days_ge_planning_flow": thirty_day[
                "observed_peak_days_ge_planning_flow"
            ],
            "evidence_status": thirty_day["evidence_status"],
            "promotion_decision": thirty_day["promotion_decision"],
        },
        "water_year_2026_to_date": {
            "threshold_cfs": seasonal["threshold_cfs"],
            "days_peak_ge_threshold": seasonal["days_peak_ge_threshold"],
            "days_median_ge_threshold": seasonal["days_median_ge_threshold"],
            "total_hours_ge_threshold": seasonal["total_hours_ge_threshold"],
            "promotion_decision": seasonal["promotion_decision"],
            "top_peak_dates": _top_peak_dates(seasonal),
        },
        "multiyear_context": {
            "threshold_cfs": multiyear["threshold_cfs"],
            "days_peak_ge_threshold": multiyear["days_peak_ge_threshold"],
            "days_median_ge_threshold": multiyear["days_median_ge_threshold"],
            "total_hours_ge_threshold": multiyear["total_hours_ge_threshold"],
            "complete_water_year_peak_day_counts": multiyear[
                "complete_water_year_peak_day_counts"
            ],
            "promotion_decision": multiyear["promotion_decision"],
            "top_peak_dates": _top_peak_dates(multiyear),
        },
        "full_reach_decision": (
            "attached_for_full_reach_review_but_not_accepted_for_gameplay_or_visual_tuning"
        ),
        "why_not_promoted": [
            "CBR/A25 evidence is station context, not rapid-scale hydraulic validation.",
            "A25 release-routing and flagged samples still need interpretation.",
            "Guide/outfitter validation and legal/redistribution signoff remain open.",
            "C++ water parity and conservation gates still control live rapid approval.",
        ],
    }


def build_south_fork_a1_full_reach_flow_window_review(
    repo_root: Path,
) -> dict[str, Any]:
    """Build the machine-readable full-reach flow-window review for A1."""

    repo_root = repo_root.resolve()
    flow_presets = _load_json(repo_root, FLOW_PRESETS_RELATIVE_PATH)
    thirty_day_review = _load_json(repo_root, FLOW_BAND_REVIEW_RELATIVE_PATH)
    source_selection = _load_json(repo_root, FLOW_SOURCE_SELECTION_RELATIVE_PATH)
    seasonal_review = _load_json(repo_root, SEASONAL_WINDOW_REVIEW_RELATIVE_PATH)
    multiyear_review = _load_json(repo_root, MULTIYEAR_FLOW_REVIEW_RELATIVE_PATH)
    station_candidates = _load_json(
        repo_root,
        FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH,
    )
    route_clips = _load_json(
        repo_root,
        FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH,
    )
    flow_band_ids = [band["flow_band"] for band in flow_presets["flow_bands"]]

    return {
        "schema": "raftsim.south_fork.a1_full_reach_flow_window_review.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": "south_fork_american_chili_bar",
        "status": "full_reach_flow_windows_attached_review_gated_not_promoted",
        "production_promoted": False,
        "inputs": {
            "full_reach_acquisition_plan": FULL_REACH_ACQUISITION_RELATIVE_PATH,
            "anchor_review": FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH,
            "station_candidates": FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH,
            "station_candidates_geojson": (
                FULL_REACH_DIRECTED_STATION_CANDIDATES_GEOJSON_RELATIVE_PATH
            ),
            "route_clip_candidates": (
                FULL_REACH_DIRECTED_ROUTE_CLIPS_GEOJSON_RELATIVE_PATH
            ),
            "flow_presets": FLOW_PRESETS_RELATIVE_PATH,
            "flow_band_review_30_day": FLOW_BAND_REVIEW_RELATIVE_PATH,
            "seasonal_window_review": SEASONAL_WINDOW_REVIEW_RELATIVE_PATH,
            "multiyear_flow_review": MULTIYEAR_FLOW_REVIEW_RELATIVE_PATH,
            "flow_source_selection": FLOW_SOURCE_SELECTION_RELATIVE_PATH,
        },
        "full_reach_scope": {
            "route_candidates_status": route_clips["status"],
            "route_candidate_count": route_clips["feature_count"],
            "station_candidates_status": station_candidates["status"],
            "named_rapid_candidate_count": len(
                station_candidates["named_rapid_station_candidates"]
            ),
            "flow_applies_to": (
                "Chili Bar-to-Salmon Falls/Folsom review candidates as station "
                "context only; exact reach hydraulics still require solver, bed, "
                "and guide review."
            ),
            "can_promote_full_reach_flow_bands": False,
        },
        "official_source_selection": {
            "primary_station_id": "CBR",
            "primary_station_name": "AMERICAN RIVER AT CHILI BAR",
            "primary_source_status": source_selection["status"],
            "secondary_station_id": "A25",
            "secondary_station_role": (
                "powerhouse release-operation context only until routing is reviewed"
            ),
            "usgs_screening": source_selection["usgs_screening"],
            "required_before_flow_band_promotion": source_selection[
                "required_before_flow_band_promotion"
            ],
        },
        "evidence_windows": {
            "thirty_day_context": {
                "path": FLOW_BAND_REVIEW_RELATIVE_PATH,
                "status": thirty_day_review["status"],
                "summary": thirty_day_review["cdec_window_summary"],
                "promotion_blockers": thirty_day_review["promotion_blockers"],
            },
            "water_year_2026_to_date": {
                "path": SEASONAL_WINDOW_REVIEW_RELATIVE_PATH,
                "status": seasonal_review["status"],
                "request_window": seasonal_review["request_window"],
                "summary": seasonal_review["water_year_summary"],
                "series": seasonal_review["series"],
                "promotion_blockers": seasonal_review["promotion_blockers"],
            },
            "multiyear_context": {
                "path": MULTIYEAR_FLOW_REVIEW_RELATIVE_PATH,
                "status": multiyear_review["status"],
                "request_window": multiyear_review["request_window"],
                "summary": multiyear_review["requested_window_summary"],
                "series": multiyear_review["series"],
                "high_flow_outlier_review": multiyear_review[
                    "high_flow_outlier_review"
                ],
                "promotion_blockers": multiyear_review["promotion_blockers"],
            },
        },
        "reviewed_flow_bands": [
            _flow_band_record(
                band_id,
                flow_presets,
                thirty_day_review,
                seasonal_review,
                multiyear_review,
            )
            for band_id in flow_band_ids
        ],
        "flow_dependent_feature_tuning_policy": {
            "feature_forcing_allowed_now": False,
            "feature_forcing_default_scale": 0.0,
            "may_use_for_planning": [
                "holes and wave trains that appear/disappear by flow band",
                "wet-bank and exposed-rock visual review",
                "boulder push/damping hypotheses",
                "guide discussion of sticky/washout flow windows",
            ],
            "forbidden_use": [
                "solver retuning",
                "hiding conservation failures",
                "claiming lifelike water visuals",
                "approving live named-rapid water windows",
            ],
            "promotion_dependency": (
                "Only promote after exact anchors, guide review, C++/GeoClaw parity, "
                "and conservation gates agree for the rapid windows."
            ),
        },
        "promotion_gate": {
            "can_promote_flow_bands": False,
            "can_bind_unreal_flow_variants": False,
            "can_approve_named_rapid_water_windows": False,
            "can_enable_feature_forcing_for_review_runs": False,
            "exit_criteria": [
                "Resolve A25 flag/routing and station-to-rapid timing.",
                "Record guide/outfitter validation for low/reference/high bands.",
                "Resolve exact downstream anchor and full-reach corridor windows.",
                "Pass live C++ water parity/conservation gates for rapid windows.",
                "Record legal/redistribution signoff for CDEC-derived artifacts.",
            ],
        },
    }


def write_south_fork_a1_full_reach_flow_window_review(repo_root: Path) -> Path:
    payload = build_south_fork_a1_full_reach_flow_window_review(repo_root)
    path = repo_root / FULL_REACH_FLOW_WINDOW_REVIEW_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
