#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "RaftSimCrewAvatarActor.generated.h"

class UMaterialInterface;
class UProceduralMeshComponent;
class USceneComponent;

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
};

/**
 * Project-owned, procedurally meshed crew character. Rounded organic body,
 * splash clothing, PFD, helmet, paddle, and joint-driven animation are built
 * from source at runtime, avoiding placeholder Engine primitives and raw-asset
 * redistribution concerns.
 */
UCLASS(BlueprintType)
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

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Animation")
    ERaftSimCrewAvatarAction GetAvatarAction() const { return CurrentAction; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    int32 GetProceduralBodyPartCount() const { return BodyParts.Num(); }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool UsesProjectOwnedProceduralGeometry() const { return true; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Crew|Appearance")
    bool HasFiniteVisualTransforms() const;

private:
    void BuildVisual();
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

    UPROPERTY()
    TArray<TObjectPtr<UProceduralMeshComponent>> BodyParts;

    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Pelvis;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Torso;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Pfd;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Head;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> Helmet;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> LeftUpperArm;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> LeftLowerArm;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> RightUpperArm;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> RightLowerArm;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> LeftThigh;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> LeftShin;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> RightThigh;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> RightShin;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> PaddleShaft;
    UPROPERTY() TObjectPtr<UProceduralMeshComponent> PaddleBlade;

    UPROPERTY(VisibleAnywhere, Category = "RaftSim|Crew|Animation")
    ERaftSimCrewAvatarAction CurrentAction = ERaftSimCrewAvatarAction::SeatedIdle;

    int32 VariantIndex = 0;
    int32 SeatSide = 1;
    bool bGuide = false;
    bool bVisualBuilt = false;
    float AnimationPhase = 0.0f;
    float ActionIntensity = 1.0f;
};
