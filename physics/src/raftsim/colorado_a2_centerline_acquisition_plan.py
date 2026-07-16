"""Plan the Colorado A2 full-reach centerline acquisition.

This records the source, endpoint, CRS, and review gates required before the
Colorado A2 window plan can turn into real source-pull bboxes or promoted rapid
stationing. It intentionally does not download data or promote geometry.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .colorado_a2_full_reach_window_plan import (
    COLORADO_A2_FULL_REACH_WINDOW_PLAN_RELATIVE_PATH,
    COLORADO_RIVER_ID,
    FLOW_PRESETS_RELATIVE_PATH,
    METER_PER_RIVER_MILE,
    NAMED_RAPID_CATALOG_RELATIVE_PATH,
    SOURCE_MANIFEST_RELATIVE_PATH,
)


COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/hydrography/"
    "full_reach_centerline_acquisition_plan.json"
)
COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_SCHEMA = (
    "raftsim.colorado.a2_centerline_acquisition_plan.v1"
)
LEES_FERRY_STATIONING_CANDIDATE_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/hydrography/"
    "nhd_hu8_lees_ferry_mainstem_stationing_candidate.json"
)
FULL_REACH_REVIEW_ENVELOPE_WGS84 = {
    "min_lon": -114.35,
    "min_lat": 35.65,
    "max_lon": -111.45,
    "max_lat": 36.95,
}


def build_colorado_a2_centerline_acquisition_plan(repo_root: Path) -> dict[str, Any]:
    """Build the no-promotion acquisition contract for the full Colorado centerline."""

    repo_root = repo_root.resolve()
    catalog = _load_json(repo_root / NAMED_RAPID_CATALOG_RELATIVE_PATH)
    source_manifest = _load_json(repo_root / SOURCE_MANIFEST_RELATIVE_PATH)
    flow_presets = _load_json(repo_root / FLOW_PRESETS_RELATIVE_PATH)
    window_plan = _load_json(repo_root / COLORADO_A2_FULL_REACH_WINDOW_PLAN_RELATIVE_PATH)
    lees_ferry_stationing = _load_json(repo_root / LEES_FERRY_STATIONING_CANDIDATE_RELATIVE_PATH)
    river = _colorado_catalog_entry(catalog)
    pilot_origin = lees_ferry_stationing["station_samples"][0]
    existing_bounds = source_manifest["bounds_wgs84"]
    run_length_m = float(river["run_length_m"])

    return {
        "schema": COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A2",
        "river_id": COLORADO_RIVER_ID,
        "display_name": river["display_name"],
        "status": "planned_no_source_downloaded_not_centerline_or_crs_authority",
        "production_promoted": False,
        "source_downloads_allowed": False,
        "centerline_binding_allowed": False,
        "source_window_bbox_generation_allowed": False,
        "rapid_stationing_promotion_allowed": False,
        "inputs": {
            "named_rapid_catalog": NAMED_RAPID_CATALOG_RELATIVE_PATH,
            "source_manifest": SOURCE_MANIFEST_RELATIVE_PATH,
            "flow_presets": FLOW_PRESETS_RELATIVE_PATH,
            "window_plan": COLORADO_A2_FULL_REACH_WINDOW_PLAN_RELATIVE_PATH,
            "lees_ferry_stationing_candidate": LEES_FERRY_STATIONING_CANDIDATE_RELATIVE_PATH,
        },
        "current_scope_gap": {
            "existing_source_manifest_bounds_wgs84": existing_bounds,
            "existing_source_manifest_bounds_status": (
                "pilot_and_partial_canyon_bounds_insufficient_for_pearce_ferry_full_run"
            ),
            "existing_editor_binding_max_station_m": float(
                river["editor_geometry_source"]["maximum_bind_station_m"]
            ),
            "planned_run_length_m": run_length_m,
            "planned_run_length_river_miles": round(run_length_m / METER_PER_RIVER_MILE, 3),
            "a2_window_count_waiting_for_bboxes": window_plan["windowing_policy"][
                "window_count"
            ],
        },
        "review_envelope_wgs84": FULL_REACH_REVIEW_ENVELOPE_WGS84,
        "review_envelope_policy": {
            "authority": "source_discovery_and_bbox_planning_only_not_route_geometry",
            "reason": (
                "The envelope intentionally over-covers the full Lees Ferry to "
                "Pearce Ferry planning span so source discovery cannot inherit the "
                "current Lees Ferry pilot bounds."
            ),
            "must_clip_to_reviewed_centerline_before_download": True,
        },
        "endpoint_review_targets": [
            {
                "anchor_id": "lees_ferry_put_in",
                "role": "upstream_start",
                "river_mile": 0.0,
                "current_seed_lon_lat": [pilot_origin["lon"], pilot_origin["lat"]],
                "current_seed_source": LEES_FERRY_STATIONING_CANDIDATE_RELATIVE_PATH,
                "current_seed_status": (
                    "NHD pilot station zero seed requires NPS/access/oarsman review"
                ),
                "promotion_gate": (
                    "Confirm put-in/access geometry and station zero before using "
                    "the seed as full-run coordinate authority."
                ),
            },
            {
                "anchor_id": "pearce_ferry_takeout",
                "role": "downstream_end",
                "river_mile": round(run_length_m / METER_PER_RIVER_MILE, 3),
                "current_seed_lon_lat": None,
                "current_seed_status": "missing_exact_anchor",
                "promotion_gate": (
                    "Attach reviewed Pearce Ferry take-out/access geometry and "
                    "publication sensitivity before clipping the full centerline."
                ),
            },
        ],
        "centerline_source_candidates": _centerline_source_candidates(),
        "working_crs_candidates": _working_crs_candidates(),
        "source_request_prerequisites": [
            "Choose the full-length centerline source family and preserve source feature IDs.",
            "Record exact Lees Ferry and Pearce Ferry anchors with publication review.",
            "Select and test the canyon working CRS or local river-mile transform for distortion.",
            "Generate window bboxes from the reviewed centerline, not from equal-station placeholders.",
            "Cross-check all major rapid miles against NPS/USGS sources and oarsman review before promotion.",
        ],
        "planned_outputs": [
            {
                "artifact": (
                    "physics/data/real_world/colorado_river_grand_canyon_rowing/"
                    "hydrography/full_reach_centerline_candidate.geojson"
                ),
                "status": "not_generated",
                "blocked_by": "centerline_source_selection_and_endpoint_review",
            },
            {
                "artifact": (
                    "physics/data/real_world/colorado_river_grand_canyon_rowing/"
                    "hydrography/full_reach_stationing_candidate.json"
                ),
                "status": "not_generated",
                "blocked_by": "working_crs_and_river_mile_calibration",
            },
            {
                "artifact": (
                    "physics/data/real_world/colorado_river_grand_canyon_rowing/"
                    "production_corridor/full_reach_source_pull_plan.json"
                ),
                "status": "not_generated",
                "blocked_by": "reviewed_centerline_window_bboxes",
            },
            {
                "artifact": (
                    "physics/data/real_world/colorado_river_grand_canyon_rowing/"
                    "review/full_reach_rapid_mile_crosscheck.json"
                ),
                "status": "not_generated",
                "blocked_by": "nps_usgs_hydraulic_maps_and_oarsman_review",
            },
        ],
        "flow_context_status": flow_presets["status"],
        "promotion_gate": {
            "acquisition_contract_recorded": True,
            "full_length_centerline_source_selected": False,
            "lees_ferry_anchor_reviewed": False,
            "pearce_ferry_anchor_reviewed": False,
            "working_crs_selected": False,
            "rapid_mile_crosscheck_complete": False,
            "source_window_bboxes_generated": False,
            "can_download_full_reach_sources": False,
            "can_promote_a2_centerline": False,
        },
    }


def write_colorado_a2_centerline_acquisition_plan(repo_root: Path) -> Path:
    payload = build_colorado_a2_centerline_acquisition_plan(repo_root)
    path = repo_root / COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_RELATIVE_PATH
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


def _bbox_query(bounds: dict[str, float]) -> str:
    return ",".join(
        str(bounds[key])
        for key in ("min_lon", "min_lat", "max_lon", "max_lat")
    )


def _tnm_products_url(dataset: str) -> str:
    return (
        "https://tnmaccess.nationalmap.gov/api/v1/products?"
        f"datasets={quote(dataset)}&bbox={_bbox_query(FULL_REACH_REVIEW_ENVELOPE_WGS84)}"
    )


def _centerline_source_candidates() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "usgs_3dhp_or_nhd_full_reach",
            "source_family": "USGS hydrography",
            "query_url": _tnm_products_url("National Hydrography Dataset (NHD)"),
            "status": "planned_metadata_and_product_selection_required",
            "use_if": "official flowline coverage can be clipped and station-calibrated to reviewed river miles",
            "promotion_caveat": (
                "Hydrography linework alone is not rapid, bank, sandbar, or runnable-line authority."
            ),
        },
        {
            "candidate_id": "nps_or_gcmrc_river_mile_reference",
            "source_family": "NPS/GCMRC river-mile reference",
            "query_url": "link_only_source_selection_required",
            "status": "needed_for_river_mile_calibration",
            "use_if": "station-zero, river-mile ticks, and endpoint policy can be cited and reviewed",
            "promotion_caveat": "Do not vendor maps or guide text without item-level rights.",
        },
        {
            "candidate_id": "usgs_hydraulic_maps_major_rapids",
            "source_family": "USGS hydraulic map series",
            "query_url": "https://pubs.usgs.gov/imap/1897j/",
            "status": "link_only_crosscheck_required",
            "use_if": "major rapid locations/features can be used as cross-check evidence under source terms",
            "promotion_caveat": "Rapid hydraulic maps cross-check rapid windows; they do not replace a full centerline.",
        },
    ]


def _working_crs_candidates() -> list[dict[str, str]]:
    return [
        {
            "crs_id": "EPSG:26912",
            "name": "NAD83 / UTM zone 12N",
            "status": "candidate_needs_full_reach_distortion_and_zone_edge_review",
            "notes": (
                "Covers most of the Grand Canyon working span but must be checked near the "
                "western take-out and against Unreal/world-partition precision needs."
            ),
        },
        {
            "crs_id": "local_river_mile_station_axis",
            "name": "Reviewed river-mile station axis with local cross-stream offsets",
            "status": "candidate_needs_centerline_and_anchor_selection",
            "notes": (
                "Useful for long-corridor authoring and streaming, but source rasters still "
                "need their native CRS and per-window transforms preserved."
            ),
        },
    ]
