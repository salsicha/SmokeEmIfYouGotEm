"""Build the South Fork A1 downstream-anchor decision packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .south_fork_a1_anchor_review import FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH
from .south_fork_a1_directed_station_candidates import (
    FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH,
)
from .south_fork_a1_window_source_preflight import (
    FULL_REACH_WINDOW_SOURCE_PULL_PREFLIGHT_RELATIVE_PATH,
)


FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_PACKET_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_downstream_anchor_decision_packet.json"
)
FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_downstream_anchor_decision_candidates.geojson"
)
FULL_REACH_WINDOW_DERIVATIVE_MANIFEST_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "full_reach_window_derivative_manifest.json"
)

_FINAL_WINDOW_ID = "salmon_falls_folsom_review_32991_33796m"
_LOWER_GORGE_WINDOW_ID = "lower_gorge_to_salmon_falls_28500_32991m"


def _load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _downstream_anchor(anchor_review: dict[str, Any]) -> dict[str, Any]:
    return next(
        anchor
        for anchor in anchor_review["anchor_reviews"]
        if anchor["role"] == "downstream_end"
    )


def _window_record(derivative_manifest: dict[str, Any], window_id: str) -> dict[str, Any]:
    return next(
        window
        for window in derivative_manifest["windows"]
        if window["window_id"] == window_id
    )


def _candidate_option(
    *,
    option_id: str,
    candidate: dict[str, Any],
    interpretation: str,
    review_consequence: str,
) -> dict[str, Any]:
    return {
        "option_id": option_id,
        "station_id": candidate["station_id"],
        "published_river_mile": candidate["published_river_mile"],
        "station_m": candidate["station_m"],
        "lon_lat": candidate["lon_lat"],
        "source_id": candidate["source_id"],
        "reachcode": candidate["reachcode"],
        "permanent_identifier": candidate["permanent_identifier"],
        "source_record_index": candidate["source_record_index"],
        "geometry_status": candidate["geometry_status"],
        "interpretation": interpretation,
        "review_consequence": review_consequence,
        "can_select_without_guide_geospatial_review": False,
        "can_bind_editor_geometry": False,
        "can_crop_final_corridor": False,
        "can_bind_solver_windows": False,
    }


def build_south_fork_a1_downstream_anchor_decision_packet(
    repo_root: Path,
) -> dict[str, Any]:
    """Build the review packet for the unresolved Salmon Falls/Folsom anchor."""

    repo_root = repo_root.resolve()
    anchor_review = _load_json(repo_root, FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH)
    directed = _load_json(repo_root, FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH)
    derivative_manifest = _load_json(
        repo_root,
        FULL_REACH_WINDOW_DERIVATIVE_MANIFEST_RELATIVE_PATH,
    )
    preflight = _load_json(repo_root, FULL_REACH_WINDOW_SOURCE_PULL_PREFLIGHT_RELATIVE_PATH)

    downstream = _downstream_anchor(anchor_review)
    downstream_window = directed["source_anchor_station_candidates"][
        "downstream_source_window"
    ]
    minimum = downstream_window["minimum_source_mile_candidate"]
    maximum = downstream_window["maximum_source_mile_candidate"]
    station_delta_m = round(float(maximum["station_m"]) - float(minimum["station_m"]), 6)
    final_window = _window_record(derivative_manifest, _FINAL_WINDOW_ID)
    lower_gorge_window = _window_record(derivative_manifest, _LOWER_GORGE_WINDOW_ID)
    options = [
        _candidate_option(
            option_id="select_20_5_mile_salmon_falls_basis",
            candidate=minimum,
            interpretation=(
                "Use the American Rivers 20.5-mile Salmon Falls Bridge/Folsom-area "
                "take-out basis as the downstream station convention."
            ),
            review_consequence=(
                "Final crop would end at the upstream edge of the current anchor "
                "review window; the 21.0-mile over-cover would remain source context "
                "unless a reviewer selects it for access/stage reasons."
            ),
        ),
        _candidate_option(
            option_id="select_21_0_mile_full_run_folsom_basis",
            candidate=maximum,
            interpretation=(
                "Use the American Whitewater 21.0-mile full-run/Folsom basis as "
                "the downstream station convention."
            ),
            review_consequence=(
                "Final crop would preserve the full 804.672 m downstream review "
                "window beyond the 20.5-mile candidate; access, reservoir stage, "
                "and publication-sensitivity review must justify the extra context."
            ),
        ),
    ]

    return {
        "schema": "raftsim.south_fork.a1_downstream_anchor_decision_packet.v1",
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": anchor_review["river_id"],
        "status": "decision_packet_ready_exact_anchor_not_selected",
        "production_promoted": False,
        "inputs": {
            "anchor_review": FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH,
            "directed_station_candidates": FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH,
            "window_derivative_manifest": FULL_REACH_WINDOW_DERIVATIVE_MANIFEST_RELATIVE_PATH,
            "source_pull_preflight": FULL_REACH_WINDOW_SOURCE_PULL_PREFLIGHT_RELATIVE_PATH,
        },
        "decision_required": {
            "question": (
                "Which reviewed downstream anchor and station convention should "
                "define the South Fork full-run endpoint?"
            ),
            "current_state": downstream["current_seed_status"],
            "exact_anchor_selected": False,
            "acceptable_answers": [
                "Select the 20.5-mile Salmon Falls basis after guide/geospatial review.",
                "Select the 21.0-mile Folsom/full-run basis after guide/geospatial review.",
                "Replace both candidates with another exact, reviewed take-out/access point.",
            ],
            "must_record_before_promotion": [
                "exact lon/lat and station_m",
                "source-mile convention",
                "access/land-status authority",
                "reservoir-stage/access interpretation",
                "guide/geospatial reviewer approval",
                "publication-sensitivity decision for screenshots and maps",
            ],
        },
        "candidate_window": {
            "minimum_station_m": minimum["station_m"],
            "maximum_station_m": maximum["station_m"],
            "station_delta_m": station_delta_m,
            "station_delta_miles": downstream["source_mile_window"]["delta_miles"],
            "validation_status": downstream_window["validation_status"],
            "geojson_candidates": (
                FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH
            ),
        },
        "options": options,
        "visual_review_inputs": {
            "lower_gorge_window": {
                "window_id": lower_gorge_window["window_id"],
                "station_range_m": lower_gorge_window["station_range_m"],
                "edge_report": lower_gorge_window["edge_report"],
                "derived_artifacts": lower_gorge_window["derived_artifacts"],
            },
            "anchor_review_window": {
                "window_id": final_window["window_id"],
                "station_range_m": final_window["station_range_m"],
                "edge_report": final_window["edge_report"],
                "derived_artifacts": final_window["derived_artifacts"],
            },
        },
        "source_review_state": {
            "source_mile_evidence": downstream["source_mile_evidence"],
            "source_leads": [
                source
                for source in anchor_review["source_leads"]
                if any("Folsom" in item or "Salmon Falls" in item for item in source["used_for"])
            ],
            "preflight_status": preflight["status"],
            "overcover_interpretation": preflight["downstream_anchor_review"][
                "interpretation"
            ],
        },
        "promotion_gate": {
            "can_select_anchor_without_human_review": False,
            "can_crop_to_final_downstream_anchor": False,
            "can_promote_full_reach_centerline": False,
            "can_regenerate_rapid_stationing": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
            "next_required_actions": [
                "Open the derivative NAIP overlays and the candidate GeoJSON in the editor/GIS review tool.",
                "Compare the two candidate points against official access, reservoir-stage, land-status, and guide evidence.",
                "Record the selected exact downstream anchor or a replacement reviewed take-out point.",
                "Regenerate clipped corridor windows, rapid stationing, and editor geometry only after that decision.",
            ],
        },
    }


def build_south_fork_a1_downstream_anchor_decision_geojson(
    repo_root: Path,
) -> dict[str, Any]:
    packet = build_south_fork_a1_downstream_anchor_decision_packet(repo_root)
    candidate_features = [
        {
            "type": "Feature",
            "id": option["option_id"],
            "geometry": {
                "type": "Point",
                "coordinates": option["lon_lat"],
            },
            "properties": {
                "river_id": packet["river_id"],
                "task_id": packet["task_id"],
                "station_id": option["station_id"],
                "published_river_mile": option["published_river_mile"],
                "station_m": option["station_m"],
                "source_id": option["source_id"],
                "geometry_status": option["geometry_status"],
                "can_bind_editor_geometry": False,
                "can_bind_solver_windows": False,
                "production_promoted": False,
            },
        }
        for option in packet["options"]
    ]
    span_feature = {
        "type": "Feature",
        "id": "downstream_anchor_decision_span_20_5_to_21_0_miles",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                packet["options"][0]["lon_lat"],
                packet["options"][1]["lon_lat"],
            ],
        },
        "properties": {
            "river_id": packet["river_id"],
            "task_id": packet["task_id"],
            "station_start_m": packet["candidate_window"]["minimum_station_m"],
            "station_end_m": packet["candidate_window"]["maximum_station_m"],
            "station_delta_m": packet["candidate_window"]["station_delta_m"],
            "geometry_status": "review_span_only_exact_anchor_not_selected",
            "can_bind_editor_geometry": False,
            "can_bind_solver_windows": False,
            "production_promoted": False,
        },
    }
    return {
        "type": "FeatureCollection",
        "schema": "raftsim.south_fork.a1_downstream_anchor_decision_candidates.geojson.v1",
        "generated_on": packet["generated_on"],
        "status": packet["status"],
        "river_id": packet["river_id"],
        "features": [*candidate_features, span_feature],
        "policy": {
            "allowed_use": [
                "anchor decision review",
                "GIS/editor overlay",
                "guide/geospatial source comparison",
            ],
            "forbidden_use": [
                "final access geometry",
                "corridor crop authority",
                "named-rapid stationing authority",
                "solver-window binding",
            ],
        },
    }


def write_south_fork_a1_downstream_anchor_decision_packet(repo_root: Path) -> list[Path]:
    repo_root = repo_root.resolve()
    packet = build_south_fork_a1_downstream_anchor_decision_packet(repo_root)
    geojson = build_south_fork_a1_downstream_anchor_decision_geojson(repo_root)
    packet_path = repo_root / FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_PACKET_RELATIVE_PATH
    geojson_path = repo_root / FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH
    _write_json(packet_path, packet)
    _write_json(geojson_path, geojson)
    return [packet_path, geojson_path]
