#pragma once
#include "CoreMinimal.h"

namespace RaftSimPhysicalEddyExposure
{
// The adapter's sample heights have ALREADY subtracted the river datum.
// Physical contact is in Unreal world centimeters. Adding the datum here
// compares incompatible frames and rejects captured rocks on elevated rivers.
inline bool IsExposed(double GroundWorldZCm,double WaterDatumRelativeSurfaceM)
{
    return FMath::IsFinite(GroundWorldZCm) && FMath::IsFinite(WaterDatumRelativeSurfaceM) &&
        GroundWorldZCm>=WaterDatumRelativeSurfaceM*100.;
}
}
