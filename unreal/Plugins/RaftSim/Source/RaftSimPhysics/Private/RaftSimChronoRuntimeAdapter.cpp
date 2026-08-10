#include "RaftSimChronoRuntimeAdapter.h"

namespace
{
// Matches the P1 actor-integrator constant so the swap is behavior-preserving.
constexpr double kSupportGravityMps2 = 9.80665;
}

void URaftSimChronoRuntimeAdapter::ConfigureRaftBody(const FRaftSimRaftBodyConfig& InConfig)
{
    RaftConfig = InConfig;
    AuthorityIntegrationPolicy.SelectedRuntime = InConfig.Runtime;

    // Six tube buoyancy sample points from the footprint: bow pair, midship
    // pair, stern pair (meters, local). For the 4.3 m x 2.0 m paddle raft
    // this reproduces the P1 test-tank layout exactly.
    const double HalfLength = 0.5 * RaftConfig.LengthMeters;
    const double HalfWidth = 0.5 * RaftConfig.WidthMeters;
    const double EndX = FMath::Max(HalfLength - 0.3, 0.1);
    const double EndY = FMath::Max(HalfWidth - 0.15, 0.1);
    TubeSamplePointsM = {
        FVector(EndX, -EndY, 0.0), FVector(EndX, EndY, 0.0),
        FVector(0.0, -HalfWidth, 0.0), FVector(0.0, HalfWidth, 0.0),
        FVector(-EndX, -EndY, 0.0), FVector(-EndX, EndY, 0.0),
    };
    PendingLinearImpulseNs = FVector::ZeroVector;
    PendingAngularImpulseNms = FVector::ZeroVector;
}

void URaftSimChronoRuntimeAdapter::AddExternalImpulse(
    FVector LinearImpulseNs, FVector AngularImpulseNms)
{
    PendingLinearImpulseNs += LinearImpulseNs;
    PendingAngularImpulseNms += AngularImpulseNms;
}

void URaftSimChronoRuntimeAdapter::SetWaterSurfaceSampler(
    TFunction<bool(const FVector& WorldPositionCm, float& OutWaterSurfaceZCm)> InSampler)
{
    WaterSurfaceSampler = MoveTemp(InSampler);
}

void URaftSimChronoRuntimeAdapter::SetFlexibleWaterFieldSampler(
    TFunction<bool(
        const FVector& WorldPositionCm,
        FRaftSimFlexUniformWater& OutWater)> InSampler)
{
    FlexibleWaterFieldSampler = MoveTemp(InSampler);
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
    FlexCapsizedSeats = FlexSeats;
    for (FRaftSimFlexCrewSeat& Seat : FlexCapsizedSeats)
    {
        Seat.bOccupied = false;
    }
    FlexLayout = RaftSimFlex::BuildDefaultCompliantTubeLayout(
        FlexParameters,
        /*SegmentCountPerSide=*/4,
        /*SegmentCountPerEnd=*/2,
        NominalPressurePa);
    LiveWaterBySegmentScratch.Reset();
    LiveWaterBySegmentScratch.Reserve(FlexLayout.Num());
    FlexActions.Reset();
    FlexObstacles.Reset();
    bFlexCapsized = false;
    FlexPressureFraction = 1.0f;
    FlexFabricIntegrity = 1.0f;
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
    bFlexUniformWaterOverrideEnabled = bInEnabled;
}

void URaftSimChronoRuntimeAdapter::SetFlexibleCapsized(bool bInCapsized)
{
    if (bFlexCapsized == bInCapsized)
    {
        return;
    }
    bFlexCapsized = bInCapsized;
    if (bFlexCapsized)
    {
        // A self-bailing raft cannot retain its upright deck-water reservoir
        // after rolling over. Crew loads also disappear through the temporary
        // unoccupied seat view in StepFlexibleRaftDynamics. Do not clear D4
        // indentation here: an inverted boat can remain wrapped or pinned.
        RetainedVolumeBySegment.Reset();
        FlexActions.Reset();
    }
}

void URaftSimChronoRuntimeAdapter::SetFlexibleRockObstacles(const TArray<FRaftSimFlexRockObstacle>& InObstacles)
{
    FlexObstacles = InObstacles;
}

void URaftSimChronoRuntimeAdapter::SetFlexibleConditionModifiers(
    float PressureFraction,
    float FabricIntegrity)
{
    FlexPressureFraction = FMath::Clamp(PressureFraction, 0.25f, 1.0f);
    FlexFabricIntegrity = FMath::Clamp(FabricIntegrity, 0.0f, 1.0f);
}

