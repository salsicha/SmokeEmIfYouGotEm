#include "RaftSimWaterFeatureKinematics.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterFeatureKinematicsTest,
    "RaftSim.P2.SharedFeatureKinematics", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimWaterFeatureKinematicsTest::RunTest(const FString&)
{
    using namespace RaftSimWaterFeatureKinematics;
    for(const TCHAR* Name : {TEXT("L_SouthForkAmerican_FullReach"),TEXT("L_SouthFork_Troublemaker"),
        TEXT("L_Hance"),TEXT("L_LavaCanyon"),TEXT("L_Terminator"),TEXT("L_UpperHuacas"),
        TEXT("L_Zambezi"),TEXT("L_ZambeziUpperGorge")})
    {
        TestTrue(TEXT("playable river shares feature current"),IsPlayableRiver(Name));
        TestTrue(TEXT("PIE production river"),IsPlayableRiver(FString(TEXT("UEDPIE_12_"))+Name));
        TestTrue(TEXT("package path production river"),IsPlayableRiver(FString(TEXT("/Game/RaftSim/Maps/"))+Name));
        TestFalse(TEXT("suffix cannot enable review map"),IsPlayableRiver(FString(TEXT("Review_"))+Name));
    }
    for(const TCHAR* Name : {TEXT("L_RaftSimBoot"),TEXT("L_RaftSimTestTank"),TEXT("SouthForkSurveyPlayable"),
        TEXT("UEDPIE_bad_L_Hance"),TEXT("UEDPIE__L_Hance"),TEXT("L_HanceReview")})
        TestFalse(TEXT("nonproduction map remains unchanged"),IsPlayableRiver(Name));
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
    for (const double Radius : {.75,1.,2.,4.,8.})
    {
        TestTrue(TEXT("centreline return has no downstream seam"),
            2.+EddyDelta(4.*Radius,0.,Radius,2.).X<0.);
        TestTrue(TEXT("slightly off-centre boat enters return current"),
            2.+EddyDelta(4.*Radius,.4*Radius,Radius,2.).X<0.);
        TestTrue(TEXT("upstream head turns left outward"),
            EddyDelta(1.75*Radius,.6*Radius,Radius,2.).Y>0.);
        TestTrue(TEXT("upstream head turns right outward"),
            EddyDelta(1.75*Radius,-.6*Radius,Radius,2.).Y<0.);
        TestTrue(TEXT("outer branch rejoins downstream current"),
            EddyDelta(2.25*Radius,1.25*Radius,Radius,2.).X>0.);
        TestEqual(TEXT("symmetry axis has no invented side kick"),
            EddyDelta(4.*Radius,0.,Radius,2.).Y,0.);
        TestEqual(TEXT("wake compact downstream support"),
            EddyDelta(6.6*Radius,0.,Radius,2.),FVector::ZeroVector);
    }
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
    double MaxObliqueDiv=0.,MaxCurlError=0.;
    for(double Across : {-1.5,.8,1.5})
    {
        TestEqual(TEXT("incident cross-current cancelled at wake core"),
            Across+EddyDelta(3.25,0,1,2,Across).Y,0.);
        for (double ReturnX:{1.25,1.5,1.75,2.,2.25,2.5,3.,3.5,4.,4.5})
            TestEqual(TEXT("inlet-to-head axis cancels incident cross drift"),
                Across+EddyDelta(ReturnX,0,1,2,Across).Y,0.);
        TestEqual(TEXT("oblique correction does not escape compact wake"),
            EddyDelta(6.6,0,1,2,Across),FVector::ZeroVector);
        for(int32 I=0;I<31;++I)for(int32 J=0;J<31;++J)
        {
            const double X=.37+I*.177,Y=-1.9+J*.127,H=1.e-4;
            const FVector U=EddyDelta(X,Y,1,2,Across);
            const double Div=(EddyDelta(X+H,Y,1,2,Across).X-EddyDelta(X-H,Y,1,2,Across).X)/(2*H)
                +(EddyDelta(X,Y+H,1,2,Across).Y-EddyDelta(X,Y-H,1,2,Across).Y)/(2*H);
            MaxObliqueDiv=FMath::Max(MaxObliqueDiv,FMath::Abs(Div));
            const FVector Curl((EddyWakePsi(X,Y+H,1,2,Across)-EddyWakePsi(X,Y-H,1,2,Across))/(2*H),
                -(EddyWakePsi(X+H,Y,1,2,Across)-EddyWakePsi(X-H,Y,1,2,Across))/(2*H),0.);
            MaxCurlError=FMath::Max(MaxCurlError,(U-Curl).Size());
            const FVector Mirror=EddyDelta(X,-Y,1,2,-Across);
            TestTrue(TEXT("oblique wake mirror remains symmetric"),
                FMath::Abs(U.X-Mirror.X)<1.e-10 && FMath::Abs(U.Y+Mirror.Y)<1.e-10);
        }
    }
    TestTrue(TEXT("oblique correction retains flat-control divergence"),MaxObliqueDiv<1.e-6);
    TestTrue(TEXT("actual evaluator is curl of oblique compact streamfunction"),MaxCurlError<1.e-6);
    AddInfo(FString::Printf(TEXT("oblique flat controls: divergence=%g /s curl_error=%g m/s; not clipped/curved river conservation"),MaxObliqueDiv,MaxCurlError));
    AddInfo(FString::Printf(TEXT("flat controls: max added flux=%g m3/s/m, max eddy divergence=%g /s; not river conservation proof"),MaxFlux,MaxDiv));
    return true;
}
#endif
