#pragma once
#include "RaftSimWaterRuntimeAdapter.h"

namespace RaftSimBreakingHeightKey
{
// Identity of the HEIGHT query only, not the separately refreshed foam source.
// Keep every geometric input, site order and legacy intensity. Physical sites
// already store their final amplitude in PhysicalCrestHeightMeters; their
// Intensity and all SpillingFraction values are not read by the height query.
inline TArray<double> Build(TConstArrayView<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites,
    float Lift,float Spacing,float Scale,float Sign)
{
    TArray<double> Key={Lift,Spacing,Scale,Sign};
    Key.Reserve(4+8*Sites.Num());
    for(const auto& Site:Sites)
        Key.Append({Site.RiverCoordinatesMeters.X,Site.RiverCoordinatesMeters.Y,
            Site.PhysicalCrestHeightMeters,Site.PhysicalCrestLengthMeters,
            Site.PhysicalCrestHeightMeters>=0.f ? 0. : double(Site.Intensity),
            Site.FlowDirection.X,Site.FlowDirection.Y,Site.bLocalEnvelopeCap ? 1. : 0.});
    return Key;
}
}
