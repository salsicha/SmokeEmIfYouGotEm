// Separate fixture: the original registered-replay regression still exercises
// the original conservative-edge package and must not be mistaken for this one.
#include "Misc/AutomationTest.h"
#include "RaftSimWaterRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSouthForkGapReplayTest,
    "RaftSim.Survey.SouthForkGapCandidateReplay",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FRaftSimSouthForkGapReplayTest::RunTest(const FString&)
{
    const FString Directory=TEXT("tmp/south-fork-survey-hydraulics/1m-mixed-inlet-enclosed-rock-gaps-continuation-20260907/engine_review");
    URaftSimWaterRuntimeAdapter* Adapter=NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest=false;
    Config.bEnableDeterministicCapture=false;
    Adapter->Configure(Config);
    if (!TestTrue(TEXT("candidate coordinate map loads"),Adapter->ConfigureRiverCoordinateMap(Directory/TEXT("coordinate_map.json"))) ||
        !TestTrue(TEXT("candidate complete fields load"),Adapter->ConfigureRiverWindow(
            Directory,TEXT("median_runnable"),FVector2D::ZeroVector,FVector2D(273,273),0.041f,false))) return false;
    // Fixture from the exported final state, not an authored target wave.
    FVector Position;
    if (!TestTrue(TEXT("candidate spawn maps"),Adapter->RiverToWorldPosition(FVector2D(-60,-8),228.0731492f,Position))) return false;
    TestTrue(TEXT("candidate east coordinate"),FMath::Abs(Position.X-5874.046961)<0.03);
    TestTrue(TEXT("candidate north coordinate"),FMath::Abs(Position.Y+1461.359742)<0.03);
    TestTrue(TEXT("candidate datum applied once"),FMath::Abs(Position.Z-807.31492)<0.03);
    FRaftSimWaterSample Sample;
    if (!TestTrue(TEXT("candidate sample exists"),Adapter->SampleWaterAtWorldPosition(Position,Sample))) return false;
    TestTrue(TEXT("candidate initial depth matches source"),Sample.bWet && FMath::Abs(Sample.DepthMeters-1.13562524f)<0.003f);
    TestTrue(TEXT("candidate initial stage matches source"),FMath::Abs(Sample.SurfaceHeightMeters-8.0731492f)<0.003f);
    FRaftSimWaterLiveWindowStats Stats;
    if (!TestTrue(TEXT("candidate initial stats available"),Adapter->GetLiveWindowStats(Stats))) return false;
    TestTrue(TEXT("candidate complete grid volume matches export"),FMath::Abs(Stats.TotalWaterVolumeM3-16833.5977)<1.0);
    for (int32 Step=0;Step<120;++Step)
        if (!TestTrue(TEXT("candidate replay advances"),Adapter->StepWater(1.0f/60.0f))) return false;
    if (!TestTrue(TEXT("candidate evolved stats available"),Adapter->GetLiveWindowStats(Stats))) return false;
    TestFalse(TEXT("candidate replay stays finite"),Stats.bHasNonFinite);
    TestTrue(TEXT("candidate replay retains bounded storage"),Stats.TotalWaterVolumeM3>16000 && Stats.TotalWaterVolumeM3<17500);
    AddInfo(TEXT("Two-second candidate replay is a registration regression, not long-run stability or visual acceptance."));
    return true;
}
#endif
