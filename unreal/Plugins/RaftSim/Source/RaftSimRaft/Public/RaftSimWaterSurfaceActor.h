#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ProceduralMeshComponent.h"

#include "RaftSimWaterSurfaceActor.generated.h"

class UProceduralMeshComponent;
class UMaterialInterface;
class URaftSimWaterRuntimeAdapter;

/**
 * Renders the live solver's free surface (water-rendering v1, P2): a procedural
 * grid mesh whose vertices track the water-runtime adapter's surface height and
 * normal each tick, with vertex-colour foam driven by the local Froude number.
 * Resolves the bridge subsystem's adapter at BeginPlay; falls back to a flat
 * plane when no live window is configured.
 */
UCLASS()
class RAFTSIMRAFT_API ARaftSimWaterSurfaceActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimWaterSurfaceActor();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    TObjectPtr<UProceduralMeshComponent> SurfaceMesh;

    /** Water material applied to the surface (single-layer water). */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    TObjectPtr<UMaterialInterface> WaterMaterial;

    /** Grid origin (world cm, lower corner). Centred on world origin, where the
     * loader re-centres the reach's hydraulic crux. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    FVector2D GridOriginCm = FVector2D(-10000.0, -10000.0);

    /** Legacy straight-window grid extent in meters. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    float GridSizeMeters = 200.0f;

    /** Curved full-reach surface length centred on the raft. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Full Reach")
    float CurvedGridLengthMeters = 240.0f;

    /** Curved full-reach surface width across the channel. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Full Reach")
    float CurvedGridWidthMeters = 96.0f;

    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Full Reach")
    float CurvedGridRecenterDistanceMeters = 32.0f;

    /** World-space spacing between surface vertices in meters — fine enough for
     * smooth foam/whitewater edges through the rapid. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    float VertexSpacingMeters = 1.5f;

    /** Surface refresh interval (s); the FV field evolves slowly at gameplay scale. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    float RefreshIntervalSeconds = 1.0f / 30.0f;

private:
    void BuildGrid();
    void RefreshSurface();
    void RecenterCurvedGrid();
    void ClampCurvedGridCenter();
    void UpdateCurvedGridPlanarGeometry();

    UPROPERTY()
    TObjectPtr<URaftSimWaterRuntimeAdapter> WaterAdapter;

    int32 GridStationN = 0;
    int32 GridLateralN = 0;
    bool bUsesCurvedRiverCoordinates = false;
    float CurvedGridCenterStationM = 0.0f;
    TArray<FVector> Vertices;
    TArray<FVector2D> RiverCoordinatesM;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<FProcMeshTangent> Tangents;
    float TimeSinceRefresh = 0.0f;
};
