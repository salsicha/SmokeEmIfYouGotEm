#include "RaftSimCrewStateContracts.h"

namespace
{
FVector OffsetForCommand(ERaftSimCrewWeightShiftAction Action, float Intensity)
{
    const float ClampedIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
    switch (Action)
    {
        case ERaftSimCrewWeightShiftAction::Brace:
            return FVector(0.0f, 0.0f, -0.12f * ClampedIntensity);
        case ERaftSimCrewWeightShiftAction::LeanLeft:
            return FVector(0.0f, -0.28f * ClampedIntensity, 0.0f);
        case ERaftSimCrewWeightShiftAction::LeanRight:
            return FVector(0.0f, 0.28f * ClampedIntensity, 0.0f);
        case ERaftSimCrewWeightShiftAction::HighSideLeft:
            return FVector(0.0f, -0.55f * ClampedIntensity, 0.08f * ClampedIntensity);
        case ERaftSimCrewWeightShiftAction::HighSideRight:
            return FVector(0.0f, 0.55f * ClampedIntensity, 0.08f * ClampedIntensity);
        case ERaftSimCrewWeightShiftAction::None:
        case ERaftSimCrewWeightShiftAction::HoldOn:
        case ERaftSimCrewWeightShiftAction::RecoverSeated:
        default:
            return FVector::ZeroVector;
    }
}

const FRaftSimCrewWeightShiftCommand* FindCommandForSeat(
    const TArray<FRaftSimCrewWeightShiftCommand>& Commands,
    FName SeatId
)
{
    return Commands.FindByPredicate(
        [SeatId](const FRaftSimCrewWeightShiftCommand& Command)
        {
            return Command.SeatId == SeatId;
        }
    );
}
}

FRaftSimCrewWeightDistributionFrame URaftSimCrewWeightDistributionLibrary::EvaluateWeightDistribution(
    const TArray<FRaftSimCrewSeatOccupancy>& Seats,
    const TArray<FRaftSimCrewWeightShiftCommand>& Commands
)
{
    FRaftSimCrewWeightDistributionFrame Frame;
    FVector WeightedPosition = FVector::ZeroVector;

    for (const FRaftSimCrewSeatOccupancy& Seat : Seats)
    {
        if (!Seat.bOccupied || Seat.PassengerMassKg <= 0.0f)
        {
            continue;
        }

        FVector AdjustedPosition = Seat.LocalSeatPositionMeters;
        if (const FRaftSimCrewWeightShiftCommand* Command = FindCommandForSeat(Commands, Seat.SeatId))
        {
            AdjustedPosition += OffsetForCommand(Command->Action, Command->NormalizedIntensity);
            switch (Command->Action)
            {
                case ERaftSimCrewWeightShiftAction::Brace:
                    ++Frame.BraceCount;
                    break;
                case ERaftSimCrewWeightShiftAction::LeanLeft:
                case ERaftSimCrewWeightShiftAction::LeanRight:
                    ++Frame.LeanCount;
                    break;
                case ERaftSimCrewWeightShiftAction::HighSideLeft:
                case ERaftSimCrewWeightShiftAction::HighSideRight:
                    ++Frame.HighSideCount;
                    break;
                default:
                    break;
            }
        }

        Frame.TotalMassKg += Seat.PassengerMassKg;
        WeightedPosition += AdjustedPosition * Seat.PassengerMassKg;
    }

    if (Frame.TotalMassKg <= KINDA_SMALL_NUMBER)
    {
        return Frame;
    }

    Frame.CenterOfGravityLocalMeters = WeightedPosition / Frame.TotalMassKg;
    Frame.RollMomentNewtonMeters = Frame.TotalMassKg * 9.81f * Frame.CenterOfGravityLocalMeters.Y;

    const float LateralCog = FMath::Abs(Frame.CenterOfGravityLocalMeters.Y);
    Frame.PinLoadModifier = FMath::Clamp(
        1.0f + 0.04f * Frame.BraceCount - 0.10f * Frame.HighSideCount,
        0.5f,
        1.5f
    );
    Frame.FlipRiskModifier = FMath::Clamp(
        1.0f + LateralCog * 0.25f - 0.08f * Frame.BraceCount - 0.12f * Frame.HighSideCount,
        0.4f,
        1.8f
    );
    Frame.ReleaseAssistModifier = FMath::Clamp(
        1.0f + 0.10f * Frame.LeanCount + 0.15f * Frame.HighSideCount + LateralCog * 0.10f,
        0.5f,
        2.0f
    );

    return Frame;
}

