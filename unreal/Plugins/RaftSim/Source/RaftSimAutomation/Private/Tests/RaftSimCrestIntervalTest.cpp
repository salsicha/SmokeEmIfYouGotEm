#include "Misc/AutomationTest.h"
#include "RaftSimPreparedBreakingHeightRange.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestIntervalBoundTest,
    "RaftSim.P2.CrestIntervalBound",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestIntervalBoundTest::RunTest(const FString&)
{
    using FSite=URaftSimWaterRuntimeAdapter::FSupportBreakingSite;
    FRandomStream Random(193371);int64 Samples=0;int32 Sharper=0;
    for(int32 Case=0;Case<8;++Case)
    {
        const FVector2D Origin=Case==7 ? FVector2D(1.e8,-1.e8) : FVector2D(-5440.,-3600.);
        TArray<FSite> Sites;
        for(int32 I=0;I<8;++I)
        {
            auto& S=Sites.AddDefaulted_GetRef();S.RiverCoordinatesMeters=Origin+FVector2D(I*2.,I%3*3.);
            S.FlowDirection=RaftSimWaterFlowFrame::FromAngle(I*.63f)*(Case==3 ? 1.31 : 1.);
            S.PhysicalCrestHeightMeters=I%4 ? .2f+I*.23f : 0.f;S.PhysicalCrestLengthMeters=1.f+I;
            S.bLocalEnvelopeCap=Case%2==0 || I%2==0;
        }
        const FRaftSimPreparedBreakingHeightRange Prepared(Sites);
        const auto Check=[&](const FBox2D& Box)
        {
            const float Width=Prepared.WidthMeters<true>(Box),Original=Prepared.WidthMeters(Box);
            float Low=MAX_flt,High=-MAX_flt;
            for(int32 Y=0;Y<=8;++Y)for(int32 X=0;X<=8;++X)
            {
                const FVector2D P=Box.Min+Box.GetSize()*FVector2D(X*.125,Y*.125);
                const float H=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,.35f,.7f);
                Low=FMath::Min(Low,H);High=FMath::Max(High,H);++Samples;
            }
            if(High-Low>Width || Width<0.f || Width>Original)
            {AddError(FString::Printf(TEXT("Interval violation case=%d low=%.9g high=%.9g width=%.9g original=%.9g"),Case,Low,High,Width,Original));return false;}
            if(High>.05f && Width<Original*.5f)++Sharper;
            return true;
        };
        for(int32 I=0;I<100;++I)
        {
            const FVector2D C=Origin+FVector2D(Random.FRandRange(-35.f,60.f),Random.FRandRange(-35.f,45.f));
            const double Radius=I%5 ? .125 : 4.;
            if(!Check(FBox2D(C-FVector2D(Radius),C+FVector2D(Radius))))return false;
        }
        for(const auto& S:Sites)
        {
            const float L=FMath::Clamp(S.PhysicalCrestLengthMeters,2.f,7.f);
            for(double D:{-3.*L,-2.*L,0.,.95*L,2.8*L,5.1*L,6.*L,7.*L})for(double A:{-12.,-10.,0.,10.,12.})
            {
                const FVector2D P=S.RiverCoordinatesMeters+RaftSimWaterFlowFrame::ToField(FVector2D(D,A),S.FlowDirection)/S.FlowDirection.SizeSquared();
                for(double R:{.00001,.125})if(!Check(FBox2D(P-FVector2D(R),P+FVector2D(R))))return false;
            }
        }
        Sites[0].PhysicalCrestHeightMeters=-1.f;
        TestEqual(TEXT("unsupported profile disables interval shortcut"),FRaftSimPreparedBreakingHeightRange(Sites).WidthMeters<true>(FBox2D(Origin,Origin+FVector2D(1.))),MAX_flt);
    }
    TestTrue(TEXT("nonzero local profiles receive a sharper range"),Sharper>0);
    AddInfo(FString::Printf(TEXT("Interval encloses %lld samples, sharper nonzero boxes %d"),Samples,Sharper));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestIntervalSelectionTest,
    "RaftSim.M4.CrestIntervalSelection",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestIntervalSelectionTest::RunTest(const FString&)
{
    constexpr int32 N=19;TArray<FVector2D> XY;TArray<int32> Triangles;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        XY.Emplace((X-N/2)*300.,(Y-N/2)*300.);
        if(X<N-1 && Y<N-1){const int32 A=Y*N+X;Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});}
    }
    FRaftSimSurfaceRefinement Work[2];int64 Calls[2]={};
    for(int32 Frame=0;Frame<8;++Frame)
    {
        if(Frame>2)XY[N*N/2]+=FVector2D(.173,-.241);
        TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites;
        for(int32 I=0;I<3;++I)
        {
            auto& S=Sites.AddDefaulted_GetRef();S.RiverCoordinatesMeters=FVector2D(Frame*.17,I*4.);
            S.FlowDirection=RaftSimWaterFlowFrame::FromAngle(Frame*.23f+I*.1f);
            S.PhysicalCrestHeightMeters=Frame%4 ? .7f : 0.f;S.PhysicalCrestLengthMeters=2.f+I;
            S.bLocalEnvelopeCap=(Frame%2)!=0;
        }
        const FRaftSimPreparedBreakingHeightRange Prepared(Sites);
        Work[0].HeightRangeWidthCm=[&](const FBox2D& B){return 100.f*Prepared.WidthMeters(FBox2D(B.Min*.01,B.Max*.01));};
        Work[1].HeightRangeWidthCm=[&](const FBox2D& B){return 100.f*Prepared.WidthMeters<true>(FBox2D(B.Min*.01,B.Max*.01));};
        const FBox2D Detail(FVector2D(-200),FVector2D(200));const FBox2D* Window=Frame%2 ? &Detail : nullptr;
        TArray<FVector2D> Points[2];
        for(int32 I=0;I<2;++I)
        {
            Work[I].bIndexedEdges=true;
            const auto Height=[&](const FVector2D& P)
            {++Calls[I];return 100.f*URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P*.01,Sites,.35f,1.f);};
            if(!Work[I].BuildAdaptive(XY,Triangles,Height,3,.5f,{},nullptr,false,false,Window,25.f))return false;
            Work[I].Expand(XY,Points[I]);
        }
        TestTrue(TEXT("interval retains ordered parents, indices, ownership and coordinates across history"),
            Work[0].MidpointParents==Work[1].MidpointParents && Work[0].Triangles==Work[1].Triangles &&
            Work[0].TriangleOrigins==Work[1].TriangleOrigins && Points[0]==Points[1]);
    }
    TestTrue(TEXT("same topology uses fewer height samples"),Calls[1]<Calls[0]);
    AddInfo(FString::Printf(TEXT("Height calls: original %lld interval %lld"),Calls[0],Calls[1]));
    return !HasAnyErrors();
}
#endif
