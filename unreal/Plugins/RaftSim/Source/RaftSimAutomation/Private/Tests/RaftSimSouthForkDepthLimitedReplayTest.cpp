#include "Misc/AutomationTest.h"
#include "RaftSimWaterRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSouthForkDepthLimitedReplayTest,
    "RaftSim.Survey.SouthForkDepthLimitedCandidateReplay",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FRaftSimSouthForkDepthLimitedReplayTest::RunTest(const FString&)
{
    const FString Directory=TEXT("tmp/south-fork-survey-hydraulics/1m-mixed-inlet-depth-limited-hydrostatic-20260907/engine_review");
    URaftSimWaterRuntimeAdapter* Adapter=NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest=false;
    Config.bEnableDeterministicCapture=false;
    Adapter->Configure(Config);
    if (!TestTrue(TEXT("candidate coordinate map loads"),Adapter->ConfigureRiverCoordinateMap(Directory/TEXT("coordinate_map.json"))) ||
        !TestTrue(TEXT("candidate fields load"),Adapter->ConfigureRiverWindow(
            Directory,TEXT("median_runnable"),FVector2D::ZeroVector,FVector2D(273,273),0.041f,false))) return false;
    FVector Position;
    if (!TestTrue(TEXT("candidate start maps"),Adapter->RiverToWorldPosition(FVector2D(-60,-9),228.0519848f,Position))) return false;
    TestTrue(TEXT("east registration"),FMath::Abs(Position.X-5910.802955)<0.03);
    TestTrue(TEXT("north registration"),FMath::Abs(Position.Y+1368.359758)<0.03);
    TestTrue(TEXT("datum applied once"),FMath::Abs(Position.Z-805.19848)<0.03);
    FRaftSimWaterSample Sample;
    if (!TestTrue(TEXT("candidate sample exists"),Adapter->SampleWaterAtWorldPosition(Position,Sample))) return false;
    // Independent float32 field values at (row 71, column 75), not old-package values.
    TestTrue(TEXT("candidate initial depth"),Sample.bWet && FMath::Abs(Sample.DepthMeters-1.110561967f)<0.003f);
    TestTrue(TEXT("candidate initial stage"),FMath::Abs(Sample.SurfaceHeightMeters-8.051984787f)<0.003f);
    FRaftSimWaterLiveWindowStats Stats;
    if (!TestTrue(TEXT("candidate initial stats"),Adapter->GetLiveWindowStats(Stats))) return false;
    TestTrue(TEXT("candidate initial volume"),FMath::Abs(Stats.TotalWaterVolumeM3-16533.64105)<1.0);
    for (int32 Step=0;Step<120;++Step)
        if (!TestTrue(TEXT("candidate replay advances"),Adapter->StepWater(1.0f/60.0f))) return false;
    if (!TestTrue(TEXT("candidate evolved stats"),Adapter->GetLiveWindowStats(Stats))) return false;
    TestFalse(TEXT("candidate replay finite"),Stats.bHasNonFinite);
    TestTrue(TEXT("candidate storage remains bounded"),FMath::Abs(Stats.TotalWaterVolumeM3-16533.64105)<20.0);
    AddInfo(TEXT("Two-second candidate registration/replay only; no spatial-convergence or visual acceptance."));
    return true;
}
#endif
