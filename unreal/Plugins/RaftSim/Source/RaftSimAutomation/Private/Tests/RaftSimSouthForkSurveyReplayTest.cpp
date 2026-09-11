// Opt-in diagnostic gate. Requires export_south_fork_survey_review_fields.py;
// this test does not certify rapid identity, photorealism or production data.
#include "Misc/AutomationTest.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimSouthForkSurveyReplayTest,
    "RaftSim.Survey.SouthForkRegisteredReplay",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FRaftSimSouthForkSurveyReplayTest::RunTest(const FString&)
{
    const FString Directory = TEXT(
        "tmp/south-fork-survey-hydraulics/1m-mixed-inlet-conservative-edge/engine_review");
    URaftSimWaterRuntimeAdapter* Adapter = NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest = false;
    Config.bEnableDeterministicCapture = false;
    Adapter->Configure(Config);
    if (!TestTrue(TEXT("rigid map loads"), Adapter->ConfigureRiverCoordinateMap(Directory / TEXT("coordinate_map.json"))) ||
        !TestTrue(TEXT("complete replay field loads"), Adapter->ConfigureRiverWindow(
            Directory, TEXT("median_runnable"), FVector2D::ZeroVector, FVector2D(273.0,273.0),0.041f,false)))
    {
        return false;
    }
    FVector Position;
    TestTrue(TEXT("local grid point maps to geographic world"),
        Adapter->RiverToWorldPosition(FVector2D(-61.0,-2.0),228.12757497817572f,Position));
    TestTrue(TEXT("east coordinate preserves rigid rotation"), FMath::Abs(Position.X-5746.510984)<0.02);
    TestTrue(TEXT("north coordinate preserves rigid rotation"), FMath::Abs(Position.Y+2056.115636)<0.02);
    TestTrue(TEXT("NAVD88 datum applied exactly once"),FMath::Abs(Position.Z-812.757498)<0.02);
    FRaftSimWaterSample Sample;
    TestTrue(TEXT("registered water sample exists"),Adapter->SampleWaterAtWorldPosition(Position,Sample));
    TestTrue(TEXT("registered water sample is wet"),Sample.bWet && Sample.DepthMeters>1.0f);
    TestTrue(TEXT("water surface matches source state"),FMath::Abs(Sample.SurfaceHeightMeters-8.127574978)<0.003);
    TestTrue(TEXT("water normal points above the terrain"),Sample.SurfaceNormal.Z>0.0f);
    TestFalse(TEXT("non-finite time step is rejected"),
        Adapter->StepWater(std::numeric_limits<float>::quiet_NaN()));
    TestEqual(TEXT("rejected time step commits no water frame"),Adapter->GetCommittedWaterFrame(),0);
    for (int32 Step=0;Step<60;++Step)
    {
        if (!TestTrue(TEXT("replay advances"),Adapter->StepWater(1.0f/60.0f))) return false;
    }
    FRaftSimWaterLiveWindowStats Stats;
    TestTrue(TEXT("replay stats available"),Adapter->GetLiveWindowStats(Stats));
    TestFalse(TEXT("replay remains finite"),Stats.bHasNonFinite);
    TestTrue(TEXT("replay retains positive storage"),Stats.TotalWaterVolumeM3>16000 && Stats.TotalWaterVolumeM3<17500);
    // A total-discharge inlet must not be silently applied to a partial crop.
    AddExpectedError(TEXT("Survey replay requires the complete grid"),EAutomationExpectedErrorFlags::Contains,1);
    TestFalse(TEXT("partial survey replay is rejected"),Adapter->ConfigureRiverWindow(
        Directory,TEXT("median_runnable"),FVector2D::ZeroVector,FVector2D(100,80),0.041f,false));
    TestFalse(TEXT("missing acceptance manifest faults explicitly"),
        Adapter->LoadAcceptedReportManifest(Directory/TEXT("nonexistent-acceptance-regression.json")));
    const int32 BeforeFaultRetry=Adapter->GetCommittedWaterFrame();
    TestFalse(TEXT("faulted adapter cannot silently restart on the next tick"),Adapter->StepWater(1.0f/60.0f));
    TestTrue(TEXT("fault remains latched"),Adapter->GetStatus()==ERaftSimWaterRuntimeStatus::Faulted);
    TestEqual(TEXT("fault retry commits no water frame"),Adapter->GetCommittedWaterFrame(),BeforeFaultRetry);
    return true;
}
#endif
