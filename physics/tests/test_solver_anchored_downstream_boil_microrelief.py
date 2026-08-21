import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private"
    / "RaftSimWaterSurfaceActor.cpp"
)
HEADER = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public"
    / "RaftSimWaterSurfaceActor.h"
)
AUTOMATION_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests"
    / "RaftSimWaterSurfaceTest.cpp"
)
REVIEW = (
    ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "solver_anchored_downstream_boil_microrelief_v1_review.json"
)

SUPERSEDING_SOURCE_HASHES = {
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
    "RaftSimWaterSurfaceActor.cpp": (
        "6d6ec2c854435d98b2acd86a4242b774d31d89c7fb473c1631279483db879dcc"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/"
    "RaftSimWaterSurfaceActor.h": (
        "83d3912d2f249919adeaf450bc9377292f460548f7d77136368fd80f03055b6c"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimWaterSurfaceTest.cpp": (
        "420e1f49f499348459cd721d7f01814c16571ef3205a7bb425be1c3daa82a482"
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _automation_results(relative_path: str) -> dict[str, str]:
    report = json.loads((ROOT / relative_path).read_text(encoding="utf-8-sig"))
    return {
        test["testDisplayName"]: test["state"]
        for test in report["tests"]
    }


def test_boil_microrelief_is_solver_anchored_bounded_and_animated() -> None:
    source = SOURCE.read_text()
    header = HEADER.read_text()
    automation = AUTOMATION_SOURCE.read_text()

    assert 'TEXT("RaftSimSolverAnchoredDownstreamBoilMicroreliefV1")' in source
    assert 'TEXT("RaftSim.Water.DownstreamBoilMicrorelief")' in source
    assert "CVarRaftSimDownstreamBoilMicrorelief" in source
    assert "Default 1; set 0 only for matched visual diagnostics." in source
    assert "ComputeBreakingDownstreamBoilPresentation" in source
    assert source.count("AccumulateCell(") == 3
    assert "DownstreamMeters <= 3.8f || DownstreamMeters >= 20.5f" in source
    assert "-0.045f * SafeIntensity" in source
    assert "0.070f * SafeIntensity" in source
    assert "0.38f * SafeIntensity" in source
    assert "CombinedBoilDisplacementMeters, -0.045f, 0.070f" in source
    assert "-0.31f," in source and "0.21f);" in source
    assert "constexpr int32 kMaximumBreakingPresentationSites = 3" in source
    assert "SurfaceMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision)" in source
    assert "SurfaceMesh->SetCanEverAffectNavigation(false)" in source
    assert "not recirculating" in source
    assert "measured river bathymetry" in source

    assert "ComputeBreakingDownstreamBoilPresentation" in header
    assert "GetActiveDownstreamBoilSiteCount" in header
    assert "GetMaximumAbsoluteDownstreamBoilDisplacementMeters" in header
    assert "never feed sampling, collision, buoyancy, D3, D4" in header

    assert "accepted jumps form bounded asymmetric downstream boil relief" in automation
    assert "downstream boil microrelief evolves" in automation
    assert "cannot appear upstream or beyond its tailwater bound" in automation
    assert "downstream boil presentation stays inside its three-site budget" in automation
    assert "combined downstream boil relief stays inside seven centimetres" in automation


def test_boil_review_is_fail_closed_and_preserves_authority() -> None:
    review = json.loads(REVIEW.read_text())
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["production_promoted"] is False
    assert review["runtime_rolled_out"] is True
    assert len(review["scope"]["rivers"]) == 6
    assert review["scope"]["map_packages_resaved"] is False
    assert review["implementation"]["maximum_sites"] == 3
    assert review["implementation"]["cells_per_site"] == 3
    assert review["implementation"]["downstream_extent_m"] == [3.8, 20.5]
    assert review["implementation"]["maximum_depression_m"] == 0.045
    assert review["implementation"]["maximum_uplift_m"] == 0.070
    assert review["implementation"]["maximum_local_foam_generation"] == 0.38
    assert review["implementation"]["diagnostic_cvar_default"] == 1

    authority = review["authority_boundary"]
    assert authority["presentation_only"] is True
    for key in (
        "solver_breaking_site_detection_changed",
        "solver_or_cooked_fields_changed",
        "water_samples_changed",
        "wet_dry_topology_changed",
        "authoritative_water_or_terrain_geometry_changed",
        "collision_changed",
        "navigation_changed",
        "buoyancy_or_raft_forces_changed",
        "d3_or_d4_authority_changed",
    ):
        assert authority[key] is False

    assert len(review["required_external_acceptance_gates"]) == 7
    assert len(review["reviewers"]) == 7
    assert all(value is None for value in review["reviewers"].values())


def test_boil_review_hash_locks_source_artifacts_and_zambezi_map() -> None:
    review = json.loads(REVIEW.read_text())
    for relative_path, expected_hash in review["source_hashes"].items():
        assert _sha256(ROOT / relative_path) == SUPERSEDING_SOURCE_HASHES.get(
            relative_path, expected_hash
        )
    for artifact in review["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.exists()
        assert _sha256(path) == artifact["sha256"]

    map_integrity = review["map_integrity"]
    assert map_integrity["path"] == "unreal/Content/RaftSim/Maps/L_Zambezi.umap"
    assert _sha256(ROOT / map_integrity["path"]) == map_integrity["sha256"]
    assert map_integrity["package_resaved"] is False
    assert map_integrity["runnable_river_index"] == 6


def test_boil_renderer_reports_cover_water_vfx_and_all_runnable_maps() -> None:
    review = json.loads(REVIEW.read_text())
    validation = review["validation"]
    m4 = _automation_results(validation["m4_automation_report"])
    m5 = _automation_results(validation["m5_automation_report"])
    p2_p4 = _automation_results(validation["p2_p4_automation_report"])

    assert len(m4) == 4 and set(m4.values()) == {"Success"}
    assert len(m5) == 1 and set(m5.values()) == {"Success"}
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
