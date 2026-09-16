#pragma once
#include "RaftSimDetailSampleGrid.h"

// Exact native queries needed before a detail update/remap. Do not replace
// missing source cells with clamped edges or a raft-only safety radius.
struct FRaftSimDetailSourceFootprint
{
    static bool Required(FVector2f CurrentOrigin,FVector2f NextOrigin,int32 SampleSide,FBox2D& Out)
    {
        Out=FBox2D(ForceInit);
        if(SampleSide!=67 && SampleSide!=69)return false;
        FRaftSimDetailSampleGrid Current,Next;
        if(!Current.Register(CurrentOrigin) || !Next.Register(NextOrigin))return false;
        const double Halo=(SampleSide-65)/2;
        const auto Include=[&](const FRaftSimDetailSampleGrid& Grid)
        {
            const FVector2D Origin(Grid.CoarseOriginMeters);
            Out+=Origin-FVector2D(Halo);
            Out+=Origin+FVector2D(64.+Halo);
        };
        Include(Next);
        // Same overlap condition as the nonlinear closing-window observation.
        // A teleport has no overlapping history and needs only the new source.
        const FVector2f Shift=(NextOrigin-CurrentOrigin)/.5f;
        if(FMath::Abs(Shift.X)<128 && FMath::Abs(Shift.Y)<128)Include(Current);
        return Out.bIsValid;
    }

    static bool Covered(const FBox2D& Field,const FBox2D& Required)
    {
        return Field.bIsValid && Required.bIsValid &&
            Field.IsInsideOrOn(Required.Min) && Field.IsInsideOrOn(Required.Max);
    }
};
