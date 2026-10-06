#pragma once
#include "RaftSimFlexibleRaftModel.h"
#include "Engine/HitResult.h"

// Query coordinates/radius are centimetres. Dynamics remain metres/seconds.
using FRaftSimGroundSweep = TFunction<bool(const FVector&,const FVector&,double,FHitResult&)>;

struct FRaftSimSweptContactResult
{
    bool bCompleted=false;
    int32 Impulses=0;
    double ConsumedSeconds=0;
    FString Failure;
};

namespace RaftSimSweptGround
{
RAFTSIMPHYSICS_API void Advance(FRaftSimFlexRigidState& S,double Dt);
RAFTSIMPHYSICS_API bool ApplyNormalImpulse(FRaftSimFlexRigidState& S,const FVector& Local,
    const FVector& Normal,double Mass,const FVector& Inertia);
RAFTSIMPHYSICS_API FRaftSimSweptContactResult Integrate(FRaftSimFlexRigidState& State,
    const FRaftSimFlexRigidState& Previous,const TArray<FVector>& Supports,
    double Radius,double Mass,const FVector& Inertia,double Dt,const FRaftSimGroundSweep& Sweep);
}
