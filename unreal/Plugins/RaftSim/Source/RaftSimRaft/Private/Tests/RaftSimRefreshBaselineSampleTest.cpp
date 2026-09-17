#include "Misc/AutomationTest.h"
#include "RaftSimRefreshBaselineSample.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRefreshBaselineSampleTest,
    "RaftSim.M4.RefreshBaselineSample",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimRefreshBaselineSampleTest::RunTest(const FString&)
{
    const auto Equal=[](const FRaftSimWaterSample& A,const FRaftSimWaterSample& B)
    {
        return A.WorldPosition==B.WorldPosition && A.SurfaceHeightMeters==B.SurfaceHeightMeters &&
            A.BedHeightMeters==B.BedHeightMeters && A.DepthMeters==B.DepthMeters &&
            A.VelocityMetersPerSecond==B.VelocityMetersPerSecond && A.SurfaceNormal==B.SurfaceNormal && A.bWet==B.bWet;
    };
    for (int32 Kind=0;Kind<3;++Kind)
    {
        FRaftSimWaterSample Expected;
        Expected.WorldPosition=FVector(12.,-3.,71.);
        Expected.SurfaceHeightMeters=7.25f; Expected.BedHeightMeters=5.75f;
        Expected.DepthMeters=Kind==0 ? 1.5f : 0.f;
        Expected.VelocityMetersPerSecond=FVector(1.25,-2.75,.125);
        Expected.SurfaceNormal=FVector(.1,-.3,.9).GetSafeNormal();
        Expected.bWet=Kind==0;
        const bool Valid=Kind!=2;
        int32 Queries=0;
        const auto Query=[&](FRaftSimWaterSample& Out) { ++Queries;Out=Expected;return Valid; };
        FRaftSimRefreshBaselineSample Cached;
        for (int32 Use=0;Use<3;++Use)
        {
            FRaftSimWaterSample Out;
            Out.SurfaceHeightMeters=-999.f;
            TestEqual(TEXT("valid, dry and failed verdicts are retained"),Cached.Read(Query,Out),Valid);
            TestTrue(TEXT("all fields match, including values written by a failed query"),Equal(Out,Expected));
            Out.DepthMeters=100.f; // Consumer edits must not alter the cached source.
        }
        TestEqual(TEXT("one baseline read for repeated uses at the same vertex"),Queries,1);
        Expected.SurfaceHeightMeters+=13.f;
        FRaftSimRefreshBaselineSample NextVertexOrRefresh;
        FRaftSimWaterSample Next;
        NextVertexOrRefresh.Read(Query,Next);
        TestEqual(TEXT("new vertex/refresh performs a fresh query"),Queries,2);
        TestTrue(TEXT("no old source crosses the stack lifetime"),Equal(Next,Expected));
    }
    return !HasAnyErrors();
}
#endif
