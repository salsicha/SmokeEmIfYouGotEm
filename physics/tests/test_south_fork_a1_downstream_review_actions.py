import json
from pathlib import Path

from raftsim.south_fork_a1_downstream_review_actions import (
    FULL_REACH_DOWNSTREAM_ANCHOR_REVIEW_ACTIONS_RELATIVE_PATH,
    build_south_fork_a1_downstream_anchor_review_actions,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_actions() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_DOWNSTREAM_ANCHOR_REVIEW_ACTIONS_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_downstream_review_actions_are_reproducible():
    generated = build_south_fork_a1_downstream_anchor_review_actions(REPO_ROOT)
    committed = _load_actions()

    assert generated == committed
    assert (
        committed["schema"]
        == "raftsim.south_fork.a1_downstream_anchor_review_actions.v1"
    )
    assert (
        committed["status"]
        == "editor_geospatial_review_actions_ready_exact_anchor_pending"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_downstream_review_actions_bind_real_evidence_paths():
    actions = _load_actions()
    evidence = actions["evidence_bundle"]

    assert evidence["candidate_geojson"]["feature_count"] == 3
    assert evidence["candidate_geojson"]["geometry_type_counts"] == {
        "LineString": 1,
        "Point": 2,
    }
    assert evidence["candidate_geojson"]["candidate_option_ids"] == [
        "select_20_5_mile_salmon_falls_basis",
        "select_21_0_mile_full_run_folsom_basis",
    ]
    assert len(evidence["official_source_leads"]) == 4
    assert evidence["station_delta_m"] == 804.672

    review_windows = {window["role"]: window for window in evidence["review_windows"]}
    assert set(review_windows) == {"anchor_review_window", "lower_gorge_window"}
    for window in review_windows.values():
        assert len(window["required_artifacts"]) == 4
        for artifact in window["required_artifacts"]:
            assert len(artifact["sha256"]) == 64
            assert (REPO_ROOT / artifact["path"]).exists()


def test_south_fork_a1_downstream_review_actions_define_all_required_decisions():
    actions = _load_actions()

    roles = {role["role_id"] for role in actions["required_review_roles"]}
    assert roles == {
        "geospatial_or_technical_art_reviewer",
        "river_guide_or_oarsman_domain_reviewer",
        "rights_or_publication_sensitivity_reviewer",
        "owner_or_producer_acceptance",
    }
    assert [action["action_id"] for action in actions["action_sequence"]] == [
        "load_evidence_bundle",
        "verify_official_access_context",
        "resolve_source_mile_convention",
        "record_exact_anchor_geometry",
        "record_publication_sensitivity",
        "record_reviewer_signoff",
        "regenerate_after_approval_only",
    ]
    template = actions["review_result_template"]
    assert template["selected_option_id"] == ""
    assert template["exact_anchor_lon_lat"] == []
    assert template["production_promoted"] is False
    for reviewer in template["reviewers"].values():
        assert reviewer["approved"] is False


def test_south_fork_a1_downstream_review_actions_block_promotion_until_review_result_exists():
    actions = _load_actions()
    gate = actions["promotion_gate"]

    assert gate["can_select_downstream_anchor_from_this_packet_alone"] is False
    assert gate["can_crop_to_final_downstream_anchor"] is False
    assert gate["can_promote_full_reach_centerline"] is False
    assert gate["can_restation_named_rapids"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
    assert len(gate["complete_when"]) == 4
