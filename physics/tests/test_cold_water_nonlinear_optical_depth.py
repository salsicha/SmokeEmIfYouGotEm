import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRESENTATION = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment"
    / "RaftSimEditorSouthForkWaterPresentation.cpp"
)
RUNTIME = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private"
    / "RaftSimWaterSurfaceActor.cpp"
)
CONFIG = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimWater/Public"
    / "RaftSimRiverWaterConfig.h"
)
REVIEW = (
    ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "cold_water_balanced_light_v1_review.json"
)

SUPERSEDING_SOURCE_HASHES = {
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
    "RaftSimWaterSurfaceActor.cpp": (
        "6d6ec2c854435d98b2acd86a4242b774d31d89c7fb473c1631279483db879dcc"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Tests/"
    "RaftSimEditorZambeziWaterTest.cpp": (
        "ab70174bd66c825076b5b14ddf6836c5d88e932bddbce55fb18f6f1ca02dbd74"
    ),
}


def test_shared_parent_remaps_only_material_depth_response() -> None:
    source = PRESENTATION.read_text()
    assert 'TEXT("RaftSimOpticalDepthResponse")' in source
    assert 'TEXT("OpticalDepthResponseExponent")' in source
    assert "OpticalDepthResponse->Base.Expression = SolverDepthMask" in source
    assert "DepthBlend->Alpha.Expression = OpticalDepthResponse" in source
    assert "RewiredDepthBlends < 2" in source


def test_runtime_defaults_to_identity_and_bounds_river_override() -> None:
    config = CONFIG.read_text()
    runtime = RUNTIME.read_text()
    assert "float LiveOpticalDepthResponseExponent = 1.0f" in config
    assert "ResolvedLiveOpticalDepthResponseExponent" in runtime
    assert "? 0.25f" in runtime
    assert "0.25f," in runtime
    assert "2.0f)" in runtime
    assert 'TEXT("OpticalDepthResponseExponent")' in runtime


def test_balanced_light_review_is_fail_closed_and_hash_locked() -> None:
    review = json.loads(REVIEW.read_text())
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["production_promoted"] is False
    assert review["runtime_rolled_out"] is True
    assert len(review["required_external_acceptance_gates"]) == 7
    assert (
        review["matched_evidence"]["futaleufu_breaking_water_side"]
        ["candidate_luma_gte_200_percent"]
        < review["matched_evidence"]["futaleufu_breaking_water_side"]
        ["baseline_luma_gte_200_percent"]
    )
    for path, expected in review["source_hashes"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == (
            SUPERSEDING_SOURCE_HASHES.get(path, expected)
        )
    for artifact in review["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
