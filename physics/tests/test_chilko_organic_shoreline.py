from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FOLIAGE_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
    "RaftSimEditorLandscapeFoliage.cpp"
)
MAP_TEST_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimTroublemakerMapTest.cpp"
)
EVIDENCE_ROOT = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
)
MANIFEST = EVIDENCE_ROOT / "landscape_candidate_manifest_chilko_river_lava_canyon.json"
REVIEW = EVIDENCE_ROOT / "chilko_organic_shoreline_v1_review.json"
V2_REVIEW = EVIDENCE_ROOT / "chilko_nonrepeating_wet_bank_v2_review.json"
V3_REVIEW = EVIDENCE_ROOT / "chilko_optical_shoreline_naturalism_v3_review.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_generator_is_chilko_only_grounded_and_non_authoritative() -> None:
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")

    for token in (
        "ChilkoOrganicShorelineGravelTargetInstanceCount = 7200",
        "ChilkoOrganicShorelineGravelMinimumInstanceCount = 6800",
        "ChilkoOrganicShorelineGravelSlopeCeilingDegrees = 42.0f",
        "ChilkoOrganicShorelineGroundCoverTargetInstanceCount = 8400",
        "ChilkoOrganicShorelineGroundCoverMinimumInstanceCount = 7900",
        "ChilkoOrganicShorelineGravelRareMaximumHeightCm = 85.0f",
        "ChilkoOrganicShorelineGroundCoverMinimumHeightCm = 18.0f",
        "ChilkoOrganicShorelineGroundCoverMaximumHeightCm = 58.0f",
        "ChilkoOrganicShorelineGroundCoverSlopeCeilingDegrees = 32.0f",
        "ActiveRiverHalfWidth * 1.03f",
        "CandidateIndex < 48",
        "GetMinimumCenterlineDistanceCm(CandidatePoint)",
        "GetConditionedWaterWorldZ(CandidateLogicalX)",
        "ChilkoOrganicShorelineStartStationCm = 250.0f",
        "ChilkoOrganicShorelineEndStationCm = 59750.0f",
        'TEXT("RaftSimChilkoOrganicShorelineV2")',
        'TEXT("RaftSimChilkoShorelineNaturalismV3")',
        'TEXT("RaftSimChilkoSortedGravelScaleV3")',
        'TEXT("RaftSimChilkoMutedGroundCoverV3")',
        'TEXT("RaftSimChilkoShorelineGravel")',
        'TEXT("RaftSimChilkoShorelineGroundCover")',
        'TEXT("RaftSimGenericRockAnalogNoLithologyAuthority")',
        'TEXT("RaftSimNoSpeciesOrEcologyAuthority")',
        'TEXT("RaftSimOutsideProtectedSolverStrip")',
        'TEXT("RaftSimPresentationOnlyNoHydraulicAuthority")',
    ):
        assert token in source

    start = source.index("int32 ChilkoShorelineGravelPlacedCount")
    assert "Landscape->Import" not in source[start:]


def test_chilko_ground_cover_retones_without_changing_the_shared_default() -> None:
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")

    for token in (
        "MI_RaftSim_Chilko_MutedGroundCoverV3",
        'TEXT("VegetationColorScale")',
        "VegetationColorScale->DefaultValue = FLinearColor::White",
        'TEXT("VegetationShadowFillScale")',
        "VegetationShadowFillScale->DefaultValue = 1.0f",
        "FLinearColor(0.62f, 0.38f, 0.24f, 1.0f)",
        "0.28f",
        "const int32 ScaleClass = GravelIndex % 72",
    ):
        assert token in source


