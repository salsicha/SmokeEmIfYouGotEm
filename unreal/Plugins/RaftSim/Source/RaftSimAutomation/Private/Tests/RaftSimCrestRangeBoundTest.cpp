#include "Misc/AutomationTest.h"
#include "RaftSimBreakingHeightRange.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestRangeBoundTest,
    "RaftSim.P2.CrestRangeBound",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestRangeBoundTest::RunTest(const FString&)
{
    using FSite=URaftSimWaterRuntimeAdapter::FSupportBreakingSite;
    FRandomStream Random(77318);
    int64 Compared=0;
    for(int32 Case=0;Case<8;++Case)
    {
        const FVector2D Origin=Case==7 ? FVector2D(1.e8,-1.e8) : FVector2D(-5440.,-3600.);
        TArray<FSite> Sites;
        for(int32 I=0;I<8;++I)
        {
            auto& S=Sites.AddDefaulted_GetRef();
            S.RiverCoordinatesMeters=Origin+FVector2D(I*3.,I%3*4.);
            S.FlowDirection=RaftSimWaterFlowFrame::FromAngle(I*.63f)*(Case==3 ? 1.31 : 1.);
            S.PhysicalCrestHeightMeters=I%4 ? .2f+I*.23f : 0.f;
            S.PhysicalCrestLengthMeters=1.f+I;
            S.bLocalEnvelopeCap=Case%2==0 || I%2==0;
        }
        for(int32 Box=0;Box<80;++Box)
        {
            const FVector2D C=Origin+FVector2D(Random.FRandRange(-35.f,60.f),Random.FRandRange(-35.f,45.f));
            const double Radius=Box%5 ? .125 : 4.;
            const FBox2D Bounds(C-FVector2D(Radius),C+FVector2D(Radius));
            const float Width=RaftSimBreakingHeightRange::WidthMeters(Sites,Bounds);
            float Low=0.f,High=0.f;
            for(int32 Y=0;Y<=10;++Y)for(int32 X=0;X<=10;++X)
            {
                const FVector2D P=Bounds.Min+Bounds.GetSize()*FVector2D(X*.1,Y*.1);
                const float V=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,.35f,.7f);
                Low=FMath::Min(Low,V);High=FMath::Max(High,V);++Compared;
            }
            if(High-Low>Width)
            {AddError(FString::Printf(TEXT("Range violation case=%d box=%d width=%.9g actual=%.9g"),Case,Box,Width,High-Low));return false;}
        }
        // Explicit support boundaries and curved crest/toe extrema, not just
        // random boxes which rarely land on piecewise branch transitions.
        for(const auto& S:Sites)
        {
            const float L=FMath::Clamp(S.PhysicalCrestLengthMeters,2.f,7.f);
            for(double D:{-3.*L,-2.*L,0.,.95*L,2.8*L,5.1*L,6.*L,7.*L})
            for(double A:{-12.,-10.,0.,10.,12.})
            {
                const FVector2D P=S.RiverCoordinatesMeters+RaftSimWaterFlowFrame::ToField(FVector2D(D,A),S.FlowDirection)/S.FlowDirection.SizeSquared();
                const FBox2D B(P-FVector2D(.00001),P+FVector2D(.00001));
                const float W=RaftSimBreakingHeightRange::WidthMeters(Sites,B);
                const float H=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,.35f,.7f);
                TestTrue(TEXT("boundary range includes zero and actual profile"),FMath::Abs(H)<=W);++Compared;
            }
        }
        Sites[0].PhysicalCrestHeightMeters=-1.f;
        TestEqual(TEXT("legacy profile disables bound"),RaftSimBreakingHeightRange::WidthMeters(Sites,FBox2D(Origin,Origin+FVector2D(1.))),MAX_flt);
    }
    AddInfo(FString::Printf(TEXT("Conservative physical crest range contains %lld actual samples across rotating/mixed-cap/large-coordinate profiles and support boundaries"),Compared));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestRangeSelectionTest,
    "RaftSim.M4.CrestRangeSelection",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestRangeSelectionTest::RunTest(const FString&)
{
    constexpr int32 N=19;
    TArray<FVector2D> XY;TArray<int32> Triangles;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        XY.Emplace((X-N/2)*300.,(Y-N/2)*300.);
        if(X<N-1 && Y<N-1){const int32 A=Y*N+X;Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});}
    }
    FRaftSimSurfaceRefinement Reference,Candidate;
    int64 OriginalCalls=0,CandidateCalls=0,TotalOriginalCalls=0,TotalCandidateCalls=0;
    for(int32 Frame=0;Frame<8;++Frame)
    {
        if(Frame>2)XY[N*N/2]+=FVector2D(.173,-.241);
        TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites;
        for(int32 I=0;I<2;++I)
        {
            auto& S=Sites.AddDefaulted_GetRef();S.RiverCoordinatesMeters=FVector2D(Frame*.17,I*4.);
            S.FlowDirection=RaftSimWaterFlowFrame::FromAngle(Frame*.23f);
            S.PhysicalCrestHeightMeters=Frame%4 ? .7f : 0.f;S.PhysicalCrestLengthMeters=2.f+I;
            S.bLocalEnvelopeCap=(Frame%2)!=0;
        }
        const auto Height=[&](const FVector2D& P)
        {return 100.f*URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P*.01,Sites,.35f,1.f);};
        Candidate.HeightRangeWidthCm=[&](const FBox2D& B)
        {return 100.f*RaftSimBreakingHeightRange::WidthMeters(Sites,FBox2D(B.Min*.01,B.Max*.01));};
        const FBox2D Detail(FVector2D(-200),FVector2D(200));
        const FBox2D* Window=Frame%2 ? &Detail : nullptr;
        const auto H0=[&](const FVector2D& P){++OriginalCalls;return Height(P);};
        const auto H1=[&](const FVector2D& P){++CandidateCalls;return Height(P);};
        if(!Reference.BuildAdaptive(XY,Triangles,H0,3,.5f,{},nullptr,false,false,Window,25.f) ||
            !Candidate.BuildAdaptive(XY,Triangles,H1,3,.5f,{},nullptr,false,false,Window,25.f))return false;
        TArray<FVector2D> A,B;Reference.Expand(XY,A);Candidate.Expand(XY,B);
        TestTrue(TEXT("range early-out preserves every ordered parent, triangle, cell owner and coordinate"),
            Reference.MidpointParents==Candidate.MidpointParents && Reference.Triangles==Candidate.Triangles &&
            Reference.TriangleOrigins==Candidate.TriangleOrigins && A==B);
        TotalOriginalCalls+=OriginalCalls;TotalCandidateCalls+=CandidateCalls;
        // A failed bound must fall back to the original selection, never cull.
        Candidate.HeightRangeWidthCm=[](const FBox2D&){return -1.f;};
        if(!Candidate.BuildAdaptive(XY,Triangles,H1,3,.5f,{},nullptr,false,false,Window,25.f))return false;
        TestTrue(TEXT("invalid bound falls back"),Reference.MidpointParents==Candidate.MidpointParents && Reference.Triangles==Candidate.Triangles);
        OriginalCalls=0;CandidateCalls=0;
    }
    TestTrue(TEXT("same physical profiles require fewer exact evaluations"),TotalCandidateCalls<TotalOriginalCalls);
    AddInfo(FString::Printf(TEXT("Exact topology: reference %lld height calls, bounded %lld"),TotalOriginalCalls,TotalCandidateCalls));
    // Isolate proof of a useful shortcut from the topology checks above.
    int32 Calls=0;
    Candidate.HeightRangeWidthCm=[](const FBox2D&){return 0.f;};
    TestTrue(TEXT("zero-range profile builds"),Candidate.BuildAdaptive(XY,Triangles,[&](const FVector2D&){++Calls;return 0.f;},3,.5f));
    TestEqual(TEXT("certified zero range needs no profile samples"),Calls,0);
    return !HasAnyErrors();
}
#endif
