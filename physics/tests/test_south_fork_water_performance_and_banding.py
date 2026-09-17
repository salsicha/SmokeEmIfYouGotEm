from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
    "RaftSimWaterSurfaceActor.cpp"
)
AUTHORING_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
    "RaftSimEditorSouthForkFullReach.cpp"
)
WATER_SURFACE_HEADER = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/"
    "RaftSimWaterSurfaceActor.h"
)
STREAMING_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
    "RaftSimRiverWaterStreamingActor.cpp"
)
PHYSICS_BRIDGE_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimPhysics/Private/"
    "RaftSimPhysicsBridgeSubsystem.cpp"
)
LIVE_WINDOW_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimWater/Private/"
    "RaftSimLiveWaterWindow.cpp"
)


def test_south_fork_full_reach_uses_crest_resolving_carrier_budget() -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")
    assert "!bUsesSouthForkFullReachSingleSurface" in source
    assert "bUsesSouthForkFullReachSingleSurface\n        ? 2" in source
    assert "401 x 65 = 26,065 vertices" in source
    assert "bSingleLiveWaterSurfaceEnabled ? 16 : 1" in source


def test_half_meter_hydraulics_use_a_forward_biased_bounded_runtime_crop() -> None:
    header = WATER_SURFACE_HEADER.read_text(encoding="utf-8")
    streaming = STREAMING_SOURCE.read_text(encoding="utf-8")
    hydraulic_window = header.split(
        "static constexpr float GetSouthForkHydraulicWindowLengthMeters()", 1
    )[1].split("}", 1)[0]
    assert "return 160.0f;" in hydraulic_window
    assert "0.30f * CachedMovingWindowStationExtentM" in streaming


def test_live_solver_cannot_enter_a_render_frame_catch_up_spiral() -> None:
    bridge = PHYSICS_BRIDGE_SOURCE.read_text(encoding="utf-8")
    live_window = LIVE_WINDOW_SOURCE.read_text(encoding="utf-8")
    tick_bridge = bridge.split(
        "FRaftSimPhysicsTickOutput URaftSimPhysicsBridgeSubsystem::TickBridge", 1
    )[1].split(
        "void URaftSimPhysicsBridgeSubsystem::RecordContactTelemetryEvent", 1
    )[0]
    compact = re.sub(r'\s+', '', tick_bridge)
    assert 'LastOutput.bFixedTickFailed=!FixedClock.Advance(double(Input.FrameDeltaSeconds),double(WaterStepSeconds),4,' in compact
    assert '[this]{returnRunOneFixedWaterTick();},Completed)' in compact
    assert 'LastOutput.FixedTicksThisFrame=Completed;' in compact
    assert 'LastOutput.SimulationBacklogSeconds=FixedClock.BacklogSeconds;' in compact
    # Fmod discarded hitch debt in the former implementation. Its presence is
    # now a regression, not something a performance test should demand.
    assert 'Fmod(' not in tick_bridge
    clock = (PHYSICS_BRIDGE_SOURCE.parents[1] / 'Public/RaftSimFixedStepClock.h').read_text()
    clock = re.sub(r'\s+', '', clock)
    assert 'while(Completed<MaximumTicks&&BacklogSeconds>=StepSeconds)' in clock
    assert 'if(!RunTick())returnfalse;' in clock
    assert 'BacklogSeconds-=StepSeconds;CommittedSeconds+=StepSeconds;' in clock
    assert 'Fmod(' not in clock
    # The current coupled Cartesian path must retain source MUSCL2; the old
    # unrelated legacy first-order branch is not the normal-path authority.
    coupled = live_window.split('double Manning = 0., SpatialOrder = 0.;', 1)[1].split('Scenario.boundaries.clear();', 1)[0]
    assert 'SpatialOrder != 2.' in coupled
    assert 'Config.spatial_order = 2;' in coupled


def test_single_surface_disables_periodic_bars_and_bounds_surface_detail() -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")
    single_surface_block = source.split(
        "if (bSingleLiveWaterSurfaceEnabled)", 1
    )[1].split(
        "// Review override: raftsim.PresentationStandingWaveScale", 1
    )[0]
    assert "ResolvedPresentationStandingWaveScale = 0.0f" in single_surface_block
    assert 'TEXT("CalmRippleStrength"), bRebaseWaterTextureCoordinates ? 0.08f : 0.0f' in source
    assert 'TEXT("FlowRippleStrength"), bRebaseWaterTextureCoordinates ? 0.14f : 0.0f' in source
    assert 'TEXT("FoamRippleStrength"), bRebaseWaterTextureCoordinates ? 0.25f : 0.0f' in source
    assert 'TEXT("SpeedAerationFraction"), 0.0f' in source
    assert 'TEXT("RippleGrazingFloor"), bRebaseWaterTextureCoordinates ? 0.50f : 0.015f' in source
    assert 'TEXT("WaterRoughness"), 0.22f' in source


