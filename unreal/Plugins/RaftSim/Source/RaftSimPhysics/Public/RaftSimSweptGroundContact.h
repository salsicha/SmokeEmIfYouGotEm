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
inline void Advance(FRaftSimFlexRigidState& S,double Dt)
{
    S.Position+=S.LinearVelocity*Dt;
    const double Speed=S.AngularVelocity.Length();
    if(Speed>1.e-12)
        S.Orientation=(FQuat(S.AngularVelocity/Speed,Speed*Dt)*S.Orientation).GetNormalized();
}

// Uses the selected integrator's world-axis diagonal inertia convention.
// This impulse dissipates contact-normal kinetic energy; no position lift,
// restitution, arbitrary velocity reset or extra source of energy is added.
inline bool ApplyNormalImpulse(FRaftSimFlexRigidState& S,const FVector& Local,
    const FVector& Normal,double Mass,const FVector& Inertia)
{
    const FVector R=S.Orientation.RotateVector(Local);
    const double Closing=FVector::DotProduct(S.PointVelocity(Local),Normal);
    if(Closing>=-1.e-9)return false;
    const FVector Cross=FVector::CrossProduct(R,Normal);
    const FVector InvCross(Cross.X/Inertia.X,Cross.Y/Inertia.Y,Cross.Z/Inertia.Z);
    const double InverseEffectiveMass=1./Mass+FVector::DotProduct(Cross,InvCross);
    const double J=-Closing/InverseEffectiveMass;
    S.LinearVelocity+=Normal*(J/Mass);
    S.AngularVelocity+=InvCross*J;
    return true;
}

// Experimental swept support spheres, not a full continuous hull. Rotation
// is piecewise chord-swept with <=0.005 rad per segment (not exact arc CCD).
// Existing six supports and their radius are unchanged. Any unresolved step
// is reported, never silently handed to the old roof-height projection.
inline FRaftSimSweptContactResult Integrate(FRaftSimFlexRigidState& State,
    const FRaftSimFlexRigidState& Previous,const TArray<FVector>& Supports,
    double Radius,double Mass,const FVector& Inertia,double Dt,const FRaftSimGroundSweep& Sweep)
{
    FRaftSimSweptContactResult Result;
    FRaftSimFlexRigidState Current=State;
    Current.Position=Previous.Position;Current.Orientation=Previous.Orientation;
    double Remaining=Dt;
    for(int32 Iteration=0;Iteration<128 && Remaining>1.e-12;++Iteration)
    {
        const double Segment=FMath::Min(Remaining,.005/FMath::Max(Current.AngularVelocity.Length(),1.e-12));
        auto Predicted=Current;Advance(Predicted,Segment);
        double Earliest=1.;int32 SupportIndex=INDEX_NONE;FHitResult EarliestHit;
        for(int32 I=0;I<Supports.Num();++I)
        {
            FHitResult Hit;
            if(!Sweep(Current.WorldPoint(Supports[I])*100.,Predicted.WorldPoint(Supports[I])*100.,Radius*100.,Hit))continue;
            if(!FMath::IsFinite(Hit.Time) || Hit.Time<0 || Hit.Time>1 || Hit.Normal.ContainsNaN() || Hit.Normal.IsNearlyZero())
            {Result.Failure=TEXT("invalid sweep hit");return Result;}
            if(Hit.bStartPenetrating && Hit.PenetrationDepth>.001)
            {Result.Failure=FString::Printf(TEXT("initial sphere overlap %.9g cm"),double(Hit.PenetrationDepth));return Result;}
            const FVector Normal=Hit.Normal.GetSafeNormal();
            if(Hit.Time<=1.e-7 && FVector::DotProduct(Current.PointVelocity(Supports[I]),Normal)>=-1.e-9)continue;
            if(Hit.Time<=Earliest){Earliest=Hit.Time;SupportIndex=I;EarliestHit=Hit;}
        }
        if(SupportIndex==INDEX_NONE)
        {Current=Predicted;Remaining-=Segment;Result.ConsumedSeconds+=Segment;continue;}
        // FHitResult stores TOI as float. Stop ten micrometres before that
        // rounded boundary, then spend the remaining time with the impulse-
        // corrected velocity. This is an explicit numerical contact skin,
        // not a discarded timestep or a positional depenetration.
        constexpr double ContactSkinM=1.e-5;
        const double PointSpeed=Current.PointVelocity(Supports[SupportIndex]).Length();
        const double AdvanceSeconds=FMath::Max(0.,Segment*Earliest-ContactSkinM/FMath::Max(PointSpeed,1.e-12));
        Advance(Current,AdvanceSeconds);Remaining-=AdvanceSeconds;Result.ConsumedSeconds+=AdvanceSeconds;
        if(ApplyNormalImpulse(Current,Supports[SupportIndex],EarliestHit.Normal.GetSafeNormal(),Mass,Inertia))++Result.Impulses;
        else {Result.Failure=TEXT("non-closing swept hit could not advance");return Result;}
    }
    if(Remaining>1.e-12){Result.Failure=TEXT("contact iteration limit; unconsumed substep");return Result;}
    // Preserve the existing no-collision pose bit-for-bit when one segment
    // sufficed. Subdivided rotation deliberately uses the segmented path.
    if(Result.Impulses || Dt*State.AngularVelocity.Length()>.005)State=Current;
    Result.bCompleted=true;
    return Result;
}
}
