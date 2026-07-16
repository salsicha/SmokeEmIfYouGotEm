"""Build the Colorado A2 full-reach window planning packet."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


COLORADO_A2_FULL_REACH_WINDOW_PLAN_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/"
    "full_reach_window_plan.json"
)
COLORADO_A2_FULL_REACH_WINDOW_PLAN_SCHEMA = (
    "raftsim.colorado.a2_full_reach_window_plan.v1"
)
COLORADO_RIVER_ID = "colorado_river_grand_canyon_rowing"
NAMED_RAPID_CATALOG_RELATIVE_PATH = "physics/data/real_world/named_rapid_source_catalog.json"
SOURCE_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/source_manifest.json"
)
FLOW_PRESETS_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/flow_presets.json"
)
EXISTING_PILOT_CORRIDOR_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/"
    "lees_ferry_reach_2200_4700m/manifest.json"
)
METER_PER_RIVER_MILE = 1609.344
FULL_REACH_WINDOW_COUNT = 23
MIN_A2_WINDOW_LENGTH_M = 10_000.0
MAX_A2_WINDOW_LENGTH_M = 20_000.0


def build_colorado_a2_full_reach_window_plan(repo_root: Path) -> dict[str, Any]:
    """Build a fail-closed A2 source-window plan for the full Grand Canyon run."""

    repo_root = repo_root.resolve()
    catalog = _load_json(repo_root / NAMED_RAPID_CATALOG_RELATIVE_PATH)
    source_manifest = _load_json(repo_root / SOURCE_MANIFEST_RELATIVE_PATH)
    flow_presets = _load_json(repo_root / FLOW_PRESETS_RELATIVE_PATH)
    catalog_entry = _colorado_catalog_entry(catalog)

    run_length_m = float(catalog_entry["run_length_m"])
    windows = _build_source_windows(run_length_m)
    rapid_assignments = _assign_rapids_to_windows(catalog_entry["rapids"], windows)
    windows_by_id = {window["window_id"]: window for window in windows}
    for assignment in rapid_assignments:
        windows_by_id[assignment["assigned_window_id"]]["rapid_names"].append(
            assignment["name"]
        )
    for window in windows:
        window["rapid_count"] = len(window["rapid_names"])
        if window["rapid_count"]:
            window["review_priority"] = _window_priority(rapid_assignments, window["window_id"])

    critical_rapid_names = sorted(
        assignment["name"]
        for assignment in rapid_assignments
        if assignment["review_priority"] == "critical"
    )

    return {
        "schema": COLORADO_A2_FULL_REACH_WINDOW_PLAN_SCHEMA,
        "generated_on": "2026-07-16",
        "river_id": COLORADO_RIVER_ID,
        "display_name": catalog_entry["display_name"],
        "status": "a2_full_reach_window_plan_recorded_no_source_download_no_promotion",
        "production_promoted": False,
        "full_reach_source_pull_ready": False,
        "unreal_import_allowed": False,
        "rapid_stationing_promotion_allowed": False,
        "solver_window_binding_allowed": False,
        "source_contracts": {
            "named_rapid_catalog": NAMED_RAPID_CATALOG_RELATIVE_PATH,
            "source_manifest": SOURCE_MANIFEST_RELATIVE_PATH,
            "flow_presets": FLOW_PRESETS_RELATIVE_PATH,
            "existing_lees_ferry_pilot": EXISTING_PILOT_CORRIDOR_RELATIVE_PATH,
        },
        "source_manifest_status": source_manifest["provenance"]["review_status"],
        "flow_band_status": flow_presets["status"],
        "stationing_authority": catalog_entry["stationing_authority"],
        "run_length_m": run_length_m,
        "run_length_river_miles": round(run_length_m / METER_PER_RIVER_MILE, 3),
        "windowing_policy": {
            "window_count": FULL_REACH_WINDOW_COUNT,
            "window_length_policy": (
                "equal_station_windows_across_catalog_run_length_until_full_centerline_"
                "and_canyon_crs_are_selected"
            ),
            "target_window_length_m": round(run_length_m / FULL_REACH_WINDOW_COUNT, 3),
            "minimum_allowed_length_m": MIN_A2_WINDOW_LENGTH_M,
            "maximum_allowed_length_m": MAX_A2_WINDOW_LENGTH_M,
            "rapid_assignment_basis": (
                "published river-mile station converted to meters; every assignment "
                "requires NPS/USGS/oarsman/geospatial review before promotion"
            ),
        },
        "full_reach_source_requirements": _source_requirements(),
        "source_windows": windows,
        "rapid_assignments": rapid_assignments,
        "rapid_assignment_summary": {
            "rapid_count": len(rapid_assignments),
            "critical_rapid_count": len(critical_rapid_names),
            "critical_rapid_names": critical_rapid_names,
            "all_rapids_have_window": all(
                assignment["assigned_window_id"] in windows_by_id
                for assignment in rapid_assignments
            ),
            "all_rapids_blocked_from_promotion": all(
                not assignment["exact_stationing_promoted"]
                and not assignment["editor_binding_enabled"]
                and not assignment["solver_window_enabled"]
                for assignment in rapid_assignments
            ),
        },
        "promotion_gate": {
            "a2_window_plan_recorded": True,
            "full_length_centerline_selected": False,
            "exact_put_in_take_out_anchors_reviewed": False,
            "nps_usgs_rapid_miles_crosschecked": False,
            "full_reach_source_pull_urls_generated": False,
            "full_reach_sources_downloaded_and_hashed": False,
            "per_window_manifests_generated": False,
            "stitched_validation_exported": False,
            "oarsman_geospatial_rights_review_complete": False,
            "can_promote_a2": False,
            "blocking_reasons": [
                "The current official-source pilot covers only a Lees Ferry slice, not the full Lees Ferry to Pearce Ferry run.",
                "The planning axis still uses published river miles until a full-length centerline and canyon working CRS are selected.",
                "Major rapid miles still need NPS/USGS hydraulic-map and oarsman/geospatial cross-checks.",
                "No full-reach per-window DEM/imagery source URLs, hashes, stitched validation outputs, or review manifests exist yet.",
            ],
            "next_required_actions": [
                "Select or build the full-length Colorado River centerline and canyon working CRS.",
                "Generate per-window USGS 3DEP/NAIP source-pull requests from reviewed window bboxes.",
                "Cross-check each major rapid mile against NPS, USGS hydraulic maps, and oarsman review evidence.",
                "Generate hash-locked per-window source manifests and stitched validation reports before Unreal import.",
            ],
        },
    }


def write_colorado_a2_full_reach_window_plan(repo_root: Path) -> Path:
    payload = build_colorado_a2_full_reach_window_plan(repo_root)
    path = repo_root / COLORADO_A2_FULL_REACH_WINDOW_PLAN_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _colorado_catalog_entry(catalog: dict[str, Any]) -> dict[str, Any]:
    for river in catalog["rivers"]:
        if river["river_id"] == COLORADO_RIVER_ID:
            return river
    raise RuntimeError(f"Missing {COLORADO_RIVER_ID} in named rapid catalog")


def _build_source_windows(run_length_m: float) -> list[dict[str, Any]]:
    window_length_m = run_length_m / FULL_REACH_WINDOW_COUNT
    if not MIN_A2_WINDOW_LENGTH_M <= window_length_m <= MAX_A2_WINDOW_LENGTH_M:
        raise RuntimeError("Colorado A2 window length falls outside the 10-20 km plan")

    windows: list[dict[str, Any]] = []
    for index in range(FULL_REACH_WINDOW_COUNT):
        station_start_m = index * window_length_m
        station_end_m = run_length_m if index == FULL_REACH_WINDOW_COUNT - 1 else (
            index + 1
        ) * window_length_m
        river_mile_start = station_start_m / METER_PER_RIVER_MILE
        river_mile_end = station_end_m / METER_PER_RIVER_MILE
        windows.append(
            {
                "window_id": f"colorado_a2_window_{index + 1:02d}",
                "order": index + 1,
                "station_start_m": round(station_start_m, 3),
                "station_end_m": round(station_end_m, 3),
                "river_mile_start": round(river_mile_start, 3),
                "river_mile_end": round(river_mile_end, 3),
                "window_length_m": round(station_end_m - station_start_m, 3),
                "source_bbox_status": "pending_full_centerline_and_canyon_working_crs",
                "terrain_source_plan": "USGS 3DEP 10 m or better, with lidar slots where available",
                "imagery_source_plan": "USDA NAIP plus rights-reviewed canyon reference imagery",
                "hydrography_source_plan": "NHD/USGS mainstem centerline cross-checked to river miles",
                "existing_pilot_overlap": index == 0,
                "rapid_names": [],
                "rapid_count": 0,
                "review_priority": "setup",
                "promotion_status": "blocked_pending_source_pull_window_bbox_and_review",
            }
        )
    return windows


def _assign_rapids_to_windows(
    rapids: list[dict[str, Any]], windows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    assignments = []
    for rapid in rapids:
        station_m = float(rapid["river_mile"]) * METER_PER_RIVER_MILE
        window = _window_for_station(station_m, windows)
        assignments.append(
            {
                "name": rapid["name"],
                "aliases": rapid.get("aliases", []),
                "class": rapid["class"],
                "review_priority": rapid["review_priority"],
                "feature_tags": rapid["feature_tags"],
                "published_river_mile": float(rapid["river_mile"]),
                "planning_station_m": round(station_m, 3),
                "assigned_window_id": window["window_id"],
                "stationing_status": (
                    "published_mile_only_pending_nps_usgs_hydraulic_map_"
                    "and_oarsman_geospatial_crosscheck"
                ),
                "exact_stationing_promoted": False,
                "editor_binding_enabled": False,
                "solver_window_enabled": False,
                "required_reviews_before_promotion": [
                    "NPS or USGS river-mile cross-check",
                    "USGS hydraulic-map or equivalent geospatial rapid evidence",
                    "oarsman or guide line/feature review",
                    "rights/publication review before exposing exact public screenshots",
                    "stitched source-window terrain/imagery validation",
                ],
            }
        )
    return assignments


def _window_for_station(station_m: float, windows: list[dict[str, Any]]) -> dict[str, Any]:
    for window in windows:
        if window["station_start_m"] <= station_m < window["station_end_m"]:
            return window
    if math.isclose(station_m, windows[-1]["station_end_m"]):
        return windows[-1]
    raise RuntimeError(f"No Colorado A2 window contains station {station_m}")


def _window_priority(assignments: list[dict[str, Any]], window_id: str) -> str:
    priorities = {
        assignment["review_priority"]
        for assignment in assignments
        if assignment["assigned_window_id"] == window_id
    }
    if "critical" in priorities:
        return "critical"
    if "high" in priorities:
        return "high"
    if "medium" in priorities:
        return "medium"
    return "setup"


def _source_requirements() -> list[dict[str, str]]:
    return [
        {
            "requirement_id": "full_length_centerline",
            "source_family": "NHD/USGS/NPS/GCMRC",
            "status": "missing_full_reach_authority",
            "required_before": "window_bbox_generation",
        },
        {
            "requirement_id": "terrain_dem",
            "source_family": "USGS 3DEP",
            "status": "planned_not_downloaded",
            "required_before": "per_window_manifest_generation",
        },
        {
            "requirement_id": "aerial_imagery",
            "source_family": "USDA NAIP",
            "status": "planned_not_downloaded",
            "required_before": "per_window_manifest_generation",
        },
        {
            "requirement_id": "major_rapid_hydraulic_maps",
            "source_family": "USGS hydraulic maps plus NPS/oarsman review",
            "status": "link_only_crosscheck_required",
            "required_before": "rapid_stationing_promotion",
        },
        {
            "requirement_id": "release_flow_context",
            "source_family": "USGS 09380000/09402500 and USBR Glen Canyon releases",
            "status": "pilot_data_exists_full_reach_review_required",
            "required_before": "flow_variant_promotion",
        },
    ]
