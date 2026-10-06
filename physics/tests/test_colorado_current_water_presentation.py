"""Focused source/numeric guards; screenshot review remains a separate gate."""
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parents[2]
MATERIAL = ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorColoradoWaterMaterial.cpp"
CURRENT = MATERIAL.with_name("RaftSimEditorCurrentWaterMaterial.cpp")


def test_current_normal_is_advected_filtered_and_colorado_scoped():
    source = MATERIAL.read_text() + CURRENT.read_text()
    code = source.split('Detail->Code = TEXT(R"HLSL(', 1)[1].split(')HLSL', 1)[0]
    assert "(UV + Origin.xy) * 3.0 - Current.xy" in code
    assert "ddx(p)" in code and "ddy(p)" in code
    assert "sin(" not in code and "WaveClock" not in code
    assert "ColoradoRun/Water/Materials/M_RaftSim_ColoradoCurrentWaterV3" in source
    assert "Material->StateId = FGuid::NewGuid()" in source
    assert "Material->GetEditorOnlyData()->Normal.Connect(0, Detail)" in source


def test_resolved_foam_survives_without_speed_painted_whitewater():
    source = MATERIAL.read_text() + CURRENT.read_text()
    assert 'Gain->ParameterName == TEXT("HydraulicFoamIntensity")' in source
    assert "Cutoff->R = -FoamCutoff" in source
    assert 'TEXT("Colorado"), 0.04f, 0.32f' in source
    assert 'SetScalar(TEXT("HydraulicWhitewaterGain"), 0.0f)' in source
    assert 'SetScalar(TEXT("HydraulicFoamCoverageGain"), 4.0f)' in source
    coverage = lambda foam: min(1.0, max(0.0, (foam * 0.9 - 0.04) * 4.0) * 1.8)
    assert coverage(0.0) == 0.0
    assert coverage(0.02) == 0.0
    assert coverage(0.26) == 1.0
    assert max(0.0, 0.26 * 0.9 - 0.28) == 0.0  # previous cutoff


def test_hance_lattice_budget_is_bounded_without_changing_solver():
    source = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp").read_text()
    section = source.split("const int32 ResolvedSubdivision =", 1)[1].split("ResolvedVertexSpacingMeters =", 1)[0]
    assert "bUsesMigratedColoradoVolumeCore" in section
    assert "FMath::Clamp(ConfiguredRapidSubdivision, 1, 3)" in section
    assert (240 + 1) * (96 + 1) == 23377
    assert (480 + 1) * (192 + 1) == 92833


def test_noise_derivative_matches_finite_difference_and_has_no_cell_jump():
    # Check the exact cubic interpolation/derivative used in the HLSL,
    # independent of corner hash values and current speed.
    a, b, c, d = 0.13, 0.78, 0.44, 0.21
    smooth = lambda f: f * f * (3 - 2 * f)
    def height(x, y):
        u, v = smooth(x), smooth(y)
        return (a + (b-a)*u) * (1-v) + (c + (d-c)*u) * v
    for x, y in [(0.1, 0.3), (0.43, 0.82), (0.99, 0.01)]:
        dx = 6*x*(1-x) * ((b-a)*(1-smooth(y)) + (d-c)*smooth(y))
        dy = 6*y*(1-y) * ((c-a)*(1-smooth(x)) + (d-b)*smooth(x))
        eps = 1e-5
        assert math.isclose(dx, (height(x+eps, y)-height(x-eps, y))/(2*eps), abs_tol=1e-7)
        assert math.isclose(dy, (height(x, y+eps)-height(x, y-eps))/(2*eps), abs_tol=1e-7)
    assert 6*0*(1-0) == 6*1*(1-1) == 0  # normal derivative at shared cell edge
