#include "Misc/AutomationTest.h"
#include "RaftSimRefreshScratch.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRefreshScratchTest,"RaftSim.Water.RefreshScratchReset",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimRefreshScratchTest::RunTest(const FString&)
{
    FRaftSimRefreshScratch Scratch;
    for(int32 N : {1200,1200,3,0,1400,1400,1})
    {
        Scratch.Reset(N);
        for(auto* A : {&Scratch.Wet,&Scratch.LiveWet,&Scratch.Sampled,&Scratch.ProbeWanted})
        {
            TestEqual(TEXT("mask shape"),A->Num(),N);
            for(auto& V : *A){TestEqual(TEXT("no stale mask"),int32(V),0);V=255;}
        }
        for(auto* A : {&Scratch.Feather,&Scratch.Heights,&Scratch.Relief,&Scratch.Froude,&Scratch.Foam})
        {
            TestEqual(TEXT("field shape"),A->Num(),N);
            for(auto& V : *A){TestEqual(TEXT("no stale field"),V,0.f);V=37.f;}
        }
        TestEqual(TEXT("sample shape"),Scratch.Samples.Num(),N);
        for(auto& S : Scratch.Samples)
        {
            TestTrue(TEXT("all sample defaults restored, including up normal"),
                S.WorldPosition.IsZero() && S.SurfaceHeightMeters==0.f && S.BedHeightMeters==0.f &&
                S.DepthMeters==0.f && S.VelocityMetersPerSecond.IsZero() &&
                S.SurfaceNormal==FVector::UpVector && !S.bWet);
            S.WorldPosition=FVector(1,2,3); S.SurfaceHeightMeters=1; S.BedHeightMeters=2;
            S.DepthMeters=3; S.VelocityMetersPerSecond=FVector(4,5,6);
            S.SurfaceNormal=FVector::ForwardVector; S.bWet=true;
        }
    }
    return true;
}
#endif
