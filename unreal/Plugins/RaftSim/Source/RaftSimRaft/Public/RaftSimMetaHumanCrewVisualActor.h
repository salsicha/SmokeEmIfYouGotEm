#pragma once

#include "CoreMinimal.h"
#include "RaftSimCrewAvatarActor.h"

#include "RaftSimMetaHumanCrewVisualActor.generated.h"

class UChildActorComponent;
class UMaterialInstanceDynamic;
class UPoseableMeshComponent;
class USceneComponent;
class USkeletalMeshComponent;
class UStaticMeshComponent;

/**
 * MetaHuman adapter used by the production guide/crew host.
 *
 * A complete roster uses optimized assembled Blueprints so authored skin,
 * face RigLogic, grooms and wardrobe survive intact. A local blank archetype
 * remains available only for offline diagnostics. RaftSim retains authority
 * over safety gear, paddle interaction and the deterministic whitewater pose
 * solve; no cloud rigging or texture synthesis runs at runtime or during cook.
 */
UCLASS(BlueprintType)
class RAFTSIMRAFT_API ARaftSimMetaHumanCrewVisualActor final
    : public AActor,
      public IRaftSimCrewProductionVisual
{
    GENERATED_BODY()

public:
    ARaftSimMetaHumanCrewVisualActor();

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

    /** True when the production body exposes every digit needed for a closed paddle grip. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool HasArticulatedPaddleGripRig() const;

    /** Maximum middle-palm error against the last visible-paddle grip targets. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetMaximumPaddleGripAnchorErrorCm() const
    {
        return MaximumPaddleGripAnchorErrorCm;
    }

    /** True only when the reviewed, assembled character BP is the rendered body. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool IsUsingAssembledCharacter() const { return bUsingAssembledCharacter; }

    /** Body, face, wardrobe, hair, brows and lashes all resolve to production assets. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool HasCompleteAssembledPresentation() const
    {
        return bAssembledPresentationReady;
    }

    /** The live assembled child used by gameplay and renderer validation. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    AActor* GetAssembledCharacterActor() const;

    /** Effective forced LOD on the assembled hair groom, or INDEX_NONE. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    int32 GetAssembledHairForcedLOD() const;

    /** True when the reviewed LOD-5 hair mesh is attached to the live head bone. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool IsUsingHairMeshFallback() const { return HairMeshFallback != nullptr; }

    /** Imported garments remain audited but are hidden behind fitted rafting PPE. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool IsAssembledWardrobeSuppressedForSafetyGear() const;

    /** The anatomical body is rendered as the fitted rafting wetsuit layer. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool IsAssembledBodyUsingWetsuit() const;

    /** Authored face pixels use the baked identity shader with its PPE crop. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool IsAssembledFaceUsingCroppedSkin() const
    {
        return bAssembledFaceUsesCroppedSkin;
    }

    /** The audited hair mesh stays aligned but hidden beneath the mandatory helmet. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool IsHairMeshFallbackSuppressedForHelmet() const;

    /** No generated groom shell may compete with the fitted river helmet. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool IsAssembledHairGroomSuppressedForHelmet() const;

    /** Optimized groom assets are audited but baked face representation owns pixels. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool AreAssembledGroomsSuppressedForGameplay() const;

    /** Distance between the visible fallback origin and solved head bone. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetHairMeshFallbackHeadErrorCm() const;

    /** World-space head pivot used to frame close validation and fit PPE. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FVector GetSolvedHeadWorldLocation() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FVector GetAssembledFaceReferenceHeadComponentLocation() const
    {
        return ReferenceAssembledFaceHeadComponentTransform.GetLocation();
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FVector GetAssembledFacePreSkinnedBoundsOrigin() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FVector GetAssembledFacePreSkinnedBoundsExtent() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetAssembledFaceCropHeightCm() const { return AssembledFaceCropHeightCm; }

    /** Conventional optimized-build class path shared by runtime and validation. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    static FString GetAssembledBlueprintClassPath(bool bGuide, int32 VariantIndex);

    /** Prevents a partially authored roster from producing mixed release captures. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    static bool AreAllProductionCharactersAvailable();

    /**
     * Retain the posed wetsuit body as the grounded character silhouette while
     * omitting duplicate face and attachment geometry from virtual shadows.
     */
    void SetBodyOnlyShadowMode(bool bEnabled);

private:
    bool EnsureAssetsLoaded();
    bool TryActivateAssembledCharacter();
    void ResetAssembledCharacter();
    void CacheReferencePose();
    void ApplyBodyPose(const FRaftSimCrewAvatarPose& Pose);
    void ApplyPaddleGripPose(bool bShowPaddle);
    void ApplyFingerChain(bool bLeft, const TCHAR* Digit, bool bHasMetacarpal,
                          float GripAlpha);
    void SynchronizeAssembledFollowers();
    void UpdateRigidAssembledFace();
    void SetBoneAtPoint(FName BoneName, const FVector& DesiredPointCm);
    void SetSegmentBone(
        FName BoneName,
        FName ReferenceEndBone,
        const FVector& DesiredStartCm,
        const FVector& DesiredEndCm);
    void SetDrivenBoneTransform(FName BoneName, const FTransform& Transform);
    FVector ToMeshSpace(const FVector& PointCm) const;
    FVector ResolvePaddleGripWristCm(
        bool bLeft,
        const FVector& DesiredGripCm) const;
    float MeasurePaddleGripAnchorErrorCm(
        bool bLeft,
        const FVector& DesiredGripCm) const;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> Root;

    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Production")
    TObjectPtr<UPoseableMeshComponent> Body;

    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Production")
    TObjectPtr<UPoseableMeshComponent> Face;

    /**
     * Instantiates the optimized MetaHuman Blueprint so its face AnimBP,
     * RigLogic, grooms, eyelashes and wardrobe keep their authored runtime
     * behavior. The hidden poseable body remains the deterministic pose leader.
     */
    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Production")
    TObjectPtr<UChildActorComponent> AssembledCharacter;

    UPROPERTY(Transient)
    TObjectPtr<USkeletalMeshComponent> AssembledBody;

    float MaximumPaddleGripAnchorErrorCm = 0.0f;

    UPROPERTY(Transient)
    TObjectPtr<USkeletalMeshComponent> AssembledFace;

    UPROPERTY(Transient)
    TObjectPtr<UStaticMeshComponent> HairMeshFallback;

    UPROPERTY(Transient)
    TObjectPtr<UMaterialInstanceDynamic> FaceSkin;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UMaterialInstanceDynamic>> CroppedFaceSkins;

    UPROPERTY()
    TMap<FName, FTransform> ReferenceBodyTransforms;

    FTransform ReferenceAssembledFaceHeadComponentTransform = FTransform::Identity;
    FVector AssembledFaceComponentScale = FVector::OneVector;

    int32 CurrentVariantIndex = 0;
    bool bCurrentGuide = false;
    bool bBodyReady = false;
    bool bUsingAssembledCharacter = false;
    bool bAssembledPresentationReady = false;
    bool bAssembledWardrobeSuppressedForSafetyGear = false;
    bool bAssembledBodyUsesWetsuit = false;
    bool bAssembledFaceUsesCroppedSkin = false;
    float AssembledFaceCropHeightCm = 0.0f;
    static constexpr float BodyScale = 1.0f;
};
