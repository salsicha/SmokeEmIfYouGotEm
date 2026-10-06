#include "Misc/AutomationTest.h"
#include "RaftSimWaterRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSouthForkRegisteredRockReplayTest,
    "RaftSim.Survey.SouthForkRegisteredRockCandidateReplay",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FRaftSimSouthForkRegisteredRockReplayTest::RunTest(const FString&)
{
    const FString Directory=TEXT("tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907/engine_review");
    URaftSimWaterRuntimeAdapter* Adapter=NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest=false;
    Config.bEnableDeterministicCapture=false;
    Adapter->Configure(Config);
    if (!TestTrue(TEXT("registered candidate coordinate map loads"),Adapter->ConfigureRiverCoordinateMap(Directory/TEXT("coordinate_map.json"))) ||
        !TestTrue(TEXT("registered candidate fields load"),Adapter->ConfigureRiverWindow(
            Directory,TEXT("median_runnable"),FVector2D::ZeroVector,FVector2D(273,273),0.041f,false))) return false;
    FVector Position;
    if (!TestTrue(TEXT("registered candidate start maps"),Adapter->RiverToWorldPosition(FVector2D(-60,-9),228.0485754f,Position))) return false;
    TestTrue(TEXT("east registration"),FMath::Abs(Position.X-5910.802955)<0.03);
    TestTrue(TEXT("north registration"),FMath::Abs(Position.Y+1368.359758)<0.03);
    TestTrue(TEXT("datum applied once"),FMath::Abs(Position.Z-804.85754)<0.03);
    FRaftSimWaterSample Sample;
    if (!TestTrue(TEXT("registered candidate sample exists"),Adapter->SampleWaterAtWorldPosition(Position,Sample))) return false;
    // Independent exported float32 values, at row 71 / column 75. This must
    // not silently load the old raster-centred geometry or its solved state.
    TestTrue(TEXT("registered candidate initial depth"),Sample.bWet && FMath::Abs(Sample.DepthMeters-1.107152820f)<0.003f);
    TestTrue(TEXT("registered candidate initial stage"),FMath::Abs(Sample.SurfaceHeightMeters-8.048575401f)<0.003f);
    FRaftSimWaterLiveWindowStats Stats;
    if (!TestTrue(TEXT("registered candidate initial stats"),Adapter->GetLiveWindowStats(Stats))) return false;
    TestTrue(TEXT("registered candidate initial volume"),FMath::Abs(Stats.TotalWaterVolumeM3-16530.28614)<1.0);
    for (int32 Step=0;Step<120;++Step)
        if (!TestTrue(TEXT("registered candidate replay advances"),Adapter->StepWater(1.0f/60.0f))) return false;
    if (!TestTrue(TEXT("registered candidate evolved stats"),Adapter->GetLiveWindowStats(Stats))) return false;
    TestFalse(TEXT("registered candidate replay finite"),Stats.bHasNonFinite);
    TestTrue(TEXT("registered candidate storage remains bounded"),FMath::Abs(Stats.TotalWaterVolumeM3-16530.28614)<20.0);
    AddInfo(TEXT("Two-second corrected-rock registration/replay only; not traversal, spatial-convergence or visual acceptance."));
    return true;
}
#endif