def test_runtime_map_contract_counts_and_disclaims_both_families() -> None:
    source = MAP_TEST_SOURCE.read_text(encoding="utf-8")

    assert 'TEXT("RaftSimChilkoOrganicShorelineV2")' in source
    assert 'TEXT("RaftSimChilkoShorelineNaturalismV3")' in source
    assert 'TEXT("RaftSimChilkoSortedGravelScaleV3")' in source
    assert 'TEXT("RaftSimChilkoMutedGroundCoverV3")' in source
    assert "MI_RaftSim_Chilko_MutedGroundCoverV3" in source
    assert "OrganicShorelineActorCount" in source
    assert "OrganicShorelineGravelActorCount" in source
    assert "OrganicShorelineGravelInstanceCount >= 6800" in source
    assert "OrganicShorelineGroundCoverActorCount" in source
    assert "OrganicShorelineGroundCoverInstanceCount >= 7900" in source
    assert 'TEXT("RaftSimGenericRockAnalogNoLithologyAuthority")' in source
    assert 'TEXT("RaftSimNoSpeciesOrEcologyAuthority")' in source
    assert "ECollisionEnabled::NoCollision" in source


def test_saved_chilko_manifest_records_complete_organic_shoreline() -> None:
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "chilko_river_lava_canyon"
    assert candidate["landscape_dressing_boulder_instance_count"] == 8820
    assert candidate["landscape_dressing_foliage_instance_count"] == 16400
    assert candidate["landscape_dressing_understory_instance_count"] == 11750
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_status"
    ] == (
        "source_grounded_rights_reviewed_cc0_six_variant_full_runnable_reach_"
        "sorted_scale_organic_shoreline_gravel_v3_captured"
    )
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_target_instance_count"
    ] == 7200
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_instance_count"
    ] == 7200
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_rejected_placement_count"
    ] == 0
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_minimum_centerline_distance_cm"
    ] >= 1800.0 * 1.03 + 45.0
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_maximum_slope_degrees"
    ] <= 42.0
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_status"
    ] == (
        "source_grounded_full_runnable_reach_muted_short_meadow_ground_cover_"
        "v3_captured"
    )
    assert candidate["landscape_dressing_foliage_material_asset_count"] == 2
    assert candidate["landscape_dressing_understory_material_asset"].endswith(
        "MI_RaftSim_Chilko_MutedGroundCoverV3.MI_RaftSim_Chilko_"
        "MutedGroundCoverV3"
    )
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_target_instance_count"
    ] == 8400
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_instance_count"
    ] == 8400
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_rejected_placement_count"
    ] == 0
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_minimum_centerline_distance_cm"
    ] >= 1800.0 * 1.03 + 85.0
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_maximum_slope_degrees"
    ] <= 32.0


def test_review_retains_measured_breakup_but_rejects_photoreal_acceptance() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == "raftsim.environment.chilko_organic_shoreline_review.v1"
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["organic_shoreline_v1_retained"] is True
    assert review["decision"]["initial_far_bank_small_scale_tuning_rejected"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["terrain_geometry_changed"] is False
    assert review["decision"]["terrain_collision_changed"] is False
    assert review["decision"]["water_geometry_changed"] is False
    assert review["decision"]["hydraulics_changed"] is False
    assert review["decision"]["bathymetry_changed"] is False
    assert review["decision"]["raft_forces_changed"] is False
    assert len(review["remaining_photoreal_defects"]) >= 8
    assert len(review["required_external_acceptance_gates"]) == 6

    comparison = review["visual_comparison"]
    baseline = comparison["baseline_transmitting_water_v2"]
    retained = comparison["retained_organic_shoreline_v1"]
    assert retained["bank_green_dominant_fraction"] > baseline[
        "bank_green_dominant_fraction"
    ] * 1.5
    assert retained["bank_edge_fraction"] > baseline["bank_edge_fraction"] * 1.6
    assert retained["bank_mean_edge_magnitude"] > baseline[
        "bank_mean_edge_magnitude"
    ] * 1.4

    capture = REPO_ROOT / retained["path"]
    assert capture.is_file()
    assert _sha256(capture) == retained["sha256"]


def test_v2_review_locks_full_reach_correction_and_stays_fail_closed() -> None:
    review = json.loads(V2_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.chilko_nonrepeating_wet_bank_review.v2"
    )
    assert review["status"] == (
        "technical_candidate_retained_photoreal_and_external_review_open"
    )
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["organic_shoreline_v1_full_route_claim_superseded"] is True
    assert review["decision"]["v1_placement_end_station_m"] == 253.0
    assert review["decision"]["v2_placement_station_range_m"] == [2.5, 597.5]
    assert review["implementation"]["material"]["world_position_offset_connected"] is False
    assert review["implementation"]["full_reach_shoreline"][
        "gravel_placed_instance_count"
    ] == 7200
    assert review["implementation"]["full_reach_shoreline"][
        "ground_cover_placed_instance_count"
    ] == 8400
    assert len(review["remaining_photoreal_defects"]) >= 8
    assert len(review["required_external_acceptance_gates"]) == 6
    assert "does not claim increased global edge density" in review[
        "matched_visual_check"
    ]["verdict"]

    for artifact in review["retained_artifacts"]:
        if (
            artifact["path"].startswith("unreal/Content/")
            or artifact["path"].endswith(
                "landscape_candidate_manifest_chilko_river_lava_canyon.json"
            )
            or artifact["path"]
            == (
                "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
                "RaftSimEditorLandscapeFoliage.cpp"
            )
            or artifact["path"]
            == (
                "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
                "RaftSimEditorMaterialsBase.cpp"
            )
        ):
            # V3 deliberately supersedes the mutable generator, manifest, and
            # runtime packages. The retained V2 captures and unchanged shader
            # sources remain hash-locked here; V3 owns the new runtime hashes.
            continue
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]


