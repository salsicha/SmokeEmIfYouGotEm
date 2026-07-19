#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ProceduralMeshComponent.h"

#include "RaftSimRiverbedActor.generated.h"

class UProceduralMeshComponent;
class UMaterialInterface;
class URaftSimWaterRuntimeAdapter;

/**
 * Renders the solver window's riverbed and banks (photoreal terrain, P4): a
 * procedural grid whose vertices track the water-runtime adapter's sampled bed
 * elevation, textured with the world-aligned physical-corridor terrain
 * material. The cooked window carries genuine DEM relief (channel thalweg up
 * through the canyon walls), so sampling the bed reproduces the real terrain;
 * beyond the window the adapter clamps to the bank rim, so the walls continue
 * outward. Built once at BeginPlay (the bed is static), unlike the free surface.
 */
UCLASS()
class RAFTSIMRAFT_API ARaftSimRiverbedActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimRiverbedActor();

    virtual void BeginPlay() override;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Terrain")
    TObjectPtr<UProceduralMeshComponent> BedMesh;

    /** World-aligned PBR terrain material (physical-corridor rock/ground). */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Terrain")
    TObjectPtr<UMaterialInterface> TerrainMaterial;

    /** Grid origin (world cm, lower corner) — wider than the water window so the
     * banks and valley walls are visible around the rendered free surface. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Terrain")
    FVector2D GridOriginCm = FVector2D(-15000.0, -15000.0);

    /** Grid extent in meters (square). */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Terrain")
    float GridSizeMeters = 300.0f;

    /** World-space spacing between bed vertices in meters. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Terrain")
    float VertexSpacingMeters = 2.5f;

    /** Drops the whole bed by this many cm so the free surface reads as sitting
     * in the channel rather than z-fighting the thalweg. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Terrain")
    float BedSinkCm = 5.0f;

private:
    void BuildBed();

    UPROPERTY()
    TObjectPtr<URaftSimWaterRuntimeAdapter> WaterAdapter;
};
