"""Record the Colorado A2 full-reach TNM metadata probe."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .colorado_a2_centerline_acquisition_plan import (
    COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_RELATIVE_PATH,
    FULL_REACH_REVIEW_ENVELOPE_WGS84,
)
from .colorado_a2_full_reach_window_plan import (
    COLORADO_A2_FULL_REACH_WINDOW_PLAN_RELATIVE_PATH,
    COLORADO_RIVER_ID,
)


COLORADO_A2_METADATA_PROBE_RELATIVE_PATH = (
    "physics/data/real_world/colorado_river_grand_canyon_rowing/hydrography/"
    "full_reach_metadata_probe.json"
)
COLORADO_A2_METADATA_PROBE_SCHEMA = "raftsim.colorado.a2_metadata_probe.v1"


def build_colorado_a2_metadata_probe() -> dict[str, Any]:
    """Build the recorded TNM metadata probe result for Colorado A2."""

    return {
        "schema": COLORADO_A2_METADATA_PROBE_SCHEMA,
        "generated_on": "2026-07-16",
        "river_id": COLORADO_RIVER_ID,
        "status": "metadata_probe_recorded_no_source_download_no_promotion",
        "production_promoted": False,
        "source_downloads_allowed": False,
        "centerline_binding_allowed": False,
        "unreal_import_allowed": False,
        "inputs": {
            "centerline_acquisition_plan": COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_RELATIVE_PATH,
            "window_plan": COLORADO_A2_FULL_REACH_WINDOW_PLAN_RELATIVE_PATH,
        },
        "review_envelope_wgs84": FULL_REACH_REVIEW_ENVELOPE_WGS84,
        "retrieval": {
            "retrieved_on": "2026-07-16",
            "method": "curl -L --max-time 20 against official TNM metadata endpoints",
            "raw_response_policy": (
                "Raw temporary JSON responses were not committed; byte counts, "
                "SHA-256 hashes, query URLs, totals, and representative titles are recorded."
            ),
        },
        "results": _probe_results(),
        "promotion_gate": {
            "metadata_probe_recorded": True,
            "hydrography_products_available_for_review": True,
            "terrain_product_metadata_available": False,
            "naip_product_metadata_available": False,
            "source_archives_or_rasters_downloaded": False,
            "full_reach_source_pull_urls_generated": False,
            "can_promote_centerline_or_windows": False,
            "next_required_actions": [
                "Select the smallest official hydrography product family covering the full review envelope.",
                "Use bounded USGS 3DEP ImageServer or tile exports for terrain because TNM product metadata returned zero 3DEP hits for the envelope.",
                "Use bounded USDA/APFO NAIP ImageServer or tile-index exports for imagery because TNM product metadata returned zero NAIP hits for the envelope.",
                "Do not generate per-window source-pull URLs until a reviewed full centerline and CRS exist.",
            ],
        },
    }


def write_colorado_a2_metadata_probe(repo_root: Path) -> Path:
    payload = build_colorado_a2_metadata_probe()
    path = repo_root / COLORADO_A2_METADATA_PROBE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _bbox_query() -> str:
    return ",".join(
        str(FULL_REACH_REVIEW_ENVELOPE_WGS84[key])
        for key in ("min_lon", "min_lat", "max_lon", "max_lat")
    )


def _tnm_products_url(dataset: str) -> str:
    return (
        "https://tnmaccess.nationalmap.gov/api/v1/products?"
        f"datasets={quote(dataset)}&bbox={_bbox_query()}"
    )


def _probe_results() -> list[dict[str, Any]]:
    return [
        {
            "source_class": "hydrography",
            "source_id": "tnm_nhd_full_reach_envelope",
            "dataset": "National Hydrography Dataset (NHD)",
            "query_url": _tnm_products_url("National Hydrography Dataset (NHD)"),
            "http_status": 200,
            "curl_exit_code": 0,
            "total": 94,
            "returned_item_count": 50,
            "raw_response_bytes": 155455,
            "raw_response_sha256": (
                "6abd6af5332e92dff8ce6fbafedfa3d0b00e47c915f42c904465d55e7807c604"
            ),
            "representative_titles": [
                "USGS National Hydrography Dataset Best Resolution (NHD) (published 20250918) FileGDB",
                "USGS National Hydrography Dataset Best Resolution (NHD) (published 20250918) GeoPackage",
                "USGS National Hydrography Dataset Best Resolution (NHD) - Arizona (published 20231227) FileGDB",
                "USGS National Hydrography Dataset Best Resolution (NHD) - Arizona (published 20231227) GeoPackage",
                "USGS National Hydrography Dataset Best Resolution (NHD) - Arizona (published 20231227) Shapefile",
            ],
            "next_action": (
                "Select the smallest official product family that covers the full "
                "review envelope, then extract source-ID-preserving flowlines only."
            ),
        },
        {
            "source_class": "terrain_dem_or_lidar",
            "source_id": "tnm_3dep_full_reach_envelope",
            "dataset": "Elevation Products (3D Elevation Program Products and Services)",
            "query_url": _tnm_products_url(
                "Elevation Products (3D Elevation Program Products and Services)"
            ),
            "http_status": 200,
            "curl_exit_code": 0,
            "total": 0,
            "returned_item_count": 0,
            "raw_response_bytes": 713,
            "raw_response_sha256": (
                "e10fcbd722f8452dac5a68a01f53e51c2d905ad55cb5fe8a59f9d798c325063b"
            ),
            "messages": [
                "The offset is greater than the total number of results for this query. No items returned."
            ],
            "next_action": (
                "Use bounded official USGS 3DEP ImageServer or tile exports after "
                "reviewed window bboxes exist; do not treat TNM product metadata as terrain coverage."
            ),
        },
        {
            "source_class": "aerial_imagery",
            "source_id": "tnm_naip_full_reach_envelope",
            "dataset": "Imagery - NAIP (1 meter to .5 foot)",
            "query_url": _tnm_products_url("Imagery - NAIP (1 meter to .5 foot)"),
            "http_status": 200,
            "curl_exit_code": 0,
            "total": 0,
            "returned_item_count": 0,
            "raw_response_bytes": 685,
            "raw_response_sha256": (
                "28f286d7dab16ee0cc56a20e6f9ce6199fc4d6e5129eaaa37834ba0bdf140f66"
            ),
            "messages": [
                "The offset is greater than the total number of results for this query. No items returned."
            ],
            "next_action": (
                "Use bounded official USDA/APFO NAIP ImageServer or tile-index exports "
                "after reviewed window bboxes exist; do not treat TNM product metadata as imagery coverage."
            ),
        },
    ]
