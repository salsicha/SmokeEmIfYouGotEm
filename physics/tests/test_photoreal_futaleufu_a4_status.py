import json
from pathlib import Path

from raftsim.futaleufu_a4_status import (
    FUTALEUFU_A4_STATUS_RELATIVE_PATH,
    FUTALEUFU_A4_STATUS_SCHEMA,
    FUTALEUFU_RIVER_ID,
    build_futaleufu_a4_stationing_flow_status,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_status() -> dict:
    return json.loads(
        (REPO_ROOT / FUTALEUFU_A4_STATUS_RELATIVE_PATH).read_text(encoding="utf-8")
    )


def test_futaleufu_a4_status_is_reproducible_and_fail_closed():
    generated = build_futaleufu_a4_stationing_flow_status(REPO_ROOT)
    committed = _load_status()

    assert generated == committed
    assert committed["schema"] == FUTALEUFU_A4_STATUS_SCHEMA
    assert committed["river_id"] == FUTALEUFU_RIVER_ID
    assert committed["status"] == (
        "blocked_pending_exact_rapid_stationing_dga_route_translation_and_guide_review"
    )
    assert committed["production_promoted"] is False
    assert committed["exact_stationing_promoted"] is False
    assert committed["flow_bands_promoted"] is False
    assert committed["editor_binding_allowed"] is False
    assert committed["solver_window_binding_allowed"] is False


def test_futaleufu_a4_status_tracks_order_only_named_rapids():
    status = _load_status()
    scaffold = status["catalog_stationing_scaffold"]
    records = {rapid["name"]: rapid for rapid in scaffold["rapid_stations"]}

    assert scaffold["stationing_authority"] == "published_order_only_route_length_approximate"
    assert scaffold["catalog_run_length_m"] == 10000.0
    assert scaffold["route_stationing_length_m"] == 15936.77551712958
    assert scaffold["route_to_catalog_length_ratio"] > 1.59
    assert scaffold["rapid_count"] == 5
    assert scaffold["critical_rapid_count"] == 4
    assert scaffold["all_rapids_are_order_only"] is True
    assert set(records) == {
        "Asleep at the Wheel",
        "Terminator",
        "Son of Terminator",
        "Khyber Pass",
        "Himalayas",
    }
    assert records["Terminator"]["catalog_station_m_from_order_interpolation"] == 3333.333
    assert records["Terminator"]["route_order_station_m_for_review_focus"] == 5312.259
    assert records["Khyber Pass"]["aliases"] == ["Kyber Pass", "Kipper Pass"]
    assert records["Himalayas"]["stationing_kind"] == (
        "provisional_downstream_order_interpolation"
    )


def test_futaleufu_a4_status_preserves_corridor_evidence_without_binding():
    status = _load_status()
    corridor = status["current_corridor_evidence"]

    assert corridor["corridor_status"] == "source_scale_technical_corridor_not_yet_lifelike"
    assert corridor["route_stationing_schema"] == "raftsim.route_stationing.v1"
    assert corridor["route_length_m"] == 15936.776
    assert corridor["route_sample_count"] == 205
    assert corridor["geometry_authority"] == (
        "osm_named_river_cross_reference_with_rapid_tags_not_surveyed_centerline"
    )
    assert corridor["guide_approval"] is None
    assert corridor["editor_geometry_binding_enabled_in_catalog"] is True
    assert corridor["editor_geometry_binding_allowed_by_a4"] is False


def test_futaleufu_a4_status_records_dga_flow_evidence_as_review_gated():
    status = _load_status()
    flow = status["flow_evidence"]

    assert flow["provider"] == "Direccion General de Aguas, Chile"
    assert flow["station"] == "Rio Futaleufu ante junta rio Malito"
    assert flow["station_code"] == "10704002-1"
    assert flow["units"] == "m3/s"
    assert flow["planning_band_count"] == 4
    assert flow["numeric_ranges_present"] is True
    assert flow["numeric_flow_bands_promoted"] is False
    assert "route translation and travel-time review required" in flow["relation_to_reach"]
    assert "review-only" in flow["promotion_gate"]


def test_futaleufu_a4_acceptance_and_promotion_gates_remain_closed():
    status = _load_status()
    acceptance = {
        item["requirement"]: item["status"] for item in status["a4_acceptance"]
    }

    assert acceptance[
        "Exact stationing for Terminator, Khyber Pass, Himalayas, and other catalog markers."
    ] == "not_met"
    assert acceptance[
        "DGA Chile gauge research and flow bands reviewed for the game reach."
    ] == "partial_review_gated"
    assert acceptance[
        "Exit gate: no Futaleufu marker uses provisional order interpolation."
    ] == "not_met"
    gate = status["promotion_gate"]
    assert gate["can_promote_a4_stationing"] is False
    assert gate["can_promote_a4_flow_bands"] is False
    assert gate["can_bind_editor_geometry"] is False
    assert gate["can_generate_rapid_water_windows"] is False
    assert gate["can_bind_solver_windows"] is False
