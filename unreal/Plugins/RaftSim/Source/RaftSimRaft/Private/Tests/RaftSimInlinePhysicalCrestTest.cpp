#include "Misc/AutomationTest.h"
#include "RaftSimIndexedBreakingProfile.h"
#include "RaftSimSurfaceRefinement.h"
#include <cmath>
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimInlinePhysicalCrestTest,"RaftSim.M4.InlinePhysicalCrest",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimInlinePhysicalCrestTest::RunTest(const FString&)
{
    using FSite=URaftSimWaterRuntimeAdapter::FSupportBreakingSite;
    uint64 Queries=0;bool Exact=true;
    const auto Bits=[](float A,float B){return FMemory::Memcmp(&A,&B,sizeof(float))==0;};
    const auto Compare=[&](const TArray<FSite>& Sites,const TArray<FVector2D>& Points)
    {
        const FRaftSimIndexedBreakingProfile Profile(Sites,.7f,.83f);
        for(const auto& P:Points)
        {
            float A=-1,B=-2;
            const float H0=Profile.Sample(P,&A),H1=Profile.SamplePhysicalInline(P,&B);
            Exact &= Bits(H0,H1) && Bits(A,B) && Bits(Profile.Sample(P),Profile.SamplePhysicalInline(P));
            ++Queries;
        }
    };
    TArray<FVector2D> Points;
    for(int32 Y=-40;Y<=40;++Y)for(int32 X=-50;X<=50;++X)Points.Emplace(X*.73,Y*.37);
    // Support limits, float conversion boundaries and direct-index boundaries.
    for(double X:{-24.,-21.,-14.,-8.,-6.,0.,8.,14.,24.,49.})
        for(double Y:{-12.,-10.,0.,10.,12.})for(double D:{-1.,0.,1.})
            Points.Emplace(D==0?X:std::nextafter(X,D>0?INFINITY:-INFINITY),Y);
    Compare({},Points);
    for(int32 Pass=0;Pass<24;++Pass)
    {
        TArray<FSite> Sites;
        for(int32 I=0;I<12;++I)
        {
            FSite S;S.RiverCoordinatesMeters=FVector2D(I*2.1-8.,I%3*3.7-4.);
            S.PhysicalCrestHeightMeters=I%5*.37f;S.PhysicalCrestLengthMeters=1.4f+I*.83f;
            S.SpillingFraction=I%4*.42f-.1f;S.bLocalEnvelopeCap=(I+Pass)%2!=0;
            const double Angle=(I+Pass)*.37,Norm=Pass%3==0?.8:1.;
            S.FlowDirection=Norm*FVector2D(FMath::Cos(Angle),FMath::Sin(Angle));Sites.Add(S);
        }
        FSite Distant;Distant.RiverCoordinatesMeters=FVector2D(10000,10000);
        Distant.PhysicalCrestHeightMeters=1.1f;if(Pass%2)Sites.Add(Distant);
        Compare(Sites,Points);
        // Selection must preserve all topology, not merely sampled heights.
        FRaftSimIndexedBreakingProfile Profile(Sites,.7f,.83f);
        TArray<FVector2D> XY={{-310,-230},{470,-230},{-310,390},{470,390}};
        TArray<int32> Triangles={0,1,2,2,1,3};
        FRaftSimSurfaceRefinement Reference,Candidate;
        TestTrue(TEXT("reference adaptive build"),Reference.BuildAdaptive(XY,Triangles,
            [&](const FVector2D& P){return Profile.Sample(P*.01)*100.f;},3,.5f));
        TestTrue(TEXT("specialized adaptive build"),Candidate.BuildAdaptive(XY,Triangles,
            [&](const FVector2D& P){return Profile.SamplePhysicalInline(P*.01)*100.f;},3,.5f));
        Exact &= Reference.Triangles==Candidate.Triangles && Reference.MidpointParents==Candidate.MidpointParents &&
            Reference.TriangleOrigins==Candidate.TriangleOrigins;
    }
    FSite Legacy;Legacy.Intensity=.8f;Compare({Legacy},Points);
    FSite Invalid;Invalid.PhysicalCrestHeightMeters=.7f;Invalid.FlowDirection=FVector2D(.01,.01);
    Compare({Invalid},Points);
    Invalid.FlowDirection=FVector2D(1,0);Invalid.PhysicalCrestLengthMeters=std::numeric_limits<float>::quiet_NaN();
    Compare({Invalid},{{0,0},{1,2}});
    FSite Zero;Zero.PhysicalCrestHeightMeters=0;Zero.SpillingFraction=1;
    Compare({Zero},Points); // Height-only zero must not suppress requested foam.
    TArray<FSite> OverCapacity;
    for(int32 I=0;I<5000;++I){FSite S;S.PhysicalCrestHeightMeters=.01f;S.PhysicalCrestLengthMeters=7.f;OverCapacity.Add(S);}
    TestFalse(TEXT("capacity fallback remains full evaluator"),FRaftSimIndexedBreakingProfile(OverCapacity,.7f,1.f).IsIndexed());
    Compare(OverCapacity,{{0,0},{2,3},{100,100}});
    Compare({Zero},{{1.e9,1.e9},{std::numeric_limits<double>::quiet_NaN(),0}});
    AddInfo(FString::Printf(TEXT("Inline physical crest bit-exact height/foam queries: %llu; 24 adaptive topologies"),Queries));
    TestTrue(TEXT("specialization preserves reference bits, fallback and adaptive topology"),Exact);
    return !HasAnyErrors();
}
#endif
