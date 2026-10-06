#pragma once
#include "CoreMinimal.h"

// Read-only pre-projection evidence. Coordinates/poses are world centimetres;
// the support offset/radius/correction use metres as in the selected solver.
struct FRaftSimGroundContactObservation
{
    FTransform PreviousPoseCm,PredictedPoseCm;
    FVector LocalSupportMeters,VelocityBeforeProjectionMps,ContactNormal;
    double RadiusMeters=0,GroundZCm=0,VerticalCorrectionMeters=0;
    double SubstepSeconds=0,MassKg=0;
};
