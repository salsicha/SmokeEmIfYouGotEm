#include "Algo/Reverse.h"
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

    RaftSimRaftMesh::FMeshData RestTubes, RestFloor, RestRigging, RestMetal, RestRubber;
    RaftSimRaftMesh::BuildInflatableRaft(
        Body.LengthMeters, Body.WidthMeters, Body.TubeRadiusMeters,
        RestTubes, RestFloor, {}, {}, &RestRigging, &RestMetal, &RestRubber);
    RaftSimRaftMesh::FMeshData ContactTubes, ContactFloor, ContactRigging;
    RaftSimRaftMesh::FMeshData ContactMetal, ContactRubber;
    RaftSimRaftMesh::BuildInflatableRaft(
        Body.LengthMeters, Body.WidthMeters, Body.TubeRadiusMeters,
        ContactTubes, ContactFloor, Adapter->GetFlexibleVisualSegments(), {}, &ContactRigging,
        &ContactMetal, &ContactRubber);

    TestEqual(TEXT("tube topology vertex count stays stable"),
              ContactTubes.Vertices.Num(), RestTubes.Vertices.Num());
    TestEqual(TEXT("tube topology triangle count stays stable"),
              ContactTubes.Triangles.Num(), RestTubes.Triangles.Num());
    TestEqual(TEXT("floor topology vertex count stays stable"),
              ContactFloor.Vertices.Num(), RestFloor.Vertices.Num());
    TestEqual(TEXT("rigging topology vertex count stays stable"),
              ContactRigging.Vertices.Num(), RestRigging.Vertices.Num());
    TestEqual(TEXT("D-ring topology vertex count stays stable"),
              ContactMetal.Vertices.Num(), RestMetal.Vertices.Num());
    TestEqual(TEXT("rubber detail topology vertex count stays stable"),
              ContactRubber.Vertices.Num(), RestRubber.Vertices.Num());

    float MaxTubeDisplacementCm = 0.0f;
    float MaxRiggingDisplacementCm = 0.0f;
    float MaxHardwareDisplacementCm = 0.0f;
    FBox ContactTubeBounds(ForceInit);
    bool bFinite = true;
    for (int32 Index = 0; Index < RestTubes.Vertices.Num(); ++Index)
    {
        const FVector& Vertex = ContactTubes.Vertices[Index];
        bFinite &= !Vertex.ContainsNaN();
        MaxTubeDisplacementCm = FMath::Max(
            MaxTubeDisplacementCm,
            FVector::Distance(RestTubes.Vertices[Index], Vertex));
        ContactTubeBounds += Vertex;
    }
    for (int32 Index = 0; Index < RestRigging.Vertices.Num(); ++Index)
    {
        const FVector& Vertex = ContactRigging.Vertices[Index];
        bFinite &= !Vertex.ContainsNaN();
        MaxRiggingDisplacementCm = FMath::Max(
            MaxRiggingDisplacementCm,
            FVector::Distance(RestRigging.Vertices[Index], Vertex));
    }
    for (int32 Index = 0; Index < RestMetal.Vertices.Num(); ++Index)
    {
        const FVector& Vertex = ContactMetal.Vertices[Index];
        bFinite &= !Vertex.ContainsNaN();
        MaxHardwareDisplacementCm = FMath::Max(
            MaxHardwareDisplacementCm,
            FVector::Distance(RestMetal.Vertices[Index], Vertex));
    }
    for (int32 Index = 0; Index < RestRubber.Vertices.Num(); ++Index)
    {
        const FVector& Vertex = ContactRubber.Vertices[Index];
        bFinite &= !Vertex.ContainsNaN();
        MaxHardwareDisplacementCm = FMath::Max(
            MaxHardwareDisplacementCm,
            FVector::Distance(RestRubber.Vertices[Index], Vertex));
    }
    const FBox BondedDetailEnvelope = ContactTubeBounds.ExpandBy(25.0f);
    bool bBondedDetailsStayOnTube = true;
    for (const FVector& Vertex : ContactRubber.Vertices)
    {
        bBondedDetailsStayOnTube &= BondedDetailEnvelope.IsInsideOrOn(Vertex);
    }
    TestTrue(TEXT("deformed vertices remain finite"), bFinite);
    TestTrue(
        TEXT("bonded rubber details remain within 25 cm of the deformed tube envelope"),
        bBondedDetailsStayOnTube);
    TestTrue(
        FString::Printf(
            TEXT("contact visibly moves the tube by more than 5 cm (measured %.3f cm)"),
            MaxTubeDisplacementCm),
        MaxTubeDisplacementCm > 5.0f);
    TestTrue(TEXT("perimeter rigging follows contact deformation"),
             MaxRiggingDisplacementCm > 1.0f);
    TestTrue(TEXT("commercial fittings follow contact deformation"),
             MaxHardwareDisplacementCm > 0.5f);

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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimFlexibleRaftOverwashLongRunStabilityTest,
    "RaftSim.M1.FlexibleRaftOverwashLongRunStability",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimFlexibleRaftOverwashLongRunStabilityTest::RunTest(const FString& Parameters)
{
    FRaftSimFlexParameters Flex;
    const TArray<FRaftSimFlexTubeSegment> Layout =
        RaftSimFlex::BuildDefaultCompliantTubeLayout(Flex);
    const TArray<FRaftSimFlexCrewSeat> Seats = RaftSimFlex::BuildDefaultCrewSeats(Flex);

    FRaftSimFlexRigidState State;
    State.LinearVelocity = FVector(0.0, 2.0, 0.0);
    FRaftSimFlexSeatLoadSolve SeatSolve = RaftSimFlex::SolveSeatLoadCoupledTubeD2(
        State,
        Flex,
        Seats,
        {},
        Layout);

    // Lookup must remain keyed by SegmentId rather than relying on matching
    // array order. This also exercises the allocation-free path introduced
    // after the packaged soak caught a transient response-map rehash crash.
    Algo::Reverse(SeatSolve.TubeSolve.SegmentResponses);

    FRaftSimFlexUniformWater Water;
    Water.SurfaceHeightM = 0.42;
    Water.VelocityMps = FVector(0.0, -4.0, 0.0);
    Water.bWet = true;

    TMap<FString, double> RetainedVolumeBySegment;
    constexpr int32 EvaluationCount = 20000;
    for (int32 EvaluationIndex = 0; EvaluationIndex < EvaluationCount; ++EvaluationIndex)
    {
        Water.SurfaceHeightM = 0.42 + 0.03 * FMath::Sin(static_cast<double>(EvaluationIndex) * 0.013);
        const FRaftSimFlexOverwashSolve Overwash = RaftSimFlex::EvaluateOverwashFlipD3(
            SeatSolve,
            Water,
            Layout,
            &RetainedVolumeBySegment,
            1.0 / 120.0);

        if (Overwash.SegmentOverwash.Num() != Layout.Num())
        {
            AddError(FString::Printf(
                TEXT("evaluation %d returned %d of %d segment responses"),
                EvaluationIndex,
                Overwash.SegmentOverwash.Num(),
                Layout.Num()));
            return false;
        }
        if (
            !FMath::IsFinite(Overwash.TotalOvertoppingFluxM3S)
            || !FMath::IsFinite(Overwash.TotalRetainedWaterVolumeM3)
            || !FMath::IsFinite(Overwash.ReferenceFlipMarginNm)
            || Overwash.TotalOvertoppingFluxM3S < 0.0
            || Overwash.TotalRetainedWaterVolumeM3 < 0.0)
        {
            AddError(FString::Printf(
                TEXT("evaluation %d produced non-finite or negative overwash telemetry"),
                EvaluationIndex));
            return false;
        }

        RetainedVolumeBySegment.Reset();
        for (const FRaftSimFlexSegmentOverwash& Segment : Overwash.SegmentOverwash)
        {
            if (Segment.RetainedWaterVolumeM3 > 0.0)
            {
                RetainedVolumeBySegment.Add(
                    Segment.SegmentId,
                    Segment.RetainedWaterVolumeM3);
            }
        }
    }

    TestTrue(
        TEXT("sustained overwash evaluation retains at least one wet segment"),
        RetainedVolumeBySegment.Num() > 0);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimFlexibleCapsizeLoadingStateTest,
    "RaftSim.M1.FlexibleCapsizeLoadingState",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimFlexibleCapsizeLoadingStateTest::RunTest(const FString& Parameters)
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
    Adapter->ConfigureFlexibleRaftModel(Flex, RaftSimFlex::BuildDefaultCrewSeats(Flex));

    FRaftSimFlexUniformWater Water;
    Water.SurfaceHeightM = 0.8;
    Water.VelocityMps = FVector(0.0, 6.0, 0.0);
    Water.bWet = true;
    Adapter->SetFlexibleUniformWater(Water, true);

    FRaftSimFlexRockObstacle Rock;
    Rock.ObstacleId = TEXT("capsized_wrap_rock");
    Rock.LocalPosition = FVector(0.0, -1.0, 0.0);
    Rock.RadiusM = 1.4;
    Rock.FrictionCoefficient = 0.78;
    Adapter->SetFlexibleRockObstacles({Rock});

    TestTrue(TEXT("loaded overwash/contact step succeeds"),
             Adapter->StepRaftDynamics(1.0f / 120.0f));
    TestTrue(TEXT("upright solve retains overwash"),
             Adapter->GetFlexibleRetainedVolumeBySegment().Num() > 0);
    TestTrue(TEXT("upright solve records D4 indentation"),
             Adapter->GetFlexibleIndentationBySegment().Num() > 0);

    Adapter->SetFlexibleCapsized(true);
    TestTrue(TEXT("adapter enters capsized loading state"), Adapter->IsFlexibleCapsized());
    TestEqual(TEXT("capsize drains retained deck water"),
              Adapter->GetFlexibleRetainedVolumeBySegment().Num(), 0);
    TestTrue(TEXT("capsize preserves D4 indentation memory"),
             Adapter->GetFlexibleIndentationBySegment().Num() > 0);

    TestTrue(TEXT("capsized contact step succeeds"),
             Adapter->StepRaftDynamics(1.0f / 120.0f));
    const FRaftSimFlexStepTelemetry Capsized = Adapter->GetLastFlexibleStepTelemetry();
    TestTrue(TEXT("capsized solve keeps crew freeboard load removed"),
             Capsized.MaxFreeboardLossM < 0.001);
    TestTrue(TEXT("capsized solve keeps retained water drained"),
             Capsized.TotalRetainedWaterMassKg < 0.001);
    TestTrue(TEXT("capsized solve continues D4 contact"), Capsized.ContactCount > 0);

    Adapter->SetFlexibleCapsized(false);
    TestFalse(TEXT("adapter exits capsized loading state"), Adapter->IsFlexibleCapsized());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimFlexibleLiveWaterFieldD3Test,
    "RaftSim.M1.FlexibleLiveWaterFieldDrivesD3",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimFlexibleLiveWaterFieldD3Test::RunTest(const FString& Parameters)
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
    Adapter->ConfigureFlexibleRaftModel(Flex, RaftSimFlex::BuildDefaultCrewSeats(Flex));

    int32 SamplerCallCount = 0;
    Adapter->SetFlexibleWaterFieldSampler(
        [&SamplerCallCount](
            const FVector& WorldPositionCm,
            FRaftSimFlexUniformWater& OutWater) -> bool
        {
            ++SamplerCallCount;
            // Strong lateral water overtops only the upstream (negative-Y)
            // tubes. This proves D3 consumes segment positions rather than a
            // single raft-center descriptor.
            OutWater.SurfaceHeightM = WorldPositionCm.Y < 0.0f ? 0.8 : -0.5;
            OutWater.VelocityMps = FVector(0.0, 6.0, 0.0);
            OutWater.bWet = true;
            return true;
        });

    TestTrue(TEXT("live-field D3 step succeeds"),
             Adapter->StepRaftDynamics(1.0f / 120.0f));
    const FRaftSimFlexStepTelemetry Live = Adapter->GetLastFlexibleStepTelemetry();
    TestTrue(TEXT("D3 reports the live field"), Live.bUsedLiveWaterField);
    TestFalse(TEXT("uniform fixture override is not active"),
              Live.bUsedUniformWaterOverride);
    TestEqual(TEXT("sampler called once for every flexible segment"),
              SamplerCallCount, Live.LiveWaterSampleCount);
    TestTrue(TEXT("all default tube segments receive samples"),
             Live.LiveWaterSampleCount >= 12);
    TestEqual(TEXT("all returned samples are wet"),
              Live.LiveWetSampleCount, Live.LiveWaterSampleCount);
    TestTrue(TEXT("live lateral water retains deck load"),
             Live.TotalRetainedWaterMassKg > 0.0);
    TestTrue(TEXT("segment-varying water produces a roll moment"),
             FMath::Abs(Live.RetainedWaterRollMomentNm) > 0.0);

    // Keep the field active long enough to exercise angular-velocity feedback.
    // A prior uncapped production path let point velocity inflate flux until
    // retained water reached hundreds of millions of kilograms.
    double MaximumCoupledRetainedMassKg = Live.TotalRetainedWaterMassKg;
    bool bCoupledStateStayedFinite = true;
    for (int32 StepIndex = 0; StepIndex < 600; ++StepIndex)
    {
        bCoupledStateStayedFinite &=
            Adapter->StepRaftDynamics(1.0f / 120.0f);
        const FRaftSimFlexStepTelemetry& Coupled =
            Adapter->GetLastFlexibleStepTelemetry();
        MaximumCoupledRetainedMassKg = FMath::Max(
            MaximumCoupledRetainedMassKg,
            Coupled.TotalRetainedWaterMassKg);
        const FRaftSimRaftKinematicState& State = Adapter->GetKinematicState();
        bCoupledStateStayedFinite &= State.WorldTransform.IsValid() &&
            !State.LinearVelocityMetersPerSecond.ContainsNaN() &&
            !State.AngularVelocityRadiansPerSecond.ContainsNaN();
    }
    TestTrue(TEXT("five-second live-field feedback remains finite"),
             bCoupledStateStayedFinite);
    TestTrue(
        FString::Printf(
            TEXT("self-bailing retained load stays within 12 x 50 kg capacity (%.3f kg)"),
            MaximumCoupledRetainedMassKg),
        MaximumCoupledRetainedMassKg <= 600.001);

    FRaftSimFlexUniformWater Override;
    Override.bWet = false;
    Adapter->SetFlexibleUniformWater(Override, true);
    TestTrue(TEXT("uniform override step succeeds"),
             Adapter->StepRaftDynamics(1.0f / 120.0f));
    const FRaftSimFlexStepTelemetry Overridden =
        Adapter->GetLastFlexibleStepTelemetry();
    TestTrue(TEXT("uniform fixture override takes precedence"),
             Overridden.bUsedUniformWaterOverride);
    TestFalse(TEXT("live sampler is bypassed by fixture override"),
              Overridden.bUsedLiveWaterField);
    TestEqual(TEXT("override publishes zero live samples"),
              Overridden.LiveWaterSampleCount, 0);

    Adapter->SetFlexibleUniformWater(FRaftSimFlexUniformWater{}, false);
    TestTrue(TEXT("live field resumes after override clears"),
             Adapter->StepRaftDynamics(1.0f / 120.0f));
    TestTrue(TEXT("D3 returns to live segment samples"),
             Adapter->GetLastFlexibleStepTelemetry().bUsedLiveWaterField);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimDryRapidCrestGroundingTest,
    "RaftSim.M1.DryRapidCrestGroundingStopsRaft",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimDryRapidCrestGroundingTest::RunTest(const FString& Parameters)
{
    URaftSimChronoRuntimeAdapter* Adapter =
        NewObject<URaftSimChronoRuntimeAdapter>();
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

    // Model the top of a rapid where the cooked wet mask exposes a shallow
    // bar. Water contributes no support there; the solver bed must stop the
    // custom kinematic body instead of letting it fall through visual ground.
    Adapter->SetWaterSurfaceSampler(
        [](const FVector&, float&) -> bool
        {
            return false;
        });
    int32 GroundSampleCount = 0;
    Adapter->SetGroundSurfaceSampler(
        [&GroundSampleCount](
            const FVector&,
            float& OutGroundZCm,
            FVector& OutGroundNormal) -> bool
        {
            ++GroundSampleCount;
            OutGroundZCm = 0.0f;
            OutGroundNormal = FVector::UpVector;
            return true;
        });

    FRaftSimRaftKinematicState State;
    State.WorldTransform.SetTranslation(FVector(0.0f, 0.0f, -50.0f));
    State.LinearVelocityMetersPerSecond = FVector(3.0f, 0.0f, -4.0f);
    Adapter->SetKinematicState(State);

    bool bStayedFinite = true;
    constexpr float Dt = 1.0f / 120.0f;
    for (int32 StepIndex = 0; StepIndex < 120; ++StepIndex)
    {
        bStayedFinite &= Adapter->StepRaftDynamics(Dt);
        const FRaftSimRaftKinematicState& Current =
            Adapter->GetKinematicState();
        bStayedFinite &= Current.WorldTransform.IsValid() &&
            !Current.LinearVelocityMetersPerSecond.ContainsNaN();
    }

    const FRaftSimRaftKinematicState& Grounded =
        Adapter->GetKinematicState();
    const float GroundedZMeters =
        Grounded.WorldTransform.GetTranslation().Z / 100.0f;
    TestTrue(TEXT("dry-crest grounding remains finite"), bStayedFinite);
    TestEqual(TEXT("all six water support points report dry"),
              Adapter->GetLastDrySupportPointCount(), 6);
    TestTrue(TEXT("ground sampler runs once per tube point per substep"),
             GroundSampleCount >= 6 * 120);
    TestEqual(TEXT("all six tube points remain grounded"),
              Adapter->GetLastGroundedSupportPointCount(), 6);
    TestTrue(
        FString::Printf(
            TEXT("terrain keeps tube center above its %.2f m radius (z %.4f m)"),
            Body.TubeRadiusMeters,
            GroundedZMeters),
        GroundedZMeters >= Body.TubeRadiusMeters - 1.0e-4f);
    TestTrue(TEXT("terrain removes downward velocity"),
             Grounded.LinearVelocityMetersPerSecond.Z >= -1.0e-4f);
    TestTrue(
        FString::Printf(
            TEXT("inelastic ground contact stops horizontal slide (%.4f m/s)"),
            Grounded.LinearVelocityMetersPerSecond.Size2D()),
        Grounded.LinearVelocityMetersPerSecond.Size2D() < 0.05f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimDeepRapidMaskGapBuoyancyTest,
    "RaftSim.M1.DeepRapidMaskGapRetainsBuoyancy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimDeepRapidMaskGapBuoyancyTest::RunTest(const FString& Parameters)
{
    URaftSimChronoRuntimeAdapter* Adapter =
        NewObject<URaftSimChronoRuntimeAdapter>();
    TestNotNull(TEXT("adapter"), Adapter);
    if (Adapter == nullptr)
    {
        return false;
    }

    FRaftSimRaftBodyConfig Body;
    Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Body.MassKg = 605.0f;
    Body.LengthMeters = 4.3f;
    Body.WidthMeters = 2.0f;
    Body.TubeRadiusMeters = 0.28f;
    Body.BuoyancyWeightMultiple = 5.2f;
    Body.LinearDragCoefficient = 650.0f;
    Body.LowSpeedDragReferenceMps = 1.5f;
    Body.InertiaTensorKgM2 = FVector(900.0f, 900.0f, 1100.0f);
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

    bool bWetMaskPresent = true;
    Adapter->SetWaterSurfaceSampler(
        [&bWetMaskPresent](
            const FVector&,
            float& OutSurfaceZCm) -> bool
        {
            OutSurfaceZCm = 0.0f;
            return bWetMaskPresent;
        });
    Adapter->SetFlexibleWaterFieldSampler(
        [&bWetMaskPresent](
            const FVector&,
            FRaftSimFlexUniformWater& OutWater) -> bool
        {
            OutWater.SurfaceHeightM = 0.0;
            OutWater.VelocityMps = FVector(0.8, 0.0, 0.0);
            OutWater.bWet = bWetMaskPresent;
            return true;
        });
    Adapter->SetGroundSurfaceSampler(
        [](const FVector&, float& OutGroundZCm, FVector& OutNormal) -> bool
        {
            // Deep channel beneath a false dry cell: this is not a shoal.
            OutGroundZCm = -300.0f;
            OutNormal = FVector::UpVector;
            return true;
        });

    FRaftSimRaftKinematicState State;
    State.WorldTransform.SetTranslation(FVector(0.0f, 0.0f, -12.0f));
    State.LinearVelocityMetersPerSecond = FVector(0.8f, 0.0f, 0.0f);
    Adapter->SetKinematicState(State);

    constexpr float Dt = 1.0f / 120.0f;
    bool bStayedFinite = true;
    for (int32 StepIndex = 0; StepIndex < 120; ++StepIndex)
    {
        bStayedFinite &= Adapter->StepRaftDynamics(Dt);
    }
    const float WetZMeters =
        Adapter->GetKinematicState().WorldTransform.GetTranslation().Z / 100.0f;

    // Cross a two-second all-dry hole before the rapid. Its deep bed proves
    // that the dry mask is missing water, not describing exposed terrain.
    bWetMaskPresent = false;
    for (int32 StepIndex = 0; StepIndex < 240; ++StepIndex)
    {
        bStayedFinite &= Adapter->StepRaftDynamics(Dt);
    }
    const FRaftSimRaftKinematicState& Bridged =
        Adapter->GetKinematicState();
    const float BridgedZMeters =
        Bridged.WorldTransform.GetTranslation().Z / 100.0f;
    TestTrue(TEXT("deep mask-gap crossing remains finite"), bStayedFinite);
    TestEqual(TEXT("all six support probes still report the mask as dry"),
              Adapter->GetLastDrySupportPointCount(), 6);
    TestEqual(TEXT("deep channel does not falsely ground the raft"),
              Adapter->GetLastGroundedSupportPointCount(), 0);
    TestTrue(
        FString::Printf(
            TEXT("deep dry gap preserves the wet waterline (wet %.3f m, gap %.3f m)"),
            WetZMeters,
            BridgedZMeters),
        FMath::Abs(BridgedZMeters - WetZMeters) < 0.20f);
    TestTrue(TEXT("deep dry gap never sinks the hull below its tube envelope"),
             BridgedZMeters > -0.45f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimPaddleCoastDownTest,
    "RaftSim.M1.PaddleCoastDownUsesLowSpeedHullResistance",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimPaddleCoastDownTest::RunTest(const FString& Parameters)
{
    URaftSimChronoRuntimeAdapter* Adapter =
        NewObject<URaftSimChronoRuntimeAdapter>();
    TestNotNull(TEXT("adapter"), Adapter);
    if (Adapter == nullptr)
    {
        return false;
    }

    FRaftSimRaftBodyConfig Body;
    Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Body.MassKg = 605.0f;
    Body.LengthMeters = 4.3f;
    Body.WidthMeters = 2.0f;
    Body.TubeRadiusMeters = 0.28f;
    Body.BuoyancyWeightMultiple = 5.2f;
    Body.LinearDragCoefficient = 650.0f;
    Body.LowSpeedDragReferenceMps = 1.5f;
    Body.InertiaTensorKgM2 = FVector(900.0f, 900.0f, 1100.0f);
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
    Adapter->SetWaterSurfaceSampler(
        [](const FVector&, float& OutSurfaceZCm) -> bool
        {
            OutSurfaceZCm = 0.0f;
            return true;
        });
    Adapter->SetFlexibleWaterFieldSampler(
        [](const FVector&, FRaftSimFlexUniformWater& OutWater) -> bool
        {
            OutWater.SurfaceHeightM = 0.0;
            OutWater.VelocityMps = FVector::ZeroVector;
            OutWater.bWet = true;
            return true;
        });

    FRaftSimRaftKinematicState State;
    State.WorldTransform.SetTranslation(FVector(0.0f, 0.0f, -12.0f));
    State.LinearVelocityMetersPerSecond = FVector(2.0f, 0.0f, 0.0f);
    Adapter->SetKinematicState(State);

    bool bStayedFinite = true;
    constexpr float Dt = 1.0f / 120.0f;
    for (int32 StepIndex = 0; StepIndex < 600; ++StepIndex)
    {
        bStayedFinite &= Adapter->StepRaftDynamics(Dt);
    }
    const FRaftSimRaftKinematicState& Coasted =
        Adapter->GetKinematicState();
    const float SpeedMps =
        Coasted.LinearVelocityMetersPerSecond.Size2D();
    const float DistanceMeters =
        Coasted.WorldTransform.GetTranslation().X / 100.0f;
    TestTrue(TEXT("five-second coast-down remains finite"), bStayedFinite);
    TestTrue(
        FString::Printf(
            TEXT("stopped paddling sheds speed below 0.50 m/s (%.3f m/s)"),
            SpeedMps),
        SpeedMps < 0.50f);
    TestTrue(
        FString::Printf(
            TEXT("coasting hull stops within 5.5 m (%.3f m)"),
            DistanceMeters),
        DistanceMeters < 5.5f);
    TestTrue(TEXT("coast-down keeps the loaded raft afloat"),
             Coasted.WorldTransform.GetTranslation().Z > -45.0f);
    return true;
}

#endif // WITH_AUTOMATION_TESTS
