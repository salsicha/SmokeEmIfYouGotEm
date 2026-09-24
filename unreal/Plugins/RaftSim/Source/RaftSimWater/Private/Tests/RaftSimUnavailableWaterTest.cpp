#include "RaftSimWaterRuntimeAdapter.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimUnavailableWaterTest,
    "RaftSim.M3.UnavailableWaterFailsClosed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimUnavailableWaterTest::RunTest(const FString&)
{
    auto* Water=NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterSample Sample;
    const auto CheckMissing=[&]()
    {
        for(float Z:{-10000.f,0.f,25000.f})
        {
            TestFalse(TEXT("absent field never fabricates world water"),
                Water->SampleWaterAtWorldPosition(FVector(200,300,Z),Sample));
            TestFalse(TEXT("absent field never fabricates raft support"),
                Water->SampleRaftSupportSurfaceAtWorldPosition(FVector(200,300,Z),Sample));
        }
        TestFalse(TEXT("absent field never fabricates river water"),
            Water->SampleWaterFieldAtRiverCoordinates(FVector2D(2,3),Sample));
    };
    CheckMissing();
    FRaftSimWaterRuntimeConfig Config;
    Config.ScenarioPackagePath=TEXT("unavailable-water-test");
    Config.AcceptedReportSetManifestPath.Empty();
    Config.bRequireAcceptedReportManifest=false;
    Config.bEnableDeterministicCapture=false;
    Water->Configure(Config);
    CheckMissing();
    TestTrue(TEXT("scenario clock may run without creating a water field"),Water->StepWater(.05f));
    CheckMissing();
#if RAFTSIM_HAS_LIVE_SOLVER
    if(!TestTrue(TEXT("explicit physical tank loads"),
        Water->ConfigureDevTankWindow(FVector2D(0,0),10,10,1,5,2)))return false;
    for(float Z:{-10000.f,0.f,25000.f})
    {
        TestTrue(TEXT("valid tank samples independently of probe height"),
            Water->SampleWaterAtWorldPosition(FVector(200,300,Z),Sample));
        TestEqual(TEXT("tank stage remains metric"),Sample.SurfaceHeightMeters,5.f);
        TestEqual(TEXT("tank bed remains metric"),Sample.BedHeightMeters,3.f);
        TestEqual(TEXT("tank depth remains physical"),Sample.DepthMeters,2.f);
    }
    TestFalse(TEXT("missing required manifest faults the existing adapter"),
        Water->LoadAcceptedReportManifest(TEXT("Saved/Automation/RaftSim/does-not-exist-unavailable-water.json")));
    CheckMissing();
    TestTrue(TEXT("explicit valid reload recovers from fault"),
        Water->ConfigureDevTankWindow(FVector2D(0,0),10,10,1,5,2));
    TestTrue(TEXT("recovered tank samples"),Water->SampleWaterAtWorldPosition(FVector(200,300,0),Sample));
#endif
    return !HasAnyErrors();
}
#endif
