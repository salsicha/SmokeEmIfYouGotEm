import json
from pathlib import Path

from raftsim.south_fork_a1_downstream_access_review import (
    FULL_REACH_DOWNSTREAM_ACCESS_REVIEW_RELATIVE_PATH,
    build_south_fork_a1_downstream_access_publication_review,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_review() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_DOWNSTREAM_ACCESS_REVIEW_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_downstream_access_review_is_reproducible():
    generated = build_south_fork_a1_downstream_access_publication_review(REPO_ROOT)
    committed = _load_review()

    assert generated == committed
    assert (
        committed["schema"]
        == "raftsim.south_fork.a1_downstream_access_publication_review.v1"
    )
    assert (
        committed["status"]
        == "official_downstream_access_source_leads_attached_exact_geometry_pending"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_downstream_access_review_records_official_source_leads():
    review = _load_review()
    sources = {source["source_id"]: source for source in review["sources_checked"]}

    assert len(sources) == 4
    assert "ca_state_parks_dbw_salmon_falls_btaf" in sources
    assert "ca_state_parks_dbw_american_south_fork_facilities" in sources
    assert "blm_south_fork_american_river" in sources
    assert "ca_state_parks_folsom_lake_boat_launch_status" in sources
    assert sources["ca_state_parks_dbw_salmon_falls_btaf"]["http_status"] == 200
    assert sources["ca_state_parks_dbw_salmon_falls_btaf"]["rights_status"] == (
        "link_only_factual_index"
    )
    assert "American River-South Fork" in " ".join(
        sources["ca_state_parks_dbw_salmon_falls_btaf"]["evidence"]
    )
    assert "Salmon Falls Bridge" in " ".join(
        sources["blm_south_fork_american_river"]["evidence"]
    )


def test_south_fork_a1_downstream_access_review_supports_both_candidates_without_promoting():
    review = _load_review()
    support = {item["option_id"]: item for item in review["candidate_support"]}

    assert set(support) == {
        "select_20_5_mile_salmon_falls_basis",
        "select_21_0_mile_full_run_folsom_basis",
    }
    assert "ca_state_parks_dbw_salmon_falls_btaf" in support[
        "select_20_5_mile_salmon_falls_basis"
    ]["supporting_sources"]
    assert "blm_south_fork_american_river" in support[
        "select_21_0_mile_full_run_folsom_basis"
    ]["supporting_sources"]
    for item in support.values():
        assert item["still_required"]
        assert item["support_status"].endswith("pending")


def test_south_fork_a1_downstream_access_review_blocks_promotion_and_publication_authority():
    review = _load_review()
    gate = review["promotion_gate"]

    assert gate["can_select_downstream_anchor"] is False
    assert gate["can_crop_to_final_downstream_anchor"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_restation_named_rapids"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
    assert "final access geometry" in review["forbidden_use"]
    assert "public route-detail screenshots without review" in review["forbidden_use"]
