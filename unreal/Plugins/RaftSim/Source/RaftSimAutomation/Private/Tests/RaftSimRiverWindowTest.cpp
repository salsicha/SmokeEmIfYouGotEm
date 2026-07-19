// P2 river-window gate (release-1.0-plan.md §5 A-1 / §7 P2): a live solver
// window seeded from the cooked South Fork steady flow fields loads with
// verified hashes, steps the genuine FV solver, and stays physical.

#include "Misc/AutomationTest.h"
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
    TestTrue(
        TEXT("downstream station velocity rotates into the route tangent"),
        FVector::DotProduct(Water.VelocityMetersPerSecond, Tangent) > 0.0f);
    TestTrue(TEXT("rotated water surface normal is unit length"), Water.SurfaceNormal.IsUnit(1.0e-3f));

    FVector OutsideWorldPosition;
    TestTrue(
        TEXT("outside-bank coordinate still maps to world"),
        Adapter->RiverToWorldPosition(
            FVector2D(5000.0, 180.0), Adapter->GetRiverVerticalDatumM(), OutsideWorldPosition));
    TestFalse(
        TEXT("outside the finite live crop does not create fallback water"),
        Adapter->SampleWaterAtWorldPosition(OutsideWorldPosition, Water));
    return true;
#endif // RAFTSIM_HAS_LIVE_SOLVER
}

#endif // WITH_AUTOMATION_TESTS
