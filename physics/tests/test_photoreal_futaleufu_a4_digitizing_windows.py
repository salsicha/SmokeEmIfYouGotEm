import json
from pathlib import Path

from raftsim.futaleufu_a4_digitizing_windows import (
    FUTALEUFU_A4_DIGITIZING_WORK_WINDOW_MANIFEST_RELATIVE_PATH,
    FUTALEUFU_A4_DIGITIZING_WORK_WINDOW_MANIFEST_SCHEMA,
    FUTALEUFU_A4_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH,
    FUTALEUFU_A4_DIGITIZING_WORK_WINDOWS_SCHEMA,
    build_futaleufu_a4_digitizing_work_window_manifest,
    build_futaleufu_a4_digitizing_work_windows_geojson,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_geojson() -> dict:
    return json.loads(
        (REPO_ROOT / FUTALEUFU_A4_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_manifest() -> dict:
    return json.loads(
        (
            REPO_ROOT / FUTALEUFU_A4_DIGITIZING_WORK_WINDOW_MANIFEST_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_futaleufu_a4_digitizing_work_windows_geojson_is_reproducible():
    generated = build_futaleufu_a4_digitizing_work_windows_geojson(REPO_ROOT)
    committed = _load_geojson()

    assert generated == committed
    assert committed["schema"] == FUTALEUFU_A4_DIGITIZING_WORK_WINDOWS_SCHEMA
    assert committed["type"] == "FeatureCollection"
    assert committed["status"] == (
        "review_only_digitizing_windows_on_route_scaffold_not_authoritative"
    )
    assert len(committed["features"]) == 5


def test_futaleufu_a4_digitizing_work_windows_cover_every_rapid_with_lines():
    geojson = _load_geojson()
    features = {feature["properties"]["rapid_name"]: feature for feature in geojson["features"]}

    assert set(features) == {
        "Asleep at the Wheel",
        "Terminator",
        "Son of Terminator",
        "Khyber Pass",
        "Himalayas",
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


def test_futaleufu_a4_digitizing_work_windows_record_route_order_mapping():
    geojson = _load_geojson()
    features = {feature["properties"]["rapid_name"]: feature for feature in geojson["features"]}

    terminator = features["Terminator"]["properties"]
    assert terminator["catalog_order_station_m"] == 3333.333
    assert terminator["route_order_station_m"] == 5312.259
    assert terminator["window_start_m"] == 4512.259
    assert terminator["window_end_m"] == 6112.259
    assert terminator["half_length_m"] == 800.0
    assert terminator["lateral_review_buffer_m"] == 180.0

    asleep = features["Asleep at the Wheel"]["properties"]
    assert asleep["half_length_m"] == 600.0
    assert asleep["lateral_review_buffer_m"] == 140.0

    khyber = features["Khyber Pass"]["properties"]
    assert khyber["aliases"] == ["Kyber Pass", "Kipper Pass"]
    assert khyber["window_id"] == "futaleufu_a4_window_04_khyber_pass"


def test_futaleufu_a4_digitizing_work_window_manifest_is_reproducible_and_blocked():
    generated = build_futaleufu_a4_digitizing_work_window_manifest(REPO_ROOT)
    committed = _load_manifest()

    assert generated == committed
    assert committed["schema"] == FUTALEUFU_A4_DIGITIZING_WORK_WINDOW_MANIFEST_SCHEMA
    assert committed["status"] == (
        "work_windows_ready_for_manual_digitizing_review_no_stationing_promotion"
    )
    assert committed["production_promoted"] is False
    assert committed["rapid_count"] == 5
    assert committed["critical_window_count"] == 4
    assert committed["route_stationing_length_m"] == 15936.77551712958
    assert committed["catalog_run_length_m"] == 10000.0
    assert committed["route_to_catalog_length_ratio"] > 1.59
    gate = committed["promotion_gate"]
    assert gate["can_replace_order_interpolation"] is False
    assert gate["can_regenerate_named_rapid_catalog"] is False
    assert gate["can_bind_editor_geometry"] is False
    assert gate["can_generate_rapid_water_windows"] is False
    assert gate["can_bind_solver_windows"] is False


def test_futaleufu_a4_digitizing_work_window_manifest_summarizes_window_coordinates():
    manifest = _load_manifest()
    windows = {window["rapid_name"]: window for window in manifest["windows"]}

    assert windows["Himalayas"]["review_priority"] == "critical"
    assert windows["Himalayas"]["coordinate_count"] >= 18
    assert windows["Himalayas"]["window_end_m"] <= manifest["route_stationing_length_m"]
    assert all(window["window_start_m"] < window["window_end_m"] for window in windows.values())
