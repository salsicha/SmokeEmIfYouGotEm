#include "RaftSimWetEdgeCache.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWetEdgeCacheTest,"RaftSim.P2.WetEdgeCache",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimWetEdgeCacheTest::RunTest(const FString&)
{
    FRaftSimWetEdgeCache Cache;
    int64 Compared=0;int32 Hits=0,Misses=0;
    auto Evaluate=[&](int32 Nx,int32 Ny,const TArray<uint8>& Mask)
    {
        const auto Original=RaftSimWaterFlowFrame::WetEdgeStepsReference(Nx,Ny,Mask);
        if(Cache.Matches(Nx,Ny,Mask))++Hits;
        else {++Misses;Cache.Store(Nx,Ny,Mask,RaftSimWaterFlowFrame::WetEdgeStepsSweep(Nx,Ny,Mask));}
        Compared+=Mask.Num();
        return TestTrue(TEXT("every cached distance equals independent queue"),Cache.Get()==Original);
    };
    TArray<uint8> Mask;Mask.Init(1,31*47);
    TestFalse(TEXT("empty cache cannot match a real mask"),Cache.Matches(31,47,Mask));
    for(int32 Frame=0;Frame<120;++Frame)
    {
        const int32 Nx=Frame%8<4 ? 31 : 47,Ny=Frame%8<4 ? 47 : 31;
        if(Frame%3==0)Mask[(Frame*37)%Mask.Num()]^=1;
        if(Frame==40)Mask.Init(0,31*47);
        if(Frame==50)Mask.Init(1,31*47);
        if(Frame==60)Cache.Reset();
        const auto Before=Mask;
        if(!Evaluate(Nx,Ny,Mask) || !Evaluate(Nx,Ny,Mask))return false;
        TestTrue(TEXT("cache does not mutate supplied mask"),Mask==Before);
    }
    Mask.Init(1,31*47);Evaluate(31,47,Mask);
    Mask[Mask.Num()/2]=0;
    TestFalse(TEXT("one-cell mutation invalidates owned copy"),Cache.Matches(31,47,Mask));
    TestFalse(TEXT("same area does not imply same dimensions"),Cache.Matches(47,31,Mask));
    Cache.Reset();TestTrue(TEXT("reset discards distances"),Cache.Get().IsEmpty());
    Mask.Reset();if(!Evaluate(0,0,Mask) || !Evaluate(0,0,Mask))return false;
    TestTrue(TEXT("both hit and changing-input paths exercised"),Hits>100 && Misses>30);
    AddInfo(FString::Printf(TEXT("%lld exact distances, %d hits, %d misses"),Compared,Hits,Misses));
    return !HasAnyErrors();
}
#endif
