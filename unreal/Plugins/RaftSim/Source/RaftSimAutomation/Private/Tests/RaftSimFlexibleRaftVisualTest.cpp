#include "Misc/AutomationTest.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimRaftMesh.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimFlexibleRaftVisualTest,
    "RaftSim.M1.FlexibleRaftVisualTracksContact",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimFlexibleRaftVisualTest::RunTest(const FString& Parameters)
{
    URaftSimChronoRuntimeAdapter* Adapter = NewObject<URaftSimChronoRuntimeAdapter>();
    TestNotNull(TEXT("adapter"), Adapter);
    if (Adapter == nullptr)
    {
        return false;
    }

    FRaftSimRaftBodyConfig Body;
    Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Body.MassKg = 220.0f;
    Body.LengthMeters = 4.3f;
    Body.WidthMeters = 2.0f;
    Body.TubeRadiusMeters = 0.28f;
    Body.InertiaTensorKgM2 = FVector(180.0f, 180.0f, 400.0f);
    Adapter->ConfigureRaftBody(Body);

    FRaftSimFlexParameters Flex;
    Flex.MassKg = Body.MassKg;
    Flex.LengthM = Body.LengthMeters;
    Flex.WidthM = Body.WidthMeters;
    Flex.TubeRadiusM = Body.TubeRadiusMeters;
    Flex.GuideMassKg = 0.0;
    Flex.PassengerMassKg = 0.0;
    Flex.PassengerCount = 0;
    Adapter->ConfigureFlexibleRaftModel(Flex, {});

    FRaftSimFlexRockObstacle Rock;
    Rock.ObstacleId = TEXT("m1_wrap_rock");
    Rock.LocalPosition = FVector(0.0, -1.0, 0.0);
    Rock.RadiusM = 1.4;
    Rock.FrictionCoefficient = 0.78;
    Adapter->SetFlexibleRockObstacles({Rock});

    TestTrue(TEXT("contact step succeeds"), Adapter->StepRaftDynamics(1.0f / 120.0f));
    const FRaftSimFlexStepTelemetry ContactTelemetry = Adapter->GetLastFlexibleStepTelemetry();
    TestTrue(TEXT("rock reaches at least three tube segments"), ContactTelemetry.ContactCount >= 3);
    TestTrue(TEXT("D4 reports a wrapping contact"), ContactTelemetry.WrappingContactCount >= 3);
    TestTrue(TEXT("D4 retains a visible indentation"), ContactTelemetry.MaxIndentationM > 0.05);

    RaftSimRaftMesh::FMeshData RestTubes, RestFloor;
    RaftSimRaftMesh::BuildInflatableRaft(
        Body.LengthMeters, Body.WidthMeters, Body.TubeRadiusMeters,
        RestTubes, RestFloor);
    RaftSimRaftMesh::FMeshData ContactTubes, ContactFloor;
    RaftSimRaftMesh::BuildInflatableRaft(
        Body.LengthMeters, Body.WidthMeters, Body.TubeRadiusMeters,
        ContactTubes, ContactFloor, Adapter->GetFlexibleVisualSegments());

    TestEqual(TEXT("tube topology vertex count stays stable"),
              ContactTubes.Vertices.Num(), RestTubes.Vertices.Num());
    TestEqual(TEXT("tube topology triangle count stays stable"),
              ContactTubes.Triangles.Num(), RestTubes.Triangles.Num());
    TestEqual(TEXT("floor topology vertex count stays stable"),
              ContactFloor.Vertices.Num(), RestFloor.Vertices.Num());

    float MaxTubeDisplacementCm = 0.0f;
    bool bFinite = true;
    for (int32 Index = 0; Index < RestTubes.Vertices.Num(); ++Index)
    {
        const FVector& Vertex = ContactTubes.Vertices[Index];
        bFinite &= !Vertex.ContainsNaN();
        MaxTubeDisplacementCm = FMath::Max(
            MaxTubeDisplacementCm,
            FVector::Distance(RestTubes.Vertices[Index], Vertex));
    }
    TestTrue(TEXT("deformed vertices remain finite"), bFinite);
    TestTrue(
        FString::Printf(
            TEXT("contact visibly moves the tube by more than 5 cm (measured %.3f cm)"),
            MaxTubeDisplacementCm),
        MaxTubeDisplacementCm > 5.0f);

    // Removing the obstacle exercises D4 shape recovery. A long bounded step
    // makes the deterministic recovery factor reach zero without a sleep or
    // latent frame dependency.
    Adapter->SetFlexibleRockObstacles({});
    TestTrue(TEXT("recovery step succeeds"), Adapter->StepRaftDynamics(0.5f));
    TestTrue(TEXT("indentation recovers toward rest"),
             Adapter->GetLastFlexibleStepTelemetry().MaxIndentationM < 0.001);
    TestEqual(TEXT("no wrapping contact remains after release"),
              Adapter->GetLastFlexibleStepTelemetry().WrappingContactCount, 0);
    return true;
}

#endif // WITH_AUTOMATION_TESTS
