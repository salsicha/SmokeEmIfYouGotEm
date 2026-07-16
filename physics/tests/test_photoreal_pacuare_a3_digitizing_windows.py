import json
from pathlib import Path

from raftsim.pacuare_a3_digitizing_windows import (
    PACUARE_A3_DIGITIZING_WORK_WINDOW_MANIFEST_RELATIVE_PATH,
    PACUARE_A3_DIGITIZING_WORK_WINDOW_MANIFEST_SCHEMA,
    PACUARE_A3_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH,
    PACUARE_A3_DIGITIZING_WORK_WINDOWS_SCHEMA,
    build_pacuare_a3_digitizing_work_window_manifest,
    build_pacuare_a3_digitizing_work_windows_geojson,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_geojson() -> dict:
    return json.loads(
        (REPO_ROOT / PACUARE_A3_DIGITIZING_WORK_WINDOWS_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_manifest() -> dict:
    return json.loads(
        (
            REPO_ROOT / PACUARE_A3_DIGITIZING_WORK_WINDOW_MANIFEST_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_pacuare_a3_digitizing_work_windows_geojson_is_reproducible():
    generated = build_pacuare_a3_digitizing_work_windows_geojson(REPO_ROOT)
    committed = _load_geojson()

    assert generated == committed
    assert committed["schema"] == PACUARE_A3_DIGITIZING_WORK_WINDOWS_SCHEMA
    assert committed["type"] == "FeatureCollection"
    assert committed["status"] == (
        "review_only_digitizing_windows_on_preview_scaffold_not_authoritative"
    )
    assert len(committed["features"]) == 15


def test_pacuare_a3_digitizing_work_windows_cover_every_rapid_with_lines():
    geojson = _load_geojson()
    features = {feature["properties"]["rapid_name"]: feature for feature in geojson["features"]}

    assert set(features) == {
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
    for feature in features.values():
        assert feature["geometry"]["type"] == "LineString"
        assert len(feature["geometry"]["coordinates"]) >= 4
        assert feature["properties"]["stationing_status"] == (
            "order_distributed_preview_work_window_not_authoritative"
        )
        assert feature["properties"]["geometry_status"] == (
            "review_focus_window_not_exact_rapid_geometry"
        )


def test_pacuare_a3_digitizing_work_windows_record_preview_order_mapping():
    geojson = _load_geojson()
    features = {feature["properties"]["rapid_name"]: feature for feature in geojson["features"]}

    upper_huacas = features["Upper Huacas"]["properties"]
    assert upper_huacas["catalog_order_station_m"] == 6562.5
    assert upper_huacas["preview_order_station_m"] == 11410.605
    assert upper_huacas["window_start_m"] == 10510.605
    assert upper_huacas["window_end_m"] == 12310.605
    assert upper_huacas["half_length_m"] == 900.0
    assert upper_huacas["lateral_review_buffer_m"] == 180.0

    pyramid = features["Pyramid Rock"]["properties"]
    assert pyramid["half_length_m"] == 650.0
    assert pyramid["lateral_review_buffer_m"] == 130.0

    bienvenidos = features["Bienvenidos"]["properties"]
    assert bienvenidos["half_length_m"] == 450.0
    assert bienvenidos["lateral_review_buffer_m"] == 90.0


def test_pacuare_a3_digitizing_work_window_manifest_is_reproducible_and_blocked():
    generated = build_pacuare_a3_digitizing_work_window_manifest(REPO_ROOT)
    committed = _load_manifest()

    assert generated == committed
    assert committed["schema"] == PACUARE_A3_DIGITIZING_WORK_WINDOW_MANIFEST_SCHEMA
    assert committed["status"] == (
        "work_windows_ready_for_manual_digitizing_review_no_stationing_promotion"
    )
    assert committed["production_promoted"] is False
    assert committed["rapid_count"] == 15
    assert committed["critical_window_count"] == 6
    assert committed["preview_length_m"] == 45642.42
    assert committed["catalog_run_length_m"] == 26250.0
    assert committed["preview_to_catalog_length_ratio"] > 1.7
    gate = committed["promotion_gate"]
    assert gate["can_replace_order_interpolation"] is False
    assert gate["can_regenerate_named_rapid_catalog"] is False
    assert gate["can_bind_editor_geometry"] is False
    assert gate["can_generate_rapid_water_windows"] is False
    assert gate["can_bind_solver_windows"] is False


def test_pacuare_a3_digitizing_work_window_manifest_summarizes_window_coordinates():
    manifest = _load_manifest()
    windows = {window["rapid_name"]: window for window in manifest["windows"]}

    assert windows["Dos Montanas"]["review_priority"] == "critical"
    assert windows["Dos Montanas"]["coordinate_count"] >= 8
    assert windows["Las Ranitas"]["window_end_m"] <= manifest["preview_length_m"]
    assert all(window["window_start_m"] < window["window_end_m"] for window in windows.values())
