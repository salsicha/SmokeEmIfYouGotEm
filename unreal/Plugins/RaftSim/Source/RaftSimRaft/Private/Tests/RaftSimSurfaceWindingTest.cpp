#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceWinding.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSurfaceWindingTest,"RaftSim.P2.SurfaceWinding",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSurfaceWindingTest::RunTest(const FString&)
{
    TArray<FVector> Positions={FVector(0,0,5),FVector(100,0,7),FVector(0,100,9)};
    const TArray<int32> Clockwise={0,2,1},Reverse={0,1,2};
    const TArray<int32> Degenerate={0,0,0,0,2,1},Invalid={0,2,99},Empty;
    TestFalse(TEXT("actual clockwise carrier is retained"),
        RaftSimSurfaceWinding::NeedsClockwiseFlip(Positions,Clockwise));
    TestTrue(TEXT("actual reverse-facing carrier needs one swap"),
        RaftSimSurfaceWinding::NeedsClockwiseFlip(Positions,Reverse));
    Positions[2].Y=-100.;
    TestTrue(TEXT("reflected actual positions reverse source winding"),
        RaftSimSurfaceWinding::NeedsClockwiseFlip(Positions,Clockwise));
    TestFalse(TEXT("already corrected reflected indices must not flip twice"),
        RaftSimSurfaceWinding::NeedsClockwiseFlip(Positions,Reverse));
    TestTrue(TEXT("skip a degenerate first triangle"),
        RaftSimSurfaceWinding::NeedsClockwiseFlip(Positions,Degenerate));
    TestFalse(TEXT("unknown invalid topology cannot request a swap"),
        RaftSimSurfaceWinding::NeedsClockwiseFlip(Positions,Invalid));
    TestFalse(TEXT("empty topology cannot request a swap"),
        RaftSimSurfaceWinding::NeedsClockwiseFlip(Positions,Empty));
    return true;
}
#endif
