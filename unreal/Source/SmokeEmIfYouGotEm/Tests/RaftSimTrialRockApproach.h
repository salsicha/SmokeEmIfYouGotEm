#pragma once
#include "CoreMinimal.h"

// Test-driver decisions using normal controls, never collision geometry.
// The owner's inferred wake radius is deliberately not a clearance radius.
namespace RaftSimTrialRockApproach
{
inline bool IsLocalizedOwner(bool DedicatedRockActor,const FString& MeshName)
{
    // A solver-dry island can be part of a large terrain tile. Component
    // impulses elsewhere on that tile cannot prove contact with this rock.
    return DedicatedRockActor || MeshName==TEXT("SM_CapturedRockEnvelope") ||
        MeshName==TEXT("SM_CapturedRockInferredFlanks");
}
inline bool Eligible(const FVector2D& Boat,const FVector2D& Owner,double Control,double Finish)
{
    return !Boat.ContainsNaN()&&!Owner.ContainsNaN()&&Owner.X>=Boat.X+45. &&
        Owner.X<=Finish-20. && FMath::Abs(Owner.X-Control)<=100.;
}
inline double HeadingOffset(double BoatLateral,double OwnerLateral,const FVector& Tangent,const FVector& Left)
{
    // Positive progress-lateral is left, but geographic maps mirror world Y.
    // Resolve direction in the actual world basis, not by a hard-coded yaw.
    const double A=FMath::DegreesToRadians(80.);
    const FVector Aim=FMath::Cos(A)*Tangent+FMath::Sin(A)*(OwnerLateral<BoatLateral?-1.:1.)*Left;
    return FMath::FindDeltaAngleDegrees(Tangent.Rotation().Yaw,Aim.Rotation().Yaw);
}
inline bool AlignBroadside(const FVector2D& Boat,const FVector2D& Owner)
{
    // Finish the ferry before spending steering authority on orientation.
    return Boat.X>=Owner.X-40. && Boat.X<Owner.X+25. && FMath::Abs(Boat.Y-Owner.Y)<=3.;
}
}
