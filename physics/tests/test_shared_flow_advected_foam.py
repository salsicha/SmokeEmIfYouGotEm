import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATERIAL_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials"
    / "RaftSimEditorMaterialsBase.cpp"
)
UNIFIED_WATER_MATERIAL_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials"
    / "RaftSimEditorPhotorealMaterials.cpp"
)
RUNTIME_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private"
    / "RaftSimWaterSurfaceActor.cpp"
)
STREAMING_RUNTIME_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private"
    / "RaftSimRiverWaterStreamingActor.cpp"
)
SOUTH_FORK_WATER_PRESENTATION_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment"
    / "RaftSimEditorSouthForkWaterPresentation.cpp"
)
REVIEW = (
    ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "shared_flow_advected_foam_v1_review.json"
)

SUPERSEDING_SOURCE_HASHES = {
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorMaterialsBase.cpp": (
        "a9c76ffdf199c6deb42d5b0553f5de2aaf77abefa7f5b2bcbfeb64700e536d5f"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Tests/RaftSimEditorZambeziWaterTest.cpp": (
        "4037533415156d0d7cb5270dbdfaeaa0bf8a63a26c70f2b6aa75d51849f9bf69"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp": (
        "6d6ec2c854435d98b2acd86a4242b774d31d89c7fb473c1631279483db879dcc"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorPhotorealMaterials.cpp": (
        "4269db2aba4fac08b21b3d1d58aa9979096993f71a206f9319f3f20d8c94153c"
    ),
    "physics/tests/test_editor_source_layout.py": (
        "8b7b6640a4756178651a6a5fb2119fb244cc51bd3f00ec7d0a19228ab509ff23"
    ),
}

SUPERSEDING_ARTIFACT_HASHES = {
    "unreal/Content/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverFieldFoamCandidate.uasset": (
        "941c756e8a1ae7ab8d51de9c7a65b785c5f0feb8119c03126aeaa3b99906f4ef"
    ),
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/shared_flow_advected_foam_v1_native.json": (
        "de9cd54f3671da6c0fa6676699bdb588b956e73b56d28619fa4284ee705c61b2"
    ),
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/shared_flow_advected_foam_v1_p2_p4.json": (
        "842466540f12cd4b4648503f6e4f356233c61f63a8766a760953a962dd0524b9"
    ),
}


def test_shared_foam_is_lit_multiscale_and_solver_masked() -> None:
    source = MATERIAL_SOURCE.read_text()
    assert "Material->SetShadingModel(MSM_DefaultLit)" in source
    assert 'TEXT("RaftSimSolverCurrentAdvectedFoamPrimary")' in source
    assert 'TEXT("RaftSimSolverCurrentAdvectedFoamDetail")' in source
    assert 'TEXT("RaftSimFlowAdvectedMultiscaleFoamV1")' in source
    assert source.count('ParameterName = TEXT("SolverOverlayFoamLace")') >= 2
    assert 'CollectionParameter(TEXT("RaftSimFoamAdvectionMeters"), false)' in source
    assert "FoamPrimaryAdvectionUv->A.Expression = FoamAdvectionRiverMeters" in source
    assert "FoamDetailAdvectionUv->A.Expression = FoamAdvectionRiverMeters" in source
    assert "SolverMaskedLace->A.Expression = VertexColor" in source
    assert "SolverMaskedLace->A.OutputIndex = 4" in source
    assert (
        "SolverMaskedLace->B.Expression = FlowAdvectedMultiscaleLace" in source
    )
    assert "OcclusionSafeFoamMask->B.Expression = RaftExclusion" in source
    assert "Material->OpacityMaskClipValue = 0.01f" in source


def test_shared_foam_does_not_move_solver_or_physics_authority() -> None:
    runtime = RUNTIME_SOURCE.read_text()
    assert "SourceFoam[Index]" in runtime
    assert "VertexColors[Index].R = FinalFoam" in runtime
    assert "FocusedFoam * VertexColors[Index].A" in runtime
    assert "SmoothRapidFoamCoverage(" in runtime
    assert "FoamCoverage >= 0.01f" in runtime
    assert "RaftSimFoamAdvectionMeters" in runtime
    assert "RapidFoamMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision)" in runtime
    assert "RapidFoamMesh->SetCastShadow(false)" in runtime


