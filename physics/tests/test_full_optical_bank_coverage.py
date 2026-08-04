import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REVIEW = (
    ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "cold_water_full_optical_bank_coverage_v1_review.json"
)
AUTHORING = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment"
    / "RaftSimEditorSouthForkWaterPresentation.cpp"
)
NATIVE_TEST = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Tests"
    / "RaftSimEditorZambeziWaterTest.cpp"
)
def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _review() -> dict:
    return json.loads(REVIEW.read_text())


def test_single_layer_bank_coverage_owns_surface_and_optical_terms() -> None:
    source = AUTHORING.read_text()
    assert 'TEXT("RaftSimLiveVolumeBankCoverage")' in source
    assert 'TEXT("RaftSimLiveVolumeBankOpticalCoverage")' in source
    assert "CoveredScattering->A.Expression = OriginalScattering" in source
    assert "CoveredAbsorption->A.Expression = OriginalAbsorption" in source
    assert "CoveredBehindWaterScale->A.Expression = IdentityBehindWater" in source
    assert "CoveredBehindWaterScale->B.Expression = OriginalBehindWaterScale" in source
    assert "BankCoverageScaleExpression" in source
    assert "WaterOutput->ScatteringCoefficients.Expression = CoveredScattering" in source
    assert "WaterOutput->AbsorptionCoefficients.Expression = CoveredAbsorption" in source
    assert "WaterOutput->ColorScaleBehindWater.Expression" in source


def test_native_material_audit_requires_complete_optical_coverage() -> None:
    native = NATIVE_TEST.read_text()
    assert "bHasOpticalCoverageFeather" in native
    assert "Zambezi volume parent fades complete bank optical volume" in native
    assert "RaftSimLiveVolumeBankOpticalCoverage" in native


def test_review_is_fail_closed_and_hash_locked() -> None:
    review = _review()
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["production_promoted"] is False
    assert len(review["required_external_acceptance_gates"]) == 7

    for path, expected in review["source_hashes"].items():
        assert _sha256(ROOT / path) == expected
    for artifact in review["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.exists()
        assert _sha256(path) == artifact["sha256"]
