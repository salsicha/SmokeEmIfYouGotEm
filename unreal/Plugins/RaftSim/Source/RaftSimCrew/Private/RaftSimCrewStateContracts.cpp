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
