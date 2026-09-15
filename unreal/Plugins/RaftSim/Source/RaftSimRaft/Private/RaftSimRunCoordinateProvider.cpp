#include "RaftSimRunCoordinateProvider.h"
#include "EngineUtils.h"
#include "RaftSimWaterRuntimeAdapter.h"

namespace
{
bool FindProvider(UWorld* World, IRaftSimRunCoordinateProvider*& OutProvider)
{
    OutProvider = nullptr;
    if (!World) return false;
    for (TActorIterator<AActor> It(World); It; ++It)
        if (auto* Provider = Cast<IRaftSimRunCoordinateProvider>(*It))
        {
            if (OutProvider) return false; // Never depend on actor iteration order.
            OutProvider = Provider;
        }
    return true;
}
}

const URaftSimWaterRuntimeAdapter* RaftSimReviewCoordinates::GetMap(
    UWorld* World, const URaftSimWaterRuntimeAdapter* Water)
{
    IRaftSimRunCoordinateProvider* Provider;
    if (!FindProvider(World, Provider)) return nullptr;
    if (Provider) return Provider->GetProgressCoordinates(Water);
    return Water && Water->HasRiverCoordinateMap() && !Water->HasCartesianWaterCoordinates()
        ? Water : nullptr;
}

bool RaftSimReviewCoordinates::WorldToCoordinates(UWorld* World,
    const URaftSimWaterRuntimeAdapter* Water, const FVector& Position,
    FVector2D& OutStationLateralM, FVector& OutTangent, FVector& OutLeft)
{
    IRaftSimRunCoordinateProvider* Provider;
    if (!FindProvider(World, Provider)) return false;
    if (Provider) return Provider->WorldToRunCoordinates(
        Position, Water, OutStationLateralM, OutTangent, OutLeft);
    return Water && Water->HasRiverCoordinateMap() && !Water->HasCartesianWaterCoordinates() &&
        Water->WorldToRiverCoordinates(Position, OutStationLateralM, OutTangent, OutLeft);
}

bool RaftSimReviewCoordinates::ShorePose(UWorld* World,
    const URaftSimWaterRuntimeAdapter* Water, const FVector& RaftPosition,
    bool bRiverLeft, bool bLow, bool bLegacyHydraulicFrame,
    FVector& OutLocation, FRotator& OutRotation)
{
    FVector2D Coordinates;
    FVector Tangent = FVector::ZeroVector, Left = FVector::ZeroVector;
    const bool bValid = bLegacyHydraulicFrame
        ? Water && Water->WorldToRiverCoordinates(RaftPosition, Coordinates, Tangent, Left)
        : WorldToCoordinates(World, Water, RaftPosition, Coordinates, Tangent, Left);
    if (!bValid) return false;
    const FVector Along = Tangent.GetSafeNormal2D();
    const FVector Toward = (bRiverLeft ? Left : -Left).GetSafeNormal2D();
    if (Along.IsNearlyZero() || Toward.IsNearlyZero()) return false;
    OutLocation = RaftPosition - Along * 300.f + FVector::UpVector * (bLow ? 70.f : 320.f);
    const FVector LookAt = RaftPosition + Toward * (bLow ? 2200.f : 1500.f) +
        Along * (bLow ? 600.f : 1400.f) + FVector::UpVector * (bLow ? 40.f : 0.f);
    OutRotation = (LookAt - OutLocation).Rotation();
    return true;
}
