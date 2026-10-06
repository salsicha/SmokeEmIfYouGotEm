import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REVIEW_PATH = (
    ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "cold_water_presentation_bank_naturalism_v1_review.json"
)
RUNTIME_CPP = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private"
    / "RaftSimWaterSurfaceActor.cpp"
)
RUNTIME_HEADER = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public"
    / "RaftSimWaterSurfaceActor.h"
)
CONFIG_HEADER = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimWater/Public"
    / "RaftSimRiverWaterConfig.h"
)
GENERATOR_CPP = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape"
    / "RaftSimEditorLandscapeGeometry.cpp"
)
NATIVE_TEST_CPP = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests"
    / "RaftSimWaterSurfaceTest.cpp"
)

SUPERSEDING_SOURCE_HASHES = {
    "runtime_cpp_sha256": (
        "5926ec1037883be54b9e4c8f795ee7f1ba3e28011bf7858d3639c929dbce19ee"
    ),
    "runtime_header_sha256": (
        "83d3912d2f249919adeaf450bc9377292f460548f7d77136368fd80f03055b6c"
    ),
    "config_header_sha256": (
        "6616b4809f4b4fb78811c523ec398d1b4dfb2062676105aac416f5d8d30cc95f"
    ),
    "generator_cpp_sha256": (
        "6bd20f4f22a5b4869c106a758747686688794b8fb7462cc5cf8de8d402d69205"
    ),
    "native_test_cpp_sha256": (
        "420e1f49f499348459cd721d7f01814c16571ef3205a7bb425be1c3daa82a482"
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _review() -> dict:
    return json.loads(REVIEW_PATH.read_text())


def test_review_retains_only_a_bounded_technical_improvement() -> None:
    review = _review()
    assert review["passed"] is False
    assert review["status"] == (
        "retained_bounded_presentation_improvement_"
        "photoreal_and_external_acceptance_open"
    )
    decision = review["decision"]
    assert decision["technical_candidate_passed"] is True
    assert decision["chilko_close_bank_visual_improvement_passed"] is True
    assert decision["futaleufu_rapid_side_no_new_artifact_gate_passed"] is True
    assert decision["candidate_retained"] is True
    assert decision["photoreal_acceptance_passed"] is False
    assert decision["production_promoted"] is False
    assert len(review["required_external_acceptance_gates"]) == 6


def test_config_is_fail_closed_and_only_cold_generation_opts_in() -> None:
    config = CONFIG_HEADER.read_text()
    assert "bEnableLivePresentationBankNaturalism = false" in config
    assert "LivePresentationBankNaturalismAmplitudeMeters = 0.0f" in config

    generator = GENERATOR_CPP.read_text()
    water_authoring = generator.split(
        "ARaftSimRiverWaterConfig* WaterConfig", 1
    )[1]
    chilko = water_authoring.split("else if (bChilkoLavaCanyon)", 1)[1].split(
        "else if (bFutaleufuTerminator)", 1
    )[0]
    futaleufu = water_authoring.split("else if (bFutaleufuTerminator)", 1)[1].split(
        "else if (bZambezi)", 1
    )[0]
    for block in (chilko, futaleufu):
        assert "bEnableLivePresentationBankNaturalism = true" in block
        assert "LivePresentationBankNaturalismAmplitudeMeters = 0.90f" in block
    assert generator.count("bEnableLivePresentationBankNaturalism = true") == 2


def test_runtime_changes_only_presentation_coverage_and_optical_core_vertices() -> None:
    source = RUNTIME_CPP.read_text()
    assert "ComputePresentationBankProfile" in source
    assert "ComputePresentationBankCoverage" in source
    assert "ComputePresentationBankRetreatMeters" in source
    assert "bUsesMigratedColdWaterVolumeCore" in source
    assert "VertexColors[Index].A = StationCoverage * LateralCoverage" in source
    assert "LiveVolumeCoreVertices[RiverRightIndex] = FMath::Lerp" in source
    assert "LiveVolumeCoreVertices[RiverLeftIndex] = FMath::Lerp" in source
    assert "InVertexSpacingMeters * 0.80f" in source
    assert "WetVertexMask[Index] = bSampled && Sample.bWet ? 1 : 0" in source
    assert "const bool bFullyWetCell" in source
    assert "WetVertexMask[I0] != 0 && WetVertexMask[I1] != 0" in source
    assert "LiveVolumeCoreMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision)" in source
    assert "SurfaceMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision)" in source


def test_native_contract_guards_zero_outer_coverage_and_inward_subcell_retreat() -> None:
    header = RUNTIME_HEADER.read_text()
    native = NATIVE_TEST_CPP.read_text()
    assert "static float ComputePresentationBankCoverage" in header
    assert "static float ComputePresentationBankRetreatMeters" in header
    assert "bank naturalism never covers the outermost solver-wet vertex" in native
    assert "natural bank retreat stays inward and inside one render cell" in native
    assert "disabled optical-core bank retreat is exactly zero" in native


def test_review_source_and_evidence_hashes_are_current() -> None:
    review = _review()
    source_paths = {
        "runtime_cpp_sha256": RUNTIME_CPP,
        "runtime_header_sha256": RUNTIME_HEADER,
        "config_header_sha256": CONFIG_HEADER,
        "generator_cpp_sha256": GENERATOR_CPP,
        "native_test_cpp_sha256": NATIVE_TEST_CPP,
    }
    for key, path in source_paths.items():
        assert _sha256(path) == SUPERSEDING_SOURCE_HASHES.get(
            key, review["source_hashes"][key]
        )
    for artifact in review["retained_artifacts"]:
        path = ROOT / artifact["path"]
        assert path.exists()
        assert _sha256(path) == artifact["sha256"]


def test_review_records_improvement_without_claiming_futaleufu_visual_gain() -> None:
    evidence = _review()["matched_evidence"]
    chilko = evidence["chilko_bank_closeup"]
    assert chilko["candidate_mean_edge_y_px"] < chilko["baseline_mean_edge_y_px"]
    assert (
        chilko["candidate_detrended_edge_std_px"]
        > chilko["baseline_detrended_edge_std_px"]
    )
    assert chilko["absolute_mean_edge_shift_px"] == 3.84
    assert chilko["detrended_edge_std_increase_percent"] == 16.69
    assert "does not support a claim of material Futaleufu bank improvement" in (
        evidence["futaleufu_breaking_water_side"]["visual_verdict"]
    )
