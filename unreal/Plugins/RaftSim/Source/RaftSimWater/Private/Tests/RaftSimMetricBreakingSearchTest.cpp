#include "RaftSimMetricBreakingSearch.h"
#include "RaftSimMetricBreakingSearchReference.h"
#include "Math/RandomStream.h"
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimMetricBreakingSearchEndpointPrefilterTest,
    "RaftSim.P2.MetricBreakingSearchEndpointPrefilter",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimMetricBreakingSearchEndpointPrefilterTest::RunTest(const FString&)
{
    constexpr int32 NX=41,NY=37,Center=18*NX+20;
    TArray<uint8> Wet;Wet.Init(1,NX*NY);
    TArray<float> Fr;Fr.Init(.8f,NX*NY);
    TArray<FVector2D> Directions;Directions.Init(FVector2D(1.,0.),NX*NY);
    int32 FastCalls=0,ReferenceCalls=0;
    const auto FastDirection=[&](int32 I){++FastCalls;return Directions[I];};
    const auto ReferenceDirection=[&](int32 I){++ReferenceCalls;return Directions[I];};
    TestEqual(TEXT("uniform subcritical fast rejection"),RaftSimMetricBreakingSearch::Find(
        Center,NX,NY,1.f,2,FVector2D(1.,0.),Wet,Fr,FastDirection),INDEX_NONE);
    TestEqual(TEXT("uniform subcritical reference rejection"),RaftSimMetricBreakingSearchReference::Find(
        Center,NX,NY,1.f,2,FVector2D(1.,0.),Wet,Fr,ReferenceDirection),INDEX_NONE);
    TestEqual(TEXT("ineligible endpoints need no direction samples"),FastCalls,0);
    TestEqual(TEXT("reference traverses six cells"),ReferenceCalls,6);
    FRandomStream Random(0x39ac17);
    int32 SurvivingCases=0,SavedDirectionCalls=0;
    for(int32 Case=0;Case<1600;++Case)
    {
        const float Spacings[]={.5f,.75f,1.f,1.5f,2.f,3.f,6.f,7.f};
        const float Spacing=Spacings[Case%UE_ARRAY_COUNT(Spacings)];
        const double Angle=Random.FRand()*2.*PI;
        const FVector2D D(FMath::Cos(Angle),FMath::Sin(Angle));
        for(int32 I=0;I<Fr.Num();++I)
        {
            Wet[I]=Random.FRand()>.04f;
            Fr[I]=Random.FRandRange(.2f,1.6f);
            Directions[I]=Random.FRand()>.04f ? D : -D;
        }
        const int32 Index=Case%3==0 ? Random.RandRange(0,NX*NY-1) : Center;
        Wet[Index]=1;Fr[Index]=Case%13==0 ? .95f : .8f;
        const int32 Existing=FMath::Max(1,FMath::RoundToInt(2.f/Spacing));
        FastCalls=ReferenceCalls=0;
        const int32 Fast=RaftSimMetricBreakingSearch::Find(Index,NX,NY,Spacing,Existing,D,Wet,Fr,FastDirection);
        const int32 Reference=RaftSimMetricBreakingSearchReference::Find(Index,NX,NY,Spacing,Existing,D,Wet,Fr,ReferenceDirection);
        if(!TestEqual(FString::Printf(TEXT("exact endpoint/path parity case %d"),Case),Fast,Reference))return false;
        if(!TestTrue(TEXT("prefilter never adds direction work"),FastCalls<=ReferenceCalls))return false;
        SurvivingCases+=Reference!=INDEX_NONE;
        SavedDirectionCalls+=ReferenceCalls-FastCalls;
    }
    TestTrue(TEXT("differential corpus includes accepted transitions"),SurvivingCases>100);
    TestTrue(TEXT("differential corpus eliminates path work"),SavedDirectionCalls>100);
    AddInfo(FString::Printf(TEXT("Metric endpoint prefilter: 1600 exact comparisons, %d accepted transitions, %d avoided direction samples; not game timing"),SurvivingCases,SavedDirectionCalls));
    return true;
}
#endif
