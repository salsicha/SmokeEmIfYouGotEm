#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimRockObstacleActor.generated.h"

class UProceduralMeshComponent;
class USceneComponent;
class UStaticMeshComponent;
class UStaticMesh;

/**
 * Runtime-authoritative contact proxy for a rock that can wrap or pin the raft.
 * The visible mesh and the D4 obstacle share this actor transform and radius;
 * decorative rocks without this actor never silently influence raft physics.
 */
UCLASS()
class RAFTSIMRAFT_API ARaftSimRockObstacleActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimRockObstacleActor();

    virtual void BeginPlay() override;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Contact")
    float GetContactRadiusM() const { return ContactRadiusM; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Contact")
    float GetContactFriction() const { return FrictionCoefficient; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Contact")
    void ConfigureContact(float InRadiusM, float InFrictionCoefficient);

    /** Select the reviewed scan or deterministic project-owned fallback shell. */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Contact")
    void SetPreferReviewedVisual(bool bInPreferReviewedVisual);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Contact")
    bool HasProductionRiverBoulder() const;

    /**
     * Replace only the dormant reviewed visual for an explicit renderer
     * diagnostic. This never changes D4 contact or the procedural fallback.
     */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Contact|Diagnostics")
    void SetReviewedVisualMeshForDiagnostics(UStaticMesh* InMesh);

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    TObjectPtr<UProceduralMeshComponent> RockMesh;

    // Project-owned high-density closed shell used for ordinary presentation.
    // It has no collision and is fitted inside the native D4 contact envelope.
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    TObjectPtr<UStaticMeshComponent> ProductionRockVisual;

    // A rights-reviewed CC0 scan may provide the visible surface when the
    // asset is cooked. The procedural component remains the deterministic
    // fallback and D4 remains the only collision/contact authority.
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact")
    TObjectPtr<UStaticMeshComponent> ReviewedRockVisual;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact", meta = (ClampMin = "0.1"))
    float ContactRadiusM = 0.9f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Contact", meta = (ClampMin = "0.0", ClampMax = "2.0"))
    float FrictionCoefficient = 0.72f;

    // Fail closed to the deterministic shell. The optional scan remains
    // available for explicit renderer diagnostics until it passes that gate.
    bool bPreferReviewedVisual = false;

private:
    void RebuildVisualGeometry();

    /** Samples the live water field at the rock footprint and writes the local
     * surface elevation into the boulder material's RockWaterlineZCm, giving
     * every rock the dark wet band real river rock carries at its waterline.
     * Retries briefly because the live river window is configured by the raft
     * after many level actors have already begun play. Presentation only. */
    void ApplyWaterlineToMaterials();

    FTimerHandle WaterlineRetryHandle;
    int32 WaterlineAttemptsRemaining = 20;
};
