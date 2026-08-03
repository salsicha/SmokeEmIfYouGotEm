#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimColoradoHanceWaterCaptureTest,
    "RaftSim.M9.FColoradoHanceWaterCapture",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimColoradoHanceWaterCaptureTest::RunTest(const FString& Parameters)
{
    FString Summary;
    const bool bCaptured =
        RaftSimEditorEnvironment::CaptureColoradoHanceWaterReview(Summary);
    AddInfo(Summary);
    TestTrue(
        TEXT("Three saved-map Colorado Hance water review cameras capture"),
        bCaptured);
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
