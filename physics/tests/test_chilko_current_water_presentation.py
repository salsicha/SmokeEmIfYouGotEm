"""Chilko optical and presentation-budget guards, not photoreal acceptance."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATERIALS = ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials"


def test_chilko_resolved_aeration_survives_without_speed_whitening():
    source = (MATERIALS / "RaftSimEditorChilkoWaterMaterial.cpp").read_text()
    assert "M_RaftSim_ChilkoCurrentWaterV4" in source
    assert 'TEXT("Chilko"), 0.045f, 0.18f' in source
    assert 'SetScalar(TEXT("HydraulicWhitewaterGain"), 0.0f)' in source
    assert 'SetScalar(TEXT("ChilkoCurrentNormalStrength"), 0.18f)' in source
    assert 'SetScalar(TEXT("HydraulicFoamCoverageGain"), 4.0f)' in source
    assert 'SetScalar(TEXT("HydraulicFoamColorCoreGain"), 1.8f)' in source
    assert 'SetScalar(TEXT("WhitewaterFrothLaceModulationFloor"), 0.10f)' in source
    assert 'SetScalar(TEXT("HydraulicFoamColorBreakupBias"), 0.0f)' in source
    response = lambda foam: min(1, max(0, foam*.9-.045)*4*1.8)
    assert response(0) == response(.03) == 0
    assert response(.2614) == 1
    assert max(0, .2614*.9-.28) == 0


def test_chilko_uses_filtered_triangular_current_gradient():
    source = (MATERIALS / "RaftSimEditorCurrentWaterMaterial.cpp").read_text()
    choice = source.split("const bool bUseTriangularCurrentGradient =", 1)[1].split(";", 1)[0]
    assert 'RiverLabel == TEXT("Chilko")' in choice
    assert 'RiverLabel == TEXT("Futaleufu")' in choice
    assert "simplexGradient(float2 p)" in source
    assert "ddx(p)" in source and "ddy(p)" in source
    assert "- Current.xy" in source


def test_chilko_lattice_budget_is_single_surface_scoped():
    source = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp").read_text()
    block = source.split("const int32 ResolvedSubdivision =", 1)[1].split("ResolvedVertexSpacingMeters =", 1)[0]
    assert "bUsesMigratedChilkoVolumeCore && bSingleLiveWaterSurfaceEnabled" in block
    assert "FMath::Clamp(ConfiguredRapidSubdivision, 1, 3)" in block
    assert "ComputeCoupledHydraulicReliefMeters" in source
    assert "ComputeCoupledStandingWave" in source
    assert "bUsesMigratedChilkoVolumeCore ? 0.10f : 0.02f" in source


def test_chilko_breaking_relief_uses_persistent_support_profile():
    source = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp").read_text()
    assert "bSharedBreakingReliefEnabled = bSpatialBreakingReview ||" in source
    assert "(bUsesMigratedChilkoVolumeCore &&" in source
    assert "CVarRaftSimChilkoSharedBreakingRelief.GetValueOnGameThread() != 0)" in source
    assert "bSharedBreakingReliefEnabled &= bSingleLiveWaterSurfaceEnabled" in source
    assert "SmoothedCm != 0.0f && !bSharedBreakingReliefEnabled" in source
    assert "bSharedBreakingReliefEnabled ? Site.PresentationWeight : 1.0f" in source
    shared = source.split("const float SharedBreakingReliefMeters =", 1)[1].split("PocketFoam *=", 1)[0]
    assert "ComputeCoupledBreakingReliefMeters" in shared
    assert "SupportSites" in shared
    assert "ResolvedPresentationHydraulicReliefScale" in shared
    assert "ShoreDisplacementWeight[VertexIndex]" in shared


def test_chilko_crest_foam_does_not_regenerate_trough_and_raw_tail_foam():
    source = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp").read_text()
    assert "bCrestLocalizedFoam = bSharedBreakingReliefEnabled &&" in source
    assert "CVarRaftSimChilkoCrestFoam.GetValueOnGameThread()" in source
    assert "? FMath::Max(HydraulicRelief, 0.0f)" in source
    assert source.count("if (!bCrestLocalizedFoam)") == 2
    assert "0.015f, 0.09f, SharedBreakingReliefMeters" in source
    # Existing transport/attack/release remains after localized generation.
    assert "FieldPosition - FieldVelocity * FoamDeltaSeconds" in source
    assert "Advected *= DecayFactor" in source
    assert "-FoamAttackDeltaSeconds / 0.22f" in source


def test_terrain_survey_compares_fixed_coordinate_water_and_terrain():
    source = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimSurveyCommand.cpp").read_text()
    assert "CentreWorld, FixedCentreWater) && FixedCentreWater.bWet" in source
    assert "FixedCentreWater.SurfaceHeightMeters * 100.0f - TerrainZCm" in source
    assert "TerrainClearanceCm = SupportZCm - TerrainZCm" not in source
    assert "fixed_solver_bed_z_cm=" in source


def test_every_water_data_update_preserves_linear_foam_depth_and_speed():
    import re
    from collections import Counter
    source = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp").read_text()
    calls = re.findall(r"(\w+)->UpdateMeshSection_LinearColor\((.*?)\);", source, re.S)
    # The refined/macro uploads added two SurfaceMesh paths and replaced the
    # former single upload. Guard all seven actual sites, not a stale total.
    assert Counter(owner for owner, _ in calls) == {
        'SurfaceMesh': 3, 'LiveVolumeCoreMesh': 3, 'RapidFoamMesh': 1}
    assert all(_has_explicit_linear_upload_argument(call) for _, call in calls)


def _has_explicit_linear_upload_argument(arguments):
    import re
    # Comments are documentation, not semantics. A trailing explicit false is
    # required: omitted arguments silently select the engine's default.
    without_comments = re.sub(r'/\*.*?\*/|//[^\n]*', '', arguments, flags=re.S)
    return bool(re.search(r',\s*false\s*$', without_comments))


def test_linear_upload_guard_rejects_default_and_srgb_conversion():
    assert _has_explicit_linear_upload_argument('0, Colors, Tangents, false')
    assert _has_explicit_linear_upload_argument('0, Colors, Tangents, /*bSRGBConversion=*/false')
    assert not _has_explicit_linear_upload_argument('0, Colors, Tangents')
    assert not _has_explicit_linear_upload_argument('0, Colors, Tangents, /*bSRGBConversion=*/true')
    assert not _has_explicit_linear_upload_argument('0, Colors, Tangents /* false */')


def test_chilko_spray_requires_a_wet_owned_crest_and_uses_surface_height():
    source = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterVfxActor.cpp").read_text()
    assert 'GetMapName().EndsWith(TEXT("L_LavaCanyon"))' in source
    assert "? Sites[SiteIndex].PersistenceWeight : Sites[SiteIndex].PresentationWeight" in source
    assert "bCrestOwnedSpray && SprayPresence <= 0.01f" in source
    assert "SampleRaftSupportSurfaceAtWorldPosition(" in source
    assert "SupportHeightM = Support.SurfaceHeightMeters;" in source
    assert "if (!bSouthForkBallisticReview)" in source
    assert "SurfaceOrigin.Z = SupportHeightM * CmPerM;" in source
    assert "Intensity > 0.12f && bWetCrest && CrestOwnership > 0.01f" in source
    assert "OwnedDensity = DistanceDensity * CrestOwnership" in source
    assert source.count("* OwnedDensity, bHorizontalSourcePlane)") == 3
    assert "bCrestOwnedSpray ? 3.0f : 60.0f" in source
    assert "bCrestOwnedSpray ? 3.0f : 32.0f" in source
    assert "bCrestOwnedSpray ? 0.12f * FMath::Sin(Site.ShapeSeed)" in source


def test_chilko_spray_plane_has_an_independent_bound_rotation():
    source = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterVfxActor.cpp").read_text()
    author = (MATERIALS / "RaftSimEditorNiagaraWaterVfx.cpp").read_text()
    assert 'SetVariableQuat(TEXT("User.SourcePlaneRotation")' in source
    assert "EmitterRotation.Inverse() * SurfaceRotation" in source
    assert "bHorizontalSourcePlane = bSouthForkCrestOwnedSpray ||" in source
    assert "(bCrestOwnedSpray && CVarChilkoSprayPlane.GetValueOnGameThread() != 0)" in source
    assert "Shape->ShapeRotation.ParameterBinding = Rotation" in author
    assert "SetParameterValue<FQuat4f>(FQuat4f::Identity" in author


def test_chilko_gameplay_preserves_authored_foam_breakup_gain():
    source = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp").read_text()
    guard = source.split("if (!bUsesMigratedChilkoVolumeCore)", 1)[1].split("}", 1)[0]
    assert 'TEXT("HydraulicFoamColorBreakupGain")' in guard
    authored = (MATERIALS / "RaftSimEditorChilkoWaterMaterial.cpp").read_text()
    assert 'SetScalar(TEXT("HydraulicFoamColorBreakupGain"), 0.58f)' in authored


def test_chilko_density_response_preserves_sparse_foam_and_brightens_dense_cores():
    source = (MATERIALS / "RaftSimEditorCurrentWaterMaterial.cpp").read_text()
    assert 'RiverLabel == TEXT("Chilko") && !ConfigureChilkoDensityFoam' in source
    assert 'Input(TEXT("Lace"), Biased->A.Expression)' in source
    assert "fwidth(Lace)" in source
    def smooth(a, b, x):
        t = min(1, max(0, (x-a)/(b-a)))
        return t*t*(3-2*t)
    def response(aeration, lace, legacy, blend=1):
        dense = smooth(.28, .72, aeration)
        threshold = .62 + (.06-.62)*dense
        packed = smooth(threshold-.06, threshold+.06, lace)*.98
        return legacy + (max(legacy, packed)-legacy)*dense*blend
    assert response(0, .9, 0) == 0
    assert response(.2, .5, .12) == .12
    assert response(.9, .5, .29) > .95
    assert abs(response(.9, 0, 0)) < 1e-12
    assert response(.9, .5, .29, 0) == .29
    for step in range(100):
        a = step / 100
        assert 0 <= response(a, .3, .1) <= 1
        assert abs(response(a+.001, .3, .1)-response(a, .3, .1)) < .025
        assert response(a+.001, .3, .1) >= response(a, .3, .1)


def test_chilko_dense_foam_optics_share_coverage_without_changing_geometry():
    source = (MATERIALS / "RaftSimEditorCurrentWaterMaterial.cpp").read_text()
    optics = source.split('OpticalFoam->Code =', 1)[1].split('return true;', 1)[0]
    assert "return lerp(Legacy, Density, saturate(Blend));" in optics
    assert 'TEXT("FoamRoughness")' in optics
    assert 'TEXT("FoamWaterOpacity")' in optics
    assert 'TEXT("SpeedAerationFraction")' in optics
    assert "if (!bRoughness || !bOpacity || !bScattering)" in optics
    assert "WorldPositionOffset" not in optics
    assert "OpacityMask.Connect" not in optics
    assert "LegacyFoam ||" in optics  # permits idempotent rewiring, not arbitrary pins
    for legacy, density in [(0, 0), (.1, .1), (.15, .7), (.2, .98)]:
        values = [legacy+(density-legacy)*i/100 for i in range(101)]
        assert values[0] == legacy
        assert abs(values[-1]-density) < 1e-12
        assert all(legacy <= value <= density+1e-12 for value in values)


def test_chilko_ballistic_spray_is_scoped_and_preserves_emission_controls():
    source = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterVfxActor.cpp").read_text()
    selection = source.split("if (PhotographicReviewVersion == 0 && GetWorld()", 1)[1].split("if (!RapidCrestSpraySystem", 1)[0]
    assert 'EndsWith(TEXT("L_LavaCanyon"))' in selection
    assert 'TEXT("RaftSimChilkoLegacySpray")' in selection
    assert "if (ChilkoRoller && ChilkoSpray)" in selection
    author = (MATERIALS / "RaftSimEditorNiagaraWaterVfx.cpp").read_text()
    variant = author.split("void CreateChilkoBallisticSpray", 1)[1].split("static FAutoConsoleCommand", 1)[0]
    assert "StaticDuplicateObject(Source" in variant
    assert "-980.665f" in variant
    assert "ENiagaraSpriteAlignment::Unaligned" in variant
    assert "SpawnRate" not in variant
    assert "SourcePlaneCm" not in variant
    for maximum_speed, minimum_life in [(260, .65), (380, .85)]:
        assert 2 * maximum_speed / 980.665 < minimum_life