bool URaftSimCrewSafetyStateLibrary::CanTransitionSafetyState(
    ERaftSimCrewSafetyState PreviousState,
    ERaftSimCrewSafetyState NextState
)
{
    if (PreviousState == NextState)
    {
        return true;
    }

    switch (PreviousState)
    {
        case ERaftSimCrewSafetyState::Seated:
            return NextState == ERaftSimCrewSafetyState::AtRisk;
        case ERaftSimCrewSafetyState::AtRisk:
            return (
                NextState == ERaftSimCrewSafetyState::Seated
                || NextState == ERaftSimCrewSafetyState::FallingEjected
            );
        case ERaftSimCrewSafetyState::FallingEjected:
            return NextState == ERaftSimCrewSafetyState::Swimming;
        case ERaftSimCrewSafetyState::Swimming:
            return (
                NextState == ERaftSimCrewSafetyState::RescueTargeted
                || NextState == ERaftSimCrewSafetyState::FailedRescue
            );
        case ERaftSimCrewSafetyState::RescueTargeted:
            return (
                NextState == ERaftSimCrewSafetyState::Rescued
                || NextState == ERaftSimCrewSafetyState::FailedRescue
            );
        case ERaftSimCrewSafetyState::Rescued:
            return NextState == ERaftSimCrewSafetyState::ReseatedRecovered;
        case ERaftSimCrewSafetyState::ReseatedRecovered:
            return NextState == ERaftSimCrewSafetyState::Seated;
        case ERaftSimCrewSafetyState::FailedRescue:
        default:
            return false;
    }
}

FRaftSimCrewSafetyStateFrame URaftSimCrewSafetyStateLibrary::ApplySafetyTransition(
    const FRaftSimCrewSafetyStateFrame& CurrentFrame,
    const FRaftSimCrewSafetyTransition& Transition
)
{
    FRaftSimCrewSafetyStateFrame NextFrame = CurrentFrame;
    if (!CanTransitionSafetyState(Transition.PreviousState, Transition.NextState))
    {
        return NextFrame;
    }

    NextFrame.CurrentState = Transition.NextState;
    NextFrame.TimeInStateSeconds = 0.0f;
    if (Transition.NextState == ERaftSimCrewSafetyState::Swimming)
    {
        NextFrame.TimeInWaterSeconds = 0.0f;
    }
    if (Transition.NextState == ERaftSimCrewSafetyState::FailedRescue)
    {
        NextFrame.FailedRescueReason = Transition.TransitionReason;
    }
    return NextFrame;
}

FRaftSimSwimmingSkillProfile URaftSimSwimmingSkillLibrary::MakeSwimmingSkillProfile(
    ERaftSimSwimmingSkillLevel SkillLevel
)
{
    FRaftSimSwimmingSkillProfile Profile;
    Profile.SkillLevel = SkillLevel;

    switch (SkillLevel)
    {
        case ERaftSimSwimmingSkillLevel::NonSwimmer:
            Profile.bSelfRescueAllowed = false;
            Profile.PanicScalar = 1.0f;
            Profile.RescuePriority = 1.0f;
            Profile.PullInDifficulty = 1.2f;
            Profile.TimeToCriticalSeconds = 8.0f;
            break;
        case ERaftSimSwimmingSkillLevel::WeakSwimmer:
            Profile.bSelfRescueAllowed = true;
            Profile.PanicScalar = 0.75f;
            Profile.RescuePriority = 0.8f;
            Profile.PullInDifficulty = 1.05f;
            Profile.TimeToCriticalSeconds = 14.0f;
            break;
        case ERaftSimSwimmingSkillLevel::StrongSwimmer:
            Profile.bSelfRescueAllowed = true;
            Profile.PanicScalar = 0.25f;
            Profile.RescuePriority = 0.35f;
            Profile.PullInDifficulty = 0.75f;
            Profile.TimeToCriticalSeconds = 32.0f;
            break;
        case ERaftSimSwimmingSkillLevel::AverageSwimmer:
        default:
            Profile.bSelfRescueAllowed = true;
            Profile.PanicScalar = 0.45f;
            Profile.RescuePriority = 0.55f;
            Profile.PullInDifficulty = 0.9f;
            Profile.TimeToCriticalSeconds = 22.0f;
            break;
    }

    return Profile;
}

