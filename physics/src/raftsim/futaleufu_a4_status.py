"""Track Futaleufu A4 stationing and flow-band readiness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .named_rapid_registry import SOURCE_CATALOG_RELATIVE_PATH


FUTALEUFU_A4_STATUS_RELATIVE_PATH = (
    "physics/data/real_world/futaleufu_river_chile/review/"
    "a4_stationing_flow_status.json"
)
FUTALEUFU_A4_STATUS_SCHEMA = "raftsim.futaleufu.a4_stationing_flow_status.v1"
FUTALEUFU_RIVER_ID = "futaleufu_river_chile"
FUTALEUFU_CORRIDOR_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/futaleufu_river_chile/production_corridor/"
    "rio_azul_swinging_bridge_to_pasarela/manifest.json"
)
FUTALEUFU_ROUTE_STATIONING_RELATIVE_PATH = (
    "physics/data/real_world/futaleufu_river_chile/production_corridor/"
    "rio_azul_swinging_bridge_to_pasarela/hydrography/route_stationing.json"
)
FUTALEUFU_SEASONAL_FLOW_CONTEXT_RELATIVE_PATH = (
    "physics/data/real_world/futaleufu_river_chile/production_corridor/"
    "rio_azul_swinging_bridge_to_pasarela/hydrology/seasonal_flow_context.json"
)


def build_futaleufu_a4_stationing_flow_status(repo_root: Path) -> dict[str, Any]:
    """Build the current fail-closed A4 status for Futaleufu."""

    repo_root = repo_root.resolve()
    catalog = _load_json(repo_root / SOURCE_CATALOG_RELATIVE_PATH)
    river = _futaleufu_catalog_record(catalog)
    corridor = _load_json(repo_root / FUTALEUFU_CORRIDOR_MANIFEST_RELATIVE_PATH)
    route_stationing = _load_json(repo_root / FUTALEUFU_ROUTE_STATIONING_RELATIVE_PATH)
    seasonal_flow = _load_json(repo_root / FUTALEUFU_SEASONAL_FLOW_CONTEXT_RELATIVE_PATH)

    rapid_records = _rapid_station_records(river, route_stationing["length_m"])
    catalog_run_length_m = float(river["run_length_m"])
    route_length_m = float(route_stationing["length_m"])
    return {
        "schema": FUTALEUFU_A4_STATUS_SCHEMA,
        "generated_on": "2026-07-16",
        "plan": (
            "docs/five-river-photoreal-execution-plan.md"
            "#workstream-a--source-data-stationing-and-seasonal-flows-per-river"
        ),
        "task_id": "A4",
        "river_id": river["river_id"],
        "display_name": river["display_name"],
        "status": "blocked_pending_exact_rapid_stationing_dga_route_translation_and_guide_review",
        "production_promoted": False,
        "exact_stationing_promoted": False,
        "flow_bands_promoted": False,
        "editor_binding_allowed": False,
        "solver_window_binding_allowed": False,
        "do_not_use_for": [
            "exact rapid geometry",
            "flow-calibrated feature behavior",
            "solver water-window binding",
            "production-playable Futaleufu completion",
        ],
        "catalog_stationing_scaffold": {
            "source_catalog": SOURCE_CATALOG_RELATIVE_PATH,
            "stationing_authority": river["stationing_authority"],
            "catalog_run_length_m": catalog_run_length_m,
            "route_stationing_length_m": route_length_m,
            "route_to_catalog_length_ratio": round(route_length_m / catalog_run_length_m, 6),
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
        "current_corridor_evidence": {
            "corridor_manifest": FUTALEUFU_CORRIDOR_MANIFEST_RELATIVE_PATH,
            "corridor_status": corridor["status"],
            "route_stationing": FUTALEUFU_ROUTE_STATIONING_RELATIVE_PATH,
            "route_stationing_schema": route_stationing["schema"],
            "route_length_m": round(route_length_m, 3),
            "route_sample_count": len(route_stationing["samples"]),
            "geometry_authority": corridor["route"]["geometry_authority"],
            "guide_approval": corridor["route"]["guide_approval"],
            "editor_geometry_binding_enabled_in_catalog": bool(
                river["editor_geometry_source"]["binding_enabled"]
            ),
            "editor_geometry_binding_allowed_by_a4": False,
            "why_blocked": (
                "The corridor is useful technical evidence, but its OSM route trace is "
                "review-gated, the catalog stations are order-only, and guide/geospatial "
                "rapid stationing has not replaced the approximate route-length scaffold."
            ),
        },
        "flow_evidence": {
            "seasonal_flow_context": FUTALEUFU_SEASONAL_FLOW_CONTEXT_RELATIVE_PATH,
            "provider": seasonal_flow["provider"],
            "station": seasonal_flow["station"],
            "station_code": seasonal_flow["station_code"],
            "units": seasonal_flow["units"],
            "relation_to_reach": seasonal_flow["relation_to_reach"],
            "planning_band_count": len(seasonal_flow["planning_bands"]),
            "planning_bands": seasonal_flow["planning_bands"],
            "source_urls": seasonal_flow["source_urls"],
            "promotion_gate": seasonal_flow["promotion_gate"],
            "numeric_ranges_present": True,
            "numeric_flow_bands_promoted": False,
            "why_blocked": (
                "The DGA downstream station and planning ranges are source evidence, not "
                "accepted reach flow bands until time-series acquisition, route translation, "
                "travel-time review, and Futaleufu guide validation are complete."
            ),
        },
        "a4_acceptance": [
            {
                "requirement": "Exact stationing for Terminator, Khyber Pass, Himalayas, and other catalog markers.",
                "status": "not_met",
                "evidence": [SOURCE_CATALOG_RELATIVE_PATH, FUTALEUFU_ROUTE_STATIONING_RELATIVE_PATH],
                "next_action": (
                    "Replace every order-only rapid record with GPS/aerial/guide-reviewed "
                    "point or span geometry tied to the reviewed route stationing."
                ),
            },
            {
                "requirement": "DGA Chile gauge research and flow bands reviewed for the game reach.",
                "status": "partial_review_gated",
                "evidence": [FUTALEUFU_SEASONAL_FLOW_CONTEXT_RELATIVE_PATH],
                "next_action": (
                    "Acquire/record DGA time-series metadata, route translation, travel-time "
                    "assumptions, and guide-reviewed low/normal/high/unsafe thresholds."
                ),
            },
            {
                "requirement": "Exit gate: no Futaleufu marker uses provisional order interpolation.",
                "status": "not_met",
                "evidence": [SOURCE_CATALOG_RELATIVE_PATH],
                "next_action": (
                    "Keep Futaleufu editor geometry, rapid water windows, and solver binding "
                    "disabled until all rapid stationing_kind values are exact reviewed records."
                ),
            },
        ],
        "promotion_gate": {
            "can_promote_a4_stationing": False,
            "can_promote_a4_flow_bands": False,
            "can_bind_editor_geometry": False,
            "can_generate_rapid_water_windows": False,
            "can_bind_solver_windows": False,
            "can_request_human_lifelike_route_review": False,
        },
    }


def write_futaleufu_a4_stationing_flow_status(repo_root: Path) -> Path:
    payload = build_futaleufu_a4_stationing_flow_status(repo_root)
    path = repo_root / FUTALEUFU_A4_STATUS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _rapid_station_records(
    river: dict[str, Any],
    route_length_m: float,
) -> list[dict[str, Any]]:
    rapids = river["rapids"]
    records: list[dict[str, Any]] = []
    for rapid in rapids:
        catalog_station_m = float(river["run_length_m"]) * int(rapid["order"]) / (len(rapids) + 1)
        route_order_station_m = route_length_m * int(rapid["order"]) / (len(rapids) + 1)
        records.append(
            {
                "name": rapid["name"],
                "aliases": rapid.get("aliases", []),
                "order": rapid["order"],
                "class": rapid["class"],
                "feature_tags": rapid["feature_tags"],
                "review_priority": rapid["review_priority"],
                "catalog_station_m_from_order_interpolation": round(catalog_station_m, 3),
                "route_order_station_m_for_review_focus": round(route_order_station_m, 3),
                "stationing_kind": "provisional_downstream_order_interpolation",
                "exact_geometry_status": "blocked_pending_gps_aerial_digitizing_and_guide_review",
            }
        )
    return records


def _futaleufu_catalog_record(catalog: dict[str, Any]) -> dict[str, Any]:
    for river in catalog["rivers"]:
        if river["river_id"] == FUTALEUFU_RIVER_ID:
            return river
    raise RuntimeError(f"Missing {FUTALEUFU_RIVER_ID} in named rapid catalog")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
