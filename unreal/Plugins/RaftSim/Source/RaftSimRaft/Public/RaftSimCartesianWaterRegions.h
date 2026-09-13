#pragma once
#include "CoreMinimal.h"

class FJsonObject;
class URaftSimWaterRuntimeAdapter;

/** Source selection in shared hydraulic XY, never downstream chainage. */
class RAFTSIMRAFT_API FRaftSimCartesianWaterRegions
{
public:
    /** Shared launch/checkpoint path. Select the actual geographic source,
     * require wet destination, and commit only a validated replacement. */
    static bool ConfigureAtWorldPosition(URaftSimWaterRuntimeAdapter* Water,
        const FString& ManifestPath, const FString& FlowBand, const FVector& PositionCm);

    struct FRegion
    {
        FString Id;
        FString FieldsDirectory;
        FBox2D BoundsM;
        bool bHasExplicitLiveCenters = false;
        TArray<FBox2D> LiveCenterBoundsM;
    };

    bool Load(const TSharedPtr<FJsonObject>& Root, FString& OutError);
    const FRegion* Select(FVector2D PositionM, const FString& ActiveDirectory,
        FVector2D* OutWindowCenterM = nullptr) const;
    bool CoversRaft(FVector2D PositionM, FVector2D WindowCenterM) const;
    bool NeedsRecentering(FVector2D PositionM, FVector2D PreviousCenterM) const;
    FVector2D GetExtentM() const { return ExtentM; }
    float GetRoughnessManning() const { return static_cast<float>(RoughnessManning); }
    int32 Num() const { return Regions.Num(); }

private:
    TArray<FRegion> Regions;
    FVector2D ExtentM = FVector2D::ZeroVector;
    double GridSpacingM = 1.;
    double SourceContextCells = 1.;
    double AdvanceM = 80.;
    double RoughnessManning = 0.;
    double MinimumRaftInteriorMarginM = 0.;
};