FRaftSimPassengerSwimmingSkillAssignment URaftSimSwimmingSkillLibrary::AssignSwimmingSkillFromNormalizedValue(
    FName PassengerId,
    FName SeatId,
    float NormalizedValue,
    int32 AssignmentSeed,
    bool bAssignedFromRoster
)
{
    const float Roll = FMath::Clamp(NormalizedValue, 0.0f, 1.0f);
    ERaftSimSwimmingSkillLevel SkillLevel = ERaftSimSwimmingSkillLevel::StrongSwimmer;
    if (Roll < 0.15f)
    {
        SkillLevel = ERaftSimSwimmingSkillLevel::NonSwimmer;
    }
    else if (Roll < 0.40f)
    {
        SkillLevel = ERaftSimSwimmingSkillLevel::WeakSwimmer;
    }
    else if (Roll < 0.85f)
    {
        SkillLevel = ERaftSimSwimmingSkillLevel::AverageSwimmer;
    }

    FRaftSimPassengerSwimmingSkillAssignment Assignment;
    Assignment.PassengerId = PassengerId;
    Assignment.SeatId = SeatId;
    Assignment.bAssignedFromRoster = bAssignedFromRoster;
    Assignment.AssignmentSeed = AssignmentSeed;
    Assignment.Profile = MakeSwimmingSkillProfile(SkillLevel);
    return Assignment;
}

namespace
{
float MaxDistanceForRescueMethod(ERaftSimRescueMethod Method, bool bThrowLineAvailable)
{
    switch (Method)
    {
        case ERaftSimRescueMethod::ReachGrab:
            return 1.2f;
        case ERaftSimRescueMethod::PaddleGrab:
            return 2.0f;
        case ERaftSimRescueMethod::ThrowLine:
            return bThrowLineAvailable ? 8.0f : 0.0f;
        case ERaftSimRescueMethod::None:
        default:
            return 0.0f;
    }
}

float PullInSecondsForRescueMethod(ERaftSimRescueMethod Method)
{
    switch (Method)
    {
        case ERaftSimRescueMethod::ReachGrab:
            return 2.5f;
        case ERaftSimRescueMethod::PaddleGrab:
            return 3.5f;
        case ERaftSimRescueMethod::ThrowLine:
            return 6.0f;
        case ERaftSimRescueMethod::None:
        default:
            return 1000000.0f;
    }
}

float AimThresholdForRescueMethod(ERaftSimRescueMethod Method)
{
    switch (Method)
    {
        case ERaftSimRescueMethod::ReachGrab:
            return 0.45f;
        case ERaftSimRescueMethod::PaddleGrab:
            return 0.60f;
        case ERaftSimRescueMethod::ThrowLine:
            return 0.82f;
        case ERaftSimRescueMethod::None:
        default:
            return 1.0f;
    }
}
}

FRaftSimSwimmerRescueFrame URaftSimSwimmerRescueLibrary::IntegrateSwimmerDrift(
    const FRaftSimSwimmerRescueFrame& CurrentFrame,
    FVector WaterVelocityMetersPerSecond,
    float DeltaSeconds
)
{
    FRaftSimSwimmerRescueFrame NextFrame = CurrentFrame;
    const float StepSeconds = FMath::Max(DeltaSeconds, 0.0f);
    NextFrame.SwimmerDriftVelocityMetersPerSecond = WaterVelocityMetersPerSecond;
    NextFrame.SwimmerWorldPositionMeters += WaterVelocityMetersPerSecond * StepSeconds;
    NextFrame.TimeInWaterSeconds += StepSeconds;
    NextFrame.VisibilityScore = FMath::Clamp(
        CurrentFrame.VisibilityScore - 0.015f * StepSeconds,
        0.0f,
        1.0f
    );
    NextFrame.CalloutPriority = FMath::Clamp(
        CurrentFrame.CalloutPriority + 0.04f * StepSeconds,
        0.0f,
        1.0f
    );
    return NextFrame;
}

