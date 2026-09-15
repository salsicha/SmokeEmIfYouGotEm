"""Guards for the live/static full-reach water contract (not visual acceptance)."""
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV = ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment"


def test_bank_terrain_probes_skip_blockers_without_expanding_the_ray_budget():
    source = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
    helper = source.split('bool ARaftSimWaterSurfaceActor::TraceTerrainSurface', 1)[1].split(
        'void ARaftSimWaterSurfaceActor::InvalidateMissedTerrainProbes', 1)[0]
    assert 'Attempt < 4 && RemainingRayBudget > 0' in helper
    assert '--RemainingRayBudget' in helper
    assert 'TerrainParams.AddIgnoredActor(Actor)' in helper
    assert 'Actor->ActorHasTag(TEXT("RaftSimFullReachTerrain"))' in helper
    assert 'ALandscapeProxy' not in helper
    assert source.count('ProbeParams, ProbeBudget, Hit)') == 2
    assert source.count('VisualBankProbeState[Index] = ProbeBudget == 0 ? 0 : 2') == 2
    assert 'kVisualBankProbeBudgetPerRefresh = 192' in source
    streaming = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimRiverWaterStreamingActor.cpp').read_text()
    assert 'if (bTerrainArrived)' in streaming
    assert 'It->InvalidateMissedTerrainProbes()' in streaming


def test_static_water_presentation_cannot_block_terrain_or_boats():
    streaming = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimRiverWaterStreamingActor.cpp').read_text()
    visibility = streaming.split('void ARaftSimRiverWaterStreamingActor::ApplyStaticFlowBandVisibilityToActor(', 1)[1].split(
        'void ARaftSimRiverWaterStreamingActor::HandleLevelAddedToWorld(', 1)[0]
    assert 'if (bBakedFoamOverlay || bIsBandPresentation)' in visibility
    assert 'Actor->SetActorEnableCollision(false);' in visibility
    assert visibility.index('Actor->SetActorEnableCollision(false);') < visibility.index('Actor->SetActorHiddenInGame(true);')
    assert 'Terrain' not in visibility.split('if (bBakedFoamOverlay || bIsBandPresentation)', 1)[0]


def test_south_fork_crest_spray_experiment_is_opt_in_and_map_scoped():
    source = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterVfxActor.cpp').read_text()
    cvar = source.split('CVarSouthForkCrestSpray(', 1)[1].split(';', 1)[0]
    assert 'TEXT("raftsim.SouthForkCrestSpray"), 0,' in cvar
    gating = source.split('const bool bSouthForkCrestOwnedSpray =', 1)[1].split('TArray<int32> RankedSiteIndices', 1)[0]
    assert 'IsSouthForkSprayReviewMap(GetWorld()->GetMapName()) &&' in gating
    scope = source.split('bool ARaftSimWaterVfxActor::IsSouthForkSprayReviewMap(', 1)[1].split(
        'FQuat ARaftSimWaterVfxActor::ComputeRapidSourcePlaneRotation(', 1)[0]
    assert 'Name == TEXT("L_SouthForkAmerican_FullReach")' in scope
    assert 'Name == TEXT("SouthForkRegisteredRockPlayable")' in scope
    assert 'Name.Mid(7, Separator - 7).IsNumeric()' in scope
    assert 'EndsWith' not in scope  # no unrelated suffix-lookalike maps
    assert 'CVarSouthForkCrestSpray.GetValueOnGameThread() != 0' in gating
    assert 'EndsWith(TEXT("L_LavaCanyon")) &&' in gating
    assert 'CVarChilkoCrestSpray.GetValueOnGameThread() != 0' in gating


def test_local_fluid_clock_phase_matches_render_and_raft_support():
    support = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimWater/Private/RaftSimWaterRuntimeAdapter.cpp').read_text()
    rendering = (ENV / 'RaftSimEditorSouthForkWaterPresentation.cpp').read_text()
    assert 'WaveClockSeconds * 1.70f +' in support
    assert '2.90f * BoilNoiseB + 2.0f * UE_PI * BoilNoiseA' in support
    assert 'WaveClock * 1.70 + 2.90 * boilNoiseB + 6.2831853 * boilNoiseA' in rendering
    assert '(1.45f + 0.55f * BoilNoiseB)' not in support


