#pragma once
#include "CoreMinimal.h"
#include "Math/TranslationMatrix.h"

// One frame for the entire published water packet, never one per bank.
// CPU geometry/support remain in component coordinates; only GPU storage moves.
struct FRaftSimWaterRenderFrame
{
    FVector Origin=FVector::ZeroVector;
    FVector3f Store(const FVector& P)const{return FVector3f(Origin==FVector::ZeroVector ? P : P-Origin);}
    FVector Restore(const FVector3f& P)const{return FVector(P)+Origin;}
    FMatrix Transform(const FMatrix& ComponentToWorld)const
    {return Origin==FVector::ZeroVector ? ComponentToWorld : FTranslationMatrix(Origin)*ComponentToWorld;}
    FBoxSphereBounds Bounds(FBoxSphereBounds ComponentBounds)const
    {ComponentBounds.Origin-=Origin;return ComponentBounds;}
};