FRaftSimSwimmerRescueFrame URaftSimSwimmerRescueLibrary::EvaluateRescueAttempt(
    const FRaftSimSwimmerRescueFrame& CurrentFrame,
    const FRaftSimRescueAttempt& Attempt,
    const FRaftSimSwimmingSkillProfile& SkillProfile
)
{
    FRaftSimSwimmerRescueFrame NextFrame = CurrentFrame;
    NextFrame.RescueMethod = Attempt.Method;
    NextFrame.bThrowLineAvailable = Attempt.bThrowLineAvailable;
    NextFrame.TimeInWaterSeconds = Attempt.TimeInWaterSeconds;

    const float MaxDistance = MaxDistanceForRescueMethod(Attempt.Method, Attempt.bThrowLineAvailable);
    const bool bInsideDistance = Attempt.DistanceMeters <= MaxDistance;
    const bool bInsideWindow = Attempt.TimeInWaterSeconds <= SkillProfile.TimeToCriticalSeconds;
    if (bInsideDistance && bInsideWindow)
    {
        const float PullInSeconds = PullInSecondsForRescueMethod(Attempt.Method);
        NextFrame.PullInProgress = FMath::Clamp(
            CurrentFrame.PullInProgress + 1.0f / FMath::Max(PullInSeconds, KINDA_SMALL_NUMBER),
            0.0f,
            1.0f
        );
        NextFrame.FatigueDelta = 0.08f;
        NextFrame.TrustDelta = 0.08f;
        NextFrame.FailedRescueReason = NAME_None;
        return NextFrame;
    }

    NextFrame.PullInProgress = 0.0f;
    NextFrame.FatigueDelta = 0.35f;
    NextFrame.TrustDelta = -0.25f;
    NextFrame.FailedRescueReason = bInsideDistance
        ? FName(TEXT("time_to_critical_exceeded"))
        : FName(TEXT("out_of_reach"));
    return NextFrame;
}

FRaftSimRescueInteractionState URaftSimSwimmerRescueLibrary::BeginRescueInteraction(
    FName TargetPassengerId,
    ERaftSimRescueMethod Method,
    FVector LineStartWorldMeters,
    FVector TargetWorldMeters,
    FVector AimDirection,
    bool bThrowLineAvailable,
    float TimeInWaterSeconds,
    const FRaftSimSwimmingSkillProfile& SkillProfile
)
{
    FRaftSimRescueInteractionState State;
    State.TargetPassengerId = TargetPassengerId;
    State.Method = Method;
    State.LineStartWorldMeters = LineStartWorldMeters;
    State.LineEndWorldMeters = TargetWorldMeters;
    const FVector ToTarget = TargetWorldMeters - LineStartWorldMeters;
    State.DistanceMeters = ToTarget.Size();
    const FVector SafeAim = AimDirection.GetSafeNormal();
    State.AimAlignment = SafeAim.IsNearlyZero() || ToTarget.IsNearlyZero()
        ? 0.0f
        : FVector::DotProduct(SafeAim, ToTarget.GetSafeNormal());

    const float MaxDistance = MaxDistanceForRescueMethod(Method, bThrowLineAvailable);
    if (TargetPassengerId.IsNone() || Method == ERaftSimRescueMethod::None)
    {
        State.Phase = ERaftSimRescueInteractionPhase::Failed;
        State.FeedbackCode = TEXT("rescue_no_target");
    }
    else if (TimeInWaterSeconds > SkillProfile.TimeToCriticalSeconds)
    {
        State.Phase = ERaftSimRescueInteractionPhase::Failed;
        State.FeedbackCode = TEXT("rescue_window_expired");
    }
    else if (State.DistanceMeters > MaxDistance)
    {
        State.Phase = ERaftSimRescueInteractionPhase::Failed;
        State.FeedbackCode = TEXT("rescue_out_of_range");
    }
    else if (State.AimAlignment < AimThresholdForRescueMethod(Method))
    {
        State.Phase = ERaftSimRescueInteractionPhase::Aiming;
        State.FeedbackCode = TEXT("rescue_adjust_aim");
    }
    else
    {
        State.Phase = Method == ERaftSimRescueMethod::ThrowLine
            ? ERaftSimRescueInteractionPhase::LineInFlight
            : ERaftSimRescueInteractionPhase::Pulling;
        State.bLineVisible = Method == ERaftSimRescueMethod::ThrowLine;
        State.FeedbackCode = Method == ERaftSimRescueMethod::ThrowLine
            ? FName(TEXT("rescue_line_thrown"))
            : FName(TEXT("rescue_contact"));
    }
    return State;
}