def test_south_fork_falling_spray_review_reuses_assets_without_promoting_defaults():
    source = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterVfxActor.cpp').read_text()
    selection = source.split('if (PhotographicReviewVersion == 0 && GetWorld() &&', 2)[2].split('// The retained V4/V5', 1)[0]
    assert 'IsSouthForkSprayReviewMap(GetWorld()->GetMapName())' in selection
    assert 'FParse::Param(FCommandLine::Get(), TEXT("RaftSimSouthForkBallisticSpray"))' in selection
    assert 'if (BallisticRoller && BallisticSpray)' in selection
    assert 'RapidRollerSystem = BallisticRoller;' in selection
    assert 'RapidCrestSpraySystem = BallisticSpray;' in selection
    assert 'StaticDuplicateObject' not in selection and 'Save' not in selection
    ownership = source.split('const bool bSouthForkCrestOwnedSpray =', 1)[1].split('TArray<int32> RankedSiteIndices', 1)[0]
    assert 'TEXT("RaftSimSouthForkBallisticSpray")' in ownership
    assert 'const bool bHorizontalSourcePlane = bSouthForkCrestOwnedSpray' in ownership


def test_local_spray_presence_is_independent_of_remote_geometry_ranking():
    vfx = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterVfxActor.cpp').read_text()
    surface = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
    assert 'Published.PersistenceWeight = Persistent.Envelope;' in surface
    assert '? Sites[SiteIndex].PersistenceWeight : Sites[SiteIndex].PresentationWeight' in vfx
    assert '? Site.PersistenceWeight : Site.PresentationWeight' in vfx
    assert 'RankedSiteIndices.Sort(' in vfx  # retain nearest-site bounded pool
    assert 'MaxActiveRapidNiagaraSites,' in vfx
    assert 'if (!bSouthForkBallisticReview)' in vfx
    assert 'SurfaceOrigin.Z = SupportHeightM * CmPerM;' in vfx
    assert 'bEnabled = Intensity > 0.12f && bWetCrest && CrestOwnership > 0.01f' in vfx


def test_visible_carrier_spray_lookup_uses_rendered_triangles_without_physics_queries():
    surface = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
    lookup = surface.split('bool ARaftSimWaterSurfaceActor::SampleVisibleCarrierAtRiverCoordinates(', 1)[1].split('bool ARaftSimWaterSurfaceActor::IsBreakingLipVisible()', 1)[0]
    assert 'CoordinatesM - RiverCoordinatesM[0]' in lookup
    assert 'SourceVertices = bGpuCarrier ? Vertices : RenderedLiveVolumeCoreVertices' in lookup
    assert 'GetActorTransform().TransformPosition(SourceVertices[Index]) : SourceVertices[Index]' in lookup
    assert 'WaterAdapter->HasCartesianWaterCoordinates()' in lookup
    assert 'CartesianShorelineMesh->GetCellOffsets()' in lookup
    assert '!SampleCartesianCarrierPosition(QueryWorld,OutPositionCm,bWet) || !bWet' in lookup
    assert 'U + V <= 1.0f' in lookup
    assert 'SprayWetCarrierMask[Index] == 0' in lookup
    mask = surface.split('SprayWetCarrierMask.SetNumUninitialized', 1)[1].split('if (!bLoggedHydraulicReliefDiagnostics', 1)[0]
    assert 'LiveSolverWetVertexMask[Index] != 0' in mask
    assert 'WetVertexMask[Index] != 0' in mask
    assert 'VisualBankTerrainZCm[Index] + 2.0f' in lookup
    assert 'WaterSamples[Index].DepthMeters >= 0.10f' in mask
    assert 'SampleWater' not in lookup and 'LineTrace' not in lookup
    assert 'WorldToRiverCoordinates' not in lookup
    vfx = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterVfxActor.cpp').read_text()
    assert 'bCrestOwnedSpray && (!bSouthForkBallisticReview || bLogSprayReview)' in vfx
    assert 'FVector2D(0, -1.5), FVector2D(0, 1.5)' in vfx
    assert 'FVector2D(-0.8, 0), FVector2D(0.8, 0)' in vfx


def test_carrier_triangle_lookup_matches_diagonal_and_linear_grade():
    # Both triangles agree on the shared edge, preserve a linear grade and
    # use nonnegative weights, including all four exact grid corners.
    for u in [i / 20 for i in range(21)]:
        for v in [i / 20 for i in range(21)]:
            if u + v <= 1:
                points, weights = [(0, 0), (0, 1), (1, 0)], [1-u-v, v, u]
            else:
                points, weights = [(1, 0), (0, 1), (1, 1)], [1-v, 1-u, u+v-1]
            assert min(weights) >= -1e-12 and abs(sum(weights)-1) < 1e-12
            height = sum(w * (3*x + 7*y + 2) for w, (x, y) in zip(weights, points))
            assert abs(height - (3*u + 7*v + 2)) < 1e-12


