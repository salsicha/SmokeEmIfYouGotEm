#include "Misc/AutomationTest.h"
#include "RaftSimWaterFlowHistory.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterFlowHistoryTest,
    "RaftSim.Water.LocalFlowHistory",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimWaterFlowHistoryTest::RunTest(const FString&)
{
    const FVector2D Target(2.0,-0.85);
    FVector2D Flow=FVector2D::ZeroVector;
    for (int32 I=0; I<60; ++I) Flow=RaftSimWaterFlowHistory::Advance(Flow,Target,1.f/30.f);
    TestTrue(TEXT("Steady current converges instead of restarting from zero"), (Flow-Target).Size()<.001);
    TestTrue(TEXT("Cross-current sign is retained"), Flow.Y<-.849);
    const auto Whole=RaftSimWaterFlowHistory::Advance(FVector2D::ZeroVector,Target,.25f);
    auto Split=FVector2D::ZeroVector;
    for (int32 I=0; I<5; ++I) Split=RaftSimWaterFlowHistory::Advance(Split,Target,.05f);
    TestTrue(TEXT("Constant current smoothing is timestep consistent"), (Whole-Split).Size()<1.e-6);
    TestEqual(TEXT("Zero time preserves history"), RaftSimWaterFlowHistory::Advance(Flow,Target,0.f), Flow);
    TestEqual(TEXT("Existing large-change immediate update retained"),
        RaftSimWaterFlowHistory::Advance(FVector2D::ZeroVector,FVector2D(6,0),.05f),FVector2D(6,0));
    return true;
}
#endif
