"""Plan the South Fork A1 full-reach source acquisition.

This module does not download source data. It records the exact review envelope,
source classes, route-selection gates, and output artifacts needed before the
South Fork centerline can be promoted beyond the current pilot slice.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .named_rapid_registry import MILES_TO_METERS, SOURCE_CATALOG_RELATIVE_PATH
from .south_fork_a1_stationing import (
    A1_STATUS_RELATIVE_PATH,
    ALIGNMENT_REVIEW_RELATIVE_PATH,
)


FULL_REACH_ACQUISITION_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/hydrography/"
    "full_reach_acquisition_plan.json"
)
ACCESS_POINTS_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "production_import_pilot/access_points.geojson"
)

FULL_REACH_REVIEW_ENVELOPE_WGS84 = {
    "min_lon": -121.12,
    "min_lat": 38.68,
    "max_lon": -120.70,
    "max_lat": 38.86,
}


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _south_fork_catalog_record(catalog: dict[str, Any]) -> dict[str, Any]:
    for river in catalog["rivers"]:
        if river["river_id"] == "south_fork_american_chili_bar":
            return river
    raise ValueError("South Fork catalog record is missing")


def _access_feature_by_id(access_points: dict[str, Any], annotation_id: str) -> dict[str, Any]:
    for feature in access_points["features"]:
        if feature["properties"]["annotation_id"] == annotation_id:
            return feature
    raise ValueError(f"Missing access feature: {annotation_id}")


def _bbox_query(bounds: dict[str, float]) -> str:
    return ",".join(
        str(bounds[key])
        for key in ("min_lon", "min_lat", "max_lon", "max_lat")
    )


def _tnm_products_url(dataset: str, bounds: dict[str, float]) -> str:
    return (
        "https://tnmaccess.nationalmap.gov/api/v1/products?"
        f"datasets={quote(dataset)}&bbox={_bbox_query(bounds)}"
    )


def _review_window(
    center_lon: float,
    center_lat: float,
    half_width_deg: float,
    half_height_deg: float,
) -> dict[str, float]:
    return {
        "min_lon": round(center_lon - half_width_deg, 6),
        "min_lat": round(center_lat - half_height_deg, 6),
        "max_lon": round(center_lon + half_width_deg, 6),
        "max_lat": round(center_lat + half_height_deg, 6),
    }


def build_south_fork_a1_full_reach_acquisition_plan(
    repo_root: Path,
) -> dict[str, Any]:
    """Build the full-reach data-acquisition and promotion contract for A1."""

    repo_root = repo_root.resolve()
    catalog = _load_json(repo_root, SOURCE_CATALOG_RELATIVE_PATH)
    river = _south_fork_catalog_record(catalog)
    access_points = _load_json(repo_root, ACCESS_POINTS_RELATIVE_PATH)
    alignment = _load_json(repo_root, ALIGNMENT_REVIEW_RELATIVE_PATH)
    a1_status = _load_json(repo_root, A1_STATUS_RELATIVE_PATH)

    chili_bar = _access_feature_by_id(
        access_points,
        "chili_bar_put_in_review_seed",
    )
    coloma = _access_feature_by_id(access_points, "coloma_takeout_review_seed")
    coloma_station_m = float(
        alignment["published_reference"]["coloma_bridge_station_m"]
    )
    run_length_m = float(river["run_length_m"])
    envelope = FULL_REACH_REVIEW_ENVELOPE_WGS84

    return {
        "schema": "raftsim.south_fork.a1_full_reach_acquisition_plan.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": river["river_id"],
        "display_name": river["display_name"],
        "status": "planned_no_source_downloaded_not_geometry_authority",
        "production_promoted": False,
        "inputs": {
            "a1_status": A1_STATUS_RELATIVE_PATH,
            "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
            "alignment_review": ALIGNMENT_REVIEW_RELATIVE_PATH,
            "access_points": ACCESS_POINTS_RELATIVE_PATH,
        },
        "current_blockers": [
            "Current NHD bbox extract is pilot-only and not full reach.",
            "Current production corridor is the 0-2.531 km Chili Bar slice.",
            "Current alignment review records a 26.2 km candidate vs. 9.0 km Coloma checkpoint conflict.",
            "Flow bands are attached but review-gated, not promoted gameplay bands.",
        ],
        "review_envelope_wgs84": envelope,
        "review_envelope_policy": {
            "authority": "download_and_search_window_only_not_final_access_geometry",
            "reason": (
                "The envelope intentionally over-covers Chili Bar, Coloma, the "
                "Gorge sequence, and the Folsom Reservoir approach so the next "
                "source pull cannot hide the current endpoint conflict."
            ),
            "must_clip_to_reviewed_anchors_before_promotion": True,
        },
        "metadata_probe_2026_07_16": {
            "status": "metadata_only_no_archives_tiles_or_media_downloaded",
            "probe_scope": (
                "Small TNM product metadata queries for the full-review envelope; "
                "large hydrography archives, DEM rasters, NAIP tiles, and media were "
                "not downloaded."
            ),
            "results": [
                {
                    "source_class": "hydrography",
                    "source_id": "usgs_3dhp_or_nhd_full_reach",
                    "http_status": 200,
                    "item_total": 38,
                    "query_url": _tnm_products_url(
                        "National Hydrography Dataset (NHD)",
                        envelope,
                    ),
                    "observed_product_examples": [
                        "NHD Best Resolution national FileGDB/GeoPackage",
                        "NHD Best Resolution California State Shapefile",
                        "NHDPlus HR HU4/National products for network-order review",
                    ],
                    "next_action": (
                        "Select the smallest official product family that covers the "
                        "full review envelope, then extract only the needed flowline "
                        "and support layers with source IDs preserved."
                    ),
                },
                {
                    "source_class": "terrain_dem_or_lidar",
                    "source_id": "usgs_3dep_full_reach_tiles",
                    "http_status": 200,
                    "item_total": 0,
                    "query_url": _tnm_products_url(
                        "Elevation Products (3D Elevation Program Products and Services)",
                        envelope,
                    ),
                    "next_action": (
                        "Record the TNM metadata zero-hit and use bounded official "
                        "USGS 3DEP ImageServer/tile exports for full-reach terrain."
                    ),
                },
                {
                    "source_class": "aerial_imagery",
                    "source_id": "usda_naip_full_reach_tiles",
                    "http_status": 200,
                    "item_total": 0,
                    "query_url": _tnm_products_url(
                        "Imagery - NAIP (1 meter to .5 foot)",
                        envelope,
                    ),
                    "next_action": (
                        "Record the TNM metadata zero-hit and use bounded official "
                        "USDA/APFO NAIP ImageServer or tile-index exports."
                    ),
                },
            ],
        },
        "anchor_review_targets": [
            {
                "anchor_id": "chili_bar_put_in",
                "role": "upstream_start",
                "current_seed_lon_lat": [
                    chili_bar["properties"]["station_lon"],
                    chili_bar["properties"]["station_lat"],
                ],
                "current_seed_status": chili_bar["properties"]["stationing_status"],
                "search_window_wgs84": _review_window(
                    float(chili_bar["properties"]["station_lon"]),
                    float(chili_bar["properties"]["station_lat"]),
                    0.01,
                    0.008,
                ),
                "promotion_gate": (
                    "Replace the seed with official land/access geometry or "
                    "record guide/geospatial approval before publishing or gameplay use."
                ),
            },
            {
                "anchor_id": "coloma_bridge_checkpoint",
                "role": "station_checkpoint_not_final_takeout",
                "published_station_m": coloma_station_m,
                "published_station_miles": round(coloma_station_m / MILES_TO_METERS, 3),
                "current_seed_lon_lat": [
                    coloma["properties"]["station_lon"],
                    coloma["properties"]["station_lat"],
                ],
                "current_seed_status": coloma["properties"]["stationing_status"],
                "maximum_allowed_station_delta_m_before_manual_review": 250.0,
                "promotion_gate": (
                    "The corrected route must hit the published Chili Bar-to-Coloma "
                    "station checkpoint before any Gorge or Folsom projection is trusted."
                ),
            },
            {
                "anchor_id": "folsom_reservoir_takeout",
                "role": "downstream_end",
                "current_seed_lon_lat": None,
                "current_seed_status": "missing_exact_anchor",
                "search_window_wgs84": {
                    "min_lon": -121.12,
                    "min_lat": 38.68,
                    "max_lon": -120.88,
                    "max_lat": 38.84,
                },
                "published_run_length_m": run_length_m,
                "published_run_length_miles": round(run_length_m / MILES_TO_METERS, 3),
                "promotion_gate": (
                    "Attach an exact reviewed take-out/access point near the Folsom "
                    "Reservoir reach before full-run stationing is promoted."
                ),
            },
        ],
        "source_pull_queue": [
            {
                "source_class": "hydrography",
                "source_id": "usgs_3dhp_or_nhd_full_reach",
                "status": "metadata_probe_passed_products_available",
                "url": _tnm_products_url("National Hydrography Dataset (NHD)", envelope),
                "preferred_products": [
                    "3DHP if available for the full envelope",
                    "NHD Best Resolution state/HU products",
                    "NHDPlus HR only as supplemental network-order evidence",
                ],
                "target_artifacts": [
                    "hydrography/full_reach_raw_flowline_extract.geojson",
                    "hydrography/full_reach_raw_support_layers.geojson",
                    "hydrography/full_reach_source_manifest.json",
                ],
            },
            {
                "source_class": "terrain_dem_or_lidar",
                "source_id": "usgs_3dep_full_reach_tiles",
                "status": "tnm_metadata_zero_hits_use_official_3dep_image_service",
                "url": _tnm_products_url(
                    "Elevation Products (3D Elevation Program Products and Services)",
                    envelope,
                ),
                "target_artifacts": [
                    "terrain/full_reach_3dep_tile_manifest.json",
                    "terrain/full_reach_windowed_heightfields/",
                ],
            },
            {
                "source_class": "aerial_imagery",
                "source_id": "usda_naip_full_reach_tiles",
                "status": "tnm_metadata_zero_hits_use_official_naip_image_service",
                "url": _tnm_products_url(
                    "Imagery - NAIP (1 meter to .5 foot)",
                    envelope,
                ),
                "target_artifacts": [
                    "imagery/full_reach_naip_tile_manifest.json",
                    "imagery/full_reach_windowed_drapes/",
                ],
            },
            {
                "source_class": "flow_history",
                "source_id": "cdec_cbr_a25_plus_usgs_context",
                "status": "attached_but_needs_full_window_review",
                "existing_evidence": a1_status["flow_evidence"]["source_selection"],
                "target_artifacts": [
                    "hydrology/production_import_pilot/flow_band_review.json",
                    "hydrology/full_reach_flow_window_review.json",
                ],
            },
            {
                "source_class": "guide_and_access_review",
                "source_id": "guide_outfitter_land_manager_review",
                "status": "planned_link_and_annotation_only",
                "target_artifacts": [
                    "review/full_reach_anchor_review.json",
                    "review/full_reach_sensitive_publication_review.json",
                    "review/full_reach_guide_stationing_notes.json",
                ],
            },
        ],
        "route_solution_requirements": [
            {
                "requirement": "Select a directed South Fork American mainstem graph from Chili Bar to Folsom Reservoir.",
                "acceptance": (
                    "One ordered route chain, no unexplained reversals or branch jumps, "
                    "and every source segment preserves ID/provenance."
                ),
            },
            {
                "requirement": "Clip route to reviewed Chili Bar and Folsom anchors.",
                "acceptance": (
                    "Route start/end are exact reviewed anchors, not the broad source "
                    "download envelope or unreviewed access seeds."
                ),
            },
            {
                "requirement": "Validate Coloma checkpoint before projecting Gorge rapids.",
                "acceptance": (
                    "Corrected station at Coloma is within 250 m of the published "
                    f"{coloma_station_m:.3f} m checkpoint, or manual review remains blocked."
                ),
            },
            {
                "requirement": "Project all 20 published rapid miles onto the corrected route.",
                "acceptance": (
                    "Every South Fork marker has exact route geometry and zero markers "
                    "fall back to downstream-order interpolation."
                ),
            },
            {
                "requirement": "Generate windowed full-run corridor packages.",
                "acceptance": (
                    "Chili Bar, Coloma, Gorge, and Folsom windows are stitched for "
                    "validation outputs; seams cannot hide physics or art errors."
                ),
            },
        ],
        "planned_outputs": [
            "hydrography/full_reach_centerline.geojson",
            "hydrography/full_reach_stationing.json",
            "hydrography/full_reach_alignment_review.json",
            "production_corridor/full_reach_window_manifest.json",
            "review/full_reach_named_rapid_stationing_review.json",
            "review/named_rapid_station_alignment_review.json",
            "unreal/Content/RaftSim/River/named_rapid_editor_geometry.geojson",
        ],
        "promotion_gate": {
            "can_enable_south_fork_editor_geometry": False,
            "can_bind_meat_grinder_troublemaker_solver_windows": False,
            "exit_criteria": [
                "Full-reach official hydrography or 3DHP/NHD route selected and clipped.",
                "Chili Bar, Coloma checkpoint, and Folsom take-out anchors reviewed.",
                "All 20 rapid stations regenerated from corrected route geometry.",
                "Flow windows reviewed against CDEC/USGS context and guide notes.",
                "Corridor regression tests pass on stitched whole-window outputs.",
            ],
        },
    }


def write_south_fork_a1_full_reach_acquisition_plan(repo_root: Path) -> Path:
    payload = build_south_fork_a1_full_reach_acquisition_plan(repo_root)
    path = repo_root / FULL_REACH_ACQUISITION_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
