"""Current-water optical/budget contracts; not photoreal acceptance."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATERIAL = ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorFutaleufuWaterMaterial.cpp"
RUNTIME = ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp"


def test_futaleufu_current_parent_reveals_aeration_without_speed_paint():
    source = MATERIAL.read_text()
    assert "M_RaftSim_FutaleufuCurrentWaterV5" in source
    assert 'TEXT("Futaleufu"), 0.07f, 0.22f' in source
    assert 'SetScalar(TEXT("HydraulicWhitewaterGain"), 0.0f)' in source
    assert 'SetScalar(TEXT("HydraulicFoamCoverageGain"), 3.5f)' in source
    assert 'SetScalar(TEXT("HydraulicFoamColorCoreGain"), 1.8f)' in source
    response = lambda foam: min(1, max(0, foam * 0.9 - 0.07) * 3.5 * 1.8)
    assert response(0.03) == response(0) == 0
    assert response(0.2614) == 1
    assert max(0, 0.2614 * 0.9 - 0.28) == 0


def test_futaleufu_budget_preserves_single_surface_and_solver_authority():
    source = RUNTIME.read_text()
    subdivision = source.split("const int32 ResolvedSubdivision =", 1)[1].split("ResolvedVertexSpacingMeters =", 1)[0]
    assert "bUsesMigratedFutaleufuVolumeCore && bSingleLiveWaterSurfaceEnabled" in subdivision
    assert "FMath::Clamp(ConfiguredRapidSubdivision, 1, 3)" in subdivision
    assert "ResolvedPresentationStandingWaveScale = 0.0f" in source
    assert "ResolvedPresentationHydraulicReliefScale" in source
    assert "ComputeCoupledHydraulicReliefMeters" in source


def test_cold_water_palette_is_scoped_and_depth_differentiated():
    source = RUNTIME.read_text()
    shallow = source.split("const FLinearColor ResolvedLiveShallowSurfaceColor =", 1)[1].split("const FLinearColor ResolvedLiveDeepSurfaceColor", 1)[0]
    deep = source.split("const FLinearColor ResolvedLiveDeepSurfaceColor =", 1)[1].split("const FLinearColor ResolvedLiveReflectedSkyColor", 1)[0]
    assert "bUsesMigratedFutaleufuVolumeCore" in shallow
    assert "FLinearColor(0.012f, 0.085f, 0.100f, 1.0f)" in shallow
    assert "FLinearColor(0.003f, 0.035f, 0.046f, 1.0f)" in deep
    assert "bUsesLegacyChilkoPresentationDefaults" in shallow


def test_triangular_gradient_is_continuous_and_matches_height_derivative():
    import math
    import random
    source = (MATERIAL.parent / "RaftSimEditorCurrentWaterMaterial.cpp").read_text()
    assert 'bUseTriangularCurrentGradient = RiverLabel == TEXT("Futaleufu")' in source
    assert "result += t*t*t*t*g - 8.0*t*t*t*d*x" in source

    def hash2(x, y):
        q = [v * 0.1031 % 1 for v in (x, y, x)]
        d = sum(q[i] * (q[(i+1) % 3] + 33.33) for i in range(3))
        q = [v+d for v in q]
        return ((q[0]+q[1])*q[2]) % 1

    def sample(px, py):
        f, g = 0.3660254038, 0.2113248654
        skew = (px+py)*f
        cx, cy = math.floor(px+skew), math.floor(py+skew)
        x0, y0 = px-cx+(cx+cy)*g, py-cy+(cx+cy)*g
        corner = (1, 0) if x0 > y0 else (0, 1)
        value, dx, dy = 0.0, 0.0, 0.0
        for ox, oy in ((0, 0), corner, (1, 1)):
            x, y = x0-ox+(ox+oy)*g, y0-oy+(ox+oy)*g
            gx = hash2(cx+ox, cy+oy)*2-1
            gy = hash2(cx+ox+47.17, cy+oy+47.17)*2-1
            inv = 1/math.sqrt(max(gx*gx+gy*gy, 0.0001))
            gx, gy = gx*inv, gy*inv
            t, d = max(0.5-x*x-y*y, 0), gx*x+gy*y
            value += t**4*d
            dx += t**4*gx - 8*t**3*d*x
            dy += t**4*gy - 8*t**3*d*y
        return value*45, dx*45, dy*45

    rng = random.Random(903)
    points = [(rng.uniform(-30, 30), rng.uniform(-30, 30)) for _ in range(80)]
    points += [(a, a) for a in (0, .1, .23, 1.2, -2.3)]
    eps = 1e-5
    for x, y in points:
        _, dx, dy = sample(x, y)
        nx = (sample(x+eps, y)[0] - sample(x-eps, y)[0]) / (2*eps)
        ny = (sample(x, y+eps)[0] - sample(x, y-eps)[0]) / (2*eps)
        assert abs(dx-nx) < 2e-4 and abs(dy-ny) < 2e-4
        assert math.dist(sample(x+eps, y)[1:], sample(x-eps, y)[1:]) < .003
