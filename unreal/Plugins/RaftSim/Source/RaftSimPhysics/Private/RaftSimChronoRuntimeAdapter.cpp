#include "RaftSimChronoRuntimeAdapter.h"

void URaftSimChronoRuntimeAdapter::ConfigureRaftBody(const FRaftSimRaftBodyConfig& InConfig)
{
    RaftConfig = InConfig;
    AuthorityIntegrationPolicy.SelectedRuntime = InConfig.Runtime;
}

void URaftSimChronoRuntimeAdapter::ConfigureAuthorityIntegrationPolicy(const FRaftSimRaftAuthorityIntegrationPolicy& InPolicy)
{
    AuthorityIntegrationPolicy = InPolicy;
    RaftConfig.Runtime = InPolicy.SelectedRuntime;
}

void URaftSimChronoRuntimeAdapter::SetKinematicState(const FRaftSimRaftKinematicState& InState)
{
    KinematicState = InState;
}

void URaftSimChronoRuntimeAdapter::ConfigureFlexibleRaftModel(
    const FRaftSimFlexParameters& InParameters,
    const TArray<FRaftSimFlexCrewSeat>& InSeats,
    double NominalPressurePa)
{
    FlexParameters = InParameters;
    FlexSeats = InSeats;
    FlexLayout = RaftSimFlex::BuildDefaultCompliantTubeLayout(
        FlexParameters,
        /*SegmentCountPerSide=*/4,
        /*SegmentCountPerEnd=*/2,
        NominalPressurePa);
    FlexActions.Reset();
    FlexObstacles.Reset();
    ResetFlexiblePersistentState();
}

void URaftSimChronoRuntimeAdapter::SetFlexibleCrewActions(const TArray<FRaftSimFlexCrewAction>& InActions)
{
    FlexActions = InActions;
}

void URaftSimChronoRuntimeAdapter::SetFlexibleUniformWater(
    const FRaftSimFlexUniformWater& InWater,
    bool bInEnabled)
{
    FlexWater = InWater;
    bFlexWaterEnabled = bInEnabled;
}

void URaftSimChronoRuntimeAdapter::SetFlexibleRockObstacles(const TArray<FRaftSimFlexRockObstacle>& InObstacles)
{
    FlexObstacles = InObstacles;
}

void URaftSimChronoRuntimeAdapter::ResetFlexiblePersistentState()
{
    RetainedVolumeBySegment.Reset();
    IndentationBySegment.Reset();
    LastFlexStepTelemetry = FRaftSimFlexStepTelemetry();
}

bool URaftSimChronoRuntimeAdapter::StepRaftDynamics(float SubstepSeconds)
{
    if (SubstepSeconds <= 0.0f)
    {
        return false;
    }

    if (
        RaftConfig.Runtime == ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody
        && IsFlexibleModelConfigured()
    )
    {
        return StepFlexibleRaftDynamics(static_cast<double>(SubstepSeconds));
    }

    const FVector TranslationDelta = KinematicState.LinearVelocityMetersPerSecond * SubstepSeconds * 100.0f;
    KinematicState.WorldTransform.AddToTranslation(TranslationDelta);
    return true;
}

