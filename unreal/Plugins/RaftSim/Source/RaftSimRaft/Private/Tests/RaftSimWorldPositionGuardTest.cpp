#include "Misc/AutomationTest.h"
#include "../RaftSimWorldPositionGuard.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWorldPositionGuardTest,
    "RaftSim.Continuous.WorldPositionGuard",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimWorldPositionGuardTest::RunTest(const FString&)
{
    const FVector Last(-10378.749,5658.607,61677.347);
    const FVector Moving(1.4,-.8,.03);
    // Actual continuous Colorado launch, both sides of the old limits, and a
    // 453 km descent. These are coordinate checks, not physical boat trials.
    for (const FVector Expected : {Last,FVector(5000001.,-5000001.,50001.),
        FVector(45333400.,-24000000.,-65000.),FVector(-45333400.,12000000.,150000.),
        FVector(12.,30.,-150.)})
    {
        FVector Location=Expected,Velocity=Moving;
        TestFalse(TEXT("valid geographic pose does not trigger recovery"),
            RaftSimWorldPositionGuard::Recover(Location,Velocity,Last));
        TestTrue(TEXT("position preserved exactly"),Location==Expected);
        TestTrue(TEXT("velocity preserved exactly"),Velocity==Moving);
    }
    for (const FVector Invalid : {FVector(HALF_WORLD_MAX*2.,0,0),
        FVector(0,-HALF_WORLD_MAX*2.,0),FVector(0,0,HALF_WORLD_MAX*2.),
        FVector(std::numeric_limits<double>::infinity(),0,0),
        FVector(0,std::numeric_limits<double>::quiet_NaN(),0)})
    {
        FVector Location=Invalid,Velocity=Moving;
        TestTrue(TEXT("invalid pose recovers"),RaftSimWorldPositionGuard::Recover(Location,Velocity,Last));
        TestTrue(TEXT("recovery uses previous geography, not the origin"),Location==Last);
        TestTrue(TEXT("runaway linear velocity cleared"),Velocity.IsZero());
    }
    return !HasAnyErrors();
}
#endif
