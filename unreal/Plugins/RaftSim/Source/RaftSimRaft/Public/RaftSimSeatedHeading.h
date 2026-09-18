#pragma once
#include "CoreMinimal.h"

// Carry the seat's yaw, not its roll/pitch or the water-current heading. Mouse
// input remains an independent offset. A detached/other-camera interval starts
// a new observation, so reboarding cannot replay the boat's intervening turn.
struct FRaftSimSeatedHeading
{
    bool bObserved = false;
    double PreviousYaw = 0.;

    double Advance(double SeatYaw, bool bSeatedView)
    {
        if (!bSeatedView || !FMath::IsFinite(SeatYaw))
        {
            bObserved = false;
            return 0.;
        }
        const double Delta = bObserved ? FMath::FindDeltaAngleDegrees(PreviousYaw, SeatYaw) : 0.;
        PreviousYaw = SeatYaw;
        bObserved = true;
        return Delta;
    }
};
