import json
from pathlib import Path

from raftsim.south_fork_a1_source_mile_access_decision import (
    FULL_REACH_SOURCE_MILE_ACCESS_DECISION_PACKET_RELATIVE_PATH,
    build_south_fork_a1_source_mile_access_decision_packet,
)
from raftsim.south_fork_a1_source_mile_access_decision_result import (
    FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_RELATIVE_PATH,
    FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_SCHEMA,
    FULL_REACH_SOURCE_MILE_ACCESS_DECISION_VALIDATION_REPORT_RELATIVE_PATH,
    FULL_REACH_SOURCE_MILE_ACCESS_DECISION_VALIDATION_REPORT_SCHEMA,
    build_south_fork_a1_source_mile_access_decision_result_template,
    build_south_fork_a1_source_mile_access_decision_validation_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_template() -> dict:
    return json.loads(
        (
            REPO_ROOT
            / FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def _load_validation_report() -> dict:
    return json.loads(
        (
            REPO_ROOT
            / FULL_REACH_SOURCE_MILE_ACCESS_DECISION_VALIDATION_REPORT_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_south_fork_a1_source_mile_access_decision_result_template_is_reproducible():
    generated = build_south_fork_a1_source_mile_access_decision_result_template(
        REPO_ROOT
    )
    committed = _load_template()

    assert generated == committed
    assert committed["schema"] == (
        FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_SCHEMA
    )
    assert committed["status"] == "empty_decision_result_template_no_route_promotion"
    assert committed["production_promoted"] is False
    assert committed["source_decision_packet"] == (
        FULL_REACH_SOURCE_MILE_ACCESS_DECISION_PACKET_RELATIVE_PATH
    )


def test_south_fork_a1_source_mile_access_decision_result_template_matches_packet_options():
    packet = build_south_fork_a1_source_mile_access_decision_packet(REPO_ROOT)
    template = _load_template()

    assert template["allowed_option_ids"] == packet["required_decision_record"][
        "must_choose_one_option_id"
    ]
    assert template["required_filled_fields"] == packet[
        "required_decision_record"
    ]["required_fields"]
    assert template["post_decision_regeneration_plan"] == packet[
        "post_decision_regeneration_plan"
    ]
    assert template["blocked_actions_until_completed_result"] == packet[
        "required_decision_record"
    ]["blocks"]


def test_south_fork_a1_source_mile_access_decision_result_template_is_empty():
    template = _load_template()
    result = template["decision_result"]

    assert result["chosen_option_id"] == ""
    assert result["decision_owner"] == ""
    assert result["decision_date"] == ""
    assert result["decision_status"] == "not_recorded"
    assert result["route_regeneration_scope"] == []
    geometry = result["selected_downstream_endpoint_lon_lat_or_centerline_geometry"]
    assert geometry == {
        "geometry_type": "",
        "coordinates": [],
        "crs": "",
        "source_authority": "",
        "source_report": "",
    }


def test_south_fork_a1_source_mile_access_decision_result_template_requires_all_reviewers():
    template = _load_template()
    expected_roles = {
        "owner_or_producer_acceptance",
        "river_guide_or_oarsman_domain_reviewer",
        "geospatial_reviewer",
        "rights_publication_reviewer",
    }

    assert set(template["required_reviewer_roles"]) == expected_roles
    assert set(template["reviewer_signoff"]) == expected_roles
    for role in template["reviewer_signoff"].values():
        assert role["name_or_role"] == ""
        assert role["review_date"] == ""
        assert role["approved"] is False
        assert role["evidence"] == []


def test_south_fork_a1_source_mile_access_decision_result_template_blocks_a1_promotion():
    template = _load_template()
    gate = template["promotion_gate"]
    contract = template["validation_contract"]

    assert contract["template_is_empty"] is True
    assert contract["chosen_option_must_be_allowed"] is True
    assert contract["all_required_fields_must_be_populated"] is True
    assert contract["all_reviewer_roles_must_approve"] is True
    assert contract["may_promote_current_route_from_empty_template"] is False
    assert contract["may_regenerate_corridor_windows_from_empty_template"] is False
    assert contract["may_bind_solver_windows_from_empty_template"] is False
    assert gate["can_promote_current_nhd_route"] is False
    assert gate["can_select_endpoint_from_empty_template"] is False
    assert gate["can_crop_to_final_downstream_anchor"] is False
    assert gate["can_restation_named_rapids"] is False
    assert gate["can_bind_solver_windows"] is False


def test_south_fork_a1_source_mile_access_decision_validation_report_is_reproducible():
    generated = build_south_fork_a1_source_mile_access_decision_validation_report(
        REPO_ROOT
    )
    committed = _load_validation_report()

    assert generated == committed
    assert committed["schema"] == (
        FULL_REACH_SOURCE_MILE_ACCESS_DECISION_VALIDATION_REPORT_SCHEMA
    )
    assert committed["status"] == "decision_result_incomplete_route_promotion_blocked"
    assert committed["decision_valid"] is False
    assert committed["production_promoted"] is False


def test_south_fork_a1_source_mile_access_decision_validation_blocks_empty_template():
    report = _load_validation_report()

    assert report["validation_error_count"] > 0
    assert set(report["missing_required_fields"]) == {
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
    }
    assert {failure["role"] for failure in report["reviewer_failures"]} == {
        "owner_or_producer_acceptance",
        "river_guide_or_oarsman_domain_reviewer",
        "geospatial_reviewer",
        "rights_publication_reviewer",
    }
    permissions = report["regeneration_permissions"]
    assert permissions["can_regenerate_directed_route"] is False
    assert permissions["can_restation_named_rapids"] is False
    assert permissions["can_bind_solver_windows"] is False


def test_south_fork_a1_source_mile_access_decision_validation_accepts_complete_result():
    payload = _complete_decision_payload()
    report = build_south_fork_a1_source_mile_access_decision_validation_report(
        REPO_ROOT,
        payload,
    )

    assert report["status"] == "decision_result_valid_manual_regeneration_allowed"
    assert report["decision_valid"] is True
    assert report["validation_error_count"] == 0
    assert report["missing_required_fields"] == []
    assert report["invalid_fields"] == []
    assert report["reviewer_failures"] == []
    assert report["regeneration_permissions"]["can_regenerate_directed_route"] is True
    assert report["regeneration_permissions"]["can_bind_solver_windows"] is True
    assert report["regeneration_permissions"]["can_promote_current_nhd_route"] is False
    assert report["promotion_gate"][
        "can_promote_current_route_without_regenerated_artifacts"
    ] is False


def test_south_fork_a1_source_mile_access_decision_validation_rejects_bad_option():
    payload = _complete_decision_payload()
    payload["decision_result"]["chosen_option_id"] = "not_allowed"
    report = build_south_fork_a1_source_mile_access_decision_validation_report(
        REPO_ROOT,
        payload,
    )

    assert report["decision_valid"] is False
    assert {"field": "chosen_option_id", "reason": "option_id_not_allowed"} in report[
        "invalid_fields"
    ]


def _complete_decision_payload() -> dict:
    payload = build_south_fork_a1_source_mile_access_decision_result_template(
        REPO_ROOT
    )
    payload["decision_result"].update(
        {
            "chosen_option_id": payload["allowed_option_ids"][0],
            "decision_owner": "owner-review",
            "decision_date": "2026-07-16",
            "decision_status": "approved",
            "selected_downstream_endpoint_lon_lat_or_centerline_geometry": {
                "geometry_type": "Point",
                "coordinates": [-121.0, 38.0],
                "crs": "EPSG:4326",
                "source_authority": "reviewed field/GIS point",
                "source_report": "review/example_source_mile_access_decision_source.json",
            },
            "endpoint_source_authority": "reviewed field/GIS point",
            "simulation_station_axis_policy": "separate physical endpoint chainage",
            "published_mile_convention_policy": "guide miles mapped separately",
            "reservoir_stage_or_access_assumptions": "reviewed normal access stage",
            "route_regeneration_scope": [
                "directed_route",
                "corridor_windows",
                "rapid_stationing",
                "solver_windows",
            ],
        }
    )
    for role in payload["reviewer_signoff"].values():
        role.update(
            {
                "name_or_role": "reviewer",
                "review_date": "2026-07-16",
                "approved": True,
                "evidence": ["review/example_evidence.json"],
                "notes": "synthetic complete test payload",
            }
        )
    return payload
