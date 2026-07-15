from __future__ import annotations

import hashlib
import json
from pathlib import Path

from raftsim.chilko_source_attachment import build_chilko_source_attachment


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT / "physics/data/real_world/chilko_river_bc"


def _read(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_chilko_source_attachment_regenerates_deterministically() -> None:
    expected = {path.relative_to(REPO_ROOT) for path in build_chilko_source_attachment(REPO_ROOT)}
    assert expected == {
        Path(
            "physics/data/real_world/chilko_river_bc/hydrography/"
            "lodge_to_taseko_junction_candidate_segments.geojson"
        ),
        Path("physics/data/real_world/chilko_river_bc/hydrography/route_source_review.json"),
        Path("physics/data/real_world/chilko_river_bc/hydrology/seasonal_flow_context.json"),
        Path("physics/data/real_world/chilko_river_bc/terrain/terrain_source_review.json"),
        Path("physics/data/real_world/chilko_river_bc/imagery/imagery_source_review.json"),
        Path("physics/data/real_world/chilko_river_bc/review/land_and_publication_source_review.json"),
        Path("physics/data/real_world/chilko_river_bc/source_manifest.json"),
    }


def test_chilko_route_uses_official_segments_without_approving_seed_endpoints() -> None:
    route = _read("hydrography/route_source_review.json")
    candidate = _read("hydrography/lodge_to_taseko_junction_candidate_segments.geojson")

    assert route["source_feature_count"] == 545
    assert route["candidate_feature_count"] == 160
    assert 55_000.0 < route["candidate_feature_length_sum_m"] < 57_000.0
    assert route["put_in"]["exact_geometry_approved"] is False
    assert route["take_out"]["exact_ramp_geometry_approved"] is False
    assert route["put_in"]["nearest_fwa_match"]["seed_to_source_distance_m"] < 250.0
    assert route["take_out"]["nearest_fwa_match"]["seed_to_source_distance_m"] < 100.0
    assert route["route_authority"]["candidate_is_stitched_centerline"] is False
    assert route["route_authority"]["production_promotion_allowed"] is False
    assert len(candidate["features"]) == route["candidate_feature_count"]
    assert all(feature["properties"]["GNIS_NAME"] == "Chilko River" for feature in candidate["features"])


def test_chilko_flow_history_is_official_but_gameplay_bands_remain_blocked() -> None:
    flow = _read("hydrology/seasonal_flow_context.json")
    stations = {station["station_number"]: station for station in flow["stations"]}

    assert set(stations) == {"08MA001", "08MA002"}
    assert stations["08MA002"]["monthly_history"]["first_month"] == "1928-11"
    assert stations["08MA002"]["monthly_history"]["last_month"] == "2025-12"
    assert stations["08MA002"]["role"] == "primary_upstream_seasonality_and_timing_candidate"
    assert "downstream_of_taseko_confluence" in stations["08MA001"]["limitation"]
    assert flow["gameplay_flow_bands"]["numeric_thresholds"] == []
    assert flow["gameplay_flow_bands"]["status"].startswith("blocked")


def test_chilko_terrain_review_rejects_false_positive_lidar_envelopes() -> None:
    terrain = _read("terrain/terrain_source_review.json")

    assert terrain["hrdem_lidar"]["stac_search_item_count"] == 2
    assert terrain["hrdem_lidar"]["actual_extent_intersection_count"] == 0
    assert terrain["mrdem30"]["resolution_m"] == 30
    assert terrain["mrdem30"]["clip_attached"] is False
    assert terrain["production_promotion_allowed"] is False


def test_chilko_imagery_and_publication_evidence_stay_review_gated() -> None:
    imagery = _read("imagery/imagery_source_review.json")
    land = _read("review/land_and_publication_source_review.json")

    assert imagery["selected_scene"]["item_id"] == "S2C_10UDC_20250825_0_L2A"
    assert imagery["selected_scene"]["cloud_cover_percent"] < 0.01
    preview = REPO_ROOT / imagery["selected_scene"]["attached_preview"]
    assert imagery["selected_scene"]["attached_preview_sha256"] == _sha256(preview)
    assert imagery["production_promotion_allowed"] is False
    assert imagery["rights"]["third_party_portal_content_promoted"] is False
    assert land["policy"]["consultation_or_permission_complete"] is False
    assert land["policy"]["nation_media_or_text_downloaded"] is False
    assert land["policy"]["detailed_access_or_sensitive_location_publication_allowed"] is False


def test_chilko_manifest_hashes_sources_and_keeps_all_promotion_gates_closed() -> None:
    manifest = _read("source_manifest.json")

    assert manifest["status"] == "first_official_source_attachment_complete_production_corridor_blocked"
    assert manifest["reach"]["exact_endpoint_geometry_approved"] is False
    assert manifest["promotion_gates"]["source_attachment_complete"] is True
    assert all(
        value is False
        for key, value in manifest["promotion_gates"].items()
        if key != "source_attachment_complete"
    )
    for artifact in manifest["generated_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert artifact["sha256"] == _sha256(path)
