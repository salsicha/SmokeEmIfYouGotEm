from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from raftsim.chilko_production_corridor import (
    UNREAL_LANDSCAPE_SIZE,
    stitch_official_route,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RIVER_ROOT = REPO_ROOT / "physics/data/real_world/chilko_river_bc"
CORRIDOR_ROOT = (
    RIVER_ROOT
    / "production_corridor/chilko_river_lodge_to_taseko_junction"
)
UNREAL_REVIEW_ROOT = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_official_fwa_route_is_one_complete_unbranched_chain() -> None:
    source = _read_json(
        RIVER_ROOT
        / "hydrography/lodge_to_taseko_junction_candidate_segments.geojson"
    )
    route = stitch_official_route(source)

    assert route.diagnostics["source_feature_count"] == 160
    assert route.diagnostics["stitched_feature_count"] == 160
    assert route.diagnostics["all_source_segments_used"] is True
    assert route.diagnostics["maximum_join_gap_m"] == 0.0
    assert route.diagnostics["clipped_length_m"] == pytest.approx(55_845.696, abs=0.01)
    assert route.diagnostics["put_in_seed_offset_m"] == pytest.approx(218.440, abs=0.01)
    assert route.diagnostics["take_out_seed_offset_m"] == pytest.approx(84.929, abs=0.01)
    assert route.diagnostics["exact_access_geometry_approved"] is False


def test_official_source_clips_are_hash_locked_and_review_gated() -> None:
    terrain = _read_json(
        RIVER_ROOT
        / "source/terrain/nrcan_mrdem30_chilko_corridor_manifest.json"
    )
    imagery = _read_json(
        RIVER_ROOT
        / "source/imagery/sentinel2_20250825_chilko_corridor_manifest.json"
    )

    assert terrain["vertical_datum"] == "CGVD2013 orthometric heights (EPSG:6647)"
    assert terrain["metadata"]["source_crs"] == "EPSG:3979"
    assert terrain["metadata"]["effective_resolution_m"] == 30.0
    assert terrain["production_promoted"] is False
    assert terrain["per_pixel_source_classes"] == [
        {
            "value": 1,
            "meaning": "adjusted_copernicus_glo_30",
            "pixel_count": 1_462_383,
        }
    ]
    assert imagery["scene"]["item_id"] == "S2C_10UDC_20250825_0_L2A"
    assert imagery["tci_metadata"]["effective_resolution_m"] == 10.0
    assert imagery["scl_metadata"]["effective_resolution_m"] == 20.0
    assert imagery["obscured_fraction_of_valid_clip"] == 0.0
    assert imagery["production_promoted"] is False

    for manifest in (terrain, imagery):
        for output in manifest["outputs"].values():
            path = REPO_ROOT / output["path"]
            assert path.is_file()
            assert _sha256(path) == output["sha256"]


def test_corridor_manifest_preserves_authority_and_promotion_blockers() -> None:
    corridor = _read_json(CORRIDOR_ROOT / "manifest.json")
    conditioning = corridor["artifacts"]["channel_conditioning_summary"]
    source_scale_policy = corridor["artifacts"]["heightfield_source_scale_policy"]

    assert corridor["route"]["all_source_segments_stitched"] is True
    assert corridor["route"]["exact_access_geometry_approved"] is False
    assert corridor["terrain"]["source_resolution_m"] == 30.0
    assert corridor["imagery"]["obscured_fraction_of_valid_clip"] == 0.0
    assert conditioning["measurements"]["maximum_cut_m"] <= 70.0
    assert conditioning["measurements"]["maximum_fill_m"] == 0.0
    assert conditioning["authority"]["changes_custom_cpp_solver_state"] is False
    assert conditioning["authority"]["changes_collision_or_raft_forces"] is False
    assert source_scale_policy["size"] == UNREAL_LANDSCAPE_SIZE
    assert source_scale_policy["source_dtm_resolution_m"] == 30.0
    assert corridor["promotion_gates"]["official_source_chain_stitched"] is True
    assert corridor["promotion_gates"]["source_scale_corridor_generated"] is True
    assert corridor["promotion_gates"]["rapid_scale_terrain_and_bathymetry"] is False
    assert corridor["promotion_gates"]["numeric_flow_bands"] is False
    assert corridor["promotion_gates"]["lifelike_capture"] is False
    assert corridor["production_promoted"] is False

    heightfield = REPO_ROOT / corridor["artifacts"]["heightfield_source_scale"]
    with Image.open(heightfield) as image:
        assert image.size == (UNREAL_LANDSCAPE_SIZE, UNREAL_LANDSCAPE_SIZE)
        assert image.mode == "I;16"


def test_unreal_candidate_is_captured_with_nanite_but_not_promoted() -> None:
    contract = _read_json(
        REPO_ROOT / "unreal/Content/RaftSim/River/chilko_heightfield_import_test.json"
    )
    review = _read_json(
        UNREAL_REVIEW_ROOT
        / "landscape_candidate_manifest_chilko_river_lava_canyon.json"
    )
    candidate = review["candidates"][0]

    assert contract["heightfield_size"] == UNREAL_LANDSCAPE_SIZE
    assert contract["landscape_nanite_requested"] is True
    assert contract["authority"]["changes_solver_state"] is False
    assert contract["authority"]["changes_collision_or_raft_forces"] is False
    assert contract["production_promoted"] is False
    assert candidate["river_id"] == "chilko_river_lava_canyon"
    assert candidate["heightfield_width_px"] == UNREAL_LANDSCAPE_SIZE
    assert candidate["component_count_total"] == 64
    assert candidate["material_bound_component_count"] == 64
    assert candidate["material_binding_status"] == "all_source_components_bound"
    assert candidate["nanite_enabled"] is True
    assert candidate["nanite_component_count"] == 1
    assert candidate["nanite_material_bound_slot_count"] == 64
    assert candidate["nanite_material_audit_error_count"] == 0
    assert candidate["nanite_representation_status"] == "enabled_and_built_up_to_date"
    assert candidate["promotion_status"].startswith("review_gated_")

    for key in ("guide_seat_capture", "river_eye_capture"):
        capture_path = REPO_ROOT / candidate[key]
        assert capture_path.is_file()
        pixels = np.asarray(Image.open(capture_path).convert("RGB"), dtype=np.float32)
        assert pixels.std() > 8.0

    map_path = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/"
        "L_ChilkoRiver_PhysicalCorridorCandidate.umap"
    )
    assert map_path.is_file()


def test_unreal_command_supports_an_isolated_chilko_build() -> None:
    source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimEditorModule.cpp"
    ).read_text(encoding="utf-8")

    assert 'TEXT("chilko_river_lava_canyon")' in source
    assert "L_ChilkoRiver_PhysicalCorridorCandidate" in source
    assert "const FString& RiverIdFilter" in source
    assert "Candidates.FilterByPredicate" in source
    assert "Candidate.LandscapeSize = 1009" in source
    assert "Candidate.bEnableLandscapeNanite = true" in source
    assert "CenterSampleSpacingCm = bChilkoSourceScale ? 500.0f : 100.0f" in source
