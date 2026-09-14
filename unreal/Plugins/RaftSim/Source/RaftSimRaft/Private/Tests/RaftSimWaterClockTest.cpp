#include "Misc/AutomationTest.h"
#include "RaftSimFixedStepClock.h"
#include "RaftSimCommittedWaterClock.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "Engine/GameInstance.h"
#include "Subsystems/SubsystemCollection.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFixedWaterClockTest,"RaftSim.Clock.FixedQueue",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFixedWaterClockTest::RunTest(const FString&)
{
    const double Step=double(1.f/60.f);
    for(int32 TicksPerFrame : {1,2})
    {
        FRaftSimFixedStepClock Clock;int32 Calls=0,Completed=0;
        for(int32 Frame=0;Frame<300;++Frame)
        {
            TestTrue(TEXT("ordinary render frame accepted"),Clock.Advance(TicksPerFrame*Step,Step,4,[&]{++Calls;return true;},Completed));
            TestEqual(TEXT("fixed ticks independent of render rate"),Completed,TicksPerFrame);
        }
        TestEqual(TEXT("60/30 FPS retain full simulation duration"),Clock.CommittedSeconds,300*TicksPerFrame*Step);
        TestEqual(TEXT("all fixed ticks executed"),Calls,300*TicksPerFrame);
        TestEqual(TEXT("no ordinary frame debt"),Clock.BacklogSeconds,0.);
    }
    FRaftSimFixedStepClock Clock;int32 Calls=0,Completed=0;
    auto Tick=[&]{++Calls;return true;};
    TestTrue(TEXT("hitch queues work"),Clock.Advance(.5,1./64.,4,Tick,Completed));
    TestEqual(TEXT("bounded work after hitch"),Completed,4);
    TestEqual(TEXT("hitch is not clipped to one tick"),Clock.BacklogSeconds,28./64.);
    for(int32 Frame=0;Frame<7;++Frame)TestTrue(TEXT("queued hitch drains"),Clock.Advance(0,1./64.,4,Tick,Completed));
    TestEqual(TEXT("no discarded hitch ticks"),Calls,32);
    TestEqual(TEXT("hitch duration conserved"),Clock.CommittedSeconds,.5);
    TestEqual(TEXT("hitch debt drained"),Clock.BacklogSeconds,0.);
    Clock.Reset();Calls=0;
    TestFalse(TEXT("failure stops this frame"),Clock.Advance(.5,1./64.,4,[&]{return ++Calls<2;},Completed));
    TestEqual(TEXT("only successful ticks committed"),Completed,1);
    TestEqual(TEXT("failed tick debt retained"),Clock.BacklogSeconds,31./64.);
    TestTrue(TEXT("retained debt can resume"),Clock.Advance(0,1./64.,4,Tick,Completed));
    TestEqual(TEXT("only accepted duration counted"),Clock.CommittedSeconds,5./64.);
    const double BeforeRequested=Clock.RequestedSeconds,BeforeDebt=Clock.BacklogSeconds;
    for(double Bad : {-1.,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()})
        TestFalse(TEXT("invalid frame refused"),Clock.Advance(Bad,Step,4,Tick,Completed));
    TestFalse(TEXT("zero step refused"),Clock.Advance(1,0,4,Tick,Completed));
    TestFalse(TEXT("zero work budget refused"),Clock.Advance(1,Step,0,Tick,Completed));
    TestEqual(TEXT("invalid input does not change request"),Clock.RequestedSeconds,BeforeRequested);
    TestEqual(TEXT("invalid input does not erase debt"),Clock.BacklogSeconds,BeforeDebt);
    Clock.Reset();Calls=0;
    TestFalse(TEXT("unrepresentable debt cannot spin or commit"),Clock.Advance(1e300,Step,4,Tick,Completed));
    TestEqual(TEXT("unrepresentable tick not invoked"),Calls,0);
    TestEqual(TEXT("unrepresentable work remains uncommitted"),Clock.CommittedSeconds,0.);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCommittedWaterClockTest,"RaftSim.Clock.CommittedDetail",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCommittedWaterClockTest::RunTest(const FString&)
{
    FRaftSimCommittedWaterClock Clock;double Delta=99;
    TestTrue(TEXT("initialize at nonzero committed time"),Clock.Initialize(12.5));
    TestTrue(TEXT("unchanged water holds detail"),Clock.Observe(12.5,Delta));
    TestEqual(TEXT("no wall-time extrapolation"),Delta,0.);
    TestTrue(TEXT("accepted water advances detail"),Clock.Observe(12.75,Delta));
    TestEqual(TEXT("exact committed delta"),Delta,.25);
    TestEqual(TEXT("target relative to attachment"),Clock.TargetSeconds(),.25);
    for(double Bad : {12.,-1.,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()})
    {
        TestFalse(TEXT("invalid/regressed source refused"),Clock.Observe(Bad,Delta));
        TestEqual(TEXT("rejected source has no elapsed duration"),Delta,0.);
        TestEqual(TEXT("rejected source preserves last observation"),Clock.Last,12.75);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNativeWaterClockTest,"RaftSim.Clock.NativeBridge",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FNativeWaterClockTest::RunTest(const FString&)
{
    UGameInstance* Instance=NewObject<UGameInstance>();
    URaftSimPhysicsBridgeSubsystem* Bridge=NewObject<URaftSimPhysicsBridgeSubsystem>(Instance);
    FSubsystemCollection<UGameInstanceSubsystem> Collection;
    Bridge->Initialize(Collection);
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest=false;
    Config.AcceptedReportSetManifestPath.Reset();
    Config.bEnableDeterministicCapture=false;
    const float Step=1.f/60.f;
    Bridge->ConfigureBridge(Config,FRaftSimRaftBodyConfig(),FRaftSimWaterRaftCouplingPolicy(),Step,Step*.5f);
    auto* Water=Bridge->GetWaterRuntime();
    if(!TestTrue(TEXT("actual native FV tank created"),Water && Water->ConfigureDevTankWindow(FVector2D::ZeroVector,4,4,.5,0,1)))
    {Bridge->Deinitialize();return false;}
    FRaftSimPhysicsTickInput Input;Input.FrameDeltaSeconds=2*Step;
    for(int32 Frame=0;Frame<30;++Frame)
    {
        const auto Output=Bridge->TickBridge(Input);
        TestFalse(TEXT("native fixed tick succeeds"),Output.bFixedTickFailed);
        TestEqual(TEXT("30 FPS executes two water/raft ticks"),Output.FixedTicksThisFrame,2);
        TestEqual(TEXT("native ordinary frame has no backlog"),Output.SimulationBacklogSeconds,0.);
    }
    double NativeSeconds=0;
    TestTrue(TEXT("native field clock observable"),Water->GetLiveFieldTimeSeconds(NativeSeconds));
    TestEqual(TEXT("native solver advanced all 60 steps"),NativeSeconds,60*double(Step));
    TestEqual(TEXT("adapter and actual native clock agree"),Water->GetCommittedStepSeconds(),NativeSeconds);
    TestEqual(TEXT("raft and water committed same frame count"),Bridge->GetLastOutput().CommittedPhysicsFrame,Water->GetCommittedWaterFrame());
    FRaftSimCommittedWaterClock DetailClock;DetailClock.Initialize(Water->GetCommittedStepSeconds());
    const double Before=Water->GetCommittedStepSeconds();
    TestTrue(TEXT("explicit cold spatial boot succeeds"),Water->ConfigureDevTankWindow(FVector2D(20,20),4,4,.5,0,1));
    TestTrue(TEXT("cold native clock observable"),Water->GetLiveFieldTimeSeconds(NativeSeconds));
    TestEqual(TEXT("cold field has new local epoch"),NativeSeconds,0.);
    TestEqual(TEXT("spatial boot preserves committed duration"),Water->GetCommittedStepSeconds(),Before);
    Bridge->TickBridge(Input);
    double Delta=0;
    TestTrue(TEXT("detail follows committed timeline across spatial boot"),DetailClock.Observe(Water->GetCommittedStepSeconds(),Delta));
    TestEqual(TEXT("no rewind or invented elapsed time after spatial boot"),Delta,2*double(Step));
    const double BeforeFault=Water->GetCommittedStepSeconds();
    const int32 FrameBeforeFault=Water->GetCommittedWaterFrame();
    AddExpectedError(TEXT("RaftSim native water clock mismatch"),EAutomationExpectedErrorFlags::Contains,1);
    TestFalse(TEXT("native large-dt clipping cannot claim full completion"),Water->StepWater(.2f));
    TestEqual(TEXT("mismatched advance latches fault"),Water->GetStatus(),ERaftSimWaterRuntimeStatus::Faulted);
    TestEqual(TEXT("mismatched advance does not publish requested duration"),Water->GetCommittedStepSeconds(),BeforeFault);
    TestEqual(TEXT("mismatched advance does not publish frame"),Water->GetCommittedWaterFrame(),FrameBeforeFault);
    const auto FaultedOutput=Bridge->TickBridge(Input);
    TestTrue(TEXT("bridge reports native fault"),FaultedOutput.bFixedTickFailed);
    TestEqual(TEXT("failed water does not commit raft tick"),FaultedOutput.FixedTicksThisFrame,0);
    TestEqual(TEXT("failed request debt retained"),FaultedOutput.SimulationBacklogSeconds,2*double(Step));
    Bridge->Deinitialize();
    return true;
}
#endif
