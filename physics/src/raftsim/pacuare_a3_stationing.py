"""Track the Pacuare A3 stationing repair gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .named_rapid_registry import SOURCE_CATALOG_RELATIVE_PATH


PACUARE_A3_STATIONING_STATUS_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/review/"
    "a3_stationing_repair_status.json"
)
PACUARE_A3_STATIONING_STATUS_SCHEMA = "raftsim.pacuare.a3_stationing_repair_status.v1"
PACUARE_RIVER_ID = "pacuare_river_costa_rica"
SOURCE_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/source_manifest.json"
)
FLOW_PRESETS_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/flow_presets.json"
)
PREVIEW_CENTERLINE_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/hydrography/"
    "production_import_pilot/preview_centerline_scaffold_manifest.json"
)
PREVIEW_STATIONING_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/hydrography/"
    "production_import_pilot/preview_stationing_scaffold.json"
)
RAPID_ACCESS_STATIONING_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/hydrography/"
    "production_import_pilot/rapid_and_access_stationing.geojson"
)
OFFICIAL_SOURCE_ACCESS_PLAN_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/hydrography/"
    "production_import_pilot/official_source_access_plan.json"
)
SNIT_LAYER_CATALOG_SUMMARY_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/hydrography/"
    "production_import_pilot/snit_layer_catalog_summary.json"
)
SENTINEL_CORRIDOR_QA_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/imagery/"
    "production_import_pilot/sentinel_20250320_corridor_bbox_scl_qa_review.json"
)
SENTINEL_DRAFT_BANK_REVIEW_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/imagery/"
    "production_import_pilot/sentinel_20250320_draft_bank_window_review.json"
)
HYDROLOGY_GAUGE_SEARCH_RELATIVE_PATH = (
    "physics/data/real_world/pacuare_river_costa_rica/hydrology/"
    "costa_rica_gauge_search.json"
)


def build_pacuare_a3_stationing_repair_status(repo_root: Path) -> dict[str, Any]:
    """Build the current fail-closed A3 stationing status for Pacuare."""

    repo_root = repo_root.resolve()
    catalog = _load_json(repo_root / SOURCE_CATALOG_RELATIVE_PATH)
    river = _pacuare_catalog_record(catalog)
    source_manifest = _load_json(repo_root / SOURCE_MANIFEST_RELATIVE_PATH)
    flow_presets = _load_json(repo_root / FLOW_PRESETS_RELATIVE_PATH)
    preview_manifest = _load_json(repo_root / PREVIEW_CENTERLINE_MANIFEST_RELATIVE_PATH)
    preview_stationing = _load_json(repo_root / PREVIEW_STATIONING_RELATIVE_PATH)
    rapid_access = _load_json(repo_root / RAPID_ACCESS_STATIONING_RELATIVE_PATH)

    rapid_records = _rapid_station_records(river)
    preview_length_m = float(preview_manifest["summary"]["length_m_preview_wgs84_linearized"])
    catalog_length_m = float(river["run_length_m"])
    rapid_seed_count = sum(
        1
        for feature in rapid_access["features"]
        if feature["properties"]["feature_role"].startswith("rapid")
    )
    return {
        "schema": PACUARE_A3_STATIONING_STATUS_SCHEMA,
        "generated_on": "2026-07-16",
        "plan": (
            "docs/five-river-photoreal-execution-plan.md"
            "#workstream-a--source-data-stationing-and-seasonal-flows-per-river"
        ),
        "task_id": "A3",
        "river_id": river["river_id"],
        "display_name": river["display_name"],
        "status": "blocked_pending_official_hydrography_aerial_stationing_and_guide_review",
        "production_promoted": False,
        "exact_stationing_promoted": False,
        "editor_binding_allowed": False,
        "solver_window_binding_allowed": False,
        "do_not_use_for": [
            "exact rapid geometry",
            "official access or protected-area route publication",
            "solver water-window binding",
            "production-playable Pacuare completion",
        ],
        "catalog_stationing_scaffold": {
            "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
            "stationing_authority": river["stationing_authority"],
            "run_length_m": catalog_length_m,
            "rapid_count": len(rapid_records),
            "critical_rapid_count": sum(
                1 for rapid in rapid_records if rapid["review_priority"] == "critical"
            ),
            "all_rapids_are_order_only": all(
                rapid["stationing_kind"] == "provisional_downstream_order_interpolation"
                for rapid in rapid_records
            ),
            "rapid_stations": rapid_records,
        },
        "current_geometry_evidence": {
            "source_manifest": SOURCE_MANIFEST_RELATIVE_PATH,
            "source_manifest_review_status": source_manifest["provenance"]["review_status"],
            "preview_centerline_manifest": PREVIEW_CENTERLINE_MANIFEST_RELATIVE_PATH,
            "preview_centerline_status": preview_manifest["status"],
            "preview_stationing": PREVIEW_STATIONING_RELATIVE_PATH,
            "preview_stationing_review_status": preview_stationing["review_status"],
            "rapid_and_access_stationing": RAPID_ACCESS_STATIONING_RELATIVE_PATH,
            "rapid_access_preview_seed_count": rapid_seed_count,
            "preview_length_m": round(preview_length_m, 3),
            "catalog_run_length_m": catalog_length_m,
            "preview_to_catalog_length_ratio": round(preview_length_m / catalog_length_m, 6),
            "preview_length_matches_catalog_run": abs(preview_length_m - catalog_length_m) < 250.0,
            "geometry_binding_enabled": False,
            "why_blocked": (
                "The committed route is a generated Unreal preview scaffold, the "
                "catalog rapid positions are order-only, and the preview scaffold "
                "length materially differs from the catalog run length."
            ),
        },
        "source_review_inputs": [
            {
                "source_class": "official_hydrography_access",
                "path": OFFICIAL_SOURCE_ACCESS_PLAN_RELATIVE_PATH,
                "status": "lead_recorded_not_route_authority",
                "required_before_promotion": "official route/access source selected and reviewed",
            },
            {
                "source_class": "snit_layer_catalog",
                "path": SNIT_LAYER_CATALOG_SUMMARY_RELATIVE_PATH,
                "status": "lead_recorded_not_route_authority",
                "required_before_promotion": "candidate hydrography/protected-area layers selected and clipped",
            },
            {
                "source_class": "sentinel_corridor_imagery",
                "path": SENTINEL_CORRIDOR_QA_RELATIVE_PATH,
                "status": "review_imagery_available_not_exact_rapid_stationing",
                "required_before_promotion": "cloud/shadow and bank-window suitability accepted",
            },
            {
                "source_class": "sentinel_bank_window",
                "path": SENTINEL_DRAFT_BANK_REVIEW_RELATIVE_PATH,
                "status": "draft_bank_window_review_not_rapid_stationing",
                "required_before_promotion": "aerial-interpreted rapid locations digitized and guide-confirmed",
            },
            {
                "source_class": "hydrology_gauge_search",
                "path": HYDROLOGY_GAUGE_SEARCH_RELATIVE_PATH,
                "status": "review_leads_recorded_no_numeric_flow_promotion",
                "required_before_promotion": "gauge/stage/rainfall source class selected for flow bands",
            },
        ],
        "flow_evidence": {
            "flow_presets": FLOW_PRESETS_RELATIVE_PATH,
            "flow_status": flow_presets["status"],
            "numeric_discharge_values_allowed": flow_presets["flow_band_policy"][
                "numeric_discharge_values_allowed"
            ],
            "flow_band_count": len(flow_presets["flow_bands"]),
            "hydrology_review_needs": flow_presets["hydrology_review_needs"],
        },
        "a3_acceptance": [
            {
                "requirement": "Replace order-interpolated stations for all 15 markers.",
                "status": "not_met",
                "evidence": [SOURCE_CATALOG_RELATIVE_PATH],
                "next_action": (
                    "Digitize every rapid from accepted aerial/orthomosaic imagery against a "
                    "reviewed route, then record guide/outfitter confirmation."
                ),
            },
            {
                "requirement": "Terrain and imagery source class recorded.",
                "status": "partial_review_gated",
                "evidence": [
                    SOURCE_MANIFEST_RELATIVE_PATH,
                    SENTINEL_CORRIDOR_QA_RELATIVE_PATH,
                    PREVIEW_CENTERLINE_MANIFEST_RELATIVE_PATH,
                ],
                "next_action": (
                    "Select official route/hydrography and cloud-screened high-resolution imagery "
                    "before stationing or production Landscape promotion."
                ),
            },
            {
                "requirement": "Flow bands recorded with source class.",
                "status": "planning_placeholders_only",
                "evidence": [FLOW_PRESETS_RELATIVE_PATH, HYDROLOGY_GAUGE_SEARCH_RELATIVE_PATH],
                "next_action": (
                    "Replace relative flow placeholders with reviewed gauge, stage, rainfall, "
                    "or operator-range source classes."
                ),
            },
            {
                "requirement": "Exit gate: no Pacuare marker uses provisional order interpolation.",
                "status": "not_met",
                "evidence": [SOURCE_CATALOG_RELATIVE_PATH],
                "next_action": (
                    "Keep Pacuare editor geometry, rapid water windows, and solver binding disabled "
                    "until all rapid stationing_kind values are exact GPS/aerial/guide-reviewed records."
                ),
            },
        ],
        "promotion_gate": {
            "can_promote_a3_stationing": False,
            "can_bind_editor_geometry": False,
            "can_generate_rapid_water_windows": False,
            "can_bind_solver_windows": False,
            "can_request_human_lifelike_route_review": False,
        },
    }


def write_pacuare_a3_stationing_repair_status(repo_root: Path) -> Path:
    payload = build_pacuare_a3_stationing_repair_status(repo_root)
    path = repo_root / PACUARE_A3_STATIONING_STATUS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _pacuare_catalog_record(catalog: dict[str, Any]) -> dict[str, Any]:
    for river in catalog["rivers"]:
        if river["river_id"] == PACUARE_RIVER_ID:
            return river
    raise RuntimeError(f"Missing {PACUARE_RIVER_ID} in named rapid catalog")


def _rapid_station_records(river: dict[str, Any]) -> list[dict[str, Any]]:
    rapids = river["rapids"]
    records: list[dict[str, Any]] = []
    for rapid in rapids:
        station_m = float(river["run_length_m"]) * int(rapid["order"]) / (len(rapids) + 1)
        records.append(
            {
                "name": rapid["name"],
                "aliases": rapid.get("aliases", []),
                "order": rapid["order"],
                "class": rapid["class"],
                "feature_tags": rapid["feature_tags"],
                "review_priority": rapid["review_priority"],
                "station_m_from_order_interpolation": round(station_m, 3),
                "stationing_kind": "provisional_downstream_order_interpolation",
                "exact_geometry_status": "blocked_pending_aerial_digitizing_and_guide_review",
            }
        )
    return records
