#include "Misc/AutomationTest.h"
#include "RaftSimSwimmerSurface.h"
#include <limits>
#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSwimmerSurfaceTest,"RaftSim.Crew.SwimmerSurfaceDatum",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSwimmerSurfaceTest::RunTest(const FString&)
{
    FVector P(12,-37,999);
    FRaftSimWaterSample S;
    S.bWet=true;
    for (float Height : {23.f,22.8f,-4.f,25.f})
    {
        S.SurfaceHeightMeters=Height;
        TestTrue(TEXT("wet finite sample accepted"),RaftSimAttachSwimmerToSurface(P,S));
        TestTrue(TEXT("surface datum changes only Z"),P==FVector(12,-37,Height));
    }
    const FVector Before=P;
    S.bWet=false;
    TestFalse(TEXT("dry sample cannot snap swimmer"),RaftSimAttachSwimmerToSurface(P,S));
    TestTrue(TEXT("dry preserves position"),P==Before);
    S.bWet=true;
    for(float Bad : {std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::infinity()})
    {
        S.SurfaceHeightMeters=Bad;
        TestFalse(TEXT("non-finite surface rejected"),RaftSimAttachSwimmerToSurface(P,S));
        TestTrue(TEXT("invalid preserves position"),P==Before);
    }
    return true;
}
#endif
