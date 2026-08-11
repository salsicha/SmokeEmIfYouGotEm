#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "UObject/Interface.h"

#include "RaftSimCrewAvatarActor.generated.h"

class UMaterialInterface;
class UMaterialInstanceDynamic;
class UChildActorComponent;
class UProceduralMeshComponent;
class USceneComponent;
class UStaticMeshComponent;

/** Project-owned articulated animation states; no third-party character asset is required. */
UENUM(BlueprintType)
enum class ERaftSimCrewAvatarAction : uint8
{
    SeatedIdle,
    ForwardStroke,
    BackStroke,
    TurnLeft,
    TurnRight,
    Brace,
    HighSidePort,
    HighSideStarboard,
    Falling,
    Swimming,
    ReachRescue,
    ThrowLine,
    Reentry
};

/**
 * Contract implemented by a production character wrapper Blueprint. The
 * wrapper can contain an assembled MetaHuman (or an equivalent licensed
 * skeletal character) while the raft simulation remains asset-agnostic.
 */
UINTERFACE(BlueprintType)
class RAFTSIMRAFT_API URaftSimCrewProductionVisual : public UInterface
{
    GENERATED_BODY()
};

class RAFTSIMRAFT_API IRaftSimCrewProductionVisual
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "RaftSim|Crew|Production")
    void ConfigureCrewAppearance(int32 VariantIndex, int32 SeatSide, bool bGuide);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "RaftSim|Crew|Production")
    void ApplyCrewPose(
        ERaftSimCrewAvatarAction Action,
        float NormalizedPhase,
        float Intensity,
        int32 SeatSide);
};

/** Joint targets in avatar-local centimetres. */
USTRUCT(BlueprintType)
struct FRaftSimCrewAvatarPose
{
    GENERATED_BODY()

    FVector TorsoCenterCm = FVector::ZeroVector;
    FRotator TorsoRotation = FRotator::ZeroRotator;
    FVector HeadCenterCm = FVector::ZeroVector;
    FVector LeftShoulderCm = FVector::ZeroVector;
    FVector LeftHandCm = FVector::ZeroVector;
    FVector RightShoulderCm = FVector::ZeroVector;
    FVector RightHandCm = FVector::ZeroVector;
    FVector LeftHipCm = FVector::ZeroVector;
    FVector LeftKneeCm = FVector::ZeroVector;
    FVector LeftFootCm = FVector::ZeroVector;
    FVector RightHipCm = FVector::ZeroVector;
    FVector RightKneeCm = FVector::ZeroVector;
    FVector RightFootCm = FVector::ZeroVector;
    FVector PaddleTopCm = FVector::ZeroVector;
    FVector PaddleBottomCm = FVector::ZeroVector;
    bool bShowPaddle = true;
};

UCLASS()
class RAFTSIMRAFT_API URaftSimCrewAvatarPoseLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** Deterministic Control-Rig-equivalent pose solve used by runtime and automation. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Animation")
    static FRaftSimCrewAvatarPose EvaluatePose(
        ERaftSimCrewAvatarAction Action,
        float NormalizedPhase,
        int32 SeatSide
    );

    /** Small repeatable timing error that keeps a commanded crew coordinated but not cloned. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Animation")
    static float GetDeterministicTimingOffset(int32 VariantIndex, bool bGuide);

};

/**
 * Crew presentation host. It prefers a configured production-character
 * wrapper implementing IRaftSimCrewProductionVisual and retains the complete
 * project-owned procedural character as a deterministic missing-asset fallback.
 */
