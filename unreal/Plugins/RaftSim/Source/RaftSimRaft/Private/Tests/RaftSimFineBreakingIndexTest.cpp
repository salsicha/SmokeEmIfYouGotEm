#include "Misc/AutomationTest.h"
#include "RaftSimIndexedBreakingProfile.h"
#include <cmath>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFineBreakingIndexTest,"RaftSim.M4.FineBreakingIndex",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimFineBreakingIndexTest::RunTest(const FString&)
{
    using FSite=URaftSimWaterRuntimeAdapter::FSupportBreakingSite;
    uint64 Queries=0;bool Exact=true;
    const auto Compare=[&](const TArray<FSite>& Sites,const TArray<FVector2D>& Points)
    {
        FRaftSimIndexedBreakingProfile Reference(Sites,.7f,1.f);
        FRaftSimFineIndexedBreakingProfile Fine(Sites,.7f,1.f);
        for(const auto& P:Points)
        {
            float Foam[3]={};
            const float A=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,.7f,1.f,&Foam[0]);
            const float B=Reference.Sample(P,&Foam[1]),C=Fine.Sample(P,&Foam[2]);
            Exact &= A==B && A==C && Foam[0]==Foam[1] && Foam[0]==Foam[2];++Queries;
        }
    };
    TArray<FVector2D> Points;
    for(int32 Y=-60;Y<=60;++Y)for(int32 X=-60;X<=60;++X)Points.Emplace(X*.71,Y*.63);
    for(double X:{-16.,-8.,-2.,0.,2.,8.,16.})for(double Y:{-12.,-2.,0.,2.,12.})
        for(double D:{-1.,0.,1.})Points.Emplace(D==0?X:std::nextafter(X,D>0?INFINITY:-INFINITY),Y);
    Compare({},Points);
    for(int32 Pass=0;Pass<12;++Pass)
    {
        TArray<FSite> Sites;
        for(int32 I=0;I<9;++I)
        {
            FSite S;S.RiverCoordinatesMeters=FVector2D(I*2.1-8.,I%3*3.7-4.);
            S.PhysicalCrestHeightMeters=I%4*.37f;S.PhysicalCrestLengthMeters=1.4f+I*.83f;
            S.SpillingFraction=I%3*.42f;S.bLocalEnvelopeCap=(I+Pass)%2!=0;
            const double Angle=(I+Pass)*.37,Norm=Pass%3==0?.8:1.;
            S.FlowDirection=Norm*FVector2D(FMath::Cos(Angle),FMath::Sin(Angle));Sites.Add(S);
        }
        Compare(Sites,Points);
        // A distant global owner must still cap local overlapping profiles.
        FSite Distant;Distant.RiverCoordinatesMeters=FVector2D(10000,10000);
        Distant.PhysicalCrestHeightMeters=1.1f;Sites.Add(Distant);Compare(Sites,Points);
    }
    FSite Legacy;Legacy.Intensity=.8f;Compare({Legacy},Points);
    FSite Invalid;Invalid.PhysicalCrestHeightMeters=.7f;Invalid.FlowDirection=FVector2D(.01,.01);
    Compare({Invalid},Points);
    TArray<FSite> OverCapacity;
    for(int32 I=0;I<300;++I){FSite S;S.PhysicalCrestHeightMeters=.01f;S.PhysicalCrestLengthMeters=7.f;OverCapacity.Add(S);}
    FRaftSimFineIndexedBreakingProfile Limited(OverCapacity,.7f,1.f);
    TestFalse(TEXT("bounded index falls back rather than dropping sites"),Limited.IsIndexed());
    Compare(OverCapacity,{FVector2D(0,0),FVector2D(2,3),FVector2D(100,100)});
    AddInfo(FString::Printf(TEXT("Fine index exact original height/foam queries: %llu"),Queries));
    TestTrue(TEXT("fine/coarse/full scan exactly preserve height, foam and global/local caps"),Exact);
    return !HasAnyErrors();
}
#endif
