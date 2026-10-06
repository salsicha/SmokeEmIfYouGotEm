#include "../RaftSimTransitionLayout.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimTransitionLayoutTest,
    "RaftSim.M7.TransitionSafeRegion",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
    EAutomationTestFlags::ProductFilter)

bool FRaftSimTransitionLayoutTest::RunTest(const FString& Parameters)
{
    for (const FVector2D Viewport : {FVector2D(1920,1080), FVector2D(1280,720),
        FVector2D(1080,1920), FVector2D(800,600), FVector2D(2560,1080)})
    for (const float Scale : {0.75f,1.0f,1.25f,1.5f})
    {
        const auto Region = RaftSimTransitionLayout::Resolve(Viewport, Scale);
        const FVector2D BottomLeft = FVector2D(0,Viewport.Y) + Region.Position;
        const FVector2D Centre = Viewport * 0.5;
        const FVector2D TopLeft = Centre +
            (BottomLeft - FVector2D(0,Region.Size.Y) - Centre) * Scale;
        const FVector2D BottomRight = Centre +
            (BottomLeft + FVector2D(Region.Size.X,0) - Centre) * Scale;
        TestTrue(TEXT("positive bounded text region"), Region.Size.X > 0 && Region.Size.Y > 0);
        TestTrue(TEXT("full fitted region remains inside viewport"),
            TopLeft.X >= 0 && TopLeft.Y >= 0 &&
            BottomRight.X <= Viewport.X && BottomRight.Y <= Viewport.Y);
        TestTrue(TEXT("bottom safe margin preserved under UI scale"),
            FMath::IsNearlyEqual(BottomRight.Y, Viewport.Y-FMath::Min(40.0,Viewport.Y*0.05), 0.001));
        TestTrue(TEXT("briefing occupies at most lower forty percent"),
            BottomRight.Y-TopLeft.Y <= Viewport.Y*0.4+0.001);
    }
    return true;
}
#endif
