#include "Misc/AutomationTest.h"
#include "RaftSimIndexedBreakingProfile.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimIndexedBreakingProfileTest,
    "RaftSim.P2.IndexedBreakingProfile", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimIndexedBreakingProfileTest::RunTest(const FString&)
{
    using FSite=URaftSimWaterRuntimeAdapter::FSupportBreakingSite;
    FRandomStream Random(842619);
    int64 Compared=0;
    for (int32 Case=0;Case<9;++Case)
    {
        TArray<FSite> Sites;
        for (int32 I=0;I<24 && Case!=8;++I)
        {
            auto& S=Sites.AddDefaulted_GetRef();
            S.RiverCoordinatesMeters=FVector2D(-5460.+(I%6)*14.,3590.+(I/6)*11.);
            S.FlowDirection=RaftSimWaterFlowFrame::FromAngle(I*.71f)*(Case==3 ? 1.31 : 1.);
            S.PhysicalCrestHeightMeters=I==23 ? 1.7f : .12f+(I%5)*.15f;
            S.PhysicalCrestLengthMeters=1.f+(I%9);
            S.SpillingFraction=(I%4)*.41f;
            S.bLocalEnvelopeCap=Case==0 || (Case!=1 && I%2==0);
            S.Intensity=.7f;
        }
        if(Case==4)Sites[11].PhysicalCrestHeightMeters=-1.f; // Exact legacy fallback.
        if(Case==5)Sites[8].FlowDirection=FVector2D::ZeroVector;
        if(Case==6)Sites[7].RiverCoordinatesMeters.X=1.e9; // Bounded-index fallback.
        if(Case==7)Algo::Reverse(Sites);
        FRaftSimIndexedBreakingProfile Index(Sites,.35f,.7f);
        TestEqual(TEXT("unsupported profiles use original full scan"),Index.IsIndexed(),Case!=4 && Case!=5 && Case!=6);
        const auto Compare=[&](const FVector2D& P)
        {
            float FullFoam=-1.f,IndexedFoam=-1.f;
            const float Full=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,.35f,.7f,&FullFoam);
            const float Fast=Index.Sample(P,&IndexedFoam);
            if(Full!=Fast || FullFoam!=IndexedFoam)
            {
                AddError(FString::Printf(TEXT("Case%d at(%.17g,%.17g): full %.9g/%.9g indexed %.9g/%.9g"),
                    Case,P.X,P.Y,Full,FullFoam,Fast,IndexedFoam));
                return false;
            }
            // Height-only path skips zero-lift emitters but retains owner caps.
            if(Index.Sample(P)!=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,.35f,.7f))
            { AddError(TEXT("Height-only profile differs"));return false; }
            ++Compared; return true;
        };
        for(int32 I=0;I<16000;++I)
            if(!Compare(FVector2D(Random.FRandRange(-5500.f,-5320.f),Random.FRandRange(3520.f,3700.f)))) return false;
        for(const auto& Site:Sites)
        {
            const double Norm=Site.FlowDirection.SizeSquared();
            if(Norm==0 || Site.PhysicalCrestHeightMeters<0)continue;
            const float L=FMath::Clamp(Site.PhysicalCrestLengthMeters,2.f,7.f);
            for(double D:{-3.*L,0.,7.*L}) for(double A:{-12.,0.,12.})
                for(double E:{-.00001,0.,.00001})
                    if(!Compare(Site.RiverCoordinatesMeters+
                        RaftSimWaterFlowFrame::ToField(FVector2D(D+E,A+E),Site.FlowDirection)/Norm))return false;
        }
        // Tile seams, negative coordinates and far-away points cannot lose a lobe.
        for(int32 I=-10;I<10;++I)for(double E:{-.00001,0.,.00001})
            if(!Compare(FVector2D(-5464.+I*8.+E,3592.+I*8.-E)))return false;
        if(!Compare(FVector2D(0,0)))return false;
    }
    AddInfo(FString::Printf(TEXT("Indexed crest height and foam EXACT against full scan at %lld points; changed order, mixed/global/local caps, edges, non-unit directions and fallback"),Compared));
    return !HasAnyErrors();
}
#endif
