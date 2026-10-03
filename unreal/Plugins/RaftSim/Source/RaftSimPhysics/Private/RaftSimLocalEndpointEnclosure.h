#pragma once
#include "CoreMinimal.h"

// Per-query accumulation, never a cached pose or a subset of the hull. Feed
// every original local endpoint while constructing the existing arrays. The
// caller still performs both directions of containment before using a bound
// to prove separation. A finite world coordinate can overflow on subtraction;
// that local refusal must survive even when the source tree is disjoint.
class FRaftSimLocalEndpointEnclosure
{
    FBox EndBounds=FBox(ForceInit);
    bool bFinite=true;
public:
    void Add(const FVector& Start,const FVector& End)
    {
        if(Start.ContainsNaN() || End.ContainsNaN())
        {bFinite=false;return;}
        EndBounds+=End;
    }
    bool Whole(const FBox& InitialBounds,FBox& Out) const
    {
        if(!bFinite || !EndBounds.IsValid)return false;
        Out=InitialBounds;
        Out+=EndBounds;
        return true;
    }
};