void URaftSimChronoRuntimeAdapter::ResetFlexiblePersistentState()
{
    RetainedVolumeBySegment.Reset();
    IndentationBySegment.Reset();
    LastFlexStepTelemetry = FRaftSimFlexStepTelemetry();
    LastFlexVisualSegments.Reset();
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
    const FRaftSimFlexRigidState PreviousFiniteState = State;

    const RaftSimFlex::EModelMode Mode = RaftConfig.bEnableCompliantContacts
        ? RaftSimFlex::EModelMode::Compliant
        : RaftSimFlex::EModelMode::RigidBaseline;

    // D1+D2: crew/seat loads into compliant tube deformation.
    const TArray<FRaftSimFlexCrewSeat>& SeatsForStep =
        bFlexCapsized ? FlexCapsizedSeats : FlexSeats;
    const FRaftSimFlexSeatLoadSolve SeatSolve = RaftSimFlex::SolveSeatLoadCoupledTubeD2(
        State,
        FlexParameters,
        SeatsForStep,
        FlexActions,
        FlexLayout,
        Mode);

    // D3: sample the live water field at every deformed tube segment. The
    // explicit uniform descriptor remains a deterministic fixture override;
    // capsized loading is always dry so an open floor cannot retain deck water.
    FRaftSimFlexUniformWater Water;
    Water.bWet = false;
    const TMap<FString, FRaftSimFlexUniformWater>* WaterBySegment = nullptr;
    int32 LiveWaterSampleCount = 0;
    int32 LiveWetSampleCount = 0;
    const bool bUseUniformOverride =
        bFlexUniformWaterOverrideEnabled && !bFlexCapsized;
    if (bUseUniformOverride)
    {
        Water = FlexWater;
    }
    else if (!bFlexCapsized && FlexibleWaterFieldSampler)
    {
        LiveWaterBySegmentScratch.Reset();
        for (const FRaftSimFlexSegmentResponse& Response :
             SeatSolve.TubeSolve.SegmentResponses)
        {
            FRaftSimFlexUniformWater SegmentWater;
            SegmentWater.bWet = false;
            const FVector WorldPositionCm =
                State.WorldPoint(Response.LocalPosition) * 100.0;
            if (!FlexibleWaterFieldSampler(WorldPositionCm, SegmentWater))
            {
                continue;
            }
            ++LiveWaterSampleCount;
            LiveWetSampleCount += SegmentWater.bWet ? 1 : 0;
            LiveWaterBySegmentScratch.Add(Response.SegmentId, SegmentWater);
        }
        WaterBySegment = &LiveWaterBySegmentScratch;
    }
    if (bFlexCapsized)
    {
        Water.bWet = false;
    }
    const FRaftSimFlexOverwashSolve Overwash = RaftSimFlex::EvaluateOverwashFlipD3(
        SeatSolve,
        Water,
        FlexLayout,
        &RetainedVolumeBySegment,
        Dt,
        // The production tube top is one current pressure-scaled radius above
        // its segment center. The 0.16 m reference default remains available
        // to D6 fixtures, but using it here placed normal loaded equilibrium
        // below the overtopping plane in any moving current.
        /*BaseTubeTopFreeboardM=*/FlexParameters.TubeRadiusM *
            FMath::Lerp(0.82, 1.0, static_cast<double>(FlexPressureFraction)),
        /*FluxCoefficient=*/0.65,
        /*DrainageRatePerS=*/0.55,
        /*WaterDensityKgM3=*/1000.0,
        /*GravityMps2=*/9.81,
        WaterBySegment,
        // Bound reduced-model feedback to the supported South Fork flow
        // envelope and the finite interior volume of a self-bailing paddle
        // raft. These are production coupling limits, not D6 fixture changes.
        /*MaximumIncomingSpeedMps=*/8.0,
        /*MaximumOvertoppingDepthM=*/2.0 * FlexParameters.TubeRadiusM,
        /*MaximumRetainedVolumePerSegmentM3=*/0.05);

    // D4: rock contact, wrap, pin, release, and shape recovery.
    const FRaftSimFlexRockContactSolve Contacts = RaftSimFlex::EvaluateRockContactWrapPinD4(
        SeatSolve,
        FlexObstacles,
        FlexLayout,
        FlexParameters.TubeRadiusM * FMath::Lerp(0.82, 1.0, static_cast<double>(FlexPressureFraction)),
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

    // Export the visible shape from the exact D1-D4 result. Multiple contacts
    // can affect one segment; retain the deepest contact and OR the discrete
    // wrap/pin/recovery states so the rendered tube never understates the
    // authoritative contact outcome.
    LastFlexVisualSegments.Reset(FlexLayout.Num());
    TMap<FString, int32> VisualIndexById;
    for (const FRaftSimFlexSegmentResponse& Response : SeatSolve.TubeSolve.SegmentResponses)
    {
        FRaftSimFlexVisualSegmentState Visual;
        Visual.SegmentId = Response.SegmentId;
        Visual.LocalPositionM = Response.LocalPosition;
        Visual.CompressionM = Response.CompressionM;
        Visual.FreeboardLossM = Response.FreeboardLossM;
        const FString SegmentId = Visual.SegmentId;
        const int32 VisualIndex = LastFlexVisualSegments.Add(MoveTemp(Visual));
        VisualIndexById.Add(SegmentId, VisualIndex);
    }
    for (const FRaftSimFlexRockContact& Contact : Contacts.Contacts)
    {
        const int32* FoundIndex = VisualIndexById.Find(Contact.SegmentId);
        if (FoundIndex == nullptr || !LastFlexVisualSegments.IsValidIndex(*FoundIndex))
        {
            continue;
        }
        FRaftSimFlexVisualSegmentState& Visual = LastFlexVisualSegments[*FoundIndex];
        if (Contact.IndentationM >= Visual.IndentationM)
        {
            Visual.IndentationM = Contact.IndentationM;
            Visual.ContactNormalLocal = Contact.ContactNormalLocal;
        }
        Visual.bWrapping |= Contact.bWrapping;
        Visual.bPinned |= Contact.bPinned;
        Visual.bRecovering |= Contact.bRecovering;
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
    const FVector Inertia(
        FMath::Max(static_cast<double>(RaftConfig.InertiaTensorKgM2.X), 1.0e-3),
        FMath::Max(static_cast<double>(RaftConfig.InertiaTensorKgM2.Y), 1.0e-3),
        FMath::Max(static_cast<double>(RaftConfig.InertiaTensorKgM2.Z), 1.0e-3));

    // Buoyancy support stage (ported from the P1 actor integrator): gravity,
    // multi-point tube buoyancy against the live water surface, quadratic
    // drag, and heave damping. Engaged when the bridge has bound a water
    // sampler; forces are evaluated from the pre-impulse state, exactly as
    // the actor's integrator did.
    double SubmergedFraction = 0.0;
    const bool bSupportStage = static_cast<bool>(WaterSurfaceSampler) && TubeSamplePointsM.Num() > 0;
    if (bSupportStage)
    {
        const double WeightN = MassKg * kSupportGravityMps2;
        ForceN.Z += -WeightN;
        const double PerPointBuoyancyN =
            WeightN * static_cast<double>(RaftConfig.BuoyancyWeightMultiple) /
            static_cast<double>(TubeSamplePointsM.Num()) *
            FMath::Lerp(0.48, 1.0, static_cast<double>(FlexPressureFraction)) *
            FMath::Lerp(0.80, 1.0, static_cast<double>(FlexFabricIntegrity));
        const double SaturationDepthM =
            FMath::Max(2.0 * static_cast<double>(RaftConfig.TubeRadiusMeters), 1.0e-3);
        LastDrySupportPointCount = 0;
        float CenterSurfaceZCm = 0.0f;
        const bool bCenterWet =
            WaterSurfaceSampler(State.Position * 100.0, CenterSurfaceZCm);
        if (bCenterWet)
        {
            LastWetCenterSurfaceZCm = CenterSurfaceZCm;
            bHasLastWetCenterSurface = true;
        }
        for (const FVector& LocalM : TubeSamplePointsM)
        {
            const FVector WorldOffset = State.Orientation.RotateVector(LocalM);
            const FVector WorldPointM = State.Position + WorldOffset;
            float SurfaceZCm = 0.0f;
            if (!WaterSurfaceSampler(WorldPointM * 100.0, SurfaceZCm))
            {
                ++LastDrySupportPointCount;
                if (!bHasLastWetCenterSurface)
                {
                    // Never been in water (spawn on land): nothing to hold.
                    continue;
                }
                // Masked-dry cell under a tube point — a boulder patch or
                // bar in the cooked wet mask, which has no collision actor
                // of its own. Support the point at the current (or, when
                // the whole hull is over the patch, the last) wet centre
                // surface so the raft grounds at the waterline instead of
                // falling through the hole in the mask. Drift telemetry
                // 2026-08-10: dry_points 1->3 sank the hull 1.2 m, and the
                // wider patch at station ~240 dropped it 2.3 m once the
                // centre went dry — the playtest's "a hole opened in the
                // water and the boat sank".
                SurfaceZCm = bCenterWet ? CenterSurfaceZCm : LastWetCenterSurfaceZCm;
            }
            const double SubmersionM = static_cast<double>(SurfaceZCm) / 100.0 - WorldPointM.Z;
            const double Saturation = FMath::Clamp(SubmersionM / SaturationDepthM, 0.0, 1.0);
            if (Saturation <= 0.0)
            {
                continue;
            }
            SubmergedFraction += Saturation / static_cast<double>(TubeSamplePointsM.Num());
            const FVector PointForceN(0.0, 0.0, PerPointBuoyancyN * Saturation);
            ForceN += PointForceN;
            TorqueNm += FVector::CrossProduct(WorldOffset, PointForceN);
        }

        // Quadratic water drag opposing velocity RELATIVE TO THE CURRENT,
        // scaled by submersion. The former term opposed absolute velocity —
        // identical in still water (every tank test passed) but structurally
        // wrong in a river: a raft at rest in a current received zero
        // horizontal force and could never be carried downstream (measured
        // 2026-08-10 at Chili Bar: water 0.63-0.79 m/s at the hull, raft
        // 0.001 m/s after two minutes free).
        FVector WaterVelocityMps = FVector::ZeroVector;
        if (FlexibleWaterFieldSampler)
        {
            FRaftSimFlexUniformWater CenterWater;
            if (FlexibleWaterFieldSampler(State.Position * 100.0, CenterWater) &&
                CenterWater.bWet)
            {
                WaterVelocityMps = CenterWater.VelocityMps;
            }
        }
        const FVector RelativeVelocity = State.LinearVelocity - WaterVelocityMps;
        const double RelativeSpeed = RelativeVelocity.Length();
        if (RelativeSpeed > KINDA_SMALL_NUMBER && SubmergedFraction > 0.0)
        {
            ForceN += RelativeVelocity *
                      (-static_cast<double>(RaftConfig.LinearDragCoefficient) *
                       SubmergedFraction * RelativeSpeed);
        }

        // Linear heave damping: quadratic drag alone is negligible at bobbing
        // speeds, leaving the buoyancy spring underdamped.
        if (SubmergedFraction > 0.0)
        {
            ForceN.Z += -static_cast<double>(RaftConfig.HeaveDampingNsPerM) *
                        SubmergedFraction * State.LinearVelocity.Z;
        }
    }

    // External (paddle) impulses queued since the last substep.
    State.LinearVelocity += PendingLinearImpulseNs / MassKg;
    State.AngularVelocity += FVector(
        PendingAngularImpulseNms.X / Inertia.X,
        PendingAngularImpulseNms.Y / Inertia.Y,
        PendingAngularImpulseNms.Z / Inertia.Z);
    PendingLinearImpulseNs = FVector::ZeroVector;
    PendingAngularImpulseNms = FVector::ZeroVector;

    const FVector LinearAcceleration = ForceN / MassKg;
    const FVector AngularAcceleration(
        TorqueNm.X / Inertia.X,
        TorqueNm.Y / Inertia.Y,
        TorqueNm.Z / Inertia.Z);

    // Semi-implicit fixed-step update (RaftState6DoF.advance semantics).
    State.LinearVelocity += LinearAcceleration * Dt;
    State.AngularVelocity += AngularAcceleration * Dt;
    if (bSupportStage)
    {
        State.AngularVelocity *= FMath::Clamp(
            1.0 - static_cast<double>(RaftConfig.AngularDampingPerSecond) * Dt, 0.0, 1.0);
    }
    State.Position += State.LinearVelocity * Dt;
    const double AngularSpeed = State.AngularVelocity.Length();
    if (AngularSpeed > 1.0e-12)
    {
        const FQuat Delta(State.AngularVelocity / AngularSpeed, AngularSpeed * Dt);
        State.Orientation = (Delta * State.Orientation).GetNormalized();
    }

    // Renderer-facing safety boundary: extreme coupled contact must never
    // publish a non-finite transform. Preserve the last finite pose and shed
    // poisoned velocity; telemetry still exposes the provoking contact.
    const double OrientationSizeSquared = State.Orientation.SizeSquared();
    const bool bInvalidState = State.Position.ContainsNaN() ||
        State.LinearVelocity.ContainsNaN() || State.AngularVelocity.ContainsNaN() ||
        State.Orientation.ContainsNaN() || !FMath::IsFinite(OrientationSizeSquared) ||
        OrientationSizeSquared < 1.0e-8;
    if (bInvalidState)
    {
        State = PreviousFiniteState;
        State.LinearVelocity = FVector::ZeroVector;
        State.AngularVelocity = FVector::ZeroVector;
        const double PreviousOrientationSizeSquared = State.Orientation.SizeSquared();
        if (State.Orientation.ContainsNaN() || !FMath::IsFinite(PreviousOrientationSizeSquared) ||
            PreviousOrientationSizeSquared < 1.0e-8)
        {
            State.Orientation = FQuat::Identity;
        }
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
    LastFlexStepTelemetry.bUsedLiveWaterField = WaterBySegment != nullptr;
    LastFlexStepTelemetry.bUsedUniformWaterOverride = bUseUniformOverride;
    LastFlexStepTelemetry.LiveWaterSampleCount = LiveWaterSampleCount;
    LastFlexStepTelemetry.LiveWetSampleCount = LiveWetSampleCount;
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
