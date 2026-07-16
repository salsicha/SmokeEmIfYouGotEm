import json
from pathlib import Path

from raftsim.south_fork_a1_stationing import (
    A1_STATUS_RELATIVE_PATH,
    build_south_fork_a1_stationing_repair_status,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_status() -> dict:
    return json.loads((REPO_ROOT / A1_STATUS_RELATIVE_PATH).read_text(encoding="utf-8"))


def test_south_fork_a1_stationing_status_is_reproducible():
    generated = build_south_fork_a1_stationing_repair_status(REPO_ROOT)
    committed = _load_status()

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_stationing_repair_status.v1"
    assert (
        committed["status"]
        == "blocked_pending_full_reach_hydrography_exact_anchors_and_guide_review"
    )
    assert committed["production_promoted"] is False
    assert "exact rapid geometry" in committed["do_not_use_for"]


def test_south_fork_a1_preserves_published_mile_scaffold_without_geometry_promotion():
    status = _load_status()
    scaffold = status["catalog_stationing_scaffold"]

    assert scaffold["stationing_authority"] == "published_river_miles"
    assert scaffold["rapid_count"] == 20
    assert scaffold["rapid_mile_min"] == 0.0
    assert scaffold["rapid_mile_max"] == 19.3
    assert scaffold["downstreammost_catalog_rapid"] == "Surprise"
    assert scaffold["all_rapids_have_published_miles"] is True
    assert scaffold["run_length_m"] == 33796.224

    rapid_names = [rapid["name"] for rapid in scaffold["rapid_stations"]]
    assert rapid_names[:2] == ["Chili Bar Hole", "Meat Grinder"]
    assert "Troublemaker" in rapid_names
    assert rapid_names[-1] == "Surprise"
    assert {
        rapid["exact_geometry_status"] for rapid in scaffold["rapid_stations"]
    } == {"blocked_pending_full_reach_centerline_and_guide_review"}


def test_south_fork_a1_records_current_geometry_conflict_and_slice_coverage():
    status = _load_status()
    geometry = status["current_geometry_evidence"]
    coverage = status["current_source_coverage"]

    assert geometry["alignment_status"] == "failed_alignment_binding_disabled"
    assert geometry["candidate_declared_length_m"] == 26204.692
    assert geometry["published_chili_bar_to_coloma_length_m"] == 9012.3264
    assert geometry["candidate_to_published_coloma_length_ratio"] > 2.9
    assert geometry["access_seed_to_published_coloma_delta_m"] > 3800.0
    assert geometry["candidate_covers_catalog_full_run_length"] is False
    assert geometry["geometry_binding_enabled"] is False

    assert coverage["nhd_extract_is_full_reach"] is False
    assert coverage["production_corridor_reach_id"] == "chili_bar_0_2500m"
    assert (
        coverage["production_corridor_local_centerline_status"]
        == "source_aligned_review_gated_not_gameplay_authority"
    )
    assert coverage["production_corridor_point_count"] == 799
    assert coverage["production_corridor_station_range_m"] == [0.0, 2531.325]
    assert "0-2.5 km Chili Bar slice" in coverage["coverage_blocker"]


def test_south_fork_a1_records_review_gated_flow_evidence_and_exit_blocker():
    status = _load_status()
    flow = status["flow_evidence"]
    acceptance = {
        entry["requirement"]: entry["status"] for entry in status["a1_acceptance"]
    }

    assert flow["primary_candidate"] == "CDEC CBR American River at Chili Bar"
    assert flow["secondary_context"] == "CDEC A25 Chili Bar Powerhouse"
    assert flow["reviewed_band_count"] == 3
    assert [band["flow_band"] for band in flow["reviewed_bands"]] == [
        "low_runnable",
        "median_runnable",
        "high_runnable",
    ]
    assert [band["planning_discharge_cfs"] for band in flow["reviewed_bands"]] == [
        900.0,
        1600.0,
        3000.0,
    ]
    assert {band["promotion_decision"] for band in flow["reviewed_bands"]} == {
        "blocked_pending_broader_windows_release_context_station_routing_guide_review"
    }

    assert acceptance[
        "Fix NHD flowline conflict and re-anchor Chili Bar plus Folsom take-out."
    ] == "blocked"
    assert acceptance[
        "Extend corridor to the full Chili Bar-to-Folsom reach."
    ] == "blocked"
    assert acceptance["Attach official low/reference/high flow bands."] == (
        "attached_but_review_gated"
    )
    assert acceptance[
        "Re-station all 20 catalog markers with no order interpolation."
    ] == "published_mile_scaffold_ready_exact_geometry_blocked"
    assert acceptance[
        "Exit gate: conflict resolved and zero South Fork markers use order interpolation."
    ] == "not_met"
