#include "RaftSimLiveWaterWindow.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimPinballCropBoundaryTest,
    "RaftSim.M3.PinballCropBoundary",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimPinballCropBoundaryTest::RunTest(const FString&)
{
    const FString Fields=URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
        TEXT("physics/data/real_world/pacuare_river_costa_rica/scenario_huacas_evidence_2017/cooked_flow_fields"));
    const FString Band=TEXT("rainfed_runnable_45cms");FString Error;
    auto Seed=FRaftSimLiveWaterWindow::CreateFromCookedFields(Fields,Band,FVector2D(1164,0),FVector2D(2328,96),.041f,Error,false);
    auto Live=FRaftSimLiveWaterWindow::CreateFromCookedFields(Fields,Band,FVector2D(1950,0),FVector2D(480,96),.041f,Error,false);
    if(!TestTrue(*Error,Seed.IsValid() && Live.IsValid()))return false;
    // The failed native hands-off run crossed this crown at 2.65 m depth;
    // the offline cook was about 0.19 m. Exercise the actual crop, a handoff,
    // and continued production solver evolution, not an offline substitute.
    const FVector2D Probes[]={FVector2D(2052,-26),FVector2D(2052,-30),FVector2D(2048,-30),FVector2D(2056,-30),
        FVector2D(2050,-18),FVector2D(2050,-16),FVector2D(2050,-14),FVector2D(2050,-12)};
    double MaximumStageChange=0.,MaximumCrownDepth=0.;
    for(int32 Step=0;Step<2400;++Step)
    {
        Live->Step(.05f);
        if(Step==1599)
        {
            auto Next=FRaftSimLiveWaterWindow::CreateFromCookedFields(Fields,Band,FVector2D(2030,0),FVector2D(480,96),.041f,Error,false);
            if(!TestTrue(*Error,Next.IsValid()))return false;
            Next->TransferOverlapStateFrom(*Live);Live=MoveTemp(Next);
        }
        if(Step%20)continue;
        if(!TestFalse(TEXT("crop stays finite"),Live->HasNonFiniteState()))return false;
        for(const auto P:Probes)
        {
            const auto A=Live->Sample(P),S=Seed->Sample(P);
            if(!TestTrue(TEXT("probes remain in real source coverage"),A.bValid && S.bValid))return false;
            MaximumStageChange=FMath::Max(MaximumStageChange,FMath::Abs(double(A.SurfaceHeightM)-S.SurfaceHeightM));
            MaximumCrownDepth=FMath::Max(MaximumCrownDepth,double(A.DepthM));
        }
    }
    AddInfo(FString::Printf(TEXT("Pinball 120 s crop and handoff: max stage change %.6f m, crown depth %.6f m"),MaximumStageChange,MaximumCrownDepth));
    TestTrue(TEXT("moving crop does not manufacture a flood over the calibrated bar"),MaximumStageChange<.1);
    TestTrue(TEXT("bar remains shallow in the live solver"),MaximumCrownDepth<.35);
    return !HasAnyErrors();
}
#endif
