#include "RaftSimTrialRockApproach.h"
#include "Misc/AutomationTest.h"
#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimTrialRockApproachTest,
    "RaftSim.Review.TrialRockApproach",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimTrialRockApproachTest::RunTest(const FString&)
{
    using namespace RaftSimTrialRockApproach;
    TestFalse(TEXT("a large captured terrain tile is not a localized rock owner"),IsLocalizedOwner(false,TEXT("SM_FullReachTerrainTile_0008")));
    TestTrue(TEXT("captured rock envelope is a localized owner"),IsLocalizedOwner(false,TEXT("SM_CapturedRockEnvelope")));
    TestTrue(TEXT("dedicated production rock actor is a localized owner"),IsLocalizedOwner(true,TEXT("OtherRockMesh")));
    const FVector2D Owner(8359.43,-16.27);
    TestTrue(TEXT("current owner is eligible with upstream preparation"),Eligible(FVector2D(8200,0),Owner,8368,8520));
    TestFalse(TEXT("late owner cannot silently become an impact experiment"),Eligible(FVector2D(8330,0),Owner,8368,8520));
    TestTrue(TEXT("unmirrored rightward ferry"),FMath::IsNearlyEqual(HeadingOffset(0,-16.27,FVector(1,0,0),FVector(0,1,0)),-80.));
    TestTrue(TEXT("mirrored geographic rightward ferry"),FMath::IsNearlyEqual(HeadingOffset(0,-16.27,FVector(1,0,0),FVector(0,-1,0)),80.));
    TestTrue(TEXT("mirrored leftward ferry"),FMath::IsNearlyEqual(HeadingOffset(0,10,FVector(1,0,0),FVector(0,-1,0)),-80.));
    TestFalse(TEXT("the observed missed ferry must not turn broadside early"),AlignBroadside(FVector2D(8350,-3),Owner));
    TestTrue(TEXT("aligned approach may begin broadside preparation"),AlignBroadside(FVector2D(8330,-15),Owner));
    TestFalse(TEXT("do not keep holding sideways downstream of the target"),AlignBroadside(FVector2D(8385,-16),Owner));
    return !HasAnyErrors();
}
#endif
