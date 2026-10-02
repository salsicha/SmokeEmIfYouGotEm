#include "RaftSimWaterFeatureKinematics.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterFeatureKinematicsTest,
    "RaftSim.P2.SharedFeatureKinematics", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimWaterFeatureKinematicsTest::RunTest(const FString&)
{
    using namespace RaftSimWaterFeatureKinematics;
    TestTrue(TEXT("current Cartesian South Fork map enabled independently of retired data path"),
        IsPlayableSouthFork(TEXT("L_SouthForkAmerican_FullReach")));
    TestTrue(TEXT("PIE South Fork map"),IsPlayableSouthFork(TEXT("UEDPIE_0_L_SouthForkAmerican_FullReach")));
    TestFalse(TEXT("other rivers unchanged"),IsPlayableSouthFork(TEXT("L_Zambezi")));
    TestFalse(TEXT("review map is not ordinary South Fork"),IsPlayableSouthFork(TEXT("SouthForkSurveyPlayable")));
    TestTrue(TEXT("hole surface return overcomes through-flow"),
        2.0 + HoleDelta(4.4,0,1,1.5,2,1).X < 0.0);
    TestTrue(TEXT("hole submerged through-flow"),
        HoleDelta(4.4,0,.35,1.5,2,1).X > 0.0);
    TestEqual(TEXT("surface turnover does not pull through surface"),
        HoleDelta(2.4,0,1,1.5,2,1).Z,0.0);
    TestEqual(TEXT("bed is impermeable"),HoleDelta(2.4,0,0,1.5,2,1).Z,0.0);
    TestTrue(TEXT("upstream half turns down"),HoleDelta(2.4,0,.7,1.5,2,1).Z<0.0);
    TestTrue(TEXT("downstream half turns up"),HoleDelta(6.4,0,.7,1.5,2,1).Z>0.0);
    double MaxFlux=0.0,MaxDiv=0.0;
    for (int32 I=0;I<17;++I)
    {
        const double X=.41+I*.49;
        double Flux=0.0;
        for(int32 K=0;K<1000;++K)
            Flux+=HoleDelta(X,0,(K+.5)/1000.,1.5,2,1).X*1.5/1000.;
        MaxFlux=FMath::Max(MaxFlux,FMath::Abs(Flux));
        for(int32 K=1;K<10;++K)
        {
            const double Z=K*.1,H=1.e-4;
            const double Div=(HoleDelta(X+H,0,Z,1.5,2,1).X-HoleDelta(X-H,0,Z,1.5,2,1).X)/(2*H)
                +(HoleDelta(X,0,Z+H/1.5,1.5,2,1).Z-HoleDelta(X,0,Z-H/1.5,1.5,2,1).Z)/(2*H);
            MaxDiv=FMath::Max(MaxDiv,FMath::Abs(Div));
        }
    }
    TestTrue(TEXT("roller section flux balanced"),MaxFlux<2.e-6);
    TestTrue(TEXT("roller local divergence"),MaxDiv<1.e-7);
    TestTrue(TEXT("eddy return branch overcomes through-flow"),2.+EddyDelta(3.,.5,1.,2.).X<0.);
    TestTrue(TEXT("eddy outside branch downstream"),EddyDelta(3.,1.3,1.,2.).X>0.);
    TestEqual(TEXT("no eddy inside rock"),EddyDelta(0,0,1,2),FVector::ZeroVector);
    TestEqual(TEXT("still water has no invented circulation"),EddyDelta(3,.5,1,0),FVector::ZeroVector);
    MaxDiv=0.0;
    for(int32 I=0;I<31;++I)for(int32 J=0;J<31;++J)
    {
        const double X=.37+I*.177,Y=-1.9+J*.127,H=1.e-4;
        const double Div=(EddyDelta(X+H,Y,1,2).X-EddyDelta(X-H,Y,1,2).X)/(2*H)
            +(EddyDelta(X,Y+H,1,2).Y-EddyDelta(X,Y-H,1,2).Y)/(2*H);
        MaxDiv=FMath::Max(MaxDiv,FMath::Abs(Div));
    }
    TestTrue(TEXT("eddy local divergence"),MaxDiv<1.e-6);
    AddInfo(FString::Printf(TEXT("flat controls: max added flux=%g m3/s/m, max eddy divergence=%g /s; not river conservation proof"),MaxFlux,MaxDiv));
    return true;
}
#endif
