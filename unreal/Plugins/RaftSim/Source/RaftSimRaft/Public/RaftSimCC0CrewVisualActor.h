#pragma once

#include "CoreMinimal.h"
#include "RaftSimCrewAvatarActor.h"

#include "RaftSimCC0CrewVisualActor.generated.h"

class UPoseableMeshComponent;
class USceneComponent;

/**
 * Packaged CC0 human body used by the production guide/crew adapter.
 *
 * Five independently morphed MakeHuman game-engine rigs provide the body,
 * face, skin, eyes, and wetsuit. The host avatar keeps authority over rafting
 * gear, the paddle, gameplay, rescue state, and the deterministic pose solve.
 */
UCLASS(BlueprintType)
class RAFTSIMRAFT_API ARaftSimCC0CrewVisualActor final
    : public AActor,
      public IRaftSimCrewProductionVisual
{
    GENERATED_BODY()

public:
    ARaftSimCC0CrewVisualActor();

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

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FString GetSelectedMeshPath() const;

    /** World-space anchor of the coherently posed head/hair island. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FVector GetSolvedHeadWorldLocation() const;

    /** World-space direction the rendered face points after the rafting pose. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FVector GetSolvedFaceForwardWorldVector() const;

    /** World-space crown direction paired with the rendered face frame. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FVector GetSolvedFaceUpWorldVector() const;

    /** Uniform shell scale for the five similarly sized authored skulls. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetRecommendedWhitewaterHelmetScale() const { return 0.96f; }

private:
    bool EnsureBodyLoaded();
    void CacheReferencePose();
    void CacheRenderedFaceAnchorVertices();
    bool TryGetRenderedFaceEyeCenterWorld(FVector& OutWorldLocation) const;
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

    /** LOD0 rendered-eye vertices; their live centroid anchors the fitted helmet. */
    TArray<int32> RenderedFaceAnchorVertexIndices;

    int32 CurrentVariantIndex = 0;
    bool bCurrentGuide = false;
    bool bBodyReady = false;
    static constexpr float BodyScale = 1.0f;
};
