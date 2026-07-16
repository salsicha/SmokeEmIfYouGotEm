import json
from pathlib import Path

from raftsim.pacuare_a3_stationing import (
    PACUARE_A3_STATIONING_STATUS_RELATIVE_PATH,
    PACUARE_A3_STATIONING_STATUS_SCHEMA,
    PACUARE_RIVER_ID,
    build_pacuare_a3_stationing_repair_status,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_status() -> dict:
    return json.loads(
        (REPO_ROOT / PACUARE_A3_STATIONING_STATUS_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_pacuare_a3_stationing_status_is_reproducible_and_fail_closed():
    generated = build_pacuare_a3_stationing_repair_status(REPO_ROOT)
    committed = _load_status()

    assert generated == committed
    assert committed["schema"] == PACUARE_A3_STATIONING_STATUS_SCHEMA
    assert committed["river_id"] == PACUARE_RIVER_ID
    assert committed["status"] == (
        "blocked_pending_official_hydrography_aerial_stationing_and_guide_review"
    )
    assert committed["production_promoted"] is False
    assert committed["exact_stationing_promoted"] is False
    assert committed["editor_binding_allowed"] is False
    assert committed["solver_window_binding_allowed"] is False


def test_pacuare_a3_stationing_status_tracks_all_order_only_rapids():
    status = build_pacuare_a3_stationing_repair_status(REPO_ROOT)
    scaffold = status["catalog_stationing_scaffold"]
    records = {rapid["name"]: rapid for rapid in scaffold["rapid_stations"]}

    assert scaffold["stationing_authority"] == "published_map_order_only"
    assert scaffold["rapid_count"] == 15
    assert scaffold["critical_rapid_count"] == 6
    assert scaffold["all_rapids_are_order_only"] is True
    assert set(records) == {
        "Bienvenidos",
        "Pyramid Rock",
        "Pele El Ojo",
        "Upper Huacas",
        "Bobo Falls",
        "Lower Huacas",
        "Rodeo",
        "Guatemala",
        "Double Drop",
        "Cimarrones",
        "Upper Pinball",
        "Lower Pinball",
        "Wall of Sorrow",
        "Dos Montanas",
        "Las Ranitas",
    }
    assert records["Upper Huacas"]["stationing_kind"] == (
        "provisional_downstream_order_interpolation"
    )
    assert records["Upper Huacas"]["station_m_from_order_interpolation"] == 6562.5
    assert records["Dos Montanas"]["aliases"] == ["Dos Montañas"]
    assert records["Dos Montanas"]["exact_geometry_status"] == (
        "blocked_pending_aerial_digitizing_and_guide_review"
    )


def test_pacuare_a3_status_records_preview_scaffold_length_mismatch():
    status = build_pacuare_a3_stationing_repair_status(REPO_ROOT)
    geometry = status["current_geometry_evidence"]

    assert geometry["preview_centerline_status"] == (
        "generated_review_gated_preview_route_not_official_hydrography"
    )
    assert geometry["preview_stationing_review_status"] == (
        "preview_metric_stationing_review_required_not_final_crs_or_official_route"
    )
    assert geometry["catalog_run_length_m"] == 26250.0
    assert geometry["preview_length_m"] == 45642.42
    assert geometry["preview_to_catalog_length_ratio"] > 1.7
    assert geometry["preview_length_matches_catalog_run"] is False
    assert geometry["geometry_binding_enabled"] is False


def test_pacuare_a3_status_keeps_flow_and_source_reviews_unpromoted():
    status = build_pacuare_a3_stationing_repair_status(REPO_ROOT)
    flow = status["flow_evidence"]
    source_inputs = {item["source_class"]: item for item in status["source_review_inputs"]}

    assert flow["flow_status"] == (
        "planning_placeholders_require_costa_rica_hydrology_rainfall_and_guide_review"
    )
    assert flow["numeric_discharge_values_allowed"] is False
    assert flow["flow_band_count"] == 4
    assert "authoritative_gauge_or_stage_history" in flow["hydrology_review_needs"]
    assert source_inputs["official_hydrography_access"]["status"] == (
        "lead_recorded_not_route_authority"
    )
    assert source_inputs["sentinel_corridor_imagery"]["status"] == (
        "review_imagery_available_not_exact_rapid_stationing"
    )
    assert source_inputs["hydrology_gauge_search"]["status"] == (
        "review_leads_recorded_no_numeric_flow_promotion"
    )


def test_pacuare_a3_acceptance_remains_not_met_until_reviewed_stationing():
    status = build_pacuare_a3_stationing_repair_status(REPO_ROOT)
    acceptance = {
        item["requirement"]: item["status"] for item in status["a3_acceptance"]
    }

    assert acceptance["Replace order-interpolated stations for all 15 markers."] == (
        "not_met"
    )
    assert acceptance["Terrain and imagery source class recorded."] == (
        "partial_review_gated"
    )
    assert acceptance["Flow bands recorded with source class."] == (
        "planning_placeholders_only"
    )
    assert acceptance[
        "Exit gate: no Pacuare marker uses provisional order interpolation."
    ] == "not_met"
    gate = status["promotion_gate"]
    assert gate["can_promote_a3_stationing"] is False
    assert gate["can_bind_editor_geometry"] is False
    assert gate["can_generate_rapid_water_windows"] is False
    assert gate["can_bind_solver_windows"] is False
