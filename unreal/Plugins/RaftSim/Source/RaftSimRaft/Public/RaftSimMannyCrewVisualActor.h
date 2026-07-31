#pragma once

#include "CoreMinimal.h"
#include "RaftSimCrewAvatarActor.h"

#include "RaftSimMannyCrewVisualActor.generated.h"

class UMaterialInterface;
class UMaterialInstanceDynamic;
class UPoseableMeshComponent;
class USceneComponent;

/**
 * Locally packaged, rigged human-body fallback for crew presentation.
 *
 * The body comes from Epic's Unreal Engine mannequin template and is posed by
 * the same deterministic rafting pose contract as production characters. The
 * host avatar retains the project-owned PFD, helmet, boots, and paddle while
 * Manny supplies one coherent head/neck/hand silhouette instead of receiving
 * disconnected procedural anatomy overlays.
 */
UCLASS(BlueprintType)
class RAFTSIMRAFT_API ARaftSimMannyCrewVisualActor final
    : public AActor,
      public IRaftSimCrewProductionVisual
{
    GENERATED_BODY()

public:
    ARaftSimMannyCrewVisualActor();

    virtual void ConfigureCrewAppearance_Implementation(
        int32 VariantIndex,
        int32 SeatSide,
        bool bGuide) override;

    virtual void ApplyCrewPose_Implementation(
        ERaftSimCrewAvatarAction Action,
        float NormalizedPhase,
        float Intensity,
        int32 SeatSide) override;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool IsBodyReady() const { return bBodyReady; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool HasFinitePose() const;

private:
    bool EnsureBodyLoaded();
    void CacheReferencePose();
    void ApplyBodyPose(const FRaftSimCrewAvatarPose& Pose);
    void SetBoneAtPoint(FName BoneName, const FVector& DesiredPointCm);
    void SetSegmentBone(
        FName BoneName,
        FName ReferenceEndBone,
        const FVector& DesiredStartCm,
        const FVector& DesiredEndCm);
    FVector ToMeshSpace(const FVector& PointCm) const;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> Root;

    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Production")
    TObjectPtr<UPoseableMeshComponent> Body;

    UPROPERTY()
    TMap<FName, FTransform> ReferenceComponentTransforms;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UMaterialInstanceDynamic>> BodyMaterialInstances;

    bool bBodyReady = false;
    static constexpr float BodyScale = 0.72f;
};