def test_single_water_surface_owns_foam_without_a_flashing_second_sheet() -> None:
    runtime = RUNTIME_SOURCE.read_text()
    material = UNIFIED_WATER_MATERIAL_SOURCE.read_text()
    south_fork = SOUTH_FORK_WATER_PRESENTATION_SOURCE.read_text()
    assert "!bSingleLiveWaterSurfaceEnabled &&" in runtime
    assert "if (bSingleLiveWaterSurfaceEnabled)" in runtime
    assert "HideBreakingLipMesh();" in runtime
    assert "HideBreakingRollerVolumeMesh();" in runtime
    assert 'TEXT("HydraulicFoamColorBreakupBias"), 0.06f' in runtime
    assert 'TEXT("HydraulicFoamColorBreakupGain"), 1.08f' in runtime
    assert 'TEXT("DriftFoamOpacity"), 0.0f' in runtime
    assert 'TEXT("CalmRippleStrength"), 0.0f' in runtime
    assert 'TEXT("FlowRippleStrength"), 0.0f' in runtime
    assert 'TEXT("FoamRippleStrength"), 0.0f' in runtime
    assert 'TEXT("LiveFlowStreakRoughness"), 0.0f' in runtime
    assert 'TEXT("LiveFlowStreakTint"), 0.0f' in runtime
    assert 'TEXT("FlowStreakRoughness"), 0.0f' in runtime
    assert 'TEXT("FlowStreakSpeedGain"), 0.0f' in runtime
    assert 'TEXT("CalmSurfaceColorVariation"), 0.0f' in runtime
    assert 'TEXT("FallbackSkyReflectionVariation"), 0.0f' in runtime
    assert 'TEXT("FallbackSkyReflectionFloor"), 1.0f' in runtime
    assert 'TEXT("SouthForkTravelingWaveWPOStrength"), 0.0f' in runtime
    assert "bHasTravelingWaveWPOStrengthParameter" in runtime
    assert "LegacyMaterialWPOCounterM = 0.012f" in runtime
    assert "PresentationWaveClockSeconds = 0.0f" in runtime
    assert "bSingleLiveWaterSurfaceEnabled ? 32 : 1" in runtime
    assert "bSingleLiveWaterSurfaceEnabled ||" in runtime
    assert "bSingleLiveWaterSurfaceEnabled\n            ? 1.0f" in runtime
    assert "ResolvedPresentationStandingWaveScale = bSingleLiveWaterSurfaceEnabled" in runtime
    assert "FMath::Max(ConfiguredLiveFoamIntensity, 0.90f)" in runtime
    assert "bSingleLiveWaterSurfaceEnabled ? 0.12f : 0.55f" in runtime
    assert "0.028f * SpeedEnvelope" in runtime
    assert "FoamAttackBlend" in runtime
    assert "SourceFoam[Index] > Advected" in runtime
    assert "RaftSimUnifiedCurrentWaterSurface" in material
    assert "RaftSimUnifiedCurrentFoamFroth" in material
    assert "RaftSimUnifiedCurrentLiveFroth" in material
    assert 'TEXT("WhitewaterFrothBubbleCells")' in material
    assert 'TEXT("WhitewaterFrothBubbleHoleFloor"), 0.08f' in material
    assert 'TEXT("WhitewaterFrothCoreFill"), 0.58f' in material
    assert 'TEXT("WhitewaterFrothShadowColor")' in material
    assert 'TEXT("LiveFoamRoughnessOpenCell"), 0.43f' in material
    assert 'TEXT("LiveFoamRoughnessBubble"), 0.72f' in material
    assert 'TEXT("LiveSolverFoamGlowFloor"), 0.08f' in material
    assert 'TEXT("LiveSolverFoamGlowPatternGain"), 0.92f' in material
    assert 'TEXT("SolverFoamOpacityGain"), 0.12f' in material
    assert 'TEXT("WhitewaterFrothOpacityGain"), 1.28f' in material
    assert 'TEXT("UnifiedSurfaceFeatureScaleBlend"), 0.55f' in material
    assert 'TEXT("UnifiedSurfaceFeatureSpeedGain"), 4.5f' in material
    assert 'TEXT("UnifiedSurfaceFeatureFoamGain"), 1.5f' in material
    assert 'TEXT("UnifiedSurfaceFeatureDark"), 0.68f' in material
    assert 'TEXT("UnifiedSurfaceFeatureBright"), 1.03f' in material
    assert 'TEXT("UnifiedSurfaceFeatureStrength"), 0.85f' in material
    assert 'TEXT("UnifiedSurfaceFeatureRoughness"), 0.12f' in material
    assert 'TEXT("LiveSolverFoamGlowFloor"), 0.45f' not in material
    assert 'TEXT("SolverFoamOpacityGain"), 0.55f' not in material
    assert "MetersToUv->R = -UTiling * SlipFactor / 3.0f" in material
    assert "MetersToUv->G = -VTiling * SlipFactor / 3.0f" in material
    assert "M_RaftSim_SouthForkRaftTransmissionWaterV2" in south_fork
    assert 'TEXT("HydraulicFoamColorBreakupBias")), 0.06f' in south_fork
    assert 'TEXT("HydraulicFoamColorBreakupGain")), 1.08f' in south_fork
    assert 'TEXT("DriftFoamAerationGain")), 0.0f' in south_fork
    assert 'TEXT("DriftFoamSpeedGain")), 0.0f' in south_fork
    assert 'TEXT("CalmRippleStrength")), 0.0f' in south_fork
    assert 'TEXT("FlowRippleStrength")), 0.0f' in south_fork
    assert 'TEXT("FoamRippleStrength")), 0.0f' in south_fork
    assert 'TEXT("LiveFlowStreakRoughness")), 0.0f' in south_fork
    assert 'TEXT("LiveFlowStreakTint")), 0.0f' in south_fork
    assert 'TEXT("FlowStreakRoughness")), 0.0f' in south_fork
    assert 'TEXT("FlowStreakSpeedGain")), 0.0f' in south_fork
    assert 'TEXT("CalmSurfaceColorVariation")), 0.0f' in south_fork
    assert 'TEXT("FallbackSkyReflectionVariation")), 0.0f' in south_fork
    assert 'TEXT("FallbackSkyReflectionFloor")), 1.0f' in south_fork
    assert 'TEXT("SouthForkTravelingWaveWPOStrength")), 0.0f' in south_fork
    assert "RaftSimTravelingBakeWaveWPOStrengthGate" in south_fork


