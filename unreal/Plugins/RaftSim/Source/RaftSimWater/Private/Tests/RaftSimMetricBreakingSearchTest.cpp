#include "RaftSimMetricBreakingSearch.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimMetricBreakingSearchTest,
    "RaftSim.P2.MetricBreakingSearch",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimMetricBreakingSearchTest::RunTest(const FString&)
{
    for(float Spacing:{.5f,1.f,1.5f})
    {
        constexpr int32 N=41;
        const int32 Center=20*N+20;
        TArray<uint8> Wet;Wet.Init(1,N*N);
        TArray<float> Fr;Fr.Init(1.f,N*N);Fr[Center]=.8f;
        const int32 Up=Center-FMath::RoundToInt(6.f/Spacing);
        Fr[Up]=1.5f;
        const auto Direction=[](int32){return FVector2D(1.,0.);};
        const auto Find=[&](){return RaftSimMetricBreakingSearch::Find(Center,N,N,Spacing,
            FMath::RoundToInt(2.f/Spacing),FVector2D(1.,0.),Wet,Fr,Direction);};
        TestEqual(TEXT("same six-metre transition across carrier resolutions"),Find(),Up);
        Wet[Center-1]=0;
        TestEqual(TEXT("dry path cannot bridge to wet upstream endpoint"),Find(),INDEX_NONE);
        Wet[Center-1]=1;Fr[Up]=1.119f;
        TestEqual(TEXT("upstream threshold is not lowered"),Find(),INDEX_NONE);
        Fr[Up]=1.5f;Fr[Center]=.941f;
        TestEqual(TEXT("downstream threshold retained"),Find(),INDEX_NONE);
        Fr[Center]=.8f;
        TestEqual(TEXT("opposed current rejected"),RaftSimMetricBreakingSearch::Find(Center,N,N,Spacing,
            2,FVector2D(1.,0.),Wet,Fr,[](int32){return FVector2D(-1.,0.);}),INDEX_NONE);
    }
    constexpr int32 N=21,Center=10*N+10;
    TArray<uint8> Wet;Wet.Init(1,N*N);
    TArray<float> Fr;Fr.Init(1.f,N*N);Fr[Center]=.8f;
    const FVector2D D=FVector2D(1.,1.).GetSafeNormal();
    Fr[8*N+8]=1.5f;
    const auto Find=[&](){return RaftSimMetricBreakingSearch::Find(Center,N,N,1.f,2,D,Wet,Fr,[&](int32){return D;});};
    TestEqual(TEXT("diagonal connected front"),Find(),8*N+8);
    Wet[10*N+9]=0;
    TestEqual(TEXT("dry corner cannot be crossed diagonally"),Find(),INDEX_NONE);
    Wet[10*N+9]=1;
    TestEqual(TEXT("already covered six-metre path adds nothing"),RaftSimMetricBreakingSearch::Find(
        Center,N,N,1.f,6,D,Wet,Fr,[&](int32){return D;}),INDEX_NONE);
    for(int32 Step:{6,12})
    {
        Fr.Init(1.f,N*N);Fr[Center]=.8f;
        const int32 Up=RaftSimWaterFlowFrame::OffsetIndex(Center,N,N,D,-Step);
        TestEqual(TEXT("fixture repeats rounded endpoint"),Up,
            RaftSimWaterFlowFrame::OffsetIndex(Center,N,N,D,-(Step-1)));
        Fr[Up]=1.5f;
        TestEqual(TEXT("half-metre diagonal endpoint is not skipped"),
            RaftSimMetricBreakingSearch::Find(Center,N,N,.5f,4,D,Wet,Fr,[&](int32){return D;}),Up);
        Wet[10*N+9]=0;
        TestEqual(TEXT("repeated endpoint still requires wet path"),
            RaftSimMetricBreakingSearch::Find(Center,N,N,.5f,4,D,Wet,Fr,[&](int32){return D;}),INDEX_NONE);
        Wet[10*N+9]=1;
    }
    return true;
}
#endif
