#include "Misc/AutomationTest.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimDetailEntrainment.h"
#include "RaftSimWaterFlowFrame.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimAcceptedCrestEntrainmentTest,
    "RaftSim.WaterDetail.AcceptedCrestEntrainment",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimAcceptedCrestEntrainmentTest::RunTest(const FString&)
{
    auto* Water=NewObject<URaftSimWaterRuntimeAdapter>();
    TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites;
    auto& Site=Sites.AddDefaulted_GetRef();
    Site.RiverCoordinatesMeters=FVector2D(-5430,3600);
    Site.FlowDirection=FVector2D(-.6,.8);
    Site.PhysicalCrestLengthMeters=3.f;Site.bLocalEnvelopeCap=true;
    int32 Compared=0;
    for (float Height:{0.f,.7f})for(float Spill:{0.f,.25f,1.f})
    {
        Site.PhysicalCrestHeightMeters=Height;Site.SpillingFraction=Spill;
        Water->ConfigureRaftSupportBreakingSites(Sites,0.f,1.f);
        // Zero subgrid lift still represents a resolved spilling jump.
        const float Peak=Water->SampleAcceptedBreakingSource(Site.RiverCoordinatesMeters);
        TestEqual(TEXT("accepted spill survives zero missing height"),Peak,.85f*Spill);
        for(int32 Y=-30;Y<=30;++Y)for(int32 X=-30;X<=30;++X)
        {
            const FVector2D P=Site.RiverCoordinatesMeters+FVector2D(X*.5,Y*.5);
            float Expected=0;
            URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Sites,0.f,1.f,&Expected);
            TestEqual(TEXT("adapter source exactly matches oriented carrier source"),Water->SampleAcceptedBreakingSource(P),Expected);
            // Frozen pre-optimization expression, independent of the shared
            // envelope helper used by both new runtime query paths.
            const auto R=RaftSimWaterFlowFrame::ToLocal(P-Site.RiverCoordinatesMeters,Site.FlowDirection);
            const float Across=R.Y,Downstream=R.X,Length=3.f;
            float Reference=0;
            if (FMath::Abs(Across)<=12.f && Downstream>=-3.f*Length && Downstream<=7.f*Length)
            {
                const float Along=Downstream-.035f*Across*Across;
                const float Width=Along<0.f ? Length : .42f*Length;
                const float Crest=FMath::Exp(-FMath::Square(Along/Width));
                const float Edge=FMath::SmoothStep(-3.f*Length,-2.f*Length,Downstream)*
                    (1.f-FMath::SmoothStep(6.f*Length,7.f*Length,Downstream));
                const float Lateral=FMath::Exp(-FMath::Square(Across/FMath::Clamp(Length,3.f,5.f)))*
                    (1.f-FMath::SmoothStep(10.f,12.f,FMath::Abs(Across)));
                Reference=.85f*FMath::SmoothStep(.65f,.95f,Crest)*Edge*Lateral*Spill;
            }
            TestEqual(TEXT("source-only optimization preserves prior expression exactly"),Expected,Reference);
            const FVector4f Flow(1,3,-2,.2f);
            const float Merged=FRaftSimDetailEntrainment::MergeBreakingSource(Flow,Expected);
            TestEqual(TEXT("same source is not added twice"),Merged,FMath::Max(.2f,Expected));
            TestEqual(TEXT("dry cells reject crest source"),FRaftSimDetailEntrainment::MergeBreakingSource(FVector4f(0,3,-2,.2f),Expected),0.f);
            ++Compared;
        }
    }
    Water->ConfigureRaftSupportBreakingSites({},0.f,1.f);
    TestEqual(TEXT("removed sites leave no source"),Water->SampleAcceptedBreakingSource(Site.RiverCoordinatesMeters),0.f);
    AddInfo(FString::Printf(TEXT("Compared %d exact shared-source samples, including zero-lift and zero-spill regimes"),Compared));
    return !HasAnyErrors();
}
#endif
