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
