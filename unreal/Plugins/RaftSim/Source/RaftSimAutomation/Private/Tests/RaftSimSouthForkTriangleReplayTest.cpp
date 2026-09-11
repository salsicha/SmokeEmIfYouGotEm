// The previous gap test deliberately retains its bilinear fixture. This test
// exercises the distinct mesh-triangle hydraulic package, without promoting it.
#include "Misc/AutomationTest.h"
#include "RaftSimWaterRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSouthForkTriangleReplayTest,
    "RaftSim.Survey.SouthForkTriangleCandidateReplay",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FRaftSimSouthForkTriangleReplayTest::RunTest(const FString&)
{
    const FString Directory=TEXT("tmp/south-fork-survey-hydraulics/1m-mixed-inlet-mesh-triangles-20260907/engine_review");
    URaftSimWaterRuntimeAdapter* Adapter=NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest=false;
    Config.bEnableDeterministicCapture=false;
    Adapter->Configure(Config);
    if (!TestTrue(TEXT("triangle coordinate map loads"),Adapter->ConfigureRiverCoordinateMap(Directory/TEXT("coordinate_map.json"))) ||
        !TestTrue(TEXT("triangle fields load"),Adapter->ConfigureRiverWindow(
            Directory,TEXT("median_runnable"),FVector2D::ZeroVector,FVector2D(273,273),0.041f,false))) return false;
    // Independently read from the exported float32 arrays at grid (row 72,col 75).
    FVector Position;
    if (!TestTrue(TEXT("triangle spawn maps"),Adapter->RiverToWorldPosition(FVector2D(-60,-8),228.08081436f,Position))) return false;
    TestTrue(TEXT("east registration"),FMath::Abs(Position.X-5874.046961)<0.03);
    TestTrue(TEXT("north registration"),FMath::Abs(Position.Y+1461.359742)<0.03);
    TestTrue(TEXT("datum applied once"),FMath::Abs(Position.Z-808.081436)<0.03);
    FRaftSimWaterSample Sample;
    if (!TestTrue(TEXT("triangle sample exists"),Adapter->SampleWaterAtWorldPosition(Position,Sample))) return false;
    TestTrue(TEXT("triangle initial depth"),Sample.bWet && FMath::Abs(Sample.DepthMeters-1.143263698f)<0.003f);
    TestTrue(TEXT("triangle initial stage"),FMath::Abs(Sample.SurfaceHeightMeters-8.08081436f)<0.003f);
    FRaftSimWaterLiveWindowStats Stats;
    if (!TestTrue(TEXT("initial triangle stats"),Adapter->GetLiveWindowStats(Stats))) return false;
    TestTrue(TEXT("triangle grid volume"),FMath::Abs(Stats.TotalWaterVolumeM3-16878.08355)<1.0);
    for (int32 Step=0;Step<120;++Step)
        if (!TestTrue(TEXT("triangle replay advances"),Adapter->StepWater(1.0f/60.0f))) return false;
    if (!TestTrue(TEXT("evolved triangle stats"),Adapter->GetLiveWindowStats(Stats))) return false;
    TestFalse(TEXT("triangle replay finite"),Stats.bHasNonFinite);
    TestTrue(TEXT("triangle replay bounded storage"),Stats.TotalWaterVolumeM3>16000 && Stats.TotalWaterVolumeM3<17500);
    AddInfo(TEXT("Two-second registration regression only; settling, convergence and visual acceptance remain separate."));
    return true;
}
#endif
