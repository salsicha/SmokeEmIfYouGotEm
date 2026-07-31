#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "UObject/Interface.h"

#include "RaftSimCrewAvatarActor.generated.h"

class UMaterialInterface;
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

    /** True when both solved feet use the authored static whitewater river boot. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasProductionRiverBoots() const;

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

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasFiniteVisualTransforms() const;

    /** Distance between the visible helmet fit and the solved production head. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetProductionHelmetHeadErrorCm() const;

    /** Distance between the authored PFD origin and deterministic torso solve. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Production")
    float GetProductionPfdTorsoErrorCm() const;

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
    void AlignProductionHeadgearToSolvedHead();
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
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Pfd;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> PfdRearWebbing;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> PfdBelt;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> PfdBuckle;
    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Production")
    TObjectPtr<UStaticMeshComponent> ProductionPfd;
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
    float AnimationPhase = 0.0f;
    float AnimationPhaseOffset = 0.0f;
    float ActionIntensity = 1.0f;
};
