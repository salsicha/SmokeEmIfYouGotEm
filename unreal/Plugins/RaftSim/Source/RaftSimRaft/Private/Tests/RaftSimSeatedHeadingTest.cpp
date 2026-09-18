#include "RaftSimSeatedHeading.h"
#include "Misc/AutomationTest.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSeatedHeadingTest, "RaftSim.Guide.SeatedHeading",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSeatedHeadingTest::RunTest(const FString&)
{
    FRaftSimSeatedHeading Heading;
    TestEqual(TEXT("first attachment does not replace authored look"), Heading.Advance(170., true), 0.);
    TestEqual(TEXT("positive wrap is a short turn"), Heading.Advance(-170., true), 20.);
    TestEqual(TEXT("negative wrap is a short turn"), Heading.Advance(175., true), -15.);
    TestEqual(TEXT("same seat frame is idempotent"), Heading.Advance(175., true), 0.);
    double Seat = 175., View = 202., ExpectedOffset = 27.;
    for (int32 I = 0; I < 400; ++I)
    {
        Seat = FMath::UnwindDegrees(Seat + (I % 3 == 0 ? -4. : 2.));
        const double Mouse = I % 7 == 0 ? .25 : -.125;
        ExpectedOffset += Mouse;
        View = FMath::UnwindDegrees(View + Mouse + Heading.Advance(Seat, true));
        TestTrue(TEXT("user look offset survives turns and wrap"),
            FMath::Abs(FMath::FindDeltaAngleDegrees(Seat, View) - ExpectedOffset) < 1.e-10);
    }
    TestEqual(TEXT("swimming/chase/cinematic gate carries no yaw"), Heading.Advance(90., false), 0.);
    TestEqual(TEXT("return to seat does not replay an unseen turn"), Heading.Advance(-30., true), 0.);
    TestEqual(TEXT("new seated turn resumes"), Heading.Advance(-25., true), 5.);
    TestEqual(TEXT("invalid pose resets the observation"), Heading.Advance(std::numeric_limits<double>::quiet_NaN(), true), 0.);
    TestEqual(TEXT("finite recovery does not replay invalid state"), Heading.Advance(60., true), 0.);
    return true;
}
#endif
