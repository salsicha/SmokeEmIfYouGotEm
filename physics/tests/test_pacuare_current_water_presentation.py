"""Optical contract guards, not visual or hydraulic acceptance."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
MATERIALS = ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials"


def test_pacuare_uses_an_isolated_current_parent_and_aeration_only_froth():
    source = (MATERIALS / "RaftSimEditorPacuareWaterMaterial.cpp").read_text()
    assert "M_RaftSim_PacuareCurrentWaterV2" in source
    assert 'TEXT("Pacuare"), 0.06f, 0.24f' in source
    assert 'SetScalar(TEXT("HydraulicWhitewaterGain"), 0.0f)' in source
    assert 'SetScalar(TEXT("HydraulicFoamCoverageGain"), 4.5f)' in source
    assert 'SetScalar(TEXT("HydraulicFoamColorCoreGain"), 1.8f)' in source
    response = lambda x: min(1.0, max(0.0, 0.9*x-0.06)*4.5*1.8)
    assert response(0.0) == response(0.02) == 0
    assert response(0.2188) == 1.0
    assert max(0.0, 0.2188*0.9-0.28) == 0.0


def test_lattice_budget_is_scoped_to_pacuare_single_surface():
    source = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp").read_text()
    assert 'TEXT("pacuare_river_costa_rica")' in source
    block = source.split("const int32 ResolvedSubdivision =", 1)[1].split("ResolvedVertexSpacingMeters =", 1)[0]
    assert "bUsesPacuarePresentation && bSingleLiveWaterSurfaceEnabled" in block
    assert "FMath::Clamp(ConfiguredRapidSubdivision, 1, 3)" in block
    assert 23377 < 92833 / 3.9


def test_shared_authoring_refactor_preserves_reviewed_colorado_normal_code():
    source = (MATERIALS / "RaftSimEditorCurrentWaterMaterial.cpp").read_text()
    code = source.split('Detail->Code = TEXT(R"HLSL(', 1)[1].split(')HLSL', 1)[0]
    evidence = json.loads((ROOT / "docs/reports/images/2026-09-05-colorado-current-water/material-audit.json").read_text())
    assert code.strip() == evidence["normal_code"].strip()
    assert "Cutoff->R = -FoamCutoff" in source
    assert "if (!bFoundCutoff)" in source
    assert "Material->StateId = FGuid::NewGuid()" in source
    colorado = (MATERIALS / "RaftSimEditorColoradoWaterMaterial.cpp").read_text()
    assert 'TEXT("Colorado"), 0.04f, 0.32f' in colorado
