import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUTHOR_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials"
    / "RaftSimEditorBreakingWaterMaterial.cpp"
)
REVIEW = (
    ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "breaking_water_raft_crew_occlusion_v2_review.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _automation_results(relative_path: str) -> dict[str, str]:
    report = json.loads((ROOT / relative_path).read_text(encoding="utf-8-sig"))
    return {
        test["testDisplayName"]: test["state"]
        for test in report["tests"]
    }


def test_breaking_water_consumes_live_raft_crew_occlusion_fail_closed() -> None:
    source = AUTHOR_SOURCE.read_text()

    assert "MaterialExpressionCollectionParameter.h" in source
    assert "MaterialExpressionCustom.h" in source
    assert "MaterialExpressionWorldPosition.h" in source
    assert "MaterialParameterCollection.h" in source
    assert (
        'TEXT("/Game/RaftSim/Materials/MPC_RaftSim_RaftFoamOcclusion."'
        in source
    )
    assert "FoamOcclusionCollection == nullptr" in source
    assert "return nullptr;" in source
    assert 'TEXT("RaftFoamExclusionEnabled")' in source
    assert 'TEXT("RaftFoamExclusionCenterAndHalfWidthCm")' in source
    assert 'TEXT("RaftFoamExclusionForwardAndHalfLengthCm")' in source
    assert 'TEXT("RaftSimBreakingWaterRaftCrewOcclusionV2")' in source
    assert "ForwardAndHalfLength.w * 0.86" in source
    assert "CenterAndHalfWidth.w * 0.47" in source
    assert "smoothstep(0.80, 1.30, EllipseSquared)" in source
    assert "OcclusionSafeEdgeFeather = Multiply(" in source
    assert "OcclusionSafeEdgeFeather," in source
    assert "changes no water," in source
    assert "contact, collision, buoyancy, navigation, D3, D4, or raft-force state" in source

    # Re-authoring the material must not churn established source assets.
    assert "if (!ExistingOcclusionCollection)" in source
    assert "(!ExistingFoamLace || !ExistingFlowNormal) &&" in source
    assert "LoadOrCreateRaftFoamOcclusionCollection" in source
    assert "BuildSouthForkWaterTextureAssets" in source


def test_occlusion_review_is_fail_closed_and_preserves_authority() -> None:
    review = json.loads(REVIEW.read_text())
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["production_promoted"] is False
    assert review["runtime_rolled_out"] is True
    assert len(review["scope"]["rivers"]) == 6
    assert review["scope"]["map_packages_resaved"] is False

    implementation = review["implementation"]
    assert implementation["marker"] == "RaftSimBreakingWaterRaftCrewOcclusionV2"
    assert implementation["runtime_parameter_collection_changed"] is False
    assert implementation["breaking_water_width_scale"] == 0.47
    assert implementation["breaking_water_length_scale"] == 0.86
    assert implementation["ellipse_squared_smoothstep"] == [0.80, 1.30]
    assert implementation["missing_collection_behavior"] == "authoring fails closed"
    assert implementation["depth_bearing_d4_review_default_enabled"] is False

    authority = review["authority_boundary"]
    assert authority["presentation_only"] is True
    for key in (
        "solver_or_cooked_fields_changed",
        "solver_breaking_site_detection_changed",
        "water_samples_changed",
        "wet_dry_topology_changed",
        "terrain_or_authoritative_water_geometry_changed",
        "collision_changed",
        "navigation_changed",
        "buoyancy_or_raft_forces_changed",
        "d3_authority_changed",
        "d4_contact_geometry_or_authority_changed",
    ):
        assert authority[key] is False

    assert len(review["required_external_acceptance_gates"]) == 7
    assert len(review["reviewers"]) == 7
    assert all(value is None for value in review["reviewers"].values())


def test_occlusion_review_hash_locks_sources_maps_and_visual_evidence() -> None:
    review = json.loads(REVIEW.read_text())

    for relative_path, expected_hash in review["source_hashes"].items():
        assert _sha256(ROOT / relative_path) == expected_hash
    for relative_path, expected_hash in review["map_integrity"]["sha256"].items():
        assert _sha256(ROOT / relative_path) == expected_hash

    evidence = review["visual_evidence"]
    for key in ("baseline", "retained_normal_water", "retained_waterless_isolation"):
        artifact = evidence[key]
        assert _sha256(ROOT / artifact["path"]) == artifact["sha256"]
    assert review["runtime_contact_evidence"]["waterless_isolation_d4_plume_visible"]
    assert review["runtime_contact_evidence"]["depth_bearing_v10_cached_frames"] == 6
    assert len(
        review["runtime_contact_evidence"]["depth_bearing_v10_frame_triangle_counts"]
    ) == 6


def test_occlusion_renderer_reports_cover_contact_vfx_and_all_runnable_maps() -> None:
    review = json.loads(REVIEW.read_text())
    validation = review["validation"]
    m4 = _automation_results(validation["m4_automation_report"])
    m5 = _automation_results(validation["m5_automation_report"])
    p2_p4 = _automation_results(validation["p2_p4_automation_report"])

    assert len(m4) == 4 and set(m4.values()) == {"Success"}
    assert m5 == {"ProductionNiagaraWaterVfx": "Success"}
    assert set(p2_p4) == {
        "WaterSurfaceRenders",
        "L_Hance",
        "L_LavaCanyon",
        "L_Terminator",
        "L_Troublemaker",
        "L_UpperHuacas",
        "L_Zambezi",
    }
    assert set(p2_p4.values()) == {"Success"}

    for relative_path, expected_hash in review["automation_report_hashes"].items():
        assert _sha256(ROOT / relative_path) == expected_hash
