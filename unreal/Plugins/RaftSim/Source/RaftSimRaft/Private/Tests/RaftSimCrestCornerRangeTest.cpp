#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"
#include "RaftSimPreparedBreakingHeightRange.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestCornerRangeTest,
    "RaftSim.M4.CrestCornerRange",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestCornerRangeTest::RunTest(const FString&)
{
    TArray<FVector2D> XY;
    TArray<int32> Triangles;
    constexpr int32 N=13;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        XY.Emplace((X-6)*150.,(Y-6)*150.);
        if(X<N-1 && Y<N-1){const int32 A=Y*N+X;Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});}
    }
    FRaftSimSurfaceRefinement Work[2];
    int32 LinearRangeCalls[2]={};
    // A steep LINEAR profile must remain unrefined: spread only skips a range
    // query, it is NOT the interpolation-error criterion.
    for(int32 Kind=0;Kind<2;++Kind)
    {
        Work[Kind].HeightRangeWidthCm=[&,Kind](const FBox2D& B)
        {++LinearRangeCalls[Kind];return float(B.GetSize().X+B.GetSize().Y);};
        const auto Linear=[](const FVector2D& P){return float(P.X+P.Y);};
        TestTrue(TEXT("Linear build"),Kind ? Work[Kind].BuildAdaptive<true>(XY,Triangles,Linear,3,.5f)
                                          : Work[Kind].BuildAdaptive(XY,Triangles,Linear,3,.5f));
        TestTrue(TEXT("Steep linear surface not overrefined"),Work[Kind].Triangles==Triangles);
    }
    TestTrue(TEXT("Unusable range queries avoided"),LinearRangeCalls[0]>0 && LinearRangeCalls[1]==0);
    for(int32 Pass=0;Pass<12;++Pass)
    {
        XY[N*N/2]+=FVector2D(.173,-.241);
        TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites;
        for(int32 I=0;I<4;++I)
        {
            auto& S=Sites.AddDefaulted_GetRef();S.RiverCoordinatesMeters=FVector2D(Pass*.17,I*2.);
            S.FlowDirection=RaftSimWaterFlowFrame::FromAngle(Pass*.23f+I*.1f);
            S.PhysicalCrestHeightMeters=Pass%4 ? .7f : 0.f;S.PhysicalCrestLengthMeters=2.f+I;
            S.bLocalEnvelopeCap=(Pass%2)!=0;
        }
        const FRaftSimPreparedBreakingHeightRange Prepared(Sites);
        const FBox2D Detail(FVector2D(-200),FVector2D(200));
        for(int32 Kind=0;Kind<2;++Kind)
        {
            auto& W=Work[Kind];W.bIndexedEdges=true;
            W.ParallelBatchSize=Pass%3 ? 7 : 128;
            W.HeightRangeWidthCm=Pass==10 ? TFunction<float(const FBox2D&)>() :
                TFunction<float(const FBox2D&)>([&](const FBox2D& B)
                {return Pass==11 ? std::numeric_limits<float>::quiet_NaN() :
                    100.f*Prepared.WidthMeters<true>(FBox2D(B.Min*.01,B.Max*.01));});
            const auto Height=[&](const FVector2D& P)
            {return 100.f*URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P*.01,Sites,.35f,1.f);};
            TestTrue(TEXT("Current physical profile builds"),Kind
                ? W.BuildAdaptive<true>(XY,Triangles,Height,3,.5f,{},nullptr,
                    Pass%2==0,true,Pass%3 ? &Detail : nullptr,50.f,true)
                : W.BuildAdaptive(XY,Triangles,Height,3,.5f,{},nullptr,
                    Pass%2==0,true,Pass%3 ? &Detail : nullptr,50.f,true));
        }
        TArray<FVector2D> A,B;Work[0].Expand(XY,A);Work[1].Expand(XY,B);
        TestTrue(TEXT("Exact topology ownership and coordinates across changing states"),
            Work[0].MidpointParents==Work[1].MidpointParents && Work[0].Triangles==Work[1].Triangles &&
            Work[0].TriangleOrigins==Work[1].TriangleOrigins && A==B);
    }
    return !HasAnyErrors();
}
#endif