UCLASS(BlueprintType, Config = Game, DefaultConfig)
class RAFTSIMRAFT_API ARaftSimCrewAvatarActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimCrewAvatarActor();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Crew|Animation")
    void SetAvatarAction(ERaftSimCrewAvatarAction NewAction, float Intensity = 1.0f);

    /**
     * Hides this avatar's head and helmet so a first-person camera can sit
     * in its eye socket (possessed guide seat). Idempotent per value.
     */
    void SetFirstPersonHeadHidden(bool bHidden);

    /**
     * World-space centre of the posed head. Valid while the head is hidden
     * for first person: the hidden part still tracks the pose every frame.
     */
    FVector GetPoseHeadWorldLocationCm() const;

    /**
     * Actor-local Z of the lowest point of the seated pelvis (glute
     * underside). Seat placement uses it to rest the body ON a surface
     * instead of trusting a hand-tuned seat height.
     */
    float GetSeatedPelvisBottomLocalZCm() const;

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Crew|Appearance")
    void ConfigureAppearance(int32 InVariantIndex, int32 InSeatSide, bool bInGuide);

    /** Builds renderer-owned layers when spawned by editor validation tooling. */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Crew|Appearance")
    void InitializeAvatarVisual();

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Animation")
    ERaftSimCrewAvatarAction GetAvatarAction() const { return CurrentAction; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    int32 GetProceduralBodyPartCount() const { return BodyParts.Num(); }

    /** Deterministic depth/width/stature profile used to break up cloned silhouettes. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    FVector GetBodyProportionScale() const;

    /** Deterministic skin tone authored into the batched head mesh vertex colours. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    FLinearColor GetSkinTone() const;

    /** True when the full river-ready PFD and helmet-retention layers exist. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasLayeredCommercialSafetyGear() const;

    /** True when the fitted project-owned static whitewater helmet replaced the fallback cap. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasProductionWhitewaterHelmet() const;

    /** True when the authored static rescue PFD replaced all procedural vest layers. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasProductionWhitewaterPfd() const;

    /** True when the visible PFD shell owns its live water-response material instance. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasLivePfdMaterialResponse() const;

    /** True when the visible splash-jacket torso and sleeves share live cloth wetness. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasLiveSplashJacketMaterialResponse() const
    {
        return SplashJacketMaterialInstance != nullptr;
    }

    /** Bounded presentation-only PFD saturation; never physics or rescue authority. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    float GetPfdPresentationWetness() const { return PfdPresentationWetness; }

    /** True when both solved feet use the authored static whitewater river boot. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasProductionRiverBoots() const;

    /** True when both authored boots are fitted, toe-forward, and unambiguously sole-down. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasFittedUprightProductionRiverBoots() const;

    /** True when the host carries a modeled blade, shaft, and transverse T-grip. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasCommercialPaddleSilhouette() const;

    /** True when the existing head draw contains the complete coloured face assembly. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasBatchedFacialFeatures() const;

    /** Disconnected facial shapes batched into the existing single head draw. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    int32 GetBatchedFacialSubmeshCount() const { return 17; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool UsesProjectOwnedProceduralGeometry() const { return !bUsingProductionVisual; }

    /** True only when a packaged production wrapper loaded and accepted the adapter contract. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool IsUsingProductionVisual() const { return bUsingProductionVisual; }

    /** Configured or conventional soft class path selected for this avatar. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FString GetProductionVisualClassPath() const;

    /** Live selected visual child used by gameplay and evidence capture. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    AActor* GetProductionVisualActor() const;

    /** True when the packaged CC0 body owns the complete visible anatomy. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool HasExclusiveCC0BodyOwnership() const;

    /** Selects the packaged CC0 adapter for deterministic renderer validation. */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Crew|Validation")
    bool ActivateCC0FallbackForValidation();

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasFiniteVisualTransforms() const;

    /** Distance between the visible helmet fit and the solved production head. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetProductionHelmetHeadErrorCm() const;

    /** Dot product between the shell's authored front and the rendered face direction. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetProductionHelmetForwardAlignment() const;

    /** Effective identity-calibrated uniform scale of the production helmet. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetProductionHelmetFitScale() const;

    /** Distance between the authored PFD origin and deterministic torso solve. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetProductionPfdTorsoErrorCm() const;

    /** True when the production character retains the pose-matched wetsuit waist/hip volume. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool HasVisibleWaistHipSilhouette() const;

    /** Half-extents of the retained waist/hip volume in centimetres. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FVector GetWaistHipExtentCm() const;

    /** Distance between the visible waist/hip volume and the solved hip centre. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetWaistHipCenterErrorCm() const;

    /** True when the pelvis and pose-matched thigh roots all use opaque materials. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool IsWaistHipMaterialOpaque() const;

    /** Smallest half-extent shared by the two retained wetsuit thigh bridges. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FVector GetMinimumHipThighBridgeExtentCm() const;

    /** Smallest authored vertex count shared by the two anatomical thigh meshes. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    int32 GetMinimumThighMeshVertexCount() const;

    /** Smallest dot product between either thigh's anterior axis and torso forward. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetMinimumThighForwardAlignment() const;

    /** Largest distance from either solved hip to its buried thigh-bridge centreline. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetMaximumHipThighBridgeCoverageErrorCm() const;

    /** True when both tapered thigh overlays overlap their solved knees without oversizing them. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool HasContinuousThighKneeSilhouette() const;

    /** Largest distance from either solved knee to its tapered thigh centreline. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetMaximumThighKneeBridgeCoverageErrorCm() const;

    /** True when two pose-matched splash-jacket sleeves bridge the PFD to the assembled arms. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    bool HasVisibleShoulderSilhouette() const;

    /** Smallest half-extent shared by the two visible proximal shoulder sleeves. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    FVector GetMinimumShoulderSleeveExtentCm() const;

    /** Smallest authored vertex count shared by the two tapered garment sleeves. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    int32 GetMinimumShoulderSleeveVertexCount() const;

    /** Largest distance between a sleeve's proximal endpoint and its solved shoulder joint. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetMaximumShoulderSleeveAnchorErrorCm() const;

    /** Keep one posed production-body caster instead of duplicate character layers. */
    void SetProductionBodyOnlyShadowMode(bool bEnabled);

private:
    void BuildVisual();
    void RebuildSafetyGearMeshes();
    void RebuildPaddleMeshes();
    void RebuildHeadMesh();
    void TryActivateProductionVisual();
    bool TryActivateCC0FallbackVisual();
    /** Shows the full fallback, or only project-owned rafting gear over a rigged body. */
    void SetProceduralVisualVisible(bool bVisible);
    void DispatchProductionPose();
    bool ResolveProductionHeadFit(
        FVector& OutSolvedHeadWorldLocation,
        FVector& OutFaceForwardWorld,
        FVector& OutFaceUpWorld,
        float& OutHelmetScale) const;
    void AlignProductionHeadgearToSolvedHead();
    void UpdatePfdMaterialResponse(float DeltaSeconds);
    void ApplyPfdMaterialWetness();
    void ApplyPose(const FRaftSimCrewAvatarPose& Pose);
    UProceduralMeshComponent* CreateOrganicPart(
        const TCHAR* Name,
        UMaterialInterface* Material,
        int32 MaterialSlot = 0);
    static void SetEllipsoid(
        UProceduralMeshComponent* Component,
        const FVector& CenterCm,
        const FRotator& Rotation,
        const FVector& RadiusCm);
    static void SetRoundedLimb(
        UProceduralMeshComponent* Component,
        const FVector& StartCm,
        const FVector& EndCm,
        float RadiusCm);
    static void SetAnatomicalThigh(
        UProceduralMeshComponent* Component,
        const FVector& StartCm,
        const FVector& EndCm,
        float RadiusCm,
        const FVector& TorsoForward);

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> Root;

    /**
     * Child actor hosting a production character Blueprint. A valid wrapper
     * must implement IRaftSimCrewProductionVisual; arbitrary classes fail
     * closed to the procedural fallback.
     */
    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Production")
    TObjectPtr<UChildActorComponent> ProductionVisual;

    UPROPERTY(Config, EditAnywhere, Category = "RaftSim|Crew|Production")
    TArray<FSoftClassPath> ProductionCrewVisualClassPaths;

    UPROPERTY(Config, EditAnywhere, Category = "RaftSim|Crew|Production")
    FSoftClassPath ProductionGuideVisualClassPath;

    UPROPERTY()
    TArray<TObjectPtr<UProceduralMeshComponent>> BodyParts;

    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Pelvis;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Torso;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> LeftShoulderSleeve;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> RightShoulderSleeve;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Pfd;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> PfdRearWebbing;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> PfdBelt;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> PfdBuckle;
    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Production")
    TObjectPtr<UStaticMeshComponent> ProductionPfd;
    UPROPERTY(Transient)
    TObjectPtr<UMaterialInstanceDynamic> PfdShellMaterialInstance;
    UPROPERTY(Transient)
    TObjectPtr<UMaterialInstanceDynamic> SplashJacketMaterialInstance;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Neck;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Head;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Helmet;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> HelmetRim;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> HelmetRetention;
    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Production")
    TObjectPtr<UStaticMeshComponent> ProductionHelmet;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> LeftUpperArm;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> LeftLowerArm;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> LeftHand;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> RightUpperArm;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> RightLowerArm;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> RightHand;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> LeftThigh;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> LeftShin;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> LeftBoot;
    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Production")
    TObjectPtr<UStaticMeshComponent> ProductionLeftBoot;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> RightThigh;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> RightShin;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> RightBoot;
    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Production")
    TObjectPtr<UStaticMeshComponent> ProductionRightBoot;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> PaddleShaft;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> PaddleBlade;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> PaddleGrip;

    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Animation")
    ERaftSimCrewAvatarAction CurrentAction = ERaftSimCrewAvatarAction::SeatedIdle;

    int32 VariantIndex = 0;
    int32 SeatSide = 1;
    bool bGuide = false;
    bool bVisualBuilt = false;
    bool bUsingProductionVisual = false;
    bool bFirstPersonHeadHidden = false;
    float AnimationPhase = 0.0f;
    float AnimationPhaseOffset = 0.0f;
    float ActionIntensity = 1.0f;
    float PfdPresentationWetness = 0.0f;
};