def test_single_surface_accepts_real_near_bank_hydraulic_jumps() -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")
    policy = source.split('const float MinimumBreakingCoverage =', 1)[1].split('if (bAuditBreakingHeight)', 1)[0]
    compact = re.sub(r'\s+', '', policy)
    assert '(bSingleLiveWaterSurfaceEnabled||bSharedBreakingReliefEnabled)?0.55f:0.999f;' in compact
    assert '(bSingleLiveWaterSurfaceEnabled||bSharedBreakingReliefEnabled)?FMath::Max(ResolvedVertexSpacingMeters,3.0f):BreakingSiteInteriorClearanceMeters;' in compact
    assert re.search(r'if \(PresentationCoverage < MinimumBreakingCoverage \|\|\s*PresentationEdgeClearanceMeters <\s*MinimumBreakingClearanceMeters\)', source)


def test_optical_smoothing_review_keeps_hydraulic_sources_and_other_rivers_fixed() -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")
    assert "bSouthForkOpticalSmoothingReview = bUsesSouthForkFullReachSingleSurface" in source
    assert 'TEXT("raftsim.SouthForkOpticalSmoothingPasses"), 16' in source
    assert "const int32 HydraulicPassCount = bSingleLiveWaterSurfaceEnabled ? 4 : 1" in source
    compact = re.sub(r'\s+', '', source)
    assert 'RaftSimWaterSmoothing::OpticalPassCount(bNativeMean,bNeedsOptical,ConfiguredOpticalPassCount)' in compact
    assert 'RaftSimWaterSmoothing::Apply(PresentationSurfaceHeightMeters,WetVertexMask,GridStationN,GridLateralN,Stride,ResolvedPresentationSurfaceSmoothingStrength,OpticalPassCount,HydraulicPassCount,HydraulicSourceSurfaceHeightMeters)' in compact
    smoothing = (WATER_SURFACE_HEADER.parent / 'RaftSimWaterSmoothing.h').read_text()
    smoothing = re.sub(r'\s+', '', smoothing)
    assert 'returnbNativeMean&&!bNeedsOptical?0:Configured;' in smoothing
    assert 'FMath::Max(OpticalPasses,HydraulicPasses)' in smoothing
    assert 'constTArray<float>Previous=Surface;' in smoothing
    assert 'if(!Wet[I]||!Wet[U]||!Wet[D]||!Wet[R]||!Wet[L])continue;' in smoothing
    assert 'if(Pass+1==HydraulicPasses)Hydraulic=Surface;' in smoothing
    assert 'if(Pass+1==OpticalPasses&&OpticalPasses<Passes)Optical=Surface;' in smoothing
    assert 'if(!Optical.IsEmpty())Surface=MoveTemp(Optical);' in smoothing
    native_restore = source.split('    if (bNativeMean)\n    {', 1)[1].split('Perf.Mark(TEXT("optical_filter"))', 1)[0]
    assert 'if(WetVertexMask[I])PresentationSurfaceHeightMeters[I]=WaterSamples[I].SurfaceHeightMeters;' in re.sub(r'\s+', '', native_restore)


def test_carrier_uv_rebasing_preserves_full_precision_shader_phase() -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")
    # Both initial construction and recentering use the same local basis.
    assert source.count("(RiverCoordinatesM[Index] - WaterTextureOriginMeters) / kWaterTextureRepeatMeters") == 2
    assert 'TEXT("RaftSimWaterUVOrigin")' in source
    presentation = (AUTHORING_SOURCE.parent / "RaftSimEditorSouthForkWaterPresentation.cpp").read_text(encoding="utf-8")
    assert "Coordinate->CoordinateIndex != 0" in presentation
    assert "RaftSimFullPrecisionRiverUV" in presentation
    assert "const TArray<TObjectPtr<UMaterialExpression>> OriginalExpressions" in presentation
    assert "Input->Expression = AbsoluteUV" in presentation
    assert "Tiling->R = Coordinate->UTiling" in presentation
    assert "WaveClock * 1.70 + 2.90 * boilNoiseB" in presentation
    assert "WaveClock * (1.45 + 0.55 * boilNoiseB)" not in presentation


def test_newly_authored_south_fork_maps_persist_the_runtime_contract() -> None:
    source = AUTHORING_SOURCE.read_text(encoding="utf-8")
    assert "LivePresentationStandingWaveScale = 0.0f" in source
    assert "bEnableLiveRapidSurfaceRefinement = false" in source
    assert "LiveRapidSurfaceSubdivision = 1" in source
    assert 'TEXT("RaftSimThreeMeterFullReachCarrierV2")' in source