def test_spatial_breaking_review_is_map_scoped_and_keeps_support_in_sync():
    source = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
    selection = source.split('bSpatialBreakingReview =', 1)[1].split(';', 1)[0]
    assert 'L_SouthForkAmerican_FullReach' in selection
    assert 'RaftSimSpatialBreakingReview' in selection
    assert 'bSharedBreakingReliefEnabled = bSpatialBreakingReview ||' in source
    weighting = source.split('const float WeightTarget =', 1)[1].split('Persistent.PresentationWeight =', 1)[0]
    assert '(bSpatialBreakingReview || SiteIndex < kMaximumBreakingPresentationSites)' in weighting
    assert 'Camera' not in weighting and 'Raft' not in weighting
    assert 'SupportSite.bLocalEnvelopeCap = bSpatialBreakingReview;' in source
    assert 'ConfigureRaftSupportBreakingSites(\n            SupportSites,' in source
    assert '? StationBreakingSites[VertexIndex % GridStationN].Support : SupportSites' in source
    assert '? StationBreakingSites[Index % GridStationN].Presentation : WeightedPresentationSites' in source
    assert 'RiverCoordinatesM[VertexIndex], LocalSupportSites,' in source


def test_spatial_station_buckets_cover_all_exact_influence_rows():
    import math
    for spacing in (0.5, 0.75, 1.5, 3.0):
        start, count = 8232.0, 321
        for site in (8000.0, 8232.0, 8358.123, 8454.0, 8900.0):
            for length in (2.0, 3.2, 7.0):
                low, high = site-3*length, site+7*length
                first = max(0, min(count, math.floor((low-start)/spacing)))
                last = max(-1, min(count-1, math.ceil((high-start)/spacing)))
                for row in range(count):
                    position = start + row*spacing
                    if low <= position <= high:
                        assert first <= row <= last
                assert 0 <= first <= count and -1 <= last < count


def test_spatial_presentation_envelope_has_continuous_edges():
    def smooth(a, b, value):
        t = max(0, min(1, (value-a)/(b-a)))
        return t*t*(3-2*t)
    def weight(x, y):
        return smooth(-32, -30, x)*(1-smooth(20.5, 23, x))*(1-smooth(10, 12, abs(y)))
    for x in (-100, -32, 23, 100):
        assert weight(x, 0) == 0
    for y in (-20, -12, 12, 20):
        assert weight(0, y) == 0
    assert weight(0, 0) == 1
    for x in (-32, -30, 20.5, 23):
        assert abs(weight(x+.001, 0)-weight(x-.001, 0)) < 1e-5
    for y in (-12, -10, 10, 12):
        assert abs(weight(0, y+.001)-weight(0, y-.001)) < 1e-5


def test_troublemaker_terrain_review_is_transient_and_uses_bed_not_waterline():
    source = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimTroublemakerTerrainReview.cpp').read_text()
    assert source.startswith('#if WITH_EDITOR')
    assert 'World->IsGameWorld()' in source
    assert 'EndsWith(TEXT("L_SouthForkAmerican_FullReach"))' in source
    assert 'TEXT("SM_south_fork_02_Terrain")' in source
    assert 'FMeshDescription Description = *Source' in source
    assert 'DuplicateObject<UStaticMesh>(Original, GetTransientPackage())' in source
    assert 'Candidate->SetFlags(RF_Transient)' in source
    assert 'Sample.BedHeightMeters - Position.Z / 100.0' in source
    assert 'Sample.SurfaceHeightMeters' not in source
    assert 'SavePackage' not in source
    assert 'FMath::Abs(DeltaM) > 5.0' in source
    assert 'Body->InvalidatePhysicsData()' in source
    assert 'WorldToRiverCoordinates' not in source
    assert '8064.0 + UV.Y * 4032.0, -256.0 + UV.X * 512.0' in source
    assert 'TMap<FIntPoint, FVertexID> EdgeVertices' in source
    assert 'Mesh.DeleteTriangle(Triangle)' in source
    assert 'It->InvalidateTerrainProbes()' in source
    assert 'FMath::Clamp(CTerrainSubdivision.GetValueOnGameThread(), 0, 3)' in source
    assert 'Mesh.Compact(Remappings)' in source


