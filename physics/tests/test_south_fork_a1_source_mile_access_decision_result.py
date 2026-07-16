import json
from pathlib import Path

from raftsim.south_fork_a1_source_mile_access_decision import (
    FULL_REACH_SOURCE_MILE_ACCESS_DECISION_PACKET_RELATIVE_PATH,
    build_south_fork_a1_source_mile_access_decision_packet,
)
from raftsim.south_fork_a1_source_mile_access_decision_result import (
    FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_RELATIVE_PATH,
    FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_SCHEMA,
    build_south_fork_a1_source_mile_access_decision_result_template,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_template() -> dict:
    return json.loads(
        (
            REPO_ROOT
            / FULL_REACH_SOURCE_MILE_ACCESS_DECISION_RESULT_TEMPLATE_RELATIVE_PATH
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
