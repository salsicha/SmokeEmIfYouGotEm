import json
from pathlib import Path

from raftsim.south_fork_a1_source_mile_divergence_audit import (
    FULL_REACH_SOURCE_MILE_DIVERGENCE_AUDIT_RELATIVE_PATH,
    FULL_REACH_SOURCE_MILE_DIVERGENCE_OVERLAY_GEOJSON_RELATIVE_PATH,
    build_south_fork_a1_source_mile_divergence_audit,
    build_south_fork_a1_source_mile_divergence_overlay_geojson,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_audit() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_SOURCE_MILE_DIVERGENCE_AUDIT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_overlay() -> dict:
    return json.loads(
        (
            REPO_ROOT / FULL_REACH_SOURCE_MILE_DIVERGENCE_OVERLAY_GEOJSON_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_south_fork_a1_source_mile_divergence_audit_is_reproducible():
    generated = build_south_fork_a1_source_mile_divergence_audit(REPO_ROOT)
    committed = _load_audit()

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_source_mile_divergence_audit.v1"
    assert (
        committed["status"]
        == "published_source_mile_points_are_upstream_of_official_access_path"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_source_mile_divergence_audit_projects_published_breakpoints():
    audit = _load_audit()
    breakpoints = {
        item["breakpoint_id"]: item
        for item in audit["published_breakpoints_on_official_access_path"]
    }

    assert set(breakpoints) == {
        "salmon_falls_20_5_mile_source_convention",
        "full_run_21_0_mile_source_convention",
    }
    assert breakpoints["salmon_falls_20_5_mile_source_convention"][
        "source_station_m"
    ] == 32991.552
    assert breakpoints["full_run_21_0_mile_source_convention"][
        "source_station_m"
    ] == 33796.224
    assert breakpoints["full_run_21_0_mile_source_convention"][
        "remaining_source_path_to_official_access_m"
    ] == 15281.508
    assert breakpoints["full_run_21_0_mile_source_convention"][
        "geodesic_distance_to_official_access_m"
    ] > 10300.0


def test_south_fork_a1_source_mile_divergence_audit_summarizes_excess_path():
    audit = _load_audit()
    summary = audit["divergence_summary"]

    assert audit["official_access_endpoint"]["name"] == (
        "Salmon Falls  Lower Water Raft Take-out"
    )
    assert audit["official_access_endpoint"]["source_station_miles"] == 30.495
    assert summary["published_full_run_station_m"] == 33796.224
    assert summary["official_access_source_station_m"] == 49077.732
    assert summary["excess_source_path_after_21_miles_m"] == 15281.508
    assert summary["excess_source_path_after_21_miles_miles"] == 9.495
    assert summary["geodesic_21_mile_point_to_official_access_m"] > 10300.0


def test_south_fork_a1_source_mile_divergence_overlay_geojson_is_reproducible():
    generated = build_south_fork_a1_source_mile_divergence_overlay_geojson(REPO_ROOT)
    committed = _load_overlay()

    assert generated == committed
    assert (
        committed["schema"]
        == "raftsim.south_fork.a1_source_mile_divergence_overlay.geojson.v1"
    )
    assert committed["type"] == "FeatureCollection"
    assert committed["production_promoted"] is False
    assert len(committed["features"]) == 5
    excess = next(
        feature
        for feature in committed["features"]
        if feature["id"] == "source_path_excess_after_21_0_miles"
    )
    assert excess["geometry"]["type"] == "LineString"
    assert excess["properties"]["source_path_excess_m"] == 15281.508
    assert excess["properties"]["point_count"] > 100
    for feature in committed["features"]:
        assert feature["properties"]["production_promoted"] is False
        assert feature["properties"]["can_bind_editor_geometry"] is False
        assert feature["properties"]["can_bind_solver_windows"] is False


def test_south_fork_a1_source_mile_divergence_audit_blocks_promotion():
    gate = _load_audit()["promotion_gate"]

    assert gate["can_promote_current_nhd_station_axis"] is False
    assert gate["can_crop_to_final_downstream_anchor"] is False
    assert gate["can_restation_named_rapids"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