def test_bed_aligned_shallows_require_measured_terrain_before_ignoring_old_mask():
    source = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp').read_text()
    block = source.split('const bool bMeasuredBedAligned =', 1)[1].split('    // Recompute the crop', 1)[0]
    assert 'VisualBankProbeState[Index] == 1' in block
    assert 'FMath::IsFinite(Sample.BedHeightMeters)' in block
    assert 'VisualBankTerrainZCm[Index]) <= 10.0f' in block
    assert 'BaselineKeepProbeWanted[Index] = 1' in block
    assert 'if (!bMeasuredBedAligned && !bBaselineWet &&' in block
    assert 'else if (!bMeasuredBedAligned && bBaselineWet &&' in block
    film = source.split('const bool bMeasuredBedAligned =', 2)[2].split('VisualFilmCullMask[Index] =', 1)[0]
    assert 'LiveSolverWetVertexMask[Index] != 0' in film
    assert 'VisualBankTerrainZCm[Index]) <= 10.0f' in film
    assert 'if (bMeasuredBedAligned)' in film
    assert 'VisualFilmCullState[Index] = 0' in film


def test_terrain_refinement_retains_perimeter_edges_and_winding():
    # Match the four-child midpoint split: no cracks on shared edges and the
    # child areas exactly cover their parent, before any bed displacement.
    import numpy as np
    a, b, c = np.array([0., 0.]), np.array([4., 0.]), np.array([0., 4.])
    ab, bc, ca = (a+b)/2, (b+c)/2, (c+a)/2
    def twice_area(t):
        u, v = t[1]-t[0], t[2]-t[0]
        return u[0]*v[1]-u[1]*v[0]
    children = [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
    assert all(twice_area(t) > 0 for t in children)
    assert sum(twice_area(t) for t in children) == twice_area((a,b,c))
    assert 4 / 2**3 == .5
    # Position and attributes at a shared midpoint are orientation-independent.
    assert np.array_equal((a+b)/2, (b+a)/2)


def test_water_capture_series_does_not_overwrite_pending_frame_requests():
    source = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCaptureCommand.cpp').read_text()
    series = source.split('static void HandleCaptureSeries(', 1)[1].split('static FAutoConsoleCommandWithWorldAndArgs GCaptureSeriesCommand', 1)[0]
    gate = series.index('if (FScreenshotRequest::IsScreenshotRequested()) return;')
    assert gate < series.index('FScreenshotRequest::RequestScreenshot(')
    assert gate < series.index('++(*Taken)')
    assert 'capture-series request: index=%d world_s=%.3f frame=%llu' in series


def test_water_capture_series_records_actual_raft_and_camera_positions():
    source = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCaptureCommand.cpp').read_text()
    series = source.split('static void HandleCaptureSeries(', 1)[1].split('static FAutoConsoleCommandWithWorldAndArgs GCaptureSeriesCommand', 1)[0]
    assert 'raft_river_valid=%d raft_station_m=%.3f raft_lateral_m=%.3f' in series
    assert 'camera_valid=%d camera_world_cm=%s' in series
    assert 'Raft->GetActorLocation(), RaftRiver, Tangent, LeftNormal' in series
    assert 'Camera->GetCameraLocation().ToCompactString()' in series


def test_fixed_water_review_camera_converts_surface_elevation_only_once():
    source = (ROOT / 'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCaptureCommand.cpp').read_text()
    fixed = source.split('if (CameraPreset.StartsWith(TEXT("river_station")))', 1)[1].split('if (!bCamera && !CameraPreset.IsEmpty())', 1)[0]
    assert 'RaftSimReviewCoordinates::GetMap(W, Water)' in fixed
    assert 'Progress->RiverToWorldPosition(FVector2D(FocusStationM, FocusLateralM)' in fixed
    assert 'Water->SampleWaterAtWorldPosition(Focus, Sample)' in fixed
    assert 'Water->GetRiverVerticalDatumM(), Focus)' in fixed
    assert 'Water->GetRiverVerticalDatumM(), Ahead)' in fixed
    assert 'Focus.Z = Ahead.Z = Sample.SurfaceHeightMeters * 100.0f' in fixed
    assert 'Sample.SurfaceHeightMeters, Focus)' not in fixed
    assert 'refusing misleading fallback capture' in fixed
    assert 'TeleportForTesting' not in fixed


def test_static_water_build_preserves_absolute_station_uv_precision():
    source = (ENV / "RaftSimEditorSouthForkMeshAuthoring.cpp").read_text()
    assert 'AssetPackagePath.Contains(TEXT("/SouthForkFullReach/Water/"))' in source
    assert "BuildSettings.bUseFullPrecisionUVs = true" in source
    assert "Mesh->Build(false)" in source
    assert "if (bComplexCollision || bRiverWaterMesh)" in source
    # Reproduce why the lower river cannot use float16 absolute station UVs.
    half = lambda value: struct.unpack("e", struct.pack("e", value))[0]
    assert half(48000 / 3) == half(48001.5 / 3)
    assert struct.unpack("f", struct.pack("f", 48000 / 3))[0] != struct.unpack("f", struct.pack("f", 48001.5 / 3))[0]


def test_authored_tiles_match_live_surface_detail():
    source = (ENV / "RaftSimEditorSouthForkWaterPresentation.cpp").read_text()
    values = {
        "CalmRippleStrength": "0.08", "FlowRippleStrength": "0.14",
        "FoamRippleStrength": "0.25", "RippleGrazingFloor": "0.50",
        "FlowNormalSteepness": "2.0", "SlickNormalFloor": "0.60",
        "WaterRoughness": "0.22", "HydraulicFoamColorBreakupGain": "3.0",
        "WhitewaterFrothLaceModulationFloor": "0.02", "FoamRoughness": "0.80",
    }
    for name, expected in values.items():
        assignments = re.findall(r'FMaterialParameterInfo\(TEXT\("' + name + r'"\)\), ([\d.]+)f', source)
        assert assignments and all(float(value) == float(expected) for value in assignments), name
    assert 'FMaterialParameterInfo(TEXT("SouthForkTurbulenceWPOStrength")), 0.0f' in source


def test_boils_require_water_depth_and_migration_supplies_it():
    source = (ENV / "RaftSimEditorSouthForkWaterPresentation.cpp").read_text()
    assert "smoothstep(0.10, 0.60, max(DepthNorm, 0.0) * 4.0)" in source
    assert "* saturate(Wet) * depthGate * localWindow" in source
    assert 'AddTurbulenceInput(TEXT("DepthNorm"), TurbulenceVertexColor, 2)' in source
    assert "DepthInput.Input.Connect(2, FoamInput->Input.Expression)" in source
    assert 'Input.InputName == TEXT("DepthNorm")' in source


def test_review_start_is_map_scoped_and_does_not_write_selection():
    source = (ROOT / "unreal/Source/SmokeEmIfYouGotEm/RaftSimRunManager.cpp").read_text()
    block = source.split("void ARaftSimRunManager::ConfigureSession(", 1)[1].split("bool ARaftSimRunManager::ConfigureProgressCoordinateMap", 1)[0]
    assert "RaftSimWaterReviewStation=" in block
    assert 'EndsWith(TEXT("L_SouthForkAmerican_FullReach"))' in block
    assert "FMath::IsFinite(ReviewStationM)" in block
    assert 'ProgressCoordinates->GetRiverStationRangeM(ReviewMinimumM,ReviewMaximumM)' in block
    assert 'ReviewStationM >= ReviewMinimumM && ReviewStationM <= ReviewMaximumM' in block
    assert 'FinishStationM = ReviewMaximumM' in block
    assert "Save->" not in block
    restore = source.split('void ARaftSimRunManager::TryRestoreSessionCheckpoint()', 1)[1].split(
        'void ARaftSimRunManager::StartRun()', 1)[0]
    assert 'Progress->GetRiverStationRangeM(MinimumStationM, MaximumStationM)' in restore
    assert 'ReviewStationM >= MinimumStationM && ReviewStationM <= MaximumStationM' in restore
    assert 'ReviewStationM <= 48900' not in source


def test_legacy_normal_migration_invalidates_saved_shader_identity():
    source = (ENV / "RaftSimEditorSouthForkWaterPresentation.cpp").read_text()
    assert 'TEXT("RaftSimLegacyAnalyticNormalGate")' in source
    assert "Material->StateId = FGuid::NewGuid();" in source
    assert "Material->UpdateCachedExpressionData();" in source
    save = source.index("if (bNeedsSave)")
    assert source.index("Material->StateId =", save) < source.index("UPackage::SavePackage", save)
