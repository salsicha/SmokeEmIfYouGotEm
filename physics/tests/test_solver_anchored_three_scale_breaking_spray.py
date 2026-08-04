import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REVIEW = (
    ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "solver_anchored_three_scale_breaking_spray_v1_review.json"
)
RUNTIME_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private"
    / "RaftSimWaterVfxActor.cpp"
)
RUNTIME_HEADER = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public"
    / "RaftSimWaterVfxActor.h"
)
AUTHORING_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials"
    / "RaftSimEditorNiagaraWaterVfx.cpp"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def test_crest_spray_reuses_solver_sites_and_bounded_camera_budget() -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")
    header = RUNTIME_HEADER.read_text(encoding="utf-8")
    assert "BreakingSurface->GetBreakingSites(Sites)" in source
    assert "MaxActiveRapidNiagaraSites = 6" in source
    assert "RapidNiagaraFullDensityDistanceCm = 6000.0f" in source
    assert "RapidNiagaraCullDistanceCm = 12000.0f" in source
    assert "constexpr int32 RapidNiagaraPoolSize = 8" in source
    assert "RapidCrestSprayNiagara.Reserve(RapidNiagaraPoolSize)" in source
    assert source.count("RapidCrestSprayNiagara.Add(CrestSprayComponent)") == 1
    assert "ActiveRapidCrestSprayNiagaraCount" in source
    assert "GetActiveRapidCrestSprayNiagaraCount" in header
    assert 'TEXT("RaftSimSolverAnchoredThreeScaleBreakingSprayV1")' in source
    assert "FMath::Lerp(100.0f, 220.0f, Intensity)" in source


def test_crest_spray_has_a_dedicated_ballistic_project_asset_profile() -> None:
    source = AUTHORING_SOURCE.read_text(encoding="utf-8")
    runtime = RUNTIME_SOURCE.read_text(encoding="utf-8")
    for contract in (
        'TEXT("NS_RaftSim_RapidCrestSpray")',
        "FVector2f(0.32f, 0.72f)",
        "FVector2f(3.0f, 5.0f)",
        "FVector2f(12.0f, 24.0f)",
        "FVector2f(120.0f, 36.0f)",
        "FVector2f(240.0f, 540.0f)",
        "FVector3f(0.0f, 0.0f, -980.0f)",
    ):
        assert contract in source
    assert "RapidCrestSpraySystem" in runtime
    assert "retained V4/V5 photographic review rosters predate" in runtime
    asset = ROOT / (
        "unreal/Content/RaftSim/VFX/Water/"
        "NS_RaftSim_RapidCrestSpray.uasset"
    )
    assert asset.is_file()
    assert asset.stat().st_size > 100_000


def test_three_scale_spray_review_is_fail_closed_and_hash_locked() -> None:
    review = _load_json(REVIEW)
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["production_promoted"] is False
    assert review["runtime_rolled_out"] is True
    assert len(review["scope"]["rivers"]) == 6
    assert review["authority_boundary"]["presentation_only"] is True
    assert review["authority_boundary"]["solver_breaking_site_detection_changed"] is False
    assert review["authority_boundary"]["collision_changed"] is False
    assert review["authority_boundary"]["buoyancy_or_raft_forces_changed"] is False
    assert review["implementation"]["production_niagara_component_count"] == 27
    assert review["implementation"]["crest_spray_pool_size"] == 8
    assert review["implementation"]["maximum_active_sites"] == 6
    assert review["implementation"]["cull_distance_m"] == 120.0
    assert len(review["required_external_acceptance_gates"]) == 7
    assert all(value is None for value in review["reviewers"].values())

    asset = ROOT / review["implementation"]["niagara_asset"]
    assert _sha256(asset) == review["implementation"]["niagara_asset_sha256"]
    for relative_path, expected_hash in review["source_hashes"].items():
        assert _sha256(ROOT / relative_path) == expected_hash
    for artifact in review["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.exists()
        assert _sha256(path) == artifact["sha256"]


def test_three_scale_spray_renderer_reports_cover_runtime_assets_and_all_rivers() -> None:
    review = _load_json(REVIEW)
    artifact_paths = {
        Path(artifact["path"]).name: ROOT / artifact["path"]
        for artifact in review["artifacts"]
    }
    expected = {
        "solver_anchored_three_scale_breaking_spray_v1_m4.json": 4,
        "solver_anchored_three_scale_breaking_spray_v1_m5.json": 1,
        "solver_anchored_three_scale_breaking_spray_v1_p2_p4.json": 7,
    }
    for name, total in expected.items():
        report = _load_json(artifact_paths[name])
        assert len(report["tests"]) == total
        assert report["failed"] == 0
        assert report["notRun"] == 0
        assert all(test["state"] == "Success" for test in report["tests"])

    p2_p4 = _load_json(
        artifact_paths["solver_anchored_three_scale_breaking_spray_v1_p2_p4.json"]
    )
    names = {test["testDisplayName"] for test in p2_p4["tests"]}
    assert names == {
        "WaterSurfaceRenders",
        "L_Hance",
        "L_LavaCanyon",
        "L_Terminator",
        "L_Troublemaker",
        "L_UpperHuacas",
        "L_Zambezi",
    }