def test_single_water_surface_continues_past_crop_without_changing_hydraulics() -> None:
    runtime = RUNTIME_SOURCE.read_text()
    assert "TArray<uint8> VolumeCoreWetMask = WetVertexMask" in runtime
    assert "SamplePresentationBaselineFieldAtRiverCoordinates" in runtime
    assert "bUseCopiedBoundaryOpticalApron = false" in runtime
    assert "rectangular bank patch" in runtime
    assert "VolumeCoreWetMask[I0] != 0" in runtime
    assert "FlowVelocityMetersPerSecond," in runtime
    assert "VolumeCoreEmptyUVs" in runtime


def test_travel_keeps_shoreline_visibility_and_sampling_stable() -> None:
    runtime = RUNTIME_SOURCE.read_text()
    streaming = STREAMING_RUNTIME_SOURCE.read_text()
    assert "Preserve the global presentation lattice" in runtime
    assert "FMath::RoundToFloat(" in runtime
    assert "Only the genuinely new leading edge is sampled anew" in runtime
    assert "FWorldDelegates::LevelAddedToWorld.AddUObject" in streaming
    assert "HandleLevelAddedToWorld" in streaming
    assert "ApplyStaticFlowBandVisibilityToActor(Actor)" in streaming
    assert "FWorldDelegates::LevelAddedToWorld.Remove" in streaming
    assert "CreateMeshSection replaces an existing section atomically" in runtime
    assert (
        "LiveVolumeCoreMesh->ClearMeshSection(0);\n"
        "                LiveVolumeCoreMesh->CreateMeshSection" not in runtime
    )


def test_shared_foam_review_is_fail_closed_and_hash_locked() -> None:
    review = json.loads(REVIEW.read_text())
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["production_promoted"] is False
    assert review["runtime_rolled_out"] is True
    assert len(review["scope"]["rivers"]) == 6
    assert len(review["required_external_acceptance_gates"]) == 7
    assert (
        review["matched_evidence"]["futaleufu_breaking_water_side"]
        ["candidate_very_white_percent"]
        < review["matched_evidence"]["futaleufu_breaking_water_side"]
        ["baseline_very_white_percent"]
    )
    for relative_path, expected_hash in review["source_hashes"].items():
        path = ROOT / relative_path
        current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if relative_path == "physics/tests/test_shared_flow_advected_foam.py":
            # The review records the exact historical guard. This guard may
            # evolve only to recognize explicitly hash-locked superseding
            # presentation milestones; keep the historical digest immutable.
            assert expected_hash == (
                "087ea3adc60a4db28c25c1fbaab03e92a14ff0227b35bb0cb1eaf0d060f9d9be"
            )
        else:
            assert current_hash == SUPERSEDING_SOURCE_HASHES.get(
                relative_path, expected_hash
            )
    for artifact in review["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == (
            SUPERSEDING_ARTIFACT_HASHES.get(artifact["path"], artifact["sha256"])
        )