def test_v3_review_locks_optical_naturalism_gain_and_stays_fail_closed() -> None:
    review = json.loads(V3_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.chilko_optical_shoreline_naturalism_review.v3"
    )
    assert review["status"] == (
        "technical_candidate_retained_photoreal_and_external_review_open"
    )
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["legacy_presentation_override_defect_corrected"] is True
    assert review["implementation"]["live_water"][
        "legacy_defaults_apply_only_when_explicit_volume_core_flag_is_absent"
    ] is True
    assert review["implementation"]["live_water"][
        "shared_live_wet_coverage_default_enable"
    ] == 0.0
    assert review["implementation"]["live_water"][
        "chilko_live_wet_coverage_runtime_enable"
    ] == 1.0
    assert review["implementation"]["shoreline"][
        "shared_temperate_parent_identity_defaults_retained"
    ] is True

    comparison = review["visual_comparison"]
    v2_water = comparison["v2_breaking_water_side"]
    v3_water = comparison["v3_breaking_water_side"]
    assert v3_water["water_mean_luminance"] < v2_water["water_mean_luminance"]
    assert v3_water["water_p95_luminance"] < v2_water["water_p95_luminance"]
    assert v3_water["water_fraction_over_0_90"] < (
        v2_water["water_fraction_over_0_90"] * 0.42
    )
    assert v3_water["water_fraction_over_0_95"] < (
        v2_water["water_fraction_over_0_95"] * 0.02
    )
    assert v3_water["bank_neon_green_fraction"] < (
        v2_water["bank_neon_green_fraction"] * 0.36
    )
    assert comparison["v3_bank_closeup"]["bank_neon_green_fraction"] < (
        comparison["v2_bank_closeup"]["bank_neon_green_fraction"] * 0.63
    )
    assert len(review["remaining_photoreal_defects"]) >= 8
    assert len(review["required_external_acceptance_gates"]) == 6

    superseded_artifacts = {
        "unreal/Content/RaftSim/Maps/L_LavaCanyon.umap",
        "unreal/Content/RaftSim/Environment/ChilkoRun/Water/Materials/MI_RaftSim_ChilkoLavaCanyon_LiveVolumeWaterV2.uasset",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp",
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/RaftSimEditorLandscapeFoliage.cpp",
    }
    for artifact in review["retained_artifacts"]:
        if artifact["path"] in superseded_artifacts:
            continue
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]
