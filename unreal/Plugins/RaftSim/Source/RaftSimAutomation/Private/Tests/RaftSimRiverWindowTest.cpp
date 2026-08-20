// P2 river-window gate (release-1.0-plan.md §5 A-1 / §7 P2): a live solver
// window seeded from the cooked South Fork steady flow fields loads with
// verified hashes, steps the genuine FV solver, and stays physical.

#include "Misc/AutomationTest.h"
#include "Misc/Paths.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimWaterRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimRiverWindowLoadsTest,
    "RaftSim.P2.RiverWindowLoads",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

bool FRaftSimRiverWindowLoadsTest::RunTest(const FString&)
{
#if !RAFTSIM_HAS_LIVE_SOLVER
    AddError(TEXT(
        "River windows require the live solver library; build it via "
        "unreal/Scripts/build_solver_lib.sh"));
    return false;
#else
    URaftSimWaterRuntimeAdapter* Adapter = NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest = false;
    Config.bEnableDeterministicCapture = false;
    Adapter->Configure(Config);

    // Full-axis median window: the cooked chili-bar seed grid spans cell
    // centers x in [0, 284], y in [-31, 31]; this extent clamps to all of it.
    const FString CookedFieldsDir = TEXT(
        "physics/data/real_world/south_fork_american_chili_bar/cooked_flow_fields");
    if (!Adapter->ConfigureRiverWindow(
            CookedFieldsDir, TEXT("median_runnable"),
            FVector2D(142.0, 0.0), FVector2D(400.0, 100.0)))
    {
        AddError(TEXT("ConfigureRiverWindow failed for median_runnable"));
        return false;
    }
    TestTrue(TEXT("adapter reports a live window"), Adapter->HasLiveWindow());

    FRaftSimWaterLiveWindowStats SeededStats;
    if (!Adapter->GetLiveWindowStats(SeededStats))
    {
        AddError(TEXT("live window stats unavailable after ConfigureRiverWindow"));
        return false;
    }
    TestTrue(
        TEXT("seeded water volume is positive"), SeededStats.TotalWaterVolumeM3 > 0.0f);
    TestTrue(
        TEXT("cooked seed wet fraction is positive"), SeededStats.SeedWetFraction > 0.0f);
    TestFalse(TEXT("seeded state is finite"), SeededStats.bHasNonFinite);

    // A wet mid-channel sample with downstream flow (world position in cm).
    FRaftSimWaterSample MidChannel;
    TestTrue(
        TEXT("mid-window sample succeeds"),
        Adapter->SampleWaterAtWorldPosition(FVector(14200.0f, 0.0f, 0.0f), MidChannel));
    TestTrue(TEXT("mid-window sample is wet"), MidChannel.bWet);
    TestTrue(TEXT("mid-window depth is positive"), MidChannel.DepthMeters > 0.0f);

    // Two simulated seconds of the genuine solver on the game step.
    for (int32 StepIndex = 0; StepIndex < 120; ++StepIndex)
    {
        if (!Adapter->StepWater(1.0f / 60.0f))
        {
            AddError(FString::Printf(TEXT("StepWater failed at step %d"), StepIndex));
            return false;
        }
    }

    FRaftSimWaterLiveWindowStats SteppedStats;
    if (!Adapter->GetLiveWindowStats(SteppedStats))
    {
        AddError(TEXT("live window stats unavailable after stepping"));
        return false;
    }
    TestTrue(
        FString::Printf(
            TEXT("water mass stays positive (volume %.1f m^3)"),
            SteppedStats.TotalWaterVolumeM3),
        SteppedStats.TotalWaterVolumeM3 > 0.0f);
    TestFalse(TEXT("no NaNs/infinities after 120 steps"), SteppedStats.bHasNonFinite);
    TestTrue(
        FString::Printf(
            TEXT("wet fraction %.4f within 10%% of cooked wet fraction %.4f"),
            SteppedStats.WetFraction, SteppedStats.SeedWetFraction),
        FMath::Abs(SteppedStats.WetFraction - SteppedStats.SeedWetFraction) <=
            0.1f * SteppedStats.SeedWetFraction);
    return true;
#endif // RAFTSIM_HAS_LIVE_SOLVER
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimMovingRiverWindowHandoffTest,
    "RaftSim.M3.MovingRiverWindowPreservesOverlap",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

bool FRaftSimMovingRiverWindowHandoffTest::RunTest(const FString&)
{
#if !RAFTSIM_HAS_LIVE_SOLVER
    AddError(TEXT("Moving river windows require the live solver library"));
    return false;
#else
    URaftSimWaterRuntimeAdapter* Adapter = NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest = false;
    Config.bEnableDeterministicCapture = false;
    Adapter->Configure(Config);

    const FString CookedFieldsDir = TEXT(
        "physics/data/real_world/south_fork_american_chili_bar/"
        "full_hydraulics/rapids/chili_bar_hole/cooked");
    if (!Adapter->ConfigureMovingRiverWindow(
            CookedFieldsDir, TEXT("median_runnable"),
            FVector2D(120.0, 0.0), FVector2D(240.0, 80.0)))
    {
        AddError(TEXT("initial globally stationed river crop failed"));
        return false;
    }
    for (int32 StepIndex = 0; StepIndex < 30; ++StepIndex)
    {
        if (!Adapter->StepWater(1.0f / 60.0f))
        {
            AddError(TEXT("pre-handoff water step failed"));
            return false;
        }
    }

    FRaftSimWaterSample Before;
    const FVector OverlapSamplePosition(16000.0f, 0.0f, 0.0f);
    TestTrue(
        TEXT("pre-handoff overlap sample succeeds"),
        Adapter->SampleWaterAtWorldPosition(OverlapSamplePosition, Before));
    const float AdapterTimeBefore = Adapter->GetSimTimeSeconds();

    if (!Adapter->ConfigureMovingRiverWindow(
            CookedFieldsDir, TEXT("median_runnable"),
            FVector2D(200.0, 0.0), FVector2D(240.0, 80.0)))
    {
        AddError(TEXT("overlapping downstream river crop handoff failed"));
        return false;
    }

    FRaftSimWaterSample After;
    TestTrue(
        TEXT("post-handoff overlap sample succeeds"),
        Adapter->SampleWaterAtWorldPosition(OverlapSamplePosition, After));
    TestEqual(
        TEXT("adapter simulation clock does not reset"),
        Adapter->GetSimTimeSeconds(), AdapterTimeBefore);
    TestTrue(
        TEXT("overlap depth is preserved"),
        FMath::IsNearlyEqual(After.DepthMeters, Before.DepthMeters, 1.0e-4f));
    TestTrue(
        TEXT("overlap downstream velocity is preserved"),
        FMath::IsNearlyEqual(
            After.VelocityMetersPerSecond.X,
            Before.VelocityMetersPerSecond.X, 1.0e-4f));
    TestTrue(
        TEXT("overlap cross-stream velocity is preserved"),
        FMath::IsNearlyEqual(
            After.VelocityMetersPerSecond.Y,
            Before.VelocityMetersPerSecond.Y, 1.0e-4f));

    FRaftSimWaterLiveWindowStats Stats;
    TestTrue(TEXT("moving-window stats are available"), Adapter->GetLiveWindowStats(Stats));
    TestTrue(TEXT("handoff transferred cells"), Stats.LastHandoffTransferredCellCount > 0);
    TestEqual(TEXT("one moving-window handoff recorded"), Stats.MovingWindowHandoffCount, 1);
    TestTrue(TEXT("handoff reports preserved state"), Stats.bLastHandoffPreservedState);
    TestTrue(
        TEXT("solver simulation clock is preserved"),
        FMath::IsNearlyEqual(Stats.SimTimeSeconds, AdapterTimeBefore, 1.0e-5f));
    TestFalse(TEXT("handoff state stays finite"), Stats.bHasNonFinite);

    TestTrue(TEXT("post-handoff water step succeeds"), Adapter->StepWater(1.0f / 60.0f));
    TestTrue(TEXT("post-handoff stats are available"), Adapter->GetLiveWindowStats(Stats));
    TestFalse(TEXT("post-handoff step stays finite"), Stats.bHasNonFinite);
    return true;
#endif // RAFTSIM_HAS_LIVE_SOLVER
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimFullReachTransitWindowTest,
    "RaftSim.M3.FullReachTransitWindowLoadsAndMoves",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

bool FRaftSimFullReachTransitWindowTest::RunTest(const FString&)
{
#if !RAFTSIM_HAS_LIVE_SOLVER
    AddError(TEXT("Full-reach transit windows require the live solver library"));
    return false;
#else
    URaftSimWaterRuntimeAdapter* Adapter = NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest = false;
    Config.bEnableDeterministicCapture = false;
    Adapter->Configure(Config);

    const FString TransitFieldsDir = TEXT(
        "physics/data/real_world/south_fork_american_chili_bar/"
        "full_hydraulics/full_reach_transit_seed");
    TestTrue(
        TEXT("full-reach transit crop loads"),
        Adapter->ConfigureMovingRiverWindow(
            TransitFieldsDir, TEXT("median_runnable"),
            FVector2D(5000.0, 0.0), FVector2D(240.0, 80.0)));
    const FString BaselineFieldPath =
        URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(FPaths::Combine(
            TransitFieldsDir,
            TEXT("support_band_field_median_runnable.bin")));
    TestTrue(
        TEXT("full-reach terrain-clipped presentation baseline loads"),
        Adapter->LoadPresentationBaselineFieldFromFile(BaselineFieldPath));
    FRaftSimWaterSample BaselineWater;
    TestTrue(
        TEXT("presentation baseline retains wet organic channel center"),
        Adapter->SamplePresentationBaselineFieldAtRiverCoordinates(
            FVector2D(5000.0, 0.0), BaselineWater));
    TestTrue(
        TEXT("presentation baseline carries a downstream visual current"),
        BaselineWater.bWet &&
            BaselineWater.VelocityMetersPerSecond.X > 0.0f);
    TestFalse(
        TEXT("presentation baseline does not wet far terrain outside bank"),
        Adapter->SamplePresentationBaselineFieldAtRiverCoordinates(
            FVector2D(5000.0, 100.0), BaselineWater));
    TestTrue(TEXT("transit crop steps genuine solver"), Adapter->StepWater(1.0f / 60.0f));
    TestTrue(
        TEXT("downstream transit crop transfers overlap"),
        Adapter->ConfigureMovingRiverWindow(
            TransitFieldsDir, TEXT("median_runnable"),
            FVector2D(5080.0, 0.0), FVector2D(240.0, 80.0)));

    FRaftSimWaterLiveWindowStats Stats;
    TestTrue(TEXT("transit stats are available"), Adapter->GetLiveWindowStats(Stats));
    TestTrue(TEXT("transit handoff moved cells"), Stats.LastHandoffTransferredCellCount > 0);
    TestTrue(TEXT("transit handoff preserved state"), Stats.bLastHandoffPreservedState);
    TestFalse(TEXT("transit handoff remains finite"), Stats.bHasNonFinite);
    TestTrue(TEXT("transit water volume remains positive"), Stats.TotalWaterVolumeM3 > 0.0f);
    return true;
#endif // RAFTSIM_HAS_LIVE_SOLVER
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimCurvedRiverCoordinateMapTest,
    "RaftSim.M4.CurvedRiverCoordinateMapDrivesLiveWater",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

bool FRaftSimCurvedRiverCoordinateMapTest::RunTest(const FString&)
{
#if !RAFTSIM_HAS_LIVE_SOLVER
    AddError(TEXT("Curved live-river tests require the live solver library"));
    return false;
#else
    URaftSimWaterRuntimeAdapter* Adapter = NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest = false;
    Config.bEnableDeterministicCapture = false;
    Adapter->Configure(Config);

    const FString CoordinateMap = TEXT(
        "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
        "photoreal_environment/river_coordinate_map.json");
    TestTrue(
        TEXT("dense South Fork coordinate map loads"),
        Adapter->ConfigureRiverCoordinateMap(CoordinateMap));
    TestTrue(TEXT("adapter reports curved coordinate map"), Adapter->HasRiverCoordinateMap());

    const FVector2D ExpectedRiverPosition(5000.0, 17.5);
    FVector WorldPosition;
    TestTrue(
        TEXT("station/lateral converts to curved world"),
        Adapter->RiverToWorldPosition(
            ExpectedRiverPosition, Adapter->GetRiverVerticalDatumM(), WorldPosition));
    TestTrue(TEXT("vertical datum maps to local Z zero"), FMath::IsNearlyZero(WorldPosition.Z));
    TestTrue(
        TEXT("curved map is not the old straight +X strip"),
        FMath::Abs(WorldPosition.Y) > 10000.0f);

    FVector2D RoundTrip;
    FVector Tangent;
    FVector LeftNormal;
    TestTrue(
        TEXT("curved world converts back to station/lateral"),
        Adapter->WorldToRiverCoordinates(WorldPosition, RoundTrip, Tangent, LeftNormal));
    TestTrue(
        TEXT("station round trip stays within one dense-grid interval"),
        FMath::IsNearlyEqual(RoundTrip.X, ExpectedRiverPosition.X, 4.1f));
    TestTrue(
        TEXT("lateral round trip is sub-centimetre"),
        FMath::IsNearlyEqual(RoundTrip.Y, ExpectedRiverPosition.Y, 0.01f));
    TestTrue(TEXT("world tangent is unit length"), Tangent.IsUnit(1.0e-3f));
    TestTrue(TEXT("world left normal is unit length"), LeftNormal.IsUnit(1.0e-3f));
    TestTrue(
        TEXT("world tangent and left normal are orthogonal"),
        FMath::IsNearlyZero(FVector::DotProduct(Tangent, LeftNormal), 1.0e-4f));

    // Raft physics submits a continuous chain of adjacent tube probes. Verify
    // the previous-segment fast path retains the exact ruled-corridor inverse.
    const FVector2D NearbyExpected(5003.0, 18.5);
    FVector NearbyWorld;
    FVector2D NearbyRoundTrip;
    TestTrue(
        TEXT("nearby station/lateral converts to curved world"),
        Adapter->RiverToWorldPosition(
            NearbyExpected, Adapter->GetRiverVerticalDatumM(), NearbyWorld));
    TestTrue(
        TEXT("nearby curved probe uses a continuous exact inverse"),
        Adapter->WorldToRiverCoordinates(
            NearbyWorld, NearbyRoundTrip, Tangent, LeftNormal));
    TestTrue(
        TEXT("nearby cached station round trip stays sub-centimetre"),
        FMath::IsNearlyEqual(NearbyRoundTrip.X, NearbyExpected.X, 0.01f));
    TestTrue(
        TEXT("nearby cached lateral round trip stays sub-centimetre"),
        FMath::IsNearlyEqual(NearbyRoundTrip.Y, NearbyExpected.Y, 0.01f));

    const FString TransitFieldsDir = TEXT(
        "physics/data/real_world/south_fork_american_chili_bar/"
        "full_hydraulics/full_reach_transit_seed");
    TestTrue(
        TEXT("curved live-water crop loads"),
        Adapter->ConfigureMovingRiverWindow(
            TransitFieldsDir, TEXT("median_runnable"),
            FVector2D(5000.0, 0.0), FVector2D(240.0, 80.0)));
    FVector WetWorldPosition;
    TestTrue(
        TEXT("mid-channel station maps to world"),
        Adapter->RiverToWorldPosition(
            FVector2D(5000.0, 0.0), Adapter->GetRiverVerticalDatumM(), WetWorldPosition));
    FRaftSimWaterSample Water;
    TestTrue(
        TEXT("world-space probe samples the station-space live solver"),
        Adapter->SampleWaterAtWorldPosition(WetWorldPosition, Water));
    TestTrue(TEXT("curved mid-channel probe is wet"), Water.bWet);
    TestTrue(TEXT("curved probe has positive depth"), Water.DepthMeters > 0.0f);
    const float AbsoluteSurfaceM =
        Water.SurfaceHeightMeters + Adapter->GetRiverVerticalDatumM();
    TestTrue(
        FString::Printf(
            TEXT("station 5 km live surface restores the cooked elevation datum (%.3f m)"),
            AbsoluteSurfaceM),
        FMath::IsNearlyEqual(AbsoluteSurfaceM, 355.71f, 2.0f));
    TestTrue(
        TEXT("station 5 km surface remains above the Unreal river datum"),
        Water.SurfaceHeightMeters > 0.0f);
    TestTrue(
        TEXT("downstream station velocity rotates into the route tangent"),
        FVector::DotProduct(Water.VelocityMetersPerSecond, Tangent) > 0.0f);
    TestTrue(TEXT("rotated water surface normal is unit length"), Water.SurfaceNormal.IsUnit(1.0e-3f));

    FRaftSimWaterSample DirectWater;
    TestTrue(
        TEXT("river-coordinate probe samples without inverse projection"),
        Adapter->SampleWaterAtRiverCoordinates(FVector2D(5000.0, 0.0), DirectWater));
    TestTrue(TEXT("direct curved probe is wet"), DirectWater.bWet);
    TestTrue(
        TEXT("direct and world probes agree on depth"),
        FMath::IsNearlyEqual(DirectWater.DepthMeters, Water.DepthMeters, 1.0e-4f));
    TestTrue(
        TEXT("direct and world probes agree on velocity"),
        DirectWater.VelocityMetersPerSecond.Equals(
            Water.VelocityMetersPerSecond, 1.0e-4f));
    TestTrue(
        TEXT("direct probe reports its curved world location"),
        DirectWater.WorldPosition.Equals(
            FVector(WetWorldPosition.X, WetWorldPosition.Y,
                DirectWater.SurfaceHeightMeters * 100.0f),
            0.1f));

    FRaftSimWaterSample FieldWater;
    TestTrue(
        TEXT("lightweight river-field probe samples without a world-basis lookup"),
        Adapter->SampleWaterFieldAtRiverCoordinates(
            FVector2D(5000.0, 0.0), FieldWater));
    TestTrue(
        TEXT("field and transformed probes agree on speed"),
        FMath::IsNearlyEqual(
            FieldWater.VelocityMetersPerSecond.Size(),
            DirectWater.VelocityMetersPerSecond.Size(), 1.0e-4f));
    TestTrue(
        TEXT("field and transformed probes agree on depth"),
        FMath::IsNearlyEqual(
            FieldWater.DepthMeters, DirectWater.DepthMeters, 1.0e-4f));
    TestTrue(
        TEXT("field and transformed probes agree on restored surface elevation"),
        FMath::IsNearlyEqual(
            FieldWater.SurfaceHeightMeters,
            DirectWater.SurfaceHeightMeters, 1.0e-4f));

    // Couple the genuine curved South Fork field into the production reduced
    // raft solve. Positioning the raft slightly low and side-on represents a
    // crest/low-side encounter and must produce real segment-keyed D3 load;
    // no deterministic uniform-water fixture is involved.
    URaftSimChronoRuntimeAdapter* RaftAdapter =
        NewObject<URaftSimChronoRuntimeAdapter>();
    FRaftSimRaftBodyConfig Body;
    Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Body.MassKg = 220.0f;
    Body.LengthMeters = 4.3f;
    Body.WidthMeters = 2.0f;
    Body.TubeRadiusMeters = 0.28f;
    Body.InertiaTensorKgM2 = FVector(180.0f, 180.0f, 400.0f);
    RaftAdapter->ConfigureRaftBody(Body);
    FRaftSimFlexParameters Flex;
    Flex.MassKg = Body.MassKg;
    Flex.LengthM = Body.LengthMeters;
    Flex.WidthM = Body.WidthMeters;
    Flex.TubeRadiusM = Body.TubeRadiusMeters;
    RaftAdapter->ConfigureFlexibleRaftModel(
        Flex, RaftSimFlex::BuildDefaultCrewSeats(Flex));

    FRaftSimRaftKinematicState RaftState;
    RaftState.WorldTransform.SetTranslation(FVector(
        WetWorldPosition.X,
        WetWorldPosition.Y,
        Water.SurfaceHeightMeters * 100.0f - 25.0f));
    RaftState.WorldTransform.SetRotation(
        FRotator(0.0f, Tangent.Rotation().Yaw + 90.0f, 0.0f).Quaternion());
    RaftAdapter->SetKinematicState(RaftState);

    RaftAdapter->SetWaterSurfaceSampler(
        [Adapter](const FVector& PositionCm, float& OutSurfaceZCm) -> bool
        {
            FRaftSimWaterSample Sample;
            if (!Adapter->SampleWaterAtWorldPosition(PositionCm, Sample) || !Sample.bWet)
            {
                return false;
            }
            OutSurfaceZCm = Sample.SurfaceHeightMeters * 100.0f;
            return true;
        });
    float MaximumSampledSpeedMps = 0.0f;
    RaftAdapter->SetFlexibleWaterFieldSampler(
        [Adapter, &MaximumSampledSpeedMps](
            const FVector& PositionCm,
            FRaftSimFlexUniformWater& OutWater) -> bool
        {
            FRaftSimWaterSample Sample;
            if (!Adapter->SampleWaterAtWorldPosition(PositionCm, Sample))
            {
                return false;
            }
            OutWater.SurfaceHeightM = Sample.SurfaceHeightMeters;
            OutWater.VelocityMps = Sample.VelocityMetersPerSecond;
            OutWater.bWet = Sample.bWet;
            MaximumSampledSpeedMps = FMath::Max(
                MaximumSampledSpeedMps,
                Sample.VelocityMetersPerSecond.Size());
            return true;
        });
    TestTrue(TEXT("real South Fork water advances the flexible raft"),
             RaftAdapter->StepRaftDynamics(1.0f / 120.0f));
    const FRaftSimFlexStepTelemetry& LiveD3 =
        RaftAdapter->GetLastFlexibleStepTelemetry();
    AddInfo(FString::Printf(
        TEXT("real South Fork D3: samples=%d wet=%d speed=%.3f m/s retained=%.3f kg rollMoment=%.3f Nm"),
        LiveD3.LiveWaterSampleCount,
        LiveD3.LiveWetSampleCount,
        MaximumSampledSpeedMps,
        LiveD3.TotalRetainedWaterMassKg,
        LiveD3.RetainedWaterRollMomentNm));
    TestTrue(TEXT("real river coupling uses the live D3 field"),
             LiveD3.bUsedLiveWaterField);
    TestFalse(TEXT("real river coupling does not use the uniform fixture"),
              LiveD3.bUsedUniformWaterOverride);
    TestTrue(TEXT("real river samples every flexible tube segment"),
             LiveD3.LiveWaterSampleCount >= 12);
    TestEqual(TEXT("side-on mid-channel raft has all segments wet"),
              LiveD3.LiveWetSampleCount, LiveD3.LiveWaterSampleCount);
    TestTrue(
        FString::Printf(
            TEXT("D3 receives nonzero cooked South Fork speed (%.3f m/s)"),
            MaximumSampledSpeedMps),
        MaximumSampledSpeedMps > 0.1f);
    TestTrue(TEXT("real side-on river water retains deck load"),
             LiveD3.TotalRetainedWaterMassKg > 0.0);
    TestTrue(TEXT("real side-on river water produces a roll moment"),
             FMath::Abs(LiveD3.RetainedWaterRollMomentNm) > 0.0);

    FVector OutsideWorldPosition;
    TestTrue(
        TEXT("outside-bank coordinate still maps to world"),
        Adapter->RiverToWorldPosition(
            FVector2D(5000.0, 180.0), Adapter->GetRiverVerticalDatumM(), OutsideWorldPosition));
    TestFalse(
        TEXT("outside the finite live crop does not create fallback water"),
        Adapter->SampleWaterAtWorldPosition(OutsideWorldPosition, Water));
    TestFalse(
        TEXT("direct probe outside the finite crop does not create fallback water"),
        Adapter->SampleWaterAtRiverCoordinates(FVector2D(5000.0, 180.0), Water));

    // Named-rapid cooks use a local solver elevation for precision. Their
    // manifest-recorded source datum must restore the same absolute route
    // elevation as the transit seed before the Unreal datum is applied.
    URaftSimWaterRuntimeAdapter* RapidAdapter = NewObject<URaftSimWaterRuntimeAdapter>();
    RapidAdapter->Configure(Config);
    TestTrue(
        TEXT("rapid adapter loads the same curved coordinate map"),
        RapidAdapter->ConfigureRiverCoordinateMap(CoordinateMap));
    const FString ChiliBarFieldsDir = TEXT(
        "physics/data/real_world/south_fork_american_chili_bar/"
        "full_hydraulics/rapids/chili_bar_hole/cooked");
#if WITH_EDITOR
    const FString ExpectedSourceFieldsDir = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(FPaths::ProjectDir(), TEXT(".."), ChiliBarFieldsDir));
    TestTrue(
        TEXT("editor water validation prefers source data over stale packaged copies"),
        FPaths::IsSamePath(
            URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(ChiliBarFieldsDir),
            ExpectedSourceFieldsDir));
#endif
    TestTrue(
        TEXT("station 120 named-rapid crop loads"),
        RapidAdapter->ConfigureMovingRiverWindow(
            ChiliBarFieldsDir, TEXT("median_runnable"),
            FVector2D(120.0, 0.0), FVector2D(240.0, 80.0)));
    FVector RapidWorldPosition;
    TestTrue(
        TEXT("station 120 maps to the production route"),
        RapidAdapter->RiverToWorldPosition(
            FVector2D(120.0, 0.0), RapidAdapter->GetRiverVerticalDatumM(),
            RapidWorldPosition));
    FRaftSimWaterSample RapidWater;
    TestTrue(
        TEXT("station 120 named-rapid water samples in world space"),
        RapidAdapter->SampleWaterAtWorldPosition(RapidWorldPosition, RapidWater));
    const float RapidAbsoluteSurfaceM =
        RapidWater.SurfaceHeightMeters + RapidAdapter->GetRiverVerticalDatumM();
    TestTrue(
        FString::Printf(
            TEXT("named-rapid source datum restores the launch surface (%.3f m)"),
            RapidAbsoluteSurfaceM),
        FMath::IsNearlyEqual(RapidAbsoluteSurfaceM, 464.04f, 1.0f));
    TestTrue(
        TEXT("named-rapid launch water is hundreds of metres above local origin"),
        RapidWater.SurfaceHeightMeters > 300.0f);
    return true;
#endif // RAFTSIM_HAS_LIVE_SOLVER
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimMeatGrinderLiveD3LineCalibrationTest,
    "RaftSim.M4.MeatGrinderLiveD3LineCalibration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

bool FRaftSimMeatGrinderLiveD3LineCalibrationTest::RunTest(const FString&)
{
#if !RAFTSIM_HAS_LIVE_SOLVER
    AddError(TEXT("Named-rapid D3 calibration requires the live solver library"));
    return false;
#else
    struct FLineResult
    {
        bool bConfigured = false;
        bool bFinite = true;
        int32 MinimumSampleCount = MAX_int32;
        int32 MinimumWetSampleCount = MAX_int32;
        float MaximumSampledSpeedMps = 0.0f;
        float MaximumConsecutiveFlipRiskSeconds = 0.0f;
        double MinimumFlipMarginNm = TNumericLimits<double>::Max();
        double MaximumRetainedWaterMassKg = 0.0;
        float MaximumAbsRollDegrees = 0.0f;
        FVector FinalPositionM = FVector::ZeroVector;
    };

    const FString CookedFieldsDir = TEXT(
        "physics/data/real_world/south_fork_american_chili_bar/"
        "full_hydraulics/rapids/meat_grinder/cooked");
    auto RunLine = [this, &CookedFieldsDir](
        const FVector2D StartRiverM,
        float StartYawDegrees,
        bool bHighSide) -> FLineResult
    {
        FLineResult Result;
        URaftSimWaterRuntimeAdapter* Water = NewObject<URaftSimWaterRuntimeAdapter>();
        FRaftSimWaterRuntimeConfig WaterConfig;
        WaterConfig.bRequireAcceptedReportManifest = false;
        WaterConfig.bEnableDeterministicCapture = false;
        Water->Configure(WaterConfig);
        if (!Water->ConfigureMovingRiverWindow(
                CookedFieldsDir,
                TEXT("high_runnable"),
                FVector2D(965.6064, 0.0),
                FVector2D(240.0, 80.0)))
        {
            return Result;
        }

        const FVector StartWorldCm(
            StartRiverM.X * 100.0,
            StartRiverM.Y * 100.0,
            0.0);
        FRaftSimWaterSample StartWater;
        if (!Water->SampleWaterAtWorldPosition(StartWorldCm, StartWater) ||
            !StartWater.bWet)
        {
            return Result;
        }

        URaftSimChronoRuntimeAdapter* Raft =
            NewObject<URaftSimChronoRuntimeAdapter>();
        FRaftSimRaftBodyConfig Body;
        Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
        Body.MassKg = 220.0f;
        Body.LengthMeters = 4.3f;
        Body.WidthMeters = 2.0f;
        Body.TubeRadiusMeters = 0.28f;
        Body.InertiaTensorKgM2 = FVector(180.0f, 180.0f, 400.0f);
        Raft->ConfigureRaftBody(Body);

        FRaftSimFlexParameters Flex;
        Flex.MassKg = Body.MassKg;
        Flex.LengthM = Body.LengthMeters;
        Flex.WidthM = Body.WidthMeters;
        Flex.TubeRadiusM = Body.TubeRadiusMeters;
        Flex.PassengerCount = 4;
        Raft->ConfigureFlexibleRaftModel(
            Flex, RaftSimFlex::BuildDefaultCrewSeats(Flex));
        if (bHighSide)
        {
            FRaftSimFlexCrewAction GuideAction;
            GuideAction.SeatId = TEXT("guide");
            GuideAction.HighSideDirection = -1;
            GuideAction.bBrace = true;
            Raft->SetFlexibleCrewActions({GuideAction});
        }

        FRaftSimRaftKinematicState State;
        State.WorldTransform.SetTranslation(FVector(
            StartWorldCm.X,
            StartWorldCm.Y,
            StartWater.SurfaceHeightMeters * 100.0f + 6.0f));
        State.WorldTransform.SetRotation(
            FRotator(0.0f, StartYawDegrees, 0.0f).Quaternion());
        Raft->SetKinematicState(State);

        Raft->SetWaterSurfaceSampler(
            [Water](const FVector& PositionCm, float& OutSurfaceZCm) -> bool
            {
                FRaftSimWaterSample Sample;
                if (!Water->SampleWaterAtWorldPosition(PositionCm, Sample) || !Sample.bWet)
                {
                    return false;
                }
                OutSurfaceZCm = Sample.SurfaceHeightMeters * 100.0f;
                return true;
            });
        Raft->SetFlexibleWaterFieldSampler(
            [Water, &Result](
                const FVector& PositionCm,
                FRaftSimFlexUniformWater& OutWater) -> bool
            {
                FRaftSimWaterSample Sample;
                if (!Water->SampleWaterAtWorldPosition(PositionCm, Sample))
                {
                    return false;
                }
                OutWater.SurfaceHeightM = Sample.SurfaceHeightMeters;
                OutWater.VelocityMps = Sample.VelocityMetersPerSecond;
                OutWater.bWet = Sample.bWet;
                Result.MaximumSampledSpeedMps = FMath::Max(
                    Result.MaximumSampledSpeedMps,
                    Sample.VelocityMetersPerSecond.Size());
                return true;
            });

        constexpr float RaftDt = 1.0f / 120.0f;
        float ConsecutiveFlipRiskSeconds = 0.0f;
        for (int32 StepIndex = 0; StepIndex < 240; ++StepIndex)
        {
            if ((StepIndex % 2) == 0 && !Water->StepWater(1.0f / 60.0f))
            {
                Result.bFinite = false;
                break;
            }
            if (!Raft->StepRaftDynamics(RaftDt))
            {
                Result.bFinite = false;
                break;
            }
            const FRaftSimFlexStepTelemetry& Telemetry =
                Raft->GetLastFlexibleStepTelemetry();
            Result.MinimumSampleCount = FMath::Min(
                Result.MinimumSampleCount, Telemetry.LiveWaterSampleCount);
            Result.MinimumWetSampleCount = FMath::Min(
                Result.MinimumWetSampleCount, Telemetry.LiveWetSampleCount);
            Result.MinimumFlipMarginNm = FMath::Min(
                Result.MinimumFlipMarginNm, Telemetry.ReferenceFlipMarginNm);
            Result.MaximumRetainedWaterMassKg = FMath::Max(
                Result.MaximumRetainedWaterMassKg,
                Telemetry.TotalRetainedWaterMassKg);
            ConsecutiveFlipRiskSeconds = Telemetry.bReferenceFlipRisk
                ? ConsecutiveFlipRiskSeconds + RaftDt
                : 0.0f;
            Result.MaximumConsecutiveFlipRiskSeconds = FMath::Max(
                Result.MaximumConsecutiveFlipRiskSeconds,
                ConsecutiveFlipRiskSeconds);
            const FRaftSimRaftKinematicState& Current = Raft->GetKinematicState();
            const FRotator Rotation = Current.WorldTransform.Rotator();
            Result.MaximumAbsRollDegrees = FMath::Max(
                Result.MaximumAbsRollDegrees,
                FMath::Abs(FMath::UnwindDegrees(Rotation.Roll)));
            Result.bFinite &= Current.WorldTransform.IsValid() &&
                !Current.LinearVelocityMetersPerSecond.ContainsNaN() &&
                !Current.AngularVelocityRadiansPerSecond.ContainsNaN();
        }
        Result.FinalPositionM =
            Raft->GetKinematicState().WorldTransform.GetTranslation() * 0.01f;
        Result.bConfigured = true;
        return Result;
    };

    // Improper broadside entry into the interpreted mid-river hole is the
    // hazardous control. The comparison line stays downstream-facing on the
    // deeper river-left shoulder and uses the shipping guide high-side action.
    const FLineResult Hazard = RunLine(FVector2D(966.0, 0.4), 90.0f, false);
    const FLineResult Control = RunLine(FVector2D(930.0, 8.0), 0.0f, true);
    AddInfo(FString::Printf(
        TEXT("Meat Grinder hazard: samples=%d wet=%d speed=%.3f m/s mass=%.3f kg margin=%.3f Nm risk=%.3f s roll=%.3f deg final=(%.2f,%.2f,%.2f) m"),
        Hazard.MinimumSampleCount,
        Hazard.MinimumWetSampleCount,
        Hazard.MaximumSampledSpeedMps,
        Hazard.MaximumRetainedWaterMassKg,
        Hazard.MinimumFlipMarginNm,
        Hazard.MaximumConsecutiveFlipRiskSeconds,
        Hazard.MaximumAbsRollDegrees,
        Hazard.FinalPositionM.X,
        Hazard.FinalPositionM.Y,
        Hazard.FinalPositionM.Z));
    AddInfo(FString::Printf(
        TEXT("Meat Grinder control: samples=%d wet=%d speed=%.3f m/s mass=%.3f kg margin=%.3f Nm risk=%.3f s roll=%.3f deg final=(%.2f,%.2f,%.2f) m"),
        Control.MinimumSampleCount,
        Control.MinimumWetSampleCount,
        Control.MaximumSampledSpeedMps,
        Control.MaximumRetainedWaterMassKg,
        Control.MinimumFlipMarginNm,
        Control.MaximumConsecutiveFlipRiskSeconds,
        Control.MaximumAbsRollDegrees,
        Control.FinalPositionM.X,
        Control.FinalPositionM.Y,
        Control.FinalPositionM.Z));
    TestTrue(TEXT("hazard line configures from cooked high-flow water"),
             Hazard.bConfigured);
    TestTrue(TEXT("control line configures from cooked high-flow water"),
             Control.bConfigured);
    TestTrue(TEXT("hazard traversal remains finite"), Hazard.bFinite);
    TestTrue(TEXT("control traversal remains finite"), Control.bFinite);
    TestTrue(TEXT("hazard keeps live D3 tube sampling"),
             Hazard.MinimumSampleCount >= 12);
    TestTrue(TEXT("control keeps live D3 tube sampling"),
             Control.MinimumSampleCount >= 12);
    TestEqual(TEXT("hazard keeps every sampled tube segment wet"),
              Hazard.MinimumWetSampleCount, Hazard.MinimumSampleCount);
    TestEqual(TEXT("control keeps every sampled tube segment wet"),
              Control.MinimumWetSampleCount, Control.MinimumSampleCount);
    TestTrue(TEXT("broadside hole line sustains negative D3 margin past actor latch"),
             Hazard.MinimumFlipMarginNm < 0.0 &&
                 Hazard.MaximumConsecutiveFlipRiskSeconds >= 0.35f);
    TestTrue(TEXT("downstream-facing high-side control stays below D3 flip risk"),
             Control.MinimumFlipMarginNm > 0.0 &&
                 Control.MaximumConsecutiveFlipRiskSeconds < 0.35f);
    TestTrue(TEXT("hazard line remains within finite self-bailing capacity"),
             Hazard.MaximumRetainedWaterMassKg <= 600.001);
    TestTrue(TEXT("control line remains within finite self-bailing capacity"),
             Control.MaximumRetainedWaterMassKg <= 600.001);
    TestTrue(TEXT("control line remains upright through the measured encounter"),
             Control.MaximumAbsRollDegrees < 20.0f);
    TestTrue(TEXT("named-rapid trajectories remain in the source elevation envelope"),
             FMath::Abs(Hazard.FinalPositionM.Z) < 1000.0f &&
                 FMath::Abs(Control.FinalPositionM.Z) < 1000.0f);
    return true;
#endif // RAFTSIM_HAS_LIVE_SOLVER
}

#endif // WITH_AUTOMATION_TESTS
