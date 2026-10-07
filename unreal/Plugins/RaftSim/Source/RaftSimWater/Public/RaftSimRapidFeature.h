#pragma once
#include "CoreMinimal.h"
#include "RaftSimRapidFeature.generated.h"

/** Authored shared crest/roller, expressed in the bound hydraulic chart. */
USTRUCT()
struct RAFTSIMWATER_API FRaftSimRapidFeature
{
    GENERATED_BODY()
    UPROPERTY() double Station = 0.;
    UPROPERTY() double Lateral = 0.;
    UPROPERTY() double AngleDegrees = 0.;
    UPROPERTY() float Height = 0.f;
    UPROPERTY() float Length = 0.f;
    UPROPERTY() float Spill = 0.f;

    FRaftSimRapidFeature() = default;
    FRaftSimRapidFeature(double S,double Y,double A,float H,float L,float F)
        : Station(S),Lateral(Y),AngleDegrees(A),Height(H),Length(L),Spill(F) {}
};
