"""Build the South Fork A1 source-mile/access decision packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .south_fork_a1_source_mile_access_options import (
    FULL_REACH_SOURCE_MILE_ACCESS_OPTION_MATRIX_RELATIVE_PATH,
    FULL_REACH_SOURCE_MILE_ACCESS_OPTION_POINTS_GEOJSON_RELATIVE_PATH,
    build_south_fork_a1_source_mile_access_option_matrix,
)
from .south_fork_a1_source_mile_divergence_audit import (
    FULL_REACH_SOURCE_MILE_DIVERGENCE_AUDIT_RELATIVE_PATH,
    FULL_REACH_SOURCE_MILE_DIVERGENCE_OVERLAY_GEOJSON_RELATIVE_PATH,
    build_south_fork_a1_source_mile_divergence_audit,
)


FULL_REACH_SOURCE_MILE_ACCESS_DECISION_PACKET_RELATIVE_PATH = (
    "physics/data/real_world/south_fork_american_chili_bar/review/"
    "full_reach_source_mile_access_decision_packet.json"
)
FULL_REACH_SOURCE_MILE_ACCESS_DECISION_SCHEMA = (
    "raftsim.south_fork.a1_source_mile_access_decision_packet.v1"
)


def build_south_fork_a1_source_mile_access_decision_packet(
    repo_root: Path,
) -> dict[str, Any]:
    """Build the decision packet that keeps A1 route promotion fail-closed."""

    repo_root = repo_root.resolve()
    matrix = build_south_fork_a1_source_mile_access_option_matrix(repo_root)
    divergence = build_south_fork_a1_source_mile_divergence_audit(repo_root)
    primary = next(
        option
        for option in matrix["official_access_options"]
        if option["option_id"]
        == matrix["option_rankings"]["primary_access_option_id"]
    )
    summary = matrix["summary"]
    divergence_summary = divergence["divergence_summary"]
    return {
        "schema": FULL_REACH_SOURCE_MILE_ACCESS_DECISION_SCHEMA,
        "generated_on": "2026-07-16",
        "task_id": "A1",
        "river_id": matrix["river_id"],
        "status": "source_mile_access_decision_required_route_promotion_blocked",
        "production_promoted": False,
        "inputs": {
            "source_mile_access_option_matrix": (
                FULL_REACH_SOURCE_MILE_ACCESS_OPTION_MATRIX_RELATIVE_PATH
            ),
            "source_mile_access_option_points_geojson": (
                FULL_REACH_SOURCE_MILE_ACCESS_OPTION_POINTS_GEOJSON_RELATIVE_PATH
            ),
            "source_mile_divergence_audit": (
                FULL_REACH_SOURCE_MILE_DIVERGENCE_AUDIT_RELATIVE_PATH
            ),
            "source_mile_divergence_overlay_geojson": (
                FULL_REACH_SOURCE_MILE_DIVERGENCE_OVERLAY_GEOJSON_RELATIVE_PATH
            ),
        },
        "current_operating_mode": {
            "mode": "review_only_no_endpoint_or_station_axis_selected",
            "can_promote_route_now": False,
            "can_regenerate_corridor_windows_now": False,
            "can_restation_named_rapids_now": False,
            "can_bind_solver_windows_now": False,
            "reason": (
                "All official downstream access candidates conflict with the "
                "published 20.5/21.0-mile source conventions on the current NHD "
                "station axis, and the published 21.0-mile point remains far "
                "upstream of the official Salmon Falls access lead."
            ),
        },
        "evidence_summary": {
            "official_access_option_count": summary["official_access_option_count"],
            "options_within_snap_warning_threshold": summary[
                "options_within_snap_warning_threshold"
            ],
            "source_mile_conflict_count": summary["source_mile_conflict_count"],
            "manual_snap_review_count": summary["manual_snap_review_count"],
            "all_access_options_conflict_with_published_source_miles": summary[
                "all_access_options_conflict_with_published_source_miles"
            ],
            "primary_access_option_id": primary["option_id"],
            "primary_access_name": primary["name"],
            "primary_access_source_station_miles": primary["source_station_miles"],
            "primary_access_snap_distance_m": primary[
                "nearest_graph_node_distance_m"
            ],
            "official_access_source_station_miles": divergence[
                "official_access_endpoint"
            ]["source_station_miles"],
            "excess_source_path_after_21_miles_m": divergence_summary[
                "excess_source_path_after_21_miles_m"
            ],
            "geodesic_21_mile_point_to_official_access_m": divergence_summary[
                "geodesic_21_mile_point_to_official_access_m"
            ],
            "published_breakpoint_count": len(
                divergence["published_breakpoints_on_official_access_path"]
            ),
        },
        "decision_options": [
            _retain_official_access_with_separate_axis(primary),
            _select_guide_approved_access_option(matrix),
            _replace_route_axis_option(),
            _split_publication_and_simulation_axis_option(primary),
        ],
        "required_decision_record": {
            "decision_id": "south_fork_a1_source_mile_access_authority",
            "must_choose_one_option_id": [
                "retain_official_access_with_separate_simulation_station_axis",
                "select_guide_approved_access_endpoint_and_regenerate_route",
                "replace_current_nhd_axis_with_reviewed_centerline",
                "split_published_mile_convention_from_simulation_and_publication_axes",
            ],
            "required_fields": [
                "chosen_option_id",
                "decision_owner",
                "decision_date",
                "selected_downstream_endpoint_lon_lat_or_centerline_geometry",
                "endpoint_source_authority",
                "simulation_station_axis_policy",
                "published_mile_convention_policy",
                "guide_reviewer",
                "geospatial_reviewer",
                "rights_publication_reviewer",
                "reservoir_stage_or_access_assumptions",
                "route_regeneration_scope",
            ],
            "blocks": [
                "promoting the South Fork full-reach route",
                "cropping the final downstream corridor",
                "regenerating full-reach corridor windows from a selected endpoint",
                "restationing all 20 South Fork named rapids",
                "binding Meat Grinder or Troublemaker to production geometry",
                "binding any South Fork full-reach solver window",
            ],
        },
        "post_decision_regeneration_plan": [
            {
                "step_id": "a1_regenerate_directed_route",
                "description": (
                    "Regenerate the directed route from Chili Bar to the selected "
                    "endpoint or reviewed centerline axis."
                ),
                "requires_decision_fields": [
                    "chosen_option_id",
                    "selected_downstream_endpoint_lon_lat_or_centerline_geometry",
                    "simulation_station_axis_policy",
                ],
            },
            {
                "step_id": "a1_regenerate_corridor_windows",
                "description": (
                    "Rebuild the full-reach source-window manifest, source-pull "
                    "status, stitched validation, and derivatives against the "
                    "selected route basis."
                ),
                "requires_decision_fields": [
                    "route_regeneration_scope",
                    "reservoir_stage_or_access_assumptions",
                ],
            },
            {
                "step_id": "a1_restation_catalog_and_editor_markers",
                "description": (
                    "Restation all South Fork named rapids and regenerate editor "
                    "markers only after the route/station axis is reviewed."
                ),
                "requires_decision_fields": [
                    "guide_reviewer",
                    "geospatial_reviewer",
                    "published_mile_convention_policy",
                ],
            },
            {
                "step_id": "a1_bind_first_solver_windows",
                "description": (
                    "Bind Meat Grinder and Troublemaker to regenerated production "
                    "geometry and validated C++ water windows."
                ),
                "requires_decision_fields": [
                    "selected_downstream_endpoint_lon_lat_or_centerline_geometry",
                    "simulation_station_axis_policy",
                ],
            },
        ],
        "promotion_gate": {
            "can_promote_current_nhd_route": False,
            "can_select_endpoint_from_decision_packet_alone": False,
            "can_crop_to_final_downstream_anchor": False,
            "can_restation_named_rapids": False,
            "can_import_unreal_full_reach_landscape": False,
            "can_bind_named_rapid_geometry": False,
            "can_bind_solver_windows": False,
        },
    }


def write_south_fork_a1_source_mile_access_decision_packet(
    repo_root: Path,
) -> Path:
    payload = build_south_fork_a1_source_mile_access_decision_packet(repo_root)
    path = repo_root / FULL_REACH_SOURCE_MILE_ACCESS_DECISION_PACKET_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _retain_official_access_with_separate_axis(
    primary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "option_id": "retain_official_access_with_separate_simulation_station_axis",
        "label": (
            "Use the primary official Salmon Falls access lead as the physical "
            "downstream endpoint, but separate published guide miles from the "
            "simulation station axis."
        ),
        "uses_primary_official_access": True,
        "endpoint_option_id": primary["option_id"],
        "route_promotion_allowed_without_review": False,
        "requires_route_regeneration": True,
        "risks": [
            "The current NHD path places this endpoint near 30.5 source miles, far beyond the 21.0-mile guide convention.",
            "Published rapid-mile references need a mapping policy instead of direct station equality.",
        ],
    }


def _select_guide_approved_access_option(matrix: dict[str, Any]) -> dict[str, Any]:
    return {
        "option_id": "select_guide_approved_access_endpoint_and_regenerate_route",
        "label": (
            "Pick the exact guide/geospatial-approved Salmon Falls, Skunk Hollow, "
            "or nearby bank endpoint and regenerate all route/window products."
        ),
        "candidate_option_ids": [
            option["option_id"] for option in matrix["official_access_options"]
        ],
        "route_promotion_allowed_without_review": False,
        "requires_route_regeneration": True,
        "risks": [
            "Every current official access option conflicts with the published 20.5/21.0-mile conventions.",
            "One access lead also exceeds the manual snap-review threshold and cannot be used without geometry review.",
        ],
    }


def _replace_route_axis_option() -> dict[str, Any]:
    return {
        "option_id": "replace_current_nhd_axis_with_reviewed_centerline",
        "label": (
            "Reject the current NHD station axis and replace it with a reviewed "
            "centerline or alternate official hydrography before route promotion."
        ),
        "uses_primary_official_access": "decision_dependent",
        "route_promotion_allowed_without_review": False,
        "requires_route_regeneration": True,
        "risks": [
            "Requires a new source authority or hand-reviewed centerline with CRS, source, and reviewer provenance.",
            "All existing source-window station assignments must be regenerated against the replacement axis.",
        ],
    }


def _split_publication_and_simulation_axis_option(
    primary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "option_id": "split_published_mile_convention_from_simulation_and_publication_axes",
        "label": (
            "Treat published 20.5/21.0 miles as public/guide conventions, use a "
            "reviewed physical endpoint for simulation, and maintain an explicit "
            "publication-sensitivity mapping between the two."
        ),
        "uses_primary_official_access": True,
        "endpoint_option_id": primary["option_id"],
        "route_promotion_allowed_without_review": False,
        "requires_route_regeneration": True,
        "risks": [
            "Requires careful UI/editor labeling so guide-source miles do not appear as exact GIS chainage.",
            "Requires rights/publication review before exposing route-detail screenshots or precise access geometry.",
        ],
    }
