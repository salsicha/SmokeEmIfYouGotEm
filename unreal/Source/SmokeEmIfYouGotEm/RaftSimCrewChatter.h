#pragma once

#include "CoreMinimal.h"
#include "RaftSimRaftActor.h"

/**
 * What the crew say on the river, in their own voices (URaftSimCrewRoster).
 * Watches the raft for the moments people react to — big water, a clean
 * run-out, a swimmer, a rescue, a flip — and picks a line from whoever would
 * speak: the swimmer about their own swim, the nervous first-timer more
 * often in big water, the guide calling the flip. Presentation only; one
 * line at a time with a short gap, important lines queued.
 */
class FRaftSimCrewChatter
{
public:
    /** Advance one frame; true with the "Name: line" text when someone speaks. */
    bool Tick(const ARaftSimRaftActor& Raft, float DeltaSeconds, FText& OutLine);

private:
    void Say(FName PassengerId, const TArray<FText>& Lines, bool bImportant);
    /** A guide's command shout: jumps the queue and plays this frame. */
    void Shout(const FText& Line);
    int32 LastHighSideCount = -1;
    ERaftSimCrewCommand LastCommand = ERaftSimCrewCommand::Rest;
    ERaftSimCrewCommand LastCall = ERaftSimCrewCommand::Rest;
    ERaftSimRescueInteractionPhase LastRescuePhase = ERaftSimRescueInteractionPhase::Idle;
    ERaftSimFlipLinePhase LastFlipPhase = ERaftSimFlipLinePhase::Idle;

    struct FPendingLine
    {
        FText Text;
        bool bImportant = false;
    };
    TArray<FPendingLine> Pending;
    TMap<FName, bool> WasSwimming;
    TMap<FName, bool> WasSpent;
    ERaftSimRaftMode LastMode = ERaftSimRaftMode::Upright;
    FQuat LastRotation = FQuat::Identity;
    bool bHasLastRotation = false;
    float SmoothedTurnRateDegPerS = 0.0f;
    float RoughSeconds = 0.0f;
    float CalmSeconds = 0.0f;
    bool bInBigWater = false;
    float SecondsSinceBigWaterLine = 1000.0f;
    float Cooldown = 2.0f;
    FRandomStream Random{20261001};
};
