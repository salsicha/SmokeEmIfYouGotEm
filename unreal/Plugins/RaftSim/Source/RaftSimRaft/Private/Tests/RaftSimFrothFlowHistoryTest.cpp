#include "Misc/AutomationTest.h"
#include "RaftSimFrothFlowHistory.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFrothFlowHistoryTest,
    "RaftSim.Water.FrothFlowHistory",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimFrothFlowHistoryTest::RunTest(const FString&)
{
    FRaftSimFrothFlowHistory H;TArray<FVector4f> Flow;Flow.Init(FVector4f(2,1,0,0),4);
    const FIntPoint Size(2,2);const FVector2f Origin(-5430,3600);
    TestTrue(TEXT("first original interval"),H.Append(0,.125,0,Size,Origin,.5f,Flow));
    TestTrue(TEXT("unchanged source coalesces"),H.Append(.125,.25,0,Size,Origin,.5f,Flow));
    TestEqual(TEXT("one exact input interval"),H.Intervals.Num(),1);
    Flow[0].Y=2;
    TestTrue(TEXT("different source retained"),H.Append(.25,.5,.25,Size,Origin,.5f,Flow));
    TestEqual(TEXT("caller mutation cannot change old source"),H.Intervals[0].Flow[0].Y,1.f);
    TestFalse(TEXT("gap is not frozen continuation"),H.Append(.6,.7,.5,Size,Origin,.5f,Flow));
    TestFalse(TEXT("overlap rejected"),H.Append(.4,.6,.5,Size,Origin,.5f,Flow));
    TestFalse(TEXT("hold does not manufacture interval"),H.Append(.5,.5,.5,Size,Origin,.5f,Flow));
    TestTrue(TEXT("remap retains old frame"),H.Append(.5,.75,.5,Size,Origin+FVector2f(.5,0),.5f,Flow));
    TestTrue(TEXT("old origin remains exact"),H.Intervals[0].Origin==Origin);
    for(int32 N=3;N<12;++N)TestTrue(TEXT("advance"),H.Append(N*.25,(N+1)*.25,N*.25,Size,Origin,.5f,Flow));
    TestTrue(TEXT("bounded complete retained intervals"),H.Intervals.Num()<=6 && H.Intervals[0].Start<=1.75 && H.Intervals[0].End>1.75);
    H.Reset();TestTrue(TEXT("teleport discards history"),H.Intervals.IsEmpty());
    TestTrue(TEXT("explicit restart clock"),H.Append(0,.25,99,Size,Origin,.5f,Flow));
    const int32 Count=H.Intervals.Num();Flow[0].X=-1;
    TestFalse(TEXT("invalid original flow rejected"),H.Append(.25,.5,99,Size,Origin,.5f,Flow));
    TestEqual(TEXT("rejection keeps evidence"),H.Intervals.Num(),Count);
    return !HasAnyErrors();
}
#endif
