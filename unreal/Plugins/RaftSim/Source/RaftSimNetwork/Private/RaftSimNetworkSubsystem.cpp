#include "RaftSimNetworkSubsystem.h"

void URaftSimNetworkSubsystem::ConfigureSession(const FRaftSimNetworkSessionConfig& InConfig)
{
    SessionState.Config = InConfig;
    SessionState.SeatAssignments.Reset();
    SessionState.RecentTelemetry.Reset();
}

bool URaftSimNetworkSubsystem::AssignSeat(
    const FName& SeatId,
    const FString& PlayerId,
    ERaftSimSeatOccupantKind OccupantKind
)
{
    if (SeatId.IsNone())
    {
        return false;
    }

    for (FRaftSimSeatAssignment& Assignment : SessionState.SeatAssignments)
    {
        if (Assignment.SeatId == SeatId)
        {
            Assignment.PlayerId = PlayerId;
            Assignment.OccupantKind = OccupantKind;
            Assignment.bReady = false;
            return true;
        }
    }

    FRaftSimSeatAssignment NewAssignment;
    NewAssignment.SeatId = SeatId;
    NewAssignment.PlayerId = PlayerId;
    NewAssignment.OccupantKind = OccupantKind;
    SessionState.SeatAssignments.Add(NewAssignment);
    return true;
}

bool URaftSimNetworkSubsystem::SetPlayerReady(const FString& PlayerId, bool bReady)
{
    for (FRaftSimSeatAssignment& Assignment : SessionState.SeatAssignments)
    {
        if (Assignment.PlayerId == PlayerId)
        {
            Assignment.bReady = bReady;
            return true;
        }
    }
    return false;
}

bool URaftSimNetworkSubsystem::ApplyAIFallbackToSeat(const FName& SeatId)
{
    for (FRaftSimSeatAssignment& Assignment : SessionState.SeatAssignments)
    {
        if (Assignment.SeatId == SeatId)
        {
            Assignment.PlayerId.Reset();
            Assignment.OccupantKind = ERaftSimSeatOccupantKind::AIFallback;
            Assignment.bReady = true;
            return true;
        }
    }
    return AssignSeat(SeatId, FString(), ERaftSimSeatOccupantKind::AIFallback);
}

void URaftSimNetworkSubsystem::RecordTelemetryFrame(const FRaftSimNetworkTelemetryFrame& TelemetryFrame)
{
    constexpr int32 MaxTelemetryFrames = 300;
    SessionState.RecentTelemetry.Add(TelemetryFrame);
    if (SessionState.RecentTelemetry.Num() > MaxTelemetryFrames)
    {
        SessionState.RecentTelemetry.RemoveAt(0, SessionState.RecentTelemetry.Num() - MaxTelemetryFrames);
    }
}