bool URaftSimChronoRuntimeAdapter::StepFlexibleRaftDynamics(double Dt)
{
    // Build the rigid state in meters from the UE-centimeter kinematic state.
    FRaftSimFlexRigidState State;
    State.Position = KinematicState.WorldTransform.GetTranslation() * 0.01;
    State.Orientation = KinematicState.WorldTransform.GetRotation().GetNormalized();
    State.LinearVelocity = KinematicState.LinearVelocityMetersPerSecond;
    State.AngularVelocity = KinematicState.AngularVelocityRadiansPerSecond;

    const RaftSimFlex::EModelMode Mode = RaftConfig.bEnableCompliantContacts
        ? RaftSimFlex::EModelMode::Compliant
        : RaftSimFlex::EModelMode::RigidBaseline;

    // D1+D2: crew/seat loads into compliant tube deformation.
    const FRaftSimFlexSeatLoadSolve SeatSolve = RaftSimFlex::SolveSeatLoadCoupledTubeD2(
        State,
        FlexParameters,
        FlexSeats,
        FlexActions,
        FlexLayout,
        Mode);

    // D3: overwash sampling against the depressed tube tops. A disabled water
    // descriptor still drains retained water deterministically.
    FRaftSimFlexUniformWater Water = FlexWater;
    if (!bFlexWaterEnabled)
    {
        Water.bWet = false;
    }
    const FRaftSimFlexOverwashSolve Overwash = RaftSimFlex::EvaluateOverwashFlipD3(
        SeatSolve,
        Water,
        FlexLayout,
        &RetainedVolumeBySegment,
        Dt);

    // D4: rock contact, wrap, pin, release, and shape recovery.
    const FRaftSimFlexRockContactSolve Contacts = RaftSimFlex::EvaluateRockContactWrapPinD4(
        SeatSolve,
        FlexObstacles,
        FlexLayout,
        FlexParameters.TubeRadiusM,
        &IndentationBySegment,
        Mode,
        Dt);

    // Persist retained-water and indentation memory for the next substep.
    RetainedVolumeBySegment.Reset();
    for (const FRaftSimFlexSegmentOverwash& Segment : Overwash.SegmentOverwash)
    {
        if (Segment.RetainedWaterVolumeM3 > 0.0)
        {
            RetainedVolumeBySegment.Add(Segment.SegmentId, Segment.RetainedWaterVolumeM3);
        }
    }
    IndentationBySegment.Reset();
    for (const FRaftSimFlexRockContact& Contact : Contacts.Contacts)
    {
        if (Contact.IndentationM <= 0.0)
        {
            continue;
        }
        double& Stored = IndentationBySegment.FindOrAdd(Contact.SegmentId);
        Stored = FMath::Max(Stored, Contact.IndentationM);
    }

    // Quasi-static force/moment modifiers on the kinematic state.
    constexpr double GravityMps2 = 9.81;
    FVector ForceN = FVector::ZeroVector;
    FVector TorqueNm = FVector::ZeroVector;

    for (const FRaftSimFlexSegmentOverwash& Segment : Overwash.SegmentOverwash)
    {
        const double LoadN = Segment.RetainedWaterMassKg * GravityMps2;
        if (LoadN <= 0.0)
        {
            continue;
        }
        const FVector WorldOffset = State.Orientation.RotateVector(Segment.LocalPosition);
        const FVector SegmentForce(0.0, 0.0, -LoadN);
        ForceN += SegmentForce;
        TorqueNm += FVector::CrossProduct(WorldOffset, SegmentForce);
    }

    for (const FRaftSimFlexRockContact& Contact : Contacts.Contacts)
    {
        if (Contact.bRecovering)
        {
            continue;
        }
        const FVector WorldNormal = State.Orientation.RotateVector(Contact.ContactNormalLocal);
        const FVector WorldOffset = State.Orientation.RotateVector(Contact.LocalPosition);
        const FVector NormalForce = WorldNormal * Contact.NormalForceN;
        ForceN += NormalForce;
        TorqueNm += FVector::CrossProduct(WorldOffset, NormalForce);

        const FVector PointVelocity = State.PointVelocity(Contact.LocalPosition);
        const FVector Tangential =
            PointVelocity - WorldNormal * FVector::DotProduct(PointVelocity, WorldNormal);
        const double TangentialSpeed = Tangential.Length();
        if (TangentialSpeed > 1.0e-6)
        {
            const FVector FrictionForce = (Tangential / TangentialSpeed) * -Contact.FrictionForceN;
            ForceN += FrictionForce;
            TorqueNm += FVector::CrossProduct(WorldOffset, FrictionForce);
        }
    }

    const double MassKg = FMath::Max(static_cast<double>(RaftConfig.MassKg), 1.0e-3);
    const FVector LinearAcceleration = ForceN / MassKg;
    const FVector Inertia(
        FMath::Max(static_cast<double>(RaftConfig.InertiaTensorKgM2.X), 1.0e-3),
        FMath::Max(static_cast<double>(RaftConfig.InertiaTensorKgM2.Y), 1.0e-3),
        FMath::Max(static_cast<double>(RaftConfig.InertiaTensorKgM2.Z), 1.0e-3));
    const FVector AngularAcceleration(
        TorqueNm.X / Inertia.X,
        TorqueNm.Y / Inertia.Y,
        TorqueNm.Z / Inertia.Z);

    // Semi-implicit fixed-step update (RaftState6DoF.advance semantics).
    State.LinearVelocity += LinearAcceleration * Dt;
    State.AngularVelocity += AngularAcceleration * Dt;
    State.Position += State.LinearVelocity * Dt;
    const double AngularSpeed = State.AngularVelocity.Length();
    if (AngularSpeed > 1.0e-12)
    {
        const FQuat Delta(State.AngularVelocity / AngularSpeed, AngularSpeed * Dt);
        State.Orientation = (Delta * State.Orientation).GetNormalized();
    }

    KinematicState.WorldTransform.SetTranslation(State.Position * 100.0);
    KinematicState.WorldTransform.SetRotation(State.Orientation);
    KinematicState.LinearVelocityMetersPerSecond = State.LinearVelocity;
    KinematicState.AngularVelocityRadiansPerSecond = State.AngularVelocity;

    LastFlexStepTelemetry.bEvaluated = true;
    LastFlexStepTelemetry.MaxFreeboardLossM = SeatSolve.TubeSolve.MaxFreeboardLossM;
    LastFlexStepTelemetry.PortTotalFreeboardLossM = SeatSolve.PortTotalFreeboardLossM;
    LastFlexStepTelemetry.StarboardTotalFreeboardLossM = SeatSolve.StarboardTotalFreeboardLossM;
    LastFlexStepTelemetry.TubeRollLoadBiasNm = SeatSolve.TubeSolve.RollLoadBiasNm;
    LastFlexStepTelemetry.TubePitchLoadBiasNm = SeatSolve.TubeSolve.PitchLoadBiasNm;
    LastFlexStepTelemetry.TotalRetainedWaterMassKg = Overwash.TotalRetainedWaterMassKg;
    LastFlexStepTelemetry.RetainedWaterRollMomentNm = Overwash.RetainedWaterRollMomentNm;
    LastFlexStepTelemetry.ReferenceFlipThresholdNm = Overwash.ReferenceFlipThresholdNm;
    LastFlexStepTelemetry.ReferenceFlipMarginNm = Overwash.ReferenceFlipMarginNm;
    LastFlexStepTelemetry.bReferenceFlipRisk = Overwash.bReferenceFlipRisk;
    LastFlexStepTelemetry.ContactCount = Contacts.Contacts.Num();
    LastFlexStepTelemetry.WrappingContactCount = Contacts.WrappingContactCount;
    LastFlexStepTelemetry.PinnedObstacleCount = Contacts.PinnedObstacleCount;
    LastFlexStepTelemetry.RecoveringContactCount = Contacts.RecoveringContactCount;
    LastFlexStepTelemetry.MaxIndentationM = Contacts.MaxIndentationM;
    LastFlexStepTelemetry.MinReleaseMarginN = Contacts.MinReleaseMarginN;
    LastFlexStepTelemetry.AppliedForceN = ForceN;
    LastFlexStepTelemetry.AppliedTorqueNm = TorqueNm;
    return true;
}
