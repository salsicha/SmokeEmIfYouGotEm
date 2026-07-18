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

#endif // WITH_AUTOMATION_TESTS
