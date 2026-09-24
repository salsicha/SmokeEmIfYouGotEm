#pragma once

#include "CoreMinimal.h"
#include "RaftSimFlexibleRaftModel.h"

// Shared normal-scene anchors, in raft-local centimetres. These are the
// existing authored seating layout, not measured human centres of mass.
namespace RaftSimCrewSeatLayout
{
inline FVector AnchorCm(int32 PassengerIndex, bool bGuide, bool bLeftHandedGuide)
{
    if (bGuide) return FVector(-155., bLeftHandedGuide ? -62. : 62., 30.);
    return FVector(115. - (PassengerIndex / 2) * 105.,
        PassengerIndex % 2 == 0 ? -62. : 62., 22.);
}

inline TArray<FRaftSimFlexCrewSeat> BuildNormalSeats(
    const FRaftSimFlexParameters& Parameters, bool bLeftHandedGuide)
{
    // Leave the Python/D6 reference builder unchanged. Normal play shares the
    // rendered anchors in XY, retaining the existing inferred vertical load
    // height until an articulated-body COM model is qualified.
    auto Seats = RaftSimFlex::BuildDefaultCrewSeats(Parameters);
    for (int32 Index = 0; Index < Seats.Num(); ++Index)
    {
        const FVector Anchor = AnchorCm(Index - 1, Index == 0, bLeftHandedGuide) * .01;
        Seats[Index].LocalPosition.X = Anchor.X;
        Seats[Index].LocalPosition.Y = Anchor.Y;
    }
    return Seats;
}
}