FRaftSimRescueInteractionState URaftSimSwimmerRescueLibrary::AdvanceRescueInteraction(
    const FRaftSimRescueInteractionState& CurrentState,
    FVector LineStartWorldMeters,
    FVector TargetWorldMeters,
    float DeltaSeconds
)
{
    FRaftSimRescueInteractionState State = CurrentState;
    const float Step = FMath::Clamp(DeltaSeconds, 0.0f, 0.25f);
    State.LineStartWorldMeters = LineStartWorldMeters;
    State.LineEndWorldMeters = TargetWorldMeters;
    State.DistanceMeters = FVector::Distance(LineStartWorldMeters, TargetWorldMeters);
    State.PhaseElapsedSeconds += Step;

    if (State.Phase == ERaftSimRescueInteractionPhase::LineInFlight)
    {
        State.bLineVisible = true;
        if (State.PhaseElapsedSeconds >= 0.45f)
        {
            State.Phase = ERaftSimRescueInteractionPhase::Pulling;
            State.PhaseElapsedSeconds = 0.0f;
            State.FeedbackCode = TEXT("rescue_line_connected");
        }
        return State;
    }
    if (State.Phase != ERaftSimRescueInteractionPhase::Pulling)
    {
        return State;
    }

    const float PullSeconds = PullInSecondsForRescueMethod(State.Method);
    State.PullProgress = FMath::Clamp(
        State.PullProgress + Step / FMath::Max(PullSeconds, KINDA_SMALL_NUMBER),
        0.0f,
        1.0f);
    State.bLineVisible = State.Method == ERaftSimRescueMethod::ThrowLine;
    if (State.PullProgress >= 1.0f)
    {
        State.Phase = ERaftSimRescueInteractionPhase::ReadyForReentry;
        State.PhaseElapsedSeconds = 0.0f;
        State.FeedbackCode = TEXT("rescue_ready_reentry");
    }
    else
    {
        State.FeedbackCode = TEXT("rescue_pulling");
    }
    return State;
}

FRaftSimRescueInteractionState URaftSimSwimmerRescueLibrary::CompleteReseat(
    const FRaftSimRescueInteractionState& CurrentState,
    float DistanceToRaftMeters
)
{
    FRaftSimRescueInteractionState State = CurrentState;
    if (State.Phase != ERaftSimRescueInteractionPhase::ReadyForReentry)
    {
        State.FeedbackCode = TEXT("rescue_not_ready");
        return State;
    }
    if (DistanceToRaftMeters > 1.35f)
    {
        State.FeedbackCode = TEXT("rescue_bring_to_tube");
        return State;
    }
    State.Phase = ERaftSimRescueInteractionPhase::Completed;
    State.PullProgress = 1.0f;
    State.bLineVisible = false;
    State.FeedbackCode = TEXT("rescue_reseated");
    return State;
}

FRaftSimGameplayScoreBreakdown URaftSimGameplayScoringLibrary::EvaluateGameplayScore(
    const FRaftSimGameplayScoringSignals& Signals
)
{
    FRaftSimGameplayScoreBreakdown Score;
    Score.SafetyScore = FMath::Clamp(
        1.0f - 0.18f * Signals.SafetyIncidentCount - 0.45f * Signals.FailedRescueCount,
        0.0f,
        1.0f
    );
    Score.LineChoiceScore = FMath::Clamp(Signals.CleanLineRatio, 0.0f, 1.0f);
    Score.BoatAngleScore = FMath::Clamp(
        1.0f - Signals.MeanBoatAngleErrorDegrees / 90.0f,
        0.0f,
        1.0f
    );
    Score.PaddleEfficiencyScore = FMath::Clamp(Signals.UsefulPaddleImpulseRatio, 0.0f, 1.0f);
    Score.CommandTimingScore = FMath::Clamp(
        1.0f - Signals.MeanCommandLatencySeconds / 3.0f,
        0.0f,
        1.0f
    );
    Score.HighSideBraceTimingScore = FMath::Clamp(
        1.0f - Signals.HighSideBraceTimingErrorSeconds / 2.0f,
        0.0f,
        1.0f
    );
    Score.SwimRescueScore = FMath::Clamp(
        1.0f - 0.18f * Signals.SwimCount - Signals.TimeInWaterSeconds / 90.0f - Signals.CrewRecoverySeconds / 120.0f,
        0.0f,
        1.0f
    );

    Score.TotalScore =
        0.30f * Score.SafetyScore
        + 0.18f * Score.LineChoiceScore
        + 0.14f * Score.BoatAngleScore
        + 0.12f * Score.PaddleEfficiencyScore
        + 0.10f * Score.CommandTimingScore
        + 0.08f * Score.HighSideBraceTimingScore
        + 0.08f * Score.SwimRescueScore;
    return Score;
}
