import json
from pathlib import Path

from raftsim.chilko_a5_digitizing_windows import (
    CHILKO_A5_DIGITIZING_WORK_WINDOW_MANIFEST_RELATIVE_PATH,
    CHILKO_A5_DIGITIZING_WORK_WINDOW_MANIFEST_SCHEMA,
    CHILKO_A5_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH,
    CHILKO_A5_DIGITIZING_WORK_WINDOWS_SCHEMA,
    build_chilko_a5_digitizing_work_window_manifest,
    build_chilko_a5_digitizing_work_windows_geojson,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_geojson() -> dict:
    return json.loads(
        (REPO_ROOT / CHILKO_A5_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_manifest() -> dict:
    return json.loads(
        (REPO_ROOT / CHILKO_A5_DIGITIZING_WORK_WINDOW_MANIFEST_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_chilko_a5_digitizing_work_windows_geojson_is_reproducible():
    generated = build_chilko_a5_digitizing_work_windows_geojson(REPO_ROOT)
    committed = _load_geojson()

    assert generated == committed
    assert committed["schema"] == CHILKO_A5_DIGITIZING_WORK_WINDOWS_SCHEMA
    assert committed["type"] == "FeatureCollection"
    assert committed["status"] == (
        "review_only_digitizing_windows_on_route_scaffold_not_authoritative"
    )
    assert committed["production_promoted"] is False
    assert len(committed["features"]) == 5


def test_chilko_a5_digitizing_work_windows_cover_every_priority_rapid_with_lines():
    geojson = _load_geojson()
    features = {feature["properties"]["rapid_name"]: feature for feature in geojson["features"]}

    assert set(features) == {
        "Bidwell Rapids",
        "Lava Canyon",
        "White Mile",
        "Green Mile",
        "Miracle Canyon",
    }
    for feature in features.values():
        assert feature["geometry"]["type"] == "LineString"
        assert len(feature["geometry"]["coordinates"]) >= 8
        assert feature["properties"]["stationing_status"] == (
            "order_distributed_route_work_window_not_authoritative"
        )
        assert feature["properties"]["geometry_status"] == (
            "review_focus_window_not_exact_rapid_geometry"
        )
        assert feature["properties"]["current_stationing_kind"] == (
            "provisional_downstream_order_interpolation"
        )


def test_chilko_a5_digitizing_work_windows_record_route_order_mapping():
    geojson = _load_geojson()
    features = {feature["properties"]["rapid_name"]: feature for feature in geojson["features"]}

    bidwell = features["Bidwell Rapids"]["properties"]
    assert bidwell["current_station_m_from_order_interpolation"] == 9307.616
    assert bidwell["route_order_station_m"] == 9307.616
    assert bidwell["window_start_m"] == 8407.616
    assert bidwell["window_end_m"] == 10207.616
    assert bidwell["half_length_m"] == 900.0
    assert bidwell["lateral_review_buffer_m"] == 180.0

    lava = features["Lava Canyon"]["properties"]
    assert lava["review_priority"] == "critical"
    assert lava["half_length_m"] == 900.0

    green = features["Green Mile"]["properties"]
    assert green["review_priority"] == "high"
    assert green["half_length_m"] == 650.0
    assert green["lateral_review_buffer_m"] == 140.0


def test_chilko_a5_digitizing_work_window_manifest_is_reproducible_and_blocked():
    generated = build_chilko_a5_digitizing_work_window_manifest(REPO_ROOT)
    committed = _load_manifest()

    assert generated == committed
    assert committed["schema"] == CHILKO_A5_DIGITIZING_WORK_WINDOW_MANIFEST_SCHEMA
    assert committed["status"] == (
        "work_windows_ready_for_manual_digitizing_review_no_stationing_promotion"
    )
    assert committed["production_promoted"] is False
    assert committed["rapid_count"] == 5
    assert committed["critical_window_count"] == 3
    assert committed["route_stationing_length_m"] == 55845.69567955752
    assert committed["catalog_run_length_m"] == 55845.696
    gate = committed["promotion_gate"]
    assert gate["can_replace_order_interpolation"] is False
    assert gate["can_regenerate_named_rapid_catalog"] is False
    assert gate["can_bind_editor_geometry"] is False
    assert gate["can_generate_rapid_water_windows"] is False
    assert gate["can_bind_solver_windows"] is False


def test_chilko_a5_digitizing_work_window_manifest_summarizes_window_coordinates():
    manifest = _load_manifest()
    windows = {window["rapid_name"]: window for window in manifest["windows"]}

    assert windows["White Mile"]["review_priority"] == "critical"
    assert windows["White Mile"]["coordinate_count"] >= 20
    assert windows["Miracle Canyon"]["window_end_m"] <= manifest["route_stationing_length_m"]
    assert all(window["window_start_m"] < window["window_end_m"] for window in windows.values())
