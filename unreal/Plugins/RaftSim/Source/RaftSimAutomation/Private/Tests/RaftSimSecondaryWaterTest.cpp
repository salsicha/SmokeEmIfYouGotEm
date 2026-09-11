#include "Misc/AutomationTest.h"
#include "RaftSimSecondaryWater.h"
#include "RaftSimSecondaryWaterComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Misc/ScopeExit.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSecondaryWaterTest,
    "RaftSim.M4.SecondaryWater", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSecondaryWaterTest::RunTest(const FString&)
{
    using FSim = FRaftSimSecondaryWater;
    auto Flat = [](const FVector&, FSim::FCarrier& C)
    { C.HeightM = 0; C.VelocityMps = FVector(2, -1, 0); return true; };
    FSim Simulation;
    TestTrue(TEXT("wet source accepted"), Simulation.Spawn(FVector::ZeroVector, FVector(0,0,2), .03, Flat));
    for (int32 I=0; I<12; ++I) Simulation.Step(FSim::StepSeconds, Flat);
    const auto& P = Simulation.Particles[0];
    TestTrue(TEXT("air inherits full current speed"), P.PositionM.Equals(
        FVector(.4,-.2,.03+2*.2-.5*FSim::Gravity*.2*.2), 1.e-8));
    TestFalse(TEXT("still airborne before return"), P.bFoam);
    TestTrue(TEXT("constant gravity, independent of current"), FMath::IsNearlyEqual(P.VelocityMps.Z, 2-FSim::Gravity*.2, 1.e-8));
    for (int32 I=0; I<18; ++I) Simulation.Step(FSim::StepSeconds, Flat);
    TestEqual(TEXT("one return event"), Simulation.Returned, uint64(1));
    TestTrue(TEXT("returned fragment is attached"), P.bFoam);
    TestTrue(TEXT("foam travels at current, not cone speed"), P.PositionM.Equals(FVector(1,-.5,0), 1.e-8));
    TestTrue(TEXT("returned velocity is liquid velocity"), P.VelocityMps.Equals(FVector(2,-1,0),1.e-8));

    // Moving or removing an emitter cannot relocate already-born particles.
    TestTrue(TEXT("second source at another position"), Simulation.Spawn(FVector(40,20,0), FVector(0,0,2), .03, Flat));
    Simulation.Step(FSim::StepSeconds, Flat);
    TestTrue(TEXT("first birth remains independent"), P.PositionM.X < 2 && P.BirthId == 1);

    FSim Split, Whole;
    Whole.Spawn(FVector::ZeroVector,FVector(0,0,2),.03,Flat);
    Split.Spawn(FVector::ZeroVector,FVector(0,0,2),.03,Flat);
    for(int32 I=0; I<10; ++I) Whole.Step(FSim::StepSeconds,Flat);
    for(int32 I=0; I<20; ++I) Split.Step(FSim::StepSeconds*.5,Flat);
    TestTrue(TEXT("air ballistic partition equivalence"), Whole.Particles[0].PositionM.Equals(Split.Particles[0].PositionM,1.e-8));
    auto Dry = [](const FVector&,FSim::FCarrier&) {return false;};
    Whole.Step(FSim::StepSeconds,Dry);
    TestEqual(TEXT("missing/dry water never leaves floating fragments"), Whole.AliveCount(),0);
    TestFalse(TEXT("dry births rejected"), Whole.Spawn(FVector::ZeroVector,FVector::UpVector,.03,Dry));
    TestFalse(TEXT("invalid radius rejected"), Whole.Spawn(FVector::ZeroVector,FVector::UpVector,-1,Flat));

    FSim Full;
    for(int32 I=0; I<FSim::Capacity; ++I)
        TestTrue(TEXT("bounded slot accepted"), Full.Spawn(FVector::ZeroVector,FVector(0,0,2),.03,Flat));
    TestFalse(TEXT("capacity cannot grow or evict"),Full.Spawn(FVector::ZeroVector,FVector(0,0,2),.03,Flat));
    TestEqual(TEXT("original first birth retained"),Full.Particles[0].BirthId,uint64(1));
    for(int32 I=0; I<190; ++I) Full.Step(FSim::StepSeconds,Flat);
    TestEqual(TEXT("all particles expire"),Full.AliveCount(),0);
    TestEqual(TEXT("all return before expiry"),Full.Returned,uint64(FSim::Capacity));

    auto Slope = [](const FVector& X,FSim::FCarrier& C)
    { C.HeightM=-.3*X.X; C.VelocityMps=FVector(1,0,0); return true; };
    FSim Falling;
    Falling.Spawn(FVector::ZeroVector,FVector(0,0,2),.03,Slope);
    for(int32 I=0; I<40; ++I) Falling.Step(FSim::StepSeconds,Slope);
    TestTrue(TEXT("return follows descending carrier, not birth plane"), Falling.Particles[0].bFoam &&
        FMath::IsNearlyEqual(Falling.Particles[0].PositionM.Z,-.3*Falling.Particles[0].PositionM.X,1.e-8));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSecondaryWaterInstanceHistoryTest,
    "RaftSim.M4.SecondaryWaterInstanceHistory", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSecondaryWaterInstanceHistoryTest::RunTest(const FString&)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Editor, false);
    if (!TestNotNull(TEXT("instance fixture world"),World)) return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
    auto* Owner = World->SpawnActor<AActor>();
    auto* Instances = NewObject<UInstancedStaticMeshComponent>(Owner);
    Instances->SetMobility(EComponentMobility::Movable);
    Instances->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere")));
    Instances->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Instances->RegisterComponent();
    TArray<FTransform> History;
    URaftSimSecondaryWaterComponent::InitializeInstanceHistory(Instances,History);
    TestEqual(TEXT("renderer capacity bounded"),Instances->GetInstanceCount(),FRaftSimSecondaryWater::Capacity);
    TArray<FTransform> Current = History;
    Current[0] = FTransform(FVector(2,3,4));
    Current.Last() = FTransform(FVector(5,6,7));
    TestTrue(TEXT("first explicit-history batch succeeds"),Instances->BatchUpdateInstancesTransforms(0,Current,History,true,true,false));
    FTransform Before, Now;
    TestTrue(TEXT("last previous slot initialized"),Instances->GetInstancePrevTransform(History.Num()-1,Before,true));
    TestTrue(TEXT("last current slot initialized"),Instances->GetInstanceTransform(History.Num()-1,Now,true));
    TestTrue(TEXT("current and previous frames remain distinct"),Now.GetLocation().Equals(FVector(5,6,7)) && Before.GetLocation().IsNearlyZero());
    Instances->DestroyComponent();
    return true;
}
#endif
