#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "RaftSimRunCoordinateProvider.generated.h"

class URaftSimWaterRuntimeAdapter;
class UWorld;

/** Read-only access to the scenario's authored downstream axis. Hydraulic
 * Cartesian east/north must never be interpreted as downstream/river-left. */
UINTERFACE(MinimalAPI, meta = (CannotImplementInterfaceInBlueprint))
class URaftSimRunCoordinateProvider : public UInterface
{
    GENERATED_BODY()
};

class RAFTSIMRAFT_API IRaftSimRunCoordinateProvider
{
    GENERATED_BODY()
public:
    virtual const URaftSimWaterRuntimeAdapter* GetProgressCoordinates(
        const URaftSimWaterRuntimeAdapter* HydraulicCoordinates) const = 0;
    virtual bool WorldToRunCoordinates(const FVector& WorldPositionCm,
        const URaftSimWaterRuntimeAdapter* HydraulicCoordinates,
        FVector2D& OutStationLateralM, FVector& OutTangent, FVector& OutLeft) const = 0;
};

namespace RaftSimReviewCoordinates
{
    // Invalid or ambiguous scenario providers fail closed. Only worlds without
    // a provider may fall back to a non-Cartesian legacy hydraulic ribbon.
    RAFTSIMRAFT_API const URaftSimWaterRuntimeAdapter* GetMap(UWorld* World,
        const URaftSimWaterRuntimeAdapter* Water);
    RAFTSIMRAFT_API bool WorldToCoordinates(UWorld* World,
        const URaftSimWaterRuntimeAdapter* Water, const FVector& Position,
        FVector2D& OutStationLateralM, FVector& OutTangent, FVector& OutLeft);
    RAFTSIMRAFT_API bool ShorePose(UWorld* World,
        const URaftSimWaterRuntimeAdapter* Water, const FVector& RaftPosition,
        bool bRiverLeft, bool bLow, bool bLegacyHydraulicFrame,
        FVector& OutLocation, FRotator& OutRotation);
}
